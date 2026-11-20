import os
import re
import pickle
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from app.config import settings

class BM25SearchEngine:
    def __init__(self):
        self.bm25: BM25Okapi = None
        self.corpus_size: int = 0

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Lowercase, alphanumeric tokenization
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def build_index(self, corpus_texts: List[str]):
        tokenized_corpus = [self.tokenize(text) for text in corpus_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus_size = len(corpus_texts)
        print(f"BM25 index built with {self.corpus_size} documents.")

    def search(self, query: str, top_k: int = 10) -> Tuple[List[int], List[float]]:
        if not self.bm25:
            return [], []
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return [], []
        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        ranked_scores = [float(scores[i]) for i in ranked_indices]
        return ranked_indices, ranked_scores

    def save(self, filepath: str = settings.BM25_INDEX_PATH):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self.bm25, f)
        print(f"BM25 index saved to {filepath}")

    def load(self, filepath: str = settings.BM25_INDEX_PATH):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"BM25 index file not found at {filepath}")
        with open(filepath, "rb") as f:
            self.bm25 = pickle.load(f)
        self.corpus_size = self.bm25.corpus_size
        print(f"Loaded BM25 index with {self.corpus_size} documents from {filepath}")
