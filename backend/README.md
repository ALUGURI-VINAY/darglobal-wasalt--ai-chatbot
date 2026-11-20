# DarGlobal & Wasalt Real Estate AI Chatbot — FastAPI Backend

A production-grade AI Backend service for querying verified real estate data from **DarGlobal** and **Wasalt**. Built with Python FastAPI, genuine Hybrid RAG (BM25 + FAISS + `sentence-transformers/all-MiniLM-L6-v2` + Reciprocal Rank Fusion), and OpenRouter integration with a strict passage-based fallback.

---

## Architecture Overview

```
                                      +--------------------+
                                      |  Lovable Frontend  |
                                      +---------+----------+
                                                |
                                          HTTP REST API
                                                |
                                                v
+----------------------------------------------------------------------------------+
|                            FastAPI Backend (Port 8000)                           |
|                                                                                  |
|   /health              /chat                     /search              /sources   |
|      +-------------------+--------------------------+--------------------+       |
|                          |                                                       |
|                          v                                                       |
|            +----------------------------+                                        |
|            |      Hybrid Retriever      |                                        |
|            |     (Company Filtering)    |                                        |
|            +-------------+--------------+                                        |
|                          |                                                       |
|             +------------+-------------+                                         |
|             |                          |                                         |
|             v                          v                                         |
|     +---------------+          +---------------+                                 |
|     |  BM25 Keyword |          |  FAISS Vector |                                 |
|     |     Index     |          |  (all-MiniLM) |                                 |
|     +-------+-------+          +-------+-------+                                 |
|             |                          |                                         |
|             +------------+-------------+                                         |
|                          |                                                       |
|                          v                                                       |
|            +----------------------------+                                        |
|            | Reciprocal Rank Fusion(RRF)|                                        |
|            +-------------+--------------+                                        |
|                          |                                                       |
|                          v                                                       |
|            +----------------------------+       Has Key?     +---------------+   |
|            |    Grounded Prompting      +------------------->|  OpenRouter   |   |
|            |   (URL Attribution Engine) |                    |  (Gemma 4)    |   |
|            +-------------+--------------+                    +-------+-------+   |
|                          |                                           |           |
|                          | No Key / Rate Limit                       | Success   |
|                          v                                           v           |
|            +----------------------------+            +-----------------------+   |
|            | Direct Passage Fallback    |            | Grounded LLM Response |   |
|            +-------------+--------------+            +-----------+-----------+   |
|                          |                                       |               |
|                          +-------------------+-------------------+               |
|                                              |                                   |
|                                              v                                   |
|                                      JSON API Response                           |
+----------------------------------------------------------------------------------+
```

---

## Quickstart

### 1. Local Environment Setup
```bash
# Clone or navigate to the project directory
cd real_estate_chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your OpenRouter API key (free tier available at [openrouter.ai](https://openrouter.ai)):
```ini
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemma-4-31b-it:free
```
*(Note: If no key is set, the backend runs in high-precision Passage-Based Fallback mode, returning exact verified records with citations without crashing).*

### 3. Build Knowledge Base Indexes
```bash
python -m app.indexer
```
This indexes both `DARGLOBAL_VERIFIED_DATA.md` and `WASALT_VERIFIED_DATA.md`, generating `chunks.json`, `faiss_index.bin`, and `bm25_index.pkl` in the `data/` folder.

### 4. Start the FastAPI Server
```bash
python -m app.main
```
Or using Uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs are available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running Automated Tests

Run the comprehensive 15-test RAG verification suite:
```bash
python tests/test_suite.py
```
Tests cover:
- Exact keyword search (Pagani Tower, REGA License `1200016591`)
- Semantic dense retrieval without keywords
- Project-specific queries (Shams Al Riyadh)
- Executive governance (Ziad ElChaar, Vivek Pandey)
- Official FAQs (Wasalt Matchmaker)
- Property listings & active auctions
- Multi-chunk synthesis
- Unsupported question handling
- Cross-company isolation
- Official source URL preservation
- Missing API key passage fallback

---

## Docker Deployment

### Build and Run with Docker
```bash
# Build image (uses python:3.12-slim and caches embedding model)
docker build -t real-estate-chatbot .

# Run container
docker run -d -p 8000:8000 --env-file .env --name real_estate_ai real-estate-chatbot
```

### Run with Docker Compose
```bash
docker compose up --build -d
```
Verify container health:
```bash
curl http://localhost:8000/health
```

---

## Lovable Frontend Integration
Refer to [API_CONTRACT_LOVABLE.md](./API_CONTRACT_LOVABLE.md) for the exact JSON payloads, endpoints, and frontend TypeScript client templates.
