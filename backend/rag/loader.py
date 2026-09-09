from pathlib import Path

from pypdf import PdfReader



# TEXT CLEANING


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text while preserving useful
    paragraph and line structure.

    The goal is to make the text suitable for:
        PDF -> text -> chunking -> embeddings
    """

    if not text:
        return ""

    
    # Normalize line endings
    

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

   
    # Remove null characters
   

    text = text.replace("\x00", "")

    
    # Normalize spaces/tabs on each line
    

    lines = []

    for line in text.split("\n"):

        # Replace tabs with spaces
        line = line.replace("\t", " ")

        # Collapse repeated spaces
        line = " ".join(line.split())

        lines.append(line)

    
    # Remove excessive empty lines
   

    cleaned_lines = []

    previous_empty = False

    for line in lines:

        if not line:

            if previous_empty:
                continue

            previous_empty = True

        else:

            previous_empty = False

        cleaned_lines.append(line)

   
    # Final cleanup
    

    return "\n".join(cleaned_lines).strip()



# PDF LOADER


def load_pdf(file_path: str) -> list[dict]:
    """
    Extract readable text from a PDF page-by-page.

    Returns:

    [
        {
            "page": 1,
            "content": "Text from page 1..."
        },
        {
            "page": 2,
            "content": "Text from page 2..."
        }
    ]

    Important:
        Page numbers are preserved so that later RAG
        responses can provide source/page attribution.
    """

    path = Path(file_path)

    
    # 1. Validate path
    

    if not path.exists():

        raise FileNotFoundError(
            f"PDF not found: {file_path}"
        )

    if not path.is_file():

        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    
    # 2. Validate extension
    

    if path.suffix.lower() != ".pdf":

        raise ValueError(
            f"Expected a PDF file, got: {path.name}"
        )

   
    # 3. Read PDF
   

    try:

        reader = PdfReader(str(path))

    except Exception as error:

        raise ValueError(
            f"Unable to read PDF '{path.name}': {error}"
        ) from error

    
    # 4. Check encrypted PDF
    

    if reader.is_encrypted:

        try:

            decrypted = reader.decrypt("")

        except Exception as error:

            raise ValueError(
                f"PDF '{path.name}' is encrypted and could "
                f"not be opened: {error}"
            ) from error

        if not decrypted:

            raise ValueError(
                f"PDF '{path.name}' is password protected. "
                f"Please upload an unprotected PDF."
            )

    
    # 5. Check pages
   

    total_pages = len(reader.pages)

    if total_pages == 0:

        raise ValueError(
            f"PDF '{path.name}' contains no pages."
        )

    print(
        f"Reading PDF: {path.name}"
    )

    print(
        f"Total pages: {total_pages}"
    )

   
    # 6. Extract text page-by-page
    

    documents: list[dict] = []

    empty_pages = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        try:

            raw_text = page.extract_text() or ""

        except Exception as error:

            raise ValueError(
                f"Failed to extract text from page "
                f"{page_number} of '{path.name}': {error}"
            ) from error

       
        # Clean extracted text
       

        text = clean_text(raw_text)

       
        # Ignore pages with no readable text
        

        if not text:

            empty_pages += 1

            print(
                f"Page {page_number}: "
                f"no readable text"
            )

            continue

       
        # Store page
        
        documents.append(
            {
                "page": page_number,
                "content": text,
            }
        )

        print(
            f"Page {page_number}: "
            f"{len(text)} characters"
        )

    
    # 7. Make sure text was extracted
    

    if not documents:

        raise ValueError(
            f"No readable text was found in PDF "
            f"'{path.name}'. "
            f"The PDF may be scanned/image-only or "
            f"contain unsupported text encoding."
        )

   
    # 8. Summary
    

    total_characters = sum(
        len(document["content"])
        for document in documents
    )

    print(
        "PDF extraction completed:"
    )

    print(
        f"  Pages: {total_pages}"
    )

    print(
        f"  Pages with text: {len(documents)}"
    )

    print(
        f"  Empty pages: {empty_pages}"
    )

    print(
        f"  Extracted characters: {total_characters}"
    )

    
    # 9. Return extracted pages
    

    return documents