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

Amendment (PR review): `remove_note` composes `apple.core.mkdir`/`mv`
directly, at the tool layer — mirroring `update_note`'s identical
archive-on-replace composition — rather than calling `apple.core.rm`.
`apple.core.rm`'s note path is implemented separately, for real, matching
what Notes.app's own delete mechanism actually does (moves a note into
Notes' native "Recently Deleted" folder, verified empirically — not an
instant permanent purge); it has been an explicit stub since feature 002,
reserved for exactly this, but no MCP tool in this feature calls it. `rm`
called with a folder remains the existing not-implemented stub.

## Technical Context

**Language/Version**: Python 3.11+ (existing `notes-mcp` package)

**Primary Dependencies**: None beyond what's already in the project — the
`mcp` SDK (already a dependency) and `notes_mcp.apple.core`'s existing
`mv` and `mkdir` functions, which `remove_note` composes directly at the
tool layer without changing. `mkdir.js`'s root-folder creation (feature
003) and `mv_note.js`'s existing same-destination no-op guard (feature
002, see research.md §1) already provide everything `move_note` and
`remove_note` need. One new JXA script, `rm_note.js`, was added for
`apple.core.rm`'s own real delete behavior (research.md §2) — a backend
primitive this feature's tools don't call.

**Storage**: N/A — no new persistence; both tools are pass-throughs to
the existing backend.

**Testing**: pytest (existing). Same three-tier split as features 002/003:
`tests/unit/tools/` (mocked `apple.core`), `tests/unit/apple/` (mocked
`subprocess`, for `rm`'s new real behavior), `tests/contract/` (schema),
`tests/integration/` (real Notes.app, shared scratch-folder fixtures).

**Target Platform**: macOS (unchanged).

**Project Type**: Single project — two new modules under
`notes_mcp.tools`, a real implementation for `apple.core.rm`'s note path
(a backend primitive, not tool-exposed), and `server.py` registration
edits.

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
| I. Simplicity & YAGNI | PASS | `move_note` is a thin, direct wrap of `mv` — no new logic at all. `remove_note`'s archive composition (`mkdir`+`mv`) lives at the tool layer, duplicated from `update_note`'s identical composition rather than factored into a shared helper, since this is only the *second* real use case; the constitution's own threshold (three cases before abstracting) isn't met yet. `apple.core.rm`'s note-path implementation is a separate, minimal, single-call JXA delete — no logic borrowed from or shared with the archive composition. Folder-kind `rm` is deliberately left unchanged, not generalized ahead of a real need. |
| II. Test-First, Test-Always | PASS | Both tools get contract + unit + integration tests. `rm`'s existing feature-002 tests are updated: note-kind tests now cover its real delete behavior (via `Notes.delete()`) instead of asserting `NotImplementedYetError`; folder-kind tests are unchanged (still assert the stub error). `remove_note`'s own unit tests mock `mkdir`/`mv` directly, matching what it actually calls. |
| III. MCP Contract Integrity | PASS | Both tools' input/output schemas are documented in contracts/, following the same verified-against-the-real-SDK approach as feature 003. `remove_note`'s schema/behavior is unaffected by the `rm`-vs-composition amendment — only its internal implementation changed. |
| IV. Safe, Reversible Data Operations | PASS | `remove_note` (the tool) archives via the same reversible, already-tested `mv` primitive, never deletes — this principle's tool-level guarantee holds regardless of what `apple.core.rm` does internally, since no tool in this feature calls `rm`. `apple.core.rm` itself performs a real delete (verified empirically to be Notes.app's own recoverable "Recently Deleted" mechanism, not an instant purge), but is a backend-only primitive with no tool exposing it — consistent with the principle's concern being about tool-call-level destructive intent, which doesn't arise here. |
| V. Observability & Debuggability | PASS | `remove_note`'s composition and `rm`'s delete call both go through `_run_jxa`'s existing logging; no duplicate logging added at the tool or backend layer. |
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
│   ├── core.py                # updated — rm(kind="note", ...) implemented for
│   │                          #           real (Notes.app's own delete, via a
│   │                          #           new rm_note.js); rm(kind="folder", ...)
│   │                          #           unchanged (still stub); not called by
│   │                          #           any tool in this feature
│   └── jxa_scripts/rm_note.js # new — Notes.delete(note) via noteById
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
│   │   └── test_core_unit.py         # updated — TestRmFolderStub (unchanged
│   │                                 #           assertions) + new TestRmNote
│   │                                 #           covering the real rm_note op
│   └── tools/
│       ├── test_move_note_unit.py    # new — mocked apple.core.mv
│       └── test_remove_note_unit.py  # new — mocked apple.core.mkdir/mv
└── integration/
    ├── apple/
    │   └── test_core_integration.py  # updated — TestRmIntegration: note-kind
    │                                 #           test now covers real deletion
    │                                 #           via Notes.app (folder-kind
    │                                 #           test unchanged)
    └── tools/
        ├── test_move_note_integration.py    # new
        ├── test_remove_note_integration.py  # new — unaffected by the rm
        │                                    #       amendment (tool behavior
        │                                    #       unchanged)
        └── test_tools_integration.py # updated — extended to also exercise
                                       #           move_note and remove_note
```

**Structure Decision**: Single project (unchanged). Two new tool modules
under the existing `notes_mcp.tools` package, following the established
one-file-per-tool precedent. `apple.core.rm` gains a real implementation
for its note path only, in place — no new backend module, since `rm`
already exists specifically as this capability's placeholder. `remove_note`
does not depend on or call `rm`; its archive composition lives entirely
at the tool layer.

## Complexity Tracking

*No entries — Constitution Check reported no violations.*
