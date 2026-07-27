# Quickstart: Move and Remove a Note

Validates User Stories 1-2: `move_note`, `remove_note`, called as real MCP
tools over stdio against real Notes.app.

## Prerequisites

- Same as prior features: macOS, Python 3.11+, Notes.app with Automation
  permission already granted.
- No new dependencies to install.

## Setup

```bash
source .venv/bin/activate
```

## Run the automated tests

```bash
pytest tests/unit/ tests/contract/    # mocked backend + schema checks — always run
pytest tests/integration/             # real Notes.app; auto-skips off-macOS or
                                        # without Notes.app/permission
```

Expected: all pass. Integration tests run against a dedicated, disposable
scratch folder — never your real personal folders.

## Manually validate over real stdio

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
            # Expect: move_note, remove_note among the tool names.

            created = await session.call_tool(
                "create_note",
                {"folder_path": "Notes", "name": "quickstart-move-remove", "content": "hello"},
            )
            note_id = created.structuredContent["id"]

            # move_note: relocate and rename in one call
            moved = await session.call_tool(
                "move_note",
                {"note_id": note_id, "destination_folder_path": "Notes", "new_name": "quickstart-moved"},
            )
            assert moved.structuredContent["name"] == "quickstart-moved"
            assert moved.structuredContent["folder_path"] == "Notes"

            # remove_note: archives it
            removed = await session.call_tool("remove_note", {"note_id": note_id})
            assert removed.structuredContent["folder_path"] == "archive"

            archived = await session.call_tool("list_folder_contents", {"folder_path": "archive"})
            archived_names = [n["name"] for n in archived.structuredContent["notes"]]
            assert "quickstart-moved" in archived_names

            content = await session.call_tool("read_note", {"note_id": note_id})
            assert content.structuredContent["result"] == "hello"  # untouched by move/remove

            print("ALL TOOL CALLS SUCCEEDED — clean up quickstart-moved from archive manually afterward")

asyncio.run(main())
```

Expected: `move_note` relocates and renames in a single call (SC-001);
`remove_note` archives the note into the well-known `archive` folder
without altering its content (SC-002); both surface a clear error for a
missing note_id or destination folder rather than crashing (SC-003).

## Clean up

Manually remove the `quickstart-moved` note from Notes.app's `archive`
folder afterward.
