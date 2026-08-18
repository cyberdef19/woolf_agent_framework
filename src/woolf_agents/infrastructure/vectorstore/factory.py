from .contracts import VectorStoreProvider
from .basedb import ChromaVectorStoreProvider

class VectorStoreFactory:

    @staticmethod
    def create(
        provider: str,
        model_embedding,
    ) -> VectorStoreProvider:

        match provider:
            case "chroma":
                return ChromaVectorStoreProvider(embedding_model=model_embedding)

            case _:
                raise ValueError(
                    f"Unsupported vector store: {provider}"
                )