# API Contract: `apple/core.py`

This is a Python library API (function signatures), not a network
protocol — the "contract" here is the public function signatures, their
behavior, and the exceptions they raise. See [data-model.md](../data-model.md)
for `Note`/`Folder`/`FolderListing` field definitions.

## Exceptions

All defined in `apple/core.py`:

- `AppleNotesError(Exception)` — base class for everything below.
- `NotFoundError(AppleNotesError)` — a referenced note, folder, or parent
  folder does not exist.
- `AlreadyExistsError(AppleNotesError)` — `mkdir` target name already
  exists under the same parent.
- `InvalidPatternError(AppleNotesError)` — `grep` was given an invalid
  regular expression.
- `AutomationPermissionError(AppleNotesError)` — macOS has not granted
  Notes automation permission yet.
- `NotImplementedYetError(AppleNotesError)` — raised by `rm`, always, in
  this feature.
- `AmbiguousMatchError(AppleNotesError)` — `append`'s `(folder_path,
  name)` matches more than one existing note.
- `InvalidNameError(AppleNotesError)` — a note name is empty,
  whitespace-only, or contains a line break (issue #10).

## `validate_note_name(name: str) -> None`

Raises `InvalidNameError` if `name` can't be a note's title: empty,
whitespace-only, or containing `\n`/`\r`. Notes derives a title from the
first line of a note's text, so such a name would silently turn the first
line of the content into the title (or push part of the name into the
content). Called by `append` and by `mv` for a note's `new_name`, and
exposed so tools that do other work first (e.g. `create_note` creating
folders) can reject the name before changing anything.

## `ls(folder_path: str) -> FolderListing`

Lists the immediate notes and subfolders inside `folder_path`.

- **Raises** `NotFoundError` if `folder_path` does not exist. A path's
  first segment must name a *top-level* folder; a nested folder is only
  reachable through its full path (research.md §2 addendum).
- **Read-only**: never changes any Notes data (FR-008).
- Returns an empty `FolderListing` (both lists empty) for an existing,
  empty folder — this is success, not an error.

## `grep(pattern: str, folder_path: str | None = None) -> list[Note]`

Searches note plaintext content using `pattern` as a Python regular
expression. When `folder_path` is given, only notes within that folder are
searched; when omitted, the entire account is searched.

- **Raises** `InvalidPatternError` if `pattern` is not a valid regular
  expression — checked before any Notes interaction.
- **Raises** `NotFoundError` if `folder_path` is given and does not exist.
- **Read-only**: never changes any Notes data (FR-008).
- Returns an empty list when nothing matches — this is success, not an
  error.
- A whole-account search (`folder_path` omitted) returns each matching
  note exactly once, with its full `folder_path` from a top-level folder.

## `mkdir(parent_path: str, name: str) -> Folder`

Creates a new, empty folder named `name` directly under `parent_path`.

- **Raises** `NotFoundError` if `parent_path` does not exist (FR-004; no
  automatic creation of missing intermediate parents).
- **Raises** `AlreadyExistsError` if a folder named `name` already exists
  under `parent_path` (FR-003). For `parent_path=""` only top-level
  folders count — a nested folder with the same name elsewhere doesn't.
- Returns the newly created `Folder`.

## `mv(kind: Literal["note", "folder"], identifier: str, destination_folder_path: str, new_name: str | None = None) -> Note | Folder`

Moves the note (`kind="note"`, `identifier` = the note's `id`) or folder
(`kind="folder"`, `identifier` = the folder's `path`) into
`destination_folder_path`. If `new_name` is given, it is renamed in the
same call; if omitted, its current name is kept.

- **Raises** `NotFoundError` if the target note/folder, or
  `destination_folder_path`, does not exist.
- **Raises** `AlreadyExistsError` if a folder named `new_name` (or the
  item's current name, if not renaming) already exists directly under
  `destination_folder_path` for a folder move (mirrors `mkdir`'s
  duplicate-name rule — note titles, unlike folder names, are not
  required to be unique, so this check does not apply when moving a note).
- Returns the moved/renamed `Note` or `Folder` (reflecting its new
  `folder_path`/`path` and, if changed, `name`).
- **Raises** `InvalidNameError` for `kind="note"` when `new_name` is
  given but fails `validate_note_name` — checked before anything moves.
- Never destroys or duplicates content (FR-005).

## `rm(kind: Literal["note", "folder"], identifier: str) -> NoReturn`

Stub for this feature (FR-006/FR-007). **Always raises**
`NotImplementedYetError`, regardless of whether `identifier` refers to a
real note/folder, and never touches Notes data. Real removal behavior
(recoverable deletion, non-empty-folder policy) is deferred to a future
feature.

## `cat(note_id: str) -> str`

Returns the plain-text content of the note identified by `note_id`.

- **Raises** `NotFoundError` if no note with `note_id` exists.
- **Read-only**: never changes any Notes data (FR-008/FR-011).

## `append(folder_path: str, name: str, text: str) -> Note`

Appends `text` to the content of the note named `name` inside
`folder_path`. If no such note exists yet, first creates a new, empty note
there, then appends `text` to it (so its resulting content is exactly
`text`, with no leading separator — see research.md §6a). If the note
already has content, `text` is appended after a newline separator,
preserving everything already there.

- **Raises** `NotFoundError` if `folder_path` does not exist.
- **Raises** `AmbiguousMatchError` if more than one note named `name`
  already exists in `folder_path` (FR-013) — `append` never guesses which
  one to modify.
- **Raises** `InvalidNameError` if `name` fails `validate_note_name` —
  checked before any Notes interaction.
- Returns the resulting `Note` (its `id`, `name`, `folder_path` — not its
  content; use `cat` to read the content back).
- Never removes or overwrites existing content (FR-012, SC-006).
- Line breaks inside `text` are preserved exactly: `cat` returns the
  same lines that were written (research.md §6a addendum).

## Cross-cutting guarantees (all functions)

- Folder paths are accepted in any spelling that differs only by empty
  segments (`"A/B/"`, `"A//B"`, `"/A/B"`), and every path returned —
  `Note.folder_path`, `Folder.path`, `Folder.parent_path` — is canonical
  (`"A/B"`), never an echo of the input's spelling (research.md §2
  addendum).

- Every call logs its function name, outcome (success/error type), and
  duration via stdlib `logging`, per the constitution's Observability
  principle.
- No function ever interpolates its string arguments directly into an
  AppleScript/JXA script source — arguments are passed via the script's
  `argv`, eliminating script-injection risk from note/folder names
  containing special characters (see research.md §1).
