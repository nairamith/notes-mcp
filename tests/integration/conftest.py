"""Fixtures for Apple Notes integration tests.

These tests touch real Notes.app data, so everything here operates inside
a dedicated, disposable scratch folder created fresh per test and torn
down afterward — never the developer's/user's real personal folders
(constitution Principle II). Fixture setup/teardown talks to Notes.app
directly via its own small JXA scripts, bypassing `mkdir`/`rm`/`append`
(the functions under test), so a bug in those functions can't corrupt test
fixtures or mask itself by "testing mkdir using mkdir."
"""

import json
import subprocess
import uuid

import pytest

# Shared by the fixture scripts below. `account.folders` is flattened (it
# lists nested folders too, in name order), and index specifiers like
# `folders[idx]` are re-evaluated on each access, so they can land on a
# different folder — for a teardown that deletes, possibly a real one.
# Resolve by name through bulk id/name/container arrays and dereference by
# id only.
_FIXTURE_HELPERS = """
function topLevelFolderId(acct, name) {
  var acctId = acct.id();
  var containerIds = acct.folders.container.id();
  var ids = acct.folders.id();
  var names = acct.folders.name();
  for (var i = 0; i < ids.length; i++) {
    if (containerIds[i] === acctId && names[i] === name) { return ids[i]; }
  }
  return null;
}

function resolveFixtureFolder(acct, folderPath) {
  var parts = folderPath.split("/").filter(function (p) { return p.length > 0; });
  var current = acct.folders.byId(topLevelFolderId(acct, parts[0]));
  for (var i = 1; i < parts.length; i++) {
    var idx = current.folders.name().indexOf(parts[i]);
    current = current.folders.byId(current.folders.id()[idx]);
  }
  return current;
}
"""

_SCRATCH_BOOTSTRAP = """
function run(argv) {
  var Notes = Application("Notes");
  var acct = Notes.accounts[0];
  var name = argv[0];
  acct.folders.push(Notes.Folder({ name: name }));
  return "ok";
}
"""

_RECURSIVE_DELETE = _FIXTURE_HELPERS + """
function run(argv) {
  var Notes = Application("Notes");
  var acct = Notes.accounts[0];
  var name = argv[0];
  function deleteRecursive(folder) {
    try {
      var subIds = folder.folders.id();
      for (var i = 0; i < subIds.length; i++) {
        try { deleteRecursive(folder.folders.byId(subIds[i])); } catch (e) {}
      }
    } catch (e) {}
    try { Notes.delete(folder); } catch (e) {}
  }
  var id = topLevelFolderId(acct, name);
  if (id !== null) { deleteRecursive(acct.folders.byId(id)); }
  return "ok";
}
"""

_SEED_NOTE = _FIXTURE_HELPERS + """
function run(argv) {
  var Notes = Application("Notes");
  var acct = Notes.accounts[0];
  var folderPath = argv[0];
  var name = argv[1];
  var body = argv[2];
  var current = resolveFixtureFolder(acct, folderPath);
  var n = Notes.Note({ name: name, body: body });
  current.notes.push(n);
  return JSON.stringify({ id: n.id(), name: n.name() });
}
"""

_DELETE_NOTE_BY_ID = """
function run(argv) {
  var Notes = Application("Notes");
  var noteId = argv[0];
  try {
    var note = Notes.notes.byId(noteId);
    Notes.delete(note);
  } catch (e) {}
  return "ok";
}
"""

_SEED_SUBFOLDER = _FIXTURE_HELPERS + """
function run(argv) {
  var Notes = Application("Notes");
  var acct = Notes.accounts[0];
  var folderPath = argv[0];
  var name = argv[1];
  var current = resolveFixtureFolder(acct, folderPath);
  var f = Notes.Folder({ name: name });
  current.folders.push(f);
  return JSON.stringify({ name: f.name() });
}
"""


def _run_test_jxa(script: str, args: list[str]) -> str:
    """Invoke a fixture-only JXA script (never one of the module-under-test's
    scripts) and return its raw stdout.
    """
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", script, "--", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Fixture JXA script failed: {proc.stderr.strip()}")
    return proc.stdout


def _notes_scriptable() -> bool:
    """True if Notes.app can currently be scripted (macOS + permission granted)."""
    try:
        proc = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", 'Application("Notes").accounts.length'],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


@pytest.fixture(scope="session")
def notes_available() -> bool:
    return _notes_scriptable()


@pytest.fixture
def skip_without_notes(notes_available):
    if not notes_available:
        pytest.skip("Notes.app is not scriptable in this environment (not macOS, or Automation permission not granted)")


@pytest.fixture
def scratch_folder(skip_without_notes):
    """Creates a dedicated, uniquely-named top-level scratch folder for a
    single test and recursively deletes it afterward.
    """
    name = f"_notes_mcp_test_{uuid.uuid4().hex[:12]}"
    _run_test_jxa(_SCRATCH_BOOTSTRAP, [name])
    yield name
    _run_test_jxa(_RECURSIVE_DELETE, [name])


@pytest.fixture
def late_sorting_scratch_folder(skip_without_notes):
    """Like scratch_folder, but named to sort *after* typical subfolder
    names in the account's folder list, for tests where a new subfolder
    must sort before its own top-level parent.
    """
    name = f"zz_notes_mcp_test_{uuid.uuid4().hex[:12]}"
    _run_test_jxa(_SCRATCH_BOOTSTRAP, [name])
    yield name
    _run_test_jxa(_RECURSIVE_DELETE, [name])


@pytest.fixture
def seed_note():
    """Factory fixture: seed_note(folder_path, name, body) creates a note
    directly (bypassing append/mkdir) for use as fixture data.
    """

    def _seed(folder_path: str, name: str, body: str) -> dict:
        return json.loads(_run_test_jxa(_SEED_NOTE, [folder_path, name, body]))

    return _seed


@pytest.fixture
def delete_note_by_id():
    """Factory fixture: delete_note_by_id(note_id) removes exactly that note,
    bypassing the (not-yet-implemented) rm tool. Used to clean up a note
    created in a persistent, non-scratch location (e.g. the top-level
    "archive" folder update_note's overwrite mode writes to), never a
    substitute for scratch_folder's own recursive teardown.
    """

    def _delete(note_id: str) -> None:
        _run_test_jxa(_DELETE_NOTE_BY_ID, [note_id])

    return _delete


@pytest.fixture
def seed_subfolder():
    """Factory fixture: seed_subfolder(folder_path, name) creates a folder
    directly (bypassing mkdir) for use as fixture data.
    """

    def _seed(folder_path: str, name: str) -> dict:
        return json.loads(_run_test_jxa(_SEED_SUBFOLDER, [folder_path, name]))

    return _seed


@pytest.fixture
def delete_top_level_folder():
    """Factory fixture: delete_top_level_folder(name) recursively deletes
    the *top-level* folder `name`, for a test that had to create one
    outside its scratch folder (e.g. `mkdir("", ...)`). Only ever pass it
    a uniquely-named folder the test itself created.
    """

    def _delete(name: str) -> None:
        _run_test_jxa(_RECURSIVE_DELETE, [name])

    return _delete
