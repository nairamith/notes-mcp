"""Contract test: search_notes is registered with the right schema (US2)."""

from notes_mcp.server import mcp


async def test_search_notes_input_schema_has_required_pattern_and_optional_folder_path():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "search_notes")
    assert tool.inputSchema["required"] == ["pattern"]
    assert tool.inputSchema["properties"]["pattern"]["type"] == "string"
    assert "folder_path" in tool.inputSchema["properties"]


async def test_search_notes_output_schema_is_wrapped_result_array():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "search_notes")
    assert tool.outputSchema["required"] == ["result"]
    assert tool.outputSchema["properties"]["result"]["type"] == "array"
