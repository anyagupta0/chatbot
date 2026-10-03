"""
ResearchAI Backend - Database Models and Configuration
Uses SQLite with aiosqlite for async operations.
Designed for easy migration to PostgreSQL.
"""

import aiosqlite
import os
import json
from datetime import datetime
from pathlib import Path

DATABASE_DIR = Path(__file__).parent.parent / "data"
DATABASE_PATH = DATABASE_DIR / "research_ai.db"


def ensure_data_dir():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


async def get_db():
    ensure_data_dir()
    db = await aiosqlite.connect(str(DATABASE_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    ensure_data_dir()
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL DEFAULT 'default',
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                user_id TEXT NOT NULL DEFAULT 'default',
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                page_count INTEGER DEFAULT 0,
                extracted_text TEXT,
                chunks TEXT DEFAULT '[]',
                status TEXT DEFAULT 'processing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                user_id TEXT NOT NULL DEFAULT 'default',
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                row_count INTEGER DEFAULT 0,
                column_count INTEGER DEFAULT 0,
                columns TEXT DEFAULT '[]',
                summary TEXT DEFAULT '{}',
                status TEXT DEFAULT 'processing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS research_papers (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                title TEXT NOT NULL,
                authors TEXT DEFAULT '[]',
                year INTEGER,
                abstract TEXT,
                doi TEXT,
                url TEXT,
                source TEXT,
                citations INTEGER DEFAULT 0,
                keywords TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                user_id TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                report_type TEXT DEFAULT 'research',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
            CREATE INDEX IF NOT EXISTS idx_documents_conversation ON documents(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_datasets_conversation ON datasets(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_research_papers_conversation ON research_papers(conversation_id);

            -- Default user
            INSERT OR IGNORE INTO users (id, username) VALUES ('default', 'Researcher');
        """)
        await db.commit()
    finally:
        await db.close()


# ─── CRUD Helpers ───────────────────────────────────────────────

async def create_conversation(conversation_id: str, title: str = "New Chat", user_id: str = "default"):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conversation_id, user_id, title)
        )
        await db.commit()
        return conversation_id
    finally:
        await db.close()


async def get_conversations(user_id: str = "default", limit: int = 50):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, title, created_at, updated_at, metadata 
               FROM conversations WHERE user_id = ? 
               ORDER BY updated_at DESC LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_conversation(conversation_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_conversation(conversation_id: str, title: str = None):
    db = await get_db()
    try:
        if title:
            await db.execute(
                "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, conversation_id)
            )
        else:
            await db.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
        await db.commit()
    finally:
        await db.close()


async def delete_conversation(conversation_id: str):
    db = await get_db()
    try:
        await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        await db.commit()
    finally:
        await db.close()


async def add_message(message_id: str, conversation_id: str, role: str, content: str, metadata: dict = None):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, metadata) VALUES (?, ?, ?, ?, ?)",
            (message_id, conversation_id, role, content, json.dumps(metadata or {}))
        )
        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        await db.commit()
    finally:
        await db.close()


async def get_messages(conversation_id: str, limit: int = 100):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, conversation_id, role, content, created_at, metadata 
               FROM messages WHERE conversation_id = ? 
               ORDER BY created_at ASC LIMIT ?""",
            (conversation_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_document(doc_id: str, conversation_id: str, filename: str, 
                         original_filename: str, file_type: str, file_size: int,
                         page_count: int = 0, extracted_text: str = "", 
                         chunks: list = None, status: str = "ready"):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO documents 
               (id, conversation_id, filename, original_filename, file_type, file_size, 
                page_count, extracted_text, chunks, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, conversation_id, filename, original_filename, file_type, file_size,
             page_count, extracted_text, json.dumps(chunks or []), status)
        )
        await db.commit()
    finally:
        await db.close()


async def get_document(doc_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_documents_by_conversation(conversation_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM documents WHERE conversation_id = ? ORDER BY created_at DESC",
            (conversation_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_dataset(dataset_id: str, conversation_id: str, filename: str,
                        original_filename: str, file_type: str, file_size: int,
                        row_count: int = 0, column_count: int = 0,
                        columns: list = None, summary: dict = None, status: str = "ready"):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO datasets
               (id, conversation_id, filename, original_filename, file_type, file_size,
                row_count, column_count, columns, summary, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (dataset_id, conversation_id, filename, original_filename, file_type, file_size,
             row_count, column_count, json.dumps(columns or []), json.dumps(summary or {}), status)
        )
        await db.commit()
    finally:
        await db.close()


async def get_dataset(dataset_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_datasets_by_conversation(conversation_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM datasets WHERE conversation_id = ? ORDER BY created_at DESC",
            (conversation_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_research_paper(paper_id: str, conversation_id: str, title: str,
                                authors: list = None, year: int = None, abstract: str = "",
                                doi: str = "", url: str = "", source: str = "",
                                citations: int = 0, keywords: list = None):
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO research_papers
               (id, conversation_id, title, authors, year, abstract, doi, url, source, citations, keywords)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paper_id, conversation_id, title, json.dumps(authors or []), year, abstract,
             doi, url, source, citations, json.dumps(keywords or []))
        )
        await db.commit()
    finally:
        await db.close()


async def save_report(report_id: str, conversation_id: str, title: str, 
                       content: str, report_type: str = "research"):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO reports (id, conversation_id, title, content, report_type)
               VALUES (?, ?, ?, ?, ?)""",
            (report_id, conversation_id, title, content, report_type)
        )
        await db.commit()
    finally:
        await db.close()


async def search_conversations(query: str, user_id: str = "default"):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at
               FROM conversations c
               LEFT JOIN messages m ON c.id = m.conversation_id
               WHERE c.user_id = ? AND (c.title LIKE ? OR m.content LIKE ?)
               ORDER BY c.updated_at DESC LIMIT 20""",
            (user_id, f"%{query}%", f"%{query}%")
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()
