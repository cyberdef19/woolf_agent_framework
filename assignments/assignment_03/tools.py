
from langchain_core.tools import tool
from src.woolf_agents.domains.artifacts.schemas.contracts import GetAdjacentChunksInput, RetrieveHistoricalSourcesInput, SearchRelatedSourcesInput, SearchWebHistoricalSourcesInput
from src.woolf_agents.infrastructure.vectorstore.factory import VectorStoreFactory
from src.woolf_agents.infrastructure.vectorstore.basedb import MultiligualE5Embedding
from src.woolf_agents.domains.artifacts.services.services import (
    HistoricalRetrieverService, 
    HistoricalIngestionService,
    HistoricalWebSearchService,
    ingest_all_sources
)
import os

from src.woolf_agents.llm.config import ConfigTavilyAPI


@tool(args_schema=RetrieveHistoricalSourcesInput)
async def retrieve_historical_sources(
    query: str,
    top_k: int = 5,
) -> list:
    """
    Пошук релевантних фрагментів історичних джерел
    у локальній векторній базі.

    Використовуй інструмент, коли для виконання поточного
    кроку потрібні фактичні дані з корпусу історичних джерел.
    """
    embeddings = MultiligualE5Embedding()
    vector_base = VectorStoreFactory.create(provider="chroma",model_embedding=embeddings) 
    retrieval_service = HistoricalRetrieverService(vector_store=vector_base)

    return await retrieval_service.search(
        query=query,
        top_k=top_k,
    )


@tool(args_schema=GetAdjacentChunksInput)
async def get_adjacent_chunks(
    source_id: str,
    chunk_index: int,
    before: int = 1,
    after: int = 1,
) -> list:
    """
    Отримує сусідні фрагменти історичного джерела
    навколо раніше знайденого chunk.

    Використовуй інструмент, коли знайдений фрагмент
    потребує ширшого контексту для правильної
    інтерпретації. 
   
    """

    embeddings = MultiligualE5Embedding()

    vector_base = VectorStoreFactory.create(
        provider="chroma",
        model_embedding=embeddings,
    )

    retrieval_service = HistoricalRetrieverService(
        vector_store=vector_base,
    )

    return await retrieval_service.get_adjacent_chunks(
        source_id=source_id,
        chunk_index=chunk_index,
        before=before,
        after=after,
    )
    

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

@tool(args_schema=SearchRelatedSourcesInput)
async def search_related_sources(
    source_id: str,
    chunk_index: int,
    top_k: int = 5,
) -> list:
    """
    Знаходить семантично пов'язані фрагменти
    в ІНШИХ локальних історичних джерелах.

    Використовуй ТІЛЬКИ після того, як вже отримано
    source_id та chunk_index з попереднього retrieval.

    Цей tool НЕ приймає query.
    Для пошуку за текстовим запитом використовуй
    retrieve_historical_sources.
    """

    embeddings = MultiligualE5Embedding()

    vector_base = VectorStoreFactory.create(
        provider="chroma",
        model_embedding=embeddings,
    )

    retrieval_service = HistoricalRetrieverService(
        vector_store=vector_base
    )

    return await retrieval_service.search_related_sources(
        source_id=source_id,
        chunk_index=chunk_index,
        top_k=top_k,
    )