"""Single-user loopback application; no cloud-hosting or authentication claims."""

import json
import os
import re
import secrets
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import __version__
from .demo import seed_demo
from .service import analyze, assert_current_lineage, create_figure, markdown_export, save_draft
from .workflows import STAGES
from .workspace import Workspace

MAX_REQUEST = 2_000_000
MAX_UPLOAD = 21 * 1024 * 1024


class LocalGuard:
    """Reject browser cross-origin writes, DNS rebinding and oversized requests."""

    def __init__(self, app, token: str):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in scope.get("headers", [])}
        host = headers.get("host", "")
        authority = re.fullmatch(r"(?:127\.0\.0\.1|localhost|\[::1\]|testserver)(?::([0-9]{1,5}))?", host)
        if authority is None or (authority.group(1) and not 1 <= int(authority.group(1)) <= 65535):
            return await JSONResponse({"detail": "Use the local loopback address"}, 403)(scope, receive, send)
        origin = headers.get("origin")
        if origin and origin != f"{scope.get('scheme', 'http')}://{host}":
            return await JSONResponse({"detail": "Cross-origin access is disabled"}, 403)(scope, receive, send)
        if headers.get("sec-fetch-site") == "cross-site":
            return await JSONResponse({"detail": "Cross-site access is disabled"}, 403)(scope, receive, send)
        if scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
            if not secrets.compare_digest(headers.get("x-scientist-token", ""), self.token):
                return await JSONResponse({"detail": "Refresh this page before saving"}, 403)(scope, receive, send)
            body = bytearray()
            limit = MAX_UPLOAD if scope.get("path") == "/api/library/import" else MAX_REQUEST
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > limit:
                    return await JSONResponse({"detail": "Upload exceeds 21 MB" if limit == MAX_UPLOAD else "Request exceeds 2 MB"}, 413)(scope, receive, send)
                if not message.get("more_body", False):
                    break
            delivered = False

            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            return await self.app(scope, bounded_receive, send)
        return await self.app(scope, receive, send)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RecordInput(StrictModel):
    kind: str
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(default="", max_length=1_000_000)
    metadata: dict = Field(default_factory=dict)
    links: list[str] = Field(default_factory=list, max_length=100)


class RecordUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, max_length=300)
    content: str | None = Field(default=None, max_length=1_000_000)
    metadata: dict | None = None
    links: list[str] | None = Field(default=None, max_length=100)


class ReviewInput(StrictModel):
    expected_revision: int = Field(ge=1)
    decision: str
    reviewer: str = Field(min_length=1, max_length=120)
    note: str = Field(default="", max_length=5000)

    @field_validator("reviewer")
    @classmethod
    def reviewer_nonblank(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("A nonblank reviewer name is required")
        return value.strip()


class AgentInput(StrictModel):
    question: str = Field(min_length=1, max_length=8000)
    source_ids: list[str] = Field(min_length=1, max_length=16)
    task: str = "answer"
    style: str = Field(default="", max_length=2000)
    max_steps: int = Field(default=8, ge=1, le=8)
    provider: str = "demo"


class AnalysisInput(StrictModel):
    dataset_id: str
    expected_revision: int | None = Field(default=None, ge=1)
    method: str = "summary"
    value_column: str = "signal"
    group_column: str | None = "group"
    unit_column: str | None = "day"
    model: str = "random"
    comparability_confirmed: bool = False
    effect_measure: str = ""


class DraftInput(StrictModel):
    kind: str = "note"
    title: str = Field(default="Assistant draft", min_length=1, max_length=300)


class GateInput(StrictModel):
    reviewer: str = Field(min_length=1, max_length=120)
    note: str = Field(min_length=1, max_length=5000)
    checked: list[str]
    links: list[str] = Field(default_factory=list)

    @field_validator("reviewer", "note")
    @classmethod
    def nonblank(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Reviewer and decision note must be nonblank text")
        return value.strip()


def create_app(workspace_path: str | Path) -> FastAPI:
    workspace = Workspace(workspace_path)
    app = FastAPI(title="Scientist OS", version=__version__, docs_url=None, redoc_url=None)
    token = secrets.token_urlsafe(32)
    app.state.workspace, app.state.csrf_token = workspace, token
    app.add_middleware(LocalGuard, token=token)
    static = files("scientist_os").joinpath("static")
    app.mount("/static", StaticFiles(directory=str(static)), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'"
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({"detail": "Record or run not found"}, status_code=404)

    @app.exception_handler(RuntimeError)
    async def conflict(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return static.joinpath("index.html").read_text(encoding="utf-8").replace("__CSRF_TOKEN__", token)

    @app.get("/api/state")
    def state():
        return {"version": __version__, "records": workspace.list_records(),
                "runs": workspace.list_runs(), "stages": STAGES,
                "provider_configured": bool(os.getenv("SCIENTIST_OS_MODEL") and os.getenv("SCIENTIST_OS_BASE_URL")),
                "model": os.getenv("SCIENTIST_OS_MODEL", ""),
                "mode": "single-user local"}

    @app.post("/api/demo")
    def demo():
        return {"records": seed_demo(workspace)}

    @app.get("/api/records/{record_id}")
    def get_record(record_id: str):
        return workspace.get_record(record_id)

    @app.post("/api/records", status_code=201)
    def create_record(body: RecordInput):
        return workspace.create_record(**body.model_dump())

    @app.patch("/api/records/{record_id}")
    def update_record(record_id: str, body: RecordUpdate):
        return workspace.update_record(record_id, **body.model_dump(exclude_none=True))

    @app.post("/api/records/{record_id}/review")
    def review(record_id: str, body: ReviewInput):
        return workspace.review_record(record_id, **body.model_dump())

    @app.get("/api/search")
    def search(q: str = ""):
        return workspace.search(q)

    @app.get("/api/audit")
    def audit():
        from .science import audit_records
        return {"integrity": workspace.audit(), "scientific_screening": audit_records(workspace.list_records())}

    @app.get("/api/events")
    def events():
        return workspace.events()

    @app.post("/api/analyses")
    def analysis(body: AnalysisInput):
        return analyze(workspace, body.model_dump())

    @app.get("/api/records/{record_id}/figure")
    def figure(record_id: str):
        record = workspace.get_record(record_id)
        if record["kind"] != "output" or record["metadata"].get("format") != "svg":
            raise ValueError("This record is not a generated figure")
        # Regenerate exclusively from trusted numeric results; never serve imported SVG as active content.
        from .science import render_figure
        parents = [workspace.get_record(i) for i in record["links"]]
        parent = next((p for p in parents if p["kind"] == "analysis" and "result" in p["metadata"]), None)
        if parent is None:
            raise ValueError("Figure has no reproducible analysis")
        assert_current_lineage(workspace, record)
        svg = render_figure(parent["metadata"]["result"], title=record["metadata"].get("figure_title", parent["title"]))
        return Response(svg, media_type="image/svg+xml", headers={"Content-Disposition": f'inline; filename="{record_id}.svg"'})

    @app.post("/api/analyses/{record_id}/figure")
    def regenerate_figure(record_id: str):
        return create_figure(workspace, workspace.get_record(record_id))

    @app.post("/api/agent")
    def agent(body: AgentInput):
        from .agent import AgentRunner
        from .authoring_api import get_provider
        provider = get_provider(body.provider)
        return AgentRunner(workspace, provider).run(body.question, body.source_ids,
                                                     task=body.task, style=body.style,
                                                     max_steps=body.max_steps)

    @app.post("/api/runs/{run_id}/draft")
    def draft(run_id: str, body: DraftInput):
        return save_draft(workspace, run_id, **body.model_dump())

    @app.post("/api/workflow/{stage_id}")
    def gate(stage_id: str, body: GateInput):
        stage = next((s for s in STAGES if s["id"] == stage_id), None)
        if not stage or set(body.checked) != set(stage["checks"]):
            raise ValueError("Review every checkpoint for this stage before recording a decision")
        with workspace.transaction():
            record = workspace.create_record("decision", f"Stage review · {stage['title']}", body.note,
                                             metadata={"workflow_stage": stage_id, "checked": body.checked,
                                                       "reviewer": body.reviewer}, links=body.links)
            return workspace.review_record(record["id"], expected_revision=record["revision"],
                                             decision="approved", reviewer=body.reviewer, note=body.note)

    @app.get("/api/export.json")
    def export_json():
        return Response(json.dumps(workspace.export_bundle(), indent=2, ensure_ascii=False),
                        media_type="application/json", headers={"Content-Disposition": 'attachment; filename="scientist-os-handoff.json"'})

    @app.get("/api/export.md")
    def export_markdown():
        return Response(markdown_export(workspace), media_type="text/markdown",
                        headers={"Content-Disposition": 'attachment; filename="scientist-os-handoff.md"'})

    from .authoring_api import register_authoring
    register_authoring(app, workspace)
    return app
