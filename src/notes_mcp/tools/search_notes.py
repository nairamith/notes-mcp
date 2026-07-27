"""MCP tool wrapping apple.core.grep."""

from notes_mcp.apple import core
from notes_mcp.apple.core import Note


def search_notes(pattern: str, folder_path: str | None = None) -> list[Note]:
    """Searches note content for a regular expression.

    Args:
        pattern: A Python regular expression to search each note's content for.
        folder_path: If given, restricts the search to this folder and its
            subfolders. Searches the entire account when omitted.

    Returns:
        The notes whose content matches `pattern`.

    Raises:
        InvalidPatternError: `pattern` is not a valid regular expression.
        NotFoundError: `folder_path` is given and does not exist.
    """
    return core.grep(pattern, folder_path)
