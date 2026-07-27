"""Integration test: remove_note against real Notes.app, including the
already-archived idempotency edge case confirmed empirically in
research.md §2-3.

Runs inside a dedicated, disposable `scratch_folder` (see conftest.py) for
the note's original location. The archived copy necessarily lands in the
single, fixed, top-level "archive" folder (by design, spec Assumptions) —
cleaned up explicitly via delete_note_by_id, never scratch_folder's own
teardown.
"""

import pytest

from notes_mcp.apple.core import ls
from notes_mcp.tools.remove_note import remove_note

pytestmark = pytest.mark.usefixtures("skip_without_notes")


def test_remove_note_archives_it_with_content_unchanged(scratch_folder, seed_note, delete_note_by_id):
    seeded = seed_note(scratch_folder, "to-remove", "unchanged content")

    try:
        result = remove_note(seeded["id"])

        assert result.folder_path == "archive"
        assert "to-remove" not in [n.name for n in ls(scratch_folder).notes]
        assert "to-remove" in [n.name for n in ls("archive").notes]
    finally:
        delete_note_by_id(seeded["id"])


def test_remove_note_on_an_already_archived_note_is_a_safe_no_op(scratch_folder, seed_note, delete_note_by_id):
    seeded = seed_note(scratch_folder, "remove-twice", "unchanged content")

    try:
        first = remove_note(seeded["id"])
        assert first.folder_path == "archive"

        second = remove_note(seeded["id"])

        assert second.folder_path == "archive"
        assert [n.name for n in ls("archive").notes].count("remove-twice") == 1
    finally:
        delete_note_by_id(seeded["id"])
