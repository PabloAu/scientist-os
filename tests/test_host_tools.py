import asyncio
import json
import sys

import pytest

from scientist_os.host_cli import create_host_server
from scientist_os.host_tools import HostTools
from scientist_os.workspace import Workspace


def test_connection_roots_cannot_be_expanded_by_operation_arguments(tmp_path):
    research = tmp_path / "research"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.txt").write_text("private")
    workspace = Workspace(research)
    host = HostTools(workspace)
    with pytest.raises(ValueError, match="permitted roots"):
        host.call("ingest.folder", {"permitted_root": str(outside)})
    assert workspace.list_runs()[-1]["status"] == "failed"
    assert workspace.list_records() == []


def test_conversation_edit_exports_preserve_history_and_reject_stale_evidence(tmp_path):
    workspace = Workspace(tmp_path)
    host = HostTools(workspace)
    source = workspace.create_record("source", "Source", "Fictional data")
    draft = host.call("manuscript.create", {"title": "Report", "sections": [
        {"title": "Results", "text": "A descriptive difference was observed."}],
        "source_ids": [source["id"]], "reports": {"claims": "Descriptive fixture only"}})
    exported = host.call("artifact.export", {"record_id": draft["id"], "format": "docx"})
    revised = host.call("manuscript.revise", {"record_id": draft["id"],
        "expected_revision": draft["revision"], "section_id": draft["metadata"]["sections"][0]["id"],
        "selected_text": "A descriptive difference was observed.",
        "replacement": "The fictional difference does not establish a causal effect.",
        "reason": "Clarify uncertainty", "attributed_to": "test agent"})
    assert revised["review_status"] == "unreviewed"
    assert revised["metadata"]["last_conversational_edit"]["scientific_approval"] is False
    assert __import__("pathlib").Path(exported["path"]).exists()
    with pytest.raises(RuntimeError, match="changed"):
        host.call("manuscript.revise", {"record_id": draft["id"],
            "expected_revision": draft["revision"], "section_id": draft["metadata"]["sections"][0]["id"],
            "selected_text": "A descriptive difference was observed.", "replacement": "Wrong",
            "reason": "Stale editor", "attributed_to": "test agent"})
    workspace.update_record(source["id"], expected_revision=1, content="Contradictory fixture data")
    with pytest.raises(RuntimeError):
        host.call("artifact.export", {"record_id": draft["id"], "format": "docx"})


def test_host_mcp_exposes_actions_and_full_metadata(tmp_path):
    pytest.importorskip("mcp")
    workspace = Workspace(tmp_path)
    host = HostTools(workspace)
    server = create_host_server(host)
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert {"analysis_run", "ingest_folder", "manuscript_create", "task_recover", "meta_synthesize"} <= names
    assert "review_record" not in names


def test_real_host_stdio_can_create_discover_and_update(tmp_path):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=[
            "-m", "scientist_os.host_cli", "--workspace", str(tmp_path), "mcp"])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                created = await client.call_tool("record_create", {"arguments": {
                    "kind": "dataset", "title": "Fictional measurements", "content": "x\n1\n",
                    "metadata": {"units": "nm", "independence_unit": "preparation"}}})
                assert not created.isError
                record = json.loads(created.content[0].text)
                read_result = await client.call_tool("record_read", {"arguments": {"record_id": record["id"]}})
                actual = json.loads(read_result.content[0].text)
                assert actual["metadata"]["units"] == "nm"
                assert actual["review_status"] == "unreviewed"
                updated = await client.call_tool("record_update", {"arguments": {
                    "record_id": record["id"], "expected_revision": 1, "content": "x\n2\n"}})
                assert not updated.isError
                assert json.loads(updated.content[0].text)["revision"] == 2
    asyncio.run(exercise())
