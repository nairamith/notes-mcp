function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var folder = resolveFolder(acct, cmd.folder_path);
  var noteNames = folder.notes.name();
  var matchCount = noteNames.filter(function (n) { return n === cmd.name; }).length;
  if (matchCount > 1) {
    throwCustom(
      "AmbiguousMatchError",
      'More than one note named "' + cmd.name + '" in "' + cmd.folder_path + '"'
    );
  }
  var targetNote;
  if (matchCount === 1) {
    targetNote = findByName(folder.notes, cmd.name);
    var existingBody = targetNote.body();
    targetNote.body = preserveBodyWhitespace(existingBody) + textToHtml(cmd.text);
  } else {
    // `name` is a plain-text property (Notes escapes it into the body
    // itself), so it must not be HTML-escaped here — only body HTML is.
    targetNote = Notes.Note({ name: cmd.name, body: textToHtml(cmd.text) });
    folder.notes.push(targetNote);
  }
  return { id: targetNote.id(), name: targetNote.name(), folder_path: cmd.folder_path };
}
