"""MCP tool that archives a note into the well-known `archive` folder.

Composes apple.core.mkdir and apple.core.mv directly, mirroring
update_note.py's identical archive-on-replace composition, rather than
calling apple.core.rm — that function performs Notes.app's own delete
(into its native "Recently Deleted" folder), a different operation this
tool deliberately never exposes. "Removing" a note over MCP always means
archiving it into a location this project controls, never Notes' own
trash.
"""

from notes_mcp.apple import core
from notes_mcp.apple.core import AlreadyExistsError, Note

_ARCHIVE_FOLDER = "archive"


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
    try:
        core.mkdir("", _ARCHIVE_FOLDER)
    except AlreadyExistsError:
        pass
    return core.mv(kind="note", identifier=note_id, destination_folder_path=_ARCHIVE_FOLDER)
