"""Unit test: move_note with mocked apple.core.mv (US1)."""

from unittest.mock import patch

import pytest

from notes_mcp.apple.core import Note, NotFoundError
from notes_mcp.tools.move_note import move_note


def test_move_note_returns_mv_result_as_is():
    expected = Note(id="1", name="n", folder_path="Dest")
    with patch("notes_mcp.tools.move_note.core.mv", return_value=expected) as mock_mv:
        result = move_note("note-id", "Dest")
    mock_mv.assert_called_once_with(kind="note", identifier="note-id", destination_folder_path="Dest", new_name=None)
    assert result is expected


def test_move_note_passes_through_new_name():
    expected = Note(id="1", name="renamed", folder_path="Dest")
    with patch("notes_mcp.tools.move_note.core.mv", return_value=expected) as mock_mv:
        move_note("note-id", "Dest", new_name="renamed")
    mock_mv.assert_called_once_with(kind="note", identifier="note-id", destination_folder_path="Dest", new_name="renamed")


def test_move_note_propagates_not_found_error_for_missing_note():
    with patch("notes_mcp.tools.move_note.core.mv", side_effect=NotFoundError("no such note")):
        with pytest.raises(NotFoundError):
            move_note("bad-id", "Dest")


def test_move_note_propagates_not_found_error_for_missing_destination():
    with patch("notes_mcp.tools.move_note.core.mv", side_effect=NotFoundError("no such folder")):
        with pytest.raises(NotFoundError):
            move_note("note-id", "does/not/exist")
