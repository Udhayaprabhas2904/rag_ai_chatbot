from pathlib import Path

from backend.rag.loader import load_pdf
from backend.rag.splitter import split_documents
from backend.rag.embeddings import generate_embeddings

from backend.rag.vector_store import (
    create_document,
    insert_chunks,
    update_document_status,
    mark_document_failed,
)


async def index_pdf(file_path: str):
    """
    Complete PDF indexing pipeline.

    PDF
      ↓
    Extract text
      ↓
    Split into chunks
      ↓
    Create document record
      ↓
    Generate Gemini embeddings
      ↓
    Store chunks + embeddings in PostgreSQL
      ↓
    Mark document as completed
    """

    path = Path(file_path)

    
    # Validate PDF
   

    if not path.exists():
        raise FileNotFoundError(
            f"PDF not found: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    document_name = path.name

    print(
        f"Loading PDF: {document_name}"
    )

    
    # STEP 1: Extract PDF text
  

    pages = load_pdf(
        file_path
    )

    if not pages:
        raise ValueError(
            "No readable text found in PDF."
        )

    print(
        f"Extracted {len(pages)} pages"
    )

   
    # STEP 2: Split PDF text into chunks
 

    chunks = split_documents(
        pages
    )

    if not chunks:
        raise ValueError(
            "No text chunks were created from the PDF."
        )

    print(
        f"Created {len(chunks)} chunks"
    )

    
    # STEP 3: Create document record
   

    document_id = await create_document(
        filename=document_name,
        file_path=file_path,
        total_pages=len(pages),
    )

    print(
        f"Created document: {document_id}"
    )

    try:

        
        # STEP 4: Generate Gemini embeddings
       
        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = await generate_embeddings(
            texts
        )

        if not embeddings:
            raise ValueError(
                "No embeddings were generated."
            )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Number of embeddings does not "
                "match number of chunks."
            )

        # Validate embedding dimensions

        expected_dimension = 768

        for index, embedding in enumerate(
            embeddings
        ):

            if len(embedding) != expected_dimension:

                raise ValueError(
                    f"Invalid embedding dimension "
                    f"for chunk {index}. "
                    f"Expected {expected_dimension}, "
                    f"got {len(embedding)}."
                )

        print(
            f"Generated {len(embeddings)} embeddings"
        )

       
        # STEP 5: Store chunks and embeddings
        

        await insert_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        print(
            "Chunks and embeddings stored successfully."
        )

      
        # STEP 6: Mark document as completed
       

        await update_document_status(
            document_id=document_id,
            total_chunks=len(chunks),
            status="completed",
        )

        print(
            f"Indexed {document_name} successfully."
        )

        
        # Return result to FastAPI
      

        return {
            "document_id": str(document_id),
            "document": document_name,
            "pages": len(pages),
            "chunks": len(chunks),
            "status": "completed",
        }

    except Exception as error:

        print(
            f"Indexing failed for "
            f"{document_name}: {error}"
        )

       
        # Mark document as failed
        

        try:

            await mark_document_failed(
                document_id
            )

        except Exception as status_error:

            print(
                "Could not mark document as failed: "
                f"{status_error}"
            )

        raise