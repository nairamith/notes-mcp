"""Contract test: list_folder_contents is registered with the right schema (US1)."""

from notes_mcp.server import mcp


async def test_list_folder_contents_is_advertised_with_expected_input_schema():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "list_folder_contents")
    assert tool.inputSchema["required"] == ["folder_path"]
    assert tool.inputSchema["properties"]["folder_path"]["type"] == "string"


async def test_list_folder_contents_output_is_unwrapped_folder_listing():
    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "list_folder_contents")
    assert set(tool.outputSchema["required"]) == {"folders", "notes"}
