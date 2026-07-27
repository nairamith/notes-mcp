# API Contract: Apple Notes MCP Tools

Five MCP tools, each a thin wrapper around one `notes_mcp.apple.core`
backend function (see [apple_core_api.md](../../002-apple-notes-core-ops/contracts/apple_core_api.md)
for the full backend contract — exceptions, edge-case behavior, etc. are
inherited unchanged). All input/output shapes below were verified against
the real `mcp` SDK (research.md §2-4), not assumed.

## Error behavior (all five tools)

Any exception raised by the underlying `apple.core` call — `NotFoundError`,
`InvalidPatternError`, `AmbiguousMatchError`, `AutomationPermissionError`,
or the `AppleNotesError` base — is automatically converted by the SDK into
a `CallToolResult` with `isError: true` and a text content of the form
`"Error executing tool {tool_name}: {message}"`, where `{message}` is the
exception's own message (e.g. `No folder named "X" under "Y"`). The server
process never crashes on a tool error.

## `list_folder_contents(folder_path: str) -> FolderListing`

Wraps `apple.core.ls`.

- **Input schema**: `{"folder_path": {"type": "string"}}`, required.
- **Output**: **Not** wrapped in `result` — the structured content is the
  `FolderListing` object directly: `{"folders": [...], "notes": [...]}`,
  where each folder is `{"name", "path", "parent_path"}` and each note is
  `{"id", "name", "folder_path"}`.
- **Errors**: `NotFoundError` if `folder_path` does not exist.
- Read-only (FR-008).

## `search_notes(pattern: str, folder_path: str | None = None) -> list[Note]`

Wraps `apple.core.grep`.

- **Input schema**: `pattern` (string, required), `folder_path` (string or
  null, optional, default `null` — omit to search the whole account).
- **Output**: Wrapped: `{"result": [{"id", "name", "folder_path"}, ...]}`.
  Empty array (`{"result": []}`) when nothing matches — not an error.
- **Errors**: `InvalidPatternError` if `pattern` is not a valid regular
  expression; `NotFoundError` if `folder_path` is given and doesn't exist.
- Read-only (FR-008).

## `read_note(note_id: str) -> str`

Wraps `apple.core.cat`.

- **Input schema**: `{"note_id": {"type": "string"}}`, required.
- **Output**: Wrapped: `{"result": "<the note's content>"}`.
- **Errors**: `NotFoundError` if no note with `note_id` exists.
- Read-only.

## `create_note(folder_path: str, name: str, content: str) -> Note`

Wraps `apple.core.append` (its create-if-missing path is the intended use
here; see the note below on ambiguity).

- **Input schema**: `folder_path`, `name`, `content` — all strings,
  required.
- **Output**: **Not** wrapped — the structured content is the created
  `Note` directly: `{"id", "name", "folder_path"}`.
- **Errors**: `NotFoundError` if `folder_path` doesn't exist;
  `AmbiguousMatchError` if a note named `name` already exists more than
  once in `folder_path` (inherited from `append`'s contract — see note
  below).

## `update_note(folder_path: str, name: str, content: str) -> Note`

Wraps `apple.core.append` (its append-to-existing path is the intended use
here).

- **Input schema**: Identical to `create_note`'s.
- **Output**: Identical shape to `create_note`'s — the resulting `Note`.
- **Errors**: Same as `create_note` — `NotFoundError`, `AmbiguousMatchError`.
- Never overwrites or removes existing content (FR-005); appended content
  is newline-separated from what was already there (inherited from
  `append`'s contract, research.md §6a in feature 002).

**Note on `create_note` vs. `update_note`**: both call the same
`append()` function, which already does the right thing regardless of
whether a note exists yet — `create_note` and `update_note` are the same
underlying operation surfaced under two names/descriptions for a caller's
clarity of intent (research.md §5), not two different behaviors. Calling
`create_note` on a note that already exists behaves exactly like
`update_note` (appends), and vice versa; this is inherited, not new,
behavior from FR-004/FR-005.
