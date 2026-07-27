function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var isRoot = cmd.parent_path === "";
  var parent = isRoot ? acct : resolveFolder(acct, cmd.parent_path);
  var dupCheck = parent.folders.whose({ name: cmd.name })();
  if (dupCheck.length > 0) {
    throwCustom(
      "AlreadyExistsError",
      'Folder "' + cmd.name + '" already exists under "' + cmd.parent_path + '"'
    );
  }
  var newFolder = Notes.Folder({ name: cmd.name });
  parent.folders.push(newFolder);
  var path = isRoot ? cmd.name : cmd.parent_path + "/" + cmd.name;
  return folderToJson(newFolder, path);
}
