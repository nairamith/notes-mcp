# Feature Specification: Apple Notes MCP Tools

**Feature Branch**: `003-notes-mcp-tools`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Implement mcp tools to list files/folder, search for notes, create note in a folder, update a note, read contents of a note. Use the backend core functionalities defined in core"

## Clarifications

### Session 2026-07-27

- Q: A placeholder `list_folders` tool already exists from an earlier feature, returning fixed stub data (folders only, no notes). Should this feature replace it in place, or add a distinctly-named new tool and retire the stub? → A: Add a new, distinctly-named tool (folders + notes, backed by real data) and retire the existing placeholder `list_folders` tool rather than silently reshaping it.

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
2. **Given** a folder path that doesn't exist, **When** the tool is
   called, **Then** it returns a clear, structured error rather than
   creating the note somewhere unexpected.

---

### User Story 5 - Update a note (Priority: P5)

As an MCP client, I want a tool that adds content to an existing note (or
creates it if it doesn't exist yet), so that automation can record
additional information into a note over time without losing what's
already there.

**Why this priority**: The only capability that modifies existing note
content, so it's delivered last, after the read tools that let a caller
verify its effects and after the safer additive tool (create) is already
in place. Placed after "create" specifically because updating something
that might not exist yet builds on the same create-if-missing behavior.

**Independent Test**: Call the tool against a note with existing content
and confirm (via reading) the note afterward contains both the original
and the newly added content, with nothing lost.

**Acceptance Scenarios**:

1. **Given** a note that already has content, **When** the tool is
   called with additional content, **Then** the note's content afterward
   includes both the original and the newly added content.
2. **Given** no note by the given name exists yet in the given folder,
   **When** the tool is called, **Then** a new note is created there
   with the given content, exactly as User Story 4 describes.
3. **Given** more than one note already shares the given name in the
   given folder, **When** the tool is called, **Then** it returns a
   clear, structured error rather than guessing which note to change.

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
  with given content in a given, existing folder, backed by the existing
  `append` backend capability's create-if-missing behavior.
- **FR-005**: The system MUST provide an MCP tool that adds content to an
  existing note — or creates it first if no note by that name exists yet
  in the given folder — backed by the existing `append` backend
  capability. It MUST NOT overwrite or remove any of the note's existing
  content.
- **FR-006**: The note-update tool MUST fail with a clear, structured
  error — rather than guessing — when its target name matches more than
  one note in the given folder.
- **FR-007**: Every tool defined in this feature MUST translate the
  backend's typed errors (not-found, invalid pattern, ambiguous match,
  automation-permission-not-granted) into clear, structured MCP tool
  errors. No tool may crash the server process or silently return an
  empty/default result in place of a real error.
- **FR-008**: The listing and search tools MUST be read-only — calling
  them MUST NOT change any Notes data.
- **FR-009**: Each of the five tools MUST have an automated test covering
  its behavior, per this project's Test-First principle, including the
  note-update tool's create-if-missing path and its ambiguous-match error
  path.
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
  from "found nothing."
- **SC-003**: A note created via the create tool, or updated via the
  update tool, is visible with its expected content via the listing and
  reading tools immediately afterward, with no delay or extra steps.
- **SC-004**: Updating a note never loses previously recorded content —
  100% of update calls on a note with existing content preserve that
  content alongside the newly added content.

## Assumptions

- This feature wires existing backend capabilities (`ls`, `grep`, `cat`,
  `append`) into MCP tools; it does not add new backend behavior. Where
  the backend's contract already defines something (e.g., `append`'s
  newline-separated, non-destructive write behavior, or `grep`'s Python
  regular-expression matching), the corresponding tool exposes that
  behavior as-is rather than redefining it.
- "Update a note" means adding content to it (via `append`), not
  replacing its existing content — the backend has no
  replace/overwrite-note capability, and this feature does not add one.
- The note-creation tool requires its target folder to already exist; it
  does not create missing folders (matching `append`'s existing
  behavior). `mkdir`, `mv`, and `rm` (folder creation, moving/renaming,
  and deletion) are explicitly out of scope for this feature — only the
  five listed capabilities are exposed as tools here.
- The search tool exposes the backend's existing Python-regular-expression
  pattern matching as-is, rather than introducing a simplified pattern
  language.
- No external MCP client is known to depend on the existing placeholder
  `list_folders` tool today, so retiring it (FR-011) has no real migration
  burden — this is a clean removal, not a deprecation cycle.
