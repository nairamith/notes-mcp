# Phase 0 Research: Move and Remove a Note

All Technical Context items were resolved from the existing project (same
package, same `mcp` SDK, same `apple.core` backend). No `NEEDS
CLARIFICATION` markers remained in the spec, so this phase focuses on
confirming — empirically, where the platform's JXA behavior matters —
that the existing backend already supports what these two tools need,
rather than guessing.

## 1. `move_note` needs no backend changes; the "move to the same folder" edge case is already handled

**Decision**: `move_note(note_id, destination_folder_path, new_name=None)`
is a direct, unmodified wrap of `apple.core.mv(kind="note", ...)`.

**Rationale**: Reading `jxa_scripts/mv_note.js` (feature 002) shows it
already guards against calling `Notes.move()` when the note's current
container already matches the destination:

```js
if (note.container().id() !== destFolder.id()) {
  // ... only then call Notes.move ...
}
```

This exists because `Notes.move(item, {to: X})` throws `"Can't get
object"` (-1728) when `X` is already the item's current container, even
though nothing needs to move. Feature 002 added this guard defensively,
but never had a caller that actually exercised the "same folder" path in
practice (its own integration tests always move to a genuinely different
folder). This feature is the first to expose `mv` directly to external
callers, so the "move a note to the folder it's already in" edge case
(spec Edge Cases) is now actually reachable — verified empirically
against real Notes.app (a note moved to its current folder succeeds as a
no-op; the same call with a `new_name` renames it in place, since the
rename logic runs unconditionally after the container check regardless
of whether a move happened).

**Alternatives considered**: Adding a pre-check in Python (e.g. call `ls`
first to see if the note's already in the destination): rejected —
`mv_note.js` already handles this correctly at the source, and adding a
second, redundant check in Python would duplicate logic the JXA layer
already gets right.

## 2. `remove_note` implements `rm`'s note path for real, composing existing `mkdir`/`mv`

**Decision**: `apple.core.rm(kind="note", identifier)` now:
1. Ensures the well-known top-level `archive` folder exists — calls
   `mkdir("", "archive")` and ignores `AlreadyExistsError` if it's already
   there (identical pattern to `update_note`'s replacement mode, feature
   003 research.md §8).
2. Moves the note into it via `mv(kind="note", identifier=identifier,
   destination_folder_path="archive")`.
3. Returns the resulting `Note` (its `folder_path` is now `"archive"`).

`rm(kind="folder", ...)` is unchanged — still raises
`NotImplementedYetError` immediately, before any of the above runs.

**Rationale**: `rm` has existed since feature 002 specifically as this
capability's placeholder ("Real removal behavior is deferred to a future
feature" — its own docstring). Implementing it now, rather than bypassing
it with fresh logic elsewhere, keeps the backend's public shape stable:
`apple.core` remains the one place that defines what each operation does,
and `tools/remove_note.py` stays a thin wrapper, consistent with every
other tool in this project.

Composing `mkdir`+`mv` directly inside `rm` (rather than extracting a
shared `_archive_note()` helper used by both `rm` and `update_note`) is a
deliberate application of the constitution's stated threshold: "prefer
duplication over a shared abstraction until a third real use case
exists." This is only the *second* concrete case (the first being
`update_note`'s replacement mode) — not yet three — so the two
implementations stay independent for now. If a third real need for
"archive a note" composition shows up later, that's the point at which
extracting a shared helper stops being speculative.

**Alternatives considered**:
- Bypassing `rm` and implementing archiving fresh inside
  `tools/remove_note.py` (mirroring `update_note.py`'s own composition,
  leaving `rm` a permanent stub): rejected — would leave `apple.core.rm`
  a confusing, permanently-broken function sitting right next to a
  working `remove_note` tool that doesn't use it, contradicting `rm`'s
  own documented purpose.
- Extracting a shared archive-composition helper now (used by both `rm`
  and `update_note`): rejected per the constitution's explicit
  three-use-case threshold — this is only the second.
- Generalizing `rm(kind="folder", ...)` to also archive folders in this
  feature: rejected — out of scope per the spec's Assumptions; nothing in
  the request asked for folder removal, and folder archiving would raise
  its own questions (e.g. what happens to a folder's own subfolders) that
  aren't resolved here.

## 3. Removing an already-archived note is a safe no-op

**Decision**: No special-casing needed. Calling `remove_note` on a note
that's already in the `archive` folder hits the exact same "current
container already matches destination" guard in `mv_note.js` described in
§1 — the move is skipped, and the note's `Note` (with `folder_path`
already `"archive"`) is returned unchanged. Verified empirically against
real Notes.app.

**Rationale**: This falls directly out of §1's existing guard — no new
code needed, just confirmation that the composition in §2 doesn't
introduce a new failure mode here (e.g. `mkdir("", "archive")` correctly
raises and swallows `AlreadyExistsError` on every call after the first,
regardless of whether the target note happens to already be there).

**Alternatives considered**: Explicitly checking whether a note is already
in `archive` before attempting the move, to short-circuit and avoid the
redundant `mkdir` call: rejected — the redundant `mkdir` call is cheap
(a single `AlreadyExistsError` swallowed, no different from every
non-first call to `remove_note` regardless of the note's prior location)
and adding a check purely to skip it would be optimization for a case
with no measured cost (YAGNI).

## 4. Updating feature 002's existing `rm` tests

**Decision**: `rm`'s existing dedicated tests (from feature 002) split by
kind:
- `tests/unit/apple/test_core_unit.py`'s `TestRmStub` and
  `tests/integration/apple/test_core_integration.py`'s
  `TestRmIntegration`: their note-kind assertions (`rm(kind="note", ...)`
  always raises `NotImplementedYetError`) are replaced with assertions
  matching the new real behavior (archives the note, returns a `Note`
  with `folder_path="archive"`). Their folder-kind assertions are
  unchanged — `rm(kind="folder", ...)` still always raises.

**Rationale**: These tests encoded feature 002's deliberate, temporary
stub behavior. Now that the stub is real for notes, the tests must
reflect that or they'd be actively asserting something false — leaving
them unchanged would mean a passing test suite that contradicts the
actual, intended behavior.

**Alternatives considered**: Leaving the old tests in place and adding new
ones alongside: rejected — the old note-kind assertions would then be
directly contradictory (one test asserting `rm(kind="note", ...)` always
raises, another asserting it archives), which is worse than updating them
in place.

## Outcome

All unknowns resolved; two of the three findings above were confirmed
empirically against real Notes.app rather than assumed, consistent with
this project's established practice. No backend/JXA script changes are
needed — this feature is purely a Python-level composition (`rm`) plus
two new thin tool wrappers (`move_note`, `remove_note`). Ready for Phase 1
design.
