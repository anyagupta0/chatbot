"""
Research Routes — Search academic papers.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.research_service import search_papers, search_and_save

router = APIRouter(prefix="/api/research", tags=["research"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    sources: Optional[List[str]] = None
    limit: Optional[int] = 10
    conversation_id: Optional[str] = None


@router.post("/search")
async def search(request: SearchRequest):
    """Search for research papers across multiple databases."""
    try:
        if request.conversation_id:
            papers = await search_and_save(
                request.query, request.conversation_id, 
                request.sources, request.limit
            )
        else:
            papers = await search_papers(
                request.query, request.sources, request.limit
            )

        return {
            "query": request.query,
            "count": len(papers),
            "papers": papers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
