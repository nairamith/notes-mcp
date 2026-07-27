"""Contract test: read_note is registered with the right schema (US3)."""

from notes_mcp.server import mcp


async def test_read_note_input_schema_requires_note_id():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "read_note")
    assert tool.inputSchema["required"] == ["note_id"]
    assert tool.inputSchema["properties"]["note_id"]["type"] == "string"


async def test_read_note_output_schema_is_wrapped_string_result():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "read_note")
    assert tool.outputSchema["required"] == ["result"]
    assert tool.outputSchema["properties"]["result"]["type"] == "string"
