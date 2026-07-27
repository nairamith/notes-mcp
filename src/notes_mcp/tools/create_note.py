"""MCP tool wrapping apple.core.append's create-if-missing path.

If `folder_path` doesn't exist yet, create_note creates it (and any
missing intermediate folders) rather than failing, since a caller asking
to create a note in a folder most likely wants that folder to exist.
"""

from notes_mcp.apple import core
from notes_mcp.apple.core import AlreadyExistsError, Note, NotFoundError


def _ensure_folder_exists(folder_path: str) -> None:
    """Creates every folder along `folder_path` that doesn't exist yet.

    Args:
        folder_path: `/`-delimited path to ensure exists, e.g.
            "Personal/Groceries".
    """
    parent = ""
    for part in folder_path.split("/"):
        if not part:
            continue
        try:
            core.mkdir(parent, part)
        except AlreadyExistsError:
            pass
        parent = f"{parent}/{part}" if parent else part


def create_note(folder_path: str, name: str, content: str) -> Note:
    """Creates a new note in a folder, creating the folder first if needed.

    Args:
        folder_path: `/`-delimited path to the folder the note is created
            in. Created automatically (along with any missing intermediate
            folders) if it doesn't exist yet.
        name: The note's title.
        content: The note's initial content.

    Returns:
        The created Note.

    Raises:
        AmbiguousMatchError: A note named `name` already exists more than
            once in `folder_path`.
    """
    try:
        return core.append(folder_path, name, content)
    except NotFoundError:
        _ensure_folder_exists(folder_path)
        return core.append(folder_path, name, content)
