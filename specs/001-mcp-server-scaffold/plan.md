# Implementation Plan: MCP Server Scaffold with Dummy list_folders Tool

**Branch**: `001-mcp-server-scaffold` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-mcp-server-scaffold/spec.md`

## Summary

Stand up a minimal, runnable Python MCP server using the official MCP Python
SDK over the stdio transport, exposing a single stub tool, `list_folders`,
that returns a fixed in-memory list of `{id, name}` folder objects (no real
Apple Notes access yet). This establishes the runnable foundation — protocol
plumbing, tool registration pattern, test setup, and README onboarding — that
later features will add real Notes-backed tools onto.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `mcp` (official Model Context Protocol Python SDK —
`mcp.server.fastmcp.FastMCP` high-level server API, stdio transport)

**Storage**: N/A — stub tool returns a hardcoded in-memory list, no persistence

**Testing**: pytest

**Target Platform**: macOS (local process, per constitution's Platform &
Integration Constraints — no Linux/Windows support claimed)

**Project Type**: Single project — local CLI-launched MCP server

**Performance Goals**: N/A for this stub — tool call round-trip should be
effectively instant (well under 100ms), as it does no I/O

**Constraints**: Local stdio transport only (no network-exposed transport in
scope); no third-party network calls; macOS only

**Scale/Scope**: Single-user local development tool; one MCP server process;
one tool (`list_folders`) for this feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity & YAGNI | PASS | One tool, one hardcoded stub dataset, no plugin/registry system, no config layer. Direct registration of the single tool with the SDK's decorator — no speculative extensibility for tools that don't exist yet. |
| II. Test-First, Test-Always | PASS | Plan includes a contract test asserting the `list_folders` output schema/shape, written before implementation (see Phase 1 contracts + tasks phase). |
| III. MCP Contract Integrity | PASS | `list_folders` has an explicit, documented input/output schema (see `contracts/list_folders.md`); no other tools exist yet to break. |
| IV. Safe, Reversible Data Operations | PASS (N/A) | `list_folders` is a pure read with no side effects and touches no real Notes data; no destructive operation exists in this feature. |
| V. Observability & Debuggability | PASS | Server logs each tool invocation (tool name, outcome, duration) via the stdlib `logging` module; no new dependency needed. |
| VI. Minimal, Justified Dependencies | PASS | Only dependency added is `mcp` itself (the protocol implementation — hand-rolling MCP's JSON-RPC framing would be a far larger, riskier undertaking). `pytest` is a dev-only addition, justified in `research.md`. |

No violations. Complexity Tracking table is not needed for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/001-mcp-server-scaffold/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/            # Phase 1 output (/speckit-plan command)
│   └── list_folders.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── notes_mcp/
    ├── __init__.py
    ├── server.py            # FastMCP server instance, stdio entrypoint, tool registration
    └── tools/
        ├── __init__.py
        └── list_folders.py  # list_folders tool: stub data + tool function

tests/
├── contract/
│   └── test_list_folders_contract.py   # validates list_folders output shape (FR-003, FR-006)
└── unit/
    └── test_list_folders.py            # unit test on the stub data function itself

pyproject.toml               # package metadata, `mcp` runtime dependency, pytest dev dependency
README.md                    # updated per FR-005
```

**Structure Decision**: Single project (Option 1 from the template). A single
installable package, `notes_mcp`, under `src/`, with one module per tool
under `src/notes_mcp/tools/` so additional real Notes tools can be added
later as sibling files without restructuring. Tests mirror this with
`contract/` (validates the tool's declared schema/shape) and `unit/`
(validates the stub logic itself) directories, per the constitution's
Test-First principle.

## Complexity Tracking

*No entries — Constitution Check reported no violations.*
