# Data Model: Apple Notes MCP Tools

No new entities. This feature re-exposes the entities already defined by
the backend (`specs/002-apple-notes-core-ops/data-model.md`) directly over
MCP, unchanged:

- **Note** — `id`, `name`, `folder_path` (metadata only; content is read
  separately via `read_note`).
- **Folder** — `name`, `path`, `parent_path`.
- **FolderListing** — `folders: list[Folder]`, `notes: list[Note]`; the
  return shape of `list_folder_contents`.

See [contracts/mcp_tools_api.md](./contracts/mcp_tools_api.md) for exactly
how each shape appears in a tool's structured MCP response (some are
wrapped under a `result` key, some are not — see research.md §4).

## Archive location (amendment)

Not a new entity type — just an ordinary `Folder` (see above), at the
fixed top-level path `archive`. Created automatically, the first time
`update_note`'s replacement mode needs it, by the tool itself (research.md
§8). Notes moved there by that mode keep all their existing `Note` fields
unchanged (`id`, `name`, `content`) — only `folder_path` changes, to
`archive`.

## Retired

The placeholder `Folder` pydantic model defined in the now-removed
`src/notes_mcp/tools/list_folders.py` (feature 001) is retired along with
that tool (FR-011). It only ever carried stub data and is superseded by
the backend's real `Folder` dataclass.
