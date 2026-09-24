function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var parts = String(cmd.folder_path).split("/").filter(function (p) { return p.length > 0; });
  if (parts.length === 0) {
    // The account root: its top-level folders. Notes always keeps notes
    // inside some folder, so the root itself never has notes.
    var folders = topLevelFolders(acct).map(function (f) {
      return { name: f.name, path: f.name, parent_path: null };
    });
    return { folders: folders, notes: [] };
  }
  var folder = resolveFolder(acct, cmd.folder_path);
  return listImmediate(acct, folder, cmd.folder_path);
}
