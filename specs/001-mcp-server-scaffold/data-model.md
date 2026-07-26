# Data Model: MCP Server Scaffold with Dummy list_folders Tool

## Folder (stub)

A placeholder representation of an Apple Notes folder, returned by the
`list_folders` tool. Not backed by real Notes data at this stage (see spec
Assumptions); the shape is chosen so later, real tools can reference a
folder by `id` without a breaking schema change (per Clarifications
session 2026-07-26 and constitution Principle III, MCP Contract Integrity).

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Stable identifier, distinct from `name`. Unique within a single `list_folders` response. |
| `name` | string | yes | Display name of the folder. Not guaranteed unique (real Notes folders can theoretically share a display name; `id` is the identity). |

**Validation rules**:
- Both fields are required, non-empty strings.
- `id` MUST be unique across all folder entries in a single response.

**Lifecycle / state transitions**: None. This is a static, read-only stub
dataset for this feature — no create/update/delete operations exist yet.

**Stub dataset** (fixed, in-memory, returned verbatim by `list_folders`):

```json
[
  {"id": "1", "name": "Notes"},
  {"id": "2", "name": "Personal"},
  {"id": "3", "name": "Work"}
]
```
