# Implementation Plan: Apple Notes Core Backend Operations

**Branch**: `002-apple-notes-core-ops` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-apple-notes-core-ops/spec.md`

## Summary

Build a small backend module, `apple/core.py`, exposing five functions —
`ls`, `grep`, `mkdir`, `mv`, `rm` — that operate on real Apple Notes data
through macOS's officially sanctioned automation surface (JavaScript for
Automation, via `osascript`). No new dependency is introduced: `osascript`
ships with macOS, and all argument passing, JSON parsing, and regex
matching use the Python standard library. `rm` is a deliberate stub this
round (per Clarifications) — it reserves its call signature but performs
no real deletion, deferring recoverable-deletion and non-empty-folder
policy to a future feature. Not wired to any MCP tool in this feature, per
the spec's explicit scope boundary.

## Technical Context

**Language/Version**: Python 3.11+ (same package as the existing
`notes-mcp` server)

**Primary Dependencies**: None beyond the Python standard library
(`subprocess`, `json`, `re`, `logging`). Apple Notes automation goes
through the macOS-bundled `osascript` binary (JavaScript for Automation),
not a new pip package.

**Storage**: N/A — no local persistence; Apple Notes itself is the only
store, read and written live via automation calls on each function call.

**Testing**: pytest (already the project's test runner). Real
Notes-touching behavior (`ls`, `grep`, `mkdir`, `mv`) is covered by
integration tests that require macOS + Notes.app and are automatically
skipped otherwise; `rm`'s stub behavior is covered by a plain unit test
that needs no Notes access at all, since it never touches Notes data.

**Target Platform**: macOS (Notes.app via JavaScript for Automation), per
the constitution's Platform & Integration Constraints — no Linux/Windows
support.

**Project Type**: Single project — new `apple` subpackage inside the
existing `notes_mcp` package.

**Performance Goals**: `grep` completes in under 2 seconds for a
personal-scale collection (a few hundred notes), per spec SC-002 — met by
batch-fetching note properties per folder in one automation call rather
than one round trip per note.

**Constraints**: No new pip dependencies; automated tests must never
touch the developer's/user's real personal notes or folders (constitution
Principle II); functions must surface a clear, actionable error — not a
raw AppleScript/JXA error string — when Notes' Automation permission
hasn't been granted yet.

**Scale/Scope**: Personal-scale Notes collections (hundreds, not
thousands+, of notes/folders), consistent with SC-002.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity & YAGNI | PASS | One file, five functions, one small shared JXA-invocation helper (justified: all five functions need it right now, not a hypothetical future need). `rm` deliberately stays a stub rather than guessing at unimplemented policy. |
| II. Test-First, Test-Always | PASS (with a documented practical adaptation) | Every function gets a test. Apple Notes has no official sandbox/test-double API, so real Notes-touching tests run against a dedicated, clearly-named scratch test folder (not the user's real personal folders) and are skipped automatically off-macOS or without Notes.app — this is the project's concrete interpretation of "a sandboxed Notes environment." `rm`'s test needs no Notes access at all. |
| III. MCP Contract Integrity | N/A | Explicitly not wired to any MCP tool in this feature (spec Assumptions); applies when a future feature exposes these as tools. |
| IV. Safe, Reversible Data Operations | PASS | The only potentially destructive capability, `rm`, is a no-op stub this round — zero destructive risk. `mv` relocates/renames but never destroys content. `ls`/`grep` are read-only per FR-008. |
| V. Observability & Debuggability | PASS | Each function logs its name, outcome, and duration via stdlib `logging` (same pattern as the existing `list_folders` tool); automation failures (including permission-not-granted) are translated into a small set of typed exceptions with actionable messages, not raw AppleScript/JXA error text. |
| VI. Minimal, Justified Dependencies | PASS | Zero new dependencies — `osascript` is macOS-bundled; all parsing/matching uses the standard library. |

No violations. Complexity Tracking table is not needed for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/002-apple-notes-core-ops/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── apple_core_api.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/notes_mcp/
├── server.py                  # existing — untouched by this feature
├── apple/
│   ├── __init__.py             # new — package marker
│   └── core.py                 # new — ls, grep, mkdir, mv, rm + private JXA-invocation
│                                #        helper + the module's exception classes
└── tools/
    └── list_folders.py        # existing — untouched by this feature

tests/
├── contract/                   # existing — MCP tool contract tests, untouched
├── unit/
│   └── apple/
│       └── test_core_unit.py   # new — rm stub behavior, invalid-regex rejection,
│                                #        kind/identifier validation (no real Notes needed)
└── integration/
    └── apple/
        └── test_core_integration.py  # new — ls/grep/mkdir/mv against a dedicated
                                       #        scratch test folder in real Notes;
                                       #        skipped off-macOS or without Notes.app
```

**Structure Decision**: Single project (unchanged from the sibling
`001-mcp-server-scaffold` feature). `apple` is added as a subpackage of the
existing `notes_mcp` package (`src/notes_mcp/apple/core.py`), matching how
the user asked for "a file called apple/core.py" while staying consistent
with this repo's existing src-layout package. A new `tests/integration/`
directory is introduced — the sibling feature didn't need it (its one tool
was cheap to test in-process), but this feature's functions genuinely
integrate with an external system (Notes.app), which is a different test
category from the existing `contract/` (MCP protocol schema) and `unit/`
(pure logic) directories.

## Complexity Tracking

*No entries — Constitution Check reported no violations.*
