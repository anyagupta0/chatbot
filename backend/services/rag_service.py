"""
RAG Service — Retrieval-Augmented Generation for document Q&A.
Architecture ready for FAISS/ChromaDB integration.
"""

import json
from typing import List, Dict, Optional
from services.pdf_service import get_relevant_chunks
from services.ai_service import analyze_with_context


async def answer_document_question(
    query: str,
    document_text: str,
    chunks: List[Dict],
    conversation_history: List[Dict] = None,
) -> str:
    """
    Answer a question about a document using RAG.
    1. Find relevant chunks
    2. Build context from chunks
    3. Generate answer with AI
    """
    # Get relevant chunks
    relevant = get_relevant_chunks(chunks, query, top_k=5)

    # Build context from relevant chunks
    if relevant:
        context_parts = [f"[Chunk {c['index']+1}]: {c['text']}" for c in relevant]
        context = "\n\n".join(context_parts)
    else:
        # Fall back to first portion of document
        context = document_text[:6000] if document_text else "No document content available."

    prompt = f"""Based on the following document excerpts, answer the user's question.
If the answer is not in the provided excerpts, say so clearly.
Always reference specific parts of the document when possible.

Document Context:
{context}

Question: {query}"""

    return await analyze_with_context(
        query=prompt,
        context="",
        messages=conversation_history,
    )


async def answer_dataset_question(
    query: str,
    dataset_summary: Dict,
    analysis_results: Dict = None,
    conversation_history: List[Dict] = None,
) -> str:
    """
    Answer a question about a dataset using actual analysis results.
    """
    # Keep summary compact to respect rate and token limits
    summary_compact = {
        "rows": dataset_summary.get("row_count") or dataset_summary.get("rows"),
        "columns": dataset_summary.get("column_count") or dataset_summary.get("columns"),
        "column_names": (dataset_summary.get("columns") or [])[:15] if isinstance(dataset_summary.get("columns"), list) else [],
        "missing_values": dataset_summary.get("total_missing", 0),
        "duplicates": dataset_summary.get("duplicates", 0),
    }
    if "numeric_summary" in dataset_summary:
        summary_compact["statistics"] = dataset_summary["numeric_summary"]

    context = f"Dataset Overview:\n{json.dumps(summary_compact, indent=1)}"

    if analysis_results:
        # Avoid dumping entire raw DataFrames
        clean_res = json.dumps(analysis_results, default=str)[:1500]
        context += f"\n\nKey Analysis Data:\n{clean_res}"

    return await analyze_with_context(
        query=query,
        context=context,
        messages=conversation_history,
    )
