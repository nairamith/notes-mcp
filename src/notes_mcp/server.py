"""MCP server entrypoint for the Apple Notes MCP server."""

import logging

from mcp.server.fastmcp import FastMCP

from notes_mcp.tools.create_note import create_note
from notes_mcp.tools.list_folder_contents import list_folder_contents
from notes_mcp.tools.move_note import move_note
from notes_mcp.tools.read_note import read_note
from notes_mcp.tools.remove_note import remove_note
from notes_mcp.tools.search_notes import search_notes
from notes_mcp.tools.update_note import update_note

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

mcp = FastMCP("notes-mcp")
mcp.add_tool(list_folder_contents)
mcp.add_tool(search_notes)
mcp.add_tool(read_note)
mcp.add_tool(create_note)
mcp.add_tool(update_note)
mcp.add_tool(move_note)
mcp.add_tool(remove_note)


if __name__ == "__main__":
    mcp.run(transport="stdio")
