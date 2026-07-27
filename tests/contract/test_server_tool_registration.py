"""Contract test: the server advertises the full new tool set and no longer
advertises the retired list_folders placeholder.
"""

from notes_mcp.server import mcp

EXPECTED_TOOLS = {
    "list_folder_contents",
    "search_notes",
    "read_note",
    "create_note",
    "update_note",
}


async def test_all_five_tools_are_advertised():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert EXPECTED_TOOLS <= names


async def test_list_folders_is_no_longer_advertised():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert "list_folders" not in names
