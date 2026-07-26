"""Stub list_folders tool: returns fixed placeholder folders, no real Notes access."""

import logging
import time

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Folder(BaseModel):
    id: str
    name: str


_STUB_FOLDERS = [
    Folder(id="1", name="Notes"),
    Folder(id="2", name="Personal"),
    Folder(id="3", name="Work"),
]


def list_folders() -> list[Folder]:
    """Return the fixed, stubbed list of Apple Notes folders."""
    start = time.monotonic()
    try:
        result = list(_STUB_FOLDERS)
    except Exception:
        duration_ms = (time.monotonic() - start) * 1000
        logger.exception("tool=list_folders outcome=error duration_ms=%.2f", duration_ms)
        raise
    duration_ms = (time.monotonic() - start) * 1000
    logger.info("tool=list_folders outcome=success duration_ms=%.2f", duration_ms)
    return result
