"""Backend functions for interacting with Apple Notes: ls, grep, mkdir, mv,
rm (stub), cat, append.

Talks to Notes.app exclusively through JavaScript for Automation (JXA) via
the macOS-bundled `osascript` binary — no third-party dependency. Arguments
are passed through argv, never string-interpolated into the script source,
to avoid script injection from note/folder names (see
specs/002-apple-notes-core-ops/research.md §1).
"""

import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)


class AppleNotesError(Exception):
    """Base class for all errors raised by this module."""


class NotFoundError(AppleNotesError):
    """A referenced note, folder, or parent folder does not exist."""


class AlreadyExistsError(AppleNotesError):
    """A folder with the requested name already exists under the same parent."""


class InvalidPatternError(AppleNotesError):
    """`grep` was given a string that is not a valid regular expression."""


class AutomationPermissionError(AppleNotesError):
    """macOS has not granted Notes automation permission yet."""


class NotImplementedYetError(AppleNotesError):
    """Raised by the `rm` stub. Always."""


class AmbiguousMatchError(AppleNotesError):
    """`append`'s (folder_path, name) matches more than one existing note."""


_EXCEPTION_TYPES: dict[str, type[AppleNotesError]] = {
    "NotFoundError": NotFoundError,
    "AlreadyExistsError": AlreadyExistsError,
    "InvalidPatternError": InvalidPatternError,
    "AutomationPermissionError": AutomationPermissionError,
    "AmbiguousMatchError": AmbiguousMatchError,
    "AppleNotesError": AppleNotesError,
}


@dataclass(frozen=True)
class Note:
    id: str
    name: str
    folder_path: str


@dataclass(frozen=True)
class Folder:
    name: str
    path: str
    parent_path: str | None


@dataclass(frozen=True)
class FolderListing:
    folders: list[Folder]
    notes: list[Note]


# JXA driver script. Fixed and static — every call passes its arguments via
# argv (JSON-encoded in argv[0]), never by interpolating strings into this
# source, so note/folder names containing quotes or script-meaningful
# characters can never break out of the script (research.md §1).
_JXA_DRIVER = r"""
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

function dispatch(Notes, cmd) {
  var acct = Notes.accounts[0];

  if (cmd.op === "ls") {
    var lsFolder = resolveFolder(acct, cmd.folder_path);
    return listImmediate(lsFolder, cmd.folder_path);
  }

  if (cmd.op === "grep") {
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

  if (cmd.op === "mkdir") {
    var parent = resolveFolder(acct, cmd.parent_path);
    var dupCheck = parent.folders.whose({ name: cmd.name })();
    if (dupCheck.length > 0) {
      throwCustom(
        "AlreadyExistsError",
        'Folder "' + cmd.name + '" already exists under "' + cmd.parent_path + '"'
      );
    }
    var newFolder = Notes.Folder({ name: cmd.name });
    parent.folders.push(newFolder);
    return folderToJson(newFolder, cmd.parent_path + "/" + cmd.name);
  }

  if (cmd.op === "mv") {
    // Notes.move(item, {to: X}) throws "Can't get object" (-1728) when X
    // is already the item's current container, even though nothing needs
    // to move — only call it when the container truly differs. This path
    // is only used for notes: moving *folders* via JXA's Notes.move() is
    // unreliable on this platform (see mv_folder_prepare below, which
    // hands the actual cross-folder move off to classic AppleScript
    // instead).
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
      var newTitleDiv = "<div>" + escapeHtml(cmd.new_name) + "</div>";
      note.body = body.replace(/^<div>[\s\S]*?<\/div>/, newTitleDiv);
    }
    return { id: note.id(), name: note.name(), folder_path: cmd.destination_folder_path };
  }

  // Folder cross-parent moves are handled by a classic-AppleScript `move`
  // (see _move_folder_via_applescript in Python), not JXA's own
  // Notes.move() — but the deeper platform issue is not which language
  // performs the move: on this platform, a folder that has been moved to
  // a *different* parent becomes permanently un-dereferenceable by any
  // subsequent script (JXA *or* AppleScript) — collection-level queries
  // like `.name()`/`.length` still see it, but calling any method/property
  // on a freshly-obtained reference to that specific item (by id, by
  // whose(), or by bracket-index) throws "Can't get object" (-1728),
  // forever, even long after the move. So: never touch the folder again
  // after moving it. Any rename must happen *before* the move, while the
  // reference is still good, and the JSON returned to Python is built from
  // already-known values (no further Notes query needed for the result).
  if (cmd.op === "mv_folder_prepare") {
    var prepDestFolder = resolveFolder(acct, cmd.destination_folder_path);
    var prepSrcFolder = resolveFolder(acct, cmd.identifier);
    if (cmd.new_name) {
      var prepDup = prepDestFolder.folders.whose({ name: cmd.new_name })();
      if (prepDup.length > 0) {
        throwCustom(
          "AlreadyExistsError",
          'Folder "' + cmd.new_name + '" already exists under "' + cmd.destination_folder_path + '"'
        );
      }
    }
    var prepNeedsMove = prepSrcFolder.container().id() !== prepDestFolder.id();
    var prepSrcId = prepSrcFolder.id();
    var prepDestId = prepDestFolder.id();
    // Rename now, while srcFolder is still a fresh (pre-move) reference —
    // safe regardless of whether a move follows.
    if (cmd.new_name) {
      prepSrcFolder.name = cmd.new_name;
    }
    return {
      src_id: prepSrcId,
      dest_id: prepDestId,
      needs_move: prepNeedsMove,
    };
  }

  if (cmd.op === "cat") {
    var catNote = noteById(Notes, cmd.note_id);
    return { plaintext: catNote.plaintext() };
  }

  if (cmd.op === "append") {
    var appendFolder = resolveFolder(acct, cmd.folder_path);
    var appendNoteNames = appendFolder.notes.name();
    var matchCount = appendNoteNames.filter(function (n) { return n === cmd.name; }).length;
    if (matchCount > 1) {
      throwCustom(
        "AmbiguousMatchError",
        'More than one note named "' + cmd.name + '" in "' + cmd.folder_path + '"'
      );
    }
    var targetNote;
    if (matchCount === 1) {
      targetNote = findByName(appendFolder.notes, cmd.name);
      var existingBody = targetNote.body();
      targetNote.body = existingBody + "<div>" + escapeHtml(cmd.text) + "</div>";
    } else {
      targetNote = Notes.Note({ name: escapeHtml(cmd.name), body: escapeHtml(cmd.text) });
      appendFolder.notes.push(targetNote);
    }
    return { id: targetNote.id(), name: targetNote.name(), folder_path: cmd.folder_path };
  }

  throwCustom("AppleNotesError", "Unknown op: " + cmd.op);
}

function run(argv) {
  var Notes = Application("Notes");
  var command = JSON.parse(argv[0]);
  try {
    var result = dispatch(Notes, command);
    return JSON.stringify({ ok: true, result: result });
  } catch (e) {
    if (e && e.customType) {
      return JSON.stringify({ ok: false, error_type: e.customType, message: e.message });
    }
    return JSON.stringify({ ok: false, error_type: "AppleNotesError", message: String((e && e.message) || e) });
  }
}
"""


def _run_jxa(command: dict) -> object:
    """Invoke the JXA driver with `command` (JSON-encoded, passed via argv)
    and return its parsed `result`. Raises a typed AppleNotesError subclass
    on any failure — never lets a raw AppleScript/JXA error propagate.
    """
    op = command.get("op", "?")
    start = time.monotonic()
    try:
        proc = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", _JXA_DRIVER, "--", json.dumps(command)],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        duration_ms = (time.monotonic() - start) * 1000
        logger.error("op=%s outcome=error duration_ms=%.2f error=%r", op, duration_ms, exc)
        raise AppleNotesError(f"Failed to invoke osascript: {exc}") from exc

    duration_ms = (time.monotonic() - start) * 1000

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        logger.error("op=%s outcome=error duration_ms=%.2f stderr=%r", op, duration_ms, stderr)
        if "-1743" in stderr:
            raise AutomationPermissionError(
                "Notes automation permission has not been granted. Grant it via "
                "System Settings -> Privacy & Security -> Automation."
            )
        raise AppleNotesError(f"osascript failed: {stderr or '(no stderr)'}")

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        logger.error("op=%s outcome=error duration_ms=%.2f error=bad_json", op, duration_ms)
        raise AppleNotesError(f"Unexpected non-JSON output from osascript: {proc.stdout!r}") from exc

    if not payload.get("ok", False):
        error_type = payload.get("error_type", "AppleNotesError")
        message = payload.get("message", "Unknown error")
        logger.warning("op=%s outcome=error duration_ms=%.2f error_type=%s", op, duration_ms, error_type)
        exc_cls = _EXCEPTION_TYPES.get(error_type, AppleNotesError)
        raise exc_cls(message)

    logger.info("op=%s outcome=success duration_ms=%.2f", op, duration_ms)
    return payload["result"]


def _plaintext_to_content(plaintext: str) -> str:
    """Strip a note's title line (always plaintext's first line — Apple
    Notes derives the displayed title from it) to get just its content.
    """
    idx = plaintext.find("\n")
    content = "" if idx == -1 else plaintext[idx + 1 :]
    if content.endswith("\n"):
        content = content[:-1]
    return content


def ls(folder_path: str) -> FolderListing:
    """List the immediate notes and subfolders inside folder_path."""
    result = _run_jxa({"op": "ls", "folder_path": folder_path})
    folders = [Folder(**f) for f in result["folders"]]
    notes = [Note(**n) for n in result["notes"]]
    return FolderListing(folders=folders, notes=notes)


def grep(pattern: str, folder_path: str | None = None) -> list[Note]:
    """Search note content by regex `pattern`. Searches the whole account
    when `folder_path` is omitted, or that folder (and its subfolders) when
    given.
    """
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise InvalidPatternError(f"Invalid regular expression {pattern!r}: {exc}") from exc

    command: dict = {"op": "grep"}
    if folder_path is not None:
        command["folder_path"] = folder_path
    result = _run_jxa(command)

    return [
        Note(id=n["id"], name=n["name"], folder_path=n["folder_path"])
        for n in result["notes"]
        if compiled.search(n["plaintext"])
    ]


def mkdir(parent_path: str, name: str) -> Folder:
    """Create a new, empty folder named `name` directly under `parent_path`."""
    result = _run_jxa({"op": "mkdir", "parent_path": parent_path, "name": name})
    return Folder(**result)


# Classic AppleScript (not JXA) — used only for moving a folder to a
# different parent. JXA's Notes.move() is unreliable for folders on this
# platform (can throw spuriously, or fail to actually move the folder);
# the same operation via classic AppleScript's `move` command works
# reliably. Fixed and static; ids are passed via argv, never interpolated.
_APPLESCRIPT_MOVE_FOLDER = """
on run argv
    set srcId to item 1 of argv
    set destId to item 2 of argv
    tell application "Notes"
        set srcFolder to folder id srcId
        set destFolder to folder id destId
        move srcFolder to destFolder
    end tell
    return "ok"
end run
"""


def _move_folder_via_applescript(src_id: str, dest_id: str) -> None:
    op = "mv_folder_applescript"
    start = time.monotonic()
    proc = subprocess.run(
        ["osascript", "-e", _APPLESCRIPT_MOVE_FOLDER, "--", src_id, dest_id],
        capture_output=True,
        text=True,
    )
    duration_ms = (time.monotonic() - start) * 1000
    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        logger.error("op=%s outcome=error duration_ms=%.2f stderr=%r", op, duration_ms, stderr)
        if "-1743" in stderr:
            raise AutomationPermissionError(
                "Notes automation permission has not been granted. Grant it via "
                "System Settings -> Privacy & Security -> Automation."
            )
        raise AppleNotesError(f"Failed to move folder: {stderr or '(no stderr)'}")
    logger.info("op=%s outcome=success duration_ms=%.2f", op, duration_ms)


def mv(
    kind: Literal["note", "folder"],
    identifier: str,
    destination_folder_path: str,
    new_name: str | None = None,
) -> Note | Folder:
    """Move (and optionally rename) a note (identifier = its id) or folder
    (identifier = its path) into destination_folder_path.

    Known platform limitation (research.md #10): after moving a folder to
    a different parent, that destination folder's contents may become
    unreadable via ls()/grep() in the same Notes.app session — this is a
    Notes.app scripting bug (the moved item's object reference breaks),
    not data loss; the folder and its contents are unaffected in the
    Notes app itself.
    """
    if kind == "note":
        command = {
            "op": "mv",
            "identifier": identifier,
            "destination_folder_path": destination_folder_path,
            "new_name": new_name,
        }
        result = _run_jxa(command)
        return Note(**result)

    prep = _run_jxa(
        {
            "op": "mv_folder_prepare",
            "identifier": identifier,
            "destination_folder_path": destination_folder_path,
            "new_name": new_name,
        }
    )
    if prep["needs_move"]:
        _move_folder_via_applescript(prep["src_id"], prep["dest_id"])
    # Deliberately no further Notes query here: a folder that has just been
    # moved to a different parent becomes permanently un-dereferenceable
    # (see mv_folder_prepare's comment in the JXA driver above), so the
    # result is built entirely from values already known to Python/JXA
    # rather than trying to read the moved folder back.
    final_name = new_name or identifier.rsplit("/", 1)[-1]
    return Folder(
        name=final_name,
        path=f"{destination_folder_path}/{final_name}",
        parent_path=destination_folder_path,
    )


def rm(kind: Literal["note", "folder"], identifier: str) -> None:
    """Stub for this feature. Always raises NotImplementedYetError and never
    touches Notes data. Real removal behavior is deferred to a future
    feature.
    """
    logger.info("op=rm outcome=not_implemented kind=%s", kind)
    raise NotImplementedYetError(
        "rm is not implemented yet in this feature; no note or folder was removed."
    )


def cat(note_id: str) -> str:
    """Return the content of the note identified by note_id (its title line
    stripped — see _plaintext_to_content).
    """
    result = _run_jxa({"op": "cat", "note_id": note_id})
    return _plaintext_to_content(result["plaintext"])


def append(folder_path: str, name: str, text: str) -> Note:
    """Append `text` to the note named `name` in `folder_path`, creating an
    empty note there first if none exists yet. Raises AmbiguousMatchError if
    more than one note already has that name in that folder.
    """
    result = _run_jxa({"op": "append", "folder_path": folder_path, "name": name, "text": text})
    return Note(**result)
