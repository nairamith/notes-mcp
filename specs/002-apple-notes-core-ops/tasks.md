---

description: "Task list template for feature implementation"
---

# Tasks: Apple Notes Core Backend Operations

**Input**: Design documents from `/specs/002-apple-notes-core-ops/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per the project constitution (Test-First, Test-Always) and spec FR-009, every user story below includes mandatory test tasks. Write tests first, confirm they fail, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project layout (per plan.md): `src/notes_mcp/apple/` and `tests/{unit,integration}/apple/`.

**Important — same-file constraint**: nearly all implementation work lands
in one file, `src/notes_mcp/apple/core.py`, and nearly all tests land in
one of two shared files, `tests/unit/apple/test_core_unit.py` and
`tests/integration/apple/test_core_integration.py` (this is the
single-file structure the user asked for and plan.md adopted). Tasks that
touch the same file are **not** marked `[P]` even across different user
stories, since concurrent edits to one file would conflict — see
Dependencies & Execution Order below.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create `src/notes_mcp/apple/__init__.py` as an empty package marker
- [ ] T002 [P] Create test directory skeleton: `tests/unit/apple/__init__.py` and `tests/integration/apple/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Define the exception hierarchy in `src/notes_mcp/apple/core.py`: `AppleNotesError` (base), `NotFoundError`, `AlreadyExistsError`, `InvalidPatternError`, `AutomationPermissionError`, `NotImplementedYetError`, `AmbiguousMatchError` (per contracts/apple_core_api.md) (depends on T001)
- [ ] T004 Implement the private `_run_jxa(script: str, args: list[str])` helper in `src/notes_mcp/apple/core.py`: invokes `osascript -l JavaScript -e SCRIPT -- args...` via `subprocess`, passes arguments through argv (never string-interpolated, per research.md §1), parses JSON stdout, classifies failures (including `osascript`'s `-1743` permission error) into the exceptions from T003, and logs the call's outcome/duration via stdlib `logging` (depends on T003)
- [ ] T005 [P] Unit test for `_run_jxa`'s error classification — mocked `subprocess.run` covering a successful JSON response, a `-1743` permission failure, and a generic failure — in `tests/unit/apple/test_core_unit.py` (depends on T004)
- [ ] T006 [P] Create `tests/integration/apple/conftest.py` with: a `notes_available` fixture/marker that skips tests when not on macOS or Notes.app isn't scriptable; a `scratch_folder` fixture that creates a dedicated top-level test folder directly via `_run_jxa` (bypassing `mkdir`/`rm`, since those are themselves under test) and removes it after the test session; and a `seed_note(folder_path, name, body)` helper that creates a note directly via `_run_jxa` (since no function in this feature's scope creates notes except `append`'s own create path, which tests shouldn't rely on to set up their own fixtures) for tests to seed fixture data (depends on T004)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - List folder contents (Priority: P1) 🎯 MVP

**Goal**: `ls(folder_path)` returns the immediate notes and subfolders inside a folder.

**Independent Test**: Call `ls` against the scratch folder (empty, then seeded) and confirm the result exactly matches its real contents.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Integration test: `ls` on an empty `scratch_folder` returns an empty `FolderListing`; after seeding one note (`seed_note`) and one subfolder (created directly via `_run_jxa`, not `mkdir`), `ls` returns exactly those two entries — in `tests/integration/apple/test_core_integration.py` (depends on T006)
- [ ] T008 [P] [US1] Unit test: `ls` raises `NotFoundError` for a folder path that doesn't exist, using a mocked `_run_jxa` "not found" response — in `tests/unit/apple/test_core_unit.py` (depends on T004)

### Implementation for User Story 1

- [ ] T009 [US1] Implement `ls(folder_path: str) -> FolderListing` in `src/notes_mcp/apple/core.py`, batch-fetching notes'/subfolders' properties in one call per folder (research.md §6) (depends on T004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — `ls` works against real Notes data.

---

## Phase 4: User Story 2 - Search note content (Priority: P2)

**Goal**: `grep(pattern, folder_path=None)` returns notes whose content matches a regular expression.

**Independent Test**: Seed a note with known text, `grep` for a matching pattern and confirm it's returned; `grep` for a non-matching pattern and confirm an empty result.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T010 [P] [US2] Integration test: `grep` finds a `seed_note`-created note by a matching pattern within `scratch_folder`, and returns an empty list for a non-matching pattern — in `tests/integration/apple/test_core_integration.py` (depends on T006)
- [ ] T011 [P] [US2] Unit test: `grep` raises `InvalidPatternError` for a malformed regular expression, without invoking `_run_jxa` at all — in `tests/unit/apple/test_core_unit.py` (depends on T004)

### Implementation for User Story 2

- [ ] T012 [US2] Implement `grep(pattern: str, folder_path: str | None = None) -> list[Note]` in `src/notes_mcp/apple/core.py`: validate the pattern with `re.compile` before any Notes call, batch-fetch plaintext via `_run_jxa`, and match in Python (research.md §5) (depends on T004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Create a folder (Priority: P3)

**Goal**: `mkdir(parent_path, name)` creates a new, empty folder.

**Independent Test**: Call `mkdir` under `scratch_folder`, then call `ls` (US1) on the parent and confirm the new folder appears.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T013 [US3] Integration test: `mkdir` creates a folder under `scratch_folder`, verified via `ls` (per spec's Independent Test) — in `tests/integration/apple/test_core_integration.py` (depends on T006, T009)
- [ ] T014 [US3] Integration test: `mkdir` raises `AlreadyExistsError` for a duplicate name under the same parent, and `NotFoundError` when `parent_path` doesn't exist — in `tests/integration/apple/test_core_integration.py` (depends on T006; same file as T013, sequential)

### Implementation for User Story 3

- [ ] T015 [US3] Implement `mkdir(parent_path: str, name: str) -> Folder` in `src/notes_mcp/apple/core.py` (depends on T004)

**Checkpoint**: At this point, User Stories 1, 2 AND 3 should all work independently.

---

## Phase 6: User Story 4 - Move or rename a note or folder (Priority: P4)

**Goal**: `mv(kind, identifier, destination_folder_path, new_name=None)` relocates and/or renames a note or folder.

**Independent Test**: Seed a note and create a folder (via `mkdir`), move/rename each, and confirm via `ls` that they appear at their new location/name and not the old one.

### Tests for User Story 4 (MANDATORY) ⚠️

- [ ] T016 [US4] Integration test: `mv` relocates a `seed_note`-created note to a different folder, and renames a folder created via `mkdir`; both verified via `ls` before/after — in `tests/integration/apple/test_core_integration.py` (depends on T006, T009, T015; same file as T013/T014, sequential)
- [ ] T017 [P] [US4] Unit test: `mv` raises `NotFoundError` for a nonexistent note `identifier` or folder `identifier`, using a mocked `_run_jxa` response — in `tests/unit/apple/test_core_unit.py` (depends on T004)

### Implementation for User Story 4

- [ ] T018 [US4] Implement `mv(kind: Literal["note","folder"], identifier: str, destination_folder_path: str, new_name: str | None = None) -> Note | Folder` in `src/notes_mcp/apple/core.py` (depends on T004)

**Checkpoint**: At this point, User Stories 1-4 should all work independently.

---

## Phase 7: User Story 5 - Reserve a removal function, stubbed for now (Priority: P5)

**Goal**: `rm(kind, identifier)` exists with a stable signature but is a pure stub — it always raises `NotImplementedYetError` and never touches Notes data.

**Independent Test**: Call `rm` on an existing note/folder and confirm (1) it still appears via `ls` afterward and (2) `rm` raised `NotImplementedYetError`.

### Tests for User Story 5 (MANDATORY) ⚠️

- [ ] T019 [P] [US5] Unit test: `rm` always raises `NotImplementedYetError` for any `kind`/`identifier`, and never calls `_run_jxa` (assert-not-called on a mock) — in `tests/unit/apple/test_core_unit.py` (depends on T004)

### Implementation for User Story 5

- [ ] T020 [US5] Implement `rm(kind: Literal["note","folder"], identifier: str) -> NoReturn` in `src/notes_mcp/apple/core.py`: immediately raises `NotImplementedYetError`, no Notes interaction whatsoever (depends on T004)

**Checkpoint**: User Stories 1-5 are independently functional.

---

## Phase 8: User Story 6 - Read a note's content (Priority: P6)

**Goal**: `cat(note_id)` returns the plain-text content of an existing note.

**Independent Test**: Seed a note with known content, `cat` its id and confirm the exact content is returned; `cat` a nonexistent id and confirm a clear error.

### Tests for User Story 6 (MANDATORY) ⚠️

- [ ] T021 [P] [US6] Integration test: `cat` returns the exact content of a `seed_note`-created note — in `tests/integration/apple/test_core_integration.py` (depends on T006; same file as prior integration tests, sequential)
- [ ] T022 [P] [US6] Unit test: `cat` raises `NotFoundError` for a note id that doesn't exist, using a mocked `_run_jxa` "not found" response — in `tests/unit/apple/test_core_unit.py` (depends on T004)

### Implementation for User Story 6

- [ ] T023 [US6] Implement `cat(note_id: str) -> str` in `src/notes_mcp/apple/core.py` (depends on T004)

**Checkpoint**: User Stories 1-6 are independently functional.

---

## Phase 9: User Story 7 - Append to a note, creating it if it doesn't exist (Priority: P7)

**Goal**: `append(folder_path, name, text)` appends text to an existing note, or creates a new empty note first if none named `name` exists yet in `folder_path`; fails clearly if the name is ambiguous.

**Independent Test**: Call `append` against a folder/name with no matching note; confirm (via `ls`) exactly one note was created and (via `cat`) it contains exactly the given text. Call `append` again on that note with more text; confirm (via `cat`) both the original and new text are present.

### Tests for User Story 7 (MANDATORY) ⚠️

- [ ] T024 [US7] Integration test: `append` against a folder/name with no existing match creates exactly one new note (verified via `ls`) whose content (verified via `cat`) is exactly the given text, with no leading separator (research.md §6a) — in `tests/integration/apple/test_core_integration.py` (depends on T006, T009, T023; same file as prior integration tests, sequential)
- [ ] T025 [US7] Integration test: `append` to a `seed_note`-created note with existing content results in content (verified via `cat`) containing the original text, a newline, then the newly appended text — in `tests/integration/apple/test_core_integration.py` (depends on T006, T023; same file as T024, sequential)
- [ ] T026 [P] [US7] Unit test: `append` raises `AmbiguousMatchError` when a mocked `_run_jxa` response reports more than one note matching `(folder_path, name)`, and `NotFoundError` when `folder_path` doesn't exist — in `tests/unit/apple/test_core_unit.py` (depends on T004)

### Implementation for User Story 7

- [ ] T027 [US7] Implement `append(folder_path: str, name: str, text: str) -> Note` in `src/notes_mcp/apple/core.py`: look up notes named `name` in `folder_path`; raise `AmbiguousMatchError` if more than one match; if none, create a new empty note there first; append `text` (newline-separated if the note already had content, per research.md §6a) (depends on T004)

**Checkpoint**: All seven capabilities are independently functional.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Run `quickstart.md` validation end-to-end on a real macOS machine with Notes configured, confirming SC-001 through SC-007
- [ ] T029 Review `src/notes_mcp/apple/core.py` for consistent naming/docstrings, confirm every function logs per the Observability principle, and remove any dead code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 3's success test (T013), User Story 4 (T016), and User Story 7 (T024) depend on User Story 1's `ls` (T009) for verification, per the spec's own Independent Test wording — these stories are not fully parallel-independent for this reason
  - User Story 4 (T016) also depends on User Story 3's `mkdir` (T015) to create a folder to move/rename
  - User Story 7 (T024, T025) depends on User Story 6's `cat` (T023) to verify its own effects
  - User Story 5 and User Story 6 have no dependency on any other story's implementation
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Same-File Sequencing (overrides story-parallel opportunities)

- All of `src/notes_mcp/apple/core.py` (T003, T004, T009, T012, T015, T018, T020, T023, T027) must be edited sequentially, in that order, regardless of which story they belong to
- All of `tests/unit/apple/test_core_unit.py` (T005, T008, T011, T017, T019, T022, T026) must be edited sequentially
- All of `tests/integration/apple/test_core_integration.py` (T007, T010, T013, T014, T016, T021, T024, T025) must be edited sequentially
- `tests/integration/apple/conftest.py` (T006) has no same-file conflicts with the above

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- `_run_jxa` (Foundational) before any function that calls it
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- T005 and T006 (Foundational) can run in parallel — different files
- T007 (integration file) and T008 (unit file) can run in parallel
- T010 (integration file) and T011 (unit file) can run in parallel
- T017 (unit file) can run in parallel with T016 (integration file)
- T019 (unit file) has no same-phase file conflict
- T021 (integration file) and T022 (unit file) can run in parallel
- T026 (unit file) can run in parallel with T024/T025 (integration file)
- T028 (Polish) can run in parallel with T029

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 tests together (different files):
Task: "Integration test: ls on scratch_folder returns correct entries in tests/integration/apple/test_core_integration.py"
Task: "Unit test: ls raises NotFoundError for a nonexistent folder in tests/unit/apple/test_core_unit.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm `ls` works against the scratch folder
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (`ls`) → Validate independently
3. Add User Story 2 (`grep`) → Validate independently
4. Add User Story 3 (`mkdir`) → Validate independently (uses `ls` to verify)
5. Add User Story 4 (`mv`) → Validate independently (uses `mkdir` + `ls`)
6. Add User Story 5 (`rm` stub) → Validate independently
7. Add User Story 6 (`cat`) → Validate independently
8. Add User Story 7 (`append`) → Validate independently (uses `cat` + `ls`)
9. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies — see the Same-File
  Sequencing note above for why this feature has fewer `[P]` tasks than a
  typical multi-file feature
- [Story] label maps task to specific user story for traceability
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Integration tests seed their own fixture data (`seed_note`, direct
  `_run_jxa` subfolder creation) rather than using the functions under
  test to set themselves up — this avoids circular test dependencies
  (e.g. testing `mkdir` using `mkdir`, or testing `append`'s create path
  using `append` itself to seed a pre-existing note) and keeps each
  story's tests from secretly depending on another story's implementation
  being correct
- `append` (US7) is this feature's first production capability that can
  create a *note* (`mkdir`, US3, only creates folders) — see research.md
  §8's note on why test fixtures still use `seed_note` rather than
  `append` for that purpose
