from langchain_core.tools import tool
from src.woolf_agents.domains.artifacts.schemas.contracts import SearchWebHistoricalSourcesInput
from src.woolf_agents.domains.artifacts.services.services import HistoricalWebSearchService
from src.woolf_agents.llm.config import ConfigTavilyAPI


@tool(args_schema=SearchWebHistoricalSourcesInput)
async def search_web_historical_sources(
    query: str,
    max_results: int = 5,
) -> list:
    """
    Пошук історичних джерел та додаткової інформації у веб.

    Використовуй інструмент, якщо інформації з локальної
    бази історичних джерел недостатньо або потрібно
    перевірити додаткові зовнішні джерела.
    
     Даний інструмент є допоміжним, якщо інші інструменти 
     не надають достатнього результату.
    """

    service = HistoricalWebSearchService(
        api_key=ConfigTavilyAPI.TAVILYKEY
    )

    return await service.search(
        query=query,
        max_results=max_results,
    )
