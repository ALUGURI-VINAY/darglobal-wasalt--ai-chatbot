import os
import faiss
import numpy as np
from typing import List, Tuple
from app.config import settings

class VectorStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)

    def build_index(self, embeddings: np.ndarray):
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} does not match index dimension {self.dimension}")
        self.index.reset()
        self.index.add(embeddings)
        print(f"FAISS index built with {self.index.ntotal} vectors.")

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> Tuple[List[int], List[float]]:
        scores, indices = self.index.search(query_vector, top_k)
        return indices[0].tolist(), scores[0].tolist()

    def save(self, filepath: str = settings.FAISS_INDEX_PATH):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        faiss.write_index(self.index, filepath)
        print(f"FAISS index saved to {filepath}")

    def load(self, filepath: str = settings.FAISS_INDEX_PATH):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"FAISS index file not found at {filepath}")
        self.index = faiss.read_index(filepath)
        self.dimension = self.index.d
        print(f"Loaded FAISS index with {self.index.ntotal} vectors from {filepath}")
