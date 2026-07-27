"""Unit test: update_note's default (append) and overwrite (archive-then-
create) modes, with apple.core.ls/mkdir/mv/append mocked (US5).
"""

from unittest.mock import MagicMock, call, patch

import pytest

from notes_mcp.apple.core import (
    AlreadyExistsError,
    AmbiguousMatchError,
    FolderListing,
    Note,
    NotFoundError,
)
from notes_mcp.tools.update_note import update_note


def _listing(*names: str) -> FolderListing:
    return FolderListing(
        folders=[],
        notes=[Note(id=f"id-{n}", name=n, folder_path="F") for n in names],
    )


class TestDefaultMode:
    def test_default_mode_only_calls_append(self):
        expected = Note(id="1", name="n", folder_path="F")
        with (
            patch("notes_mcp.tools.update_note.core.append", return_value=expected) as mock_append,
            patch("notes_mcp.tools.update_note.core.ls") as mock_ls,
            patch("notes_mcp.tools.update_note.core.mkdir") as mock_mkdir,
            patch("notes_mcp.tools.update_note.core.mv") as mock_mv,
        ):
            result = update_note("F", "n", "content")
        mock_append.assert_called_once_with("F", "n", "content")
        mock_ls.assert_not_called()
        mock_mkdir.assert_not_called()
        mock_mv.assert_not_called()
        assert result is expected

    def test_default_mode_propagates_not_found_error(self):
        with patch("notes_mcp.tools.update_note.core.append", side_effect=NotFoundError("nope")):
            with pytest.raises(NotFoundError):
                update_note("does/not/exist", "n", "content")

    def test_default_mode_propagates_ambiguous_match_error(self):
        with patch("notes_mcp.tools.update_note.core.append", side_effect=AmbiguousMatchError("dup")):
            with pytest.raises(AmbiguousMatchError):
                update_note("F", "dup-name", "content")


class TestOverwriteModeZeroMatches:
    def test_zero_matches_skips_archive_and_only_appends(self):
        expected = Note(id="1", name="n", folder_path="F")
        with (
            patch("notes_mcp.tools.update_note.core.ls", return_value=_listing()) as mock_ls,
            patch("notes_mcp.tools.update_note.core.mkdir") as mock_mkdir,
            patch("notes_mcp.tools.update_note.core.mv") as mock_mv,
            patch("notes_mcp.tools.update_note.core.append", return_value=expected) as mock_append,
        ):
            result = update_note("F", "n", "content", overwrite=True)
        mock_ls.assert_called_once_with("F")
        mock_mkdir.assert_not_called()
        mock_mv.assert_not_called()
        mock_append.assert_called_once_with("F", "n", "content")
        assert result is expected


class TestOverwriteModeOneMatch:
    def test_one_match_archives_then_creates_in_order(self):
        manager = MagicMock()
        with (
            patch("notes_mcp.tools.update_note.core.ls", return_value=_listing("n")),
            patch("notes_mcp.tools.update_note.core.mkdir") as mock_mkdir,
            patch("notes_mcp.tools.update_note.core.mv") as mock_mv,
            patch(
                "notes_mcp.tools.update_note.core.append",
                return_value=Note(id="new", name="n", folder_path="F"),
            ) as mock_append,
        ):
            manager.attach_mock(mock_mkdir, "mkdir")
            manager.attach_mock(mock_mv, "mv")
            manager.attach_mock(mock_append, "append")
            update_note("F", "n", "content", overwrite=True)

        mock_mkdir.assert_called_once_with("", "archive")
        mock_mv.assert_called_once_with(kind="note", identifier="id-n", destination_folder_path="archive")
        mock_append.assert_called_once_with("F", "n", "content")
        assert manager.mock_calls == [
            call.mkdir("", "archive"),
            call.mv(kind="note", identifier="id-n", destination_folder_path="archive"),
            call.append("F", "n", "content"),
        ]

    def test_mkdir_already_exists_error_is_swallowed(self):
        with (
            patch("notes_mcp.tools.update_note.core.ls", return_value=_listing("n")),
            patch("notes_mcp.tools.update_note.core.mkdir", side_effect=AlreadyExistsError("already there")),
            patch("notes_mcp.tools.update_note.core.mv") as mock_mv,
            patch(
                "notes_mcp.tools.update_note.core.append",
                return_value=Note(id="new", name="n", folder_path="F"),
            ) as mock_append,
        ):
            update_note("F", "n", "content", overwrite=True)
        mock_mv.assert_called_once()
        mock_append.assert_called_once()

    def test_mv_failure_prevents_append(self):
        with (
            patch("notes_mcp.tools.update_note.core.ls", return_value=_listing("n")),
            patch("notes_mcp.tools.update_note.core.mkdir"),
            patch("notes_mcp.tools.update_note.core.mv", side_effect=NotFoundError("gone")),
            patch("notes_mcp.tools.update_note.core.append") as mock_append,
        ):
            with pytest.raises(NotFoundError):
                update_note("F", "n", "content", overwrite=True)
        mock_append.assert_not_called()


class TestOverwriteModeAmbiguousMatches:
    def test_more_than_one_match_skips_archive_and_lets_append_raise(self):
        with (
            patch("notes_mcp.tools.update_note.core.ls", return_value=_listing("n", "n")),
            patch("notes_mcp.tools.update_note.core.mkdir") as mock_mkdir,
            patch("notes_mcp.tools.update_note.core.mv") as mock_mv,
            patch(
                "notes_mcp.tools.update_note.core.append",
                side_effect=AmbiguousMatchError("more than one match"),
            ) as mock_append,
        ):
            with pytest.raises(AmbiguousMatchError):
                update_note("F", "n", "content", overwrite=True)
        mock_mkdir.assert_not_called()
        mock_mv.assert_not_called()
        mock_append.assert_called_once_with("F", "n", "content")
