"""Contract test: update_note is registered with the right schema (US5)."""

from notes_mcp.server import mcp


async def test_update_note_input_schema_requires_folder_path_name_content():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "update_note")
    assert set(tool.inputSchema["required"]) == {"folder_path", "name", "content"}
    for field in ("folder_path", "name", "content"):
        assert tool.inputSchema["properties"][field]["type"] == "string"


async def test_update_note_input_schema_has_optional_overwrite_boolean_defaulting_false():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "update_note")
    overwrite_schema = tool.inputSchema["properties"]["overwrite"]
    assert overwrite_schema["type"] == "boolean"
    assert overwrite_schema["default"] is False
    assert "overwrite" not in tool.inputSchema["required"]


async def test_update_note_output_schema_is_unwrapped_note():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "update_note")
    assert set(tool.outputSchema["required"]) == {"id", "name", "folder_path"}
