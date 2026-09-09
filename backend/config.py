from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    
    # PostgreSQL
   

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    DATABASE_URL: str

    
    # Gemini
    

    GEMINI_API_KEY: str

 
    # Embeddings
   

    EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Must match PostgreSQL VECTOR(...)
    EMBEDDING_DIMENSION: int = 768

    
    # LLM
    

    LLM_MODEL: str = "gemini-2.5-flash"

    
    # RAG Chunking
    

    CHUNK_SIZE: int = 1000

    CHUNK_OVERLAP: int = 200

    
    # Retrieval
    

    TOP_K: int = 5

    SIMILARITY_THRESHOLD: float = 0.30

    
    # Pydantic configuration
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()