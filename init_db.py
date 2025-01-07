import sqlite3
import os
from utils.db import DB_PATH

def init_database():
    """Initialize the SQLite database with the messages table."""
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            git_commit_hash TEXT,
            synced BOOLEAN DEFAULT 0
        )
        """)
        
        # Create index on created_at for faster sorting
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_created_at 
        ON messages(created_at DESC)
        """)
        
        # Create index on synced status for faster filtering
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_synced
        ON messages(synced)
        """)
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
        
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
