# notes-mcp

An MCP (Model Context Protocol) server for interacting with Apple Notes.

This is an early scaffold: the server runs and exposes one tool,
`list_folders`, which currently returns a fixed, stubbed list of folders
rather than real data from Notes. Real Apple Notes integration will replace
the stub in a later feature.

## Prerequisites

- macOS
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

## Verify list_folders

Run the automated test suite:

```bash
pytest
```

To call the tool manually, use the MCP Inspector (bundled with the `mcp`
SDK's CLI extra). The Inspector requires **Node.js 18+** and, by default,
launches the server via [`uv`](https://docs.astral.sh/uv/) — install both if
you don't already have them (`node --version` / `uv --version` to check;
older Node versions fail with a `node:fs/promises` import error):

```bash
pip install "mcp[cli]"
mcp dev src/notes_mcp/server.py
```

This opens the MCP Inspector in a browser. Connect, list tools, and invoke
`list_folders` with an empty input (`{}`). It should return:

```json
{
  "result": [
    {"id": "1", "name": "Notes"},
    {"id": "2", "name": "Personal"},
    {"id": "3", "name": "Work"}
  ]
}
```

Calling it again should return the exact same result every time.

## Project layout

```text
src/notes_mcp/
├── server.py            # FastMCP server instance, stdio entrypoint, tool registration
└── tools/
    └── list_folders.py  # list_folders tool: stub data + tool function

tests/
├── contract/            # MCP tool contract tests
└── unit/                # unit tests
```

See `specs/001-mcp-server-scaffold/` for the feature's spec, plan, and other
design documents.
