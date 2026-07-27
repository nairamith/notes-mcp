"""Data shapes returned by src/notes_mcp/apple/core.py."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    id: str
    name: str
    folder_path: str


@dataclass(frozen=True)
class Folder:
    name: str
    path: str
    parent_path: str | None


@dataclass(frozen=True)
class FolderListing:
    folders: list[Folder]
    notes: list[Note]
