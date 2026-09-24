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

// Converts plain text to Notes body HTML, one <div> per line. Notes'
// body is HTML, so raw "\n" characters in it collapse to whitespace;
// Notes itself stores each line as its own <div>, with <div><br></div>
// for a blank line.
function textToHtml(text) {
  return String(text)
    .split("\n")
    .map(function (line) { return "<div>" + (line.length ? escapeHtml(line) : "<br>") + "</div>"; })
    .join("");
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
//
// The item found is returned as a by-id specifier, never as the index
// specifier itself (collection[idx]): index specifiers are re-evaluated on
// every access, so they silently point at a different item once the
// collection reorders — e.g. a folder whose name sorts earlier being added
// to the account's (flattened) folder list, or a note being edited and
// moving to the top of its folder's modified-date order. Names and ids
// are read with the same bulk property fetch shape so they line up.
function findByName(itemsCollection, name) {
  var names = itemsCollection.name();
  var idx = names.indexOf(name);
  if (idx === -1) {
    return null;
  }
  return itemsCollection.byId(itemsCollection.id()[idx]);
}

// `account.folders` lists *every* folder in the account, nested ones
// included, flattened — not just its top-level folders. Anything that
// means "the folders directly at the account root" goes through these
// helpers, which keep only folders whose container is the account itself.
// Returns [{id, name}] in the account's folder order.
function topLevelFolders(acct) {
  var acctId = acct.id();
  var containerIds = acct.folders.container.id();
  var ids = acct.folders.id();
  var names = acct.folders.name();
  var result = [];
  for (var i = 0; i < ids.length; i++) {
    if (containerIds[i] === acctId) {
      result.push({ id: ids[i], name: names[i] });
    }
  }
  return result;
}

function findTopLevelFolder(acct, name) {
  var matches = topLevelFolders(acct).filter(function (f) { return f.name === name; });
  return matches.length === 0 ? null : acct.folders.byId(matches[0].id);
}

// A folder's `folders` collection can still include children that are no
// longer really there: a folder deleted with Notes.delete, or moved to a
// different parent (see mv_folder_prepare.js), keeps showing up in its
// parent's bulk .name()/.id() arrays, but dereferencing it in any way
// throws "Can't get object" (-1728), and it's gone from the account's
// flattened folder list. Only children still in that list are real,
// readable folders, so everything that walks or looks up a folder's
// children goes through these helpers — one such leftover must not break
// listing, searching, or resolving paths through its parent.
//
// Returns an id -> true map of every folder in the account, for passing
// to liveSubfolders (computed once per script, not once per folder).
function liveFolderIds(acct) {
  var live = {};
  acct.folders.id().forEach(function (id) { live[id] = true; });
  return live;
}

// Returns [{id, name}] for `folder`'s direct subfolders that are still
// live (see above), in the parent's folder order.
function liveSubfolders(folder, liveIds) {
  var ids = folder.folders.id();
  var names = folder.folders.name();
  var result = [];
  for (var i = 0; i < ids.length; i++) {
    if (liveIds[ids[i]]) {
      result.push({ id: ids[i], name: names[i] });
    }
  }
  return result;
}

function findLiveSubfolder(folder, name, liveIds) {
  var matches = liveSubfolders(folder, liveIds).filter(function (f) { return f.name === name; });
  return matches.length === 0 ? null : folder.folders.byId(matches[0].id);
}

function resolveFolder(acct, path) {
  var parts = String(path).split("/").filter(function (p) { return p.length > 0; });
  if (parts.length === 0) {
    throwCustom("NotFoundError", "Empty folder path");
  }
  var liveIds = parts.length > 1 ? liveFolderIds(acct) : null;
  var current = acct;
  var seen = [];
  for (var i = 0; i < parts.length; i++) {
    var name = parts[i];
    var found = i === 0 ? findTopLevelFolder(acct, name) : findLiveSubfolder(current, name, liveIds);
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

function listImmediate(acct, folder, path) {
  var folders = liveSubfolders(folder, liveFolderIds(acct)).map(function (f) {
    return { name: f.name, path: path + "/" + f.name, parent_path: path };
  });
  var noteIds = folder.notes.id();
  var noteNames = folder.notes.name();
  var notes = [];
  for (var j = 0; j < noteIds.length; j++) {
    notes.push({ id: noteIds[j], name: noteNames[j], folder_path: path });
  }
  return { folders: folders, notes: notes };
}

function collectNotesRecursive(folder, path, liveIds) {
  var ids = folder.notes.id();
  var names = folder.notes.name();
  var plaintexts = folder.notes.plaintext();
  var results = [];
  for (var i = 0; i < ids.length; i++) {
    results.push({ id: ids[i], name: names[i], folder_path: path, plaintext: plaintexts[i] });
  }
  var subfolders = liveSubfolders(folder, liveIds);
  for (var j = 0; j < subfolders.length; j++) {
    var sub = folder.folders.byId(subfolders[j].id);
    results = results.concat(collectNotesRecursive(sub, path + "/" + subfolders[j].name, liveIds));
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
