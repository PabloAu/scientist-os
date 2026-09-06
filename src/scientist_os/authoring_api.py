"""Local authoring HTTP interface; all evidence decisions live in the domain modules."""

import os
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ManuscriptInput(Input):
    title: str = Field(min_length=1, max_length=300)
    sections: list[dict] | None = None
    external_allowed: bool = False


class ManuscriptUpdate(Input):
    expected_revision: int = Field(ge=1)
    title: str | None = None
    sections: list[dict] | None = None
    external_allowed: bool | None = None


class PassageInput(Input):
    expected_revision: int = Field(ge=1)
    section_id: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    selected_text: str = Field(max_length=5000)
    instruction: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(min_length=1, max_length=16)
    style: str = Field(default="", max_length=2000)
    max_steps: int = Field(default=8, ge=1, le=8)
    provider: Literal["demo", "configured"] = "demo"


class ApplyInput(Input):
    expected_revision: int = Field(ge=1)
    reviewer: str = Field(min_length=1, max_length=120)
    replacement: str | None = Field(default=None, max_length=16000)
    note: str = Field(default="", max_length=5000)


class ReferenceInput(Input):
    title: str = Field(min_length=1, max_length=300)
    authors: list[str] | None = None
    year: int | None = None
    doi: str = ""
    url: str = ""
    journal: str = ""
    abstract: str = ""
    full_text_ids: list[str] | None = None
    external_allowed: bool = False


class ReferenceUpdate(Input):
    expected_revision: int = Field(ge=1)
    title: str | None = None
    authors: list[str] | None = None
    year: int | None = None
    doi: str | None = None
    url: str | None = None
    journal: str | None = None
    abstract: str | None = None
    full_text_ids: list[str] | None = None
    external_allowed: bool | None = None


class DiscussionInput(Input):
    title: str = Field(min_length=1, max_length=300)
    focus: str = Field(default="", max_length=2000)
    external_allowed: bool = False


class TurnInput(Input):
    expected_revision: int = Field(ge=1)
    question: str = Field(min_length=1, max_length=3000)
    source_ids: list[str] = Field(min_length=1, max_length=16)
    author: str = Field(min_length=1, max_length=120)
    include_turn_ids: list[str] | None = Field(default=None, max_length=5)
    style: str = Field(default="", max_length=2000)
    max_steps: int = Field(default=8, ge=1, le=8)
    provider: Literal["demo", "configured"] = "demo"


class PresentationInput(Input):
    title: str = Field(min_length=1, max_length=300)
    slides: list[dict] = Field(min_length=1, max_length=40)
    source_ids: list[str] | None = None


class PresentationUpdate(PresentationInput):
    expected_revision: int = Field(ge=1)


class LiteratureInput(Input):
    query: str = Field(min_length=2, max_length=300)


class ExcerptInput(Input):
    expected_revision: int = Field(ge=1)
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    selected_text: str = Field(min_length=1, max_length=20000)
    title: str = Field(min_length=1, max_length=300)
    external_allowed: bool = False


def get_provider(name: str):
    from .providers import DemoProvider, OpenAICompatibleProvider
    if name == "demo":
        return DemoProvider()
    if name != "configured":
        raise ValueError("Unknown provider")
    if not os.getenv("SCIENTIST_OS_MODEL") or not os.getenv("SCIENTIST_OS_BASE_URL"):
        raise ValueError("Configure a model on the server first; see the provider guide")
    return OpenAICompatibleProvider(base_url=os.environ["SCIENTIST_OS_BASE_URL"],
                                  model=os.environ["SCIENTIST_OS_MODEL"],
                                  api_key=os.getenv("SCIENTIST_OS_API_KEY"))


def register_authoring(app: FastAPI, workspace):
    from . import publishing, studio
    from .literature import search_literature

    @app.post("/api/demo/authoring")
    def authoring_demo():
        from .authoring_demo import seed_authoring_demo
        return {"records": seed_authoring_demo(workspace)}

    @app.post("/api/manuscripts", status_code=201)
    def manuscript(body: ManuscriptInput):
        return studio.create_manuscript(workspace, **body.model_dump())

    @app.patch("/api/manuscripts/{record_id}")
    def edit_manuscript(record_id: str, body: ManuscriptUpdate):
        return studio.update_manuscript(workspace, record_id, **body.model_dump(exclude_none=True))

    @app.post("/api/manuscripts/{record_id}/proposals")
    def passage(record_id: str, body: PassageInput):
        return studio.propose_passage(workspace, get_provider(body.provider), record_id,
                                      **body.model_dump(exclude={"provider"}))

    @app.post("/api/manuscripts/{record_id}/proposals/{proposal_id}/apply")
    def apply(record_id: str, proposal_id: str, body: ApplyInput):
        return studio.apply_passage(workspace, record_id, proposal_id, **body.model_dump())

    @app.post("/api/references", status_code=201)
    def reference(body: ReferenceInput):
        return studio.create_reference(workspace, **body.model_dump())

    @app.patch("/api/references/{record_id}")
    def edit_reference(record_id: str, body: ReferenceUpdate):
        return studio.update_reference(workspace, record_id, **body.model_dump(exclude_unset=True))

    @app.post("/api/discussions", status_code=201)
    def discussion(body: DiscussionInput):
        return studio.create_discussion(workspace, **body.model_dump())

    @app.post("/api/discussions/{record_id}/turns")
    def turn(record_id: str, body: TurnInput):
        return studio.discuss(workspace, get_provider(body.provider), record_id,
                              **body.model_dump(exclude={"provider"}))

    @app.post("/api/library/import", status_code=201)
    async def import_document(request: Request, filename: str = Query(min_length=1, max_length=200),
                              title: str = Query(default="", max_length=300),
                              category: str = Query(default="document", max_length=60)):
        if request.headers.get("content-type", "").split(";")[0] != "application/octet-stream":
            raise ValueError("Upload the original file bytes as application/octet-stream")
        return publishing.import_document(workspace, filename=filename,
                                          data=await request.body(), title=title, category=category)

    @app.get("/api/library/{record_id}/download")
    def download(record_id: str):
        from urllib.parse import quote
        data, filename, media_type = publishing.attachment_bytes(workspace, record_id)
        return Response(data, media_type=media_type, headers={
            "Content-Disposition": "attachment; filename*=UTF-8''" + quote(filename, safe="")})

    @app.post("/api/library/{record_id}/excerpts", status_code=201)
    def excerpt(record_id: str, body: ExcerptInput):
        return publishing.create_document_excerpt(workspace, record_id, **body.model_dump())

    @app.post("/api/presentations", status_code=201)
    def presentation(body: PresentationInput):
        return publishing.create_presentation(workspace, **body.model_dump())

    @app.patch("/api/presentations/{record_id}")
    def edit_presentation(record_id: str, body: PresentationUpdate):
        return publishing.update_presentation(workspace, record_id, **body.model_dump())

    @app.get("/api/presentations/{record_id}/export.pptx")
    def presentation_export(record_id: str):
        return Response(publishing.export_presentation(workspace, record_id),
                        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        headers={"Content-Disposition": 'attachment; filename="presentation.pptx"'})

    @app.get("/api/records/{record_id}/publication-figure")
    def publication_figure(record_id: str):
        return Response(publishing.publication_figure(workspace, record_id), media_type="image/png")

    @app.get("/api/manuscripts/{record_id}/export.{format}")
    def manuscript_export(record_id: str, format: Literal["docx", "html"]):
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if format == "docx" else "text/html"
        return Response(publishing.export_manuscript(workspace, record_id, format=format),
                        media_type=mime, headers={"Content-Disposition": f'attachment; filename="manuscript.{format}"'})

    @app.post("/api/literature/search")
    def literature(body: LiteratureInput):
        return search_literature(body.query)
