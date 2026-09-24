// Notes.move(item, {to: X}) throws "Can't get object" (-1728) when X is
// already the item's current container, even though nothing needs to
// move — only call it when the container truly differs. This script is
// only used for notes: moving *folders* is handled by
// mv_folder_prepare.js + classic AppleScript instead (see that file for
// why).
function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var destFolder = resolveFolder(acct, cmd.destination_folder_path);
  var note = noteById(Notes, cmd.identifier);
  if (note.container().id() !== destFolder.id()) {
    try {
      Notes.move(note, { to: destFolder });
    } catch (e) {
      // ignore — verified below
    }
    var noteId = note.id();
    note = Notes.notes.byId(noteId);
    if (note.container().id() !== destFolder.id()) {
      throwCustom("AppleNotesError", "Failed to move note to the destination folder");
    }
  }
  if (cmd.new_name) {
    var body = note.body();
    var newTitleDiv = "<div>" + preserveWhitespace(escapeHtml(cmd.new_name)) + "</div>";
    // A replacer function, not a string: in a replacement string, "$&",
    // "$1", ... in new_name would be expanded.
    note.body = preserveBodyWhitespace(body).replace(/^<div>[\s\S]*?<\/div>/, function () { return newTitleDiv; });
  }
  return { id: note.id(), name: note.name(), folder_path: cmd.destination_folder_path };
}
