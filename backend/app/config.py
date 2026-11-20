import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "700"))
    
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    RRF_K: int = int(os.getenv("RRF_K", "60"))
    BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "1.0"))
    DENSE_WEIGHT: float = float(os.getenv("DENSE_WEIGHT", "1.0"))
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    CHUNKS_PATH: str = os.path.join(DATA_DIR, "chunks.json")
    FAISS_INDEX_PATH: str = os.path.join(DATA_DIR, "faiss_index.bin")
    BM25_INDEX_PATH: str = os.path.join(DATA_DIR, "bm25_index.pkl")
    
    CORS_ORIGINS: List[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")]
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

settings = Settings()
