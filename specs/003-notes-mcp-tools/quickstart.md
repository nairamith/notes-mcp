# Quickstart: Apple Notes MCP Tools

Validates User Stories 1-5 end-to-end: `list_folder_contents`,
`search_notes`, `read_note`, `create_note`, `update_note`, called as real
MCP tools over stdio against real Notes.app.

## Prerequisites

- Same as `002-apple-notes-core-ops`: macOS, Python 3.11+, Notes.app with
  Automation permission already granted (one-time, see that feature's
  quickstart if not yet done).
- No new dependencies to install.

## Setup

```bash
source .venv/bin/activate
```

## Run the automated tests

```bash
pytest tests/unit/tools/           # mocked apple.core — always runs
pytest tests/integration/tools/    # real Notes; auto-skips off-macOS or
                                    # without Notes.app/permission
pytest tests/contract/             # server registration + schema checks
```

Expected: all pass. Integration tests run against a dedicated, disposable
scratch folder (shared fixture with the backend's own integration tests)
— never your real personal folders.

## Manually validate over real stdio

From a Python shell, using the real MCP client (matching how
`001-mcp-server-scaffold`'s tests exercise the server):

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["-m", "notes_mcp.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])
            # Expect: list_folder_contents, search_notes, read_note,
            # create_note, update_note — and NOT list_folders (retired).

            listing = await session.call_tool("list_folder_contents", {"folder_path": "Notes"})
            print(listing.structuredContent)

            created = await session.call_tool(
                "create_note",
                {"folder_path": "Notes", "name": "quickstart-note", "content": "hello"},
            )
            print(created.structuredContent)

            note_id = created.structuredContent["id"]
            read_back = await session.call_tool("read_note", {"note_id": note_id})
            assert read_back.structuredContent["result"] == "hello"

            await session.call_tool(
                "update_note",
                {"folder_path": "Notes", "name": "quickstart-note", "content": "world"},
            )
            read_back2 = await session.call_tool("read_note", {"note_id": note_id})
            assert read_back2.structuredContent["result"] == "hello\nworld"

            found = await session.call_tool("search_notes", {"pattern": "hello|world"})
            assert any(n["id"] == note_id for n in found.structuredContent["result"])

            # US5 (amendment): overwrite=True archives the original, then
            # creates a fresh note with only the new content.
            replaced = await session.call_tool(
                "update_note",
                {"folder_path": "Notes", "name": "quickstart-note", "content": "fresh-start", "overwrite": True},
            )
            new_note_id = replaced.structuredContent["id"]
            read_back3 = await session.call_tool("read_note", {"note_id": new_note_id})
            assert read_back3.structuredContent["result"] == "fresh-start"

            archived = await session.call_tool("list_folder_contents", {"folder_path": "archive"})
            archived_names = [n["name"] for n in archived.structuredContent["notes"]]
            assert "quickstart-note" in archived_names  # original, with "hello\nworld", preserved here

            old_content = await session.call_tool("read_note", {"note_id": note_id})
            assert old_content.structuredContent["result"] == "hello\nworld"  # untouched by the replace

            print("ALL TOOL CALLS SUCCEEDED — clean up quickstart-note (both copies) manually afterward")

asyncio.run(main())
```

Expected: tool list matches FR-011 (no `list_folders`); `create_note` then
`read_note` round-trips exactly (SC-003); `update_note` (default mode)
preserves prior content (SC-004); `search_notes` finds the note;
`update_note` with `overwrite=True` archives the original note intact into
the auto-created `archive` folder and creates a fresh replacement (SC-005).

## Clean up

Manually remove the `quickstart-note` note(s) created above from Notes.app
— one at its original location, one under `archive` after the overwrite
step — plus the `archive` folder itself if you don't want to keep it.
`rm` isn't wired to any tool in this feature, by design (spec Assumptions).
