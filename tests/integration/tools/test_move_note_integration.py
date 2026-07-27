"""Integration test: move_note against real Notes.app, including the
same-folder edge cases confirmed empirically in research.md §1.

Runs inside a dedicated, disposable `scratch_folder` (see conftest.py) —
never the developer's/user's real personal folders.
"""

import pytest

from notes_mcp.apple.core import NotFoundError, ls
from notes_mcp.tools.move_note import move_note

pytestmark = pytest.mark.usefixtures("skip_without_notes")


def test_move_note_to_a_different_folder(scratch_folder, seed_note, seed_subfolder):
    seed_note(scratch_folder, "movable", "content")
    seed_subfolder(scratch_folder, "destination")
    dest_path = f"{scratch_folder}/destination"

    listing = ls(scratch_folder)
    note_id = next(n.id for n in listing.notes if n.name == "movable")

    moved = move_note(note_id, dest_path)

    assert moved.folder_path == dest_path
    assert "movable" not in [n.name for n in ls(scratch_folder).notes]
    assert "movable" in [n.name for n in ls(dest_path).notes]


def test_move_note_with_rename_in_the_same_call(scratch_folder, seed_note, seed_subfolder):
    seed_note(scratch_folder, "original-name", "content")
    seed_subfolder(scratch_folder, "destination")
    dest_path = f"{scratch_folder}/destination"

    listing = ls(scratch_folder)
    note_id = next(n.id for n in listing.notes if n.name == "original-name")

    moved = move_note(note_id, dest_path, new_name="renamed")

    assert moved.name == "renamed"
    assert moved.folder_path == dest_path
    assert "renamed" in [n.name for n in ls(dest_path).notes]


def test_move_note_to_the_folder_it_is_already_in_is_a_no_op(scratch_folder, seed_note):
    seeded = seed_note(scratch_folder, "already-here", "unchanged content")

    moved = move_note(seeded["id"], scratch_folder)

    assert moved.folder_path == scratch_folder
    assert [n.name for n in ls(scratch_folder).notes].count("already-here") == 1


def test_move_note_to_the_folder_it_is_already_in_with_new_name_renames_in_place(scratch_folder, seed_note):
    seeded = seed_note(scratch_folder, "old-name", "unchanged content")

    moved = move_note(seeded["id"], scratch_folder, new_name="new-name")

    assert moved.name == "new-name"
    assert moved.folder_path == scratch_folder
    names = [n.name for n in ls(scratch_folder).notes]
    assert "new-name" in names
    assert "old-name" not in names


def test_move_note_raises_not_found_for_missing_destination(scratch_folder, seed_note):
    seeded = seed_note(scratch_folder, "n", "c")
    with pytest.raises(NotFoundError):
        move_note(seeded["id"], f"{scratch_folder}/does-not-exist")
