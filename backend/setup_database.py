import asyncio

from backend.database import (
    create_pool,
    close_pool,
)



# ENABLE PGVECTOR


CREATE_VECTOR_EXTENSION = """
CREATE EXTENSION IF NOT EXISTS vector;
"""



# DOCUMENTS TABLE


CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    filename TEXT NOT NULL,

    file_path TEXT NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'processing',

    total_pages INTEGER NOT NULL DEFAULT 0,

    total_chunks INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);
"""



# DOCUMENT CHUNKS TABLE


CREATE_DOCUMENT_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS document_chunks (

    id BIGSERIAL PRIMARY KEY,

    document_id UUID NOT NULL,

    chunk_index INTEGER NOT NULL,

    content TEXT NOT NULL,

    page_number INTEGER,

    embedding VECTOR(768) NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_document_chunks_document

        FOREIGN KEY (document_id)

        REFERENCES documents(id)

        ON DELETE CASCADE

);
"""



# DOCUMENT ID INDEX


CREATE_DOCUMENT_INDEX = """
CREATE INDEX IF NOT EXISTS
document_chunks_document_id_idx

ON document_chunks(document_id);
"""



# HNSW VECTOR INDEX


CREATE_HNSW_INDEX = """
CREATE INDEX IF NOT EXISTS
document_chunks_embedding_hnsw

ON document_chunks

USING hnsw (embedding vector_cosine_ops);
"""



# SETUP DATABASE

async def setup_database():

    print("")
    print("========================================")
    print("       RAG DATABASE SETUP")
    print("========================================")
    print("")

    pool = await create_pool()

    try:

        async with pool.acquire() as connection:

            
            # 1. Enable pgvector
            
            print("1. Enabling pgvector...")

            await connection.execute(
                CREATE_VECTOR_EXTENSION
            )

            print("   ✓ pgvector enabled")

           
            # 2. Create documents table
            

            print("2. Creating documents table...")

            await connection.execute(
                CREATE_DOCUMENTS_TABLE
            )

            print("   ✓ documents table ready")

            
            # 3. Create document_chunks table
           

            print("3. Creating document_chunks table...")

            await connection.execute(
                CREATE_DOCUMENT_CHUNKS_TABLE
            )

            print("   ✓ document_chunks table ready")

            
            # 4. Create normal index
           

            print("4. Creating document ID index...")

            await connection.execute(
                CREATE_DOCUMENT_INDEX
            )

            print("   ✓ document ID index ready")

          
            # 5. Create HNSW vector index
            

            print("5. Creating HNSW vector index...")

            await connection.execute(
                CREATE_HNSW_INDEX
            )

            print("   ✓ HNSW index ready")

    finally:

        await close_pool()

    print("")
    print("========================================")
    print("   DATABASE SETUP COMPLETED ✓")
    print("========================================")
    print("")



# MAIN


async def main():

    try:

        await setup_database()

    except Exception as error:

        print("")
        print("========================================")
        print("   DATABASE SETUP FAILED ✗")
        print("========================================")
        print("")
        print(f"Error: {error}")
        print("")

        raise


if __name__ == "__main__":

    asyncio.run(main())