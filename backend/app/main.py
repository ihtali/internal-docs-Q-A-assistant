import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import SessionLocal, init_db
from app.ingest import ingest_folder
from app.llm import DEFAULT_REFUSAL, generate
from app.prompt import build_prompt
from app.retrieve import retrieve
from app.schemas import AskRequest, AskResponse, IngestRequest, SourceItem

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Internal Docs Q&A Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(payload: IngestRequest) -> dict:
    try:
        with SessionLocal() as session:
            result = ingest_folder(payload.path, session)
            return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("ingest failed")
        raise HTTPException(status_code=503, detail="Ingestion failed") from exc


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    contexts = retrieve(payload.question, top_k=payload.top_k)

    if not contexts:
        return AskResponse(answer=DEFAULT_REFUSAL, sources=[], grounded=False)

    system, user = build_prompt(payload.question, contexts)
    answer = generate(system, user)

    source_items = [
        SourceItem(
            filename=context["filename"],
            page=context["page"],
            chunk_index=context["chunk_index"],
            snippet=context["snippet"],
            similarity=context["similarity"],
        )
        for context in contexts
    ]
    return AskResponse(answer=answer, sources=source_items, grounded=True)
