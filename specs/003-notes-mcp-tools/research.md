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

**Decision**: Both are thin wrappers around `apple.core.append()`,
implemented as two separate small functions rather than one shared helper
parameterized by intent. (Amended alongside §8: `update_note` now also
handles an explicit replacement mode, so it is no longer *identical*
under the hood to `create_note` in every case — but its default,
`overwrite=False` path still calls `append()` exactly as `create_note`
does, so the original reasoning for keeping them separate stands.)

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

## 8. `update_note`'s replacement mode (amendment)

**Decision**: `update_note(folder_path, name, content, overwrite=False)`.
When `overwrite` is `true`:
0. Call `apple.core.ls(folder_path)` and filter its `notes` for
   `name == name` to count how many notes already match. `append` itself
   does an equivalent lookup internally, but only to decide append-vs-
   create — it doesn't expose the count, and the tool needs to know it
   *before* deciding whether anything should be archived. If the count is
   **not exactly one** (zero, or ambiguous), skip straight to step 3 and
   let `append` handle it exactly as it already would: zero → it creates
   a fresh note (identical to `create_note`); more than one → *`append`
   itself* raises `AmbiguousMatchError` (FR-006) — `update_note` does not
   duplicate that check itself, it just lets the same call `append`
   already makes do the detection, once, in one place.
1. (Only when the count is exactly one.) Ensure a single, fixed,
   top-level folder named `archive` exists — call
   `apple.core.mkdir("", "archive")` and ignore `AlreadyExistsError` if
   it's already there.
2. Move the matched note into `archive` via `apple.core.mv(kind="note",
   identifier=<its id>, destination_folder_path="archive")`, unchanged —
   this step must complete before step 3.
3. Call `apple.core.append(folder_path, name, content)`. When reached via
   step 2, the original was just moved out, so this call now finds zero
   matches and takes its create-if-missing path — the same single call
   that step 0 would have gone to directly for the zero/ambiguous cases.

**Dependency this decision surfaced**: step 1 needs `apple.core.mkdir` to
create a **top-level** folder (parent = the account root), but `mkdir`'s
current implementation (feature 002) rejects an empty `parent_path` with
`NotFoundError("Empty folder path")` — verified empirically; there is
currently no way to create a top-level folder with the existing backend
at all. This is a real, narrow gap in already-shipped code, not a
hypothetical: `jxa_scripts/mkdir.js` needs a small, targeted fix so that
`parent_path == ""` is treated as "the account root" (`parent = acct`
instead of `resolveFolder(acct, parent_path)`) and the resulting path is
reported as `name` (no leading slash) rather than `"" + "/" + name`. This
is scoped to `mkdir.js` only — `resolveFolder` itself, and every other
script that calls it (`ls`, `grep`, `mv_note`, `mv_folder_prepare`,
`append`), are untouched, since nothing else in this feature needs
root-level path resolution and generalizing it further isn't a demonstrated
need yet (YAGNI). Existing callers of `mkdir` with a non-empty
`parent_path` are unaffected — this only expands what was previously a
guaranteed error into a supported case.

**Rationale**:
- **Archive, don't delete**: the constitution's Safe, Reversible Data
  Operations principle prefers additive/reversible operations over hard
  deletes wherever the platform supports it. `apple.core` has no
  overwrite-in-place capability and this feature does not add one — the
  "replacement" is really "check via `ls`, archive the old one via `mv`,
  then create a new one via `append`," composing capabilities the backend
  already has (plus the narrow `mkdir` fix above, itself additive-only —
  it only ever creates folders, never removes or overwrites anything).
- **Archive-first ordering**: doing the move *before* the create means a
  failure at step 2 (e.g., Notes automation permission revoked mid-call)
  leaves the original note exactly where it was, with the tool call
  simply failing — never a state where a replacement was created while
  the original's content is gone. Doing it in the other order would risk
  exactly that.
- **Single top-level archive folder**: matches the literal "/archive"
  phrasing in the request (a single, root-level location) most directly,
  and gives a caller one place to look for anything ever replaced,
  rather than one archive-within-each-source-folder to check.
- **Auto-create the archive folder**: failing the first time anyone uses
  replacement mode, just because nobody manually created an "archive"
  folder in Notes first, would be a poor default with no compensating
  benefit — auto-creating a conventionally-named utility folder on first
  use is an established, unsurprising pattern.
- **No renaming of archived notes**: Apple Notes doesn't require note
  titles to be unique (unlike folder names), so multiple archived notes
  sharing a name over repeated replacements is valid, not an error;
  adding a timestamp or other disambiguating suffix would be a real,
  separate feature (better organization of archived history) that
  nothing in this request actually asked for (YAGNI) — revisit if a
  concrete need for it shows up.

**Alternatives considered**:
- Archiving per-source-folder (e.g. `Personal/archive` instead of a
  single top-level `archive`): rejected — the request's "/archive"
  phrasing reads as one canonical location, and a single location is
  simpler to browse later.
- Creating the replacement before archiving the original: rejected — the
  reverse of the safe ordering above; would risk two same-named notes
  coexisting in the original folder (breaking future `AmbiguousMatchError`
  detection) if the archive step then failed.
- Failing outright if the archive folder doesn't exist yet (matching
  `mv`'s existing behavior when a destination doesn't exist): rejected as
  the tool's own behavior — auto-creating on first use is friendlier and
  is safe to do internally, even though no standalone `mkdir` tool is
  exposed to MCP clients directly (spec Assumptions).
- Timestamping or otherwise renaming archived notes: rejected as an
  unrequested scope addition (YAGNI); noted as a natural follow-up if
  archive browsability ever becomes a real problem.
- Avoiding the `mkdir` fix by nesting `archive` under some already-usable
  existing top-level folder instead (e.g. inside whichever folder the
  note being replaced happens to live in): rejected — contradicts the
  single-canonical-location decision above, and papering over a real gap
  in `mkdir` with a workaround would leave the same gap for the next
  feature that needs a top-level folder, instead of fixing it once.
- Generalizing the empty-path-means-root fix to `resolveFolder` itself
  (so `ls`, `grep`, and `mv` also gain root support): rejected for now —
  nothing in this feature needs it, and a broader change to shared,
  already-tested code carries more risk than the narrow, `mkdir.js`-only
  fix actually required here (YAGNI; revisit if a real need for
  root-level `ls`/`grep`/`mv` shows up later).

## Outcome

All unknowns resolved, several confirmed empirically against the real SDK
rather than assumed. No remaining `NEEDS CLARIFICATION` markers. §8 was
added as an amendment (not part of the original planning pass) to cover
`update_note`'s new replacement mode. Ready for Phase 1 design (already
reflected in data-model.md, contracts/, and quickstart.md).
