import sqlite3
import os
from datetime import datetime

DB_PATH = "veda.db"


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn


def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            extracted_text TEXT DEFAULT '',
            has_timestamps INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS timestamps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")


# ─── Document Operations ──────────────────────────────────────────────────────

def save_document(filename: str, file_type: str, extracted_text: str,
                  file_size: int = 0, has_timestamps: bool = False):
    """Save or update document in database"""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO documents (filename, file_type, extracted_text, file_size, has_timestamps)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                extracted_text = excluded.extracted_text,
                has_timestamps = excluded.has_timestamps,
                file_size = excluded.file_size
        """, (filename, file_type, extracted_text, file_size, int(has_timestamps)))
        conn.commit()
    finally:
        conn.close()


def get_document(filename: str):
    """Get document by filename"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM documents WHERE filename = ?", (filename,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_documents():
    """Get all documents"""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_document(filename: str):
    """Delete document by filename"""
    conn = get_db()
    try:
        conn.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        conn.commit()
    finally:
        conn.close()


def get_document_text(filename: str) -> str:
    """Get extracted text for a document"""
    doc = get_document(filename)
    return doc["extracted_text"] if doc else ""


# ─── Timestamp Operations ─────────────────────────────────────────────────────

def save_timestamps(filename: str, segments: list):
    """Save timestamps for a document"""
    conn = get_db()
    try:
        doc = conn.execute(
            "SELECT id FROM documents WHERE filename = ?", (filename,)
        ).fetchone()
        if not doc:
            return

        doc_id = doc["id"]

        # Delete existing timestamps
        conn.execute("DELETE FROM timestamps WHERE document_id = ?", (doc_id,))

        # Insert new timestamps
        for seg in segments:
            conn.execute("""
                INSERT INTO timestamps (document_id, start_time, end_time, text)
                VALUES (?, ?, ?, ?)
            """, (doc_id, seg.get("start", 0), seg.get("end", 0), seg.get("text", "")))

        conn.commit()
    finally:
        conn.close()


def get_timestamps(filename: str) -> list:
    """Get timestamps for a document"""
    conn = get_db()
    try:
        doc = conn.execute(
            "SELECT id FROM documents WHERE filename = ?", (filename,)
        ).fetchone()
        if not doc:
            return []

        rows = conn.execute("""
            SELECT start_time as start, end_time as end, text
            FROM timestamps
            WHERE document_id = ?
            ORDER BY start_time
        """, (doc["id"],)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ─── Chat History Operations ──────────────────────────────────────────────────

def save_chat_message(filename: str, role: str, content: str):
    """Save a chat message"""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO chat_history (filename, role, content)
            VALUES (?, ?, ?)
        """, (filename, role, content))
        conn.commit()
    finally:
        conn.close()


def get_chat_history(filename: str) -> list:
    """Get chat history for a document"""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT role, content, created_at
            FROM chat_history
            WHERE filename = ?
            ORDER BY created_at ASC
        """, (filename,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# Initialize database on import
init_db()
