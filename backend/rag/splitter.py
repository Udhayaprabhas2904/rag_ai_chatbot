from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from backend.config import settings



# DOCUMENT CHUNKING


def split_documents(
    documents: list[dict]
) -> list[dict]:
    """
    Split page-level PDF documents into smaller chunks
    suitable for embedding and vector search.

    Input:
        [
            {
                "page": 1,
                "content": "..."
            },
            ...
        ]

    Output:
        [
            {
                "chunk_index": 0,
                "content": "...",
                "page_number": 1,
                "metadata": {
                    "page": 1,
                    "chunk_index": 0
                }
            },
            ...
        ]

    Page information is deliberately preserved because it
    will later be used for RAG source attribution.
    """

   
    # Validate input
    
    if not documents:
        raise ValueError(
            "No documents were provided for chunking."
        )

  
    # Validate chunk configuration
   

    chunk_size = settings.CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP

    if chunk_size <= 0:
        raise ValueError(
            f"CHUNK_SIZE must be greater than 0. "
            f"Got: {chunk_size}"
        )

    if chunk_overlap < 0:
        raise ValueError(
            f"CHUNK_OVERLAP cannot be negative. "
            f"Got: {chunk_overlap}"
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"CHUNK_OVERLAP must be smaller than "
            f"CHUNK_SIZE. "
            f"Got overlap={chunk_overlap}, "
            f"size={chunk_size}"
        )

    
    # Create text splitter
    

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=chunk_size,

        chunk_overlap=chunk_overlap,

        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ],

        # Do not discard very small chunks
        # unnecessarily.
        keep_separator=True,

    )

    
    # Create chunks
   

    chunks: list[dict] = []

    chunk_counter = 0

   
    # Process each PDF page


    for document in documents:

        
        # Validate page
      

        if "page" not in document:
            raise ValueError(
                "Document is missing required 'page' field."
            )

        page_number = document["page"]

        
        # Validate content
        
        text = document.get("content", "")

        if not isinstance(text, str):
            raise ValueError(
                f"Page {page_number} content must be a string."
            )

        text = text.strip()

        if not text:
            continue

        # Split page text
        
        split_texts = splitter.split_text(text)

        
        # Create chunk records
       

        for text_chunk in split_texts:

            cleaned_chunk = text_chunk.strip()

            if not cleaned_chunk:
                continue

            chunks.append(
                {
                    "chunk_index": chunk_counter,

                    "content": cleaned_chunk,

                    "page_number": page_number,

                    "metadata": {
                        "page": page_number,
                        "chunk_index": chunk_counter
                    }
                }
            )

            chunk_counter += 1

   
    # Validate result
   

    if not chunks:

        raise ValueError(
            "No text chunks were created from the document."
        )

    
    # Logging
   

    pages_with_chunks = len(
        {
            chunk["page_number"]
            for chunk in chunks
        }
    )

    total_characters = sum(
        len(chunk["content"])
        for chunk in chunks
    )

    print(
        "Document chunking completed:"
    )

    print(
        f"  Pages processed: {pages_with_chunks}"
    )

    print(
        f"  Chunks created: {len(chunks)}"
    )

    print(
        f"  Total chunk characters: {total_characters}"
    )

    print(
        f"  Chunk size: {chunk_size}"
    )

    print(
        f"  Chunk overlap: {chunk_overlap}"
    )

    
    # Return chunks
    

    return chunks