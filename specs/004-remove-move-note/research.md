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

## 2. `rm` implements real note deletion; `remove_note` never calls it (amendment — PR review)

**Decision** (supersedes this section's original design — see the
superseded version's rationale preserved below for context): `rm(kind=
"note", identifier)` now performs a real, raw delete via a new
`jxa_scripts/rm_note.js`, calling `Notes.delete(note)`. `remove_note` (the
MCP tool) does **not** call `rm` at all. Instead it composes `mkdir`+`mv`
directly, exactly as originally designed for `rm` below, but living in
`tools/remove_note.py` instead:
1. Ensures the well-known top-level `archive` folder exists — calls
   `mkdir("", "archive")`, ignoring `AlreadyExistsError`.
2. Moves the note into it via `mv(kind="note", identifier=identifier,
   destination_folder_path="archive")`.
3. Returns the resulting `Note`.

`rm(kind="folder", ...)` is unchanged — still raises
`NotImplementedYetError` immediately.

**Why this changed**: a PR review comment on the original design asked
"why can't this just use the mv functionality to move the file to
archive?", referring to `remove_note.py` calling `rm` rather than
composing `mv` itself. The follow-up clarified the actual objection: the
functions in `apple.core` are meant to be thin, literal wrappers over
Apple Notes' own operations ("virtual functions over apple notes" — `ls`,
`grep`, `mkdir`, `mv`, `cat`, `append`, and, by the same logic, `rm`
should map to Notes' own delete). The MCP **tools** are the layer that
decides product-level policy — e.g., "remove means archive, not delete"
is a decision `remove_note` makes, the same way `update_note`'s "replace
means archive-then-recreate" decision lives entirely in
`tools/update_note.py`, not in any `apple.core` function.

The original design (documented below) put the archive-not-delete policy
inside `apple.core.rm` itself, which broke that layering: it meant this
project now had the *same* "archive a note" policy decision implemented
in two different architectural layers (the backend, for remove; the tool,
for `update_note`'s replace) — an inconsistency, not a deliberate
distinction. Moving the composition into `tools/remove_note.py` restores
the layering `update_note.py` had already established, and makes `rm`
mean what its name and Unix-derived sibling functions (`ls`, `mv`, `cat`,
...) would suggest.

**What `Notes.delete()` actually does — verified empirically**: it moves
the note into Notes.app's own native "Recently Deleted" folder rather
than purging it immediately — the same soft-delete/trash model as Mail or
Finder, not an instant, permanent, irrecoverable deletion. Confirmed via
a real Notes.app call: after `Notes.delete(note)`, the note no longer
appears in its original folder's listing, but `cat(note_id)` (which
resolves by id, same as `Notes.notes.byId(...)`) still returns its
original content unchanged, and the note is visible in the account's
"Recently Deleted" folder. This means `rm`'s real behavior is itself
already reasonably safe by Notes.app's own built-in retention — though
this project's `remove_note` tool still deliberately never relies on that
mechanism, since it's Apple's own trash policy (retention window,
permanent-purge timing), not something this project controls or has
tested the limits of.

**No MCP tool in this feature exposes `rm` directly.** Nothing in this
feature's requirements asks for a destructive-delete tool, and exposing
one would need its own explicit design (constitution Principle IV: any
operation that deletes MUST make its intent explicit at the tool-call
level with a destructive-path test) — out of scope here. `rm` exists as a
correctly-named, correctly-tested backend primitive, matching `mkdir` and
(until this feature) `mv`, both of which were real, tested backend
capabilities before ever being exposed as their own tools.

**Alternatives considered**:
- The original design (documented in this section prior to this
  amendment): `rm` composes `mkdir`+`mv` to archive; `remove_note` is a
  thin wrap of `rm`. Rejected on review — see rationale above.
- Extracting a shared archive-composition helper used by both
  `update_note.py` and `remove_note.py` now that both independently
  compose the identical `mkdir`+`mv` pattern: still rejected, unchanged
  from the original reasoning — the constitution's stated threshold is a
  *third* real use case before extracting a shared abstraction, and
  moving the composition into the tool layer doesn't change that count
  (still two: `update_note`'s replace mode, `remove_note`).
- Generalizing `rm(kind="folder", ...)` to also delete folders in this
  feature: rejected — out of scope per the spec's Assumptions.

## 3. Removing an already-archived note is a safe no-op

**Decision**: No special-casing needed in `remove_note`. Calling it on a
note that's already in the `archive` folder hits the exact same "current
container already matches destination" guard in `mv_note.js` described in
§1 — the move is skipped, and the note's `Note` (with `folder_path`
already `"archive"`) is returned unchanged. Verified empirically against
real Notes.app.

**Rationale**: This falls directly out of §1's existing guard — no new
code needed, just confirmation that `remove_note`'s composition (§2)
doesn't introduce a new failure mode here (e.g. `mkdir("", "archive")`
correctly raises and swallows `AlreadyExistsError` on every call after
the first, regardless of whether the target note happens to already be
there).

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
- `tests/unit/apple/test_core_unit.py`'s `TestRmStub` (now
  `TestRmFolderStub` + `TestRmNote`) and
  `tests/integration/apple/test_core_integration.py`'s
  `TestRmIntegration`: their note-kind assertions (`rm(kind="note", ...)`
  always raises `NotImplementedYetError`) are replaced with assertions
  matching the new real behavior — `rm` now deletes the note via
  `Notes.delete()` (§2), verified by confirming the note vanishes from
  its original folder's listing while remaining resolvable by id (its
  content preserved, per §2's "Recently Deleted" finding). Their
  folder-kind assertions are unchanged — `rm(kind="folder", ...)` still
  always raises.

**Rationale**: These tests encoded feature 002's deliberate, temporary
stub behavior. Now that the stub is real for notes, the tests must
reflect that or they'd be actively asserting something false — leaving
them unchanged would mean a passing test suite that contradicts the
actual, intended behavior.

**Alternatives considered**: Leaving the old tests in place and adding new
ones alongside: rejected — the old note-kind assertions would then be
directly contradictory (one test asserting `rm(kind="note", ...)` always
raises, another asserting it deletes), which is worse than updating them
in place.

## 5. `remove_note`'s own tests move from mocking `rm` to mocking `mkdir`/`mv`

**Decision**: `tests/unit/tools/test_remove_note_unit.py` now mocks
`apple.core.mkdir`/`apple.core.mv` directly (verifying call order:
`mkdir` then `mv`, and that `AlreadyExistsError` from `mkdir` is
swallowed) instead of mocking `apple.core.rm`, mirroring
`test_update_note_unit.py`'s existing style for its identical
composition. `remove_note`'s own integration tests
(`tests/integration/tools/test_remove_note_integration.py`) needed **no
changes at all** — the tool's externally observable behavior (archives
into `archive`, idempotent on an already-archived note) is unchanged;
only its internal implementation moved from calling `rm` to composing
`mkdir`/`mv` directly.

**Rationale**: Unit tests should mock at the boundary the code under test
actually calls — since `remove_note` no longer calls `rm`, a unit test
mocking `rm` would no longer be testing what the function does. The
unchanged integration tests are a useful confirmation that this was a
pure refactor from the tool's caller's point of view: nothing about
`remove_note`'s contract changed, only which backend functions it
composes internally.

## Outcome

All unknowns resolved; several confirmed empirically against real
Notes.app rather than assumed, consistent with this project's established
practice — including, after a PR review round, `Notes.delete()`'s actual
"Recently Deleted" semantics (§2). One new JXA script (`rm_note.js`) was
added as a direct result of that review; `move_note` still needs no
backend changes. Ready for Phase 1 design (already reflected in
data-model.md, contracts/, and quickstart.md).
