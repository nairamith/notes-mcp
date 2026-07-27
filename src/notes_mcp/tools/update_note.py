"""MCP tool wrapping apple.core.append; when overwrite=True, also composes
apple.core.ls, apple.core.mkdir, and apple.core.mv to archive any existing
note before creating its replacement (research.md §8).
"""

from notes_mcp.apple import core
from notes_mcp.apple.core import AlreadyExistsError, Note

_ARCHIVE_FOLDER = "archive"


def update_note(folder_path: str, name: str, content: str, overwrite: bool = False) -> Note:
    """Updates a note, by default appending to it (creating it if missing).

    Args:
        folder_path: `/`-delimited path to the folder the note is (or
            will be) in.
        name: The note's title.
        content: Text to append, or (when `overwrite` is true and a
            matching note exists) the replacement note's entire content.
        overwrite: If false (the default), appends `content` to the
            existing note named `name` in `folder_path`, creating it if it
            doesn't exist yet — identical to `create_note`. If true and
            exactly one note named `name` already exists, that note is
            archived (moved, unchanged, into a top-level `archive` folder,
            auto-created on first use) before a replacement note is
            created with `content`; if no such note exists yet, or if more
            than one already does, this flag has no effect and the call
            behaves exactly like the default mode.

    Returns:
        The resulting Note.

    Raises:
        NotFoundError: `folder_path` does not exist.
        AmbiguousMatchError: More than one note already named `name`
            exists in `folder_path` — checked before any change is made,
            regardless of `overwrite`.
    """
    if overwrite:
        listing = core.ls(folder_path)
        matches = [note for note in listing.notes if note.name == name]
        if len(matches) == 1:
            try:
                core.mkdir("", _ARCHIVE_FOLDER)
            except AlreadyExistsError:
                pass
            core.mv(kind="note", identifier=matches[0].id, destination_folder_path=_ARCHIVE_FOLDER)

    return core.append(folder_path, name, content)
