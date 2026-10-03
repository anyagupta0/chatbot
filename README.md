# ResearchAI

An AI-powered research assistant for academic research, document analysis, and data exploration.

## Features

- 💬 **AI Chat** — Natural language conversations with AI
- 🔎 **Research Search** — Search papers via Semantic Scholar, arXiv, Crossref, PubMed
- 📄 **PDF Analysis** — Upload and analyze research papers
- 📊 **Dataset Analysis** — Upload CSV/XLSX and get insights with charts
- 🔬 **Paper Comparison** — Compare multiple research papers side by side
- 🧪 **Research Gap Detection** — Identify gaps across papers
- 📝 **Report Generation** — Generate structured research reports
- 📚 **Citation System** — Every answer includes verifiable sources

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
AI_API_KEY=your-api-key-here
AI_MODEL=gpt-4
AI_PROVIDER=openai
DATABASE_URL=sqlite:///./data/research_ai.db
```

## Architecture

```
Frontend (React + Vite + Tailwind)
        ↓
    REST API
        ↓
Backend (FastAPI + Python)
        ↓
  ┌─────┼─────────┐
  ↓     ↓         ↓
SQLite  LLM API  Research APIs
```

## License

MIT
