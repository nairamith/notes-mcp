"""Contract test: remove_note is registered with the right schema (US2)."""

from notes_mcp.server import mcp


async def test_remove_note_input_schema_requires_note_id():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "remove_note")
    assert tool.inputSchema["required"] == ["note_id"]
    assert tool.inputSchema["properties"]["note_id"]["type"] == "string"


async def test_remove_note_output_schema_is_unwrapped_note():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "remove_note")
    assert set(tool.outputSchema["required"]) == {"id", "name", "folder_path"}
