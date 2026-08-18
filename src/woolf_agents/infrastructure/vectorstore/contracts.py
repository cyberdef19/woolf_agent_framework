from abc import ABC, abstractmethod
from langchain_core.documents import Document

class VectorStoreProvider(ABC):
    
    @abstractmethod
    async def add_documents(self, documents: list[Document], ids:list) -> list[str]:
        ...
    @abstractmethod
    async def similarity_search(self, query: str, top_k: int) -> list[Document]:
        ...