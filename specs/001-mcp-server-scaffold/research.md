# Phase 0 Research: MCP Server Scaffold with Dummy list_folders Tool

All Technical Context items were resolved from user input (Python, stdio
transport) plus the project constitution's Platform & Integration
Constraints (macOS-only, local transport). The decisions below cover the
remaining implementation choices needed before design.

## 1. MCP protocol implementation

**Decision**: Use the official MCP Python SDK (`mcp` on PyPI), specifically
its high-level `mcp.server.fastmcp.FastMCP` API, running over the stdio
transport (`mcp.run(transport="stdio")` / `FastMCP.run()` default).

**Rationale**: The SDK is maintained by the Model Context Protocol project
itself, implements the JSON-RPC framing, capability negotiation, and schema
handling correctly, and lets a tool be registered with a single decorator.
Hand-rolling the protocol would be a far larger and riskier undertaking than
the dependency it replaces — the opposite of what Principle VI (Minimal,
Justified Dependencies) is protecting against.

**Alternatives considered**:
- Hand-write JSON-RPC-over-stdio framing directly: rejected — high risk of
  subtly violating the MCP spec (initialization handshake, message framing),
  with no engineering benefit to reinventing it.
- Third-party/unofficial MCP SDKs: rejected — the official SDK is the
  lowest-risk, best-maintained option and is the reference implementation
  clients are tested against.

## 2. Transport

**Decision**: stdio, as specified by the user.

**Rationale**: Matches how local MCP servers are consumed by clients such as
Claude Desktop and Claude Code (spawned as a subprocess, communicating over
stdin/stdout). No network-exposed transport (SSE/HTTP) is needed for this
scaffold.

**Alternatives considered**: SSE/HTTP transport — explicitly out of scope
per the spec's Assumptions section; would add a web server dependency with
no present requirement (YAGNI).

## 3. Language version

**Decision**: Python 3.11+.

**Rationale**: A current, widely available stable version with good tooling
support; compatible with the `mcp` SDK's minimum Python requirement. Not
pinned to a narrower patch version since nothing in this feature depends on
version-specific behavior.

**Alternatives considered**: Python 3.10 — no benefit over 3.11 for this
project; newer 3.12/3.13 — fine but an unnecessary constraint to impose this
early; 3.11 is a safe, broadly-installed baseline.

## 4. Packaging / dependency management

**Decision**: Standard `pyproject.toml` with the `setuptools` build backend;
install via `pip install -e ".[dev]"`.

**Rationale**: Requires no tooling beyond `pip`, which is already assumed.
Keeps the dependency surface minimal per Principle VI — no Poetry/uv/Hatch
tooling is justified by a scaffold this small.

**Alternatives considered**: Poetry, uv, Hatch — all reasonable tools, but
each adds a new piece of tooling contributors must install with no present
need; deferred until a concrete reason to adopt one appears (YAGNI).

## 5. Test runner

**Decision**: pytest, as a dev-only dependency.

**Rationale**: Universally expected by Python contributors, and
meaningfully reduces boilerplate for the contract test that validates the
`list_folders` output shape. It is not shipped with the runtime package, so
it doesn't expand the deployed dependency surface — an accepted,
documented exception to preferring the standard library, per Principle VI's
"justify in the PR/plan" requirement.

**Alternatives considered**: stdlib `unittest` — would avoid the dependency
entirely, but produces materially more boilerplate for schema/shape
assertions with no compensating benefit at this project's stage.

## 6. Logging / observability

**Decision**: stdlib `logging` module. Each tool invocation logs the tool
name, outcome (success/error), and duration at INFO level.

**Rationale**: Satisfies Principle V (Observability & Debuggability) without
adding a dependency. A single-tool scaffold has no present need for a
structured-logging library (e.g. `structlog`) or log aggregation — revisit
if/when multiple handlers or machine-parseable log requirements emerge.

**Alternatives considered**: `structlog` or similar — deferred as
unjustified for one tool and one log statement per call (YAGNI).

## 7. Stub data representation

**Decision**: A hardcoded Python list of plain dicts (`{"id": ..., "name":
...}`) defined directly in `tools/list_folders.py`, returned as-is by the
tool function.

**Rationale**: FR-003 requires fixed placeholder data with no real Notes
connection. A literal in-memory list is the simplest possible representation
— no database, fixture file, or config loader is needed for three static
rows.

**Alternatives considered**: Loading stub data from a JSON fixture file or a
small dataclass — both add indirection with no present benefit; deferred
until real data modeling needs (e.g. real Notes folders) make a richer
representation necessary.

## Outcome

All unknowns resolved. No remaining `NEEDS CLARIFICATION` markers. Ready for
Phase 1 design.
