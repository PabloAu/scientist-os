"""MCP scope, human-review boundary, and a real stdio SDK round trip."""

import asyncio
import json
import sys

import pytest

from scientist_os.agent import AgentError
from scientist_os.mcp_server import MCPBridge, create_server
from scientist_os.workspace import Workspace


@pytest.fixture
def records(tmp_path):
    root = tmp_path / "workspace"
    workspace = Workspace(root)
    record = workspace.create_record("source", "Synthetic study", "Observed 4 arbitrary units.")
    private = workspace.create_record("source", "Private source", "TOP_SECRET")
    return root, workspace, record, private


def citation(record):
    return {"record_id": record["id"], "quote": record["content"], "sha256": record["sha256"]}


def test_unknown_host_requires_source_disclosure_opt_in(records):
    _, workspace, record, _ = records
    with pytest.raises(AgentError, match="external_disclosure_not_allowed"):
        MCPBridge(workspace, [record["id"]])
    record = workspace.update_record(record["id"], expected_revision=record["revision"], metadata={"external_allowed": True})
    bridge = MCPBridge(workspace, [record["id"]])
    assert bridge.read_record(record["id"])["record"]["content"] == record["content"]
    packet = bridge.agent_packet("What was observed?")
    assert packet["disclosure_policy"] == "all_sources_external_allowed"
    assert len(packet["selected_sources"]) == 1


def test_mcp_selected_scope_blocks_private_read_and_search(records):
    _, workspace, record, private = records
    bridge = MCPBridge(workspace, [record["id"]], local_client=True)
    with pytest.raises(AgentError, match="source_outside_selection"):
        bridge.read_record(private["id"])
    assert bridge.search_records("TOP_SECRET")["records"] == []
    with pytest.raises(TypeError):
        bridge.search_records("TOP_SECRET", source_ids=[private["id"]])
    assert "TOP_SECRET" not in json.dumps(bridge.agent_packet("Question"))


def test_mcp_submits_quote_checked_unapproved_run_with_trace(records):
    _, workspace, record, _ = records
    bridge = MCPBridge(workspace, [record["id"]], local_client=True)
    bridge.agent_packet("Interpret", "experiment", "Brief scientific style")
    bridge.read_record(record["id"])
    run = bridge.submit_proposal("Interpret", "A proposed follow-up needs a control.", [citation(record)], task="experiment")
    assert run["status"] == "needs_review" and run["review_status"] == "unreviewed"
    assert run["requests"] is None and run["usage"] is None
    assert run["provider"] == "mcp-client" and run["grounding"] == "verified_quotes"
    assert [event["name"] for event in run["trace"]] == ["agent_packet", "read_record", "submit_proposal"]
    assert workspace.get_run(run["id"]) == run
    assert workspace.get_record(record["id"])["review_status"] == "unreviewed"
    assert bridge.trace == []


def test_mcp_invalid_or_stale_submission_is_persisted_failed(records):
    _, workspace, record, _ = records
    bridge = MCPBridge(workspace, [record["id"]], local_client=True)
    wrong = citation(record)
    wrong["quote"] = "Manufactured evidence"
    run = bridge.submit_proposal("Question", "Claim", [wrong])
    assert run["status"] == "failed" and run["error"]["code"] == "citation_quote_mismatch"
    workspace.update_record(record["id"], expected_revision=record["revision"], content="Revised observation")
    run = bridge.submit_proposal("Question", "Claim", [citation(record)])
    assert run["status"] == "failed" and run["error"]["code"] == "source_changed"
    assert len(workspace.list_runs()) == 2
    with pytest.raises(AgentError, match="source_changed"):
        bridge.read_record(record["id"])


def test_mcp_revalidates_disclosure_for_every_read_and_packet(records):
    _, workspace, record, _ = records
    record = workspace.update_record(record["id"], expected_revision=record["revision"], metadata={"external_allowed": True})
    bridge = MCPBridge(workspace, [record["id"]])
    bridge.read_record(record["id"])
    workspace.update_record(record["id"], expected_revision=record["revision"], metadata={"external_allowed": False})
    with pytest.raises(AgentError, match="source_changed"):
        bridge.agent_packet("Question")


def test_mcp_no_citation_is_unsupported_and_operations_are_bounded(records):
    _, workspace, record, _ = records
    bridge = MCPBridge(workspace, [record["id"]], local_client=True)
    run = bridge.submit_proposal("Question", "Uncited suggestion", [])
    assert run["grounding"] == "unsupported" and run["answer"].startswith("Unsupported")
    bridge.operations = bridge.MAX_SESSION_OPERATIONS
    with pytest.raises(AgentError, match="mcp_session_operation_limit"):
        bridge.read_record(record["id"])
    run = bridge.submit_proposal("Question", "Claim", [citation(record)])
    assert run["status"] == "failed" and run["error"]["code"] == "mcp_session_operation_limit"


def test_mcp_large_unicode_traces_fail_safely_and_remain_persistable(records):
    _, workspace, record, _ = records
    record = workspace.update_record(record["id"], expected_revision=record["revision"], content="\u79d1" * 24000)
    bridge = MCPBridge(workspace, [record["id"]], local_client=True)
    with pytest.raises(AgentError, match="mcp_trace_size_limit"):
        for _ in range(20):
            bridge.read_record(record["id"])
    run = bridge.submit_proposal("Question", "Claim", [citation(record)])
    assert run["error"]["code"] == "mcp_trace_size_limit"
    assert workspace.get_run(run["id"])["status"] == "failed"


@pytest.mark.parametrize("text", ["Bad\x00text", "Bad\ud800text"])
def test_mcp_invalid_text_submissions_persist_safe_failures(records, text):
    _, workspace, record, _ = records
    bridge = MCPBridge(workspace, [record["id"]], local_client=True)
    run = bridge.submit_proposal("Question", text, [])
    assert run["status"] == "failed" and run["error"]["code"] == "invalid_answer"
    assert workspace.get_run(run["id"])["status"] == "failed"
    run = bridge.submit_proposal(text, "Answer", [])
    assert run["status"] == "failed" and run["error"]["code"] == "invalid_question"
    assert run["question"] == "[invalid text]"


def test_sdk_exposes_only_four_bounded_tools(records):
    pytest.importorskip("mcp")
    _, workspace, record, _ = records
    server = create_server(workspace, [record["id"]], local_client=True)
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {"search_records", "read_record", "agent_packet", "submit_proposal"}
    read = next(tool for tool in tools if tool.name == "read_record")
    assert set(read.inputSchema["properties"]) == {"record_id"}
    submit = next(tool for tool in tools if tool.name == "submit_proposal")
    assert "reviewer" not in submit.inputSchema["properties"] and "approved" not in submit.inputSchema["properties"]
    assert submit.annotations.readOnlyHint is False


def test_real_stdio_client_can_read_and_submit_but_not_approve(records):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    root, workspace, record, private = records

    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=[
            "-m", "scientist_os.mcp_server", "--workspace", str(root), "--source", record["id"], "--local-client",
        ])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                listed = await client.list_tools()
                assert len(listed.tools) == 4
                result = await client.call_tool("read_record", {"record_id": record["id"]})
                assert not result.isError
                data = json.loads(result.content[0].text)
                assert data["record"]["sha256"] == record["sha256"]
                refused = await client.call_tool("read_record", {"record_id": private["id"]})
                assert refused.isError
                refused = await client.call_tool("review_record", {"record_id": record["id"], "decision": "approved"})
                assert refused.isError
                result = await client.call_tool("submit_proposal", {
                    "question": "Interpret", "answer": "Proposed interpretation", "citations": [citation(record)],
                })
                assert not result.isError
                submitted = json.loads(result.content[0].text)
                assert submitted["status"] == "needs_review"
                return submitted["id"]

    run_id = asyncio.run(asyncio.wait_for(exercise(), timeout=25))
    assert workspace.get_run(run_id)["review_status"] == "unreviewed"
