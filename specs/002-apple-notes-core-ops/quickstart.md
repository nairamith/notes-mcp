# Quickstart: Apple Notes Core Backend Operations

Validates User Stories 1-7 end-to-end: `ls`, `grep`, `mkdir`, `mv`, `cat`,
and `append` against real Apple Notes data, and `rm`'s stub behavior.

## Prerequisites

- macOS with Notes.app set up (at least one account/top-level folder)
- Python 3.11+ (same venv as the rest of this repo — no new dependencies)
- **One-time manual step**: the first call will prompt macOS for
  Automation permission for the calling process (e.g. Terminal or your
  Python interpreter) to control Notes.app — accept it via System
  Settings → Privacy & Security → Automation. This cannot be granted
  non-interactively (see research.md §9).

## Setup

```bash
source .venv/bin/activate   # existing project venv; no new deps needed
```

## Run the automated tests

```bash
pytest tests/unit/apple/           # no Notes access needed — always runs
pytest tests/integration/apple/    # real Notes; auto-skips off-macOS or
                                    # without Notes.app/permission
```

Expected: unit tests always pass. Integration tests pass on a macOS
machine with Notes configured and permission granted; they run against a
dedicated scratch folder created and cleaned up by the test suite itself —
never your other personal folders.

## Manually validate the read/write operations (US1-US4)

From a Python shell in this project (`python`, with the venv active):

```python
from notes_mcp.apple.core import ls, grep, mkdir, mv

# US1: list a top-level folder
ls("Notes")

# US3: create a scratch folder to experiment in
mkdir("Notes", "quickstart-scratch")
ls("Notes")  # "quickstart-scratch" now appears

# US2: search for text (adjust the pattern to something you expect to match)
grep(r"grocery|todo", folder_path="Notes")

# US4: rename the scratch folder in place
mv(kind="folder", identifier="Notes/quickstart-scratch",
   destination_folder_path="Notes", new_name="quickstart-scratch-renamed")
ls("Notes")  # renamed folder appears; old name is gone
```

Confirm each result's shape matches [contracts/apple_core_api.md](./contracts/apple_core_api.md)
and [data-model.md](./data-model.md).

## Manually validate read and append (US6-US7)

```python
from notes_mcp.apple.core import cat, append, ls

# US7: append to a note that doesn't exist yet — it gets created
note = append("Notes/quickstart-scratch-renamed", "shopping-list", "milk")
cat(note.id)  # -> "milk"

# US7 again: append to the same note — prior content is preserved
append("Notes/quickstart-scratch-renamed", "shopping-list", "eggs")
cat(note.id)  # -> "milk\neggs"

# US6: list shows exactly one note was created, not duplicated
ls("Notes/quickstart-scratch-renamed")
```

Expected: after the first `append`, `cat` returns exactly `"milk"`; after
the second, it returns `"milk\neggs"` with nothing lost (SC-006); `ls`
shows exactly one `shopping-list` note the whole time (SC-007).

## Manually validate the `rm` stub (US5)

```python
from notes_mcp.apple.core import rm, NotImplementedYetError

try:
    rm(kind="folder", identifier="Notes/quickstart-scratch-renamed")
except NotImplementedYetError:
    print("rm correctly refused to do anything")

ls("Notes")  # the folder is still there — rm did not remove it
```

Expected: `rm` always raises `NotImplementedYetError` and `ls` shows no
change, confirming SC-005.

## Clean up

Manually remove the `quickstart-scratch-renamed` folder from Notes.app
(via the Notes UI) once you're done — `rm` can't do it yet, by design.
