---

description: "Task list template for feature implementation"
---

# Tasks: Move and Remove a Note

**Input**: Design documents from `/specs/004-remove-move-note/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per the project constitution (Test-First, Test-Always) and spec FR-010, every user story below includes mandatory test tasks. Write tests first, confirm they fail, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Single project layout (per plan.md): `src/notes_mcp/tools/` (one module per
tool), `src/notes_mcp/apple/core.py` (backend, gains `rm`'s real note-path
implementation), and `tests/{contract,unit,integration}/`.

**No Setup or Foundational phase**: unlike feature 003, this feature needs
no new shared infrastructure — the test directory layout
(`tests/unit/tools/`, `tests/integration/tools/`) and shared scratch-folder
fixtures already exist from that feature, and no existing tool is being
retired. Both user stories can begin immediately.

**Same-file constraint**: both tools' registrations land in the single
shared `src/notes_mcp/server.py`, so those two tasks (T004, T012) are not
`[P]` relative to each other.

---

## Phase 1: User Story 1 - Move a note to a different folder (Priority: P1) 🎯 MVP

**Goal**: `move_note(note_id, destination_folder_path, new_name=None)` moves a note to a different folder, optionally renaming it in the same call, via `apple.core.mv`'s existing note-moving path. No new backend logic.

**Independent Test**: Call the tool with a note and a different, existing destination folder; confirm (via listing) the note is gone from its original folder and present in the destination.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T001 [P] [US1] Contract test: `move_note` is registered with input `{note_id, destination_folder_path}` (required strings) plus `new_name` (optional string, default null), and output unwrapped as a `Note` — in `tests/contract/test_move_note_contract.py`
- [ ] T002 [P] [US1] Unit test: mocking `apple.core.mv`, verify `move_note` passes through the moved `Note` as-is and that `NotFoundError` (missing note or missing destination folder) propagates — in `tests/unit/tools/test_move_note_unit.py`

### Implementation for User Story 1

- [ ] T003 [P] [US1] Implement `move_note(note_id: str, destination_folder_path: str, new_name: str | None = None) -> Note` in `src/notes_mcp/tools/move_note.py`, calling `apple.core.mv(kind="note", identifier=note_id, destination_folder_path=destination_folder_path, new_name=new_name)` directly
- [ ] T004 [US1] Register `move_note` in `src/notes_mcp/server.py` (depends on T003)
- [ ] T005 [P] [US1] Integration test against real Notes.app covering `move_note`'s edge cases (research.md §1): move to a different existing folder, move + rename in the same call, move to the folder it's already in (succeeds as a no-op), move to the folder it's already in with a new name (renames in place) — in `tests/integration/tools/test_move_note_integration.py` (depends on T003, T004)

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 2: User Story 2 - Remove a note (Priority: P2)

**Goal**: `remove_note(note_id)` archives a note into the well-known, top-level `archive` folder (auto-created on first use, same location as `update_note`'s replacement mode from feature 003) rather than permanently deleting it. This is the first real implementation of `apple.core.rm`'s note path, which has been an explicit stub since feature 002.

**Independent Test**: Call the tool with an existing note; confirm (via listing) the note is gone from its original folder and now appears, unchanged, in the well-known top-level `archive` folder.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T006 [P] [US2] Contract test: `remove_note` is registered with input `{note_id: string}`, required, and output unwrapped as a `Note` — in `tests/contract/test_remove_note_contract.py`
- [ ] T007 [P] [US2] Unit test: mocking `apple.core.rm`, verify `remove_note` passes through the resulting `Note` as-is and that `NotFoundError` propagates — in `tests/unit/tools/test_remove_note_unit.py`

### Implementation for User Story 2

- [ ] T008 [US2] Implement `apple.core.rm`'s real note-removal behavior in `src/notes_mcp/apple/core.py` (research.md §2): for `kind="note"`, ensure the top-level `archive` folder exists (call `mkdir("", "archive")`, swallowing `AlreadyExistsError`), then `mv(kind="note", identifier=identifier, destination_folder_path="archive")` and return the resulting `Note`; for `kind="folder"`, behavior is unchanged — still raises `NotImplementedYetError` immediately, before any of the above runs. Update `rm`'s docstring accordingly (no longer "always raises")
- [ ] T009 [P] [US2] Update `NotImplementedYetError`'s docstring in `src/notes_mcp/apple/exceptions.py` — it's now raised only by `rm`'s folder path, not notes (depends on T008)
- [ ] T010 [P] [US2] Update `TestRmStub` in `tests/unit/apple/test_core_unit.py`: note-kind tests now mock `subprocess` to verify the `mkdir`-then-`mv` composition (including a swallowed `AlreadyExistsError` from `mkdir`) and that the returned `Note` has `folder_path="archive"`; folder-kind tests are unchanged — still assert `NotImplementedYetError` and that `subprocess` is never called (depends on T008)
- [ ] T011 [P] [US2] Implement `remove_note(note_id: str) -> Note` in `src/notes_mcp/tools/remove_note.py`, calling `apple.core.rm(kind="note", identifier=note_id)` directly (depends on T008)
- [ ] T012 [US2] Register `remove_note` in `src/notes_mcp/server.py` (depends on T004, T011 — same file as T004, sequential)
- [ ] T013 [P] [US2] Update `TestRmIntegration` in `tests/integration/apple/test_core_integration.py`: the note-kind test now verifies real archiving against real Notes.app (note ends up in `archive`, content unchanged); the folder-kind test is unchanged — still expects `NotImplementedYetError` (depends on T008)
- [ ] T014 [P] [US2] New integration test against real Notes.app covering `remove_note`'s edge cases (research.md §2-3): basic archive (note moved into `archive`, content preserved), archive folder auto-created on first use, removing a note already in `archive` succeeds as a safe no-op — in `tests/integration/tools/test_remove_note_integration.py` (depends on T011, T012)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: Whole-server verification once both tools exist

- [ ] T015 Update `tests/contract/test_server_tool_registration.py` to assert `move_note` and `remove_note` are now advertised alongside the existing five tools (depends on T004, T012)
- [ ] T016 Extend the combined end-to-end flow in `tests/integration/tools/test_tools_integration.py` to also call `move_note` and `remove_note` (depends on T004, T012)
- [ ] T017 [P] Run `quickstart.md` validation end-to-end on a real macOS machine with Notes configured, confirming SC-001 through SC-003
- [ ] T018 Review `move_note.py`, `remove_note.py`, and `core.py`'s updated `rm` for consistent naming/docstrings, confirm no duplicate logging was added at the tool layer, and remove any dead code

---

## Dependencies & Execution Order

### Phase Dependencies

- **User Story 1 (Phase 1)**: No dependencies — can start immediately
- **User Story 2 (Phase 2)**: No dependency on User Story 1's completion; the only shared touchpoint is `server.py` (T004 must land before T012, since both edit the same file — see Same-File Sequencing below)
- **Polish (Phase 3)**: Depends on both user stories being complete

### Same-File Sequencing

- Both edits to `src/notes_mcp/server.py` (T004, T012) must happen sequentially, in that order
- `tests/contract/test_server_tool_registration.py` (T015) and `tests/integration/tools/test_tools_integration.py` (T016) are each touched once, in Polish, after both registrations exist

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 (US1 tests) can run in parallel with each other and with T006/T007 (US2 tests) — different files, no dependencies
- T003 (US1 implementation) has no dependency on anything in US2 and can proceed in parallel with all of US2's work up through T011
- Within US2, T009 and T010 can run in parallel with each other once T008 lands; T011 can also start as soon as T008 lands, in parallel with T009/T010
- T013 (backend integration test update) can run in parallel with T009/T010/T011 — different file, only depends on T008
- T017 (Polish) can run in parallel with T018

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 tests and implementation together (different files):
Task: "Contract test: move_note schema in tests/contract/test_move_note_contract.py"
Task: "Unit test: move_note with mocked apple.core.mv in tests/unit/tools/test_move_note_unit.py"
Task: "Implement move_note in src/notes_mcp/tools/move_note.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: User Story 1 (`move_note`)
2. **STOP and VALIDATE**: Confirm `move_note` works against real Notes data, including the same-folder edge cases
3. Deploy/demo if ready

### Incremental Delivery

1. Add User Story 1 (`move_note`) → Validate independently
2. Add User Story 2 (`remove_note`) → Validate independently — this is the story that gives `apple.core.rm` real behavior for the first time, so its backend change (T008) and the accompanying updates to feature 002's existing `rm` tests (T009, T010, T013) deserve extra care
3. Each story adds value without breaking the other

---

## Notes

- [P] tasks = different files, no dependencies — see Same-File Sequencing
  above for why the two `server.py`-touching tasks specifically can't be
  parallel even though almost everything else in this feature is
  independent
- [Story] label maps task to specific user story for traceability
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- `remove_note` is not a new backend capability — it's `rm`'s first real
  implementation for notes, composing the existing `mkdir`/`mv` functions
  exactly as `update_note`'s replacement mode already does (feature 003).
  This composition is intentionally duplicated between `apple.core.rm` and
  `tools/update_note.py` rather than factored into a shared helper: the
  constitution's stated threshold for introducing a shared abstraction is
  a *third* real use case, and this is only the second (research.md §2)
