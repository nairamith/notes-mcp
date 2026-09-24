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

## 3a. `cat` / `append` addressing (asymmetric by design)

**Decision**: `cat` addresses its target the same way as `mv`/`rm` — by
the note's `id` — since it only ever reads a note already known to exist
(typically obtained from `ls`/`grep`). `append`, by contrast, addresses
its target by `(folder_path, name)`, not `id`. If no note with that name
exists in that folder, `append` creates one (empty) first, then appends.
If more than one note already has that name in that folder, `append`
raises `AmbiguousMatchError` (see §7) rather than guessing which to
modify.

**Rationale**: `append` must support "create it if it doesn't exist" per
the spec — and a note that doesn't exist yet has no `id` to address it by,
so id-based addressing is impossible for `append`'s create path. A
folder+name pair is the only address that can name a not-yet-existing
note. This makes `cat` and `append` deliberately asymmetric in how they
take a target, but each asymmetry is driven by what that specific function
needs to do, not an accidental inconsistency: `cat` never creates
anything, so it can stay on the same unambiguous `id` scheme as `mv`/`rm`;
`append` sometimes creates, so it must use an address that still means
something before the note exists. Refusing to guess on an ambiguous
folder+name match (rather than silently picking, say, "the first match")
keeps `append` from ever mutating the wrong note — consistent with the
constitution's bias against implicit behavior on destructive/mutating
paths.

**Alternatives considered**:
- Make `append` also take an `id`, with a separate `folder_path`+`name`
  pair used only when creating: rejected — this produces two different
  call shapes for what the spec describes as one operation ("append; if
  missing, create then append"), adding a branchy signature for no benefit
  over a single folder+name address.
- Make `append` silently use the first match when a name is ambiguous:
  rejected — silently mutating one of several same-named notes when the
  caller can't tell which is a real risk of corrupting the wrong note's
  content, which this project's Safe Operations bias explicitly guards
  against even outside the `rm`/deletion context.

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
account; when given, it searches only that folder's contents. All notes
in scope have their plaintext fetched via JXA and matching happens in
Python, not inside the script.

**Rationale**: The spec's FR-002 doesn't scope `grep` to a single folder
the way FR-001 scopes `ls`, so whole-account search is the more useful
default (matches how a person would expect "search my notes for X" to
behave); an optional `folder_path` still allows narrowing when wanted. An
invalid pattern is rejected with a clear error (`InvalidPatternError`)
before any Notes interaction is attempted, per FR-002.

Matching stays in Python for a correctness reason, not a capability one:
JXA is full JavaScript, so it does have a native `RegExp` engine (unlike
classic AppleScript, which has none) — but Python's `re` and JavaScript's
`RegExp` are different regex dialects (named-group syntax, lookbehind
support, `\Z`, some Unicode class handling, etc. all differ). The contract
promises `pattern` is evaluated as a **Python** regular expression
(contracts/apple_core_api.md); evaluating it in JavaScript instead would
silently change that for any pattern that leans on a Python-specific
construct, with no test to catch the drift. Re-implementing Python-
compatible regex semantics in JavaScript isn't reasonable, so the tradeoff
is: transfer each in-scope note's plaintext to Python and match there,
which keeps the documented contract exactly true.

**Alternatives considered**:
- Matching only within a single mandatory folder: rejected — no clear
  default folder exists to require, and it would make "search everything"
  require the caller to already know the full folder tree.
- Evaluating `pattern` inside the JXA script (via JavaScript's `RegExp`)
  to avoid transferring non-matching notes' plaintext: rejected — would
  silently redefine `pattern`'s dialect from Python regex to JavaScript
  regex, breaking the documented contract for edge-case patterns. Also
  unnecessary at the feature's stated scale: personal-scale collections
  (a few hundred notes) meet SC-002's 2-second target with room to spare
  as measured in practice. If a real performance need emerges at larger
  scale, a safe first pass would be a plain-substring pre-filter in JS
  (skip transferring notes that can't possibly match a literal substring
  extracted from `pattern`), falling back to Python's `re` for the actual
  evaluation — not implemented now since there's no demonstrated need
  (Principle I, YAGNI).

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

## 6a. `append` write semantics

**Decision**: `append(folder_path, name, text)` inserts a newline before
`text` when the target note already has content, so the new text never
runs directly into the end of the existing content. When `append` creates
a brand-new (previously empty) note, `text` becomes its content with no
leading newline.

**Rationale**: A simple, predictable rule that matches how appending a
line to a text file normally behaves, and guarantees SC-006 (prior content
is always preserved and the new text is always distinguishable from it)
without needing any richer formatting model. `cat`'s return value is the
note's plain content — no metadata is added to mark where an append
occurred, keeping `cat`'s contract simple (it returns exactly what's
there, not an annotated view of it).

**Alternatives considered**: Concatenating with no separator: rejected —
would silently merge the end of existing content with the start of new
text (e.g. `"buy milk" + "buy eggs"` → `"buy milkbuy eggs"`), which is
surprising and loses information about where one entry ends and the next
begins. A configurable separator: rejected as unnecessary flexibility for
what the spec describes as a simple append (YAGNI) — can be added later if
a real need for it appears.

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
- `AmbiguousMatchError` — `append`'s `(folder_path, name)` matches more
  than one existing note (§3a)

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
  validation, `cat`'s not-found classification (mocked).
- **Integration** (`tests/integration/apple/`): `ls`, `grep`, `mkdir`,
  `mv`, `cat`, `append` exercised against a real, dedicated, clearly-named
  scratch folder
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

**Note**: `append`'s create-if-missing path is this feature's first
production capability that creates a *note* (only `mkdir` created
*folders* before). Integration tests still seed pre-existing notes via the
`seed_note` test helper (direct JXA, bypassing the functions under test)
rather than via `append`, to avoid testing `append` using `append`; only
the test that specifically exercises `append`'s create-if-missing
behavior relies on `append` itself doing the creating.

## 9. macOS Automation permission (operational note, not a design decision)

The first time any process invokes `osascript` against Notes.app, macOS
prompts for one-time Automation permission (System Settings → Privacy &
Security → Automation) for the calling process (e.g. Terminal, or the
Python interpreter). This cannot be granted non-interactively. Documented
as a manual prerequisite in `quickstart.md`; `AutomationPermissionError`
(see §7) is what callers see if it hasn't been granted yet.

## 10. Platform limitation discovered during implementation: folder cross-parent moves

**Finding**: On this platform/Notes.app version, moving a **folder** to a
different parent — via JXA's `Notes.move()`, or even classic
AppleScript's `move` command — leaves the moved folder permanently
un-dereferenceable by any subsequent script (JXA or AppleScript): its name
still appears in the destination's `.name()` array, but obtaining an
actual object reference to it (by id, by `whose()`, or by bracket-index)
and calling any method/property on that reference throws "Can't get
object" (-1728), indefinitely. Worse, any later attempt to *enumerate* the
destination folder's children (as `ls`/`grep` do, to serialize each
child's name/id) fails as soon as it reaches that specific broken
reference — so the destination folder itself becomes effectively
un-listable via automation afterward, even though the data is completely
fine and displays normally in the Notes app itself. This is a scripting-
layer limitation, not data corruption.

**Decision**: `mv` still performs folder cross-parent moves (via classic
AppleScript, per §1/§4 above), and any rename is applied *before* the
move while the source reference is still valid — so the operation itself,
and the value `mv` returns (built from already-known inputs, never
re-queried from Notes), are correct. But the test suite does not chain a
live `ls()` verification against a container that has just received a
moved folder, since that specific combination is what triggers the
enumeration failure; instead, folder-to-different-parent moves are
verified via the `mv` call's own return value, in an isolated scratch
folder not reused by later assertions.

**Rationale**: This is empirically a platform/Notes.app scripting bug,
not something fixable by choosing a different automation language or
retry/delay strategy (both were tried and ruled out). Documenting it
honestly and scoping tests around it is more useful than either pretending
it doesn't exist or blocking this feature indefinitely on a platform issue
outside this project's control.

**Alternatives considered**: Blocking folder-to-different-parent moves
entirely (raising a clear "unsupported" error): rejected — the underlying
data move does succeed and is valuable; only the *subsequent automated
inspection* of the destination is affected, which is a real but narrower
limitation than "this doesn't work at all."

## 11. Stable object references: by id, never by index (issues #6, #14)

**Finding**: A JXA bracket-index specifier (`collection[idx]`) is not a
reference to an object — it is re-evaluated against the collection on
every access. Two collections this module indexes into reorder under it:

- `account.folders` is **flattened** — it lists every folder in the
  account, nested ones included, in name order. Creating a folder whose
  name sorts before an existing top-level folder shifts that folder's
  index, so a path resolved just before (or while) that happens can point
  at the wrong folder or at nothing: `create_note` into a brand-new
  subfolder named to sort before its own top-level parent failed with
  "Can't get object" (-1728) every time (issue #6).
- A folder's `notes` are ordered by modification date. Writing to a note
  moves it to the front, so after `append` edited a note found at
  `folder.notes[idx]`, reading `.id()`/`.name()` back through the same
  specifier returned whichever *other* note now sat at `idx` (issue #14).

**Decision**: `findByName` (jxa_scripts/common.js) still locates an item
through the unfiltered collection's `.name()` array (see its comment for
why not `whose()`), but returns `collection.byId(ids[idx])` — a by-id
specifier, read with the same bulk property fetch as the names — so every
later access resolves to the same object regardless of reordering.

**Alternatives considered**: Re-looking an item up by name immediately
before each use: rejected — still index-based underneath, just with a
smaller window. Retrying on -1728: rejected — hides the wrong-item case
entirely, where nothing fails but the wrong note is returned.

## Outcome

All unknowns resolved. No remaining `NEEDS CLARIFICATION` markers. One
platform limitation discovered during implementation (§10), documented
and scoped rather than blocking. Ready for Phase 1 design.
