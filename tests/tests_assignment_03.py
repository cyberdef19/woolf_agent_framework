import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock

import pytest
from langchain_core.documents import Document
from src.woolf_agents.domains.artifacts.schemas.contracts import (
    RetrieveHistoricalSourcesInput,
    GetAdjacentChunksInput,
    SearchRelatedSourcesInput,
    SearchWebHistoricalSourcesInput,
)
from src.woolf_agents.domains.artifacts.services.services import HistoricalRetrieverService


def test_retrieve_historical_sources_valid_input():
    schema = RetrieveHistoricalSourcesInput(
        query="Походження назви Хаджибей",
        top_k=5,
    )

    assert schema.query == "Походження назви Хаджибей"
    assert schema.top_k == 5


def test_retrieve_historical_sources_empty_query():
    with pytest.raises(ValidationError):
        RetrieveHistoricalSourcesInput(
            query="   ",
            top_k=5,
        )


def test_retrieve_historical_sources_invalid_top_k():
    with pytest.raises(ValidationError):
        RetrieveHistoricalSourcesInput(
            query="Хаджибей",
            top_k=0,
        )


def test_adjacent_chunks_valid_input():
    schema = GetAdjacentChunksInput(
        source_id="baser_2021",
        chunk_index=5,
        before=2,
        after=2,
    )

    assert schema.source_id == "baser_2021"
    assert schema.chunk_index == 5
    assert schema.before == 2
    assert schema.after == 2


def test_adjacent_chunks_invalid_index():
    with pytest.raises(ValidationError):
        GetAdjacentChunksInput(
            source_id="baser_2021",
            chunk_index=-1,
        )


def test_adjacent_chunks_requires_context():
    with pytest.raises(ValidationError):
        GetAdjacentChunksInput(
            source_id="baser_2021",
            chunk_index=5,
            before=0,
            after=0,
        )


def test_related_sources_empty_source_id():
    with pytest.raises(ValidationError):
        SearchRelatedSourcesInput(
            source_id="   ",
            chunk_index=3,
        )


def test_web_search_valid_input():
    schema = SearchWebHistoricalSourcesInput(
        query="Ottoman Hocabey history",
        max_results=5,
    )

    assert schema.query == "Ottoman Hocabey history"
    assert schema.max_results == 5


def test_web_search_invalid_max_results():
    with pytest.raises(ValidationError):
        SearchWebHistoricalSourcesInput(
            query="Ottoman Hocabey history",
            max_results=11,
        )


from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document


@pytest.mark.asyncio
async def test_get_adjacent_chunks():

    # Arrange
    vector_store = MagicMock()

    vector_store.get.return_value = {
        "documents": [
            "Chunk 6",
            "Chunk 4",
            "Chunk 5",
        ],
        "metadatas": [
            {
                "document_id": "source_1",
                "chunk_index": 6,
            },
            {
                "document_id": "source_1",
                "chunk_index": 4,
            },
            {
                "document_id": "source_1",
                "chunk_index": 5,
            },
        ],
    }

    service = HistoricalRetrieverService(
        vector_store=vector_store
    )

    # Act
    result = await service.get_adjacent_chunks(
        document_id="source_1",
        chunk_index=5,
        before=1,
        after=1,
    )

    # Assert
    assert len(result) == 3

    assert all(
        isinstance(document, Document)
        for document in result
    )

    assert [
        document.metadata["chunk_index"]
        for document in result
    ] == [4, 5, 6]

    assert [
        document.page_content
        for document in result
    ] == [
        "Chunk 4",
        "Chunk 5",
        "Chunk 6",
    ]

    vector_store.get.assert_called_once_with(
        where={
            "$and": [
                {
                    "document_id": {
                        "$eq": "source_1"
                    }
                },
                {
                    "chunk_index": {
                        "$gte": 4
                    }
                },
                {
                    "chunk_index": {
                        "$lte": 6
                    }
                },
            ]
        },
        include=[
            "documents",
            "metadatas",
        ],
    )