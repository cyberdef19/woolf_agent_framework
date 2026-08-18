from .contracts import VectorStoreProvider
from src.woolf_agents.infrastructure.configdb import configdb
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class MultiligualE5Embedding:
    
    def __init__(self):
        self._model = HuggingFaceEmbeddings(
            model_name=configdb["chromadb"]["embeddings"]["model_e5"],
            model_kwargs=configdb["chromadb"]["model_kwargs"],
            encode_kwargs=configdb["chromadb"]["encode_kwargs"]
        )
    def embed_documents(self, texts: list[str]) -> list[list[float]]:

        passages = [
            f"passage: {text}"
            for text in texts
        ]

        return self._model.embed_documents(
            passages
        )

    def embed_query(self, text: str) -> list[float]:

        return self._model.embed_query(
            f"query: {text}"
        )

class ChromaVectorStoreProvider(VectorStoreProvider):
    
    def __init__(self, embedding_model):
        super().__init__()
        self._vector_store = Chroma(
            collection_name=configdb["chromadb"]["collection_name"],
            persist_directory=configdb["chromadb"]["persist_directory"],
            embedding_function=embedding_model
        )
    
    async def add_documents(self, documents: list[Document], ids:list) -> list[str]:
        """_summary_ Додає документи у векторну базу

        Args:
            documents (list[Document]): _description_ 
            Список документів, що потрібно зберегти в векторній базі
        Returns:
            list[str]: _description_ список 
        """
        return await self._vector_store.aadd_documents(documents=documents, ids=ids)
    
    async def similarity_search(self, query, top_k)->list[Document]:
        """_summary_
           Пошук схожих документів
        Args:
            query (_type_): _description_
            top_k (_type_): _description_

        Returns:
             list[Document]: _description_ список 
        """        
        return await self._vector_store.asimilarity_search(
            query=query,
            k=top_k
        )