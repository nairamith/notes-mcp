# Feature Specification: Apple Notes Core Backend Operations

**Feature Branch**: `002-apple-notes-core-ops`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "I want to setup basic functionalities to interact with apple notes. Write basic functions like ls, grep, mkdir, rm, mv in a file called apple/core.py. No need to wire this to the mcp tools. Just need the backend function for this task"

## Clarifications

### Session 2026-07-26

- Q: Should `grep` do plain substring/text matching, or support full regular-expression patterns? → A: Full regular-expression support.
- Q: What should `rm` do when the target folder is non-empty? → A: `rm` is a stub for this feature — it does not perform real removal yet. Its actual deletion behavior (including the non-empty-folder policy) is deferred to a future feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - List folder contents (Priority: P1)

As a developer building on this backend, I want a function that lists the
notes and subfolders contained within a given folder, so that I can inspect
the current state of Notes before and after performing other operations.

**Why this priority**: Read-only and the safest capability; every other
operation's effects are verified by listing folder contents, so this is
both foundational and low-risk to deliver first.

**Independent Test**: Call the listing function against a known folder in a
real (or sandboxed test) Notes environment and confirm the returned notes
and subfolders exactly match what Notes actually contains.

**Acceptance Scenarios**:

1. **Given** a folder that contains notes and subfolders, **When** the
   listing function is called for that folder, **Then** it returns exactly
   the notes and subfolders directly inside it (not deeper descendants).
2. **Given** a folder that exists but is empty, **When** the listing
   function is called, **Then** it returns an empty result, not an error.

---

### User Story 2 - Search note content (Priority: P2)

As a developer building on this backend, I want a function that searches
note content for a given pattern and returns the matching notes, so that
automation can locate specific notes without enumerating every note by
hand.

**Why this priority**: Builds directly on listing (US1) to provide the next
most valuable read-only capability — finding relevant notes — before any
state-changing operations are introduced.

**Independent Test**: Create/identify a note containing a known piece of
text, call the search function with a pattern that matches it, and confirm
that note is returned; call it with a pattern that matches nothing and
confirm an empty result.

**Acceptance Scenarios**:

1. **Given** at least one note whose content contains a given piece of
   text, **When** the search function is called with a matching pattern,
   **Then** that note is included in the results.
2. **Given** no notes contain a given pattern, **When** the search function
   is called with it, **Then** it returns an empty result, not an error.

---

### User Story 3 - Create a folder (Priority: P3)

As a developer building on this backend, I want a function that creates a
new folder, so that automation can organize notes without requiring someone
to manually create folders in the Notes app first.

**Why this priority**: The first state-changing capability, but purely
additive (creates something new) rather than modifying or removing
existing content, making it lower-risk than move or remove.

**Independent Test**: Call the folder-creation function with a new folder
name, then call the listing function (US1) on its parent and confirm the
new folder now appears.

**Acceptance Scenarios**:

1. **Given** a parent folder that exists, **When** the folder-creation
   function is called with a new folder name, **Then** the new folder
   exists and is returned by listing the parent afterward.
2. **Given** a folder name that already exists under the same parent,
   **When** the folder-creation function is called with that name again,
   **Then** it fails with a clear error rather than silently creating a
   duplicate or overwriting anything.

---

### User Story 4 - Move or rename a note or folder (Priority: P4)

As a developer building on this backend, I want a function that moves a
note or folder to a different parent folder and/or renames it, so that
automation can reorganize existing content without recreating it from
scratch.

**Why this priority**: Modifies existing content's location/identity rather
than only adding or reading, so it carries more risk than US1-US3, but it
does not destroy any content — the item still exists somewhere afterward.

**Independent Test**: Create/identify a note or folder, call the move
function to relocate and/or rename it, then confirm via the listing
function that it appears at the new location/name and no longer appears at
the old one.

**Acceptance Scenarios**:

1. **Given** a note or folder in one folder, **When** it is moved to a
   different existing folder, **Then** it appears under the destination
   folder and no longer appears under the original one.
2. **Given** a note or folder, **When** it is renamed without changing its
   parent folder, **Then** it appears under its new name in the same
   parent folder.

---

### User Story 5 - Reserve a removal function, stubbed for now (Priority: P5)

As a developer building on this backend, I want a `rm` function to exist
with a defined interface — even though it does not yet actually remove
anything — so that the eventual removal capability has a stable, known
call signature for other code to build against, without any real
destructive behavior being introduced before it is properly designed.

**Why this priority**: Removal is the only destructive capability under
consideration, and this project treats destructive operations as requiring
extra care (see this project's Safe, Reversible Data Operations principle).
Rather than guess at non-empty-folder handling and other destructive-path
policy now, this feature reserves the `rm` name/interface and defers its
real behavior — including whether it must refuse or recurse on non-empty
folders — to a dedicated future feature.

**Independent Test**: Call the `rm` function against a note or folder and
confirm two things: (1) it does not actually remove anything — the target
still appears via the listing function afterward — and (2) it clearly
signals that removal is not yet implemented, rather than silently
succeeding or behaving unpredictably.

**Acceptance Scenarios**:

1. **Given** a note or folder that exists, **When** `rm` is called on it,
   **Then** the note or folder still appears afterward when its parent
   folder is listed — nothing was actually removed.
2. **Given** any target (existing or not), **When** `rm` is called,
   **Then** it clearly and consistently signals "not implemented yet"
   rather than returning success, partial results, or an unrelated error.

---

### Edge Cases

- What happens when the listing or search function is called against a
  folder that does not exist?
- What happens when the move function's destination folder does not exist,
  or already contains an item with the same name?
- How are folder/note names that collide only in case or whitespace
  treated across these operations?
- What happens when `grep` is given an invalid regular-expression pattern?
- What happens when `rm` (the stub) is called repeatedly on the same
  target — does it consistently signal "not implemented" every time?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend MUST provide a listing capability (`ls`) that
  returns the notes and subfolders directly contained within a given
  folder (not deeper descendants).
- **FR-002**: The backend MUST provide a search capability (`grep`) that
  searches note content using a regular-expression pattern and returns the
  matching notes; an invalid pattern MUST fail with a clear error rather
  than crashing or silently returning no results.
- **FR-003**: The backend MUST provide a folder-creation capability
  (`mkdir`) that creates a new, empty folder under a specified, existing
  parent folder, and fails with a clear error if a folder with that name
  already exists under the same parent.
- **FR-004**: `mkdir` MUST fail with a clear, actionable error if the
  specified parent folder does not exist, rather than silently creating
  missing parent folders.
- **FR-005**: The backend MUST provide a move/rename capability (`mv`) that
  relocates a note or folder to a different parent folder, renames it, or
  both, without destroying or duplicating its content.
- **FR-006**: The backend MUST provide an `rm` function with a defined
  call signature (accepting a note or folder target), but for this feature
  `rm` MUST be a stub: it MUST NOT actually remove, modify, or otherwise
  change any real Notes data. It MUST clearly and consistently signal that
  removal is not yet implemented (e.g., raising a dedicated "not
  implemented" error) rather than silently succeeding.
- **FR-007**: `rm`'s real deletion behavior — including whether it uses
  Apple Notes' recoverable-deletion mechanism and how it handles non-empty
  folders — is explicitly deferred to a future feature and is out of scope
  here (see Clarifications).
- **FR-008**: `ls` and `grep` MUST be read-only — calling them MUST NOT
  change any Notes data. `rm`, as a stub (FR-006), is likewise read-only in
  effect for this feature, even though it is conceptually the removal
  capability.
- **FR-009**: Each of `ls`, `grep`, `mkdir`, `mv`, and `rm` MUST have an
  automated test covering its behavior, per this project's Test-First
  principle — for `rm`, this means testing that it consistently signals
  "not implemented" and never mutates real data.
- **FR-010**: `ls`, `grep`, `mkdir`, and `mv` operate on real Apple Notes
  data through the platform's supported automation surface (not a mock or
  simulated store), consistent with this project's Platform & Integration
  Constraints. `rm` does not touch Notes data at all in this feature, since
  it is a stub (FR-006).

### Key Entities

- **Note**: An individual Apple Notes note. Has a title/name, body content,
  and belongs to exactly one folder at a time.
- **Folder**: A container for notes and/or other folders. Has a name and
  belongs to exactly one parent folder at a time (except any top-level
  folder(s)).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Listing any existing folder returns results that exactly
  match that folder's actual contents in Notes at the time of the call,
  with no missing or extra entries.
- **SC-002**: Searching for a piece of text known to exist in one or more
  notes returns every note containing it and none that don't, completing
  in under 2 seconds for a personal-scale notes collection (on the order
  of a few hundred notes).
- **SC-003**: A folder created via the creation capability is visible when
  its parent folder is listed immediately afterward, with no delay or
  extra steps required.
- **SC-004**: A note or folder moved or renamed is visible at its new
  location/name and absent from its old one immediately after the
  operation, with no manual refresh or extra steps required.
- **SC-005**: Calling `rm` never changes what a subsequent listing shows —
  100% of `rm` calls during this feature leave Notes data exactly as it was
  beforehand, and consistently signal that removal isn't implemented yet.

## Assumptions

- These are backend/library functions only for this feature — they are not
  exposed as MCP tools here; MCP tool wiring is explicitly out of scope and
  left to a separate, future feature (per the user's request).
- Operations address folders and notes primarily by human-readable name
  (matching the `ls`/`grep`/`mkdir`/`mv`/`rm` filesystem-command naming the
  user chose), the same way a person would refer to them inside the Notes
  app itself.
- `mkdir` does not automatically create missing intermediate parent
  folders (matches plain `mkdir`, not `mkdir -p`) — the parent must already
  exist.
- `mv` is a single capability that can change a note/folder's parent
  folder, its name, or both in one call (matching how Unix `mv` handles
  both moving and renaming).
- No user-facing interface (CLI, UI) is in scope — these are internal
  functions intended to be called by other code (including a future MCP
  tool layer).
- `rm`'s real removal behavior (recoverable deletion, non-empty-folder
  policy) is intentionally deferred to a separate future feature; this
  feature only reserves its interface as a stub (per Clarifications).
- `grep` uses the target platform's/language's standard regular-expression
  support; no custom pattern language is introduced.
