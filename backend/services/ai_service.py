"""
AI Service Abstraction Layer
Supports multiple LLM providers through a unified interface.
Provider can be swapped by changing AI_PROVIDER env variable.
"""

import os
import json
import asyncio
import httpx
from typing import List, Dict, Optional, AsyncGenerator
from dotenv import load_dotenv

load_dotenv()


class AIProvider:
    """Base class for AI providers."""

    async def generate(self, messages: List[Dict], **kwargs) -> str:
        raise NotImplementedError

    async def generate_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError


def _prepare_messages(messages: List[Dict], max_history_turns: int = 8, max_chars: int = 2500) -> List[Dict]:
    """Trim conversation history to avoid exceeding provider token and rate limits."""
    system_msgs = [m for m in messages if m.get("role") == "system"]
    chat_msgs = [m for m in messages if m.get("role") != "system"]

    # Keep only the last N turns
    recent_msgs = chat_msgs[-max_history_turns:] if len(chat_msgs) > max_history_turns else chat_msgs

    trimmed = []
    for m in recent_msgs:
        content = str(m.get("content", ""))
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... [content condensed for context limits]"
        trimmed.append({"role": m.get("role", "user"), "content": content})

    return system_msgs + trimmed


class OpenAIProvider(AIProvider):
    """OpenAI-compatible provider (works with OpenAI, Groq, Gemini, local models, etc.)"""

    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY", "")
        self.model = os.getenv("AI_MODEL", "gpt-4")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")

    async def generate(self, messages: List[Dict], **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.7)
        # Default to 1200 max_tokens to prevent exceeding rate limits on free tiers
        max_tokens = kwargs.get("max_tokens", 1200)

        prepared_msgs = _prepare_messages(messages, max_history_turns=6, max_chars=2500)
        current_model = self.model

        # Fallback candidates if rate limits or payload size is exceeded
        fallback_models = []
        if "120b" in current_model.lower():
            fallback_models = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

        models_to_try = [current_model] + fallback_models

        last_error = None
        for attempt_model in models_to_try:
            for retry in range(2):
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": attempt_model,
                                "messages": prepared_msgs,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                            },
                        )

                        # Handle rate limit 429
                        if response.status_code == 429:
                            last_error = "Rate limit reached (429)."
                            await asyncio.sleep(2.0 * (retry + 1))
                            max_tokens = min(max_tokens, 800)
                            continue

                        # Handle payload too large 413
                        if response.status_code == 413:
                            last_error = "Payload too large (413)."
                            # Aggressively reduce to last 2 messages
                            prepared_msgs = _prepare_messages(messages, max_history_turns=2, max_chars=1200)
                            max_tokens = min(max_tokens, 600)
                            continue

                        response.raise_for_status()
                        data = response.json()
                        return data["choices"][0]["message"]["content"]

                except httpx.HTTPStatusError as e:
                    last_error = f"API error: {e.response.status_code} - {e.response.text[:200]}"
                    if e.response.status_code in (413, 429):
                        await asyncio.sleep(1.5)
                        continue
                    break
                except Exception as e:
                    last_error = str(e)
                    break

        # If all retries and fallback models failed, raise clean user-facing error
        raise RuntimeError(
            f"The AI provider was unable to fulfill the request. {last_error or 'Please try again in a few seconds.'}"
        )

    async def generate_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        # For stream requests, fallback to generate
        full_text = await self.generate(messages, **kwargs)
        yield full_text


class DemoProvider(AIProvider):
    """Demo provider for testing without an API key."""

    DEMO_RESPONSES = {
        "research": """Based on my analysis, here are the key findings from recent research:

## Key Papers Found

1. **Advances in Neural Architecture Search** (2025)
   - *Authors:* Zhang et al.
   - *Published in:* NeurIPS 2025
   - Key contribution: Novel efficient NAS method reducing search time by 60%

2. **Transformer Models for Scientific Discovery** (2024)
   - *Authors:* Johnson, Smith, et al.
   - *Published in:* Nature Machine Intelligence
   - Key contribution: Framework for applying transformers to scientific datasets

3. **Federated Learning in Healthcare** (2025)
   - *Authors:* Patel, Lee, et al.
   - *Published in:* JAMA AI
   - Key contribution: Privacy-preserving ML for medical records

## Summary

The field is rapidly evolving with emphasis on efficiency, privacy, and real-world applications. Key trends include:

- **Efficiency improvements** in model training and architecture search
- **Privacy-preserving techniques** gaining traction in healthcare
- **Cross-domain applications** of transformer architectures

> ⚠️ *Note: This is demo data. Connect an AI provider for real research results.*""",

        "analyze": """## Document Analysis

### Overview
This document presents a comprehensive study on the given topic. Here's a structured analysis:

### Research Objective
The paper aims to investigate the relationship between the key variables and their impact on the field.

### Methodology
- **Design:** Mixed-methods approach combining quantitative analysis with qualitative insights
- **Data Collection:** Survey of 500+ participants combined with longitudinal data
- **Analysis Framework:** Statistical modeling with validation through expert review

### Key Findings
1. Strong positive correlation found between variables A and B (r = 0.78)
2. Intervention group showed 34% improvement over control
3. Three novel patterns identified in the data

### Limitations
- Sample size limited to specific geographic region
- Temporal scope restricted to 2 years
- Self-reported data may contain bias

### Research Gap
The paper does not address cross-cultural variations or long-term effects beyond the study period.

> ⚠️ *Note: This is a demo analysis. Upload a real document and connect an AI provider for actual analysis.*""",

        "dataset": """## Dataset Analysis Results

### Overview
Your dataset has been analyzed successfully. Here are the key insights:

### Statistical Summary
| Metric | Value |
|--------|-------|
| Total Records | 10,245 |
| Features | 14 |
| Missing Values | 42 (0.4%) |
| Duplicates | 18 |

### Key Findings
1. **Revenue Trend:** Steady 12% growth quarter-over-quarter
2. **Top Category:** Electronics accounts for 35% of total sales
3. **Seasonal Pattern:** Peak sales in Q4 (November-December)
4. **Correlation:** Strong correlation between marketing spend and revenue (r=0.82)

### Recommendations
- Focus marketing budget on Q3 to boost Q4 sales
- Investigate the 42 missing values in the customer_age column
- Consider removing 18 duplicate entries for cleaner analysis

> ⚠️ *Note: This is demo data. Upload a real dataset for actual analysis.*""",

        "default": """I'd be happy to help you with that! Here's what I can tell you:

{content}

### What I Can Help With
- 🔎 **Research Papers** — Search and analyze academic papers
- 📄 **Document Analysis** — Upload and analyze PDFs
- 📊 **Data Analysis** — Upload CSV/XLSX datasets for insights
- 🔬 **Paper Comparison** — Compare multiple papers
- 📝 **Report Generation** — Create structured research reports

Feel free to ask me anything or try one of the quick actions!

> ⚠️ *This is running in demo mode. Set your AI_API_KEY to connect to a real AI provider.*"""
    }

    async def generate(self, messages: List[Dict], **kwargs) -> str:
        # Analyze the last user message to determine response type
        last_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_message = msg["content"].lower()
                break

        if any(word in last_message for word in ["search", "find", "papers", "research", "literature"]):
            return self.DEMO_RESPONSES["research"]
        elif any(word in last_message for word in ["analyze", "analysis", "document", "pdf", "summarize"]):
            return self.DEMO_RESPONSES["analyze"]
        elif any(word in last_message for word in ["dataset", "csv", "data", "chart", "statistics", "correlation"]):
            return self.DEMO_RESPONSES["dataset"]
        else:
            # Generate a contextual default response
            return self.DEMO_RESPONSES["default"].replace(
                "{content}",
                f"Regarding your question about \"{last_message[:100]}\":\n\nThis is a fascinating topic that spans multiple areas of research. "
                f"In a fully connected setup, I would search academic databases, analyze relevant papers, "
                f"and provide you with comprehensive insights backed by real citations."
            )

    async def generate_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        response = await self.generate(messages, **kwargs)
        # Simulate streaming by yielding chunks
        words = response.split(" ")
        chunk = ""
        for i, word in enumerate(words):
            chunk += word + " "
            if len(chunk) > 20 or i == len(words) - 1:
                yield chunk
                chunk = ""


# ─── Factory ───────────────────────────────────────────────────

_provider_instance: Optional[AIProvider] = None


def get_ai_provider() -> AIProvider:
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = os.getenv("AI_PROVIDER", "openai").lower()
    api_key = os.getenv("AI_API_KEY", "")

    if not api_key:
        print("[INFO] No AI_API_KEY found. Running in demo mode.")
        _provider_instance = DemoProvider()
    elif provider_name == "openai":
        _provider_instance = OpenAIProvider()
    else:
        # Default to OpenAI-compatible
        _provider_instance = OpenAIProvider()

    return _provider_instance


def reset_ai_provider():
    global _provider_instance
    _provider_instance = None


# ─── High-level API ────────────────────────────────────────────

SYSTEM_PROMPT = """You are ResearchAI, an intelligent research assistant specializing in academic research, data analysis, and scientific discovery.

Your capabilities:
- Search and analyze research papers from academic databases
- Analyze uploaded PDFs and extract key information
- Analyze datasets (CSV/XLSX) and generate insights
- Compare research papers and identify gaps
- Generate structured research reports
- Provide citations for all claims

Guidelines:
- Be thorough but concise
- Use structured formatting (headings, lists, tables)
- Always cite sources when discussing research
- Never fabricate citations or paper metadata
- When analyzing data, show actual numbers and statistics
- Acknowledge limitations in your analysis
- Use academic but accessible language"""


async def generate_response(messages: List[Dict], system_prompt: str = None, **kwargs) -> str:
    provider = get_ai_provider()
    full_messages = [
        {"role": "system", "content": system_prompt or SYSTEM_PROMPT}
    ] + messages
    return await provider.generate(full_messages, **kwargs)


async def generate_response_stream(messages: List[Dict], system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
    provider = get_ai_provider()
    full_messages = [
        {"role": "system", "content": system_prompt or SYSTEM_PROMPT}
    ] + messages
    async for chunk in provider.generate_stream(full_messages, **kwargs):
        yield chunk


async def analyze_with_context(query: str, context: str, messages: List[Dict] = None, **kwargs) -> str:
    """Generate a response with additional context (document text, dataset summary, etc.)"""
    provider = get_ai_provider()
    system = SYSTEM_PROMPT + (f"\n\nContext:\n{context[:2500]}" if context else "")
    full_messages = [{"role": "system", "content": system}]
    if messages:
        # Keep only the last 2 messages of history for heavy context queries
        full_messages.extend(messages[-2:])
    full_messages.append({"role": "user", "content": query})
    return await provider.generate(full_messages, **kwargs)
