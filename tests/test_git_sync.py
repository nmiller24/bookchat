import unittest
import os
import json
import shutil
import subprocess
from datetime import datetime
import time
import uuid
from dotenv import load_dotenv
from github import Github

# Add parent directory to path to import modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.git_handler import GitHandler

class TestGitSync(unittest.TestCase):
    """Test Git synchronization functionality.
    
    These tests verify that messages can be properly pushed to and pulled from GitHub,
    and that the system handles concurrent modifications correctly.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests."""
        # Load environment variables
        load_dotenv()
        
        # Check if we have the required environment variables
        cls.github_token = os.getenv('GITHUB_TOKEN')
        if not cls.github_token:
            raise unittest.SkipTest("GITHUB_TOKEN environment variable not set")
        
        # Initialize GitHub API client
        cls.github = Github(cls.github_token)
        
        try:
            # Test API connection and get user
            cls.user = cls.github.get_user()
            cls.username = cls.user.login
            
            # Test repository creation permission
            try:
                test_repo = cls.user.create_repository(
                    "test-repo-permissions",
                    description="Testing repository permissions",
                    auto_init=True
                )
                test_repo.delete()
            except Exception as e:
                raise unittest.SkipTest(
                    "GitHub token doesn't have sufficient permissions. "
                    "Need 'repo' and 'delete_repo' scopes."
                )
            
            # Create two test repositories (one for each clone)
            repo_name = f"bookchat-test-{uuid.uuid4().hex[:8]}"
            cls.repo = cls.user.create_repo(
                repo_name,
                description="Temporary repository for BookChat sync tests",
                auto_init=True
            )
            cls.repo_url = cls.repo.clone_url.replace(
                "https://", f"https://{cls.github_token}@"
            )
        except Exception as e:
            if hasattr(cls, 'repo'):
                try:
                    cls.repo.delete()
                except:
                    pass
            raise unittest.SkipTest(f"Failed to set up GitHub repository: {str(e)}")
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create two test directories to simulate different clients
        self.test_dir1 = os.path.join(
            os.path.dirname(__file__),
            f'test_repo_sync1_{uuid.uuid4().hex[:8]}'
        )
        self.test_dir2 = os.path.join(
            os.path.dirname(__file__),
            f'test_repo_sync2_{uuid.uuid4().hex[:8]}'
        )
        
        try:
            # Clone the repository twice
            for test_dir in [self.test_dir1, self.test_dir2]:
                # Remove directory if it exists
                if os.path.exists(test_dir):
                    shutil.rmtree(test_dir, ignore_errors=True)
                
                # Clone the repository
                subprocess.run(
                    ['git', 'clone', self.repo_url, test_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Configure git
                subprocess.run(
                    ['git', 'config', 'user.name', 'Test User'],
                    cwd=test_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                subprocess.run(
                    ['git', 'config', 'user.email', 'test@example.com'],
                    cwd=test_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Create messages directory
                os.makedirs(os.path.join(test_dir, 'messages'), exist_ok=True)
            
            # Initialize GitHandler instances
            self.handler1 = GitHandler(repo_path=self.test_dir1)
            self.handler2 = GitHandler(repo_path=self.test_dir2)
            
        except subprocess.CalledProcessError as e:
            self.skipTest(f"Failed to set up git repository: {e.stderr}")
        except Exception as e:
            self.skipTest(f"Failed to set up test: {str(e)}")
    
    def tearDown(self):
        """Clean up test environment after each test."""
        try:
            # Remove test directories
            for test_dir in [self.test_dir1, self.test_dir2]:
                if os.path.exists(test_dir):
                    try:
                        shutil.rmtree(test_dir)
                    except Exception:
                        time.sleep(1)
                        shutil.rmtree(test_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Failed to clean up test directories: {str(e)}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done."""
        try:
            # Delete the test repository
            if hasattr(cls, 'repo'):
                cls.repo.delete()
        except Exception as e:
            print(f"Warning: Failed to delete test repository: {str(e)}")
        finally:
            if hasattr(cls, 'github'):
                cls.github.close()
    
    def test_basic_push_pull(self):
        """Test basic push from one client and pull from another."""
        try:
            # Create and push a message from client 1
            message_id = int(time.time())
            content = f"Test message {message_id}"
            commit_hash = self.handler1.sync_message(message_id, content)
            
            # Verify the message exists in client 1's local directory
            messages_dir1 = os.path.join(self.test_dir1, 'messages')
            files1 = os.listdir(messages_dir1)
            self.assertEqual(len(files1), 1)
            
            # Pull from client 2
            messages = self.handler2.pull_messages()
            
            # Verify the message was pulled to client 2
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]['id'], message_id)
            self.assertEqual(messages[0]['content'], content)
            
            # Verify the file exists in client 2's directory
            messages_dir2 = os.path.join(self.test_dir2, 'messages')
            files2 = os.listdir(messages_dir2)
            self.assertEqual(len(files2), 1)
            self.assertEqual(files1[0], files2[0])
        
        except Exception as e:
            self.fail(f"Test failed: {str(e)}")
    
    def test_concurrent_messages(self):
        """Test handling of concurrent messages from different clients."""
        try:
            # Create messages from both clients
            message1_id = int(time.time())
            message2_id = message1_id + 1
            
            # Push message from client 1
            content1 = f"Message 1 from client 1"
            commit_hash1 = self.handler1.sync_message(message1_id, content1)
            
            # Push message from client 2
            content2 = f"Message 2 from client 2"
            commit_hash2 = self.handler2.sync_message(message2_id, content2)
            
            # Pull from both clients to sync
            messages1 = self.handler1.pull_messages()
            messages2 = self.handler2.pull_messages()
            
            # Verify both clients have both messages
            self.assertEqual(len(messages1), 2)
            self.assertEqual(len(messages2), 2)
            
            # Verify message content
            messages1_dict = {m['id']: m['content'] for m in messages1}
            messages2_dict = {m['id']: m['content'] for m in messages2}
            
            self.assertEqual(messages1_dict[message1_id], content1)
            self.assertEqual(messages1_dict[message2_id], content2)
            self.assertEqual(messages2_dict[message1_id], content1)
            self.assertEqual(messages2_dict[message2_id], content2)
            
            # Verify files exist in both directories
            messages_dir1 = os.path.join(self.test_dir1, 'messages')
            messages_dir2 = os.path.join(self.test_dir2, 'messages')
            
            files1 = sorted(os.listdir(messages_dir1))
            files2 = sorted(os.listdir(messages_dir2))
            
            self.assertEqual(len(files1), 2)
            self.assertEqual(len(files2), 2)
            self.assertEqual(files1, files2)
        
        except Exception as e:
            self.fail(f"Test failed: {str(e)}")
    
    def test_unsynced_messages(self):
        """Test detection of unsynced messages."""
        try:
            # Create a message but don't push it
            message_id = int(time.time())
            filepath = self.handler1.create_message_file(message_id, "Unsynced message")
            
            # Check unsynced messages
            unsynced = self.handler1.get_unsynced_messages()
            self.assertEqual(len(unsynced), 1)
            self.assertEqual(unsynced[0]['id'], message_id)
            self.assertEqual(unsynced[0]['content'], "Unsynced message")
            
            # Sync the message
            self.handler1.commit_and_push(filepath, message_id)
            
            # Verify no unsynced messages remain
            unsynced = self.handler1.get_unsynced_messages()
            self.assertEqual(len(unsynced), 0)
        
        except Exception as e:
            self.fail(f"Test failed: {str(e)}")
    
    def test_pull_with_local_changes(self):
        """Test pulling when there are local changes."""
        try:
            # Create a message on client 1 and push it
            message1_id = int(time.time())
            content1 = "Message from client 1"
            self.handler1.sync_message(message1_id, content1)
            
            # Create a local message on client 2 without pushing
            message2_id = message1_id + 1
            content2 = "Local message on client 2"
            self.handler2.create_message_file(message2_id, content2)
            
            # Pull on client 2
            messages = self.handler2.pull_messages()
            
            # Verify both messages exist locally
            local_files = os.listdir(os.path.join(self.test_dir2, 'messages'))
            self.assertEqual(len(local_files), 2)
            
            # Verify unsynced message is detected
            unsynced = self.handler2.get_unsynced_messages()
            self.assertEqual(len(unsynced), 1)
            self.assertEqual(unsynced[0]['id'], message2_id)
        
        except Exception as e:
            self.fail(f"Test failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
