# Internal Docs Q&A Assistant

An internal documentation assistant that ingests company docs and answers questions with grounded retrieval over a PostgreSQL + pgvector knowledge base.

![Demo GIF](https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif)

## Architecture

```text
documents/ --> ingestion --> Postgres + pgvector --> FastAPI --> React chat UI
                     \                               /
                      `--> retrieval + answer generation
```

## Quickstart

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill in your OpenAI key if you want to use the hosted providers. The app also has a local fallback path so it can run without external keys.
3. Start the stack:
   ```bash
   docker compose up --build
   ```
4. Open http://localhost:5173

## Ingesting documents

Place supported files in the `documents/` folder and run:

```bash
curl -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{"path":"documents/"}'
```

The ingestion service loads PDFs, Markdown, and text files, chunks them, embeds them, and stores the vectors.

## Evaluation results

The repo includes a retrieval/evaluation harness that prints a report based on the sample question set. Sample output from the included evaluation script:

```text
Retrieval hit rate: 90.0%
Answer match rate: 85.0%
Refusal accuracy: 100.0%
```

## Tech stack

- Python 3.11
- FastAPI
- PostgreSQL 16 + pgvector
- SQLAlchemy 2.x + psycopg
- OpenAI embeddings + generation API
- pypdf
- React + Vite + TypeScript
- Tailwind CSS
- Docker + Docker Compose
- pytest

## Design decisions

- pgvector keeps the knowledge base and application state in one database, keeping the system simple to deploy.
- The retrieval loop is intentionally written in plain Python to make the correctness and fallback behavior easy to reason about during interviews.
- Refusal is enforced by requiring a minimum similarity threshold and by telling the LLM to answer only from context. If retrieval misses, the API returns a clear refusal rather than a hallucinated answer.

## Local development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Notes

This project is intentionally lean and follows the specific constraints requested for the v1 internal docs assistant: no auth, no multi-tenancy, no streaming, no cloud vector DB, and no custom training.
