# Quickstart: MCP Server Scaffold with Dummy list_folders Tool

Validates User Stories 1–3 end-to-end: the server starts, `list_folders`
responds with the stubbed data, and these steps alone (no source reading
required) are enough to prove it.

## Prerequisites

- macOS
- Python 3.11+
- A clone of this repository

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the automated tests

```bash
pytest
```

Expected: all tests pass, including the `list_folders` contract test
described in [contracts/list_folders.md](./contracts/list_folders.md).

## Run the server (User Story 1)

```bash
python -m notes_mcp.server
```

Expected: the process starts and waits on stdio for an MCP client — no
errors printed. It is now ready for a client to connect and request the
tool list, which MUST include `list_folders`.

## Call list_folders through an MCP client (User Story 2)

Using the MCP Inspector (bundled with the `mcp` SDK's CLI extra) is the
fastest way to call the tool manually without configuring a full client:

```bash
pip install "mcp[cli]"
mcp dev src/notes_mcp/server.py
```

This opens the MCP Inspector in a browser. Connect, list tools, and invoke
`list_folders` with an empty input.

Expected response (see [data-model.md](./data-model.md) for the full
schema):

```json
[
  {"id": "1", "name": "Notes"},
  {"id": "2", "name": "Personal"},
  {"id": "3", "name": "Work"}
]
```

Calling it multiple times MUST return the same three entries every time.

## Validate against the README (User Story 3)

Follow `README.md` from a fresh clone, without referring back to this file,
and confirm you can reach the same "server running, `list_folders`
responds" outcome in under 5 minutes (Success Criterion SC-001).
