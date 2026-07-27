# Implementation Plan: Move and Remove a Note

**Branch**: `004-remove-move-note` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-remove-move-note/spec.md`

## Summary

Add two MCP tools: `move_note` (a direct wrap of the existing
`apple.core.mv` note-moving path — no new backend logic) and
`remove_note` (a thin wrap of `apple.core.rm`, whose note-removal
behavior this feature implements for real for the first time — it has
been an explicit stub since feature 002, reserved for exactly this).
Removing a note archives it into the same single, well-known, top-level
`archive` folder already established by `update_note`'s replacement mode
(feature 003) — auto-created on first use, reusing the existing `mkdir`
root-folder fix from that feature. `rm` called with a folder remains the
existing not-implemented stub; only the note path gains real behavior.

## Technical Context

**Language/Version**: Python 3.11+ (existing `notes-mcp` package)

**Primary Dependencies**: None beyond what's already in the project — the
`mcp` SDK (already a dependency) and `notes_mcp.apple.core`'s existing
`mv` and `mkdir` functions, which this feature composes but does not
change. No JXA script changes are needed: `mkdir.js`'s root-folder
creation (feature 003) and `mv_note.js`'s existing same-destination no-op
guard (feature 002, see research.md §1) already provide everything this
feature needs.

**Storage**: N/A — no new persistence; both tools are pass-throughs to
the existing backend.

**Testing**: pytest (existing). Same three-tier split as features 002/003:
`tests/unit/tools/` (mocked `apple.core`), `tests/unit/apple/` (mocked
`subprocess`, for `rm`'s new real behavior), `tests/contract/` (schema),
`tests/integration/` (real Notes.app, shared scratch-folder fixtures).

**Target Platform**: macOS (unchanged).

**Project Type**: Single project — two new modules under
`notes_mcp.tools`, a real implementation for `apple.core.rm`'s note path,
and `server.py` registration edits.

**Performance Goals**: None new.

**Constraints**: No new dependencies; every tool's errors must reach the
MCP client as a structured result (verified in feature 003, unchanged
mechanism); `remove_note` must never permanently delete a note's content
— archiving only, per the constitution's Safe, Reversible Data Operations
principle; folder-kind `rm` behavior must remain unchanged (still raises
`NotImplementedYetError`).

**Scale/Scope**: Same personal-scale target as prior features; two tools,
each a few lines, plus `rm`'s note-path implementation (also a few lines,
mirroring `update_note`'s existing archive composition).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity & YAGNI | PASS | `move_note` is a thin, direct wrap of `mv` — no new logic at all. `rm`'s note-path implementation composes existing `mkdir`/`mv` exactly like `update_note`'s replacement mode already does (feature 003) — duplicated rather than factored into a shared helper, since this is only the *second* real use case of that composition; the constitution's own threshold (three similar cases before abstracting) isn't met yet. Folder-kind `rm` is deliberately left unchanged, not generalized ahead of a real need. |
| II. Test-First, Test-Always | PASS | Both tools get contract + unit + integration tests. `rm`'s existing feature-002 tests are updated: note-kind tests now cover real archiving behavior instead of asserting `NotImplementedYetError`; folder-kind tests are unchanged (still assert the stub error). |
| III. MCP Contract Integrity | PASS | Both tools' input/output schemas are documented in contracts/, following the same verified-against-the-real-SDK approach as feature 003. |
| IV. Safe, Reversible Data Operations | PASS | This feature exists specifically to satisfy this principle for "remove": it archives (via the same reversible, already-tested `mv` primitive) rather than deleting. No new deletion capability is introduced anywhere. |
| V. Observability & Debuggability | PASS | `rm`'s note-path implementation composes calls that already go through `_run_jxa`'s existing logging; no duplicate logging added at the tool or backend-composition layer. |
| VI. Minimal, Justified Dependencies | PASS | Zero new dependencies. |

No violations. Complexity Tracking table is not needed for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/004-remove-move-note/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/            # Phase 1 output (/speckit-plan command)
│   └── mcp_tools_api.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/notes_mcp/
├── server.py                  # updated — register move_note, remove_note
├── apple/
│   └── core.py                # updated — rm(kind="note", ...) implemented for
│                               #           real (archives via mkdir+mv); rm(kind=
│                               #           "folder", ...) unchanged (still stub)
└── tools/
    ├── move_note.py            # new — wraps apple.core.mv (note path)
    └── remove_note.py          # new — wraps apple.core.rm (note path)

tests/
├── contract/
│   ├── test_move_note_contract.py    # new
│   └── test_remove_note_contract.py  # new
├── unit/
│   ├── apple/
│   │   └── test_core_unit.py         # updated — TestRmStub split: note-kind
│   │                                 #           tests now cover real archiving,
│   │                                 #           folder-kind tests unchanged
│   └── tools/
│       ├── test_move_note_unit.py    # new — mocked apple.core.mv
│       └── test_remove_note_unit.py  # new — mocked apple.core.rm
└── integration/
    ├── apple/
    │   └── test_core_integration.py  # updated — TestRmIntegration: note-kind
    │                                 #           test now covers real archiving
    │                                 #           (folder-kind test unchanged)
    └── tools/
        └── test_tools_integration.py # updated — extended to also exercise
                                       #           move_note and remove_note
```

**Structure Decision**: Single project (unchanged). Two new tool modules
under the existing `notes_mcp.tools` package, following the established
one-file-per-tool precedent. `apple.core.rm` gains a real implementation
for its note path only, in place — no new backend module, since `rm`
already exists specifically as this capability's placeholder.

## Complexity Tracking

*No entries — Constitution Check reported no violations.*
