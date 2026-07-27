function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var allNotes = [];
  if (cmd.folder_path) {
    var scopeFolder = resolveFolder(acct, cmd.folder_path);
    allNotes = collectNotesRecursive(scopeFolder, cmd.folder_path);
  } else {
    var topFolders = acct.folders();
    var topNames = acct.folders.name();
    for (var i = 0; i < topFolders.length; i++) {
      allNotes = allNotes.concat(collectNotesRecursive(topFolders[i], topNames[i]));
    }
  }
  return { notes: allNotes };
}
