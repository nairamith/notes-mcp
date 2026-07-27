// Shared helpers for every jxa_scripts/*.js file. Each operation script
// (ls.js, grep.js, ...) is concatenated with this file before being handed
// to osascript, and defines its own `handle(Notes, cmd)` function; this
// file supplies the shared helpers plus the run(argv) entry point that
// calls handle().

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function throwCustom(errorType, message) {
  throw { customType: errorType, message: message };
}

// Dereferencing a whose()-filtered result by index (e.g.
// collection.whose({name: X})()[0]) can throw "Can't get object" (-1728)
// for an item that was moved by a *different* process moments earlier
// (classic AppleScript vs. this JXA process), even though the same
// collection's .name()/.length report it correctly. Bracket-indexing into
// the *unfiltered* collection, at the index found via its .name() array,
// does not have this problem — so every by-name lookup in this module
// goes through this helper instead of whose().
function findByName(itemsCollection, name) {
  var names = itemsCollection.name();
  var idx = names.indexOf(name);
  return idx === -1 ? null : itemsCollection[idx];
}

function resolveFolder(acct, path) {
  var parts = String(path).split("/").filter(function (p) { return p.length > 0; });
  if (parts.length === 0) {
    throwCustom("NotFoundError", "Empty folder path");
  }
  var current = acct;
  var seen = [];
  for (var i = 0; i < parts.length; i++) {
    var name = parts[i];
    var found = findByName(current.folders, name);
    if (!found) {
      throwCustom(
        "NotFoundError",
        'No folder named "' + name + '" under "' + (seen.join("/") || "<root>") + '"'
      );
    }
    current = found;
    seen.push(name);
  }
  return current;
}

function folderToJson(folder, path) {
  var parts = path.split("/");
  var parentPath = parts.length > 1 ? parts.slice(0, -1).join("/") : null;
  return { name: folder.name(), path: path, parent_path: parentPath };
}

function listImmediate(folder, path) {
  var subfolders = folder.folders();
  var folderNames = folder.folders.name();
  var folders = [];
  for (var i = 0; i < subfolders.length; i++) {
    folders.push(folderToJson(subfolders[i], path + "/" + folderNames[i]));
  }
  var noteIds = folder.notes.id();
  var noteNames = folder.notes.name();
  var notes = [];
  for (var j = 0; j < noteIds.length; j++) {
    notes.push({ id: noteIds[j], name: noteNames[j], folder_path: path });
  }
  return { folders: folders, notes: notes };
}

function collectNotesRecursive(folder, path) {
  var ids = folder.notes.id();
  var names = folder.notes.name();
  var plaintexts = folder.notes.plaintext();
  var results = [];
  for (var i = 0; i < ids.length; i++) {
    results.push({ id: ids[i], name: names[i], folder_path: path, plaintext: plaintexts[i] });
  }
  var subfolders = folder.folders();
  var subNames = folder.folders.name();
  for (var j = 0; j < subfolders.length; j++) {
    results = results.concat(collectNotesRecursive(subfolders[j], path + "/" + subNames[j]));
  }
  return results;
}

function noteById(Notes, noteId) {
  var note;
  try {
    note = Notes.notes.byId(noteId);
    note.id();
  } catch (e) {
    throwCustom("NotFoundError", 'No note with id "' + noteId + '"');
  }
  return note;
}

function run(argv) {
  var Notes = Application("Notes");
  var command = JSON.parse(argv[0]);
  try {
    var result = handle(Notes, command);
    return JSON.stringify({ ok: true, result: result });
  } catch (e) {
    if (e && e.customType) {
      return JSON.stringify({ ok: false, error_type: e.customType, message: e.message });
    }
    return JSON.stringify({ ok: false, error_type: "AppleNotesError", message: String((e && e.message) || e) });
  }
}
