# Phase 0 Research: Apple Notes MCP Tools

All Technical Context items were resolved from the existing project (same
package, same `mcp` SDK, same `apple.core` backend). The decisions below
were verified empirically against the real `mcp` SDK installed in this
project, not assumed — several of them materially simplify the
implementation versus what might otherwise be guessed.

## 1. Tool registration pattern

**Decision**: One Python module per tool under `src/notes_mcp/tools/`,
each defining a single function decorated with `@mcp.tool()` (or
registered via `mcp.add_tool()` from `server.py`, matching the existing
`list_folders.py` precedent from feature 001).

**Rationale**: Consistent with the one-file-per-tool convention already
established in this codebase; keeps each tool's implementation, its
FastMCP-visible description (the function's docstring), and its schema
(derived from its type hints) in one place.

**Alternatives considered**: One module registering all five tools:
rejected — breaks the established one-file-per-tool precedent for no
benefit, and would make future retirement/addition of individual tools
noisier to review.

## 2. Error handling: the SDK already does this

**Decision**: Tool functions call the corresponding `apple.core` function
directly and let any exception it raises propagate naturally — no
try/except in the tool wrappers.

**Rationale**: Verified empirically: `FastMCP` automatically catches *any*
exception raised inside a `@mcp.tool()`-decorated function and converts it
into a real `CallToolResult` with `isError: true` and a text content
describing the error (format: `"Error executing tool {name}: {message}"`),
confirmed via a real stdio client session, not just the in-process API.
The server does not crash, and the client receives a proper structured
error result. Since every `apple.core` exception already carries a clear,
specific message (`NotFoundError('No folder named "X" under "Y"')`,
`InvalidPatternError(...)`, `AmbiguousMatchError(...)`, etc.), this
already satisfies FR-007's "clear, structured error" requirement with
zero additional code.

**Alternatives considered**: Wrapping each backend call in a
try/except that re-raises a custom `ToolError` with an explicit
`error_type` field: rejected — the SDK's default behavior already
prevents crashes and already surfaces a specific, readable message; adding
a parallel error-classification layer at the tool boundary would duplicate
work the backend's exception classes already do, for no requirement this
feature actually has (YAGNI). If a future caller needs to
programmatically branch on error *type* rather than read the message,
that's a concrete, testable need to revisit then — not a hypothetical to
build for now.

## 3. Return types: reuse `apple.core`'s dataclasses directly

**Decision**: Tool functions return `apple.core`'s existing `Note`,
`Folder`, and `FolderListing` dataclasses (or `str`, for `read_note`)
as-is — no conversion to a separate pydantic model or MCP-specific shape.

**Rationale**: Verified empirically that `FastMCP` handles plain
`@dataclass` return types identically to `pydantic.BaseModel` for
structured-content generation, including a dataclass containing lists of
other dataclasses (`FolderListing`, tested directly). This mirrors how the
`001-mcp-server-scaffold` feature's `list_folders` tool already used a
pydantic model for the same purpose — the mechanism just works for plain
dataclasses too, so introducing a second model layer purely to satisfy an
MCP-specific type would be pure duplication.

**Alternatives considered**: Defining separate pydantic models in the
`tools` layer that mirror `apple.core`'s dataclasses: rejected — verified
unnecessary; would create two parallel definitions of the same shape to
keep in sync for no behavioral difference.

## 4. Output shape: which return types get `{"result": ...}` wrapping

**Decision**: Documented per-tool in contracts/mcp_tools_api.md based on
each tool's return type:
- `list_folder_contents` returns `FolderListing` (an object) → **not**
  wrapped; the structured content *is* `{"folders": [...], "notes": [...]}`.
- `search_notes` returns `list[Note]` (an array) → wrapped:
  `{"result": [...]}`.
- `read_note` returns `str` (a primitive) → wrapped: `{"result": "..."}`.
- `create_note` / `update_note` return `Note` (an object) → **not**
  wrapped; the structured content *is* the note's fields directly.

**Rationale**: Verified empirically (three separate cases: a bare list, a
bare string, and a dataclass containing lists of other dataclasses) that
`FastMCP` wraps a tool's return value in `{"result": ...}` only when the
top-level return type isn't already a JSON object (arrays and primitives
aren't valid top-level structured-content objects per the MCP spec's
requirement that structured content be an object) — a dataclass/object
return type is used as the structured content directly, with no
wrapping. This exact rule was already discovered for `list_folders` in
feature 001 (`list[Folder]` got wrapped); this research generalizes and
confirms it holds for `str` and for nested dataclasses too, which this
feature is the first to actually need.

**Alternatives considered**: None — this is a fixed property of the SDK,
not a design choice; documenting it accurately is what matters.

## 5. `create_note` and `update_note` are separate functions

**Decision**: Both are thin wrappers that call `apple.core.append()`
identically under the hood, implemented as two separate small functions
rather than one shared helper parameterized by intent.

**Rationale**: The reason to have two tools instead of one is the
*metadata* an MCP client (an LLM) sees — a distinct name and docstring
for "create a note" versus "add to an existing note" — not a difference
in what code runs. Sharing an implementation function called by two
`@mcp.tool()`-decorated wrappers would be marginally less duplication (one
function body instead of two nearly-identical ones), but two small
functions are more directly readable and each carries its own docstring
next to its own registration, which matters more here than saving a few
lines (Principle I: prefer duplication over premature abstraction, and
there are only two of them).

**Alternatives considered**: One shared `_append_note(...)` helper called
by both wrappers: a reasonable minor alternative, not implemented because
the duplication is small (a few lines) and keeping each tool's docstring
directly next to its registration is clearer for a reader scanning
`tools/create_note.py` or `tools/update_note.py` in isolation.

## 6. Retiring the placeholder `list_folders` tool

**Decision**: Delete `src/notes_mcp/tools/list_folders.py`, remove its
registration from `server.py`, and delete its dedicated tests
(`tests/contract/test_list_folders_contract.py`,
`tests/unit/test_list_folders.py`). Update
`tests/contract/test_server_tool_registration.py` and
`tests/contract/test_server_startup_stdio.py`, which currently assert
`list_folders` is advertised, to assert the new tool set instead.

**Rationale**: Per the resolved clarification (spec.md, FR-011) — a clean
removal, not a deprecation cycle, since no known external caller depends
on the placeholder tool today.

**Alternatives considered**: Leaving the stub active alongside the new
tools: rejected per the clarification's resolution (Option B).

## 7. Sharing scratch-folder test fixtures between `apple/` and `tools/`

**Decision**: Move `tests/integration/apple/conftest.py` up to
`tests/integration/conftest.py`, unchanged in content, so its
`notes_available`/`skip_without_notes`/`scratch_folder`/`seed_note`/
`seed_subfolder` fixtures are available to both `tests/integration/apple/`
(existing) and the new `tests/integration/tools/`.

**Rationale**: When that conftest was written in feature 002, there was
only one consumer, so keeping it local to `apple/` was the right call
(Principle I — don't share prematurely). This feature is now a second,
real consumer needing the exact same fixtures (a dedicated, disposable
scratch folder to test real note/folder creation and reading against) —
the point at which sharing stops being speculative.

**Alternatives considered**: Duplicating a second copy of the same
fixtures under `tests/integration/tools/conftest.py`: rejected — would
require keeping two copies of the JXA bootstrap/cleanup/seed scripts in
sync with no benefit.

## Outcome

All unknowns resolved, several confirmed empirically against the real SDK
rather than assumed. No remaining `NEEDS CLARIFICATION` markers. Ready for
Phase 1 design.
