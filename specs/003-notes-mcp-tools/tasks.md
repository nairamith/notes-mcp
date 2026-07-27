---

description: "Task list template for feature implementation"
---

# Tasks: Apple Notes MCP Tools

**Input**: Design documents from `/specs/003-notes-mcp-tools/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per the project constitution (Test-First, Test-Always) and spec FR-009, every user story below includes mandatory test tasks. Write tests first, confirm they fail, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project layout (per plan.md): `src/notes_mcp/tools/` (one module per
tool) and `tests/{contract,unit/tools,integration/tools}/`.

**Test tiers, per tool**: a **contract** test (static schema — tool is
registered, input/output JSON schema shape — no actual call), a **unit**
test (mocked `apple.core` call — behavior and error propagation, no real
Notes), and one shared **integration** test file exercising all five tools
end-to-end against real Notes.

**Same-file constraint**: every tool registration lands in the single
shared `src/notes_mcp/server.py`. Registration tasks are **not** marked
`[P]` relative to each other even across different user stories, since
concurrent edits to one file would conflict — see Dependencies & Execution
Order below. Each tool's own implementation file, however, is independent
of the others and can be worked on in parallel.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and shared test infrastructure

- [ ] T001 [P] Move `tests/integration/apple/conftest.py` to `tests/integration/conftest.py` (content unchanged) so its `notes_available`/`skip_without_notes`/`scratch_folder`/`seed_note`/`seed_subfolder` fixtures are shared by both `tests/integration/apple/` and the new `tests/integration/tools/` (research.md §7)
- [ ] T002 [P] Create empty directories `tests/unit/tools/` and `tests/integration/tools/` (no `__init__.py`, matching this project's existing pytest import-mode convention)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Retire the placeholder `list_folders` tool (FR-011) before any new tool is registered

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Remove the `list_folders` import and its `mcp.add_tool(list_folders)` registration from `src/notes_mcp/server.py` (depends on T001, T002)
- [ ] T004 [P] Delete `src/notes_mcp/tools/list_folders.py` (the retired placeholder tool and its stub `Folder` model)
- [ ] T005 [P] Delete `tests/contract/test_list_folders_contract.py` and `tests/unit/test_list_folders.py` (dedicated tests for the retired tool)

**Checkpoint**: Foundation ready — `server.py` has zero tool registrations, the old stub and its tests are gone, shared test fixtures are in place for user story work to begin

---

## Phase 3: User Story 1 - List the contents of a folder (Priority: P1) 🎯 MVP

**Goal**: `list_folder_contents(folder_path)` returns the real notes and subfolders inside a folder, via `apple.core.ls`.

**Independent Test**: Call the tool against a known folder over a real MCP session and confirm the returned notes/subfolders match Notes' actual contents.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T006 [P] [US1] Contract test: `list_folder_contents` is registered with input schema `{folder_path: string}` and its output schema matches an unwrapped `FolderListing` (`folders`/`notes` arrays — research.md §4) — in `tests/contract/test_list_folder_contents_contract.py` (depends on T003)
- [ ] T007 [P] [US1] Unit test: mocking `apple.core.ls`, verify the tool returns the `FolderListing` as-is and that a `NotFoundError` raised by `ls` propagates (for the SDK to convert into an `isError` result) — in `tests/unit/tools/test_list_folder_contents_unit.py` (depends on T002)

### Implementation for User Story 1

- [ ] T008 [P] [US1] Implement `list_folder_contents(folder_path: str) -> FolderListing` in `src/notes_mcp/tools/list_folder_contents.py`, calling `apple.core.ls` directly with no try/except (research.md §2)
- [ ] T009 [US1] Register `list_folder_contents` in `src/notes_mcp/server.py` (depends on T003, T008)

**Checkpoint**: User Story 1 is fully functional and testable independently — `list_folder_contents` works against real Notes data.

---

## Phase 4: User Story 2 - Search for notes (Priority: P2)

**Goal**: `search_notes(pattern, folder_path=None)` returns matching notes, via `apple.core.grep`.

**Independent Test**: Call the tool with a pattern known to match a real note and confirm it's returned; call it with a non-matching pattern and confirm an empty result.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T010 [P] [US2] Contract test: `search_notes` is registered with input schema `pattern` (required) + `folder_path` (optional, default null) and output wrapped as `{"result": [...]}` (research.md §4) — in `tests/contract/test_search_notes_contract.py` (depends on T003)
- [ ] T011 [P] [US2] Unit test: mocking `apple.core.grep`, verify pass-through of results and that `InvalidPatternError`/`NotFoundError` propagate — in `tests/unit/tools/test_search_notes_unit.py` (depends on T002)

### Implementation for User Story 2

- [ ] T012 [P] [US2] Implement `search_notes(pattern: str, folder_path: str | None = None) -> list[Note]` in `src/notes_mcp/tools/search_notes.py`, calling `apple.core.grep` directly
- [ ] T013 [US2] Register `search_notes` in `src/notes_mcp/server.py` (depends on T009, T012 — same file as T009, sequential)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Read a note's content (Priority: P3)

**Goal**: `read_note(note_id)` returns a note's content, via `apple.core.cat`.

**Independent Test**: Call the tool with a note found via search/listing and confirm its content matches what's actually in that note.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T014 [P] [US3] Contract test: `read_note` is registered with input `{note_id: string}` and output wrapped as `{"result": "<string>"}` — in `tests/contract/test_read_note_contract.py` (depends on T003)
- [ ] T015 [P] [US3] Unit test: mocking `apple.core.cat`, verify pass-through and that `NotFoundError` propagates — in `tests/unit/tools/test_read_note_unit.py` (depends on T002)

### Implementation for User Story 3

- [ ] T016 [P] [US3] Implement `read_note(note_id: str) -> str` in `src/notes_mcp/tools/read_note.py`, calling `apple.core.cat` directly
- [ ] T017 [US3] Register `read_note` in `src/notes_mcp/server.py` (depends on T013, T016 — same file as T013, sequential)

**Checkpoint**: User Stories 1, 2 AND 3 all work independently.

---

## Phase 6: User Story 4 - Create a note in a folder (Priority: P4)

**Goal**: `create_note(folder_path, name, content)` creates a new note, via `apple.core.append`'s create-if-missing path.

**Independent Test**: Call the tool for a note that doesn't exist yet; confirm (via listing) it now exists and (via reading) its content matches exactly.

### Tests for User Story 4 (MANDATORY) ⚠️

- [ ] T018 [P] [US4] Contract test: `create_note` is registered with input `{folder_path, name, content}` (all required strings) and output unwrapped as a `Note` object — in `tests/contract/test_create_note_contract.py` (depends on T003)
- [ ] T019 [P] [US4] Unit test: mocking `apple.core.append`, verify pass-through of the created `Note` and that `NotFoundError`/`AmbiguousMatchError` propagate — in `tests/unit/tools/test_create_note_unit.py` (depends on T002)

### Implementation for User Story 4

- [ ] T020 [P] [US4] Implement `create_note(folder_path: str, name: str, content: str) -> Note` in `src/notes_mcp/tools/create_note.py`, calling `apple.core.append` directly
- [ ] T021 [US4] Register `create_note` in `src/notes_mcp/server.py` (depends on T017, T020 — same file as T017, sequential)

**Checkpoint**: User Stories 1-4 all work independently.

---

## Phase 7: User Story 5 - Update a note (Priority: P5)

**Goal**: `update_note(folder_path, name, content)` appends to an existing note (or creates it, matching User Story 4, if it doesn't exist yet), via `apple.core.append`.

**Independent Test**: Call the tool against a note with existing content and confirm (via reading) the note afterward contains both the original and the newly added content.

### Tests for User Story 5 (MANDATORY) ⚠️

- [ ] T022 [P] [US5] Contract test: `update_note` is registered with the same input/output shape as `create_note` — in `tests/contract/test_update_note_contract.py` (depends on T003)
- [ ] T023 [P] [US5] Unit test: mocking `apple.core.append`, verify pass-through and that `NotFoundError`/`AmbiguousMatchError` propagate, including the ambiguous-match case (FR-006) — in `tests/unit/tools/test_update_note_unit.py` (depends on T002)

### Implementation for User Story 5

- [ ] T024 [P] [US5] Implement `update_note(folder_path: str, name: str, content: str) -> Note` in `src/notes_mcp/tools/update_note.py`, calling `apple.core.append` directly (same underlying call as `create_note`, kept as a separate function per research.md §5)
- [ ] T025 [US5] Register `update_note` in `src/notes_mcp/server.py` (depends on T021, T024 — same file as T021, sequential)

**Checkpoint**: All five tools are independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Whole-server verification once all five tools exist

- [ ] T026 [P] Integration test exercising all five tools end-to-end against real Notes.app in a shared scratch folder (create → read → update → read → search → list) — in `tests/integration/tools/test_tools_integration.py` (depends on T009, T013, T017, T021, T025)
- [ ] T027 Update `tests/contract/test_server_tool_registration.py` to assert the full new tool set (`list_folder_contents`, `search_notes`, `read_note`, `create_note`, `update_note`) is advertised and `list_folders` is absent (depends on T009, T013, T017, T021, T025)
- [ ] T028 Update `tests/contract/test_server_startup_stdio.py`'s real-subprocess tool-list check to reference `list_folder_contents` instead of the retired `list_folders` (depends on T009)
- [ ] T029 [P] Run `quickstart.md` validation end-to-end on a real macOS machine with Notes configured, confirming SC-001 through SC-004
- [ ] T030 Review the five new tool modules and `server.py` for consistent naming/docstrings, confirm no duplicate logging was added at the tool layer (research.md's Observability decision), and remove any dead code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-7)**: Each depends on Foundational phase completion. Each tool's *implementation* file is independent of the others' (different files) — US1-US5 could be built in parallel by different people. Each tool's *registration*, however, is a sequential edit to the shared `server.py`, so registration tasks (T009, T013, T017, T021, T025) must land in some serial order regardless of which story's turn it "is" — the order shown (P1→P5) is simplest, not mandatory.
- **Polish (Final Phase)**: Depends on all five user stories being complete

### Same-File Sequencing (overrides story-parallel opportunities)

- All edits to `src/notes_mcp/server.py` (T003, T009, T013, T017, T021, T025) must happen sequentially, in that order, regardless of which story they belong to
- `tests/contract/test_server_tool_registration.py` (T027) and `tests/contract/test_server_startup_stdio.py` (T028) are each touched once, in Polish, after all registrations exist

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- A tool's implementation file has no dependency on any other tool's implementation file
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- T004 and T005 (Foundational) can run in parallel — different files
- Within each user story, its contract test, unit test, and implementation file are three different files and can all be started in parallel; only that story's *registration* task must wait for the previous registration to land
- T008, T012, T016, T020, T024 (the five tool implementations) are mutually independent and could all be written in parallel, even across stories, since each is its own new file
- T029 (Polish) can run in parallel with T030

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 tests and implementation together (different files):
Task: "Contract test: list_folder_contents schema in tests/contract/test_list_folder_contents_contract.py"
Task: "Unit test: list_folder_contents with mocked apple.core.ls in tests/unit/tools/test_list_folder_contents_unit.py"
Task: "Implement list_folder_contents in src/notes_mcp/tools/list_folder_contents.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — retires the placeholder tool)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm `list_folder_contents` works against real Notes data and `list_folders` is gone
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → clean slate, old stub retired
2. Add User Story 1 (`list_folder_contents`) → Validate independently
3. Add User Story 2 (`search_notes`) → Validate independently
4. Add User Story 3 (`read_note`) → Validate independently
5. Add User Story 4 (`create_note`) → Validate independently
6. Add User Story 5 (`update_note`) → Validate independently (builds on the same `append` path as US4)
7. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies — see the Same-File
  Sequencing note above for why `server.py`-touching tasks specifically
  can't be parallel even though most of this feature's files are
  independent
- [Story] label maps task to specific user story for traceability
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- `create_note` and `update_note` call the exact same backend function
  (`apple.core.append`) and behave identically regardless of which name is
  called — they exist as two tools for the distinct metadata/description
  an MCP client sees, not two different behaviors (research.md §5)
