"""Unit test: read_note with mocked apple.core.cat (US3)."""

from unittest.mock import patch

import pytest

from notes_mcp.apple.core import NotFoundError
from notes_mcp.tools.read_note import read_note


def test_read_note_returns_cat_result_as_is():
    with patch("notes_mcp.tools.read_note.core.cat", return_value="hello") as mock_cat:
        result = read_note("note-id")
    mock_cat.assert_called_once_with("note-id")
    assert result == "hello"


def test_read_note_propagates_not_found_error():
    with patch("notes_mcp.tools.read_note.core.cat", side_effect=NotFoundError("nope")):
        with pytest.raises(NotFoundError):
            read_note("bad-id")
