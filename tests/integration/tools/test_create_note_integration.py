"""Integration test: create_note auto-creates a missing folder path against
real Notes.app.

Runs inside a dedicated, disposable `scratch_folder` (see conftest.py) —
never the developer's/user's real personal folders.
"""

import pytest

from notes_mcp.apple.core import InvalidNameError, ls
from notes_mcp.tools.create_note import create_note

pytestmark = pytest.mark.usefixtures("skip_without_notes")


def test_create_note_creates_missing_subfolder_then_the_note(scratch_folder):
    target = f"{scratch_folder}/does-not-exist-yet"

    note = create_note(target, "auto-created-note", "content")

    assert note.folder_path == target
    listing = ls(target)
    assert [n.name for n in listing.notes] == ["auto-created-note"]


def test_create_note_with_empty_name_changes_nothing(scratch_folder):
    with pytest.raises(InvalidNameError):
        create_note(f"{scratch_folder}/would-be-created", "", "content")

    listing = ls(scratch_folder)
    assert listing.folders == []
    assert listing.notes == []


def test_create_note_creates_multiple_missing_intermediate_folders(scratch_folder):
    target = f"{scratch_folder}/level-a/level-b"

    note = create_note(target, "deep-note", "content")

    assert note.folder_path == target
    listing = ls(target)
    assert [n.name for n in listing.notes] == ["deep-note"]
