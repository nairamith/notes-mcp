"""Unit test: remove_note with mocked apple.core.rm (US2)."""

from unittest.mock import patch

import pytest

from notes_mcp.apple.core import Note, NotFoundError
from notes_mcp.tools.remove_note import remove_note


def test_remove_note_returns_rm_result_as_is():
    expected = Note(id="1", name="n", folder_path="archive")
    with patch("notes_mcp.tools.remove_note.core.rm", return_value=expected) as mock_rm:
        result = remove_note("note-id")
    mock_rm.assert_called_once_with(kind="note", identifier="note-id")
    assert result is expected


def test_remove_note_propagates_not_found_error():
    with patch("notes_mcp.tools.remove_note.core.rm", side_effect=NotFoundError("no such note")):
        with pytest.raises(NotFoundError):
            remove_note("bad-id")
