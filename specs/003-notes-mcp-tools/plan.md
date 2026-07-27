# Implementation Plan: Apple Notes MCP Tools

**Branch**: `003-notes-mcp-tools` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-notes-mcp-tools/spec.md`

## Summary

Expose the existing `notes_mcp.apple.core` backend (`ls`, `grep`, `cat`,
`append`) as five MCP tools — `list_folder_contents`, `search_notes`,
`read_note`, `create_note`, `update_note` — each a thin wrapper that calls
the corresponding backend function and returns its result. No new backend
logic and no new dependencies: the `mcp` SDK already converts any
exception raised inside a tool into a proper `isError: true` result
without crashing the server (verified empirically), so the wrappers don't
need their own error-handling code. The existing placeholder `list_folders`
tool, its stub data, and its dedicated tests are retired as part of this
feature (FR-011), per the resolved clarification.

`update_note` additionally takes a boolean replacement flag (default
`false`, FR-012). When `true` and a note already exists, it archives the
existing note (via the backend's existing `mv`, into a single, auto-created
top-level archive folder) before creating a replacement via `append` — a
composition of already-existing backend primitives (`ls` to check for an
existing match, `mv`, `append`) at the tool layer, not a new backend
capability (research.md §8). One narrow exception: `mkdir` currently
cannot create a *top-level* folder at all (verified empirically), which
the archive location needs to be — a small, targeted fix to
`jxa_scripts/mkdir.js` is in scope here (research.md §8), not a new
function.

## Technical Context

**Language/Version**: Python 3.11+ (existing `notes-mcp` package)

**Primary Dependencies**: None beyond what's already in the project —
`mcp` (already a dependency, for `FastMCP`) and `notes_mcp.apple.core`
(already built, this project's own backend module — `update_note`'s
replacement mode additionally calls the backend's existing `ls`, `mv`,
and `mkdir` functions; `mkdir` needs a small, scoped fix to support
top-level folder creation, which it currently cannot do at all —
research.md §8).

**Storage**: N/A — no new persistence; each tool is a pass-through to the
existing backend, which itself talks to Notes.app live.

**Testing**: pytest (existing). Two tiers, mirroring the backend's own
split: `tests/unit/tools/` mocks the underlying `apple.core` functions to
test each tool's schema and error-translation behavior without touching
real Notes; `tests/integration/tools/` exercises the real tools against
real Notes.app, reusing the scratch-folder fixture infrastructure already
built for the backend (moved up one directory level so both consumers can
share it — see research.md §7).

**Target Platform**: macOS (unchanged — Notes.app via JXA, per the
constitution's Platform & Integration Constraints).

**Project Type**: Single project — five new modules under the existing
`notes_mcp.tools` package, plus edits to `server.py`.

**Performance Goals**: None new. SC-001 (two tool calls to go from listing
to reading) is a usability metric, not a latency target; the underlying
backend's own performance guarantees (e.g. `grep`'s SC-002 from feature
002) are unchanged since these tools add no processing of their own.

**Constraints**: No new dependencies; every tool's errors must reach the
MCP client as a structured result, never a server crash (verified
achievable via the SDK's built-in behavior — research.md §2); the
existing placeholder `list_folders` tool must be fully retired, not left
running alongside the new tools (FR-011); `update_note`'s replacement
mode must archive the original note before creating its replacement, never
the other order, so a failure partway through never loses content with no
replacement created (FR-014).

**Scale/Scope**: Same personal-scale target as the backend (hundreds of
notes/folders); five tools, each a few lines of wrapper code.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity & YAGNI | PASS | Each tool is a thin, direct wrapper around one existing backend function — no new abstraction layer, no shared "tool base class." `create_note`/`update_note` are two small separate functions rather than one parameterized helper, since the point of having two tools is the distinct metadata/description an MCP client sees, not code reuse. `update_note`'s replacement mode composes existing `ls`/`mv`/`mkdir`/`append` primitives directly, in-line, rather than introducing a new backend abstraction for "archive and replace." The one backend change (`mkdir.js`'s root-folder fix) is scoped to exactly the gap this feature hit, not generalized further than needed. |
| II. Test-First, Test-Always | PASS | Every tool gets a mocked unit test (schema/error-translation) and a real-Notes integration test, per FR-009 — including `update_note`'s replace-mode archive-then-recreate path and its archive-location auto-creation path. The backend's existing test infrastructure is reused, not duplicated. |
| III. MCP Contract Integrity | PASS | This is the first feature where this principle is fully live (feature 002 was N/A — backend only). Every tool's input/output schema is documented in contracts/, including `update_note`'s new `overwrite` parameter; errors surface as explicit `isError: true` results with a descriptive message, never a silent failure or a crash (FR-007). |
| IV. Safe, Reversible Data Operations | PASS | `create_note` and `update_note`'s default (append) mode are purely additive, backed by `append`, which never overwrites or removes content. `update_note`'s replacement mode is a deliberate exception this constitution explicitly anticipates ("prefer additive/reversible operations... over hard deletes"): it never deletes — it archives the original (via `mv`) before creating a replacement, and archiving is required to complete first (FR-014) so a partial failure can never silently lose content. No tool in this feature performs an actual deletion. |
| V. Observability & Debuggability | PASS | The backend (`apple.core`) already logs every underlying call's name, outcome, and duration; since each tool is a direct 1:1 wrapper (or, for `update_note`'s replace mode, a direct 1:1 composition of existing backend calls), no duplicate logging is added at the tool layer (would be redundant, not more observable). |
| VI. Minimal, Justified Dependencies | PASS | Zero new dependencies. |

No violations. Complexity Tracking table is not needed for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/003-notes-mcp-tools/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/            # Phase 1 output (/speckit-plan command)
│   └── mcp_tools_api.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/notes_mcp/
├── server.py                       # updated — remove list_folders registration,
│                                    #           register the 5 new tools
├── apple/
│   └── jxa_scripts/mkdir.js        # updated — small, scoped fix: parent_path=""
│                                    #           now creates a top-level folder,
│                                    #           needed for the archive location
│                                    #           (research.md §8); everything else
│                                    #           in apple/ is untouched
└── tools/
    ├── list_folders.py             # REMOVED — retired placeholder (FR-011)
    ├── list_folder_contents.py     # new — wraps apple.core.ls
    ├── search_notes.py             # new — wraps apple.core.grep
    ├── read_note.py                # new — wraps apple.core.cat
    ├── create_note.py              # new — wraps apple.core.append
    └── update_note.py              # new — wraps apple.core.append; when
                                     #      overwrite=True, also composes
                                     #      apple.core.mkdir (archive folder,
                                     #      if missing) and apple.core.mv
                                     #      (archive the original note first)

tests/
├── contract/
│   ├── test_list_folders_contract.py       # REMOVED — tested the retired tool
│   ├── test_server_tool_registration.py    # updated — expects the 5 new tool
│   │                                       #           names, not list_folders
│   ├── test_server_startup_stdio.py        # updated — same reference swap
│   ├── test_list_folder_contents_contract.py  # new
│   ├── test_search_notes_contract.py          # new
│   ├── test_read_note_contract.py             # new
│   ├── test_create_note_contract.py           # new
│   └── test_update_note_contract.py           # new
├── unit/
│   ├── test_list_folders.py        # REMOVED — tested the retired stub
│   └── tools/
│       ├── test_list_folder_contents_unit.py  # new — mocked apple.core.ls
│       ├── test_search_notes_unit.py          # new — mocked apple.core.grep
│       ├── test_read_note_unit.py             # new — mocked apple.core.cat
│       ├── test_create_note_unit.py           # new — mocked apple.core.append
│       └── test_update_note_unit.py           # new — mocked apple.core.append
└── integration/
    ├── conftest.py                   # MOVED from tests/integration/apple/conftest.py —
    │                                 # now shared by apple/ and tools/ (research.md §7)
    ├── apple/                        # existing backend integration tests — untouched
    └── tools/
        └── test_tools_integration.py  # new — the 5 tools against real Notes.app
```

**Structure Decision**: Single project (unchanged). Five new modules under
the existing `notes_mcp.tools` package — one file per tool, matching the
existing `list_folders.py` precedent — plus `server.py` edits to swap the
old registration for the five new ones. The shared scratch-folder test
fixtures move from `tests/integration/apple/conftest.py` up to
`tests/integration/conftest.py`: this feature is a second real consumer of
that fixture, which is exactly the point (per Principle I) at which
sharing it stops being speculative and starts being justified reuse.

## Complexity Tracking

*No entries — Constitution Check reported no violations.*
