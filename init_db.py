import sqlite3
import os
from datetime import datetime

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'chat.db')

def init_database():
    """Initialize the SQLite database with required tables."""
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            is_deleted BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Create message_sync table to track Git synchronization
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_sync (
            message_id INTEGER PRIMARY KEY,
            git_commit_hash TEXT,
            synced_at TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES messages(id)
        )
        ''')
        
        # Commit the changes
        conn.commit()
        print("Database initialized successfully!")
        
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
