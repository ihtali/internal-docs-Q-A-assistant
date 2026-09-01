from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    path: str = Field(..., description="Folder or file to ingest")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceItem(BaseModel):
    filename: str
    page: int | None = None
    chunk_index: int
    snippet: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    grounded: bool


class IngestResponse(BaseModel):
    ingested: int
    total_chunks: int
    documents: list[str]
