"""Guards that README.md documents install, run, and verify steps (US3, FR-005)."""

from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"


def _text() -> str:
    return README.read_text()


def test_readme_exists():
    assert README.is_file()


def test_readme_documents_install_steps():
    assert "## Install" in _text()


def test_readme_documents_run_steps():
    assert "## Run the server" in _text()


def test_readme_documents_verification_steps():
    assert "## Verify" in _text()


def test_readme_documents_current_tools_not_the_retired_placeholder():
    text = _text()
    for tool in (
        "list_folder_contents",
        "search_notes",
        "read_note",
        "create_note",
        "update_note",
        "move_note",
        "remove_note",
    ):
        assert tool in text
    assert "list_folders" not in text
