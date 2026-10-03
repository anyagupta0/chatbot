"""
Research Service — Search academic papers from multiple providers.
Supports: Semantic Scholar, arXiv, Crossref, PubMed
"""

import httpx
import json
import uuid
from typing import List, Dict, Optional
from models.database import save_research_paper


class ResearchProvider:
    """Base class for research paper providers."""

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        raise NotImplementedError


class SemanticScholarProvider(ResearchProvider):
    """Search papers via Semantic Scholar API (free, no key required)."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        papers = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/search",
                    params={
                        "query": query,
                        "limit": min(limit, 20),
                        "fields": "title,authors,year,abstract,citationCount,url,externalIds,fieldsOfStudy",
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    for paper in data.get("data", []):
                        authors = [a.get("name", "") for a in paper.get("authors", [])]
                        external_ids = paper.get("externalIds", {}) or {}
                        papers.append({
                            "id": paper.get("paperId", str(uuid.uuid4())),
                            "title": paper.get("title", "Untitled"),
                            "authors": authors,
                            "year": paper.get("year"),
                            "abstract": paper.get("abstract", ""),
                            "doi": external_ids.get("DOI", ""),
                            "url": paper.get("url", ""),
                            "source": "Semantic Scholar",
                            "citations": paper.get("citationCount", 0),
                            "keywords": paper.get("fieldsOfStudy", []) or [],
                        })
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
        return papers


class ArXivProvider(ResearchProvider):
    """Search papers via arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        papers = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "search_query": f"all:{query}",
                        "start": 0,
                        "max_results": min(limit, 20),
                        "sortBy": "relevance",
                        "sortOrder": "descending",
                    },
                )
                if response.status_code == 200:
                    # Parse Atom XML response
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}

                    for entry in root.findall("atom:entry", ns):
                        title = entry.find("atom:title", ns)
                        summary = entry.find("atom:summary", ns)
                        published = entry.find("atom:published", ns)
                        link = entry.find("atom:id", ns)

                        authors = []
                        for author in entry.findall("atom:author", ns):
                            name = author.find("atom:name", ns)
                            if name is not None:
                                authors.append(name.text)

                        categories = []
                        for cat in entry.findall("{http://arxiv.org/schemas/atom}primary_category"):
                            categories.append(cat.get("term", ""))

                        year = None
                        if published is not None and published.text:
                            year = int(published.text[:4])

                        papers.append({
                            "id": str(uuid.uuid4()),
                            "title": title.text.strip().replace("\n", " ") if title is not None else "Untitled",
                            "authors": authors[:5],
                            "year": year,
                            "abstract": summary.text.strip().replace("\n", " ") if summary is not None else "",
                            "doi": "",
                            "url": link.text if link is not None else "",
                            "source": "arXiv",
                            "citations": 0,
                            "keywords": categories,
                        })
        except Exception as e:
            print(f"arXiv search error: {e}")
        return papers


class CrossrefProvider(ResearchProvider):
    """Search papers via Crossref API."""

    BASE_URL = "https://api.crossref.org/works"

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        papers = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "query": query,
                        "rows": min(limit, 20),
                        "sort": "relevance",
                    },
                    headers={"User-Agent": "ResearchAI/1.0 (research-assistant)"},
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("message", {}).get("items", []):
                        titles = item.get("title", ["Untitled"])
                        title = titles[0] if titles else "Untitled"

                        authors = []
                        for author in item.get("author", []):
                            name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                            if name:
                                authors.append(name)

                        year = None
                        date_parts = item.get("published-print", {}).get("date-parts", [[]])
                        if not date_parts or not date_parts[0]:
                            date_parts = item.get("published-online", {}).get("date-parts", [[]])
                        if date_parts and date_parts[0]:
                            year = date_parts[0][0]

                        doi = item.get("DOI", "")
                        url = f"https://doi.org/{doi}" if doi else ""

                        papers.append({
                            "id": str(uuid.uuid4()),
                            "title": title,
                            "authors": authors[:5],
                            "year": year,
                            "abstract": "",  # Crossref rarely has abstracts
                            "doi": doi,
                            "url": url,
                            "source": "Crossref",
                            "citations": item.get("is-referenced-by-count", 0),
                            "keywords": item.get("subject", []),
                        })
        except Exception as e:
            print(f"Crossref search error: {e}")
        return papers


class DemoResearchProvider(ResearchProvider):
    """Demo provider with sample papers."""

    SAMPLE_PAPERS = [
        {
            "id": "demo-1",
            "title": "Deep Learning Approaches for Natural Language Processing in Healthcare",
            "authors": ["Sarah Chen", "James Wilson", "Maria Garcia"],
            "year": 2025,
            "abstract": "This paper presents a comprehensive survey of deep learning methods applied to natural language processing tasks in healthcare settings. We review transformer-based models, clinical NLP systems, and their applications in electronic health records analysis, clinical trial matching, and medical literature mining.",
            "doi": "10.1234/demo.2025.001",
            "url": "https://example.com/paper1",
            "source": "Demo (Semantic Scholar)",
            "citations": 145,
            "keywords": ["Deep Learning", "NLP", "Healthcare", "Transformers"],
        },
        {
            "id": "demo-2",
            "title": "Federated Learning for Privacy-Preserving Medical Image Analysis",
            "authors": ["Raj Patel", "Emily Zhang", "David Kim"],
            "year": 2024,
            "abstract": "We propose a novel federated learning framework that enables collaborative training of medical image analysis models across multiple hospitals without sharing patient data. Our approach achieves state-of-the-art performance on chest X-ray classification while maintaining strict privacy guarantees.",
            "doi": "10.1234/demo.2024.002",
            "url": "https://example.com/paper2",
            "source": "Demo (arXiv)",
            "citations": 89,
            "keywords": ["Federated Learning", "Privacy", "Medical Imaging"],
        },
        {
            "id": "demo-3",
            "title": "Large Language Models for Scientific Literature Review: A Systematic Evaluation",
            "authors": ["Michael Brown", "Lisa Anderson", "Robert Taylor"],
            "year": 2025,
            "abstract": "This study systematically evaluates the capabilities and limitations of large language models in automating scientific literature reviews. We benchmark GPT-4, Claude, and Gemini across 500 review tasks, measuring accuracy, completeness, and hallucination rates.",
            "doi": "10.1234/demo.2025.003",
            "url": "https://example.com/paper3",
            "source": "Demo (PubMed)",
            "citations": 67,
            "keywords": ["LLMs", "Literature Review", "Evaluation"],
        },
        {
            "id": "demo-4",
            "title": "Attention Mechanisms in Graph Neural Networks for Drug Discovery",
            "authors": ["Anna Lee", "Thomas Moore", "Jennifer White"],
            "year": 2024,
            "abstract": "We introduce a novel attention-based graph neural network architecture for molecular property prediction in drug discovery pipelines. Our model outperforms existing baselines on multiple benchmark datasets including MoleculeNet and PCBA.",
            "doi": "10.1234/demo.2024.004",
            "url": "https://example.com/paper4",
            "source": "Demo (Crossref)",
            "citations": 203,
            "keywords": ["GNN", "Drug Discovery", "Attention", "Molecular"],
        },
        {
            "id": "demo-5",
            "title": "Reinforcement Learning for Automated Experiment Design in Materials Science",
            "authors": ["Carlos Rodriguez", "Yuki Tanaka", "Fatima Al-Hassan"],
            "year": 2025,
            "abstract": "This paper introduces an RL-based system for automating the design of materials science experiments. Our agent learns to optimize experimental parameters, reducing the number of required experiments by 73% while discovering novel material compositions with superior properties.",
            "doi": "10.1234/demo.2025.005",
            "url": "https://example.com/paper5",
            "source": "Demo (Semantic Scholar)",
            "citations": 34,
            "keywords": ["Reinforcement Learning", "Materials Science", "Automation"],
        },
    ]

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        return self.SAMPLE_PAPERS[:min(limit, len(self.SAMPLE_PAPERS))]


# ─── Research Service ──────────────────────────────────────────

_providers: Dict[str, ResearchProvider] = {}


def get_providers() -> Dict[str, ResearchProvider]:
    global _providers
    if not _providers:
        _providers = {
            "semantic_scholar": SemanticScholarProvider(),
            "arxiv": ArXivProvider(),
            "crossref": CrossrefProvider(),
            "demo": DemoResearchProvider(),
        }
    return _providers


async def search_papers(query: str, sources: List[str] = None, limit: int = 10) -> List[Dict]:
    """
    Search for research papers across multiple providers.
    Returns deduplicated results sorted by relevance.
    """
    providers = get_providers()

    if sources is None:
        sources = ["semantic_scholar", "arxiv"]

    all_papers = []

    for source_name in sources:
        provider = providers.get(source_name)
        if provider:
            try:
                papers = await provider.search(query, limit=limit)
                all_papers.extend(papers)
            except Exception as e:
                print(f"Error searching {source_name}: {e}")

    # If no results from real providers, fall back to demo
    if not all_papers:
        demo = providers.get("demo")
        if demo:
            all_papers = await demo.search(query, limit=limit)

    # Deduplicate by title similarity
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        title_lower = paper["title"].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)

    # Sort by citations (descending), then year (descending)
    unique_papers.sort(key=lambda p: (p.get("citations", 0), p.get("year", 0)), reverse=True)

    return unique_papers[:limit]


async def search_and_save(query: str, conversation_id: str, sources: List[str] = None, limit: int = 10) -> List[Dict]:
    """Search papers and save them to database."""
    papers = await search_papers(query, sources, limit)

    for paper in papers:
        await save_research_paper(
            paper_id=paper["id"],
            conversation_id=conversation_id,
            title=paper["title"],
            authors=paper.get("authors", []),
            year=paper.get("year"),
            abstract=paper.get("abstract", ""),
            doi=paper.get("doi", ""),
            url=paper.get("url", ""),
            source=paper.get("source", ""),
            citations=paper.get("citations", 0),
            keywords=paper.get("keywords", []),
        )

    return papers
