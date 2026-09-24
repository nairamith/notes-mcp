function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var allNotes = [];
  if (cmd.folder_path) {
    var scopeFolder = resolveFolder(acct, cmd.folder_path);
    allNotes = collectNotesRecursive(scopeFolder, cmd.folder_path);
  } else {
    var topFolders = topLevelFolders(acct);
    for (var i = 0; i < topFolders.length; i++) {
      var folder = acct.folders.byId(topFolders[i].id);
      allNotes = allNotes.concat(collectNotesRecursive(folder, topFolders[i].name));
    }
  }
  return { notes: allNotes };
}
