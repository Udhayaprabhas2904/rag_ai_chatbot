from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field



# PDF Upload Response


class DocumentResponse(BaseModel):

    id: UUID

    filename: str

    status: str

    total_pages: int

    total_chunks: int

    created_at: datetime



# Document List Response


class DocumentListResponse(BaseModel):

    documents: list[DocumentResponse]



# Chat Request


class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000
    )

    document_id: UUID



# Source Information


class SourceResponse(BaseModel):

    document_id: UUID

    filename: str

    page_number: int | None = None

    chunk_index: int

    similarity: float



# Health Response

class HealthResponse(BaseModel):

    status: str

    database: str