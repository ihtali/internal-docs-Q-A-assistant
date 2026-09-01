import hashlib
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import embed
from app.models import Chunk, Document


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start + int(chunk_size * 0.4):
                end = last_space

        chunk = text[start:end].strip()
        if not chunk:
            break
        chunks.append(chunk)
        if end >= len(text):
            break

        next_start = max(start + chunk_size - overlap, end - overlap)
        if next_start <= start:
            next_start = start + 1
        while next_start < len(text) and text[start:end].strip() == text[next_start : next_start + (end - start)].strip():
            next_start += 1
        start = next_start

    return chunks


def load_text_from_file(path: str) -> tuple[str, str, int | None, list[str]]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
        combined = "\n\n".join(pages)
        return combined, "pdf", len(pages), pages

    if suffix in {".md", ".txt"}:
        text = file_path.read_text(encoding="utf-8")
        return text, suffix.lstrip("."), None, [text]

    raise ValueError(f"Unsupported file type: {suffix}")


def ingest_folder(folder_path: str, session: Session) -> dict:
    root = Path(folder_path)
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    doc_files = sorted([p for p in root.iterdir() if p.is_file() and p.suffix.lower() in {".pdf", ".md", ".txt"}])
    if not doc_files:
        return {"ingested": 0, "total_chunks": 0, "documents": []}

    ingested_files: list[str] = []
    total_chunks = 0

    for file_path in doc_files:
        content, file_type, _, _ = load_text_from_file(str(file_path))
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        existing = session.execute(
            select(Document).where(Document.source_path == str(file_path), Document.content_hash == content_hash)
        ).scalar_one_or_none()
        if existing is not None:
            ingested_files.append(file_path.name)
            total_chunks += existing.num_chunks
            continue

        existing_by_path = session.execute(select(Document).where(Document.source_path == str(file_path))).scalar_one_or_none()
        if existing_by_path is not None:
            session.delete(existing_by_path)

        chunked = chunk_text(content, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        vectors = embed(chunked)

        document = Document(
            filename=file_path.name,
            source_path=str(file_path),
            file_type=file_type,
            content_hash=content_hash,
            num_chunks=len(chunked),
        )
        session.add(document)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            existing = session.execute(
                select(Document).where(Document.source_path == str(file_path), Document.content_hash == content_hash)
            ).scalar_one_or_none()
            if existing is not None:
                ingested_files.append(file_path.name)
                total_chunks += existing.num_chunks
                continue
            raise

        for index, (chunk, vector) in enumerate(zip(chunked, vectors)):
            session.add(
                Chunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    page=None,
                    embedding=vector,
                )
            )

        ingested_files.append(file_path.name)
        total_chunks += len(chunked)

    session.commit()
    return {"ingested": len(ingested_files), "total_chunks": total_chunks, "documents": ingested_files}
