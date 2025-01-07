import sqlite3
from datetime import datetime
from typing import Dict, List
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chat.db')

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH

    def get_connection(self):
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    def create_message(self, content: str) -> int:
        """Create a new message and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (content, created_at, synced) VALUES (?, ?, ?)",
                (content, datetime.now().isoformat(), False)
            )
            return cursor.lastrowid

    def get_messages(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get recent messages."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, created_at, git_commit_hash, synced
                FROM messages
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_message(self, message_id: int) -> Dict:
        """Get a specific message by ID."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, created_at, git_commit_hash, synced
                FROM messages
                WHERE id = ?
            """, (message_id,))
            
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Message {message_id} not found")
            
            return dict(row)

    def update_sync_status(self, message_id: int, git_commit_hash: str):
        """Update the sync status of a message."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET git_commit_hash = ?, synced = ?
                WHERE id = ?
            """, (git_commit_hash, True, message_id))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Message {message_id} not found")

    def get_unsynced_messages(self) -> List[Dict]:
        """Get messages that haven't been synced with GitHub."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, created_at
                FROM messages
                WHERE synced = 0 OR synced IS NULL
                ORDER BY created_at ASC
            """)
            
            return [dict(row) for row in cursor.fetchall()]

    def clear_messages(self):
        """Clear all messages from the database. Use with caution!"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")

    def add_message(self, content: str) -> Dict:
        """Add a message and return it as a dictionary."""
        message_id = self.create_message(content)
        return self.get_message(message_id)

# Create a global instance
db = DatabaseManager()
