"""Contract test: the server advertises list_folders in its tool list (US1)."""

from notes_mcp.server import mcp


async def test_list_folders_is_advertised():
    tools = await mcp.list_tools()
    names = [tool.name for tool in tools]
    assert "list_folders" in names
