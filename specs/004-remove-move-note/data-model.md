# Data Model: Move and Remove a Note

No new entities. This feature re-exposes existing backend capabilities
(`specs/002-apple-notes-core-ops/data-model.md`) over MCP:

- **Note** — `id`, `name`, `folder_path`. Both tools in this feature
  return a `Note` (the moved note, or the removed/archived note).

## Archive location (reused, not new)

Not a new entity — the exact same well-known, top-level `Folder` at path
`archive` already established in
`specs/003-notes-mcp-tools/data-model.md` for `update_note`'s replacement
mode. `remove_note` is this feature's second real consumer of that same
location: it auto-creates it (if not already present) the same way, via
`apple.core.mkdir("", "archive")`, and moves notes into it unchanged
(`id`/`name` preserved, only `folder_path` becomes `"archive"`).

There remains exactly one canonical archive location for the whole
project — this feature does not introduce a second one, and does not
distinguish "archived via replacement" from "archived via removal" at the
data level; both land in the same folder, indistinguishable from each
other once there.
