"""
Document Routes — Upload and analyze PDF documents.
"""

import uuid
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional
from services.pdf_service import process_pdf, get_relevant_chunks
from services.rag_service import answer_document_question
from models.database import save_document, get_document, get_documents_by_conversation

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentQuestion(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
):
    """Upload and process a PDF document."""
    try:
        # Read file content
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum 50 MB.")

        # Process PDF
        result = await process_pdf(content, file.filename, conversation_id)

        # Save to database
        await save_document(
            doc_id=result["id"],
            conversation_id=conversation_id,
            filename=result["filename"],
            original_filename=result["original_filename"],
            file_type=result["file_type"],
            file_size=result["file_size"],
            page_count=result["page_count"],
            extracted_text=result["extracted_text"],
            chunks=result["chunks"],
            status=result["status"],
        )

        return {
            "id": result["id"],
            "filename": result["original_filename"],
            "file_size": result["file_size"],
            "page_count": result["page_count"],
            "status": result["status"],
            "metadata": result["metadata"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document.")


@router.post("/{doc_id}/ask")
async def ask_document(doc_id: str, question: DocumentQuestion):
    """Ask a question about an uploaded document."""
    try:
        doc = await get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks = json.loads(doc.get("chunks", "[]")) if isinstance(doc.get("chunks"), str) else doc.get("chunks", [])
        text = doc.get("extracted_text", "")

        answer = await answer_document_question(
            question.question, text, chunks
        )

        return {
            "answer": answer,
            "document_id": doc_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}")
async def get_doc(doc_id: str):
    """Get document info."""
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc["id"],
        "filename": doc["original_filename"],
        "file_size": doc["file_size"],
        "page_count": doc["page_count"],
        "status": doc["status"],
    }
