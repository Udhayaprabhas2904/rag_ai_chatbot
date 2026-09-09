from uuid import UUID

from backend.config import settings
from backend.database import get_pool
from backend.rag.embeddings import generate_embedding
from backend.rag.vector_store import vector_to_pgvector


async def retrieve_documents(
    query: str,
    document_id: UUID,
):
    """
    Retrieve the most relevant chunks from a specific document.

    Flow:

        User question
              ↓
        Gemini embedding
              ↓
        pgvector cosine similarity
              ↓
        Filter by document_id
              ↓
        Similarity threshold
              ↓
        Top-K results
    """

   
    # 1. Generate embedding for the user's question
   

    query_embedding = await generate_embedding(
        query
    )

   
    # 2. Convert embedding to PostgreSQL vector format
    

    query_vector = vector_to_pgvector(
        query_embedding
    )

   
    # 3. Get PostgreSQL connection pool
   
    pool = get_pool()

    
    # 4. Search pgvector
    
    async with pool.acquire() as connection:

        rows = await connection.fetch(
            """
            SELECT

                id,

                document_id,

                chunk_index,

                content,

                page_number,

                metadata,

                1 - (
                    embedding <=> $1::vector
                ) AS similarity

            FROM document_chunks

            WHERE document_id = $2

            AND (
                1 - (
                    embedding <=> $1::vector
                )
            ) >= $3

            ORDER BY embedding <=> $1::vector

            LIMIT $4
            """,

            query_vector,

            document_id,

            settings.SIMILARITY_THRESHOLD,

            settings.TOP_K,
        )

    
    # 5. Convert database rows to Python dictionaries
   

    results = []

    for row in rows:

        results.append(
            {
                "id": row["id"],

                "document_id": row["document_id"],

                "chunk_index": row["chunk_index"],

                "content": row["content"],

                "page_number": row["page_number"],

                "metadata": row["metadata"],

                "similarity": float(
                    row["similarity"]
                ),
            }
        )

    return results