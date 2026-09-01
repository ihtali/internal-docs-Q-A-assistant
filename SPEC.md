# Internal Docs Q&A Assistant — Build Specification

> This document reflects the requested project specification and tracks the implementation work in this repository.

## 1. What we're building

An internal knowledge-base assistant. A user points it at a folder of documents (PDF, Markdown, plain text). The system ingests them, and then a user can ask questions in plain English through a chat UI and get an answer grounded in those documents, with clickable citations back to the source. If the answer isn't in the documents, the system says so instead of guessing.

## 2. Tech stack

- Python 3.11
- FastAPI
- PostgreSQL 16 + pgvector
- SQLAlchemy 2.x + psycopg
- OpenAI text-embedding-3-small
- OpenAI gpt-4o-mini, pluggable
- pypdf
- React + Vite + TypeScript + Tailwind CSS
- Docker + Docker Compose
- pytest

## 3. Architecture

[diagram omitted for brevity in this working repository file]

## 4. Repository structure

See the built project structure under the repo root.

## 5. Configuration

The project loads environment values via pydantic-settings.

## 6. Database schema

The application uses vector similarity with cosine distance on a `chunks` table.

## 7. Backend detail

The backend includes ingestion, retrieval, response generation, and API routes.

## 8. Frontend detail

The frontend is a minimal React chat interface with citation chips.

## 9. Evaluation harness

The backend includes a YAML-driven evaluation harness and retrieval metrics.

## 10. docker-compose.yml

The app runs from a single docker compose up.

## 11. CI

GitHub Actions installs dependencies and runs lint/tests.

## 12. README requirements

The README includes the architecture, quickstart, eval results, and design notes.

## 13. Build phases

This repository implements the project in a single pass, while keeping the phases logically separated in code and docs.
