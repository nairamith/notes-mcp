# API Contract: Move and Remove a Note

Two MCP tools. `move_note` is a thin wrapper around one
`notes_mcp.apple.core` backend function; `remove_note` composes two
existing backend functions directly (`mkdir` + `mv`) rather than wrapping
a single one — see the `remove_note` section below for why (amendment,
research.md §2). See
[apple_core_api.md](../../002-apple-notes-core-ops/contracts/apple_core_api.md)
for the full backend contract). Input/output shapes follow the same
verified-against-the-real-SDK rules established in
[003-notes-mcp-tools/contracts/mcp_tools_api.md](../../003-notes-mcp-tools/contracts/mcp_tools_api.md)
(§2-4 of that feature's research.md): a `Note` return type is **not**
wrapped in `{"result": ...}` — its fields are the structured content
directly.

## Error behavior (both tools)

Any exception raised by the underlying `apple.core` call — `NotFoundError`
or the `AppleNotesError` base — is automatically converted by the SDK
into a `CallToolResult` with `isError: true` and a text content of the
form `"Error executing tool {tool_name}: {message}"`. The server process
never crashes on a tool error.

## `move_note(note_id: str, destination_folder_path: str, new_name: str | None = None) -> Note`

Wraps `apple.core.mv(kind="note", ...)`.

- **Input schema**: `note_id`, `destination_folder_path` — strings,
  required; `new_name` — string or null, optional, default `null` (omit
  to move without renaming).
- **Output**: **Not** wrapped — the structured content is the moved
  `Note` directly: `{"id", "name", "folder_path"}`. `folder_path` is
  `destination_folder_path`; `name` is `new_name` if given, otherwise
  unchanged.
- **Errors**: `NotFoundError` if `note_id` or `destination_folder_path`
  does not exist. Nothing is moved if either is missing.
  `InvalidNameError` if `new_name` is given but empty, whitespace-only, or
  multi-line — also before anything moves (issue #10; previously an empty
  `new_name` was silently ignored).
- Leading/trailing whitespace in `new_name` is trimmed, matching what
  Notes stores and what `create_note`/`update_note` look up (issue #26).
- Moving a note to the folder it's already in succeeds as a no-op with
  respect to its location (research.md §1); if `new_name` is also given,
  the note is renamed in place regardless.
- Renaming keeps the note's content exactly, spaces and tabs included —
  the rename rewrites the note's body, which previously collapsed its
  whitespace (issue #27) — and stores `new_name` verbatim.
- Unlike `create_note`, `move_note` never auto-creates its destination
  folder — the README says so (issue #12).

## `remove_note(note_id: str) -> Note`

Composes `apple.core.mkdir("", "archive")` (swallowing `AlreadyExistsError`)
then `apple.core.mv(kind="note", identifier=note_id,
destination_folder_path="archive")` — directly, at the tool layer,
mirroring `update_note`'s identical archive-on-replace composition
(feature 003). **Does not call `apple.core.rm`.**

`apple.core.rm` is out of scope for this feature entirely and remains
feature 002's original stub (raises `NotImplementedYetError` for both
`kind="note"` and `kind="folder"`) — implementing it for real (matching
what Notes.app's own delete mechanism does) is a separate, future
feature (amendment, research.md §2).

- **Input schema**: `{"note_id": {"type": "string"}}`, required.
- **Output**: **Not** wrapped — the structured content is the resulting
  `Note` directly: `{"id", "name", "folder_path"}`. `folder_path` is
  always `"archive"` afterward; `id`/`name` are unchanged. The archived
  note can subsequently be found via `list_folder_contents("archive")`.
- **Errors**: `NotFoundError` if `note_id` does not exist. Nothing is
  removed in that case.
- Never permanently deletes the note's content — the note continues to
  exist, unchanged, at the well-known `archive` location (FR-005).
- Removing a note already located in `archive` succeeds as a no-op with
  respect to its location (research.md §3) — not an error, and does not
  duplicate the note.
- Folders are out of scope: this tool only ever composes note-kind
  `mkdir`/`mv` calls.
