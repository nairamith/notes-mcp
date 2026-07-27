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

## 2. `remove_note` composes `mkdir`/`mv` directly; `apple.core.rm` is entirely out of scope (amendment — PR review, twice)

**Decision** (final, after two rounds of review): `remove_note` (the MCP
tool) composes `mkdir`/`mv` directly, at the tool layer — it never calls
`apple.core.rm`, and never has:
1. Ensures the well-known top-level `archive` folder exists — calls
   `mkdir("", "archive")`, ignoring `AlreadyExistsError`.
2. Moves the note into it via `mv(kind="note", identifier=identifier,
   destination_folder_path="archive")`.
3. Returns the resulting `Note`.

`apple.core.rm` is **entirely untouched by this feature** — still exactly
feature 002's original stub, raising `NotImplementedYetError` for every
call, both `kind="note"` and `kind="folder"`. This section briefly
implemented real `kind="note"` delete behavior for `rm` (via
`Notes.delete()`, matching what the operation's name conventionally
means) as an interim step, but that was reverted on explicit maintainer
direction: "changes to the core rm functionality is not included in scope
for this PR" — implementing `rm` for real is a separate, future feature,
not something to fold into this one incidentally.

**Why this ended up here**: a PR review comment asked "why can't this
just use the mv functionality to move the file to archive?", referring to
`remove_note.py` calling `rm` (which itself composed `mkdir`+`mv`)
instead of composing `mv` directly. The follow-up clarified the real
objection: `apple.core` functions are meant to be thin, literal wrappers
over Apple Notes' own operations, while MCP **tools** are where
product-level policy belongs — "remove means archive, not delete" is a
`remove_note`-level decision, the same way `update_note`'s "replace means
archive-then-recreate" decision lives entirely in `tools/update_note.py`,
not in any `apple.core` function. The original design (archiving inside
`rm`) broke that layering. Moving the composition into
`tools/remove_note.py` fixed it — and, along the way, `Notes.delete()`
was verified empirically to move a note into Notes.app's own native
"Recently Deleted" folder rather than purging it immediately (the same
soft-delete/trash model as Mail or Finder), confirming `rm`'s name really
does map to a real, distinct Notes.app operation. A subsequent review
comment then drew the scope line: giving `rm` that real behavior is a
legitimate, separate piece of work, not something this PR should also
take on just because the layering discussion surfaced it. `remove_note`
never depended on `rm` being real in the first place (§2's mkdir+mv
composition works whether `rm` is a stub or not), so reverting `rm` back
to the stub has zero effect on this feature's own tools.

**Alternatives considered**:
- `remove_note` wraps `apple.core.rm`, and `rm` implements the archiving
  itself (the very first design): rejected — breaks the
  backend/tool-layer split described above.
- `remove_note` wraps `apple.core.rm`, and `rm` implements a real delete
  via `Notes.delete()` (the interim design, briefly shipped and then
  reverted): correct layering, but out of scope for this PR per explicit
  maintainer direction — `apple.core.rm`'s own real implementation is a
  separate feature to take up later, not a side effect of this one.
- Extracting a shared archive-composition helper used by both
  `update_note.py` and `remove_note.py`, since both independently compose
  the identical `mkdir`+`mv` pattern: rejected — the constitution's stated
  threshold is a *third* real use case before extracting a shared
  abstraction; this is only the second.
- Generalizing `apple.core.rm` to handle folders, or implementing it at
  all in this feature: rejected — explicitly out of scope (see Decision
  above).

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

## 4. `rm`'s existing feature-002 tests are untouched

**Decision**: `tests/unit/apple/test_core_unit.py`'s `TestRmStub` and
`tests/integration/apple/test_core_integration.py`'s `TestRmIntegration`
are exactly as feature 002 left them — asserting `rm` always raises
`NotImplementedYetError`, for both `kind="note"` and `kind="folder"`,
and never touches Notes data. (An interim version of this feature
briefly updated these tests to match a real `kind="note"` delete
implementation; both the implementation and the test changes were
reverted per §2's final decision.)

**Rationale**: Since `apple.core.rm` is out of scope for this PR (§2),
there is nothing about its behavior for this feature to test — feature
002's own tests already cover the stub correctly, and continue to.

## 5. `remove_note`'s own tests mock `mkdir`/`mv`, not `rm`

**Decision**: `tests/unit/tools/test_remove_note_unit.py` mocks
`apple.core.mkdir`/`apple.core.mv` directly (verifying call order:
`mkdir` then `mv`, and that `AlreadyExistsError` from `mkdir` is
swallowed), mirroring `test_update_note_unit.py`'s existing style for its
identical composition. `remove_note`'s own integration tests
(`tests/integration/tools/test_remove_note_integration.py`) needed **no
changes at all** through any of this feature's design iterations — the
tool's externally observable behavior (archives into `archive`, idempotent
on an already-archived note) never changed; only exploration of what,
if anything, it should call in `apple.core` did.

**Rationale**: Unit tests should mock at the boundary the code under test
actually calls. Since `remove_note` composes `mkdir`/`mv` directly and
never calls `rm`, mocking `rm` would test the wrong thing. The unchanged
integration tests are a useful confirmation that `remove_note`'s contract
was stable throughout this feature's design iterations, independent of
where its composition logic ended up living or what (if anything)
`apple.core.rm` did.

## Outcome

All unknowns resolved; two of the findings above were confirmed
empirically against real Notes.app rather than assumed, consistent with
this project's established practice — including, during an interim
design later reverted, `Notes.delete()`'s actual "Recently Deleted"
semantics (§2), which remains a useful confirmation for any future
feature that does implement `rm` for real. `apple.core.rm` itself is
untouched by this feature, unchanged from feature 002. `move_note` needs
no backend changes either. Ready for Phase 1 design (already reflected in
data-model.md, contracts/, and quickstart.md).
