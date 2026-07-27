<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.1.0
Bump rationale: Materially expanded guidance (new docstring-convention requirement
  added to Development Workflow & Quality Gates) — no principle was redefined or
  removed, so MINOR rather than MAJOR. Prompted by PR #2 review feedback requesting
  Google-style docstrings for src/notes_mcp/apple/core.py.

Modified principles: n/a (no existing principle renamed or redefined)

Added sections:
  - Development Workflow & Quality Gates: new paragraph requiring Google-style
    docstrings (summary + Args/Returns/Raises as applicable) for every Python
    function/method, as a review blocker alongside the existing YAGNI/safety checks.

Removed sections: none

Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no change needed (Constitution Check gate
    reads the constitution dynamically per feature)
  - .specify/templates/spec-template.md ✅ no change needed (generic, principle-agnostic)
  - .specify/templates/tasks-template.md ✅ no change needed (docstring convention is
    a code-review concern, not a task-generation concern)
  - .specify/templates/checklist-template.md ✅ no change needed (generic)
  - src/notes_mcp/apple/core.py ✅ updated — all function docstrings rewritten to
    Google style in the same PR that prompted this amendment

Follow-up TODOs: none blocking. Earlier v1.0.0 note about README.md being a
placeholder is superseded — README.md was written in feature 001.
-->

# Notes MCP Constitution

## Core Principles

### I. Simplicity & YAGNI (NON-NEGOTIABLE)
Build only what the current feature actually requires. No speculative abstractions,
configuration knobs, or extensibility hooks for hypothetical future requirements.
Prefer three similar lines of code over a shared abstraction until a third real use
case exists. Every added dependency, indirection layer, or config option MUST be
justified by a concrete, present requirement — not a "we might need this later"
argument. Reviewers MUST reject speculative generality during code review.

**Rationale**: Apple Notes integration surfaces (AppleScript/JXA, EventKit, on-disk
stores) are narrow and quirky; premature abstraction over them creates fragile
indirection that has to be unwound the first time a real second use case disagrees
with the guessed shape.

### II. Test-First, Test-Always (NON-NEGOTIABLE)
Every feature and bug fix MUST ship with automated tests that fail without the
change and pass with it. A feature without tests is not done, regardless of manual
verification. Every MCP tool requires a contract test validating its input/output
schema. Any code path touching Apple Notes (via AppleScript/JXA, EventKit, or the
Notes data store) requires an integration test running against fakes or a sandboxed
Notes environment — never against the developer's or a user's live, real Notes
data. Tests are written before implementation where the change is non-trivial, and
must be run (and pass) before a PR merges.

**Rationale**: This server acts on irreplaceable personal data (notes) through
semi-documented platform integrations that change across macOS versions; untested
paths here fail silently and destructively rather than loudly.

### III. MCP Contract Integrity
Every tool exposed over MCP has an explicit, versioned schema for its inputs and
outputs. Breaking changes to a tool's schema require a version bump and a migration
note in the changelog/PR description. Tool responses MUST be structured and
predictable — the shape of a successful response never silently changes between
calls. Errors are returned as explicit, typed error results surfaced to the MCP
client, never swallowed or logged-and-ignored.

**Rationale**: MCP clients (agents) make decisions from tool schemas and responses
alone; an undocumented or unstable contract breaks every consumer at once with no
compiler to catch it.

### IV. Safe, Reversible Data Operations (NON-NEGOTIABLE)
This project operates on the user's real notes. Any operation that deletes,
overwrites, or otherwise irreversibly modifies note content MUST make its intent
explicit at the tool-call level (no implicit deletes as a side effect of another
operation), and MUST have a test covering the destructive path before it can merge.
Read operations MUST NOT have side effects. Prefer additive/reversible operations
(archive, move to a recoverable state) over hard deletes wherever the platform
supports it.

**Rationale**: A bug in a CRUD tool for a database row is a rollback; a bug in a
delete-note tool is a permanently lost personal note. The blast radius of a mistake
here is a real person's data, so the bar for destructive paths is higher than for
ordinary features.

### V. Observability & Debuggability
Structured logging over ad hoc prose logs. Every tool invocation logs its inputs
(sanitized of note content/PII where practical), outcome, and duration. Failures
surface actionable error messages to the MCP client rather than raw stack traces,
generic "something went wrong" messages, or silent no-ops.

**Rationale**: When a tool call fails against AppleScript/Notes internals, the
person debugging it (often not the original author) needs enough signal to
distinguish "bad input," "Notes permission not granted," and "Notes API changed"
without re-instrumenting the code first.

### VI. Minimal, Justified Dependencies
Prefer the standard library and macOS-native integration points (AppleScript/JXA,
EventKit, Notes' own automation surfaces) over third-party packages. Any new
dependency must be justified in the PR description: what it replaces, and why
rolling it by hand or using an existing dependency was insufficient.

**Rationale**: Every dependency is a supply-chain and maintenance liability for a
tool that already has to track an undocumented, moving Apple platform target;
unjustified dependencies compound that risk for no clear benefit.

## Platform & Integration Constraints

This server targets macOS only — Apple Notes has no supported cross-platform API,
so no Linux/Windows compatibility is claimed or maintained. Integration with
Notes.app MUST go through officially supported mechanisms (AppleScript/JXA,
EventKit, or other Apple-sanctioned automation surfaces); if an undocumented data
store (e.g. the Notes SQLite database) is read directly, it MUST be treated as
read-only and isolated behind an adapter that can be swapped without touching tool
logic. The server MUST request and respect macOS Automation/Full Disk Access
permissions rather than attempting to bypass or suppress them. The MCP server
communicates via a standard MCP transport (stdio or SSE per the MCP specification);
every tool's inputs and outputs MUST validate against its declared schema before
touching Notes data. Notes content MUST stay local — no transmission to
third-party network services unless the user explicitly configures an export/sync
feature, and that feature MUST be opt-in and clearly scoped.

## Development Workflow & Quality Gates

All changes land via PRs reviewed against this constitution. A PR that adds or
changes behavior without accompanying tests is rejected outright per Principle II.
CI MUST run linting, type checking (where the language supports it), and the full
automated test suite before merge; a failing check blocks merge. Code review MUST
explicitly check for YAGNI violations (Principle I) and unsafe destructive
operations (Principle IV) — these are review blockers, not style nits. Any
necessary deviation from Simplicity or Safe Operations MUST be documented in the
PR with rationale and, when driven by a specific feature, recorded in that
feature's plan.md Complexity Tracking table.

Every Python function and method MUST have a Google-style docstring (summary
line, then `Args:`/`Returns:`/`Raises:` sections as applicable to that
function) — a one-line summary alone is insufficient once a function takes
parameters, returns a meaningful value, or raises a caller-relevant exception.
This is a review blocker like the others in this section, not a style nit.

**Rationale**: A function's parameters, return shape, and error contract should
be discoverable from its docstring alone, without reading the implementation —
consistent with this project's broader bias toward explicit, debuggable
behavior (Principle V). A single, consistently-applied docstring convention
also keeps review focused on whether the documented contract is right, rather
than on inconsistent formatting.

## Governance

This constitution supersedes ad hoc conventions and prior undocumented practice.
Amendments require: (1) a documented rationale for the change, (2) a version bump
following semantic versioning — MAJOR for backward-incompatible principle removals
or redefinitions, MINOR for a new principle or materially expanded guidance, PATCH
for clarifications and wording fixes — and (3) propagation of the change to
dependent templates (plan, spec, tasks, checklist) in the same change set. Every
`/speckit-plan` Constitution Check gate and every PR review MUST verify compliance
with the principles above; unresolved violations block merge unless explicitly
justified in a Complexity Tracking table. Where day-to-day runtime guidance (e.g. a
future README.md or CLAUDE.md) conflicts with this document, this constitution
governs.

**Version**: 1.1.0 | **Ratified**: 2026-07-26 | **Last Amended**: 2026-07-27
