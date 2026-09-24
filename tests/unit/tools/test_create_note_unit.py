"""Unit test: create_note with mocked apple.core.append/mkdir (US4)."""

from unittest.mock import MagicMock, call, patch

import pytest

from notes_mcp.apple.core import AlreadyExistsError, AmbiguousMatchError, InvalidNameError, Note
from notes_mcp.tools.create_note import create_note


def test_create_note_swallows_already_exists_when_folder_already_there():
    expected = Note(id="1", name="n", folder_path="F")
    with (
        patch("notes_mcp.tools.create_note.core.append", return_value=expected) as mock_append,
        patch("notes_mcp.tools.create_note.core.mkdir", side_effect=AlreadyExistsError("already there")) as mock_mkdir,
    ):
        result = create_note("F", "n", "content")
    mock_mkdir.assert_called_once_with("", "F")
    mock_append.assert_called_once_with("F", "n", "content")
    assert result is expected


def test_create_note_creates_missing_top_level_folder_then_appends():
    expected = Note(id="1", name="n", folder_path="F")
    with (
        patch("notes_mcp.tools.create_note.core.append", return_value=expected) as mock_append,
        patch("notes_mcp.tools.create_note.core.mkdir") as mock_mkdir,
    ):
        result = create_note("F", "n", "content")
    mock_mkdir.assert_called_once_with("", "F")
    mock_append.assert_called_once_with("F", "n", "content")
    assert result is expected


def test_create_note_ensures_each_intermediate_folder_in_order_before_appending():
    manager = MagicMock()
    expected = Note(id="1", name="n", folder_path="A/B/C")
    with (
        patch("notes_mcp.tools.create_note.core.append", return_value=expected) as mock_append,
        patch("notes_mcp.tools.create_note.core.mkdir") as mock_mkdir,
    ):
        manager.attach_mock(mock_mkdir, "mkdir")
        manager.attach_mock(mock_append, "append")
        create_note("A/B/C", "n", "content")

    assert manager.mock_calls == [
        call.mkdir("", "A"),
        call.mkdir("A", "B"),
        call.mkdir("A/B", "C"),
        call.append("A/B/C", "n", "content"),
    ]


def test_create_note_swallows_already_exists_for_a_partially_existing_path():
    expected = Note(id="1", name="n", folder_path="A/B")
    with (
        patch("notes_mcp.tools.create_note.core.append", return_value=expected) as mock_append,
        patch(
            "notes_mcp.tools.create_note.core.mkdir",
            side_effect=[AlreadyExistsError("already there"), None],
        ) as mock_mkdir,
    ):
        result = create_note("A/B", "n", "content")
    assert mock_mkdir.call_args_list == [call("", "A"), call("A", "B")]
    mock_append.assert_called_once_with("A/B", "n", "content")
    assert result is expected


def test_create_note_propagates_ambiguous_match_error():
    with (
        patch("notes_mcp.tools.create_note.core.mkdir", side_effect=AlreadyExistsError("already there")),
        patch("notes_mcp.tools.create_note.core.append", side_effect=AmbiguousMatchError("dup")),
    ):
        with pytest.raises(AmbiguousMatchError):
            create_note("F", "dup-name", "content")


def test_create_note_rejects_empty_name_before_creating_any_folder():
    with (
        patch("notes_mcp.tools.create_note.core.append") as mock_append,
        patch("notes_mcp.tools.create_note.core.mkdir") as mock_mkdir,
    ):
        with pytest.raises(InvalidNameError):
            create_note("New/Folder", "", "content")
    mock_mkdir.assert_not_called()
    mock_append.assert_not_called()
