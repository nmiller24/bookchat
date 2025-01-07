import unittest
import os
import json
import shutil
import subprocess
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.git_handler import GitHandler

class TestGitHandler(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary test directory
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_repo')
        self.messages_dir = os.path.join(self.test_dir, 'messages')
        os.makedirs(self.messages_dir, exist_ok=True)
        
        # Set up environment variable for testing
        os.environ['GITHUB_TOKEN'] = 'test_token'
        
        # Initialize GitHandler with test directory
        self.git_handler = GitHandler(repo_path=self.test_dir)
    
    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove test directory and all its contents
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Remove test environment variable if it exists
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
    
    def test_init_without_token(self):
        """Test initialization without GitHub token."""
        # Remove token before test
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
            
        with self.assertRaises(ValueError):
            GitHandler(repo_path=self.test_dir)
        
        # Restore token after test
        os.environ['GITHUB_TOKEN'] = 'test_token'
    
    def test_create_message_file(self):
        """Test creation of message file."""
        message_id = 1
        content = "Test message"
        
        # Create message file
        filepath = self.git_handler.create_message_file(message_id, content)
        
        # Assert file exists
        self.assertTrue(os.path.exists(filepath))
        
        # Read and verify file contents
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data['id'], message_id)
            self.assertEqual(data['content'], content)
            self.assertTrue('timestamp' in data)
    
    @patch('subprocess.run')
    def test_commit_and_push(self, mock_run):
        """Test commit and push functionality."""
        # Create a test file
        message_id = 1
        filepath = self.git_handler.create_message_file(message_id, "Test message")
        
        # Mock subprocess.run to return a commit hash
        mock_run.return_value = MagicMock(
            stdout="abc123\n",
            returncode=0
        )
        
        # Test commit and push
        commit_hash = self.git_handler.commit_and_push(filepath, message_id)
        
        # Verify git commands were called
        expected_calls = [
            unittest.mock.call(['git', 'add', os.path.relpath(filepath, self.test_dir)],
                             cwd=self.test_dir, check=True),
            unittest.mock.call(['git', 'commit', '-m', f'Add message {message_id}'],
                             cwd=self.test_dir, check=True),
            unittest.mock.call(['git', 'pull', '--rebase', 'origin', 'main'],
                             cwd=self.test_dir, check=True),
            unittest.mock.call(['git', 'push', 'origin', 'main'],
                             cwd=self.test_dir, check=True),
            unittest.mock.call(['git', 'rev-parse', 'HEAD'],
                             cwd=self.test_dir, capture_output=True, text=True, check=True)
        ]
        mock_run.assert_has_calls(expected_calls)
        
        # Verify commit hash
        self.assertEqual(commit_hash, "abc123")
    
    @patch('subprocess.run')
    def test_sync_message(self, mock_run):
        """Test complete message synchronization workflow."""
        message_id = 1
        content = "Test message for sync"
        
        # Mock subprocess.run to return a commit hash
        mock_run.return_value = MagicMock(
            stdout="def456\n",
            returncode=0
        )
        
        # Test sync_message
        commit_hash = self.git_handler.sync_message(message_id, content)
        
        # Verify message file was created
        message_files = os.listdir(self.messages_dir)
        self.assertEqual(len(message_files), 1)
        self.assertTrue(any(f"message_{message_id}_" in f for f in message_files))
        
        # Verify commit hash
        self.assertEqual(commit_hash, "def456")
    
    @patch('subprocess.run')
    def test_git_error_handling(self, mock_run):
        """Test error handling in git operations."""
        # Mock subprocess.run to raise an error
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=['git', 'push'],
            stderr=b"error: failed to push some refs"
        )
        
        # Test error handling
        with self.assertRaises(subprocess.CalledProcessError):
            self.git_handler.sync_message(1, "Test message")

if __name__ == '__main__':
    unittest.main()
