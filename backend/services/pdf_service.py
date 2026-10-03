"""
PDF Service — Extract text, split into chunks, and analyze PDF documents.
Uses PyMuPDF (fitz) for extraction.
"""

import fitz  # PyMuPDF
import uuid
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
CHUNK_SIZE = 1500  # characters per chunk
CHUNK_OVERLAP = 200  # overlap between chunks


def validate_pdf(filename: str, file_size: int) -> Tuple[bool, str]:
    """Validate a PDF file before processing."""
    if not filename.lower().endswith(".pdf"):
        return False, "Only PDF files are supported."
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB."
    # Sanitize filename
    safe_name = re.sub(r'[^\w\-.]', '_', filename)
    return True, safe_name


def extract_text_from_pdf(file_path: str) -> Tuple[str, int, Dict]:
    """
    Extract all text from a PDF file.
    Returns: (full_text, page_count, metadata)
    """
    doc = fitz.open(file_path)
    full_text = ""
    page_count = doc.page_count
    metadata = doc.metadata or {}

    for page_num in range(page_count):
        page = doc[page_num]
        text = page.get_text("text")
        full_text += f"\n--- Page {page_num + 1} ---\n{text}"

    doc.close()

    clean_metadata = {
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "subject": metadata.get("subject", ""),
        "keywords": metadata.get("keywords", ""),
        "creator": metadata.get("creator", ""),
        "page_count": page_count,
    }

    return full_text.strip(), page_count, clean_metadata


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """
    Split text into overlapping chunks for RAG-style retrieval.
    Returns list of {text, index, start_char, end_char}
    """
    if not text:
        return []

    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end near chunk boundary
            for boundary in [". ", ".\n", "? ", "!\n", "\n\n"]:
                pos = text.rfind(boundary, start + chunk_size // 2, end + 100)
                if pos > 0:
                    end = pos + len(boundary)
                    break

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "index": index,
                "start_char": start,
                "end_char": end,
            })
            index += 1

        start = end - overlap
        if start >= len(text):
            break

    return chunks


async def process_pdf(file_content: bytes, original_filename: str, conversation_id: str = None) -> Dict:
    """
    Full PDF processing pipeline:
    1. Save file
    2. Extract text
    3. Split into chunks
    4. Return document info
    """
    # Validate
    valid, result = validate_pdf(original_filename, len(file_content))
    if not valid:
        raise ValueError(result)

    # Save file
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{result}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(file_content)

    try:
        # Extract text
        full_text, page_count, metadata = extract_text_from_pdf(str(file_path))

        # Split into chunks
        chunks = split_into_chunks(full_text)

        return {
            "id": doc_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "file_type": "pdf",
            "file_size": len(file_content),
            "page_count": page_count,
            "extracted_text": full_text,
            "chunks": chunks,
            "metadata": metadata,
            "status": "ready",
            "conversation_id": conversation_id,
        }
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        raise ValueError(f"Failed to process PDF: {str(e)}")


def get_relevant_chunks(chunks: List[Dict], query: str, top_k: int = 5) -> List[Dict]:
    """
    Simple keyword-based chunk retrieval.
    In production, replace with vector similarity search (FAISS/ChromaDB).
    """
    if not chunks:
        return []

    query_words = set(query.lower().split())

    scored_chunks = []
    for chunk in chunks:
        chunk_text = chunk.get("text", "").lower()
        # Score by keyword overlap
        score = sum(1 for word in query_words if word in chunk_text)
        # Bonus for longer matches
        for word in query_words:
            score += chunk_text.count(word) * 0.5
        scored_chunks.append((score, chunk))

    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    return [chunk for _, chunk in scored_chunks[:top_k]]
