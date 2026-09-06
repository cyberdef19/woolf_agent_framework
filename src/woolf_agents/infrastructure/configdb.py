from pathlib import Path

CONFIG_AGENT_DB = Path(__file__).resolve().parents[1]
PERSIST_DIRECTORY_CHROMA = CONFIG_AGENT_DB / "data" / "chroma"


configdb = {
    "chromadb":{
        "provider": "chroma",
        "persist_directory": PERSIST_DIRECTORY_CHROMA, #Path("I:\\WoolfFrameworkAgent\\src\\woolf_agents\\data\\chroma"),
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