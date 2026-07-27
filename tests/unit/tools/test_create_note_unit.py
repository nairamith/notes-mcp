"""Unit test: create_note with mocked apple.core.append (US4)."""

from unittest.mock import patch

import pytest

from notes_mcp.apple.core import AmbiguousMatchError, Note, NotFoundError
from notes_mcp.tools.create_note import create_note


def test_create_note_returns_append_result_as_is():
    expected = Note(id="1", name="n", folder_path="F")
    with patch("notes_mcp.tools.create_note.core.append", return_value=expected) as mock_append:
        result = create_note("F", "n", "content")
    mock_append.assert_called_once_with("F", "n", "content")
    assert result is expected


def test_create_note_propagates_not_found_error():
    with patch("notes_mcp.tools.create_note.core.append", side_effect=NotFoundError("nope")):
        with pytest.raises(NotFoundError):
            create_note("does/not/exist", "n", "content")


def test_create_note_propagates_ambiguous_match_error():
    with patch("notes_mcp.tools.create_note.core.append", side_effect=AmbiguousMatchError("dup")):
        with pytest.raises(AmbiguousMatchError):
            create_note("F", "dup-name", "content")
