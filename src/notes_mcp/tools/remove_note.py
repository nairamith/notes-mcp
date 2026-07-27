"""MCP tool wrapping apple.core.rm's note-removal path."""

from notes_mcp.apple import core
from notes_mcp.apple.core import Note


def remove_note(note_id: str) -> Note:
    """Removes a note by archiving it into the well-known `archive` folder.

    Args:
        note_id: Notes' internal id of the note to remove.

    Returns:
        The archived Note (`folder_path` is now `"archive"`).

    Raises:
        NotFoundError: No note with `note_id` exists. Nothing is removed
            in that case.
    """
    return core.rm(kind="note", identifier=note_id)
