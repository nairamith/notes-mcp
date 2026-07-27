"""MCP tool wrapping apple.core.ls."""

from notes_mcp.apple import core
from notes_mcp.apple.core import FolderListing


def list_folder_contents(folder_path: str) -> FolderListing:
    """Lists the immediate notes and subfolders inside a folder.

    Args:
        folder_path: `/`-delimited path to the folder, rooted at a
            top-level folder (e.g. "Personal/Groceries").

    Returns:
        A FolderListing with that folder's direct subfolders and notes
        (not deeper descendants).

    Raises:
        NotFoundError: `folder_path` does not exist.
    """
    return core.ls(folder_path)
