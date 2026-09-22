"""Rich Threads: conversation persistence with replay."""
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    message_id: str
    thread_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: float
    metadata: dict


@dataclass
class Thread:
    thread_id: str
    name: str
    created_at: float
    updated_at: float
    archived: bool
    message_count: int


class ConversationStore:
    """SQLite-backed conversation store with thread support."""

    def __init__(self, db_path: str = "conversations.sqlite"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                archived INTEGER DEFAULT 0
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (thread_id) REFERENCES threads(thread_id)
            )
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id, timestamp)
        """)
        self.db.commit()

    def create_thread(self, thread_id: str, name: str) -> Thread:
        now = time.time()
        self.db.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, 0)",
            (thread_id, name, now, now),
        )
        self.db.commit()
        return Thread(thread_id, name, now, now, False, 0)

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        row = self.db.execute(
            "SELECT * FROM threads WHERE thread_id = ?", (thread_id,)
        ).fetchone()
        if not row:
            return None
        count = self.db.execute(
            "SELECT COUNT(*) FROM messages WHERE thread_id = ?", (thread_id,)
        ).fetchone()[0]
        return Thread(row[0], row[1], row[2], row[3], bool(row[4]), count)

    def list_threads(self, include_archived: bool = False) -> list:
        query = "SELECT * FROM threads"
        if not include_archived:
            query += " WHERE archived = 0"
        query += " ORDER BY updated_at DESC"
        rows = self.db.execute(query).fetchall()
        return [
            Thread(row[0], row[1], row[2], row[3], bool(row[4]), 0)
            for row in rows
        ]

    def add_message(self, message: Message):
        self.db.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            (
                message.message_id,
                message.thread_id,
                message.role,
                message.content,
                message.timestamp,
                json.dumps(message.metadata),
            ),
        )
        self.db.execute(
            "UPDATE threads SET updated_at = ? WHERE thread_id = ?",
            (message.timestamp, message.thread_id),
        )
        self.db.commit()

    def get_messages(self, thread_id: str, limit: int = 50, before: Optional[float] = None) -> list:
        query = "SELECT * FROM messages WHERE thread_id = ?"
        params = [thread_id]
        if before:
            query += " AND timestamp < ?"
            params.append(before)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = self.db.execute(query, params).fetchall()
        return [
            Message(row[0], row[1], row[2], row[3], row[4], json.loads(row[5]))
            for row in reversed(rows)
        ]

    def archive_thread(self, thread_id: str):
        self.db.execute(
            "UPDATE threads SET archived = 1 WHERE thread_id = ?", (thread_id,)
        )
        self.db.commit()

    def restore_thread(self, thread_id: str):
        self.db.execute(
            "UPDATE threads SET archived = 0 WHERE thread_id = ?", (thread_id,)
        )
        self.db.commit()

    def rename_thread(self, thread_id: str, new_name: str):
        self.db.execute(
            "UPDATE threads SET name = ? WHERE thread_id = ?", (new_name, thread_id)
        )
        self.db.commit()

    def search_messages(self, query: str, limit: int = 20) -> list:
        rows = self.db.execute(
            """SELECT * FROM messages WHERE content LIKE ?
               ORDER BY timestamp DESC LIMIT ?""",
            (f"%{query}%", limit),
        ).fetchall()
        return [
            Message(row[0], row[1], row[2], row[3], row[4], json.loads(row[5]))
            for row in rows
        ]

    def replay_thread(self, thread_id: str) -> list:
        """Get all messages in a thread for replay."""
        return self.get_messages(thread_id, limit=1000)
