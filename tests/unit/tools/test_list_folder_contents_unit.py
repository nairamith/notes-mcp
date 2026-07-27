"""Unit test: list_folder_contents with mocked apple.core.ls (US1)."""

from unittest.mock import patch

import pytest

from notes_mcp.apple.core import FolderListing, NotFoundError
from notes_mcp.tools.list_folder_contents import list_folder_contents


def test_list_folder_contents_returns_ls_result_as_is():
    expected = FolderListing(folders=[], notes=[])
    with patch("notes_mcp.tools.list_folder_contents.core.ls", return_value=expected) as mock_ls:
        result = list_folder_contents("Notes")
    mock_ls.assert_called_once_with("Notes")
    assert result is expected


def test_list_folder_contents_propagates_not_found_error():
    with patch("notes_mcp.tools.list_folder_contents.core.ls", side_effect=NotFoundError("nope")):
        with pytest.raises(NotFoundError):
            list_folder_contents("does/not/exist")
