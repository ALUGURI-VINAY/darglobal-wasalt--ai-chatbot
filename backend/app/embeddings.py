import threading
from collections import OrderedDict
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.config import settings

class QueryEmbeddingCache:
    def __init__(self, maxsize: int = 512):
        self.maxsize = maxsize
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def get(self, query: str) -> Optional[np.ndarray]:
        with self._lock:
            if query in self._cache:
                self._cache.move_to_end(query)
                return self._cache[query].copy()
            return None

    def put(self, query: str, embedding: np.ndarray) -> None:
        with self._lock:
            if query in self._cache:
                self._cache.move_to_end(query)
            else:
                if len(self._cache) >= self.maxsize:
                    self._cache.popitem(last=False)
                self._cache[query] = embedding.copy()


class EmbeddingModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EmbeddingModel()
        return cls._instance

    def __init__(self):
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        self.query_cache = QueryEmbeddingCache(maxsize=512)
        print("Embedding model loaded successfully.")

    def encode(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.astype('float32')

    def encode_query(self, query: str) -> np.ndarray:
        norm_key = query.strip().lower()
        cached = self.query_cache.get(norm_key)
        if cached is not None:
            return cached
        embedding = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True).astype('float32')
        self.query_cache.put(norm_key, embedding)
        return embedding

