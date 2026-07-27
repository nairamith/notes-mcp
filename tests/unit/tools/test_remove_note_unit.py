"""Unit test: remove_note composing mocked apple.core.mkdir/mv (US2).

remove_note archives a note directly (mkdir + mv), mirroring
update_note's identical archive-on-replace composition — it does not
call apple.core.rm (which performs Notes.app's own delete/trash
mechanism, a different operation this tool deliberately never exposes).
"""

from unittest.mock import MagicMock, call, patch

import pytest

from notes_mcp.apple.core import AlreadyExistsError, Note, NotFoundError
from notes_mcp.tools.remove_note import remove_note


def test_remove_note_archives_via_mkdir_then_mv_in_order():
    manager = MagicMock()
    expected = Note(id="1", name="n", folder_path="archive")
    with (
        patch("notes_mcp.tools.remove_note.core.mkdir") as mock_mkdir,
        patch("notes_mcp.tools.remove_note.core.mv", return_value=expected) as mock_mv,
    ):
        manager.attach_mock(mock_mkdir, "mkdir")
        manager.attach_mock(mock_mv, "mv")
        result = remove_note("note-id")

    assert manager.mock_calls == [
        call.mkdir("", "archive"),
        call.mv(kind="note", identifier="note-id", destination_folder_path="archive"),
    ]
    assert result is expected


def test_remove_note_swallows_already_exists_error_from_mkdir():
    expected = Note(id="1", name="n", folder_path="archive")
    with (
        patch("notes_mcp.tools.remove_note.core.mkdir", side_effect=AlreadyExistsError("already there")),
        patch("notes_mcp.tools.remove_note.core.mv", return_value=expected) as mock_mv,
    ):
        result = remove_note("note-id")
    mock_mv.assert_called_once_with(kind="note", identifier="note-id", destination_folder_path="archive")
    assert result is expected


def test_remove_note_propagates_not_found_error_from_mv():
    with (
        patch("notes_mcp.tools.remove_note.core.mkdir", side_effect=AlreadyExistsError("already there")),
        patch("notes_mcp.tools.remove_note.core.mv", side_effect=NotFoundError("no such note")),
    ):
        with pytest.raises(NotFoundError):
            remove_note("bad-id")
