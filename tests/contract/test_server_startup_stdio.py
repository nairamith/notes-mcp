"""End-to-end contract test: spawn the server as a real subprocess over stdio
and drive it with a real MCP client session (US1's actual independent test
criterion — not just in-process FastMCP calls).
"""

import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "notes_mcp.server"],
)


async def test_server_starts_and_advertises_list_folders_over_stdio():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert "list_folders" in [tool.name for tool in tools.tools]


async def test_list_folders_call_over_real_stdio_transport():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_folders", {})
            assert result.structuredContent == {
                "result": [
                    {"id": "1", "name": "Notes"},
                    {"id": "2", "name": "Personal"},
                    {"id": "3", "name": "Work"},
                ]
            }
