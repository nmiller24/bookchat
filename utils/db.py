import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Union

# Get the database path relative to this file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'chat.db')

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH

    def get_connection(self):
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    def create_user(self, username: str) -> int:
        """Create a new user and return their ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, created_at) VALUES (?, ?)",
                    (username, datetime.now())
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError(f"Username '{username}' already exists")

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "username": result[1],
                    "created_at": result[2],
                    "last_active": result[3]
                }
            return None

    def create_message(self, user_id: int, content: str) -> int:
        """Create a new message and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute(
                "INSERT INTO messages (user_id, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, content, now, now)
            )
            return cursor.lastrowid

    def get_messages(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get recent messages with user information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, u.username 
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.is_deleted = 0
                ORDER BY m.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "user_id": row[1],
                    "content": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "username": row[7]
                })
            return messages

    def update_message(self, message_id: int, content: str) -> bool:
        """Update a message's content."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE messages SET content = ?, updated_at = ? WHERE id = ?",
                (content, datetime.now(), message_id)
            )
            return cursor.rowcount > 0

    def delete_message(self, message_id: int) -> bool:
        """Soft delete a message."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE messages SET is_deleted = 1, updated_at = ? WHERE id = ?",
                (datetime.now(), message_id)
            )
            return cursor.rowcount > 0

    def update_sync_status(self, message_id: int, git_commit_hash: str):
        """Update the sync status of a message."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO message_sync (message_id, git_commit_hash, synced_at)
                VALUES (?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    git_commit_hash = excluded.git_commit_hash,
                    synced_at = excluded.synced_at
            """, (message_id, git_commit_hash, datetime.now()))

# Create a global instance for easy import
db = DatabaseManager()
