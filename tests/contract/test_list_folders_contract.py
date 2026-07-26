"""Contract test: list_folders returns the exact stubbed schema/data (US2).

See specs/001-mcp-server-scaffold/contracts/list_folders.md for the
authoritative contract this test enforces.
"""

from notes_mcp.server import mcp

EXPECTED = [
    {"id": "1", "name": "Notes"},
    {"id": "2", "name": "Personal"},
    {"id": "3", "name": "Work"},
]


async def test_list_folders_returns_expected_stub_data():
    _content, structured = await mcp.call_tool("list_folders", {})
    assert structured == {"result": EXPECTED}


async def test_list_folders_is_consistent_across_repeated_calls():
    _content1, first = await mcp.call_tool("list_folders", {})
    _content2, second = await mcp.call_tool("list_folders", {})
    assert first == second == {"result": EXPECTED}


async def test_list_folders_ignores_unexpected_arguments():
    _content, structured = await mcp.call_tool("list_folders", {"unexpected": "arg"})
    assert structured == {"result": EXPECTED}
