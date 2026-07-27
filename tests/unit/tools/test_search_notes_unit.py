"""Unit test: search_notes with mocked apple.core.grep (US2)."""

from unittest.mock import patch

import pytest

from notes_mcp.apple.core import InvalidPatternError, Note, NotFoundError
from notes_mcp.tools.search_notes import search_notes


def test_search_notes_returns_grep_result_as_is():
    expected = [Note(id="1", name="n", folder_path="F")]
    with patch("notes_mcp.tools.search_notes.core.grep", return_value=expected) as mock_grep:
        result = search_notes("pattern", "F")
    mock_grep.assert_called_once_with("pattern", "F")
    assert result is expected


def test_search_notes_defaults_folder_path_to_none():
    with patch("notes_mcp.tools.search_notes.core.grep", return_value=[]) as mock_grep:
        search_notes("pattern")
    mock_grep.assert_called_once_with("pattern", None)


def test_search_notes_propagates_invalid_pattern_error():
    with patch("notes_mcp.tools.search_notes.core.grep", side_effect=InvalidPatternError("bad")):
        with pytest.raises(InvalidPatternError):
            search_notes("(unclosed")


def test_search_notes_propagates_not_found_error():
    with patch("notes_mcp.tools.search_notes.core.grep", side_effect=NotFoundError("nope")):
        with pytest.raises(NotFoundError):
            search_notes("pattern", "does/not/exist")
