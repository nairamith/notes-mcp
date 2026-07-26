"""MCP server entrypoint for the Apple Notes MCP scaffold."""

import logging

from mcp.server.fastmcp import FastMCP

from notes_mcp.tools.list_folders import list_folders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

mcp = FastMCP("notes-mcp")
mcp.add_tool(list_folders)


if __name__ == "__main__":
    mcp.run(transport="stdio")
