import pytest

from src.woolf_agents.core.mcp.servers.historical_mcp_server import HistoricalMCPServer


@pytest.fixture
def mcp():
    server = HistoricalMCPServer(
        name="historical_mcp_test",
        instructions="Historical MCP test server",
    )

    return server.mcp


@pytest.mark.asyncio
async def test_mcp_registers_historical_tools(mcp):
    """MCP server пропонує усі інструменти, що потрібні для дослідження"""

    tools = await mcp.list_tools()

    tool_names = {tool.name for tool in tools}

    expected_tools = {
        "retrieve_historical_sources",
        "get_adjacent_chunks",
        "search_related_sources",
        "search_web_historical_sources",
    }

    assert expected_tools.issubset(tool_names)

@pytest.mark.asyncio
async def test_retrieve_historical_sources_can_be_called(mcp):
    """Зареєстрований інструмент виконується через MCP."""

    result = await mcp.call_tool(
        "retrieve_historical_sources",
        {
            "query": "Хаджибей",
        },
    )

    assert result is not None

@pytest.mark.asyncio
async def test_mcp_rejects_invalid_tool_arguments(mcp):
    

    with pytest.raises(Exception):
        await mcp.call_tool(
            "retrieve_historical_sources",
            {
                "invalid_argument": "attack",
            },
        )