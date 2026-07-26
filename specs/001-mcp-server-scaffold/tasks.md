---

description: "Task list template for feature implementation"
---

# Tasks: MCP Server Scaffold with Dummy list_folders Tool

**Input**: Design documents from `/specs/001-mcp-server-scaffold/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per the project constitution (Test-First, Test-Always) and spec FR-006, every user story below includes mandatory test tasks. Write tests first, confirm they fail, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project layout (per plan.md): `src/notes_mcp/` and `tests/` at the repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create source and test directory skeleton per plan.md: `src/notes_mcp/`, `src/notes_mcp/tools/`, `tests/contract/`, `tests/unit/`
- [X] T002 [P] Create `pyproject.toml`: src-layout package `notes_mcp`, Python `>=3.11` requirement, `mcp` runtime dependency, and `pytest` as a dev dependency group (per research.md decisions on SDK choice, packaging, and test runner)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create `src/notes_mcp/__init__.py` and `src/notes_mcp/tools/__init__.py` as empty package markers (depends on T001)
- [X] T004 [P] Create `src/notes_mcp/server.py` with a `FastMCP` server instance, stdlib `logging` configuration (module-level logger, per research.md decision on observability), and a stdio entrypoint (`if __name__ == "__main__": mcp.run(transport="stdio")`); no tools registered yet (depends on T001, T002)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Runnable server scaffold (Priority: P1) 🎯 MVP

**Goal**: A developer can start the Python MCP server over stdio and it advertises `list_folders` in its tool list.

**Independent Test**: Start the server and, via an MCP client/test harness, request the tool list and confirm it includes `list_folders`.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T005 [P] [US1] Contract test verifying the server's advertised tool list includes `list_folders` in `tests/contract/test_server_tool_registration.py`

### Implementation for User Story 1

- [X] T006 [P] [US1] Implement the `list_folders` tool function returning the stub Folder list from data-model.md (`[{"id": "1", "name": "Notes"}, {"id": "2", "name": "Personal"}, {"id": "3", "name": "Work"}]`) in `src/notes_mcp/tools/list_folders.py`
- [X] T007 [US1] Register the `list_folders` tool with the FastMCP server instance in `src/notes_mcp/server.py` (depends on T004, T006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — server starts, `list_folders` is discoverable.

---

## Phase 4: User Story 2 - Call the list_folders tool (Priority: P2)

**Goal**: Calling `list_folders` returns the exact stubbed, schema-consistent folder list every time, with no side effects.

**Independent Test**: Call `list_folders` with no arguments, repeatedly, and confirm the response matches `contracts/list_folders.md` every time.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T008 [P] [US2] Contract test verifying `list_folders` called with `{}` returns exactly the schema and 3 entries defined in `contracts/list_folders.md`, and that repeated calls return identical results, in `tests/contract/test_list_folders_contract.py`
- [X] T009 [P] [US2] Unit test on the stub dataset itself — required fields present/non-empty and `id` values unique — in `tests/unit/test_list_folders.py`

### Implementation for User Story 2

- [X] T010 [US2] Add invocation logging (tool name, outcome, duration) around the `list_folders` call path in `src/notes_mcp/tools/list_folders.py`, using the logger configured in T004 (depends on T004, T007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Discover and run the project via the README (Priority: P3)

**Goal**: A new contributor can install, run, and verify the server using only `README.md`.

**Independent Test**: Follow `README.md` from a fresh clone and confirm the server runs and `list_folders` responds, without reading source code.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T011 [P] [US3] Add a check that `README.md` documents install, run, and verification steps (asserts required section headings are present) in `tests/unit/test_readme_contents.py`

### Implementation for User Story 3

- [X] T012 [US3] Write `README.md`: project description, prerequisites, install steps, run steps, and `list_folders` verification steps (per FR-005), following `quickstart.md` (depends on T002, T007)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T013 [P] Run `quickstart.md` validation end-to-end, confirming SC-001 (under 5 minutes) and SC-003
- [X] T014 Review `src/notes_mcp/` for consistent naming/docstrings and remove any dead code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 2 depends on User Story 1's `list_folders` implementation and registration (T006, T007) since it tests and instruments that same tool — this feature's stories are sequential rather than fully parallel due to their small, tightly-scoped nature
  - User Story 3 depends on User Story 1 (T007) being complete, since the README documents a working tool
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependencies on other stories
- **User Story 2 (P2)**: Builds on User Story 1's `list_folders` tool (T006, T007) - adds contract rigor and observability, not new tool surface
- **User Story 3 (P3)**: Builds on User Story 1's working tool (T007) to document it - independently testable via a fresh-clone walkthrough

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/tools before registration
- Registration before instrumentation/documentation
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- T003 and T004 (Foundational) can run in parallel
- T008 and T009 (User Story 2 tests) can run in parallel
- T013 (Polish) can run in parallel with T014

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 test and tool implementation together (different files):
Task: "Contract test verifying the server's advertised tool list includes list_folders in tests/contract/test_server_tool_registration.py"
Task: "Implement the list_folders tool function returning the stub Folder list in src/notes_mcp/tools/list_folders.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm the server starts and `list_folders` is discoverable
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Validate independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Validate independently → Deploy/Demo
4. Add User Story 3 → Validate independently → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- User Story 2 and 3 build directly on User Story 1's `list_folders` tool rather than being fully independent of it — reasonable for a single-tool scaffold feature this small; future features with multiple tools should return to stricter story independence
