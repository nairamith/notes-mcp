# Phase 0 Research: Apple Notes Core Backend Operations

## 1. Automation surface

**Decision**: JavaScript for Automation (JXA), invoked via
`subprocess.run(["osascript", "-l", "JavaScript", "-e", SCRIPT, "--", *args], ...)`.
`SCRIPT` is a fixed, static string (never built by interpolating
user-supplied data); arguments are passed positionally after `--` and read
inside the script via its `run(argv)` entry point.

**Rationale**: Apple Notes has no public Swift/ObjC framework API — its
only Apple-sanctioned automation surface is the scripting dictionary
(AppleScript or JXA), consistent with the constitution's Platform &
Integration Constraints. JXA is preferred over classic AppleScript because
it has native `JSON.stringify`/`JSON.parse`, so structured data (lists of
notes/folders with several fields each) can be returned as real JSON
instead of a hand-rolled delimited text format. Passing arguments via
`argv` rather than string-interpolating them into the script source avoids
a real injection risk: a folder or note name containing a quote character
could otherwise break out of a naively interpolated AppleScript/JS string
and execute arbitrary script code — the same class of bug as SQL
injection, just for AppleScript. This matters even though this feature
isn't wired to MCP yet, since a future feature will likely pass
LLM/user-influenced strings into these same functions.

**Alternatives considered**:
- Classic AppleScript with hand-rolled delimited output: rejected — no
  native JSON support, and string interpolation of arguments would
  reintroduce the injection risk described above.
- `appscript` / `py-applescript` (third-party PyObjC-based bridges):
  rejected — third-party dependency for something `subprocess` + the
  macOS-bundled `osascript` already does, violating Principle VI (Minimal,
  Justified Dependencies) with no compensating benefit.
- Reading Notes' on-disk SQLite store directly: rejected — the
  constitution requires any such undocumented store be treated read-only
  behind an adapter, and several of these operations (`mkdir`, `mv`) are
  writes; JXA is the correct, fully-sanctioned surface for both reads and
  writes.

## 2. Folder addressing

**Decision**: Folders are addressed by a `/`-delimited path of folder
names (e.g. `"Personal/Groceries"`), rooted at a top-level folder.

**Rationale**: `mkdir` (FR-003) already requires rejecting a duplicate
name within the same parent, which means folder names are effectively
unique within their parent — a path built from names is therefore
unambiguous. This directly matches the `ls`/`mkdir`/`mv` filesystem-command
metaphor the user chose.

**Alternatives considered**: Addressing folders by Notes' internal id
only: rejected as unnecessarily unfriendly for a filesystem-metaphor API
where every sibling function (`ls`, `mkdir`) already speaks in terms of
names/paths.

## 3. Note addressing

**Decision**: Notes are addressed by their stable Notes-assigned `id`, not
by name. `ls` and `grep` return each note's `id` together with its `name`
(title) and containing folder path.

**Rationale**: Unlike folders, Apple Notes does not enforce unique titles —
multiple notes can share an identical (or empty) title. A name-only
reference would be ambiguous for `mv`/`rm` the moment two notes share a
title. Using the platform's own stable id (as the sibling
`001-mcp-server-scaffold` feature already did for folders in its
`list_folders` tool) resolves this cleanly without inventing a new ID
scheme.

**Alternatives considered**: Address notes by (folder path, title) pair:
rejected — still ambiguous whenever two notes in the same folder share a
title, which is common (e.g., several blank/untitled notes).

## 4. `mv` / `rm` target disambiguation

**Decision**: Both functions take an explicit `kind: Literal["note",
"folder"]` plus an `identifier` string (a note's `id` when
`kind="note"`, a folder's path when `kind="folder"`), rather than
inferring the kind from the identifier's shape.

**Rationale**: Per the constitution's Observability & Debuggability
principle, behavior should be predictable and never rely on guessing —
inferring "is this string a note id or a folder path" from formatting
would be exactly that kind of implicit magic, and would break the moment a
folder path happened to look like an id. An explicit `kind` parameter
costs one extra argument and removes the ambiguity entirely.

**Alternatives considered**: Separate `mv_note`/`mv_folder` (and
`rm_note`/`rm_folder`) function pairs: rejected — the user explicitly
asked for one `mv` and one `rm` function; a single function with an
explicit `kind` parameter satisfies that naming while keeping the target
type unambiguous.

## 5. `grep` scope and matching

**Decision**: `grep(pattern, folder_path=None)` matches `pattern` as a
Python regular expression (`re` module) against each note's plaintext
content. When `folder_path` is omitted, it searches every note in the
account; when given, it searches only that folder's contents. Matching
happens in Python, after fetching note plaintext via JXA — JXA/AppleScript
has no native regex engine, so there is no benefit to attempting the match
inside the script itself.

**Rationale**: The spec's FR-002 doesn't scope `grep` to a single folder
the way FR-001 scopes `ls`, so whole-account search is the more useful
default (matches how a person would expect "search my notes for X" to
behave); an optional `folder_path` still allows narrowing when wanted. An
invalid pattern is rejected with a clear error (`InvalidPatternError`)
before any Notes interaction is attempted, per FR-002.

**Alternatives considered**: Matching only within a single mandatory
folder: rejected — no clear default folder exists to require, and it would
make "search everything" require the caller to already know the full
folder tree.

## 6. Performance: batching over per-item round trips

**Decision**: When listing or searching, fetch each folder's notes'
properties (`id`, `name`, plaintext) as arrays in a single JXA call (e.g.
`folder.notes.id()`, `folder.notes.name()`, `folder.notes.plaintext()`)
rather than iterating and querying each note individually.

**Rationale**: Each `osascript` invocation and each individual
AppleScript/JXA property access on Notes.app carries real IPC overhead;
querying an array property once for all notes in a folder is dramatically
faster than one round trip per note, which is necessary to meet SC-002's
2-second target for a few-hundred-note collection.

**Alternatives considered**: Per-note property access in a loop: rejected
as the well-known AppleScript/JXA performance antipattern that would risk
missing SC-002 entirely on larger folders.

## 7. Error handling

**Decision**: A small, flat exception hierarchy, all defined in
`apple/core.py`:
- `AppleNotesError` (base)
- `NotFoundError` — target note/folder/parent doesn't exist
- `AlreadyExistsError` — `mkdir` name collision
- `InvalidPatternError` — `grep` given an invalid regular expression
- `AutomationPermissionError` — macOS hasn't granted Notes automation
  permission yet (`osascript` error `-1743`)
- `NotImplementedYetError` — raised by the `rm` stub, always

Errors are classified from `osascript`'s exit code/stderr (and, where the
JXA script itself detects the problem — e.g., "no folder named X" — from a
small structured error object the script emits as JSON) into one of the
above, with a clear, human-readable message. Raw AppleScript/JXA error
text is never surfaced directly to the caller as the sole signal.

**Rationale**: Per the constitution's Observability & Debuggability
principle, a caller (or a person debugging on their behalf) needs to be
able to tell "bad input" apart from "Notes permission not granted" apart
from "Notes itself errored" without re-instrumenting the code. A flat,
small hierarchy is enough for this feature's five functions; no need for a
deeper exception taxonomy yet (YAGNI).

**Alternatives considered**: Letting `subprocess.CalledProcessError`
propagate directly: rejected — its message is raw AppleScript/JXA text,
which fails the "actionable error" requirement and couples every caller to
`osascript`'s exact error formatting.

## 8. Testing strategy given no official Notes sandbox

**Decision**: Two tiers of tests:
- **Unit** (`tests/unit/apple/`): pure logic that needs no real Notes
  access — `rm`'s stub behavior (always raises, touches nothing),
  `grep`'s invalid-pattern rejection, `mv`/`rm`'s `kind`/`identifier`
  validation.
- **Integration** (`tests/integration/apple/`): `ls`, `grep`, `mkdir`,
  `mv` exercised against a real, dedicated, clearly-named scratch folder
  (e.g. a single top-level folder reserved for this test suite) created
  fresh and cleaned up per test session — never the developer's/user's
  other personal folders. These tests are automatically skipped when not
  running on macOS, or when Notes.app / Automation permission isn't
  available, rather than failing the whole suite in environments that
  can't run them (e.g. CI without a configured macOS+Notes runner).

**Rationale**: Apple Notes has no official virtualization or test-double
API, so a real, isolated, disposable folder is the closest achievable
match to the constitution's "fakes or a sandboxed Notes environment"
requirement (Principle II) — the isolation comes from a dedicated
container, not a fake implementation. Splitting the stub (`rm`) and
pure-validation logic into a Notes-free unit tier keeps the fast, always-
runnable part of the suite from depending on macOS/Notes availability at
all.

**Alternatives considered**: Mocking the JXA/`osascript` boundary
entirely for all functions: rejected as the primary strategy — it would
prove the Python-side plumbing works but not that the actual Notes
automation calls are correct, which is the part most likely to break
across macOS/Notes versions; real integration coverage (even if narrower
and skippable) is required by the constitution for anything touching Notes
data.

## 9. macOS Automation permission (operational note, not a design decision)

The first time any process invokes `osascript` against Notes.app, macOS
prompts for one-time Automation permission (System Settings → Privacy &
Security → Automation) for the calling process (e.g. Terminal, or the
Python interpreter). This cannot be granted non-interactively. Documented
as a manual prerequisite in `quickstart.md`; `AutomationPermissionError`
(see §7) is what callers see if it hasn't been granted yet.

## Outcome

All unknowns resolved. No remaining `NEEDS CLARIFICATION` markers. Ready
for Phase 1 design.
