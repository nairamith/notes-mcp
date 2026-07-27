"""Unit tests for apple/core.py that need no real Notes access.

Covers: _run_jxa's error classification (mocked subprocess), input
validation that happens before any Notes call (grep's regex, mv's
not-found via mocked responses), and rm's stub behavior.
"""

import json
import subprocess
from unittest.mock import patch

import pytest

from notes_mcp.apple import core
from notes_mcp.apple.core import (
    AmbiguousMatchError,
    AutomationPermissionError,
    InvalidPatternError,
    NotFoundError,
    NotImplementedYetError,
    cat,
    grep,
    mv,
    rm,
)


def _fake_proc(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestRunJxaClassification:
    def test_successful_json_response(self):
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=json.dumps({"ok": True, "result": {"x": 1}}))):
            assert core._run_jxa({"op": "ls", "folder_path": "x"}) == {"x": 1}

    def test_permission_denied_raises_automation_permission_error(self):
        with patch.object(
            core.subprocess,
            "run",
            return_value=_fake_proc(returncode=1, stderr="execution error: Not authorised (-1743)"),
        ):
            with pytest.raises(AutomationPermissionError):
                core._run_jxa({"op": "ls", "folder_path": "x"})

    def test_generic_osascript_failure_raises_apple_notes_error(self):
        with patch.object(core.subprocess, "run", return_value=_fake_proc(returncode=1, stderr="some other failure")):
            with pytest.raises(core.AppleNotesError):
                core._run_jxa({"op": "ls", "folder_path": "x"})

    def test_error_type_from_payload_maps_to_correct_exception(self):
        payload = json.dumps({"ok": False, "error_type": "NotFoundError", "message": "nope"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(NotFoundError, match="nope"):
                core._run_jxa({"op": "ls", "folder_path": "x"})

    def test_unknown_error_type_falls_back_to_base_exception(self):
        payload = json.dumps({"ok": False, "error_type": "SomethingWeNeverDefined", "message": "?"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(core.AppleNotesError):
                core._run_jxa({"op": "ls", "folder_path": "x"})


class TestLsUnit:
    def test_ls_raises_not_found_for_missing_folder(self):
        payload = json.dumps({"ok": False, "error_type": "NotFoundError", "message": 'No folder named "x"'})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(NotFoundError):
                core.ls("does/not/exist")


class TestGrepUnit:
    def test_invalid_pattern_raises_without_calling_notes(self):
        with patch.object(core.subprocess, "run") as mock_run:
            with pytest.raises(InvalidPatternError):
                grep("(unclosed")
            mock_run.assert_not_called()

    def test_valid_pattern_filters_results_in_python(self):
        payload = json.dumps(
            {
                "ok": True,
                "result": {
                    "notes": [
                        {"id": "1", "name": "a", "folder_path": "F", "plaintext": "contains milk"},
                        {"id": "2", "name": "b", "folder_path": "F", "plaintext": "contains eggs"},
                    ]
                },
            }
        )
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            results = grep(r"mil.")
        assert [n.id for n in results] == ["1"]


class TestMvUnit:
    def test_mv_note_raises_not_found_for_missing_note(self):
        payload = json.dumps({"ok": False, "error_type": "NotFoundError", "message": "no such note"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(NotFoundError):
                mv(kind="note", identifier="bad-id", destination_folder_path="Somewhere")

    def test_mv_folder_raises_not_found_for_missing_source(self):
        payload = json.dumps({"ok": False, "error_type": "NotFoundError", "message": "no such folder"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(NotFoundError):
                mv(kind="folder", identifier="does/not/exist", destination_folder_path="Somewhere")


class TestAppendUnit:
    def test_append_raises_ambiguous_match_error(self):
        payload = json.dumps({"ok": False, "error_type": "AmbiguousMatchError", "message": "more than one match"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(AmbiguousMatchError):
                core.append("Folder", "dup-name", "text")

    def test_append_raises_not_found_for_missing_folder(self):
        payload = json.dumps({"ok": False, "error_type": "NotFoundError", "message": "no such folder"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(NotFoundError):
                core.append("does/not/exist", "name", "text")


class TestCatUnit:
    def test_cat_raises_not_found_for_missing_note(self):
        payload = json.dumps({"ok": False, "error_type": "NotFoundError", "message": "no such note"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=payload)):
            with pytest.raises(NotFoundError):
                cat("bad-id")

    def test_plaintext_to_content_strips_title_line(self):
        assert core._plaintext_to_content("Title\nline1\nline2\n") == "line1\nline2"

    def test_plaintext_to_content_title_only_note_has_empty_content(self):
        assert core._plaintext_to_content("TitleOnly\n") == ""


class TestRmFolderStub:
    def test_rm_folder_always_raises_not_implemented(self):
        with pytest.raises(NotImplementedYetError):
            rm(kind="folder", identifier="anything")

    def test_rm_folder_never_calls_osascript(self):
        with patch.object(core.subprocess, "run") as mock_run:
            with pytest.raises(NotImplementedYetError):
                rm(kind="folder", identifier="anything")
            mock_run.assert_not_called()


class TestRmNote:
    def test_rm_note_invokes_the_rm_note_op_with_the_identifier(self):
        response = json.dumps({"ok": True, "result": None})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=response)) as mock_run:
            rm(kind="note", identifier="note-1")
        argv = mock_run.call_args.args[0]
        assert json.loads(argv[-1]) == {"op": "rm_note", "identifier": "note-1"}

    def test_rm_note_raises_not_found_error(self):
        response = json.dumps({"ok": False, "error_type": "NotFoundError", "message": "no such note"})
        with patch.object(core.subprocess, "run", return_value=_fake_proc(stdout=response)):
            with pytest.raises(NotFoundError):
                rm(kind="note", identifier="bad-id")
