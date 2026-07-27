# Feature Specification: Apple Notes MCP Tools

**Feature Branch**: `003-notes-mcp-tools`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Implement mcp tools to list files/folder, search for notes, create note in a folder, update a note, read contents of a note. Use the backend core functionalities defined in core"

## Clarifications

### Session 2026-07-27

- Q: A placeholder `list_folders` tool already exists from an earlier feature, returning fixed stub data (folders only, no notes). Should this feature replace it in place, or add a distinctly-named new tool and retire the stub? → A: Add a new, distinctly-named tool (folders + notes, backed by real data) and retire the existing placeholder `list_folders` tool rather than silently reshaping it.

### Session 2026-07-27 (amendment)

- Q: Should `update_note` gain an explicit overwrite mode, in addition to its existing append-only behavior? → A: Yes — a boolean flag (default `false`, preserving today's append-only behavior). When `true` and a note already exists: archive the existing note (move it into a single, well-known top-level "archive" folder, auto-created on first use, name unchanged) rather than deleting it, then create a fresh note with the new content in the original location. This composes the already-existing `mv`/`append`/`mkdir` backend primitives at the tool layer; it does not require a new backend capability. If no note exists yet, the flag has no effect — a fresh note is simply created either way, matching `create_note`. If the target name is already ambiguous (more than one existing note), the tool still refuses rather than guessing, regardless of the flag.

### Session 2026-07-27 (amendment 2 — PR review)

- Q: Should `create_note` fail when `folder_path` doesn't exist yet, or create it? → A: Create it (and any missing intermediate folders along the path) rather than failing — a caller asking to create a note in a folder most likely wants that folder to exist, not a `NotFoundError`. Handled entirely within the tool itself, composing the existing `mkdir` backend capability; no new backend capability needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - List the contents of a folder (Priority: P1)

As an MCP client (an AI agent acting on a user's behalf), I want a tool
that lists the notes and subfolders inside a given folder, so that I can
see what's there before searching, reading, or creating anything.

**Why this priority**: Read-only and the safest capability; every other
tool's effects are verified by listing folder contents, so this is both
foundational and low-risk to deliver first — consistent with how the
underlying backend capability was itself prioritized.

**Independent Test**: Call the tool against a known folder and confirm the
returned notes and subfolders match what's actually in Notes.

**Acceptance Scenarios**:

1. **Given** a folder that contains notes and subfolders, **When** the
   tool is called with that folder's path, **Then** it returns exactly
   the notes and subfolders directly inside it.
2. **Given** a folder that exists but is empty, **When** the tool is
   called, **Then** it returns an empty result, not an error.
3. **Given** a folder path that doesn't exist, **When** the tool is
   called, **Then** it returns a clear, structured error rather than
   crashing the server or returning an empty result indistinguishable
   from success.

---

### User Story 2 - Search for notes (Priority: P2)

As an MCP client, I want a tool that searches note content for a pattern,
so that I can find relevant notes without first listing every folder by
hand.

**Why this priority**: The next most valuable read-only capability after
listing — finding relevant notes is usually the next step once you know
what folders exist.

**Independent Test**: Call the tool with a pattern known to match at
least one note's content and confirm that note is returned; call it with
a pattern that matches nothing and confirm an empty result.

**Acceptance Scenarios**:

1. **Given** at least one note whose content matches a given pattern,
   **When** the tool is called with that pattern, **Then** that note is
   included in the results.
2. **Given** no notes match a given pattern, **When** the tool is called,
   **Then** it returns an empty result, not an error.
3. **Given** an invalid search pattern, **When** the tool is called,
   **Then** it returns a clear, structured error identifying the pattern
   as invalid.

---

### User Story 3 - Read a note's content (Priority: P3)

As an MCP client, I want a tool that returns a specific note's content,
so that I can read what's actually inside a note I found via listing or
searching.

**Why this priority**: Read-only and as safe as listing/searching; a
natural next step after search (find a note, then read it), and needed
before "update" can be meaningfully used (an agent should see current
content before adding to it).

**Independent Test**: Call the tool with a note found via search or
listing and confirm its returned content matches what's actually in that
note.

**Acceptance Scenarios**:

1. **Given** a note that exists and has content, **When** the tool is
   called with it, **Then** it returns exactly that note's content.
2. **Given** a note that does not exist, **When** the tool is called,
   **Then** it returns a clear, structured error rather than empty
   content.

---

### User Story 4 - Create a note in a folder (Priority: P4)

As an MCP client, I want a tool that creates a new note with given
content in a specified folder, so that automation can add notes without
a person doing it manually in the Notes app.

**Why this priority**: The first capability that changes Notes data, but
purely additive (creates something new) rather than modifying or
removing existing content — lower risk than updating an existing note.

**Independent Test**: Call the tool for a note that doesn't exist yet in
a given folder; confirm (via listing) it now exists and (via reading) its
content is exactly what was given.

**Acceptance Scenarios**:

1. **Given** a folder that exists and no note by the given name in it,
   **When** the tool is called with a name and content, **Then** a new
   note with that name and content exists in that folder afterward.
2. **Given** a folder path that doesn't exist yet, **When** the tool is
   called, **Then** the folder (and any missing intermediate folders
   along its path) is created automatically, and the note is created
   inside it as normal — never a `NotFoundError` for a missing folder.

---

### User Story 5 - Update a note (Priority: P5)

As an MCP client, I want a tool that either adds to an existing note's
content or fully replaces it, so that automation can both record
additional information over time and, when appropriate, start a note's
content fresh — without ever silently destroying the note's previous
content in the process.

**Why this priority**: The only capability that modifies existing note
content, so it's delivered last, after the read tools that let a caller
verify its effects and after the safer additive tool (create) is already
in place. Placed after "create" specifically because updating something
that might not exist yet builds on the same create-if-missing behavior,
and because its replace mode itself builds directly on "create" (the
fresh note it produces) plus the backend's existing move capability (to
preserve, not destroy, what's replaced).

**Independent Test (append mode, the default)**: Call the tool against a
note with existing content, without requesting replacement, and confirm
(via reading) the note afterward contains both the original and the newly
added content, with nothing lost.

**Independent Test (replace mode)**: Call the tool against a note with
existing content, requesting replacement; confirm (via reading, at its
original location) a note now exists there with only the new content, and
confirm (via listing the archive location) the original note — with its
original content intact — is now there instead of gone.

**Acceptance Scenarios**:

1. **Given** a note that already has content, **When** the tool is
   called without requesting replacement, **Then** the note's content
   afterward includes both the original and the newly added content.
2. **Given** no note by the given name exists yet in the given folder,
   **When** the tool is called (with or without requesting replacement),
   **Then** a new note is created there with the given content, exactly
   as User Story 4 describes — requesting replacement has no effect when
   there is nothing yet to replace.
3. **Given** more than one note already shares the given name in the
   given folder, **When** the tool is called (with or without requesting
   replacement), **Then** it returns a clear, structured error rather
   than guessing which note to change.
4. **Given** a note that already has content, **When** the tool is
   called requesting replacement, **Then** afterward: the original note
   (with its original content, unchanged) is found in a single,
   well-known archive location rather than deleted, and a new note with
   only the newly given content exists at the original name and folder.
5. **Given** the well-known archive location doesn't exist yet, **When**
   the tool is called requesting replacement for the first time,
   **Then** the archive location is created automatically rather than
   the call failing for lack of it.

---

### Edge Cases

- What happens when a tool is called with a folder or note that doesn't
  exist? (Covered per-story above: a clear, structured error every time,
  never a crash or a silently empty/wrong success.)
- What happens when the search pattern is malformed?
- What happens when the note-update tool's target name matches more than
  one note in the same folder?
- What happens to any existing caller of the retired placeholder
  `list_folders` tool once it's removed from the server's advertised
  tool list? (See FR-011 — it simply stops being offered; there is no
  known existing caller to migrate.)
- What happens if replacement is requested repeatedly over time for
  notes sharing the same name? (Each replaced note accumulates in the
  archive location under its original name; Apple Notes does not require
  note names to be unique, so this is expected, not an error — see
  Assumptions.)
- What happens if archiving the original note succeeds but creating the
  replacement fails partway through, or vice versa? (See FR-014 — the
  tool MUST archive first and only then create the replacement, so a
  failure never results in the original note's content being lost with
  no replacement created.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a new, distinctly-named MCP tool
  (not the existing placeholder `list_folders` tool) that lists the
  notes and subfolders directly inside a given folder, backed by the
  existing `ls` backend capability — not placeholder data.
- **FR-002**: The system MUST provide an MCP tool that searches note
  content for a pattern and returns matching notes, backed by the
  existing `grep` backend capability, across the whole account or scoped
  to a given folder.
- **FR-003**: The system MUST provide an MCP tool that returns a single
  note's content, backed by the existing `cat` backend capability.
- **FR-004**: The system MUST provide an MCP tool that creates a new note
  with given content in a given folder, backed by the existing `append`
  backend capability's create-if-missing behavior. If the given folder
  (or any folder along its path) doesn't exist yet, the tool MUST create
  it automatically, composing the existing `mkdir` backend capability,
  rather than failing.
- **FR-005**: The system MUST provide an MCP tool that, by default, adds
  content to an existing note — or creates it first if no note by that
  name exists yet in the given folder — backed by the existing `append`
  backend capability. In this default (append) mode, it MUST NOT overwrite
  or remove any of the note's existing content.
- **FR-006**: The note-update tool MUST fail with a clear, structured
  error — rather than guessing — when its target name matches more than
  one note in the given folder, regardless of whether replacement is
  requested.
- **FR-012**: The note-update tool MUST accept a boolean flag indicating
  whether to replace the note's content instead of appending to it,
  defaulting to `false` (append) so existing callers relying on today's
  append-only behavior are unaffected.
- **FR-013**: When the replacement flag is `true` and a note by the given
  name already (unambiguously) exists, the tool MUST move that existing
  note — unchanged — into a single, well-known top-level archive
  location, then create a new note with the given content at the
  original folder and name. It MUST NOT delete the original note's
  content at any point.
- **FR-014**: The archive move (FR-013) MUST complete before the
  replacement note is created, so that a failure to archive never leaves
  the system having created a replacement while losing the original, and
  never results in two notes of the same name coexisting in the original
  folder afterward.
- **FR-015**: If the archive location does not yet exist the first time
  it's needed, the tool MUST create it automatically rather than fail for
  its absence.
- **FR-016**: When the replacement flag is `true` but no note by the
  given name exists yet, the tool MUST simply create a new note with the
  given content (there is nothing to archive) — identical to the
  append-mode behavior in that same situation (FR-005, User Story 4).
- **FR-007**: Every tool defined in this feature MUST translate the
  backend's typed errors (not-found, invalid pattern, ambiguous match,
  automation-permission-not-granted) into clear, structured MCP tool
  errors. No tool may crash the server process or silently return an
  empty/default result in place of a real error.
- **FR-008**: The listing and search tools MUST be read-only — calling
  them MUST NOT change any Notes data.
- **FR-009**: Each of the five tools MUST have an automated test covering
  its behavior, per this project's Test-First principle, including the
  note-update tool's create-if-missing path, its ambiguous-match error
  path, its replace-mode archive-then-recreate path, and its
  replace-mode archive-location auto-creation path.
- **FR-010**: Each tool's input and output MUST have an explicit,
  documented schema, consistent with this project's MCP Contract
  Integrity principle — this feature is the first to expose these
  backend capabilities over MCP, so that principle is fully in scope here
  (unlike the backend feature that built the capabilities being wrapped).
- **FR-011**: The system MUST retire the existing placeholder
  `list_folders` tool (and its stubbed data) as part of this feature,
  rather than leaving it active alongside the new listing tool from
  FR-001.

### Key Entities

- **Note**: An individual Apple Notes note, as already defined by the
  backend — has a stable identifier, a title, the folder containing it,
  and content.
- **Folder**: A container for notes and/or other folders, as already
  defined by the backend — has a name and a path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An MCP client can go from "list a folder" to "read a
  specific note's content" in two tool calls, with no manual folder-tree
  knowledge required beforehand.
- **SC-002**: Every tool call that targets something that doesn't exist
  (a missing folder or note) returns a clear, structured error 100% of
  the time — never a crash, and never an empty result indistinguishable
  from "found nothing" — except `create_note`, whose one deliberate
  exception is a missing folder, which it creates automatically instead
  of erroring (FR-004).
- **SC-003**: A note created via the create tool, or updated via the
  update tool, is visible with its expected content via the listing and
  reading tools immediately afterward, with no delay or extra steps.
- **SC-004**: Updating a note never loses previously recorded content —
  100% of append-mode update calls on a note with existing content
  preserve that content alongside the newly added content.
- **SC-005**: Replacing a note's content (update mode with replacement
  requested) never actually destroys the prior content — 100% of the
  time, the original note is found intact in the archive location
  immediately afterward, not gone.

## Assumptions

- This feature wires existing backend capabilities (`ls`, `grep`, `cat`,
  `append`, and — for the note-update tool's replacement mode only, in
  addition to `ls` and `append` — `mv` and `mkdir`) into MCP tools; it
  does not add any new *backend* function, though it does require a
  small, narrow fix to `mkdir` (which currently cannot create a top-level
  folder at all — see research.md §8) since the archive location needs
  to be one. Where the backend's contract already defines something
  (e.g., `append`'s newline-separated, non-destructive write behavior, or
  `grep`'s Python regular-expression matching), the corresponding tool
  exposes that behavior as-is rather than redefining it.
- By default, "update a note" means adding content to it (via `append`),
  not replacing its existing content. An explicit replacement flag
  (FR-012) opts into replace behavior, implemented by composing the
  backend's existing `mv` (to archive the original, unchanged) and
  `append`/`mkdir` (to create the replacement, and the archive location
  if needed) — not by adding a new destructive backend primitive. The
  backend still has no in-place overwrite capability; replacement here
  never edits a note's content directly, it moves the old one aside and
  creates a new one.
- The archive location is a single, well-known, top-level folder — not
  one archive folder per source folder — shared by every note replaced
  by this tool regardless of where it originally lived. Archived notes
  keep their original name (no timestamp or other renaming is applied);
  since Apple Notes does not require note names to be unique, multiple
  archived notes sharing a name over time is expected, not an error.
- The note-creation tool requires its target folder to already exist; it
  does not create missing folders (matching `append`'s existing
  behavior). Folder creation, moving/renaming, and deletion are not
  exposed as their own standalone tools in this feature — `mv` and
  `mkdir` are used only internally, by the note-update tool's replacement
  mode, not as directly callable capabilities.
- The search tool exposes the backend's existing Python-regular-expression
  pattern matching as-is, rather than introducing a simplified pattern
  language.
- No external MCP client is known to depend on the existing placeholder
  `list_folders` tool today, so retiring it (FR-011) has no real migration
  burden — this is a clean removal, not a deprecation cycle.
