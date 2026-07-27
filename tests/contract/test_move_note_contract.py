"""Contract test: move_note is registered with the right schema (US1)."""

from notes_mcp.server import mcp


async def test_move_note_input_schema_requires_note_id_and_destination():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "move_note")
    assert set(tool.inputSchema["required"]) == {"note_id", "destination_folder_path"}
    assert tool.inputSchema["properties"]["note_id"]["type"] == "string"
    assert tool.inputSchema["properties"]["destination_folder_path"]["type"] == "string"


async def test_move_note_input_schema_has_optional_new_name_defaulting_null():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "move_note")
    assert "new_name" not in tool.inputSchema["required"]
    new_name_schema = tool.inputSchema["properties"]["new_name"]
    assert "default" in new_name_schema
    assert new_name_schema["default"] is None


async def test_move_note_output_schema_is_unwrapped_note():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "move_note")
    assert set(tool.outputSchema["required"]) == {"id", "name", "folder_path"}
