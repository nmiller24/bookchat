import unittest
import json
import http.client
import threading
import time
import os
import sqlite3
from datetime import datetime
from app import run_server
from utils.db import DB_PATH, db
from utils.git_handler import git_handler

class TestHTTPEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the HTTP server in a separate thread."""
        # Configure Git
        os.system('git config --global user.email "test@example.com"')
        os.system('git config --global user.name "Test User"')
        
        # Start server in a thread
        cls.server_thread = threading.Thread(target=run_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        # Give the server time to start
        time.sleep(1)
        
    def setUp(self):
        """Set up test database."""
        # Clear messages table
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()
        
        # Initialize Git repository if needed
        if not os.path.exists(os.path.join(git_handler.repo_path, '.git')):
            os.system('git init')
            os.system('git config --global init.defaultBranch main')
            os.system('git add .')
            os.system('git commit -m "Initial commit"')
    
    def test_post_message(self):
        """Test POST /api/messages endpoint."""
        # Create connection
        conn = http.client.HTTPConnection("localhost", 8081)
        
        # Test data
        test_content = "Test message from HTTP endpoint test"
        data = {"content": test_content}
        
        # Send POST request
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/api/messages", json.dumps(data), headers)
        
        # Get response
        response = conn.getresponse()
        self.assertEqual(response.status, 201)
        
        # Parse response
        response_data = json.loads(response.read().decode())
        
        # Verify response structure
        self.assertIn("id", response_data)
        self.assertIn("content", response_data)
        self.assertIn("created_at", response_data)
        self.assertIn("git_commit_hash", response_data)
        self.assertIn("synced", response_data)
        
        # Verify content
        self.assertEqual(response_data["content"], test_content)
        
        # Verify database entry
        message = db.get_message(response_data["id"])
        self.assertEqual(message["content"], test_content)
        self.assertEqual(message["id"], response_data["id"])
        self.assertTrue(message["synced"])
        self.assertIsNotNone(message["git_commit_hash"])
        
        # Verify Git file
        message_file = os.path.join(git_handler.messages_dir, f"message_{message['id']}_*.json")
        matching_files = [f for f in os.listdir(git_handler.messages_dir) 
                         if f.startswith(f"message_{message['id']}_") and f.endswith(".json")]
        self.assertEqual(len(matching_files), 1)
        
        # Verify file content
        with open(os.path.join(git_handler.messages_dir, matching_files[0])) as f:
            file_data = json.load(f)
            self.assertEqual(file_data["content"], test_content)
            self.assertEqual(file_data["id"], message["id"])
    
    def test_post_message_missing_content(self):
        """Test POST /api/messages with missing content."""
        conn = http.client.HTTPConnection("localhost", 8081)
        
        # Send POST request without content
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/api/messages", json.dumps({}), headers)
        
        # Get response
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        
        # Verify no message was created
        messages = db.get_messages()
        self.assertEqual(len(messages), 0)
    
    def test_post_message_invalid_json(self):
        """Test POST /api/messages with invalid JSON."""
        conn = http.client.HTTPConnection("localhost", 8081)
        
        # Send POST request with invalid JSON
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/api/messages", "invalid json", headers)
        
        # Get response
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        
        # Verify no message was created
        messages = db.get_messages()
        self.assertEqual(len(messages), 0)

    def test_get_messages_empty(self):
        """Test GET /api/messages with empty database."""
        conn = http.client.HTTPConnection("localhost", 8081)
        
        # Send GET request
        conn.request("GET", "/api/messages")
        
        # Get response
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        
        # Parse response
        response_data = json.loads(response.read().decode())
        
        # Verify response structure
        self.assertIn("messages", response_data)
        self.assertIn("count", response_data)
        self.assertIn("limit", response_data)
        self.assertIn("offset", response_data)
        
        # Verify empty response
        self.assertEqual(response_data["count"], 0)
        self.assertEqual(len(response_data["messages"]), 0)
        self.assertEqual(response_data["limit"], 50)  # Default limit
        self.assertEqual(response_data["offset"], 0)  # Default offset
    
    def test_get_messages_with_data(self):
        """Test GET /api/messages with data in database."""
        # Create test messages
        test_messages = [
            "First test message",
            "Second test message",
            "Third test message"
        ]
        
        message_ids = []
        for content in test_messages:
            # Create message
            conn = http.client.HTTPConnection("localhost", 8081)
            data = {"content": content}
            headers = {"Content-Type": "application/json"}
            conn.request("POST", "/api/messages", json.dumps(data), headers)
            response = conn.getresponse()
            response_data = json.loads(response.read().decode())
            message_ids.append(response_data["id"])
        
        # Get messages
        conn = http.client.HTTPConnection("localhost", 8081)
        conn.request("GET", "/api/messages")
        
        # Get response
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        
        # Parse response
        response_data = json.loads(response.read().decode())
        
        # Verify response structure
        self.assertIn("messages", response_data)
        self.assertIn("count", response_data)
        self.assertEqual(response_data["count"], len(test_messages))
        
        # Verify message contents
        messages = response_data["messages"]
        self.assertEqual(len(messages), len(test_messages))
        
        # Messages should be in reverse chronological order
        for i, message in enumerate(reversed(messages)):
            self.assertEqual(message["content"], test_messages[i])
            self.assertEqual(message["id"], message_ids[i])
            self.assertTrue(message["synced"])
            self.assertIsNotNone(message["git_commit_hash"])
    
    def test_get_messages_pagination(self):
        """Test GET /api/messages with pagination."""
        # Create 5 test messages
        test_messages = [f"Test message {i}" for i in range(5)]
        
        for content in test_messages:
            conn = http.client.HTTPConnection("localhost", 8081)
            data = {"content": content}
            headers = {"Content-Type": "application/json"}
            conn.request("POST", "/api/messages", json.dumps(data), headers)
            conn.getresponse().read()
        
        # Test with limit=2, offset=1
        conn = http.client.HTTPConnection("localhost", 8081)
        conn.request("GET", "/api/messages?limit=2&offset=1")
        
        # Get response
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        
        # Parse response
        response_data = json.loads(response.read().decode())
        
        # Verify pagination
        self.assertEqual(response_data["limit"], 2)
        self.assertEqual(response_data["offset"], 1)
        self.assertEqual(len(response_data["messages"]), 2)
    
    def test_get_messages_invalid_params(self):
        """Test GET /api/messages with invalid parameters."""
        # Test with invalid limit
        conn = http.client.HTTPConnection("localhost", 8081)
        conn.request("GET", "/api/messages?limit=invalid")
        
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        
        # Test with invalid offset
        conn = http.client.HTTPConnection("localhost", 8081)
        conn.request("GET", "/api/messages?offset=invalid")
        
        response = conn.getresponse()
        self.assertEqual(response.status, 400)

if __name__ == "__main__":
    unittest.main()
