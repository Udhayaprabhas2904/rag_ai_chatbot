from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)

from backend.config import settings



# GEMINI EMBEDDING MODEL


embeddings_model = GoogleGenerativeAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    output_dimensionality=settings.EMBEDDING_DIMENSION,
)



# SINGLE TEXT EMBEDDING


async def generate_embedding(
    text: str,
) -> list[float]:
    """
    Generate a Gemini embedding for a single text.

    Returns:
        list[float]

    Raises:
        ValueError:
            If the input is empty or the embedding dimension
            is incorrect.
    """

    
    # Validate input
    

    if not isinstance(text, str):
        raise ValueError(
            "Text must be a string."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "Text cannot be empty."
        )

    
    # Generate Gemini embedding
    

    try:

        embedding = await embeddings_model.aembed_query(
            text
        )

    except Exception as error:

        raise RuntimeError(
            "Gemini embedding generation failed: "
            f"{error}"
        ) from error

   
    # Validate response
    

    if not embedding:
        raise ValueError(
            "Gemini returned an empty embedding."
        )

    expected_dimension = (
        settings.EMBEDDING_DIMENSION
    )

    actual_dimension = len(embedding)

    if actual_dimension != expected_dimension:

        raise ValueError(
            "Embedding dimension mismatch. "
            f"Expected {expected_dimension}, "
            f"got {actual_dimension}."
        )

    return embedding



# MULTIPLE TEXT EMBEDDINGS


async def generate_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate Gemini embeddings for multiple text chunks.

    The returned list preserves the exact order of the
    input texts.

    Input:
        [
            "chunk 1",
            "chunk 2",
            "chunk 3"
        ]

    Output:
        [
            [...],
            [...],
            [...]
        ]
    """

    # Validate input
    

    if not isinstance(texts, list):
        raise ValueError(
            "texts must be a list of strings."
        )

    if not texts:
        return []

  
    # Clean texts WITHOUT silently removing entries
    

    cleaned_texts: list[str] = []

    for index, text in enumerate(texts):

        if not isinstance(text, str):

            raise ValueError(
                f"Text at index {index} must be a string."
            )

        cleaned_text = text.strip()

        if not cleaned_text:

            raise ValueError(
                f"Text at index {index} is empty."
            )

        cleaned_texts.append(
            cleaned_text
        )

   
    # Generate Gemini embeddings
    

    try:

        embeddings = (
            await embeddings_model.aembed_documents(
                cleaned_texts
            )
        )

    except Exception as error:

        raise RuntimeError(
            "Gemini batch embedding generation failed: "
            f"{error}"
        ) from error

   
    # Validate number of embeddings
   

    if not embeddings:

        raise ValueError(
            "Gemini returned no embeddings."
        )

    if len(embeddings) != len(cleaned_texts):

        raise ValueError(
            "Embedding count mismatch. "
            f"Expected {len(cleaned_texts)}, "
            f"got {len(embeddings)}."
        )

   
    # Validate every embedding dimension
    

    expected_dimension = (
        settings.EMBEDDING_DIMENSION
    )

    for index, embedding in enumerate(
        embeddings
    ):

        if not embedding:

            raise ValueError(
                f"Gemini returned an empty embedding "
                f"at index {index}."
            )

        actual_dimension = len(embedding)

        if actual_dimension != expected_dimension:

            raise ValueError(
                "Embedding dimension mismatch at "
                f"index {index}. "
                f"Expected {expected_dimension}, "
                f"got {actual_dimension}."
            )

  
    # Logging
    

    print(
        "Gemini embedding generation completed:"
    )

    print(
        f"  Texts: {len(cleaned_texts)}"
    )

    print(
        f"  Embeddings: {len(embeddings)}"
    )

    print(
        f"  Dimension: {expected_dimension}"
    )

    print(
        f"  Model: {settings.EMBEDDING_MODEL}"
    )

    
    # Return
    
    return embeddings