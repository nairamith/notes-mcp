"""Guards that README.md documents install, run, and verify steps (US3, FR-005)."""

from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"


def _text() -> str:
    return README.read_text()


def test_readme_exists():
    assert README.is_file()


def test_readme_documents_install_steps():
    assert "## Install" in _text()


def test_readme_documents_claude_setup_steps():
    text = _text()
    assert "## Adding notes-mcp to Claude" in text
    assert "claude mcp add" in text
    assert "claude_desktop_config.json" in text


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


def test_readme_documents_create_note_append_and_folder_creation():
    line = next(l for l in _text().splitlines() if l.startswith("- `create_note("))
    assert "appended" in line
    assert "creating `folder_path`" in line


def test_readme_documents_move_note_destination_must_exist():
    line = next(l for l in _text().splitlines() if l.startswith("- `move_note("))
    assert "must already exist" in line
