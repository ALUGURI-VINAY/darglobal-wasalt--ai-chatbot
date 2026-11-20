import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from app.config import settings
from app.embeddings import EmbeddingModel
from app.vector_store import VectorStore
from app.bm25_search import BM25SearchEngine
from app.models import SourceCitation

class HybridRetriever:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.chunk_by_id: Dict[str, Dict[str, Any]] = {}
        self.embedding_model: EmbeddingModel = None
        self.vector_store: VectorStore = None
        self.bm25_engine: BM25SearchEngine = None
        self.is_ready: bool = False

    def load(self):
        if not os.path.exists(settings.CHUNKS_PATH):
            raise FileNotFoundError(f"Chunks file missing at {settings.CHUNKS_PATH}. Run indexer first.")
        with open(settings.CHUNKS_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.chunk_by_id = {c["chunk_id"]: c for c in self.chunks}

        self.embedding_model = EmbeddingModel.get_instance()
        self.vector_store = VectorStore()
        self.vector_store.load(settings.FAISS_INDEX_PATH)

        self.bm25_engine = BM25SearchEngine()
        self.bm25_engine.load(settings.BM25_INDEX_PATH)

        self.is_ready = True
        print(f"HybridRetriever successfully loaded {len(self.chunks)} chunks.")

    def retrieve(
        self,
        query: str,
        company: Optional[str] = "all",
        top_k: int = 5,
        return_timings: bool = False
    ) -> Union[List[SourceCitation], Tuple[List[SourceCitation], Dict[str, float]]]:
        if not self.is_ready:
            raise RuntimeError("HybridRetriever not loaded. Call load() before retrieving.")

        company_filter = (company or "all").lower().strip()

        # Step 1: Pre-calculate candidate valid indices if company filter is active
        t_filter_start = time.perf_counter()
        valid_indices = set()
        for idx, chunk in enumerate(self.chunks):
            if company_filter in ["all", "unified", "both"]:
                valid_indices.add(idx)
            elif company_filter in chunk["company"].lower():
                valid_indices.add(idx)

        filter_ms = (time.perf_counter() - t_filter_start) * 1000

        if not valid_indices:
            timings = {
                "bm25_retrieval_ms": 0.0,
                "faiss_semantic_ms": 0.0,
                "query_embedding_ms": 0.0,
                "faiss_index_search_ms": 0.0,
                "rrf_ranking_ms": 0.0,
                "retrieval_total_ms": filter_ms
            }
            return ([], timings) if return_timings else []

        # Retrieve candidates for RRF fusion
        pool_size = min(len(valid_indices), max(top_k * 4, 30))

        # 2. BM25 Keyword Search
        t_bm25_start = time.perf_counter()
        bm25_indices, bm25_scores = self.bm25_engine.search(query, top_k=len(self.chunks))
        filtered_bm25_ranks = {}
        bm25_rank = 1
        for idx, score in zip(bm25_indices, bm25_scores):
            if idx in valid_indices and score > 0:
                filtered_bm25_ranks[idx] = bm25_rank
                bm25_rank += 1
                if bm25_rank > pool_size:
                    break
        bm25_ms = (time.perf_counter() - t_bm25_start) * 1000

        # 3. FAISS Dense Semantic Search
        t_faiss_start = time.perf_counter()
        t_emb_start = time.perf_counter()
        q_emb = self.embedding_model.encode_query(query)
        embedding_ms = (time.perf_counter() - t_emb_start) * 1000

        t_search_start = time.perf_counter()
        faiss_indices, faiss_scores = self.vector_store.search(q_emb, top_k=len(self.chunks))
        filtered_faiss_ranks = {}
        faiss_rank = 1
        for idx in faiss_indices:
            if idx in valid_indices:
                filtered_faiss_ranks[idx] = faiss_rank
                faiss_rank += 1
                if faiss_rank > pool_size:
                    break
        index_search_ms = (time.perf_counter() - t_search_start) * 1000
        faiss_total_ms = (time.perf_counter() - t_faiss_start) * 1000

        # 4. Reciprocal Rank Fusion (RRF)
        t_rrf_start = time.perf_counter()
        k = settings.RRF_K
        candidate_ids = set(filtered_bm25_ranks.keys()) | set(filtered_faiss_ranks.keys())
        rrf_scores = {}

        for idx in candidate_ids:
            bm25_r = filtered_bm25_ranks.get(idx)
            faiss_r = filtered_faiss_ranks.get(idx)

            bm25_term = (settings.BM25_WEIGHT / (k + bm25_r)) if bm25_r is not None else 0.0
            dense_term = (settings.DENSE_WEIGHT / (k + faiss_r)) if faiss_r is not None else 0.0

            rrf_scores[idx] = bm25_term + dense_term

        # Sort by fused score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        citations = []
        for idx, score in sorted_candidates:
            c = self.chunks[idx]
            snippet = c["content"].replace("\n", " ").strip()
            if len(snippet) > 250:
                snippet = snippet[:247] + "..."

            citations.append(SourceCitation(
                chunk_id=c["chunk_id"],
                company=c["company"],
                category=c["category"],
                title=c["title"],
                source_url=c["source_url"],
                content_snippet=snippet,
                relevance_score=round(float(score), 5)
            ))
        rrf_ms = (time.perf_counter() - t_rrf_start) * 1000

        timings = {
            "bm25_retrieval_ms": round(bm25_ms, 2),
            "faiss_semantic_ms": round(faiss_total_ms, 2),
            "query_embedding_ms": round(embedding_ms, 2),
            "faiss_index_search_ms": round(index_search_ms, 2),
            "rrf_ranking_ms": round(rrf_ms, 2),
            "retrieval_total_ms": round(bm25_ms + faiss_total_ms + rrf_ms + filter_ms, 2)
        }

        if return_timings:
            return citations, timings
        return citations

