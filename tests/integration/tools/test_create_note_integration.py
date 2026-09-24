"""Integration test: create_note auto-creates a missing folder path against
real Notes.app.

Runs inside a dedicated, disposable `scratch_folder` (see conftest.py) —
never the developer's/user's real personal folders.
"""

import pytest

from notes_mcp.apple.core import ls
from notes_mcp.tools.create_note import create_note
from notes_mcp.tools.read_note import read_note

pytestmark = pytest.mark.usefixtures("skip_without_notes")


def test_create_note_with_existing_name_appends_to_that_note(scratch_folder):
    first = create_note(scratch_folder, "same-name", "first")

    second = create_note(scratch_folder, "same-name", "second")

    assert second.id == first.id
    assert read_note(first.id) == "first\nsecond"
    assert [n.name for n in ls(scratch_folder).notes] == ["same-name"]


def test_create_note_creates_missing_subfolder_then_the_note(scratch_folder):
    target = f"{scratch_folder}/does-not-exist-yet"

    note = create_note(target, "auto-created-note", "content")

    assert note.folder_path == target
    listing = ls(target)
    assert [n.name for n in listing.notes] == ["auto-created-note"]


def test_create_note_creates_multiple_missing_intermediate_folders(scratch_folder):
    target = f"{scratch_folder}/level-a/level-b"

    note = create_note(target, "deep-note", "content")

    assert note.folder_path == target
    listing = ls(target)
    assert [n.name for n in listing.notes] == ["deep-note"]
