# Tool Contract: `list_folders`

**Transport**: MCP over stdio

**Type**: MCP tool (invoked by name via the standard MCP `tools/call` request)

## Input Schema

No parameters. Callers SHOULD invoke with an empty input object (`{}`).

```json
{
  "type": "object",
  "properties": {}
}
```

Note: this schema does not set `additionalProperties: false` (the `FastMCP`
default for a zero-argument tool). Extra/unexpected input properties are
therefore accepted and silently ignored by the current implementation rather
than rejected — the tool always returns its fixed stub output regardless of
input. This resolves the spec's edge case "how does the system respond to
unexpected arguments."

## Output Schema

MCP structured tool output must be a JSON object at the top level, so an
array-typed result (a list of Folder objects, see
[data-model.md](../data-model.md)) is wrapped under a `result` key — this is
the official MCP Python SDK's (`FastMCP`) standard convention for any tool
whose Python return type is a list, not a scaffold-specific choice:

```json
{
  "type": "object",
  "properties": {
    "result": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" }
        },
        "required": ["id", "name"]
      }
    }
  },
  "required": ["result"]
}
```

The same data is also echoed as unstructured `TextContent` blocks (one JSON
object per folder) alongside the structured result, per standard `FastMCP`
behavior — clients may read either the structured `result` array or the
content blocks.

## Example

**Request**: `list_folders` called with `{}`

**Response** (structured content):

```json
{
  "result": [
    {"id": "1", "name": "Notes"},
    {"id": "2", "name": "Personal"},
    {"id": "3", "name": "Work"}
  ]
}
```

## Contract Guarantees (this feature)

- The response is fixed/stubbed: every call with no input returns the exact
  same three entries above (FR-003, FR-004).
- The call has no side effects and does not read real Apple Notes data.
- Unexpected/extra input arguments are accepted and ignored (see Input
  Schema note above) rather than causing an error — behavior is still
  predictable (always the same stub output) per Principle III (MCP Contract
  Integrity), even though invalid input isn't rejected outright.
- Any future change to this output shape (e.g., adding real data, changing
  field names) is a breaking contract change and requires a version note per
  the constitution's MCP Contract Integrity principle.
