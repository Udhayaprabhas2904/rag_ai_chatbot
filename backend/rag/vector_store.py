import json
from uuid import UUID

from backend.database import get_pool
from backend.config import settings



# VECTOR UTILITIES


def vector_to_pgvector(
    vector: list[float],
) -> str:
    """
    Convert a Python embedding into pgvector format.

    Example:

        [0.1, 0.2, 0.3]

    becomes:

        [0.1,0.2,0.3]
    """

    if not vector:
        raise ValueError(
            "Embedding vector cannot be empty."
        )

    try:

        values = [
            str(float(value))
            for value in vector
        ]

    except (TypeError, ValueError) as error:

        raise ValueError(
            f"Invalid embedding vector: {error}"
        ) from error

    return "[" + ",".join(values) + "]"



# DOCUMENT


async def create_document(
    filename: str,
    file_path: str,
    total_pages: int,
) -> UUID:
    """
    Create a document record.

    Returns:
        UUID of the newly created document.
    """

    if not filename:
        raise ValueError(
            "Filename cannot be empty."
        )

    if not file_path:
        raise ValueError(
            "File path cannot be empty."
        )

    if total_pages <= 0:
        raise ValueError(
            "Total pages must be greater than zero."
        )

    pool = get_pool()

    async with pool.acquire() as connection:

        document_id = await connection.fetchval(
            """
            INSERT INTO documents
            (
                filename,
                file_path,
                status,
                total_pages
            )
            VALUES
            (
                $1,
                $2,
                'processing',
                $3
            )
            RETURNING id
            """,
            filename,
            file_path,
            total_pages,
        )

    if document_id is None:
        raise RuntimeError(
            "Failed to create document."
        )

    return document_id



# INSERT CHUNKS


async def insert_chunks(
    document_id: UUID,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    """
    Insert document chunks and their Gemini embeddings.

    Each chunk is connected to its parent document.
    """

    
    # Validate input
    
    if not document_id:
        raise ValueError(
            "Document ID is required."
        )

    if not chunks:
        raise ValueError(
            "Cannot insert empty chunks."
        )

    if not embeddings:
        raise ValueError(
            "Cannot insert empty embeddings."
        )

    if len(chunks) != len(embeddings):

        raise ValueError(
            "Number of chunks and embeddings "
            "must be the same. "
            f"Chunks={len(chunks)}, "
            f"Embeddings={len(embeddings)}."
        )

    expected_dimension = (
        settings.EMBEDDING_DIMENSION
    )

    
    # Validate chunks and embeddings BEFORE database insert
   

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

        if not isinstance(chunk, dict):
            raise ValueError(
                f"Invalid chunk at index {index}."
            )

        content = chunk.get("content")

        if not content or not content.strip():
            raise ValueError(
                f"Chunk {index} has empty content."
            )

        if "chunk_index" not in chunk:
            raise ValueError(
                f"Chunk {index} is missing chunk_index."
            )

        if not isinstance(embedding, list):
            raise ValueError(
                f"Embedding {index} must be a list."
            )

        if len(embedding) != expected_dimension:

            raise ValueError(
                f"Invalid embedding dimension at "
                f"chunk {index}. "
                f"Expected {expected_dimension}, "
                f"got {len(embedding)}."
            )

    
    # Database transaction
   
    pool = get_pool()

    async with pool.acquire() as connection:

        async with connection.transaction():

            for chunk, embedding in zip(
                chunks,
                embeddings,
            ):

                
                # Convert embedding to pgvector
               

                vector = vector_to_pgvector(
                    embedding
                )

               
                # Page number
               

                page_number = chunk.get(
                    "page_number"
                )

                # Fallback to metadata if necessary
                if page_number is None:

                    metadata = chunk.get(
                        "metadata",
                        {},
                    )

                    if isinstance(metadata, dict):

                        page_number = metadata.get(
                            "page"
                        )

                
                # Metadata
              

                metadata = chunk.get(
                    "metadata",
                    {},
                )

                if not isinstance(
                    metadata,
                    dict,
                ):
                    metadata = {}

                # Keep page information in metadata
                if page_number is not None:

                    metadata.setdefault(
                        "page",
                        page_number,
                    )

                
                # Insert
                

                await connection.execute(
                    """
                    INSERT INTO document_chunks
                    (
                        document_id,
                        chunk_index,
                        content,
                        page_number,
                        embedding,
                        metadata
                    )
                    VALUES
                    (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5::vector,
                        $6::jsonb
                    )
                    """,

                    document_id,

                    chunk["chunk_index"],

                    chunk["content"].strip(),

                    page_number,

                    vector,

                    json.dumps(
                        metadata
                    ),
                )

    print(
        f"Inserted {len(chunks)} chunks "
        f"with {expected_dimension}-dimensional embeddings."
    )



# DOCUMENT STATUS


async def update_document_status(
    document_id: UUID,
    total_chunks: int,
    status: str = "completed",
) -> None:
    """
    Update document processing status.
    """

    allowed_statuses = {
        "processing",
        "completed",
        "failed",
    }

    if status not in allowed_statuses:

        raise ValueError(
            f"Invalid document status: {status}. "
            f"Allowed: {sorted(allowed_statuses)}"
        )

    if total_chunks < 0:

        raise ValueError(
            "Total chunks cannot be negative."
        )

    pool = get_pool()

    async with pool.acquire() as connection:

        result = await connection.execute(
            """
            UPDATE documents
            SET
                status = $2,
                total_chunks = $3,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,

            document_id,

            status,

            total_chunks,
        )

    if result == "UPDATE 0":

        raise ValueError(
            f"Document not found: {document_id}"
        )



# FAILED DOCUMENT


async def mark_document_failed(
    document_id: UUID,
) -> None:
    """
    Mark a document as failed.
    """

    pool = get_pool()

    async with pool.acquire() as connection:

        result = await connection.execute(
            """
            UPDATE documents
            SET
                status = 'failed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,

            document_id,
        )

    if result == "UPDATE 0":

        print(
            f"Warning: document {document_id} "
            f"was not found while marking failed."
        )



# DELETE DOCUMENT


async def delete_document(
    document_id: UUID,
) -> None:
    """
    Delete a document.

    document_chunks should be automatically deleted
    if the foreign key uses ON DELETE CASCADE.
    """

    pool = get_pool()

    async with pool.acquire() as connection:

        result = await connection.execute(
            """
            DELETE FROM documents
            WHERE id = $1
            """,

            document_id,
        )

    if result == "DELETE 0":

        raise ValueError(
            f"Document not found: {document_id}"
        )