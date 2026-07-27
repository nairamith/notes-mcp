// Folder cross-parent moves are handled by a classic-AppleScript `move`
// (see move_folder.applescript, invoked from Python's
// _move_folder_via_applescript), not JXA's own Notes.move() — but the
// deeper platform issue is not which language performs the move: on this
// platform, a folder that has been moved to a *different* parent becomes
// permanently un-dereferenceable by any subsequent script (JXA *or*
// AppleScript) — collection-level queries like `.name()`/`.length` still
// see it, but calling any method/property on a freshly-obtained reference
// to that specific item (by id, by whose(), or by bracket-index) throws
// "Can't get object" (-1728), forever, even long after the move. So:
// never touch the folder again after moving it. Any rename must happen
// *before* the move, while the reference is still good, and the JSON
// returned to Python (mv() in core.py) is built from already-known values
// — no further Notes query needed for the result.
function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var destFolder = resolveFolder(acct, cmd.destination_folder_path);
  var srcFolder = resolveFolder(acct, cmd.identifier);
  if (cmd.new_name) {
    var dup = destFolder.folders.whose({ name: cmd.new_name })();
    if (dup.length > 0) {
      throwCustom(
        "AlreadyExistsError",
        'Folder "' + cmd.new_name + '" already exists under "' + cmd.destination_folder_path + '"'
      );
    }
  }
  var needsMove = srcFolder.container().id() !== destFolder.id();
  var srcId = srcFolder.id();
  var destId = destFolder.id();
  // Rename now, while srcFolder is still a fresh (pre-move) reference —
  // safe regardless of whether a move follows.
  if (cmd.new_name) {
    srcFolder.name = cmd.new_name;
  }
  return {
    src_id: srcId,
    dest_id: destId,
    needs_move: needsMove,
  };
}
