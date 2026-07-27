# Feature Specification: Move and Remove a Note

**Feature Branch**: `004-remove-move-note`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Create features to remove and move a note. Remove should move things to /archive."

## Clarifications

### Session 2026-07-27 (amendment — PR review)

- Q: Should the remove tool archive a note by calling the backend's `rm` function (which itself composes `mkdir`/`mv` to archive), or should the tool compose `mkdir`/`mv` directly and leave `rm` as a separate, literal delete primitive? → A: The tool composes `mkdir`/`mv` directly, mirroring `update_note`'s identical archive-on-replace composition. `apple.core.rm` is implemented separately, matching what Notes.app's own delete mechanism actually does (moves a note into Notes' native "Recently Deleted" folder — verified empirically, not an instant permanent purge) — a real, correctly-named backend primitive that no MCP tool in this feature exposes. This keeps "archive, don't delete" as a tool-layer policy decision (consistent with how `update_note`'s replace-mode archiving already works), rather than baking that policy into the backend layer, which is meant to stay a thin, literal set of operations over Apple Notes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Move a note to a different folder (Priority: P1)

As an MCP client, I want a tool that moves an existing note to a different
folder (optionally renaming it in the same call), so that automation can
reorganize notes without recreating them.

**Why this priority**: A direct wrap of an already-proven, already-tested
backend capability (`mv`) — no new backend behavior, lower risk than
introducing real removal semantics for the first time.

**Independent Test**: Call the tool with a note and a different, existing
destination folder; confirm (via listing) the note is gone from its
original folder and present in the destination.

**Acceptance Scenarios**:

1. **Given** a note and a different, existing destination folder, **When**
   the tool is called, **Then** the note appears in the destination
   folder and no longer appears in its original folder.
2. **Given** a note, a destination folder, and a new name, **When** the
   tool is called with all three, **Then** the note is both moved and
   renamed in the same call.
3. **Given** a note that doesn't exist, or a destination folder that
   doesn't exist, **When** the tool is called, **Then** it returns a
   clear, structured error and nothing is moved.

---

### User Story 2 - Remove a note (Priority: P2)

As an MCP client, I want a tool that removes a note, so that automation
can clean up notes that are no longer needed — without ever permanently
destroying their content.

**Why this priority**: Delivered after move since it introduces real
removal behavior for the first time (previously an explicit stub reserved
for a future feature); a higher-risk capability than a plain move, so
it's built on top of move rather than before it.

**Independent Test**: Call the tool with an existing note; confirm (via
listing) the note is gone from its original folder and now appears,
unchanged, in the well-known top-level `archive` folder.

**Acceptance Scenarios**:

1. **Given** an existing note, **When** the tool is called with it,
   **Then** the note no longer appears in its original folder and
   instead appears, with its content unchanged, in the well-known
   top-level `archive` folder.
2. **Given** the well-known archive location doesn't exist yet, **When**
   the tool is used for the first time, **Then** it is created
   automatically rather than the call failing for its absence.
3. **Given** a note that doesn't exist, **When** the tool is called,
   **Then** it returns a clear, structured error and nothing is removed.

---

### Edge Cases

- What happens when removing a note that is already located inside the
  `archive` folder (e.g. previously archived by this tool, or by
  `update_note`'s replacement mode from a prior feature)? The call MUST
  NOT error and MUST NOT lose or duplicate the note — removing an
  already-archived note is a harmless no-op with respect to its location.
- What happens when moving a note to the folder it's already in (with no
  new name given)? The call MUST succeed as a no-op with respect to the
  note's location, not error.
- What happens when moving a note to the folder it's already in, but with
  a new name? The note MUST be renamed in place.
- Removing a note is equivalent to moving it into the well-known
  `archive` folder — a caller could also achieve the same effect by
  calling the move tool directly with `archive` as the destination; the
  remove tool exists for a caller's clarity of intent, not because it
  does anything the move tool couldn't already express.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an MCP tool that moves an existing
  note to a different, existing folder, backed by the existing `mv`
  backend capability's note-moving path.
- **FR-002**: The move tool MUST accept an optional new name, renaming the
  note in the same call, mirroring `mv`'s existing optional rename
  parameter — moving and renaming are not separate operations.
- **FR-003**: The move tool MUST fail with a clear, structured error, and
  move nothing, if the note or the destination folder does not exist.
- **FR-004**: The system MUST provide an MCP tool that removes a note by
  moving it into a single, well-known, top-level `archive` folder — the
  same location and auto-creation behavior already established for
  `update_note`'s replacement mode — rather than permanently deleting it.
  This is a tool-level policy decision, achieved by composing the
  backend's existing `mkdir`/`mv` capabilities directly (mirroring
  `update_note`'s identical composition), not by calling the backend's
  `rm` function (amendment — see below).
- **FR-004a**: The system MUST also implement real behavior for notes in
  the backend's `rm` function (previously an explicit stub reserved for a
  future feature), matching Notes.app's own delete mechanism. This is a
  distinct backend primitive from FR-004's remove tool — no MCP tool in
  this feature exposes `rm` directly; the remove tool never calls it.
- **FR-005**: The remove tool MUST NOT permanently delete a note's content
  at any point; a removed note's content remains fully intact and
  reachable afterward via the well-known archive location.
- **FR-006**: If the well-known archive location doesn't exist yet the
  first time removal is used, the system MUST create it automatically
  rather than fail for its absence.
- **FR-007**: Removing a note that doesn't exist MUST fail with a clear,
  structured error rather than silently succeeding.
- **FR-008**: Real behavior for folders (`rm` called with a folder rather
  than a note) remains out of scope for this feature and continues to
  raise its existing not-implemented error — only notes gain real `rm`
  behavior here, and only notes are supported by the remove tool.
- **FR-009**: Every tool defined in this feature MUST translate the
  backend's typed errors into clear, structured MCP tool errors,
  consistent with this project's established tool contract — no tool may
  crash the server process or silently return an empty/default result in
  place of a real error.
- **FR-010**: Each of the two tools MUST have an automated test covering
  its behavior, per this project's Test-First principle, including the
  remove tool's archive-folder auto-creation path and the
  already-archived idempotency edge case.
- **FR-011**: Each tool's input and output MUST have an explicit,
  documented schema, consistent with this project's MCP Contract
  Integrity principle.

### Key Entities

- **Note**, **Folder**: unchanged from the existing backend model (see
  `specs/002-apple-notes-core-ops/data-model.md`); no new fields.
- **Archive location**: not a new entity — the same well-known, top-level
  `archive` folder already established in `specs/003-notes-mcp-tools/`
  for `update_note`'s replacement mode. This feature reuses that single,
  canonical location rather than introducing a second one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A note can be moved to any existing folder, optionally
  renamed, in a single tool call — verifiable by listing the destination
  folder afterward.
- **SC-002**: A removed note is never permanently lost — it can always be
  found afterward, with its content unchanged, via the well-known archive
  location, verifiable using the existing listing tool.
- **SC-003**: Every tool call in this feature that targets a note or
  folder that doesn't exist returns a clear, structured error 100% of the
  time — never a crash, and never a silent no-op indistinguishable from
  success.

## Assumptions

- "Remove" (the MCP tool's behavior) means archive, not permanently
  delete — consistent with this project's constitution, which prefers
  additive/reversible operations over hard deletes wherever the platform
  supports it. This is a tool-level guarantee: the `remove_note` tool
  itself never calls anything that deletes a note.
- `apple.core.rm`, separately, does implement a real delete for notes
  (amendment — see Clarifications), matching what Notes.app's own delete
  mechanism does. This is a backend primitive, not exposed by any tool in
  this feature — it exists for the same reason `mkdir` and (until this
  feature) `mv` existed as real, tested backend capabilities before ever
  being exposed as their own tools.
- The remove tool reuses the exact same top-level `archive` folder
  already established for `update_note`'s replacement mode (feature 003)
  — a single canonical archive location for anything this project ever
  archives, not a separate location per feature.
- Scope is notes only. `apple.core.mv` already supports moving folders
  internally, but no folder-move tool is introduced here; `apple.core.rm`
  called with a folder remains an unimplemented stub, unchanged from
  today. Both are deliberate scope decisions, not oversights — revisit if
  a concrete need for folder-level move/remove tools arises.
- No new backend capability is required for the move tool — it's a direct
  wrap of the existing `mv` function. The remove tool requires no new
  backend capability either: it composes the existing `mkdir`/`mv`
  primitives directly, at the tool layer — the same composition pattern
  already used by `update_note`'s replacement mode, implemented
  independently here rather than factored into a shared helper (this
  project's constitution prefers duplication over a shared abstraction
  until a third real use case exists; this is only the second). A new
  JXA script (`rm_note.js`) was needed for `apple.core.rm`'s own real
  delete behavior, which the remove tool doesn't use.
