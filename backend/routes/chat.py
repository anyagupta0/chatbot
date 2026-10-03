"""
Chat Routes — Main chat endpoints with AI integration.
"""

import uuid
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from models.database import (
    create_conversation, get_conversations, get_conversation,
    update_conversation, delete_conversation, add_message,
    get_messages, search_conversations, get_documents_by_conversation,
    get_datasets_by_conversation,
)
from services.ai_service import generate_response, generate_response_stream
from services.research_service import search_and_save
from services.rag_service import answer_document_question, answer_dataset_question
from services.dataset_service import (
    get_dataset_summary, execute_analysis, generate_chart_data,
    _dataframe_cache, load_dataframe,
)
from services.pdf_service import get_relevant_chunks

router = APIRouter(prefix="/api", tags=["chat"])


# ─── Models ────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[str] = None
    mode: Optional[str] = "chat"  # chat, research, analyze
    document_id: Optional[str] = None
    dataset_id: Optional[str] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    content: str
    role: str = "assistant"
    metadata: Dict = {}


# ─── Chat ──────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Send a message and get AI response."""
    try:
        # Create or get conversation
        conversation_id = message.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            # Generate title from first message
            title = message.content[:60].strip()
            if len(message.content) > 60:
                title += "..."
            await create_conversation(conversation_id, title)

        # Save user message
        user_msg_id = str(uuid.uuid4())
        await add_message(user_msg_id, conversation_id, "user", message.content)

        # Get conversation history
        history = await get_messages(conversation_id)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]

        response_metadata = {}

        # Determine response type and generate
        content_lower = message.content.lower()

        # Check if user is asking about an uploaded document
        if message.document_id:
            response_content = await _handle_document_question(
                message.content, message.document_id, conversation_id, messages
            )
            response_metadata["type"] = "document_analysis"

        # Check if user is asking about a dataset
        elif message.dataset_id:
            response_content, chart_data = await _handle_dataset_question(
                message.content, message.dataset_id, conversation_id, messages
            )
            response_metadata["type"] = "dataset_analysis"
            if chart_data:
                response_metadata["chart"] = chart_data

        # Research mode
        elif message.mode == "research" or any(kw in content_lower for kw in
            ["find papers", "search papers", "research papers", "find research",
             "search research", "literature review", "find studies", "recent papers"]):
            response_content, papers = await _handle_research(
                message.content, conversation_id, messages
            )
            response_metadata["type"] = "research"
            response_metadata["papers"] = papers

        # Check for dataset analysis requests without explicit dataset_id
        elif any(kw in content_lower for kw in
            ["analyze dataset", "analyze data", "show chart", "create chart",
             "statistics", "correlation", "outliers"]):
            # Check if there's a dataset in this conversation
            datasets = await get_datasets_by_conversation(conversation_id)
            if datasets:
                dataset_id = datasets[0]["id"]
                response_content, chart_data = await _handle_dataset_question(
                    message.content, dataset_id, conversation_id, messages
                )
                response_metadata["type"] = "dataset_analysis"
                if chart_data:
                    response_metadata["chart"] = chart_data
            else:
                response_content = await generate_response(messages)

        # Check for document analysis requests without explicit document_id
        elif any(kw in content_lower for kw in
            ["summarize", "analyze document", "analyze paper", "pdf", "document",
             "what methodology", "key findings", "limitations", "research gap"]):
            docs = await get_documents_by_conversation(conversation_id)
            if docs:
                response_content = await _handle_document_question(
                    message.content, docs[0]["id"], conversation_id, messages
                )
                response_metadata["type"] = "document_analysis"
            else:
                response_content = await generate_response(messages)

        # General chat
        else:
            response_content = await generate_response(messages)

        # Save assistant message
        assistant_msg_id = str(uuid.uuid4())
        await add_message(assistant_msg_id, conversation_id, "assistant", 
                          response_content, response_metadata)

        # Update conversation timestamp
        await update_conversation(conversation_id)

        return ChatResponse(
            message_id=assistant_msg_id,
            conversation_id=conversation_id,
            content=response_content,
            metadata=response_metadata,
        )

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_research(query: str, conversation_id: str, messages: List[Dict]):
    """Handle research queries."""
    # Search for papers
    papers = await search_and_save(query, conversation_id, limit=5)

    # Build context with paper info
    papers_context = "\n\n".join([
        f"Paper {i+1}: {p['title']}\n"
        f"Authors: {', '.join(p.get('authors', []))}\n"
        f"Year: {p.get('year', 'N/A')}\n"
        f"Source: {p.get('source', 'N/A')}\n"
        f"Citations: {p.get('citations', 0)}\n"
        f"Abstract: {p.get('abstract', 'N/A')[:500]}"
        for i, p in enumerate(papers)
    ])

    research_prompt = f"""The user asked: {query}

I found the following research papers. Analyze and summarize them:

{papers_context}

Provide:
1. A summary of the key findings across these papers
2. Common themes and methodologies
3. Any notable trends or gaps
4. Proper citations for each paper mentioned

IMPORTANT: Only reference papers that are actually listed above. Do not invent additional papers."""

    messages_with_research = messages + [{"role": "user", "content": research_prompt}]
    response = await generate_response(messages_with_research)

    # Serialize papers for frontend
    serialized_papers = []
    for p in papers:
        serialized_papers.append({
            "id": p.get("id", ""),
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year"),
            "abstract": p.get("abstract", "")[:300],
            "source": p.get("source", ""),
            "citations": p.get("citations", 0),
            "url": p.get("url", ""),
            "doi": p.get("doi", ""),
            "keywords": p.get("keywords", []),
        })

    return response, serialized_papers


async def _handle_document_question(query: str, doc_id: str, conversation_id: str, messages: List[Dict]):
    """Handle document Q&A."""
    from models.database import get_document
    doc = await get_document(doc_id)
    if not doc:
        return "I couldn't find that document. Please upload it again."

    chunks = json.loads(doc.get("chunks", "[]")) if isinstance(doc.get("chunks"), str) else doc.get("chunks", [])
    text = doc.get("extracted_text", "")

    return await answer_document_question(query, text, chunks, messages)


async def _handle_dataset_question(query: str, dataset_id: str, conversation_id: str, messages: List[Dict]):
    """Handle dataset analysis questions."""
    from models.database import get_dataset
    from pathlib import Path

    dataset = await get_dataset(dataset_id)
    if not dataset:
        return "I couldn't find that dataset. Please upload it again.", None

    # Ensure DataFrame is loaded
    if dataset_id not in _dataframe_cache:
        file_path = Path(__file__).parent.parent / "data" / "uploads" / dataset["filename"]
        if file_path.exists():
            load_dataframe(dataset_id, str(file_path))
        else:
            return "The dataset file could not be found.", None

    # Get summary
    summary = get_dataset_summary(dataset_id)

    # Determine what analysis to run based on query
    content_lower = query.lower()
    chart_data = None
    analysis_result = None

    # Parse dataset columns
    columns = json.loads(dataset.get("columns", "[]")) if isinstance(dataset.get("columns"), str) else dataset.get("columns", [])

    if any(kw in content_lower for kw in ["chart", "graph", "plot", "visuali"]):
        # Try to determine chart parameters
        chart_type = "bar"
        if "line" in content_lower:
            chart_type = "line"
        elif "pie" in content_lower:
            chart_type = "pie"
        elif "scatter" in content_lower:
            chart_type = "scatter"
        elif "histogram" in content_lower:
            chart_type = "histogram"
        elif "correlation" in content_lower:
            chart_type = "correlation"

        # Try to find column names mentioned in query
        mentioned_cols = [c for c in columns if c.lower() in content_lower]
        x_col = mentioned_cols[0] if len(mentioned_cols) > 0 else (columns[0] if columns else None)
        y_col = mentioned_cols[1] if len(mentioned_cols) > 1 else (columns[1] if len(columns) > 1 else None)

        chart_data = generate_chart_data(dataset_id, chart_type, x_col, y_col)

    elif any(kw in content_lower for kw in ["missing", "null", "empty"]):
        analysis_result = execute_analysis(dataset_id, "missing_values")
    elif any(kw in content_lower for kw in ["duplicate"]):
        analysis_result = execute_analysis(dataset_id, "duplicates")
    elif any(kw in content_lower for kw in ["correlation", "correlat"]):
        analysis_result = execute_analysis(dataset_id, "correlation")
    elif any(kw in content_lower for kw in ["outlier"]):
        # Find a numeric column
        numeric_cols = [c for c in columns if c.lower() in content_lower]
        if not numeric_cols:
            numeric_cols = columns[:1]
        if numeric_cols:
            analysis_result = execute_analysis(dataset_id, "outliers", {"column": numeric_cols[0]})
    elif any(kw in content_lower for kw in ["average", "mean", "sum", "total", "max", "min"]):
        op = "mean"
        if "sum" in content_lower or "total" in content_lower:
            op = "sum"
        elif "max" in content_lower:
            op = "max"
        elif "min" in content_lower:
            op = "min"

        mentioned_cols = [c for c in columns if c.lower() in content_lower]
        if mentioned_cols:
            analysis_result = execute_analysis(dataset_id, "aggregate", 
                                                {"column": mentioned_cols[0], "operation": op})
    else:
        # Default: full summary
        analysis_result = summary

    response = await answer_dataset_question(query, summary, analysis_result, messages)

    return response, chart_data


# ─── Conversations CRUD ───────────────────────────────────────

@router.get("/chats")
async def list_chats():
    """List all conversations."""
    conversations = await get_conversations()
    return {"conversations": conversations}


@router.post("/chats")
async def create_chat(data: ConversationCreate):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    await create_conversation(conversation_id, data.title)
    return {"id": conversation_id, "title": data.title}


@router.get("/chats/{conversation_id}")
async def get_chat(conversation_id: str):
    """Get conversation with messages."""
    conversation = await get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await get_messages(conversation_id)
    docs = await get_documents_by_conversation(conversation_id)
    datasets = await get_datasets_by_conversation(conversation_id)

    return {
        "conversation": conversation,
        "messages": messages,
        "documents": docs,
        "datasets": datasets,
    }


@router.put("/chats/{conversation_id}")
async def rename_chat(conversation_id: str, data: ConversationUpdate):
    """Rename a conversation."""
    await update_conversation(conversation_id, data.title)
    return {"success": True}


@router.delete("/chats")
async def clear_all_chats():
    """Clear all chat history, documents, datasets, papers, and reports."""
    from models.database import get_db
    from services.dataset_service import _dataframe_cache
    db = await get_db()
    try:
        for table in ['messages', 'conversations', 'documents', 'datasets', 'research_papers', 'reports']:
            await db.execute(f"DELETE FROM {table}")
        await db.commit()
        _dataframe_cache.clear()
        return {"success": True}
    finally:
        await db.close()


@router.delete("/chats/{conversation_id}")
async def remove_chat(conversation_id: str):
    """Delete a conversation."""
    await delete_conversation(conversation_id)
    return {"success": True}


@router.get("/chats/search/{query}")
async def search_chats(query: str):
    """Search conversations."""
    results = await search_conversations(query)
    return {"conversations": results}


# ─── Settings ─────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    provider: Optional[str] = "openai"
    model: Optional[str] = "gpt-4o"
    base_url: Optional[str] = "https://api.openai.com/v1"


@router.get("/settings")
async def get_settings():
    """Get active AI provider configuration."""
    from services.ai_service import reset_ai_provider
    import os
    key = os.getenv("AI_API_KEY", "")
    masked = f"{key[:7]}...{key[-4:]}" if len(key) > 11 else ("***" if key else "")
    return {
        "provider": os.getenv("AI_PROVIDER", "openai"),
        "model": os.getenv("AI_MODEL", "gpt-4o"),
        "base_url": os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
        "has_key": bool(key),
        "masked_key": masked,
        "demo_mode": not bool(key),
    }


@router.post("/settings")
async def update_settings(settings: SettingsUpdate):
    """Update AI provider settings and save to .env."""
    import os
    from pathlib import Path
    from services.ai_service import reset_ai_provider

    if settings.api_key is not None:
        os.environ["AI_API_KEY"] = settings.api_key.strip()
    if settings.provider is not None:
        os.environ["AI_PROVIDER"] = settings.provider.strip()
    if settings.model is not None:
        os.environ["AI_MODEL"] = settings.model.strip()
    if settings.base_url is not None:
        os.environ["AI_BASE_URL"] = settings.base_url.strip()

    # Save to backend/.env
    env_path = Path(__file__).parent.parent / ".env"
    env_content = f"""AI_API_KEY={os.environ.get("AI_API_KEY", "")}
AI_MODEL={os.environ.get("AI_MODEL", "gpt-4o")}
AI_PROVIDER={os.environ.get("AI_PROVIDER", "openai")}
AI_BASE_URL={os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")}
DATABASE_URL={os.environ.get("DATABASE_URL", "sqlite:///./data/research_ai.db")}
MAX_FILE_SIZE_MB={os.environ.get("MAX_FILE_SIZE_MB", "50")}
ALLOWED_ORIGINS={os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")}
"""
    env_path.write_text(env_content, encoding="utf-8")

    # Reset cached provider instance
    reset_ai_provider()

    return {
        "success": True,
        "provider": os.environ.get("AI_PROVIDER"),
        "model": os.environ.get("AI_MODEL"),
        "has_key": bool(os.environ.get("AI_API_KEY")),
        "demo_mode": not bool(os.environ.get("AI_API_KEY")),
    }
