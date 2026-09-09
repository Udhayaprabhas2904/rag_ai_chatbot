DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    filename TEXT NOT NULL,

    file_path TEXT NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'processing',

    total_pages INTEGER NOT NULL DEFAULT 0,

    total_chunks INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


DOCUMENT_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS document_chunks (

    id BIGSERIAL PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES documents(id)
        ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,

    content TEXT NOT NULL,

    page_number INTEGER,

    embedding VECTOR(768) NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


DOCUMENT_CHUNKS_DOCUMENT_INDEX = """
CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
ON document_chunks(document_id);
"""


DOCUMENT_CHUNKS_HNSW_INDEX = """
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops);
"""