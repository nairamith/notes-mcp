"""Exception hierarchy raised by src/notes_mcp/apple/core.py."""


class AppleNotesError(Exception):
    """Base class for all errors raised by this module."""


class NotFoundError(AppleNotesError):
    """A referenced note, folder, or parent folder does not exist."""


class AlreadyExistsError(AppleNotesError):
    """A folder with the requested name already exists under the same parent."""


class InvalidPatternError(AppleNotesError):
    """`grep` was given a string that is not a valid regular expression."""


class AutomationPermissionError(AppleNotesError):
    """macOS has not granted Notes automation permission yet."""


class NotImplementedYetError(AppleNotesError):
    """Raised by `rm` when called with `kind="folder"` — not yet implemented."""


class AmbiguousMatchError(AppleNotesError):
    """`append`'s (folder_path, name) matches more than one existing note."""


EXCEPTION_TYPES: dict[str, type[AppleNotesError]] = {
    "NotFoundError": NotFoundError,
    "AlreadyExistsError": AlreadyExistsError,
    "InvalidPatternError": InvalidPatternError,
    "AutomationPermissionError": AutomationPermissionError,
    "AmbiguousMatchError": AmbiguousMatchError,
    "AppleNotesError": AppleNotesError,
}
