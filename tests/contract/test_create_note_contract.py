"""Contract test: create_note is registered with the right schema (US4)."""

from notes_mcp.server import mcp


async def test_create_note_input_schema_requires_folder_path_name_content():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "create_note")
    assert set(tool.inputSchema["required"]) == {"folder_path", "name", "content"}
    for field in ("folder_path", "name", "content"):
        assert tool.inputSchema["properties"][field]["type"] == "string"


async def test_create_note_output_schema_is_unwrapped_note():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "create_note")
    assert set(tool.outputSchema["required"]) == {"id", "name", "folder_path"}
