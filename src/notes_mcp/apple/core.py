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
    InvalidNameError,
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
    "InvalidNameError",
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
    "validate_note_name",
]

logger = logging.getLogger(__name__)

_SCRIPTS_DIR = Path(__file__).parent / "jxa_scripts"
_COMMON_JS = (_SCRIPTS_DIR / "common.js").read_text()


def _load_jxa_script(op: str) -> str:
    """Combines the shared JXA helpers with one operation's script.

    Args:
        op: Operation name; must match a file name (without extension)
            under jxa_scripts/, e.g. "ls" for jxa_scripts/ls.js.

    Returns:
        The full JXA source: jxa_scripts/common.js followed by
        jxa_scripts/<op>.js, ready to pass to `osascript -l JavaScript -e`.
    """
    op_js = (_SCRIPTS_DIR / f"{op}.js").read_text()
    return _COMMON_JS + "\n" + op_js


_PATH_KEYS = ("folder_path", "parent_path", "destination_folder_path")


def _normalize_path(path: str) -> str:
    """Returns `path` in canonical form: no empty segments.

    Folder lookups already skip empty segments, so "A/B/", "A//B" and
    "/A/B" all name the same folder as "A/B" — this makes every path that
    flows back to the caller use that one spelling too.

    Args:
        path: A `/`-delimited folder path.

    Returns:
        `path` with leading, trailing, and repeated `/` removed ("" for
        the account root).
    """
    return "/".join(part for part in path.split("/") if part)


def _run_jxa(command: dict) -> object:
    """Invokes the JXA script for `command["op"]` and returns its result.

    `command` is JSON-encoded and passed to the script via argv, never
    interpolated into the script source (research.md §1). Any folder path
    fields in it are normalized first (see `_normalize_path`), so scripts
    only ever see — and echo back — canonical paths.

    Args:
        command: Must include an "op" key matching a file under
            jxa_scripts/, plus whatever fields that operation expects.

    Returns:
        The parsed `result` value from the script's JSON response.

    Raises:
        AutomationPermissionError: Notes automation permission hasn't
            been granted.
        AppleNotesError: `osascript` failed to run, returned output that
            isn't valid JSON, or reported an error type this module
            doesn't recognize.
        NotFoundError: Or another `AppleNotesError` subclass, raised
            based on the `error_type` the script itself reported.
    """
    op = command.get("op", "?")
    command = {
        key: _normalize_path(value) if key in _PATH_KEYS and isinstance(value, str) else value
        for key, value in command.items()
    }
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
    """Strips a note's title line from its plaintext to get its content.

    Apple Notes always derives a note's displayed title from the first
    line of its plaintext, so the content a caller actually wrote is
    everything after that line.

    Args:
        plaintext: The note's full plaintext as returned by Notes (title,
            a newline, then the body).

    Returns:
        `plaintext` with its title line and one trailing newline removed.
        An empty string for a title-only note.
    """
    idx = plaintext.find("\n")
    content = "" if idx == -1 else plaintext[idx + 1 :]
    if content.endswith("\n"):
        content = content[:-1]
    return content


def validate_note_name(name: str) -> None:
    """Rejects a name that can't be a note's title.

    Notes derives a note's title from the first line of its text, so an
    empty or whitespace-only name makes the first line of the content the
    title instead (silently removing it from the content), and a name
    with a line break has everything after the break end up in the
    content.

    Args:
        name: The proposed note name.

    Raises:
        InvalidNameError: `name` is empty, whitespace-only, or contains a
            line break.
    """
    if not name.strip():
        raise InvalidNameError("Note name must not be empty or whitespace-only")
    if "\n" in name or "\r" in name:
        raise InvalidNameError(f"Note name must be a single line, got {name!r}")


def ls(folder_path: str) -> FolderListing:
    """Lists the immediate notes and subfolders inside a folder.

    Args:
        folder_path: `/`-delimited path to the folder, rooted at a
            top-level folder (e.g. "Personal/Groceries").

    Returns:
        A FolderListing with that folder's direct subfolders and notes
        (not deeper descendants).

    Raises:
        NotFoundError: `folder_path` does not exist.
    """
    result = _run_jxa({"op": "ls", "folder_path": folder_path})
    folders = [Folder(**f) for f in result["folders"]]
    notes = [Note(**n) for n in result["notes"]]
    return FolderListing(folders=folders, notes=notes)


def grep(pattern: str, folder_path: str | None = None) -> list[Note]:
    """Searches note content for a regular expression.

    Args:
        pattern: A Python regular expression to search each note's
            content for (research.md §5 — evaluated as Python `re`, not
            JavaScript `RegExp`).
        folder_path: If given, restricts the search to this folder and
            its subfolders. Searches the entire account when omitted.

    Returns:
        The notes whose content matches `pattern`, as `Note` metadata —
        not their content; use `cat()` to read a specific note's content.

    Raises:
        InvalidPatternError: `pattern` is not a valid regular expression.
        NotFoundError: `folder_path` is given and does not exist.
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
    """Creates a new, empty folder under an existing parent.

    Args:
        parent_path: `/`-delimited path to the existing parent folder.
            An empty string creates a new top-level folder at the account
            root instead of nesting it under an existing parent.
        name: Name for the new folder.

    Returns:
        The newly created Folder.

    Raises:
        NotFoundError: `parent_path` is non-empty and does not exist.
        AlreadyExistsError: A folder named `name` already exists under
            `parent_path` (or, for an empty `parent_path`, at the account
            root).
    """
    result = _run_jxa({"op": "mkdir", "parent_path": parent_path, "name": name})
    return Folder(**result)


def _move_folder_via_applescript(src_id: str, dest_id: str) -> None:
    """Moves a folder to a different parent via classic AppleScript.

    JXA's own `Notes.move()` is unreliable for folders on this platform
    (can throw spuriously, or fail to actually move the folder); the same
    operation via classic AppleScript's `move` command works reliably
    (see jxa_scripts/mv_folder_prepare.js for the full platform caveat).
    The script is fixed and static; ids are passed via argv, never
    interpolated into the script source.

    Args:
        src_id: Notes' internal id of the folder to move.
        dest_id: Notes' internal id of the destination folder.

    Raises:
        AutomationPermissionError: Notes automation permission hasn't
            been granted.
        AppleNotesError: The AppleScript failed to run.
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
    """Moves and/or renames a note or folder.

    Known platform limitation (research.md #10): after moving a folder to
    a different parent, that destination folder's contents may become
    unreadable via `ls()`/`grep()` in the same Notes.app session. This is
    a Notes.app scripting bug (the moved item's object reference breaks),
    not data loss — the folder and its contents are unaffected in the
    Notes app itself.

    Args:
        kind: "note" or "folder" — which kind `identifier` refers to.
        identifier: The note's id (`kind="note"`) or the folder's path
            (`kind="folder"`).
        destination_folder_path: `/`-delimited path to the folder to
            move into.
        new_name: If given, renames the item in the same call.

    Returns:
        The moved/renamed Note or Folder (matching `kind`).

    Raises:
        NotFoundError: The target note/folder, or
            `destination_folder_path`, does not exist.
        AlreadyExistsError: Renaming a folder to a name that already
            exists under `destination_folder_path`.
        InvalidNameError: `kind="note"` and `new_name` is given but empty,
            whitespace-only, or multi-line (see `validate_note_name`).
            Checked before anything is moved.
    """
    if kind == "note":
        if new_name is not None:
            validate_note_name(new_name)
        command = {
            "op": "mv_note",
            "identifier": identifier,
            "destination_folder_path": destination_folder_path,
            "new_name": new_name,
        }
        result = _run_jxa(command)
        return Note(**result)

    identifier = _normalize_path(identifier)
    destination_folder_path = _normalize_path(destination_folder_path)
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
    """Stub for this feature — always raises, never touches Notes data.

    Real removal behavior is deferred to a future feature.

    Args:
        kind: "note" or "folder" — accepted for interface stability but
            not used yet.
        identifier: The note's id or the folder's path; not used yet.

    Raises:
        NotImplementedYetError: Always.
    """
    logger.info("op=rm outcome=not_implemented kind=%s", kind)
    raise NotImplementedYetError(
        "rm is not implemented yet in this feature; no note or folder was removed."
    )


def cat(note_id: str) -> str:
    """Returns a note's content.

    Args:
        note_id: Notes' internal id of the note to read.

    Returns:
        The note's content, with its title line stripped (see
        `_plaintext_to_content`).

    Raises:
        NotFoundError: No note with `note_id` exists.
    """
    result = _run_jxa({"op": "cat", "note_id": note_id})
    return _plaintext_to_content(result["plaintext"])


def append(folder_path: str, name: str, text: str) -> Note:
    """Appends text to a note, creating it first if it doesn't exist.

    Args:
        folder_path: `/`-delimited path to the folder the note is (or
            will be) in.
        name: The note's title.
        text: Text to append. Separated from existing content with a
            newline; becomes the note's entire content if it's newly
            created (research.md §6a).

    Returns:
        The resulting Note (metadata only — use `cat()` to read its
        content back).

    Raises:
        NotFoundError: `folder_path` does not exist.
        AmbiguousMatchError: More than one note already named `name`
            exists in `folder_path`.
        InvalidNameError: `name` is empty, whitespace-only, or multi-line
            (see `validate_note_name`). Checked before anything is written.
    """
    validate_note_name(name)
    result = _run_jxa({"op": "append", "folder_path": folder_path, "name": name, "text": text})
    return Note(**result)
