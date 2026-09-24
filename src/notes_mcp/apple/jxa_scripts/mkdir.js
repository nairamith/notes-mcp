function handle(Notes, cmd) {
  var acct = Notes.accounts[0];
  var isRoot = cmd.parent_path === "";
  var parent = isRoot ? acct : resolveFolder(acct, cmd.parent_path);
  var duplicate = isRoot ? findTopLevelFolder(acct, cmd.name) : findByName(parent.folders, cmd.name);
  if (duplicate) {
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
