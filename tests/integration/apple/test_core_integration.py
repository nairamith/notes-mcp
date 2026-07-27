"""Integration tests for apple/core.py against real Apple Notes.

All tests run inside a dedicated, disposable `scratch_folder` (see
conftest.py) — never the developer's/user's real personal folders.
Automatically skipped when Notes.app isn't scriptable in this environment
(not macOS, or Automation permission not granted).
"""

import pytest

from notes_mcp.apple.core import (
    AlreadyExistsError,
    AmbiguousMatchError,
    NotFoundError,
    NotImplementedYetError,
    append,
    cat,
    grep,
    ls,
    mkdir,
    mv,
    rm,
)

pytestmark = pytest.mark.usefixtures("skip_without_notes")


class TestLsIntegration:
    def test_ls_on_empty_folder_returns_empty(self, scratch_folder):
        listing = ls(scratch_folder)
        assert listing.folders == []
        assert listing.notes == []

    def test_ls_returns_exact_seeded_contents(self, scratch_folder, seed_note, seed_subfolder):
        seed_note(scratch_folder, "a-note", "hello")
        seed_subfolder(scratch_folder, "a-subfolder")

        listing = ls(scratch_folder)

        assert [f.name for f in listing.folders] == ["a-subfolder"]
        assert [n.name for n in listing.notes] == ["a-note"]

    def test_ls_raises_not_found_for_missing_folder(self, scratch_folder):
        with pytest.raises(NotFoundError):
            ls(f"{scratch_folder}/does-not-exist")


class TestGrepIntegration:
    def test_grep_finds_matching_note(self, scratch_folder, seed_note):
        seed_note(scratch_folder, "note-a", "this note is about groceries")
        seed_note(scratch_folder, "note-b", "this note is about work")

        results = grep(r"groc\w+", folder_path=scratch_folder)

        assert [n.name for n in results] == ["note-a"]

    def test_grep_returns_empty_for_no_match(self, scratch_folder, seed_note):
        seed_note(scratch_folder, "note-a", "nothing relevant here")

        assert grep(r"zzz_no_match_zzz", folder_path=scratch_folder) == []


class TestMkdirIntegration:
    def test_mkdir_creates_folder_visible_via_ls(self, scratch_folder):
        created = mkdir(scratch_folder, "new-folder")

        assert created.name == "new-folder"
        assert created.parent_path == scratch_folder
        listing = ls(scratch_folder)
        assert "new-folder" in [f.name for f in listing.folders]

    def test_mkdir_duplicate_name_raises_already_exists(self, scratch_folder):
        mkdir(scratch_folder, "dup")
        with pytest.raises(AlreadyExistsError):
            mkdir(scratch_folder, "dup")

    def test_mkdir_missing_parent_raises_not_found(self, scratch_folder):
        with pytest.raises(NotFoundError):
            mkdir(f"{scratch_folder}/no-such-parent", "x")


class TestMvIntegration:
    def test_mv_note_to_different_folder(self, scratch_folder, seed_note):
        seeded = seed_note(scratch_folder, "movable", "content")
        dest = mkdir(scratch_folder, "destination")

        moved = mv(kind="note", identifier=seeded["id"], destination_folder_path=dest.path)

        assert moved.folder_path == dest.path
        listing = ls(dest.path)
        assert "movable" in [n.name for n in listing.notes]

    def test_mv_note_rename_preserves_content(self, scratch_folder, seed_note):
        seeded = seed_note(scratch_folder, "original-name", "line1")

        renamed = mv(kind="note", identifier=seeded["id"], destination_folder_path=scratch_folder, new_name="renamed")

        assert renamed.name == "renamed"
        assert cat(seeded["id"]) == "line1"

    def test_mv_folder_rename_in_place(self, scratch_folder):
        created = mkdir(scratch_folder, "to-rename")

        renamed = mv(kind="folder", identifier=created.path, destination_folder_path=scratch_folder, new_name="renamed-folder")

        assert renamed.name == "renamed-folder"
        listing = ls(scratch_folder)
        assert "renamed-folder" in [f.name for f in listing.folders]
        assert "to-rename" not in [f.name for f in listing.folders]

    def test_mv_folder_to_different_parent(self, scratch_folder):
        # Verified via mv()'s own return value only, per research.md #10 —
        # a container that has just received a moved folder can become
        # unreadable via ls()/grep() in this Notes.app version, so this
        # test deliberately does not chain further listing calls on the
        # destination afterward.
        dest = mkdir(scratch_folder, "destination")
        source = mkdir(scratch_folder, "source-folder")

        moved = mv(kind="folder", identifier=source.path, destination_folder_path=dest.path)

        assert moved.name == "source-folder"
        assert moved.parent_path == dest.path
        assert moved.path == f"{dest.path}/source-folder"

    def test_mv_note_raises_not_found_for_missing_destination(self, scratch_folder, seed_note):
        seeded = seed_note(scratch_folder, "n", "c")
        with pytest.raises(NotFoundError):
            mv(kind="note", identifier=seeded["id"], destination_folder_path=f"{scratch_folder}/nope")


class TestRmIntegration:
    def test_rm_note_deletes_it_via_notes_own_delete_mechanism(self, scratch_folder, seed_note):
        seeded = seed_note(scratch_folder, "remove-me", "content")

        rm(kind="note", identifier=seeded["id"])

        assert "remove-me" not in [n.name for n in ls(scratch_folder).notes]
        # Verified empirically: Notes.delete() moves the note into Notes.app's
        # own native "Recently Deleted" folder rather than purging it
        # immediately, so it's still resolvable by id via cat() -- unlike a
        # note that was never seeded, or is otherwise genuinely gone.
        assert cat(seeded["id"]) == "content"

    def test_rm_note_raises_not_found_for_missing_note(self):
        with pytest.raises(NotFoundError):
            rm(kind="note", identifier="x-coredata://not-a-real-id/ICNote/p999999")

    def test_rm_folder_still_raises_not_implemented(self, scratch_folder):
        with pytest.raises(NotImplementedYetError):
            rm(kind="folder", identifier=scratch_folder)


class TestCatIntegration:
    def test_cat_returns_exact_content(self, scratch_folder, seed_note):
        seeded = seed_note(scratch_folder, "readable", "the exact content")
        assert cat(seeded["id"]) == "the exact content"

    def test_cat_raises_not_found_for_missing_note(self, scratch_folder):
        with pytest.raises(NotFoundError):
            cat("x-coredata://not-a-real-id/ICNote/p999999")


class TestAppendIntegration:
    def test_append_creates_note_when_missing(self, scratch_folder):
        note = append(scratch_folder, "shopping-list", "milk")

        assert note.name == "shopping-list"
        assert cat(note.id) == "milk"
        listing = ls(scratch_folder)
        assert [n.name for n in listing.notes].count("shopping-list") == 1

    def test_append_preserves_existing_content(self, scratch_folder):
        note = append(scratch_folder, "shopping-list", "milk")
        append(scratch_folder, "shopping-list", "eggs")

        assert cat(note.id) == "milk\neggs"
        listing = ls(scratch_folder)
        assert [n.name for n in listing.notes].count("shopping-list") == 1

    def test_append_raises_ambiguous_match_for_duplicate_names(self, scratch_folder, seed_note):
        seed_note(scratch_folder, "dup-name", "first")
        seed_note(scratch_folder, "dup-name", "second")

        with pytest.raises(AmbiguousMatchError):
            append(scratch_folder, "dup-name", "more text")

    def test_append_raises_not_found_for_missing_folder(self, scratch_folder):
        with pytest.raises(NotFoundError):
            append(f"{scratch_folder}/nope", "name", "text")
