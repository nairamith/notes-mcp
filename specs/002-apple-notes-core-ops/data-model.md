# Data Model: Apple Notes Core Backend Operations

## Note

An individual Apple Notes note, as returned by `ls` and `grep`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Notes' own stable identifier. Unique account-wide. This — not `name` — is how `mv`/`rm` address a specific note. |
| `name` | string | yes | The note's title. May be empty and is **not** guaranteed unique — multiple notes may share (or lack) a title. |
| `folder_path` | string | yes | `/`-delimited path of the folder currently containing this note. |

**Validation rules**:
- `id` is always present and unique across the whole account.
- `name` may be an empty string (Apple Notes allows untitled notes);
  duplicates across notes are expected and not an error.

**Lifecycle**: A note's `folder_path` changes when `mv` relocates it; its
`name` changes when `mv` renames it. No other state transitions are in
scope for this feature (`rm` is a stub — see Folder/Note "Removal" note
below).

## Folder

A container for notes and/or other folders, as returned by `ls` and
created by `mkdir`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | The folder's own name (not its full path). |
| `path` | string | yes | Full `/`-delimited path from a top-level folder (e.g. `"Personal/Groceries"`). This is how `mkdir`'s parent, and `mv`/`rm`'s folder target, are addressed. |
| `parent_path` | string \| null | yes | Path of the containing folder, or `null` for a top-level folder. |

**Validation rules**:
- `name` MUST be non-empty.
- `name` MUST be unique among sibling folders under the same
  `parent_path` — `mkdir` (FR-003) rejects a duplicate name under the same
  parent, which is what makes `path` an unambiguous identifier.

**Lifecycle**: A folder's `path`/`parent_path`/`name` change when `mv`
relocates and/or renames it. `mkdir` creates a new folder with no notes
and no subfolders.

## Removal (out of scope for this feature)

Neither entity gains a "deleted" state in this feature: `rm` is a stub
(FR-006/FR-007) that never mutates either entity. Real removal semantics —
including whether a removed item becomes recoverable and how non-empty
folders are handled — are deferred to a future feature and will extend
this data model then (e.g. a possible "Recently Deleted" state), not now.

## FolderListing (return shape of `ls`)

Not a persistent entity — just the structure `ls` returns for one folder:

| Field | Type | Notes |
|---|---|---|
| `folders` | list of Folder | Immediate subfolders only, not deeper descendants. |
| `notes` | list of Note | Immediate notes only. |
