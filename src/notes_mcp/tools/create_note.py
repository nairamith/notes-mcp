"""MCP tool wrapping apple.core.append's create-if-missing path.

If `folder_path` doesn't exist yet, create_note creates it (and any
missing intermediate folders) rather than failing, since a caller asking
to create a note in a folder most likely wants that folder to exist.
"""

from notes_mcp.apple import core
from notes_mcp.apple.core import AlreadyExistsError, Note


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

    If a note named `name` already exists in `folder_path`, no new note
    is created: `content` is appended to that note instead, exactly as
    `update_note` does by default, and that note is returned.

    Args:
        folder_path: `/`-delimited path to the folder the note is created
            in. Ensured to exist (creating it, and any missing
            intermediate folders, first) before the note is created.
        name: The note's title.
        content: The note's initial content.

    Returns:
        The created Note — or, if one named `name` already existed, that
        existing Note (same id).

    Raises:
        AmbiguousMatchError: A note named `name` already exists more than
            once in `folder_path`.
    """
    _ensure_folder_exists(folder_path)
    return core.append(folder_path, name, content)
