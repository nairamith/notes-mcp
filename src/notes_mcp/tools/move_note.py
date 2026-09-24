"""MCP tool wrapping apple.core.mv's note-moving path."""

from notes_mcp.apple import core
from notes_mcp.apple.core import Note


def move_note(note_id: str, destination_folder_path: str, new_name: str | None = None) -> Note:
    """Moves a note to a different folder, optionally renaming it.

    Args:
        note_id: Notes' internal id of the note to move.
        destination_folder_path: `/`-delimited path to the folder to
            move the note into.
        new_name: If given, renames the note in the same call.

    Returns:
        The moved (and possibly renamed) Note.

    Raises:
        NotFoundError: `note_id` or `destination_folder_path` does not
            exist. Nothing is moved in that case.
        InvalidNameError: `new_name` is given but empty, whitespace-only,
            or multi-line. Nothing is moved in that case.
    """
    return core.mv(kind="note", identifier=note_id, destination_folder_path=destination_folder_path, new_name=new_name)
