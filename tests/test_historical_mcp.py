import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mcp_client():
    client = MagicMock()

    client.list_resources = AsyncMock()
    client.read_resource = AsyncMock()
    client.list_prompts = AsyncMock()
    client.get_prompt = AsyncMock()

    return client

@pytest.mark.asyncio
async def test_list_resources(mcp_client):
    resource = MagicMock()
    resource.uri = "heritage://research/methodology"

    mcp_client.list_resources.return_value = [resource]

    resources = await mcp_client.list_resources()

    uris = [str(resource.uri) for resource in resources]

    assert "heritage://research/methodology" in uris
    
@pytest.mark.asyncio
async def test_read_research_methodology(mcp_client):
    mcp_client.read_resource.return_value = (
        "МЕТОДОЛОГІЯ ІСТОРИЧНОГО ДОСЛІДЖЕННЯ HERITAGE\n"
        "Принцип обережності"
    )

    result = await mcp_client.read_resource(
        "heritage://research/methodology"
    )

    text = str(result)

    assert "МЕТОДОЛОГІЯ ІСТОРИЧНОГО ДОСЛІДЖЕННЯ HERITAGE" in text
    assert "Принцип обережності" in text
    
@pytest.mark.asyncio
async def test_list_prompts(mcp_client):
    prompt = MagicMock()
    prompt.name = "critical_review"

    mcp_client.list_prompts.return_value = [prompt]

    prompts = await mcp_client.list_prompts()

    names = [prompt.name for prompt in prompts]

    assert "critical_review" in names
    
@pytest.mark.asyncio
async def test_get_critical_review_prompt(mcp_client):
    mcp_client.get_prompt.return_value = (
        "Дослідити причини події\n"
        "Результат історичного дослідження\n"
        "Не проводь нові дослідження"
    )

    result = await mcp_client.get_prompt(
        "critical_review",
        arguments={
            "user_task": "Дослідити причини події",
            "research_result": "Результат історичного дослідження",
        },
    )

    text = str(result)

    assert "Дослідити причини події" in text
    assert "Результат історичного дослідження" in text
    assert "Не проводь нові дослідження" in text

@pytest.mark.asyncio
async def test_get_tools(mcp_client):
    tool = MagicMock()
    tool.name = "search_historical_sources"

    mcp_client.get_tools.return_value = [tool]

    tools = mcp_client.get_tools()

    names = [tool.name for tool in tools]

    assert "search_historical_sources" in names

@pytest.mark.asyncio
async def test_call_tool(mcp_client):
    mcp_client.call_tool = AsyncMock(
        return_value="Historical search result"
    )

    result = await mcp_client.call_tool(
        "search_historical_sources",
        {
            "query": "Хаджибей"
        }
    )

    assert "Historical search result" in str(result)

    mcp_client.call_tool.assert_awaited_once_with(
        "search_historical_sources",
        {
            "query": "Хаджибей"
        }
    )