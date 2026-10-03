"""
Report Service — Generate structured research reports.
"""

import uuid
import json
from typing import List, Dict, Optional
from services.ai_service import generate_response
from models.database import save_report


REPORT_PROMPT = """Generate a comprehensive research report based on the conversation and any research/analysis results provided.

The report should follow this structure:

# [Title]

## Executive Summary
A brief overview of the research topic and key findings.

## Introduction
Background context and research motivation.

## Literature Review
Summary of relevant papers and existing research.

## Methodology
Research approach and methods used.

## Analysis & Findings
Detailed analysis results with supporting data.

## Research Gaps
Identified gaps in the current literature.

## Conclusion
Summary of findings and implications.

## References
List all cited sources with full details.

---

Important:
- Only include information that was actually discussed or found during the conversation
- Never fabricate citations or sources
- Use academic language but keep it accessible
- Include actual data/statistics when available
- Clearly distinguish between established findings and AI-generated analysis"""


async def generate_report(
    conversation_id: str,
    messages: List[Dict],
    title: str = None,
    report_type: str = "research",
) -> Dict:
    """Generate a structured research report from conversation history."""

    # Build context from conversation
    context_messages = [
        {"role": "system", "content": REPORT_PROMPT}
    ]

    # Add conversation history
    for msg in messages[-30:]:  # Last 30 messages for context
        context_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    context_messages.append({
        "role": "user",
        "content": "Based on our conversation above, generate a comprehensive research report. "
                   "Include all research findings, data analysis results, and citations that were discussed.",
    })

    # Generate report content
    report_content = await generate_response(context_messages)

    if not title:
        title = f"Research Report - {conversation_id[:8]}"

    report_id = str(uuid.uuid4())

    # Save to database
    await save_report(report_id, conversation_id, title, report_content, report_type)

    return {
        "id": report_id,
        "title": title,
        "content": report_content,
        "type": report_type,
        "conversation_id": conversation_id,
    }
