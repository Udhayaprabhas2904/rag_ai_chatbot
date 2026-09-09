# Realtime RAG Chat

A high-performance, real-time Retrieval-Augmented Generation (RAG) chatbot for interacting with PDF documents.

The application combines FastAPI, WebSockets, PostgreSQL with pgvector, Gemini embeddings, and Gemini LLM streaming to provide document-based question answering with real-time responses.

## Overview

Realtime RAG Chat allows users to upload PDF documents, process their contents into searchable vector embeddings, and ask questions based on the uploaded document.

The system retrieves the most relevant document chunks using vector similarity search and provides them as context to Gemini. The generated response is streamed to the frontend through a persistent WebSocket connection.

## Key Features

- PDF document ingestion and processing
- Retrieval-Augmented Generation (RAG)
- Real-time WebSocket communication
- Token-by-token response streaming
- Gemini embeddings for semantic search
- Gemini LLM for response generation
- PostgreSQL with pgvector for vector storage
- HNSW indexing for efficient similarity search
- FastAPI asynchronous backend
- Docker-based PostgreSQL environment
- Document-aware conversational interface

## Architecture

```text
                         User
                           |
                           | Upload PDF
                           v
                    +-------------+
                    |   FastAPI   |
                    +-------------+
                           |
                           v
                    +-------------+
                    |  PDF Loader  |
                    +-------------+
                           |
                           v
                    +-------------+
                    | Text Splitter|
                    +-------------+
                           |
                           v
                  +-------------------+
                  | Gemini Embeddings |
                  +-------------------+
                           |
                           v
              +-------------------------+
              | PostgreSQL + pgvector  |
              +-------------------------+
                           |
                           v
                  +----------------+
                  | HNSW Index     |
                  +----------------+
                           |
                           | Vector Similarity Search
                           v
                    +-------------+
                    |  Retriever  |
                    +-------------+
                           |
                           | Relevant Context
                           v
                    +-------------+
                    | Gemini LLM  |
                    +-------------+
                           |
                           | Streaming Response
                           v
                  +----------------+
                  |   WebSocket    |
                  +----------------+
                           |
                           v
                    +-------------+
                    |  Frontend   |
                    +-------------+


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

http://localhost:8000/docs


## Frontend

http://localhost:5500


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

PDF Document
     │
     ▼
Text Extraction
     │
     ▼
Document Chunking
     │
     ▼
Gemini Embeddings
     │
     ▼
PostgreSQL + pgvector
     │
     ▼
HNSW Vector Index
     │
     ▼
Similarity Search
     │
     ▼
Relevant Context
     │
     ▼
Gemini LLM
     │
     ▼
WebSocket Token Streaming
     │
     ▼
Frontend Chat Interface
