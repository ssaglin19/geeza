#!/usr/bin/env python3
"""
Ingest the memory corpus template into SQLite with FTS5/BM25 indexing.

Adapted from the original Boosh spec (ingest/ingest.py) for the elderly
assistant use case. All content is prose (no transcript splitting).

Usage:
  python ingest.py corpus.md [--db memory.sqlite] [--chunk-tokens 400]
"""
import argparse
import hashlib
import re
import sqlite3
from pathlib import Path

import yaml


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split YAML front matter from markdown body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, parts[2].strip()


def chunk_text(text: str, max_tokens: int = 400) -> list[str]:
    """Split text into chunks of approximately max_tokens words."""
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for word in words:
        current.append(word)
        current_len += 1
        if current_len >= max_tokens:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def init_db(db_path: str) -> sqlite3.Connection:
    """Create the database and FTS5 table if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            heading TEXT,
            text TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text,
            content='chunks',
            content_rowid='rowid'
        )
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', old.rowid, old.text);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', old.rowid, old.text);
            INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
        END
    """)
    conn.commit()
    return conn


def ingest_file(conn: sqlite3.Connection, path: Path, chunk_tokens: int = 400):
    """Ingest a single markdown file into the database."""
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    
    # Extract heading from first # line
    heading_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    heading = heading_match.group(1) if heading_match else path.stem
    
    # Get metadata
    weight = meta.get("weight", 1.0)
    pinned = 1 if meta.get("pin", False) else 0
    tags = meta.get("tags", [])
    
    # Chunk the body
    chunks = chunk_text(body, chunk_tokens)
    
    # Insert chunks
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.sha256(f"{path}:{i}:{chunk}".encode()).hexdigest()[:16]
        conn.execute("""
            INSERT OR REPLACE INTO chunks (id, source, heading, text, weight, pinned)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chunk_id, str(path), heading, chunk, weight, pinned))
    
    conn.commit()
    return len(chunks)


def search(conn: sqlite3.Connection, query: str, limit: int = 8) -> list[dict]:
    """Search the corpus using FTS5/BM25."""
    cursor = conn.execute("""
        SELECT c.id, c.source, c.heading, c.text, c.weight, c.pinned,
               bm25(chunks_fts) as score
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.rowid
        WHERE chunks_fts MATCH ?
        ORDER BY score * (1.0 + c.weight * 0.1) * (1.0 + c.pinned * 0.5)
        LIMIT ?
    """, (query, limit))
    
    results = []
    for row in cursor:
        results.append({
            "id": row[0],
            "source": row[1],
            "heading": row[2],
            "text": row[3],
            "weight": row[4],
            "pinned": bool(row[5]),
            "score": row[6],
        })
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", help="Markdown file to ingest")
    ap.add_argument("--db", default="memory.sqlite", help="SQLite database path")
    ap.add_argument("--chunk-tokens", type=int, default=400, help="Max tokens per chunk")
    args = ap.parse_args()
    
    path = Path(args.corpus)
    if not path.exists():
        print(f"Error: {path} not found")
        return
    
    conn = init_db(args.db)
    n = ingest_file(conn, path, args.chunk_tokens)
    print(f"Ingested {n} chunks from {path} into {args.db}")
    
    # Show stats
    cursor = conn.execute("SELECT COUNT(*), SUM(pinned) FROM chunks")
    total, pinned = cursor.fetchone()
    print(f"Total chunks: {total}, pinned: {pinned}")


if __name__ == "__main__":
    main()
