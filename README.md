# Internal Docs Q&A Assistant

A production-style **RAG** (Retrieval-Augmented Generation) assistant for internal knowledge bases. Point it at a folder of documents (PDF, Markdown, plain text), and ask questions in plain English. Every answer is **grounded in your documents and cited back to the source** — and when the answer isn't in the docs, it says so instead of guessing.

---

## Why this exists

Most internal knowledge lives in scattered PDFs, wikis, and handbooks that nobody can search well. This tool ingests that content into a vector database and lets staff get **trustworthy, sourced answers** — the single most common thing companies ask an AI engineer to build first. The focus here is on the parts that make RAG production-grade rather than a demo: **citations, refusal-when-unsure, and measured retrieval quality.**

---

## Architecture

```
                    ┌─────────────────────────────┐
  documents/  ───▶  │  Ingestion pipeline         │
  (pdf/md/txt)      │  load → chunk → embed → store│
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │  PostgreSQL + pgvector       │
                    │  documents, chunks(+vector)  │
                    └──────────────┬──────────────┘
                                   ▼
  React chat UI ◀──▶  FastAPI  ┌────────────────────────────────┐
                     /ingest   │ /ask: embed q → similarity search│
                     /ask      │ → build grounded prompt          │
                     /health   │ → LLM → answer + source chunks   │
                               └────────────────────────────────┘

  Everything runs via docker-compose: [db] [api] [frontend]
```

**Request flow for a question:** embed the query → cosine similarity search over chunk embeddings in pgvector → if best match is below threshold, refuse → otherwise build a grounded prompt from the top-k chunks → LLM generates the answer → API returns the answer plus structured source citations.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.x |
| Vector store | PostgreSQL 16 + **pgvector** |
| Embeddings | OpenAI `text-embedding-3-small` (1536-dim) |
| Generation | OpenAI `gpt-4o-mini` (swappable to Anthropic Claude via env) |
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Infra | Docker Compose, GitHub Actions CI |
| Testing / eval | pytest + a custom retrieval-evaluation harness |

---

## Quickstart

**Prerequisites:** Docker + Docker Compose, and an OpenAI API key.

```bash
# 1. Clone
git clone https://github.com/ihtali/docs-qa-assistant.git
cd docs-qa-assistant

# 2. Configure
cp .env.example .env
# open .env and set OPENAI_API_KEY=sk-...

# 3. Run everything
docker compose up --build
```

Then open **http://localhost:5173** for the chat UI. The API is at **http://localhost:8000** (`GET /health` to check it's alive).

---

## Ingesting documents

Put your files in the `documents/` folder (PDF, `.md`, or `.txt`), then:

```bash
# via the ingest script
docker compose exec api python scripts/ingest_folder.py documents/

# or via the API
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"path": "documents/"}'
```

Re-running ingestion is idempotent — the same file won't be duplicated.

---

## Asking questions

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?", "top_k": 5}'
```

Example response:

```json
{
  "answer": "Refunds are accepted within 30 days of purchase...",
  "sources": [
    { "filename": "handbook.pdf", "page": 12, "chunk_index": 40,
      "snippet": "Refunds are accepted within 30 days...", "similarity": 0.82 }
  ],
  "grounded": true
}
```

If the question isn't answerable from the documents, `grounded` is `false` and `answer` is a clear refusal — by design.

---

## Evaluation

Retrieval quality is measured, not assumed. The harness runs a fixed set of gold questions (`backend/eval/questions.yaml`) and reports three headline metrics:

```bash
docker compose exec api python eval/run_eval.py
```

| Metric | Result |
|---|---|
| Retrieval hit rate (expected source in top-k) | <!-- TODO: real % --> |
| Answer match rate | <!-- TODO: real % --> |
| Refusal accuracy (correctly declines off-topic) | <!-- TODO: real % --> |

> _Fill these in with the actual output of `run_eval.py`. Do not estimate — the point of this section is that the numbers are real and reproducible._

---

## Design decisions

A short note on the choices that matter, and why:

- **pgvector instead of a managed vector DB (Pinecone/Weaviate).** Keeps everything in one Postgres instance — no extra service to run or pay for, simpler ops, and more than fast enough at this scale. Trades some scale ceiling for real simplicity.
- **Plain-Python retrieval loop instead of a framework.** The retrieve → prompt → generate path is small and explicit, so behaviour is fully under control and easy to debug. (A framework-based version is a possible refactor, not a requirement.)
- **Grounding + refusal enforced in the prompt.** The system is instructed to answer only from retrieved context and to decline otherwise, and a similarity threshold gates retrieval so weak matches trigger a refusal rather than a hallucinated answer.
- **Citations returned as structured data, not parsed from the answer text.** The API attaches sources separately so the UI can render reliable, clickable citations.

---

## Roadmap

- [ ] Reranking of retrieved chunks (cross-encoder or LLM rerank)
- [ ] Hybrid search (BM25 keyword + vector) for better recall
- [ ] Streaming responses
- [ ] Slack bot front-end
- [ ] Claude vs GPT answer-quality comparison in the eval harness

---

## Project structure

```
docs-qa-assistant/
├── backend/      # FastAPI app, ingestion, retrieval, eval harness, tests
├── frontend/     # React + Vite chat UI with source citations
├── documents/    # sample corpus
├── docker-compose.yml
└── .env.example
```

---

## License

<!-- TODO: pick one, e.g. MIT -->

## Author

**Ihtasham Ali (IHT)** — [GitHub](https://github.com/ihtali) · [LinkedIn](https://linkedin.com/in/ihtasham-ali)
