import os
import json
from app.config import settings
from app.chunker import StructureAwareChunker
from app.embeddings import EmbeddingModel
from app.vector_store import VectorStore
from app.bm25_search import BM25SearchEngine

def run_indexing():
    print("="*60)
    print("STARTING KNOWLEDGE BASE INDEXING PIPELINE")
    print("="*60)

    dg_path = os.path.join(settings.DATA_DIR, "DARGLOBAL_VERIFIED_DATA.md")
    ws_path = os.path.join(settings.DATA_DIR, "WASALT_VERIFIED_DATA.md")

    if not os.path.exists(dg_path) or not os.path.exists(ws_path):
        raise FileNotFoundError(f"Missing source Markdown files in {settings.DATA_DIR}")

    chunker = StructureAwareChunker()
    print("Chunking DarGlobal verified data...")
    dg_chunks = chunker.chunk_darglobal(dg_path)
    print(f"-> Generated {len(dg_chunks)} DarGlobal chunks.")

    print("Chunking Wasalt verified data...")
    ws_chunks = chunker.chunk_wasalt(ws_path)
    print(f"-> Generated {len(ws_chunks)} Wasalt chunks.")

    all_chunks = dg_chunks + ws_chunks
    total_chunks = len(all_chunks)
    print(f"Total Chunks: {total_chunks}")

    # Integrity & statistics check
    missing_urls = [c for c in all_chunks if not c.get("source_url") or c.get("source_url") == "N/A"]
    lengths = [len(c["content"]) for c in all_chunks]
    avg_len = sum(lengths) / total_chunks if total_chunks else 0
    max_len = max(lengths) if lengths else 0
    min_len = min(lengths) if lengths else 0

    chunk_ids = [c["chunk_id"] for c in all_chunks]
    duplicates = len(chunk_ids) - len(set(chunk_ids))

    categories = {}
    for c in all_chunks:
        k = f"{c['company']}::{c['category']}"
        categories[k] = categories.get(k, 0) + 1

    print("\n--- CHUNKING & INDEXING AUDIT REPORT ---")
    print(f"Total Chunks: {total_chunks}")
    print(f"DarGlobal Chunks: {len(dg_chunks)}")
    print(f"Wasalt Chunks: {len(ws_chunks)}")
    print(f"Duplicate Chunk IDs: {duplicates}")
    print(f"Missing Source URLs: {len(missing_urls)}")
    print(f"Chunk Character Lengths: Min={min_len}, Avg={avg_len:.1f}, Max={max_len}")
    print("Category Breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count} chunks")

    # Save chunks.json
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(settings.CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    print(f"\nSaved chunks to {settings.CHUNKS_PATH}")

    # Generate Embeddings & FAISS Index
    corpus_texts = [f"{c['title']}\n{c['content']}" for c in all_chunks]
    embed_model = EmbeddingModel.get_instance()
    print("Computing embeddings with sentence-transformers/all-MiniLM-L6-v2...")
    embeddings = embed_model.encode(corpus_texts)
    print(f"Generated embeddings shape: {embeddings.shape}")

    vector_store = VectorStore(dimension=embeddings.shape[1])
    vector_store.build_index(embeddings)
    vector_store.save(settings.FAISS_INDEX_PATH)

    # Generate BM25 Index
    print("Building BM25 keyword index...")
    bm25 = BM25SearchEngine()
    bm25.build_index(corpus_texts)
    bm25.save(settings.BM25_INDEX_PATH)

    print("="*60)
    print("INDEXING COMPLETED SUCCESSFULLY!")
    print("="*60)
    return {
        "total_chunks": total_chunks,
        "darglobal_chunks": len(dg_chunks),
        "wasalt_chunks": len(ws_chunks),
        "duplicate_chunks": duplicates,
        "missing_urls": len(missing_urls),
        "avg_length": avg_len,
        "max_length": max_len,
        "categories": categories
    }

if __name__ == "__main__":
    run_indexing()
