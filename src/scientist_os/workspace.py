"""Transactional, portable records and a tamper-evident local research history.

The workspace is a single-user data store, not an authentication system or a
security sandbox. Review decisions are attributed human statements, not proof of
scientific validity. Original record versions remain in the immutable event log.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any, Iterator
from uuid import uuid4


SCHEMA_VERSION = 1
KINDS = frozenset({
    "source", "dataset", "material", "protocol", "processed_data", "analysis",
    "output", "claim", "term", "experiment", "manuscript", "software", "decision", "note",
    "reference", "document", "presentation", "discussion",
})
MAX_CONTENT_BYTES = 2 * 1024 * 1024
MAX_METADATA_BYTES = 256 * 1024
MAX_RUN_BYTES = 4 * 1024 * 1024
MAX_LINKS = 256
_ID_RE = re.compile(r"^(?:" + "|".join(sorted(KINDS)) + r")_[0-9a-f]{32}$")
_RUN_RE = re.compile(r"^run_[0-9a-f]{32}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_SECRET_KEYS = frozenset({
    "apikey", "authorization", "proxyauthorization", "password", "passwd",
    "secret", "clientsecret", "accesstoken", "refreshtoken", "idtoken",
    "credential", "credentials", "privatekey", "cookie", "setcookie", "token", "auth",
})
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")
_API_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
_SERVICE_TOKEN_RE = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,})\b")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest(value: Any) -> str:
    return _hash(_json(value))


def _text(value: Any, name: str, maximum: int, *, empty: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8 text") from exc
    if size > maximum or "\x00" in value:
        raise ValueError(f"{name} exceeds its size limit or contains a null character")
    if not empty and not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _bounded_json(value: Any, name: str, maximum: int, *, max_depth: int = 20) -> Any:
    """Reject non-JSON values, cycles, excessive nesting and nonfinite numbers."""
    ancestors: set[int] = set()
    count = 0

    def walk(item: Any, depth: int) -> None:
        nonlocal count
        count += 1
        if depth > max_depth or count > 100_000:
            raise ValueError(f"{name} is too deeply nested or contains too many values")
        if item is None or isinstance(item, bool):
            return
        if isinstance(item, str):
            _text(item, name, maximum)
            return
        if isinstance(item, int):
            if item.bit_length() > 256:
                raise ValueError(f"{name} contains an excessively large integer")
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError(f"{name} contains a nonfinite number")
            return
        if not isinstance(item, (dict, list)):
            raise ValueError(f"{name} must contain only JSON objects, arrays and scalar values")
        identity = id(item)
        if identity in ancestors:
            raise ValueError(f"{name} contains a cycle")
        ancestors.add(identity)
        if isinstance(item, dict):
            for key, child in item.items():
                _text(key, f"{name} key", 256, empty=False)
                walk(child, depth + 1)
        else:
            for child in item:
                walk(child, depth + 1)
        ancestors.remove(identity)

    walk(value, 0)
    encoded = _json(value)
    if len(encoded.encode("utf-8")) > maximum:
        raise ValueError(f"{name} exceeds the {maximum}-byte limit")
    return json.loads(encoded)


def _record_id(value: Any) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError("Invalid record identifier")
    return value


def _revision(value: Any) -> int:
    if type(value) is not int or value < 1 or value > 2**63 - 1:
        raise ValueError("expected_revision must be a positive integer")
    return value


def _kind(value: Any) -> str:
    if not isinstance(value, str) or value not in KINDS:
        raise ValueError(f"kind must be one of: {', '.join(sorted(KINDS))}")
    return value


def _links(value: Any) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_LINKS:
        raise ValueError(f"links must be an array of at most {MAX_LINKS} record identifiers")
    result = [_record_id(item) for item in value]
    if len(set(result)) != len(result):
        raise ValueError("links must not contain duplicates")
    return result


def _metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("metadata must be a JSON object")
    result = _bounded_json(value, "metadata", MAX_METADATA_BYTES)
    if "external_allowed" in result and type(result["external_allowed"]) is not bool:
        raise ValueError("metadata.external_allowed must be a boolean")
    citations = result.get("citations", [])
    if not isinstance(citations, list) or len(citations) > MAX_LINKS:
        raise ValueError("metadata.citations must be a bounded array")
    for citation in citations:
        if not isinstance(citation, dict) or set(citation) != {"record_id", "quote", "sha256"}:
            raise ValueError("Each citation must contain exactly record_id, quote and sha256")
        _record_id(citation["record_id"])
        _text(citation["quote"], "citation quote", 16_384, empty=False)
        if not isinstance(citation["sha256"], str) or not _HASH_RE.fullmatch(citation["sha256"]):
            raise ValueError("Citation sha256 must be a lowercase SHA-256 hex digest")
    revisions = result.get("input_revisions", {})
    if not isinstance(revisions, dict) or len(revisions) > MAX_LINKS:
        raise ValueError("metadata.input_revisions must map record identifiers to revisions")
    for record_id, revision in revisions.items():
        _record_id(record_id)
        _revision(revision)
    return result


def _dependencies(record: dict[str, Any]) -> set[str]:
    return (
        set(record["links"])
        | {citation["record_id"] for citation in record["metadata"].get("citations", [])}
        | set(record["metadata"].get("input_revisions", {}))
    )


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            normalized = re.sub(r"[^a-z]", "", key.lower())
            sensitive = normalized in _SECRET_KEYS or normalized.endswith(
                ("apikey", "accesstoken", "refreshtoken", "clientsecret", "password")
            )
            result[_redact(key)] = "[REDACTED]" if sensitive else _redact(child)
        return result
    if isinstance(value, list):
        return [_redact(child) for child in value]
    if isinstance(value, str):
        return _SERVICE_TOKEN_RE.sub("[REDACTED]", _API_KEY_RE.sub("[REDACTED]", _BEARER_RE.sub("Bearer [REDACTED]", value)))
    return value


def _workspace_operation(function):
    """Mark explicit transactions aborted even for pre-connection validation."""
    @wraps(function)
    def guarded(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        except BaseException:
            active = getattr(self._local, "transaction_state", None)
            if active is not None:
                active["failed"] = True
            raise

    return guarded


class Workspace:
    """One portable directory with versioned records and an append-only audit log.

    Each operation opens its own SQLite connection. Writes, downstream review
    invalidations, and events commit together under BEGIN IMMEDIATE. Expected
    revisions prevent a stale browser or agent from overwriting a later decision.
    """

    def __init__(self, root: str | Path):
        self._local = threading.local()
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "scientist-os.sqlite3"
        with self._connection(write=True) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise RuntimeError(f"Unsupported workspace schema version {version}; expected {SCHEMA_VERSION}")
            if version == 0 and connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone():
                raise RuntimeError("Refusing to initialize an unrecognized nonempty database")
            statements = [
                """CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
                    content TEXT NOT NULL, metadata TEXT NOT NULL, links TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision > 0), sha256 TEXT NOT NULL,
                    review_status TEXT NOT NULL CHECK(review_status IN ('unreviewed','approved','rejected')),
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, state_sha256 TEXT NOT NULL
                )""",
                """CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
                    action TEXT NOT NULL, record_id TEXT, timestamp TEXT NOT NULL,
                    data TEXT NOT NULL, previous_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL
                )""",
                "CREATE INDEX IF NOT EXISTS events_record ON events(record_id, sequence)",
                "CREATE INDEX IF NOT EXISTS records_kind ON records(kind)",
                """CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, data TEXT NOT NULL, sha256 TEXT NOT NULL
                )""",
                """CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'Events are immutable'); END""",
                """CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'Events are immutable'); END""",
                """CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records
                    BEGIN SELECT RAISE(ABORT, 'Record deletion is unavailable in beta'); END""",
                """CREATE TRIGGER IF NOT EXISTS runs_no_update BEFORE UPDATE ON runs
                    BEGIN SELECT RAISE(ABORT, 'Runs are immutable'); END""",
                """CREATE TRIGGER IF NOT EXISTS runs_no_delete BEFORE DELETE ON runs
                    BEGIN SELECT RAISE(ABORT, 'Runs are immutable'); END""",
            ]
            for statement in statements:
                connection.execute(statement)
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @contextmanager
    def _connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        active = getattr(self._local, "transaction_state", None)
        if active is not None:
            try:
                if active["failed"]:
                    raise RuntimeError("Transaction is aborted because an earlier nested operation failed")
                if write and not active["write"]:
                    raise RuntimeError("A read-only transaction cannot be promoted to a write transaction")
                yield active["connection"]
            except sqlite3.Error as exc:
                active["failed"] = True
                raise RuntimeError(f"Workspace database integrity or transaction conflict: {exc}") from exc
            except BaseException:
                active["failed"] = True
                raise
            return
        connection = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        state = {"connection": connection, "write": write, "failed": False}
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 10000")
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            self._local.transaction_state = state
            yield connection
            if state["failed"]:
                raise RuntimeError("Transaction rolled back because a nested operation failed")
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise RuntimeError(f"Workspace database integrity or transaction conflict: {exc}") from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            if getattr(self._local, "transaction_state", None) is state:
                del self._local.transaction_state
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[Workspace]:
        """Atomically combine operations on this instance in the current thread.

        A write lock is obtained before the first source read, preventing source
        changes between computation and derived-record registration. Nested
        calls join the same transaction; any failed nested operation aborts the
        entire unit even when its exception is caught. Other threads and other
        Workspace instances use independent connections. Do not perform network
        requests, await work, or retain the context across threads inside it.
        """
        with self._connection(write=True):
            yield self

    @staticmethod
    def _decode_record(row: sqlite3.Row) -> dict[str, Any]:
        try:
            result = dict(row)
            result.pop("state_sha256", None)
            result["metadata"] = json.loads(result["metadata"])
            result["links"] = json.loads(result["links"])
            return result
        except (ValueError, TypeError, KeyError) as exc:
            raise RuntimeError("Record contains malformed stored data") from exc

    def _read_record(self, connection: sqlite3.Connection, record_id: str) -> dict[str, Any]:
        row = connection.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise KeyError(record_id)
        result = self._decode_record(row)
        if _hash(result["content"]) != result["sha256"] or _digest(result) != row["state_sha256"]:
            raise RuntimeError(f"Record integrity verification failed: {record_id}")
        event_row = connection.execute(
            "SELECT data FROM events WHERE record_id = ? ORDER BY sequence DESC LIMIT 1", (record_id,)
        ).fetchone()
        try:
            if event_row is None or json.loads(event_row["data"])["record_sha256"] != row["state_sha256"]:
                raise RuntimeError(f"Record does not match its audit history: {record_id}")
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(f"Malformed record audit history: {record_id}") from exc
        return result

    @staticmethod
    def _write_record(connection: sqlite3.Connection, record: dict[str, Any], *, create: bool = False) -> None:
        encoded = dict(record, metadata=_json(record["metadata"]), links=_json(record["links"]), state_sha256=_digest(record))
        if create:
            connection.execute(
                """INSERT INTO records (id,kind,title,content,metadata,links,revision,sha256,
                review_status,created_at,updated_at,state_sha256)
                VALUES (:id,:kind,:title,:content,:metadata,:links,:revision,:sha256,
                :review_status,:created_at,:updated_at,:state_sha256)""", encoded,
            )
        else:
            connection.execute(
                """UPDATE records SET title=:title, content=:content, metadata=:metadata,
                links=:links, revision=:revision, sha256=:sha256, review_status=:review_status,
                updated_at=:updated_at, state_sha256=:state_sha256 WHERE id=:id""", encoded,
            )

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection, action: str, data: dict[str, Any], record_id: str | None = None,
    ) -> dict[str, Any]:
        previous = connection.execute("SELECT sequence,sha256 FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
        event = {
            "sequence": previous["sequence"] + 1 if previous else 1,
            "id": f"event_{uuid4().hex}", "action": action, "record_id": record_id,
            "timestamp": _now(), "data": data, "previous_sha256": previous["sha256"] if previous else "0" * 64,
        }
        event["sha256"] = _digest(event)
        connection.execute(
            """INSERT INTO events (sequence,id,action,record_id,timestamp,data,previous_sha256,sha256)
            VALUES (:sequence,:id,:action,:record_id,:timestamp,:data,:previous_sha256,:sha256)""",
            dict(event, data=_json(data)),
        )
        return event

    def _record_event(
        self, connection: sqlite3.Connection, action: str, record: dict[str, Any], **details: Any,
    ) -> None:
        self._append_event(connection, action, {
            **details, "record": record, "record_sha256": _digest(record),
        }, record["id"])

    def _validate_references(self, connection: sqlite3.Connection, record: dict[str, Any]) -> None:
        # Validate the entire dependency graph, including citations and revision
        # bindings not duplicated in links. An unchanged analysis quotation is
        # still stale when that analysis was computed from corrected input data.
        cached = {record["id"]: record}
        pending = [(record, False)]
        visiting: set[str] = set()
        visited: set[str] = set()
        while pending:
            current, closing = pending.pop()
            current_id = current["id"]
            if closing:
                visiting.remove(current_id)
                visited.add(current_id)
                continue
            if current_id in visited:
                continue
            if current_id in visiting:
                raise ValueError("Circular scientific dependencies are not allowed")
            visiting.add(current_id)
            dependencies = _dependencies(current)
            if current_id in dependencies:
                raise ValueError("A record cannot reference itself")
            for dependency in dependencies:
                if dependency in visiting:
                    raise ValueError("Circular scientific dependencies are not allowed")
                if dependency not in cached:
                    try:
                        cached[dependency] = self._read_record(connection, dependency)
                    except KeyError as exc:
                        if current_id == record["id"]:
                            raise ValueError(f"Referenced record does not exist: {dependency}") from exc
                        raise RuntimeError(f"Existing provenance contains a missing record: {dependency}") from exc
            for citation in current["metadata"].get("citations", []):
                source = cached[citation["record_id"]]
                if source["sha256"] != citation["sha256"]:
                    raise RuntimeError(f"Citation source hash changed: {source['id']}")
                if citation["quote"] not in source["content"]:
                    raise ValueError(f"Citation quote is not an exact source excerpt: {source['id']}")
            for source_id, revision in current["metadata"].get("input_revisions", {}).items():
                if cached[source_id]["revision"] != revision:
                    raise RuntimeError(f"Input revision is stale: {source_id}")
            pending.append((current, True))
            pending.extend((cached[dependency], False) for dependency in sorted(dependencies) if dependency not in visited)

    def _invalidate_dependents(self, connection: sqlite3.Connection, changed_id: str) -> None:
        rows = connection.execute("SELECT * FROM records").fetchall()
        records = {row["id"]: self._decode_record(row) for row in rows}
        reverse: dict[str, set[str]] = {}
        for record in records.values():
            for dependency in _dependencies(record):
                reverse.setdefault(dependency, set()).add(record["id"])
        visited = {changed_id}
        pending = [changed_id]
        while pending:
            upstream_id = pending.pop(0)
            for dependent_id in sorted(reverse.get(upstream_id, set())):
                if dependent_id in visited:
                    continue
                visited.add(dependent_id)
                pending.append(dependent_id)
                record = self._read_record(connection, dependent_id)
                before_revision = record["revision"]
                record["revision"] += 1
                record["review_status"] = "unreviewed"
                record["updated_at"] = _now()
                self._write_record(connection, record)
                self._record_event(connection, "dependency_invalidated", record,
                                   before_revision=before_revision, changed_record_id=changed_id,
                                   immediate_dependency_id=upstream_id)

    @_workspace_operation
    def create_record(
        self, kind: str, title: str, content: str = "", metadata: dict | None = None, links: list | None = None,
    ) -> dict[str, Any]:
        kind = _kind(kind)
        timestamp = _now()
        record = {
            "id": f"{kind}_{uuid4().hex}", "kind": kind,
            "title": _text(title, "title", 1000, empty=False).strip(),
            "content": _text(content, "content", MAX_CONTENT_BYTES),
            "metadata": _metadata({} if metadata is None else metadata),
            "links": _links([] if links is None else links), "revision": 1,
            "sha256": _hash(content), "review_status": "unreviewed",
            "created_at": timestamp, "updated_at": timestamp,
        }
        with self._connection(write=True) as connection:
            self._validate_references(connection, record)
            self._write_record(connection, record, create=True)
            self._record_event(connection, "record_created", record)
        return record

    @_workspace_operation
    def get_record(self, record_id: str) -> dict[str, Any]:
        _record_id(record_id)
        with self._connection() as connection:
            return self._read_record(connection, record_id)

    @_workspace_operation
    def validate_current(self, record_id: str) -> dict[str, Any]:
        """Read one record only if its complete declared evidence is still current.

        This checks integrity and revision/citation freshness, not scientific
        validity or approval status. Ancestor records are checked locally and
        are never included in the returned selected-record snapshot.
        """
        _record_id(record_id)
        with self._connection() as connection:
            record = self._read_record(connection, record_id)
            self._validate_references(connection, record)
            return record

    @_workspace_operation
    def list_records(self, kind: str | None = None) -> list[dict[str, Any]]:
        if kind is not None:
            _kind(kind)
        with self._connection() as connection:
            query = "SELECT id FROM records" + (" WHERE kind = ?" if kind is not None else "") + " ORDER BY created_at,id"
            rows = connection.execute(query, (kind,) if kind is not None else ()).fetchall()
            return [self._read_record(connection, row["id"]) for row in rows]

    @_workspace_operation
    def update_record(
        self, record_id: str, *, expected_revision: int, title: str | None = None,
        content: str | None = None, metadata: dict | None = None, links: list | None = None,
    ) -> dict[str, Any]:
        _record_id(record_id)
        _revision(expected_revision)
        updates: dict[str, Any] = {}
        if title is not None:
            updates["title"] = _text(title, "title", 1000, empty=False).strip()
        if content is not None:
            updates["content"] = _text(content, "content", MAX_CONTENT_BYTES)
            updates["sha256"] = _hash(content)
        if metadata is not None:
            updates["metadata"] = _metadata(metadata)
        if links is not None:
            updates["links"] = _links(links)
        if not updates:
            raise ValueError("Supply at least one field to update")
        with self._connection(write=True) as connection:
            record = self._read_record(connection, record_id)
            if record["revision"] != expected_revision:
                raise RuntimeError(f"Stale revision for {record_id}: expected {expected_revision}, current {record['revision']}")
            record.update(updates)
            record.update(revision=record["revision"] + 1, updated_at=_now(), review_status="unreviewed")
            self._validate_references(connection, record)
            self._write_record(connection, record)
            self._record_event(connection, "record_updated", record, before_revision=expected_revision)
            self._invalidate_dependents(connection, record_id)
        return record

    @_workspace_operation
    def review_record(
        self, record_id: str, *, expected_revision: int, decision: str, reviewer: str, note: str = "",
    ) -> dict[str, Any]:
        _record_id(record_id)
        _revision(expected_revision)
        if decision not in ("approved", "rejected"):
            raise ValueError("decision must be approved or rejected")
        reviewer = _text(reviewer, "reviewer", 500, empty=False).strip()
        note = _text(note, "review note", 20_000)
        with self._connection(write=True) as connection:
            record = self._read_record(connection, record_id)
            if record["revision"] != expected_revision:
                raise RuntimeError(f"Stale review revision for {record_id}")
            if decision == "approved":
                self._validate_references(connection, record)
            record.update(revision=record["revision"] + 1, review_status=decision, updated_at=_now())
            self._write_record(connection, record)
            self._record_event(connection, "record_reviewed", record, before_revision=expected_revision,
                               decision=decision, reviewer=reviewer, note=note,
                               qualification="Human review is an attributed decision, not scientific validation.")
            self._invalidate_dependents(connection, record_id)
        return record

    @_workspace_operation
    def search(self, query: str, record_ids: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        query = _text(query, "query", 1000, empty=False)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        tokens = list(dict.fromkeys(re.findall(r"\w+", query.casefold())))
        if not tokens:
            raise ValueError("query must contain a word or number")
        if record_ids is not None:
            record_ids = _links(record_ids)
        with self._connection() as connection:
            ids = record_ids if record_ids is not None else [row["id"] for row in connection.execute("SELECT id FROM records")]
            results = []
            for record_id in ids:
                record = self._read_record(connection, record_id)
                content = record["content"]
                folded = content.casefold()
                title = record["title"].casefold()
                score = sum(min(folded.count(token), 100) + 3 * min(title.count(token), 10) for token in tokens)
                if not score:
                    continue
                # Find on the original text so Unicode case-fold expansions do not
                # shift source offsets. Every excerpt is an exact substring.
                matches = [re.search(re.escape(token), content, flags=re.IGNORECASE) for token in tokens]
                offsets = [match.start() for match in matches if match is not None]
                start = max(0, min(offsets, default=0) - 160)
                excerpt = content[start:start + 800]
                results.append({
                    "record_id": record_id, "title": record["title"], "kind": record["kind"],
                    "excerpt": excerpt, "quote": excerpt, "sha256": record["sha256"],
                    "revision": record["revision"], "score": score,
                })
            return sorted(results, key=lambda row: (-row["score"], row["record_id"]))[:limit]

    @staticmethod
    def _event_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
        result = []
        for row in connection.execute("SELECT * FROM events ORDER BY sequence"):
            event = dict(row)
            try:
                event["data"] = json.loads(event["data"])
            except (ValueError, TypeError) as exc:
                raise RuntimeError("Event history contains malformed JSON") from exc
            result.append(event)
        return result

    @_workspace_operation
    def events(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            return self._event_rows(connection)

    @_workspace_operation
    def save_run(self, run: dict) -> dict[str, Any]:
        if not isinstance(run, dict):
            raise ValueError("run must be a JSON object")
        run = _bounded_json(run, "run", MAX_RUN_BYTES)
        original = run
        run = _redact(original)
        if run != original:
            run["redaction_applied"] = True
        original_citations = original.get("citations", [])
        safe_citations = run.get("citations", [])
        if isinstance(original_citations, list) and safe_citations != original_citations:
            # Redaction can change a credential-shaped source quotation after an
            # agent checked exactness. Changed text must never retain that check.
            run["citations"] = [
                safe for before, safe in zip(original_citations, safe_citations)
                if before == safe
            ]
            removed = len(original_citations) - len(run["citations"])
            run["citation_redaction"] = {
                "removed": removed, "reason": "credential_redaction_changed_exact_quotation",
            }
            run["grounding"] = "verified_quotes" if run["citations"] else "unsupported"
            warnings = run.get("warnings", [])
            if not isinstance(warnings, list):
                warnings = []
            run["warnings"] = warnings + [
                "Credential redaction removed changed quotations from verified citations. "
                "The historical trace may also contain redacted text."
            ]
            if not run["citations"] and run.get("status") == "needs_review":
                answer = run.get("answer", "")
                run["answer"] = (
                    "Unsupported proposal — no verified source quotations remain after redaction.\n\n"
                    + (answer if isinstance(answer, str) else "")
                )
        if "id" not in run:
            run["id"] = f"run_{uuid4().hex}"
        if not isinstance(run["id"], str) or not _RUN_RE.fullmatch(run["id"]):
            raise ValueError("Invalid run identifier")
        if "created_at" not in run:
            run["created_at"] = _now()
        _text(run["created_at"], "run created_at", 100, empty=False)
        with self._connection(write=True) as connection:
            connection.execute("INSERT INTO runs (id,data,sha256) VALUES (?,?,?)", (run["id"], _json(run), _digest(run)))
            self._append_event(connection, "run_saved", {"run_id": run["id"], "run_sha256": _digest(run)})
        return run

    @staticmethod
    def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
        try:
            run = json.loads(row["data"])
            if not isinstance(run, dict) or run.get("id") != row["id"] or _digest(run) != row["sha256"]:
                raise RuntimeError(f"Run integrity verification failed: {row['id']}")
            return run
        except (ValueError, TypeError) as exc:
            raise RuntimeError("Run contains malformed stored data") from exc

    @_workspace_operation
    def list_runs(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            return [self._decode_run(row) for row in connection.execute("SELECT * FROM runs ORDER BY rowid")]

    @_workspace_operation
    def get_run(self, run_id: str) -> dict[str, Any]:
        if not isinstance(run_id, str) or not _RUN_RE.fullmatch(run_id):
            raise ValueError("Invalid run identifier")
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            return self._decode_run(row)

    def _audit(self, connection: sqlite3.Connection) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []

        def flag(code: str, record_id: str | None, message: str, severity: str = "error") -> None:
            findings.append({"severity": severity, "code": code, "record_id": record_id, "message": message})

        records = {}
        for row in connection.execute("SELECT * FROM records ORDER BY created_at,id"):
            try:
                record = self._decode_record(row)
                records[record["id"]] = record
                if _hash(record["content"]) != record["sha256"]:
                    flag("content_hash_mismatch", record["id"], "Stored content does not match its SHA-256.")
                if _digest(record) != row["state_sha256"]:
                    flag("record_integrity_mismatch", record["id"], "Record fields were changed outside the audited workflow.")
                _record_id(record["id"])
                _kind(record["kind"])
                _metadata(record["metadata"])
                _links(record["links"])
            except (RuntimeError, ValueError, TypeError, KeyError) as exc:
                records.pop(row["id"], None)
                flag("malformed_record", row["id"], str(exc))
        latest_hashes: dict[str, str] = {}
        run_hashes: dict[str, str] = {}
        previous_hash = "0" * 64
        previous_sequence = 0
        try:
            event_rows = self._event_rows(connection)
        except RuntimeError as exc:
            flag("malformed_event", None, str(exc))
            event_rows = []
        for event in event_rows:
            if event["previous_sha256"] != previous_hash or event["sequence"] != previous_sequence + 1:
                flag("event_chain_broken", event["record_id"], f"Event sequence {event['sequence']} has a broken predecessor.")
            try:
                intact = _digest({key: value for key, value in event.items() if key != "sha256"}) == event["sha256"]
            except (ValueError, TypeError):
                intact = False
            if not intact:
                flag("event_integrity_mismatch", event["record_id"], f"Event sequence {event['sequence']} has changed.")
            data = event["data"]
            if isinstance(data, dict):
                if event["record_id"] is not None:
                    latest_hashes[event["record_id"]] = data.get("record_sha256", "")
                    try:
                        snapshot_intact = isinstance(data.get("record"), dict) and _digest(data["record"]) == data.get("record_sha256")
                    except (ValueError, TypeError):
                        snapshot_intact = False
                    if not snapshot_intact:
                        flag("event_record_mismatch", event["record_id"], "Historical record snapshot does not match its digest.")
                if event["action"] == "run_saved":
                    if not isinstance(data.get("run_id"), str) or not isinstance(data.get("run_sha256"), str):
                        flag("malformed_event", None, "Saved run event has invalid identifiers or digests.")
                    else:
                        run_hashes[data["run_id"]] = data["run_sha256"]
            else:
                flag("malformed_event", event["record_id"], "Event data must be a JSON object.")
            previous_hash, previous_sequence = event["sha256"], event["sequence"]
        for record in records.values():
            record_id = record["id"]
            if latest_hashes.get(record_id) != _digest(record):
                flag("record_history_mismatch", record_id, "Current record does not match the latest immutable event.")
            for dependency in _dependencies(record):
                if dependency == record_id:
                    flag("self_reference", record_id, "A record refers to itself.")
                elif dependency not in records:
                    flag("dangling_link", record_id, f"Referenced record is unavailable: {dependency}")
            for citation in record["metadata"].get("citations", []):
                source = records.get(citation["record_id"])
                if source is None:
                    flag("citation_source_missing", record_id, f"Citation source is unavailable: {citation['record_id']}")
                    continue
                if citation["sha256"] != source["sha256"]:
                    flag("citation_hash_mismatch", record_id, f"Citation source changed: {source['id']}. Recheck evidence.")
                if citation["quote"] not in source["content"]:
                    flag("citation_quote_mismatch", record_id, f"Citation is no longer an exact excerpt: {source['id']}")
            for input_id, revision in record["metadata"].get("input_revisions", {}).items():
                if input_id in records and records[input_id]["revision"] != revision:
                    flag("stale_input_revision", record_id, f"Analysis input {input_id} changed after revision {revision}. Recompute or reconcile.")
        stored_run_ids = set()
        for row in connection.execute("SELECT * FROM runs"):
            stored_run_ids.add(row["id"])
            try:
                run = self._decode_run(row)
                if run_hashes.get(run["id"]) != _digest(run):
                    flag("run_history_mismatch", None, f"Run does not match its saved audit event: {run['id']}")
            except RuntimeError as exc:
                flag("run_integrity_mismatch", None, str(exc))
        for run_id in run_hashes.keys() - stored_run_ids:
            flag("missing_run", None, f"Audited run is unavailable: {run_id}")
        for record_id in latest_hashes.keys() - records.keys():
            flag("missing_record", record_id, "An audited record is missing or malformed.")
        return findings

    @_workspace_operation
    def audit(self) -> list[dict[str, Any]]:
        """Deterministic data-integrity screening, separate from scientific review."""
        with self._connection() as connection:
            return self._audit(connection)

    @_workspace_operation
    def export_bundle(self) -> dict[str, Any]:
        """Return one consistent JSON snapshot; metadata paths are never opened."""
        with self._connection() as connection:
            records = [self._read_record(connection, row["id"]) for row in connection.execute("SELECT id FROM records ORDER BY created_at,id")]
            events = self._event_rows(connection)
            runs = [self._decode_run(row) for row in connection.execute("SELECT * FROM runs ORDER BY rowid")]
            manifest = {
                "algorithm": "sha256", "canonical_json": "UTF-8; sorted keys; compact separators; no ASCII escaping",
                "records": {record["id"]: _digest(record) for record in records},
                "runs": {run["id"]: _digest(run) for run in runs},
                "events_sha256": _digest(events),
                "event_chain_tip": events[-1]["sha256"] if events else "0" * 64,
                "findings": self._audit(connection),
            }
            bundle = {"schema_version": SCHEMA_VERSION, "exported_at": _now(), "records": records,
                      "events": events, "runs": runs, "integrity_manifest": manifest}
            manifest["bundle_sha256"] = _digest(bundle)
            return bundle
