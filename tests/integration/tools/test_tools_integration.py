"""End-to-end integration test for all five MCP tools against real
Notes.app, called as real MCP tools over stdio (matching how
001-mcp-server-scaffold's own tests exercise the server).

Runs entirely inside a dedicated, disposable `scratch_folder` (see
conftest.py), except for update_note's overwrite=True path, whose archived
copy necessarily lands in the single, fixed, top-level "archive" folder
(by design, spec Assumptions) — that one note is cleaned up explicitly via
delete_note_by_id, never the scratch folder's own teardown.
"""

import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = pytest.mark.usefixtures("skip_without_notes")

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "notes_mcp.server"],
)


async def test_all_five_tools_end_to_end(scratch_folder, delete_note_by_id):
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            created = await session.call_tool(
                "create_note",
                {"folder_path": scratch_folder, "name": "integration-note", "content": "hello"},
            )
            assert not created.isError
            note_id = created.structuredContent["id"]

            read_back = await session.call_tool("read_note", {"note_id": note_id})
            assert read_back.structuredContent["result"] == "hello"

            await session.call_tool(
                "update_note",
                {"folder_path": scratch_folder, "name": "integration-note", "content": "world"},
            )
            read_back2 = await session.call_tool("read_note", {"note_id": note_id})
            assert read_back2.structuredContent["result"] == "hello\nworld"

            found = await session.call_tool("search_notes", {"pattern": "hello|world", "folder_path": scratch_folder})
            assert any(n["id"] == note_id for n in found.structuredContent["result"])

            listing = await session.call_tool("list_folder_contents", {"folder_path": scratch_folder})
            assert "integration-note" in [n["name"] for n in listing.structuredContent["notes"]]

            replaced = await session.call_tool(
                "update_note",
                {
                    "folder_path": scratch_folder,
                    "name": "integration-note",
                    "content": "fresh-start",
                    "overwrite": True,
                },
            )
            assert not replaced.isError
            new_note_id = replaced.structuredContent["id"]
            try:
                read_back3 = await session.call_tool("read_note", {"note_id": new_note_id})
                assert read_back3.structuredContent["result"] == "fresh-start"

                archived = await session.call_tool("list_folder_contents", {"folder_path": "archive"})
                archived_names = [n["name"] for n in archived.structuredContent["notes"]]
                assert "integration-note" in archived_names

                old_content = await session.call_tool("read_note", {"note_id": note_id})
                assert old_content.structuredContent["result"] == "hello\nworld"
            finally:
                # The archived copy (the original "integration-note", now
                # under "archive") is the only note this test leaves behind
                # outside scratch_folder's own recursive teardown.
                delete_note_by_id(note_id)
