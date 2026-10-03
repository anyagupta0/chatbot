"""
ResearchAI — Main FastAPI Application
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles to prevent charmap encoding errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from models.database import init_db
from routes.chat import router as chat_router
from routes.research import router as research_router
from routes.documents import router as documents_router
from routes.datasets import router as datasets_router
from routes.reports import router as reports_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    print("[OK] Database initialized")
    print(f"[OK] AI Provider: {os.getenv('AI_PROVIDER', 'demo')}")
    if not os.getenv("AI_API_KEY"):
        print("[WARN] No AI_API_KEY set -- running in demo mode")
    yield


app = FastAPI(
    title="ResearchAI",
    description="AI-powered research assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat_router)
app.include_router(research_router)
app.include_router(documents_router)
app.include_router(datasets_router)
app.include_router(reports_router)


@app.get("/")
async def root():
    return {
        "name": "ResearchAI",
        "version": "1.0.0",
        "status": "running",
        "demo_mode": not bool(os.getenv("AI_API_KEY")),
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy"}
