function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var folder = resolveFolder(acct, cmd.folder_path);
  return listImmediate(folder, cmd.folder_path);
}
