"""Unit tests on the list_folders stub dataset itself (US2)."""

from notes_mcp.tools.list_folders import list_folders


def test_stub_folders_have_required_non_empty_fields():
    folders = list_folders()
    assert len(folders) > 0
    for folder in folders:
        assert folder.id
        assert folder.name


def test_stub_folder_ids_are_unique():
    folders = list_folders()
    ids = [folder.id for folder in folders]
    assert len(ids) == len(set(ids))


def test_list_folders_has_no_side_effects_across_calls():
    first = list_folders()
    second = list_folders()
    assert first == second
