"""
Report Routes — Generate research reports.
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.report_service import generate_report
from models.database import get_messages, get_conversation

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    conversation_id: str
    title: Optional[str] = None
    report_type: Optional[str] = "research"


@router.post("/generate")
async def create_report(request: ReportRequest):
    """Generate a research report from conversation history."""
    try:
        conversation = await get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = await get_messages(request.conversation_id)
        if not messages:
            raise HTTPException(status_code=400, detail="No messages in this conversation")

        report = await generate_report(
            request.conversation_id,
            messages,
            request.title,
            request.report_type,
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CompareRequest(BaseModel):
    paper_ids: list = Field(..., min_length=2, max_length=5)
    conversation_id: Optional[str] = None


@router.post("/compare")
async def compare_papers(request: CompareRequest):
    """Compare multiple research papers."""
    from services.ai_service import generate_response
    from models.database import get_db

    try:
        db = await get_db()
        try:
            papers = []
            for pid in request.paper_ids:
                cursor = await db.execute(
                    "SELECT * FROM research_papers WHERE id = ?", (pid,)
                )
                row = await cursor.fetchone()
                if row:
                    papers.append(dict(row))
        finally:
            await db.close()

        if len(papers) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 valid papers to compare")

        # Build comparison context
        comparison_text = ""
        for i, p in enumerate(papers, 1):
            authors = json.loads(p.get("authors", "[]")) if isinstance(p.get("authors"), str) else p.get("authors", [])
            comparison_text += f"""
Paper {i}: {p.get('title', 'Untitled')}
Authors: {', '.join(authors)}
Year: {p.get('year', 'N/A')}
Source: {p.get('source', 'N/A')}
Citations: {p.get('citations', 0)}
Abstract: {p.get('abstract', 'N/A')}
Keywords: {json.loads(p.get('keywords', '[]')) if isinstance(p.get('keywords'), str) else p.get('keywords', [])}
---
"""

        messages = [{
            "role": "user",
            "content": f"""Compare the following research papers in detail:

{comparison_text}

Provide:
1. A comparison table covering: Year, Methodology, Key Findings, Limitations
2. Similarities between the papers
3. Differences in approach and findings
4. Common research gaps
5. Recommendations for future research

IMPORTANT: Only compare information that is actually available. Do not invent details."""
        }]

        response = await generate_response(messages)

        return {
            "comparison": response,
            "papers": [{
                "id": p.get("id"),
                "title": p.get("title"),
                "year": p.get("year"),
                "source": p.get("source"),
            } for p in papers],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
