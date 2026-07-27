# Implementation Plan: Move and Remove a Note

**Branch**: `004-remove-move-note` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-remove-move-note/spec.md`

## Summary

Add two MCP tools: `move_note` (a direct wrap of the existing
`apple.core.mv` note-moving path — no new backend logic) and
`remove_note` (which archives a note into the same single, well-known,
top-level `archive` folder already established by `update_note`'s
replacement mode from feature 003 — auto-created on first use, reusing
the existing `mkdir` root-folder fix from that feature).

Amendment (PR review, twice): `remove_note` composes
`apple.core.mkdir`/`mv` directly, at the tool layer — mirroring
`update_note`'s identical archive-on-replace composition — rather than
calling `apple.core.rm`. `apple.core.rm` itself is **entirely out of
scope** for this feature and remains exactly feature 002's original stub
(raises `NotImplementedYetError` for both `kind="note"` and
`kind="folder"`) — an interim design briefly implemented real
`kind="note"` delete behavior for `rm`, but that was reverted per
explicit maintainer direction, since `rm`'s own implementation is a
separate, future feature. `remove_note` never depended on `rm` being real
in the first place, so this feature ships unaffected by that reversion.

## Technical Context

**Language/Version**: Python 3.11+ (existing `notes-mcp` package)

**Primary Dependencies**: None beyond what's already in the project — the
`mcp` SDK (already a dependency) and `notes_mcp.apple.core`'s existing
`mv` and `mkdir` functions, which `remove_note` composes directly at the
tool layer without changing either. `mkdir.js`'s root-folder creation
(feature 003) and `mv_note.js`'s existing same-destination no-op guard
(feature 002, see research.md §1) already provide everything `move_note`
and `remove_note` need. No changes to `apple.core.rm` or any new JXA
script are in scope for this feature (research.md §2).

**Storage**: N/A — no new persistence; both tools are pass-throughs to
the existing backend.

**Testing**: pytest (existing). Same three-tier split as features 002/003:
`tests/unit/tools/` (mocked `apple.core`), `tests/contract/` (schema),
`tests/integration/` (real Notes.app, shared scratch-folder fixtures).
`rm`'s existing feature-002 tests (`tests/unit/apple/`,
`tests/integration/apple/`) are untouched.

**Target Platform**: macOS (unchanged).

**Project Type**: Single project — two new modules under
`notes_mcp.tools` and `server.py` registration edits. No changes to
`apple.core.rm`.

**Performance Goals**: None new.

**Constraints**: No new dependencies; every tool's errors must reach the
MCP client as a structured result (verified in feature 003, unchanged
mechanism); `remove_note` must never permanently delete a note's content
— archiving only, per the constitution's Safe, Reversible Data Operations
principle; `apple.core.rm` (both kinds) must remain unchanged from
feature 002, out of scope for this feature.

**Scale/Scope**: Same personal-scale target as prior features; two tools,
each a few lines.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity & YAGNI | PASS | `move_note` is a thin, direct wrap of `mv` — no new logic at all. `remove_note`'s archive composition (`mkdir`+`mv`) lives at the tool layer, duplicated from `update_note`'s identical composition rather than factored into a shared helper, since this is only the *second* real use case; the constitution's own threshold (three cases before abstracting) isn't met yet. `apple.core.rm` is untouched, unchanged from feature 002 — implementing it for real was explicitly kept out of this feature's scope on review, rather than folded in incidentally just because the layering discussion surfaced what it "should" do. |
| II. Test-First, Test-Always | PASS | Both tools get contract + unit + integration tests. `rm`'s existing feature-002 tests are untouched — still asserting `NotImplementedYetError` for both kinds, unchanged. `remove_note`'s own unit tests mock `mkdir`/`mv` directly, matching what it actually calls. |
| III. MCP Contract Integrity | PASS | Both tools' input/output schemas are documented in contracts/, following the same verified-against-the-real-SDK approach as feature 003. |
| IV. Safe, Reversible Data Operations | PASS | `remove_note` (the tool) archives via the same reversible, already-tested `mv` primitive, never deletes — this principle's tool-level guarantee holds independent of `apple.core.rm`, since no tool in this feature calls it and `rm` itself is unchanged. |
| V. Observability & Debuggability | PASS | `remove_note`'s composition goes through `_run_jxa`'s existing logging; no duplicate logging added at the tool layer. |
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
│   └── core.py                # UNCHANGED — rm remains feature 002's stub
└── tools/
    ├── move_note.py            # new — wraps apple.core.mv (note path)
    └── remove_note.py          # new — composes apple.core.mkdir + apple.core.mv
                                 #      directly (mirrors update_note.py); does
                                 #      NOT call apple.core.rm

tests/
├── contract/
│   ├── test_move_note_contract.py    # new
│   └── test_remove_note_contract.py  # new
├── unit/
│   ├── apple/
│   │   └── test_core_unit.py         # UNCHANGED — TestRmStub still asserts
│   │                                 #             NotImplementedYetError
│   │                                 #             for both kinds
│   └── tools/
│       ├── test_move_note_unit.py    # new — mocked apple.core.mv
│       └── test_remove_note_unit.py  # new — mocked apple.core.mkdir/mv
└── integration/
    ├── apple/
    │   └── test_core_integration.py  # UNCHANGED — TestRmIntegration still
    │                                 #             asserts nothing is removed
    └── tools/
        ├── test_move_note_integration.py    # new
        ├── test_remove_note_integration.py  # new
        └── test_tools_integration.py # updated — extended to also exercise
                                       #           move_note and remove_note
```

**Structure Decision**: Single project (unchanged). Two new tool modules
under the existing `notes_mcp.tools` package, following the established
one-file-per-tool precedent. `apple.core.rm` and its existing tests are
untouched — out of scope for this feature. `remove_note` does not depend
on or call `rm`; its archive composition lives entirely at the tool
layer.

## Complexity Tracking

*No entries — Constitution Check reported no violations.*
