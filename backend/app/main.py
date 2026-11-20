import json
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Response, Request
from starlette.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import (
    ChatRequest, ChatResponse,
    SearchRequest, SearchResponse,
    SourcesResponse, HealthResponse
)
from app.hybrid_retriever import HybridRetriever
from app.openrouter_client import OpenRouterClient, DISCLAIMER_TEXT

retriever = HybridRetriever()
openrouter_client = OpenRouterClient()

def log_timing(query: str, company: str, chunk_count: int, lat: Dict[str, float], fallback: bool):
    total = lat.get("7_total_response_ms", 1.0)
    def pct(val):
        return f"{(val / total * 100):5.1f}%" if total > 0 else "  0.0%"

    print("\n" + "=" * 78)
    print("               PERFORMANCE MONITORING: RAG LATENCY BREAKDOWN")
    print("=" * 78)
    print(f"Query:                  \"{query[:55]}{'...' if len(query) > 55 else ''}\"")
    print(f"Company Filter:         {company}")
    print(f"Retrieved Chunks:       {chunk_count}")
    print(f"Fallback Active:        {fallback}")
    print("-" * 78)
    print(f"1. Request Processing:       {lat['1_request_processing_ms']:>8.2f} ms  ({pct(lat['1_request_processing_ms'])})")
    print(f"2. BM25 Retrieval:           {lat['2_bm25_retrieval_ms']:>8.2f} ms  ({pct(lat['2_bm25_retrieval_ms'])})")
    print(f"3. FAISS Semantic Search:    {lat['3_faiss_semantic_ms']:>8.2f} ms  ({pct(lat['3_faiss_semantic_ms'])})")
    print(f"   |-- Query Embedding:      {lat['  faiss_query_embedding_ms']:>8.2f} ms")
    print(f"   |-- FAISS Index Search:   {lat['  faiss_index_search_ms']:>8.2f} ms")
    print(f"4. RRF Ranking:              {lat['4_rrf_ranking_ms']:>8.2f} ms  ({pct(lat['4_rrf_ranking_ms'])})")
    print(f"5. Context Preparation:      {lat['5_context_prep_ms']:>8.2f} ms  ({pct(lat['5_context_prep_ms'])})")
    print(f"6. OpenRouter API Time:      {lat['6_openrouter_api_ms']:>8.2f} ms  ({pct(lat['6_openrouter_api_ms'])})")
    print("-" * 78)
    print(f"7. Total Response Time:      {lat['7_total_response_ms']:>8.2f} ms  (100.0%)")
    print("=" * 78 + "\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting DarGlobal & Wasalt Real Estate Chatbot Backend...")
    try:
        retriever.load()
    except Exception as e:
        print(f"Warning on startup loading: {e}. If indexes do not exist, run indexer.py first.")
    yield
    print("Shutting down backend...")
    await openrouter_client.aclose()

app = FastAPI(
    title="DarGlobal & Wasalt Real Estate AI Chatbot API",
    description="Production REST API providing hybrid RAG search and grounded conversational intelligence for DarGlobal and Wasalt real estate knowledge bases.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Lovable and external frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint providing status of indexes, models, and credentials."""
    return HealthResponse(
        status="healthy" if retriever.is_ready else "initializing",
        chunks_indexed=len(retriever.chunks),
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        vector_index="FAISS_IndexFlatIP",
        openrouter_configured=bool(settings.OPENROUTER_API_KEY),
        active_model=settings.OPENROUTER_MODEL,
        version="1.0.0"
    )

@app.post("/chat", response_model=ChatResponse, tags=["Conversational AI"])
async def chat_endpoint(request: ChatRequest, response: Response):
    """
    Main conversational endpoint:
    - Performs genuine hybrid RAG retrieval (BM25 + FAISS + RRF) with company filtering.
    - Prompts OpenRouter LLM with strict grounding and URL citations.
    - Returns detailed sub-millisecond latency breakdown for all 7 phases.
    - Emits standard W3C Server-Timing header for browser network inspection.
    """
    t_start = time.perf_counter()
    if not retriever.is_ready:
        raise HTTPException(status_code=503, detail="Search indexes not loaded. Run indexer.py first.")

    company = request.company.lower().strip() if request.company else "all"
    top_k = request.top_k or settings.TOP_K_RETRIEVAL
    t_req_proc = (time.perf_counter() - t_start) * 1000

    # 1. Retrieve relevant chunks using hybrid RAG with timings
    citations, ret_timings = retriever.retrieve(request.query, company=company, top_k=top_k, return_timings=True)

    # 2. Extract context only for retrieved citations using pre-indexed lookup
    chunk_map = getattr(retriever, "chunk_by_id", None) or {c["chunk_id"]: c for c in retriever.chunks}
    full_chunks = {c.chunk_id: chunk_map[c.chunk_id]["content"] for c in citations if c.chunk_id in chunk_map}

    # 3. Generate response via OpenRouter with context preparation and API timings
    answer, fallback_applied, gen_timings = await openrouter_client.generate_response(
        request.query, citations, full_chunks, return_timings=True
    )

    t_total_ms = (time.perf_counter() - t_start) * 1000

    latency_breakdown = {
        "1_request_processing_ms": round(t_req_proc, 2),
        "2_bm25_retrieval_ms": ret_timings.get("bm25_retrieval_ms", 0.0),
        "3_faiss_semantic_ms": ret_timings.get("faiss_semantic_ms", 0.0),
        "  faiss_query_embedding_ms": ret_timings.get("query_embedding_ms", 0.0),
        "  faiss_index_search_ms": ret_timings.get("faiss_index_search_ms", 0.0),
        "4_rrf_ranking_ms": ret_timings.get("rrf_ranking_ms", 0.0),
        "5_context_prep_ms": gen_timings.get("context_prep_ms", 0.0),
        "6_openrouter_api_ms": gen_timings.get("openrouter_api_ms", 0.0),
        "7_total_response_ms": round(t_total_ms, 2)
    }

    # Structured log output to backend console
    log_timing(request.query, company, len(citations), latency_breakdown, fallback_applied)

    # Standard W3C Server-Timing header for browser Network DevTools
    response.headers["Server-Timing"] = (
        f"total;dur={round(t_total_ms, 1)}, "
        f"openrouter;dur={round(gen_timings.get('openrouter_api_ms', 0.0), 1)}, "
        f"faiss;dur={round(ret_timings.get('faiss_semantic_ms', 0.0), 1)}, "
        f"bm25;dur={round(ret_timings.get('bm25_retrieval_ms', 0.0), 1)}, "
        f"rrf;dur={round(ret_timings.get('rrf_ranking_ms', 0.0), 1)}"
    )

    return ChatResponse(
        answer=answer,
        company=company,
        model_used=settings.OPENROUTER_MODEL if not fallback_applied else "passage_fallback_retrieval",
        sources=citations,
        retrieval_method="hybrid_bm25_faiss_rrf",
        fallback_applied=fallback_applied,
        disclaimer=DISCLAIMER_TEXT,
        latency_breakdown_ms=latency_breakdown,
        total_time_ms=round(t_total_ms, 2)
    )


@app.post("/chat/stream", tags=["Conversational AI"])
async def chat_stream_endpoint(request: ChatRequest, req: Request):
    """
    Streaming conversational endpoint using Server-Sent Events (SSE):
    - Hybrid RAG retrieval (BM25 + FAISS + RRF) with company filtering.
    - Token-by-token streaming from OpenRouter.
    - Progressive text streaming with terminal done event carrying citations & latency metrics.
    - Aborts upstream stream on client disconnect.
    """
    t_start = time.perf_counter()
    if not retriever.is_ready:
        raise HTTPException(status_code=503, detail="Search indexes not loaded. Run indexer.py first.")

    company = request.company.lower().strip() if request.company else "all"
    top_k = request.top_k or settings.TOP_K_RETRIEVAL
    t_req_proc = (time.perf_counter() - t_start) * 1000

    citations, ret_timings = retriever.retrieve(request.query, company=company, top_k=top_k, return_timings=True)
    chunk_map = getattr(retriever, "chunk_by_id", None) or {c["chunk_id"]: c for c in retriever.chunks}
    full_chunks = {c.chunk_id: chunk_map[c.chunk_id]["content"] for c in citations if c.chunk_id in chunk_map}

    async def event_generator():
        try:
            async for event in openrouter_client.stream_response(request.query, citations, full_chunks):
                if await req.is_disconnected():
                    break
                if "citations" in event:
                    event["sources"] = [c.model_dump() if hasattr(c, "model_dump") else c for c in event["citations"]]
                    del event["citations"]
                if event.get("type") == "done":
                    total_ms = round((time.perf_counter() - t_start) * 1000, 2)
                    event["total_time_ms"] = total_ms
                    event["company"] = company
                    event["latency_breakdown_ms"] = {
                        "1_request_processing_ms": round(t_req_proc, 2),
                        "2_bm25_retrieval_ms": ret_timings.get("bm25_retrieval_ms", 0.0),
                        "3_faiss_semantic_ms": ret_timings.get("faiss_semantic_ms", 0.0),
                        "4_rrf_ranking_ms": ret_timings.get("rrf_ranking_ms", 0.0),
                        "5_ttft_ms": event.get("ttft_ms", 0.0),
                        "6_openrouter_api_ms": event.get("total_api_ms", 0.0),
                        "7_total_response_ms": total_ms
                    }
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            err_event = {
                "type": "error",
                "message": str(e),
                "sources": [c.model_dump() if hasattr(c, "model_dump") else c for c in citations],
                "company": company,
                "disclaimer": DISCLAIMER_TEXT
            }
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/search", response_model=SearchResponse, tags=["Retrieval"])
async def search_endpoint(request: SearchRequest):
    """
    Direct hybrid search endpoint:
    Returns raw ranked source chunks, snippets, scores, and URLs without calling the LLM.
    """
    if not retriever.is_ready:
        raise HTTPException(status_code=503, detail="Search indexes not ready.")

    company = request.company.lower().strip() if request.company else "all"
    top_k = request.top_k or 5
    citations = retriever.retrieve(request.query, company=company, top_k=top_k)

    return SearchResponse(
        query=request.query,
        company_filter=company,
        total_found=len(citations),
        results=citations
    )

@app.get("/sources", response_model=SourcesResponse, tags=["Knowledge Base"])
async def get_sources():
    """Returns knowledge base summary, category distribution, and primary document metadata."""
    if not retriever.is_ready:
        raise HTTPException(status_code=503, detail="Indexes not ready.")

    dg_count = sum(1 for c in retriever.chunks if c["company"] == "darglobal")
    ws_count = sum(1 for c in retriever.chunks if c["company"] == "wasalt")

    categories = {}
    for c in retriever.chunks:
        k = f"{c['company']}::{c['category']}"
        categories[k] = categories.get(k, 0) + 1

    return SourcesResponse(
        total_chunks=len(retriever.chunks),
        darglobal_chunks=dg_count,
        wasalt_chunks=ws_count,
        categories=categories,
        primary_documents=[
            "DARGLOBAL_VERIFIED_DATA.md",
            "WASALT_VERIFIED_DATA.md"
        ]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
