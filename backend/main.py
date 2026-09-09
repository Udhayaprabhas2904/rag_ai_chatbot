
from contextlib import asynccontextmanager
from pathlib import Path
import shutil

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    WebSocket,
)

from fastapi.middleware.cors import CORSMiddleware

from backend.database import (
    create_pool,
    close_pool,
)

from backend.index_document import index_pdf

from backend.websocket.chat import chat_websocket



# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting Realtime RAG backend...")

    try:
        # Create PostgreSQL connection pool
        await create_pool()

        print("PostgreSQL connection pool created")
        print("Realtime RAG backend started")

        yield

    finally:

        print("Shutting down Realtime RAG backend...")

        # Close PostgreSQL connection pool
        await close_pool()

        print("PostgreSQL connection pool closed")



# FASTAPI APPLICATION


app = FastAPI(
    title="Realtime RAG Chat API",
    description=(
        "Real-time Retrieval-Augmented Generation "
        "chat application using FastAPI, PostgreSQL, "
        "pgvector and Gemini."
    ),
    version="1.0.0",
    lifespan=lifespan,
)



# CORS


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# UPLOAD DIRECTORY

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UPLOAD_DIR = PROJECT_ROOT / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

print(f"Upload directory: {UPLOAD_DIR}")



# ROOT


@app.get("/")
async def root():

    return {
        "status": "online",
        "service": "Realtime RAG Chat API",
        "version": "1.0.0",
    }



# HEALTH CHECK


@app.get("/health")
async def health():

    from backend.database import get_pool

    try:

        pool = get_pool()

        async with pool.acquire() as connection:

            result = await connection.fetchval(
                "SELECT 1"
            )

        if result == 1:

            return {
                "status": "healthy",
                "database": "connected",
            }

        raise Exception(
            "PostgreSQL returned an unexpected result."
        )

    except Exception as error:

        print(
            f"Database health check failed: {error}"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(error),
            },
        )



# PDF UPLOAD


@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...)
):

    
    # Validate filename
   

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    
    # Validate PDF extension
    

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    
    # Create safe filename
    

    safe_filename = Path(
        file.filename
    ).name

    file_path = UPLOAD_DIR / safe_filename

    try:

        
        # Save uploaded PDF
        

        with open(
            file_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        print(
            f"PDF uploaded: {safe_filename}"
        )

        # Index PDF

        result = await index_pdf(
            str(file_path)
        )

        return {
            "success": True,
            "message": (
                "PDF uploaded and indexed successfully."
            ),
            "filename": safe_filename,
            **result,
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"PDF indexing failed: {error}"
        )

        
        # Delete uploaded file if indexing fails
        

        if file_path.exists():

            try:
                file_path.unlink()
            except Exception as cleanup_error:

                print(
                    "Failed to remove uploaded file: "
                    f"{cleanup_error}"
                )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to upload and index PDF: "
                f"{str(error)}"
            ),
        )

    finally:

        await file.close()



# WEBSOCKET CHAT


@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await chat_websocket(
        websocket
    )

