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
- **Account root**: `folder_path=""` (or `"/"`) lists the account's
  top-level folders (`parent_path: null`) and no notes — Notes keeps every
  note inside a folder (issue #13).
- **Errors**: `NotFoundError` if `folder_path` does not exist.
- Folders Notes still reports but that can't be read (deleted, or moved in
  from another parent) are omitted rather than failing the call (issue #25).
- Read-only (FR-008).

## `search_notes(pattern: str, folder_path: str | None = None) -> list[Note]`

Wraps `apple.core.grep`.

- **Input schema**: `pattern` (string, required), `folder_path` (string or
  null, optional, default `null` — omit to search the whole account).
- **Output**: Wrapped: `{"result": [{"id", "name", "folder_path"}, ...]}`.
  Empty array (`{"result": []}`) when nothing matches — not an error.
- **Errors**: `InvalidPatternError` if `pattern` is not a valid regular
  expression; `NotFoundError` if `folder_path` is given and doesn't exist.
- Unreadable leftover folders are skipped, so one of them never makes a
  scoped or whole-account search fail (issue #25).
- Read-only (FR-008).

## `read_note(note_id: str) -> str`

Wraps `apple.core.cat`.

- **Input schema**: `{"note_id": {"type": "string"}}`, required.
- **Output**: Wrapped: `{"result": "<the note's content>"}`.
- **Errors**: `NotFoundError` if no note with `note_id` exists.
- Read-only.

## `create_note(folder_path: str, name: str, content: str) -> Note`

Wraps `apple.core.append` (its create-if-missing path is the intended use
here; see the note below on ambiguity). If `folder_path` doesn't exist yet,
`create_note` creates it first (and any missing intermediate folders along
the path, via repeated `apple.core.mkdir` calls) rather than failing —
amendment, since a caller asking to create a note in a folder most likely
wants that folder to exist, not a `NotFoundError`.

- **Input schema**: `folder_path`, `name`, `content` — all strings,
  required.
- **Output**: **Not** wrapped — the structured content is the created
  `Note` directly: `{"id", "name", "folder_path"}`.
- **Errors**: `AmbiguousMatchError` if a note named `name` already exists
  more than once in `folder_path` (inherited from `append`'s contract —
  see note below); `InvalidNameError` if `name` is empty,
  whitespace-only, or multi-line — checked before any folder or note is
  created (issue #10). `folder_path` not existing is no longer an error
  case (see above).
- Leading/trailing whitespace in `name` is ignored — Notes trims it from
  titles — so a padded `name` finds (and appends to) the existing note
  rather than creating a duplicate (issue #26).

## `update_note(folder_path: str, name: str, content: str, overwrite: bool = False) -> Note`

Default (`overwrite=False`): wraps `apple.core.append` (its
append-to-existing path is the intended use here) — identical to
`create_note`'s behavior otherwise.

When `overwrite=True`: first calls `apple.core.ls(folder_path)` to check
how many notes are already named `name` (zero, one, or ambiguous — see
Errors below). If exactly one: archives it (via `apple.core.mv`, into a
single, fixed, top-level `archive` folder — auto-created via
`apple.core.mkdir` if it doesn't exist yet; `mkdir` required a small fix
to support top-level folder creation at all, research.md §8) and only
then creates a new note with `content` at `folder_path`/`name` (via
`apple.core.append`'s create-if-missing path). See research.md §8 for the
full design and why the archive step must complete before the create
step.

- **Input schema**: `folder_path`, `name`, `content` — strings, required;
  `overwrite` — boolean, optional, default `false`.
- **Output**: **Not** wrapped — the structured content is the resulting
  `Note` directly: `{"id", "name", "folder_path"}`. When `overwrite=True`
  archived an old note, that note's `Note` can subsequently be found via
  `list_folder_contents("archive")` — its own `id`/`name` are unchanged,
  only `folder_path` becomes `"archive"`.
- **Errors**: `NotFoundError` if `folder_path` doesn't exist;
  `AmbiguousMatchError` if a note named `name` already exists more than
  once in `folder_path` — checked before any change is made, regardless
  of `overwrite`; `InvalidNameError` if `name` is empty, whitespace-only,
  or multi-line — also checked before any change (issue #10).
- Leading/trailing whitespace in `name` is ignored, in both modes, as for
  `create_note` (issue #26).
- Never overwrites or removes existing content in place, in either mode
  (FR-005, FR-013): append mode adds newline-separated content (inherited
  from `append`'s contract, research.md §6a in feature 002); replace mode
  preserves the original note's content unchanged, just relocated to
  `archive`, rather than editing or deleting it.

**Note on `create_note` vs. `update_note`**: in `update_note`'s default
(`overwrite=False`) mode, both call the same `append()` function, which
already does the right thing regardless of whether a note exists yet —
they're the same underlying operation surfaced under two names/
descriptions for a caller's clarity of intent (research.md §5), not two
different behaviors. Calling `create_note` on a note that already exists
behaves exactly like `update_note` with `overwrite=False` (appends), and
vice versa. `update_note`'s `overwrite=True` mode is the one place the two
tools genuinely diverge — `create_note` has no equivalent, since it has no
existing note to replace in the first place.
