"""MCP tool wrapping apple.core.cat."""

from notes_mcp.apple import core


def read_note(note_id: str) -> str:
    """Returns a note's content.

    Args:
        note_id: Notes' internal id of the note to read.

    Returns:
        The note's content.

    Raises:
        NotFoundError: No note with `note_id` exists.
    """
    return core.cat(note_id)
