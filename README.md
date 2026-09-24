# notes-mcp

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

A local [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server that gives AI assistants like Claude direct access to Apple Notes on macOS — list, search, read, create, update, move, and remove notes, without leaving your terminal or IDE.

The server talks to Notes.app via JavaScript for Automation (JXA); your notes never leave your machine.

## Features

- `list_folder_contents(folder_path)` — the notes and subfolders directly inside a folder; pass `""` to list the top-level folders
- `search_notes(pattern, folder_path=None)` — notes whose content matches a regular expression, optionally scoped to a folder
- `read_note(note_id)` — a note's content
- `create_note(folder_path, name, content)` — create a new note
- `update_note(folder_path, name, content, overwrite=False)` — append to an existing note (creating it if missing), or, with `overwrite=True`, archive the existing note and create a fresh replacement
- `move_note(note_id, destination_folder_path, new_name=None)` — move a note to a different folder, optionally renaming it in the same call
- `remove_note(note_id)` — remove a note by archiving it (never a permanent delete)

## Requirements

- macOS, with Notes.app configured
- Python 3.11+

## Installation

```bash
git clone https://github.com/nairamith/notes-mcp.git
cd notes-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

The first time a tool is called, macOS will prompt you to grant Automation permission for Notes — accept it (or grant it in advance via **System Settings → Privacy & Security → Automation**).

## Adding notes-mcp to Claude

The server communicates over stdio, so any MCP-compatible client can launch it directly. Use the **absolute path** to the Python interpreter inside the virtual environment you just created — `<repo>/.venv/bin/python`.

### Claude Code

```bash
claude mcp add notes-mcp -s user -- /absolute/path/to/notes-mcp/.venv/bin/python -m notes_mcp.server
```

`-s user` registers it globally so it's available in every project; use `-s project` instead to share it via that project's `.mcp.json`, or omit the flag for the current project only. Run `/mcp` inside Claude Code afterward to confirm it connected.

### Claude Desktop

Add an entry to `~/Library/Application Support/Claude/claude_desktop_config.json` (create the file if it doesn't exist):

```json
{
  "mcpServers": {
    "notes-mcp": {
      "command": "/absolute/path/to/notes-mcp/.venv/bin/python",
      "args": ["-m", "notes_mcp.server"]
    }
  }
}
```

Restart Claude Desktop, then check **Settings → Connectors** to confirm `notes-mcp` is connected.

## Verify it's working

Run the automated test suite:

```bash
pip install -e ".[dev]"
pytest tests/unit/ tests/contract/    # mocked backend + schema checks — always run
pytest tests/integration/             # real Notes.app; auto-skips off-macOS or
                                       # without Notes.app/permission
```

To exercise a tool manually without a full MCP client, use the MCP Inspector (bundled with the `mcp` SDK's CLI extra). It requires **Node.js 18+** and, by default, launches the server via [`uv`](https://docs.astral.sh/uv/) — install both if you don't already have them:

```bash
pip install "mcp[cli]"
mcp dev src/notes_mcp/server.py
```

This opens the MCP Inspector in a browser. Connect, list tools, and invoke `list_folder_contents` with a real top-level folder name from your own Notes account, e.g. `{"folder_path": "Notes"}` — it talks to your real Notes data, not stubbed output.

## Contributing

Issues and pull requests are welcome. This project was built using [spec-kit](https://github.com/github/spec-kit)'s spec-driven workflow — see `specs/` for each feature's spec, plan, and design decisions, and `.specify/memory/constitution.md` for the project's guiding principles (YAGNI, test-first, safe/reversible data operations).

## License

[MIT](LICENSE)
