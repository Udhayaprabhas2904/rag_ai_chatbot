# Realtime RAG Chat

A high-performance real-time Retrieval-Augmented Generation
(RAG) chatbot using:

- FastAPI
- WebSockets
- PostgreSQL
- pgvector
- HNSW
- LangChain
- Gemini
- PDF document ingestion


## Architecture

User
 |
 | PDF
 v
FastAPI
 |
 v
PDF Loader
 |
 v
Text Splitter
 |
 v
Gemini Embeddings
 |
 v
PostgreSQL + pgvector
 |
 v
HNSW Vector Search
 |
 | User Question
 v
Retriever
 |
 v
Gemini LLM
 |
 v
WebSocket Streaming
 |
 v
Frontend


## Requirements

- Python 3.11+
- Docker Desktop
- Google AI Studio Gemini API key


## Installation

Create virtual environment:

python -m venv .venv


Activate on Windows:

.venv\Scripts\activate


Install dependencies:

pip install -r requirements.txt


## Start PostgreSQL

docker compose up -d


## Create database tables

python -m backend.setup_database


## Start FastAPI

uvicorn backend.main:app --reload


Backend:

http://localhost:8000


## Frontend

Open:

frontend/index.html


## Usage

1. Start Docker PostgreSQL.
2. Start FastAPI.
3. Open the frontend.
4. Select a PDF.
5. Click Upload PDF.
6. Wait until indexing completes.
7. Ask questions about the PDF.
8. Gemini generates the answer using retrieved PDF chunks.


## RAG Pipeline

PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Gemini Embeddings
 ↓
PostgreSQL + pgvector
 ↓
HNSW
 ↓
Similarity Search
 ↓
Relevant Context
 ↓
Gemini
 ↓
WebSocket Token Streaming