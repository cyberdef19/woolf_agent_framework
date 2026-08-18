from pathlib import Path

configdb = {
    "chromadb":{
        "provider": "chroma",
        "persist_directory": Path("I:\\WoolfFrameworkAgent\\src\\woolf_agents\\data\\chroma"),
        "collection_name": "history_sources",
        "embeddings": {
            "model_bge": "BAAI/bge-m3",
            "model_e5": "intfloat/multilingual-e5-base"
        },
        "model_kwargs": {
            "device": "cpu"
        },
        "encode_kwargs": {
            "normalize_embeddings": True
        }
        
        
    }
}