# notes-mcp

An MCP (Model Context Protocol) server for interacting with Apple Notes.

The server talks to Notes.app on macOS via JavaScript for Automation (JXA)
and exposes seven tools over MCP:

- `list_folder_contents(folder_path)` — the notes and subfolders directly
  inside a folder
- `search_notes(pattern, folder_path=None)` — notes whose content matches a
  regular expression, optionally scoped to a folder
- `read_note(note_id)` — a note's content
- `create_note(folder_path, name, content)` — create a new note
- `update_note(folder_path, name, content, overwrite=False)` — append to an
  existing note (creating it if missing), or, with `overwrite=True`, archive
  the existing note into a top-level `archive` folder and create a fresh
  replacement
- `move_note(note_id, destination_folder_path, new_name=None)` — move a note
  to a different folder, optionally renaming it in the same call
- `remove_note(note_id)` — remove a note by archiving it into the same
  top-level `archive` folder (never a permanent delete)

## Prerequisites

- macOS, with Notes.app configured and its Automation permission granted to
  whatever process runs this server (System Settings -> Privacy & Security ->
  Automation)
- Python 3.11+

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the server

```bash
python -m notes_mcp.server
```

The process starts and waits on stdio for an MCP client to connect — this is
expected; it will not print further output until a client interacts with it.

## Verify

Run the automated test suite:

```bash
pytest tests/unit/ tests/contract/    # mocked backend + schema checks — always run
pytest tests/integration/             # real Notes.app; auto-skips off-macOS or
                                       # without Notes.app/permission
```

To call a tool manually, use the MCP Inspector (bundled with the `mcp` SDK's
CLI extra). The Inspector requires **Node.js 18+** and, by default, launches
the server via [`uv`](https://docs.astral.sh/uv/) — install both if you don't
already have them (`node --version` / `uv --version` to check; older Node
versions fail with a `node:fs/promises` import error):

```bash
pip install "mcp[cli]"
mcp dev src/notes_mcp/server.py
```

This opens the MCP Inspector in a browser. Connect, list tools, and invoke
`list_folder_contents` with a real top-level folder name from your own Notes
account, e.g. `{"folder_path": "Notes"}`. It should return that folder's
actual subfolders and notes — this tool (like all seven) talks to your real
Notes data, not stubbed output.

## Project layout

```text
src/notes_mcp/
├── server.py                  # FastMCP server instance, stdio entrypoint, tool registration
├── apple/
│   ├── core.py                # backend: ls, grep, mkdir, mv, rm, cat, append
│   │                          #   (rm implements real removal for notes —
│   │                          #    archives via mkdir+mv; folders remain
│   │                          #    an unimplemented stub)
│   ├── exceptions.py          # exception hierarchy raised by core.py
│   ├── schema.py               # Note/Folder/FolderListing data shapes
│   └── jxa_scripts/            # one JXA script per backend operation
└── tools/
    ├── list_folder_contents.py # wraps apple.core.ls
    ├── search_notes.py         # wraps apple.core.grep
    ├── read_note.py            # wraps apple.core.cat
    ├── create_note.py          # wraps apple.core.append
    ├── update_note.py          # wraps apple.core.append; overwrite=True also
    │                            # composes ls/mkdir/mv to archive-then-replace
    ├── move_note.py             # wraps apple.core.mv (note path)
    └── remove_note.py           # wraps apple.core.rm (note path)

tests/
├── contract/                   # MCP tool contract tests (schema/registration)
├── unit/                       # unit tests (mocked backend)
└── integration/                # tests against real Notes.app
```

See `specs/` for each feature's spec, plan, and other design documents.
