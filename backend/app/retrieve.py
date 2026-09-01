import logging
from math import sqrt
from pathlib import Path

from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal
from app.ingest import chunk_text
from app.llm import embed

logger = logging.getLogger(__name__)


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def score_similarity(value: float, threshold: float | None = None) -> float:
    numeric_value = float(value)
    if threshold is not None:
        return max(0.0, min(1.0, numeric_value - float(threshold)))
    return max(0.0, min(1.0, numeric_value))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(x * x for x in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _fallback_retrieve(question: str, top_k: int) -> list[dict]:
    qvec = embed([question])[0]
    results: list[dict] = []
    for file_path in sorted(Path("../documents").glob("*")):
        if file_path.suffix.lower() not in {".md", ".txt", ".pdf"}:
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for idx, chunk in enumerate(chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)):
            chunk_vec = embed([chunk])[0]
            similarity = _cosine_similarity(qvec, chunk_vec)
            if similarity < settings.SIMILARITY_THRESHOLD:
                continue
            results.append(
                {
                    "id": idx,
                    "filename": file_path.name,
                    "page": None,
                    "chunk_index": idx,
                    "snippet": chunk,
                    "similarity": similarity,
                }
            )
    results.sort(key=lambda item: item["similarity"], reverse=True)
    return results[:top_k]


def retrieve(question: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.TOP_K
    qvec = embed([question])[0]
    qvec_literal = _vector_literal(qvec)

    try:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT c.id, c.document_id, c.chunk_index, c.content, c.page, d.filename,
                           1 - (c.embedding <=> CAST(:qvec AS vector)) AS similarity
                    FROM chunks c
                    JOIN documents d ON d.id = c.document_id
                    ORDER BY c.embedding <=> CAST(:qvec AS vector)
                    LIMIT :top_k
                    """
                ),
                {"qvec": qvec_literal, "top_k": top_k},
            ).mappings().all()
    except Exception:
        logger.exception("database retrieval failed; using file-system fallback")
        return _fallback_retrieve(question, top_k)

    results: list[dict] = []
    for row in rows:
        similarity = score_similarity(float(row["similarity"]))
        results.append(
            {
                "id": row["id"],
                "filename": row["filename"],
                "page": row["page"],
                "chunk_index": row["chunk_index"],
                "snippet": row["content"],
                "similarity": similarity,
            }
        )

    if not results:
        return []

    if results[0]["similarity"] < settings.SIMILARITY_THRESHOLD:
        return []

    return results
