"""Backend functions for interacting with Apple Notes: ls, grep, mkdir, mv,
rm (stub), cat, append.

Talks to Notes.app exclusively through JavaScript for Automation (JXA) via
the macOS-bundled `osascript` binary — no third-party dependency. Arguments
are passed through argv, never string-interpolated into the script source,
to avoid script injection from note/folder names (see
specs/002-apple-notes-core-ops/research.md §1). Each operation's JXA logic
lives in its own file under jxa_scripts/ (shared helpers in
jxa_scripts/common.js), combined at call time.
"""

import json
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Literal

from .exceptions import (
    EXCEPTION_TYPES,
    AlreadyExistsError,
    AmbiguousMatchError,
    AppleNotesError,
    AutomationPermissionError,
    InvalidPatternError,
    NotFoundError,
    NotImplementedYetError,
)
from .schema import Folder, FolderListing, Note

__all__ = [
    "AlreadyExistsError",
    "AmbiguousMatchError",
    "AppleNotesError",
    "AutomationPermissionError",
    "Folder",
    "FolderListing",
    "InvalidPatternError",
    "Note",
    "NotFoundError",
    "NotImplementedYetError",
    "append",
    "cat",
    "grep",
    "ls",
    "mkdir",
    "mv",
    "rm",
]

logger = logging.getLogger(__name__)

_SCRIPTS_DIR = Path(__file__).parent / "jxa_scripts"
_COMMON_JS = (_SCRIPTS_DIR / "common.js").read_text()


def _load_jxa_script(op: str) -> str:
    """Combine the shared helpers (common.js) with the operation-specific
    `handle(Notes, cmd)` implementation in jxa_scripts/<op>.js.
    """
    op_js = (_SCRIPTS_DIR / f"{op}.js").read_text()
    return _COMMON_JS + "\n" + op_js


def _run_jxa(command: dict) -> object:
    """Invoke the JXA script for `command["op"]` (JSON-encoded, passed via
    argv) and return its parsed `result`. Raises a typed AppleNotesError
    subclass on any failure — never lets a raw AppleScript/JXA error
    propagate.
    """
    op = command.get("op", "?")
    script = _load_jxa_script(op)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script, "--", json.dumps(command)],
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
        exc_cls = EXCEPTION_TYPES.get(error_type, AppleNotesError)
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


def _move_folder_via_applescript(src_id: str, dest_id: str) -> None:
    """Classic AppleScript (not JXA) — used only for moving a folder to a
    different parent. JXA's Notes.move() is unreliable for folders on this
    platform (can throw spuriously, or fail to actually move the folder);
    the same operation via classic AppleScript's `move` command works
    reliably (see jxa_scripts/mv_folder_prepare.js for the full platform
    caveat). Fixed and static; ids are passed via argv, never interpolated.
    """
    op = "mv_folder_applescript"
    script = (_SCRIPTS_DIR / "move_folder.applescript").read_text()
    start = time.monotonic()
    proc = subprocess.run(
        ["osascript", "-e", script, "--", src_id, dest_id],
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
            "op": "mv_note",
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
    # (see jxa_scripts/mv_folder_prepare.js), so the result is built
    # entirely from values already known to Python/JXA rather than trying
    # to read the moved folder back.
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
