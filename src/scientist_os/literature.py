"""Explicit public-query bibliographic discovery, never implicit project disclosure."""

from datetime import datetime, timezone
import json
import re

from defusedxml import ElementTree
import httpx

MAX_BYTES = 2_000_000
NOTICE = ("Crossref bibliographic discovery; publisher-deposited metadata can be incomplete. "
          "Results are not full-text review, a systematic search, or verification of scientific claims. "
          "Oversized or malformed abstracts are omitted; import the original paper to read them. "
          "Only the query you entered was sent; no workspace records were sent.")


def _plain(value, maximum=300):
    if not isinstance(value, str):
        return ""
    value = value.replace("\x00", "").strip()
    # Metadata is displayed as text; never interpreted as browser markup.
    return value.encode("utf-8", errors="replace").decode("utf-8")[:maximum]


def _first(value):
    return value[0] if isinstance(value, list) and value else ""


def _item(raw):
    if not isinstance(raw, dict):
        return None
    title = _plain(_first(raw.get("title")))
    doi = _plain(raw.get("DOI"), 200)
    if not title or not re.fullmatch(r"10\.[0-9]{4,9}/[^\s<>\"{}]+", doi, re.I):
        return None
    authors = []
    for author in (raw.get("author") or [])[:100]:
        if isinstance(author, dict):
            name = " ".join(filter(None, [_plain(author.get("given"), 100), _plain(author.get("family"), 100)]))
            name = name or _plain(author.get("name"), 200)
            if name:
                authors.append(name)
    year = None
    dates = raw.get("published") or raw.get("issued") or {}
    parts = dates.get("date-parts", []) if isinstance(dates, dict) else []
    first = _first(parts)
    candidate = _first(first) if isinstance(first, list) else None
    if type(candidate) is int and 1000 <= candidate <= 2100:
        year = candidate
    original_abstract = raw.get("abstract", "")
    abstract = _plain(original_abstract, 24000) if isinstance(original_abstract, str) and len(original_abstract) <= 24000 else ""
    if abstract:
        try:
            abstract = " ".join(ElementTree.fromstring("<root>" + abstract + "</root>").itertext())
        except Exception:
            abstract = ""  # Do not interpret malformed or entity-bearing publisher XML.
    if len(abstract) > 10000:
        abstract = ""  # Never present a silently truncated abstract as source evidence.
    return {"title": title, "authors": authors, "year": year, "doi": doi,
            "url": "https://doi.org/" + doi, "journal": _plain(_first(raw.get("container-title"))),
            "abstract": abstract, "full_text_ids": []}


def search_literature(query: str, *, transport=None) -> dict:
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 300 or any(ord(c) < 32 for c in query):
        raise ValueError("Enter a public literature query of 2–300 characters")
    query = query.strip()
    try:
        query.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError("The literature query contains invalid text") from exc
    # Fixed host and endpoint: imported DOI/URL fields cannot redirect network access.
    try:
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False, transport=transport,
                          headers={"User-Agent": "ScientistOS/0.2 (https://github.com/PabloAu/scientist-os)",
                                   "Accept": "application/json"}) as client:
            with client.stream("GET", "https://api.crossref.org/works",
                               params={"query.bibliographic": query, "rows": 5}) as response:
                if response.status_code != 200:
                    raise ValueError("Crossref is unavailable or rate limited. Try again later; no records were imported.")
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_BYTES:
                        raise ValueError("Crossref returned too much data; narrow the query")
        payload = json.loads(data)
        items = payload.get("message", {}).get("items")
        if not isinstance(items, list):
            raise ValueError("Crossref returned an unsupported response; no records were imported")
        normalized = [item for raw in items[:5] if (item := _item(raw))]
    except httpx.HTTPError as exc:
        raise ValueError("Crossref could not be reached. Check the network and retry; no records were imported.") from exc
    except (TypeError, AttributeError, RecursionError, json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("Crossref returned an unreadable response; no records were imported") from exc
    return {"items": normalized, "provider": "Crossref", "query": query, "notice": NOTICE,
            "retrieved_at": datetime.now(timezone.utc).isoformat()}
