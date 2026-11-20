from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    query: Optional[str] = Field(None, description="User question or query text")
    message: Optional[str] = Field(None, description="Alternative alias for query")
    company: Optional[str] = Field("all", description="Company filter: 'darglobal', 'wasalt', or 'all'")
    top_k: Optional[int] = Field(5, description="Number of context chunks to retrieve", ge=1, le=15)

    @model_validator(mode="before")
    @classmethod
    def resolve_query(cls, values: Any):
        if isinstance(values, dict):
            q = values.get("query") or values.get("message")
            if not q or not str(q).strip():
                raise ValueError("A valid non-empty 'query' or 'message' is required.")
            values["query"] = str(q).strip()
        return values


class SourceCitation(BaseModel):
    chunk_id: str
    company: str
    category: str
    title: str
    source_url: str
    content_snippet: str
    relevance_score: float

class ChatResponse(BaseModel):
    answer: str
    company: str
    model_used: str
    sources: List[SourceCitation]
    retrieval_method: str = "hybrid_bm25_faiss_rrf"
    fallback_applied: bool
    disclaimer: str
    latency_breakdown_ms: Optional[Dict[str, float]] = None
    total_time_ms: Optional[float] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string", min_length=1)
    company: Optional[str] = Field("all", description="Company filter: 'darglobal', 'wasalt', or 'all'")
    top_k: Optional[int] = Field(5, description="Max results to return", ge=1, le=20)

class SearchResponse(BaseModel):
    query: str
    company_filter: str
    total_found: int
    results: List[SourceCitation]

class SourcesResponse(BaseModel):
    total_chunks: int
    darglobal_chunks: int
    wasalt_chunks: int
    categories: Dict[str, int]
    primary_documents: List[str]

class HealthResponse(BaseModel):
    status: str
    chunks_indexed: int
    embedding_model: str
    vector_index: str
    openrouter_configured: bool
    active_model: str
    version: str = "1.0.0"
