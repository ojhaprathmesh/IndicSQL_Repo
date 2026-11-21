"""
Centralized SQLite Session & Conversation Storage for IndicSQL API.
Provides persistent storage for multi-turn conversations and message history
accessible by both Web Studio and Mobile clients.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sessions.db"


class SessionStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL,
                    is_error INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);"
            )

    def create_conversation(self, conversation_id: Optional[str] = None, title: str = "New Conversation") -> Dict[str, Any]:
        cid = conversation_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?);",
                (cid, title, now, now),
            )
        return {"id": cid, "title": title, "created_at": now, "updated_at": now}

    def list_conversations(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC;")
            return [dict(row) for row in cursor.fetchall()]

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?;", (conversation_id,))
            row = cursor.fetchone()
            if not row:
                return None
            conv = dict(row)
            msg_cursor = conn.execute(
                "SELECT id, role, content, payload_json, created_at, is_error FROM messages WHERE conversation_id = ? ORDER BY id ASC;",
                (conversation_id,),
            )
            messages = []
            for m in msg_cursor.fetchall():
                m_dict = dict(m)
                if m_dict.get("payload_json"):
                    try:
                        m_dict["payload"] = json.loads(m_dict["payload_json"])
                    except Exception:
                        m_dict["payload"] = None
                messages.append(m_dict)
            conv["messages"] = messages
            return conv

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        payload: Optional[Dict[str, Any]] = None,
        is_error: bool = False,
    ):
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            # Ensure conversation exists
            cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?;", (conversation_id,))
            count = cursor.fetchone()[0]
            if count == 0 and role == "user":
                title = content.strip().replace("\n", " ")
                if len(title) > 60:
                    title = title[:57] + "..."
                conn.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET title = excluded.title, updated_at = excluded.updated_at;",
                    (conversation_id, title, now, now),
                )
            else:
                conn.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at;",
                    (conversation_id, "New Conversation", now, now),
                )

            payload_str = json.dumps(payload) if payload else None
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, payload_json, created_at, is_error) VALUES (?, ?, ?, ?, ?, ?);",
                (conversation_id, role, content, payload_str, now, 1 if is_error else 0),
            )

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?;", (conversation_id,))
            return cursor.rowcount > 0


session_store = SessionStore()
