import unittest
import json
import http.client
import os
import tempfile
import shutil
import subprocess
from datetime import datetime
from unittest.mock import patch, MagicMock
from utils.db import db
from utils.git_handler import GitHandler
from app import git_handler

class TestGitHandler(GitHandler):
    """Test version of GitHandler that doesn't require GitHub authentication."""
    
    def __init__(self, repo_path: str = None):
        """Initialize without GitHub authentication."""
        self.repo_path = repo_path or os.getcwd()
        self.messages_dir = os.path.join(self.repo_path, 'messages')
        os.makedirs(self.messages_dir, exist_ok=True)
        
    def sync_message(self, message_id: int, content: str) -> str:
        """Mock syncing a message."""
        return 'mock_hash'

class TestServer(unittest.TestCase):
    """Test the HTTP server endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Create a temporary directory for git operations
        cls.test_dir = tempfile.mkdtemp()
        
        # Initialize git repository
        subprocess.run(['git', 'init'], cwd=cls.test_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=cls.test_dir, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=cls.test_dir, check=True)
        subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/test/test.git'], cwd=cls.test_dir, check=True)
        
        # Create a test git handler
        cls.original_git_handler = git_handler
        cls.test_git_handler = TestGitHandler(cls.test_dir)
        
        # Start the server in a separate process
        import time
        
        # Patch the git handler in app.py
        cls.git_handler_patch = patch('app.git_handler', cls.test_git_handler)
        cls.git_handler_patch.start()
        
        # Start server
        cls.server_process = subprocess.Popen(
            ['python', 'app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(2)
        
        # Create HTTP connection
        cls.conn = http.client.HTTPConnection('localhost', 8081)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        # Stop the server
        cls.server_process.terminate()
        cls.server_process.wait()
        
        # Close connection
        cls.conn.close()
        
        # Remove test directory
        shutil.rmtree(cls.test_dir)
        
        # Stop all patches
        cls.git_handler_patch.stop()
        
    def setUp(self):
        """Set up test fixtures."""
        # Clear database before each test
        db.clear_messages()
        
    def test_get_messages_empty(self):
        """Test GET /api/messages with empty database."""
        self.conn.request('GET', '/api/messages')
        response = self.conn.getresponse()
        
        # Check response status
        self.assertEqual(response.status, 200)
        
        # Check response content
        data = json.loads(response.read().decode())
        self.assertIn('messages', data)
        self.assertIn('count', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertEqual(len(data['messages']), 0)
        self.assertEqual(data['count'], 0)
        
    def test_post_message(self):
        """Test POST /api/messages."""
        # Prepare test message
        test_message = {
            'content': 'Test message'
        }
        
        # Send request
        headers = {'Content-Type': 'application/json'}
        self.conn.request(
            'POST', 
            '/api/messages',
            body=json.dumps(test_message),
            headers=headers
        )
        response = self.conn.getresponse()
        
        # Check response status
        self.assertEqual(response.status, 201)
        
        # Check response content
        data = json.loads(response.read().decode())
        self.assertIn('id', data)
        self.assertEqual(data['content'], test_message['content'])
        self.assertIn('created_at', data)
        self.assertIn('git_commit_hash', data)
        self.assertIn('synced', data)
        
        # Verify message was stored in database
        messages = db.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['content'], test_message['content'])
        
    def test_post_message_invalid_json(self):
        """Test POST /api/messages with invalid JSON."""
        # Send request with invalid JSON
        headers = {'Content-Type': 'application/json'}
        self.conn.request(
            'POST', 
            '/api/messages',
            body='invalid json',
            headers=headers
        )
        response = self.conn.getresponse()
        
        # Check response status
        self.assertEqual(response.status, 400)
        
    def test_post_message_missing_content(self):
        """Test POST /api/messages with missing content field."""
        # Send request with missing content
        headers = {'Content-Type': 'application/json'}
        self.conn.request(
            'POST', 
            '/api/messages',
            body=json.dumps({}),
            headers=headers
        )
        response = self.conn.getresponse()
        
        # Check response status
        self.assertEqual(response.status, 400)
        
    def test_get_messages_pagination(self):
        """Test GET /api/messages with pagination."""
        # Add test messages
        messages = [
            'Message 1',
            'Message 2',
            'Message 3',
            'Message 4',
            'Message 5'
        ]
        
        for msg in messages:
            db.add_message(msg)
            
        # Test with limit
        self.conn.request('GET', '/api/messages?limit=3')
        response = self.conn.getresponse()
        data = json.loads(response.read().decode())
        
        self.assertEqual(response.status, 200)
        self.assertEqual(len(data['messages']), 3)
        self.assertEqual(data['limit'], 3)
        
        # Test with offset
        self.conn.request('GET', '/api/messages?offset=2')
        response = self.conn.getresponse()
        data = json.loads(response.read().decode())
        
        self.assertEqual(response.status, 200)
        self.assertEqual(len(data['messages']), 3)  # Default limit is 50
        self.assertEqual(data['offset'], 2)
        
    def test_get_messages_invalid_params(self):
        """Test GET /api/messages with invalid parameters."""
        # Test invalid limit
        self.conn.request('GET', '/api/messages?limit=invalid')
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        
        # Test invalid offset
        self.conn.request('GET', '/api/messages?offset=invalid')
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        
    def test_static_files(self):
        """Test serving static files."""
        # Test index.html
        self.conn.request('GET', '/')
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn('text/html', response.getheader('Content-Type'))
        
        # Read and discard response body
        response.read()
        
    def test_cors_headers(self):
        """Test CORS headers are set correctly."""
        # Test OPTIONS request
        self.conn.request('OPTIONS', '/api/messages')
        response = self.conn.getresponse()
        
        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.getheader('Access-Control-Allow-Origin'),
            '*'
        )
        self.assertIn(
            'GET',
            response.getheader('Access-Control-Allow-Methods')
        )
        self.assertIn(
            'POST',
            response.getheader('Access-Control-Allow-Methods')
        )
        
        # Read and discard response body
        response.read()
        
    def test_git_sync_on_post(self):
        """Test that messages are synced to git on POST."""
        # Create a spy on sync_message
        original_sync_message = self.test_git_handler.sync_message
        sync_message_called = False
        sync_message_args = None
        
        def spy_sync_message(*args, **kwargs):
            nonlocal sync_message_called, sync_message_args
            sync_message_called = True
            sync_message_args = (args, kwargs)
            return original_sync_message(*args, **kwargs)
            
        self.test_git_handler.sync_message = spy_sync_message
        
        try:
            # Send message
            test_message = {
                'content': 'Test message'
            }
            
            headers = {'Content-Type': 'application/json'}
            self.conn.request(
                'POST', 
                '/api/messages',
                body=json.dumps(test_message),
                headers=headers
            )
            response = self.conn.getresponse()
            
            # Check response
            self.assertEqual(response.status, 201)
            data = json.loads(response.read().decode())
            self.assertIsInstance(data['git_commit_hash'], str)
            self.assertTrue(data['synced'])
            
            # Check that sync_message was called
            self.assertTrue(sync_message_called)
            args, kwargs = sync_message_args
            self.assertEqual(len(args), 2)  # message_id and content
            self.assertEqual(args[1], test_message['content'])
            
        finally:
            # Restore original method
            self.test_git_handler.sync_message = original_sync_message

if __name__ == '__main__':
    unittest.main()
