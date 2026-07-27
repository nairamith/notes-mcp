"""MCP tool wrapping apple.core.append's create-if-missing path."""

from notes_mcp.apple import core
from notes_mcp.apple.core import Note


def create_note(folder_path: str, name: str, content: str) -> Note:
    """Creates a new note in a folder.

    Args:
        folder_path: `/`-delimited path to the folder the note is created in.
        name: The note's title.
        content: The note's initial content.

    Returns:
        The created Note.

    Raises:
        NotFoundError: `folder_path` does not exist.
        AmbiguousMatchError: A note named `name` already exists more than
            once in `folder_path`.
    """
    return core.append(folder_path, name, content)
