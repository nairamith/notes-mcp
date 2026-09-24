"""Integration test: create_note auto-creates a missing folder path against
real Notes.app.

Runs inside a dedicated, disposable `scratch_folder` (see conftest.py) —
never the developer's/user's real personal folders.
"""

import pytest

from notes_mcp.apple.core import InvalidNameError, ls
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


def test_create_note_in_new_subfolder_that_sorts_before_its_parent(late_sorting_scratch_folder):
    # A new folder named to sort before its top-level parent shifts that
    # parent's position in the account's flattened folder list; lookups
    # must not depend on that position (issue #6).
    target = f"{late_sorting_scratch_folder}/aa-child"

    note = create_note(target, "sorted-before-parent", "content")

    assert note.folder_path == target
    listing = ls(target)
    assert [n.name for n in listing.notes] == ["sorted-before-parent"]
