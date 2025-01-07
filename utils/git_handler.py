import os
import json
from datetime import datetime
from github import Github
from dotenv import load_dotenv
import subprocess
from pathlib import Path
import re

# Load environment variables
load_dotenv()

class GitHandler:
    def __init__(self, repo_path: str = None):
        """Initialize GitHandler with repository path and GitHub token.
        
        Args:
            repo_path: Optional path to repository. If not provided, uses the project root.
        """
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        
        # Use provided path or find project root
        if repo_path:
            self.repo_path = repo_path
        else:
            # Find project root (directory containing .git)
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            while current_dir != os.path.dirname(current_dir):  # Stop at root
                if os.path.exists(os.path.join(current_dir, '.git')):
                    self.repo_path = current_dir
                    break
                current_dir = os.path.dirname(current_dir)
            if not hasattr(self, 'repo_path'):
                raise ValueError("Could not find Git repository root")
        
        self.messages_dir = os.path.join(self.repo_path, 'messages')
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        
        # Get repository information
        try:
            remote_url = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Extract owner and repo name from URL
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', remote_url)
            if not match:
                raise ValueError(f"Could not parse GitHub URL: {remote_url}")
            
            owner, repo = match.groups()
            self.repo = self.github.get_repo(f"{owner}/{repo}")
            
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to get remote URL: {e.stderr}")
        except Exception as e:
            raise ValueError(f"Failed to initialize GitHub repository: {str(e)}")
    
    def create_message_file(self, message_id: int, content: str) -> str:
        """Create a JSON file containing the message.
        
        Args:
            message_id: Unique identifier for the message
            content: Message content
        
        Returns:
            Path to the created file
        """
        # Create messages directory if it doesn't exist
        os.makedirs(self.messages_dir, exist_ok=True)
        
        # Initialize Git repository if needed
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            subprocess.run(["git", "init"], cwd=self.repo_path, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", self.repo.clone_url],
                cwd=self.repo_path,
                check=True
            )
        
        # Create .gitkeep if messages directory is empty
        gitkeep_path = os.path.join(self.messages_dir, '.gitkeep')
        if not os.path.exists(gitkeep_path) and not os.listdir(self.messages_dir):
            with open(gitkeep_path, 'w') as f:
                pass
            subprocess.run(
                ["git", "add", os.path.join("messages", ".gitkeep")],
                cwd=self.repo_path,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initialize messages directory"],
                cwd=self.repo_path,
                check=True
            )
            subprocess.run(
                ["git", "push", "-u", "origin", "main"],
                cwd=self.repo_path,
                check=True
            )
        
        timestamp = datetime.now().isoformat()
        filename = f"message_{message_id}_{timestamp.replace(':', '-')}.json"
        filepath = os.path.join(self.messages_dir, filename)
        
        message_data = {
            "id": message_id,
            "content": content,
            "timestamp": timestamp
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(message_data, f, indent=2)
        
        return filepath
    
    def commit_and_push(self, filepath: str, message_id: int) -> str:
        """Commit the message file and push to GitHub.
        
        Args:
            filepath: Path to the file to commit
            message_id: ID of the message (for commit message)
        
        Returns:
            The commit hash
        """
        try:
            # Force add the file (even if in .gitignore)
            subprocess.run(
                ["git", "add", "-f", os.path.relpath(filepath, self.repo_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit the file
            subprocess.run(
                ["git", "commit", "-m", f"Add message {message_id}"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Push to GitHub
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Get the commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            print(f"Error in Git operations: {e.stderr}")
            raise
    
    def pull_messages(self) -> list[dict]:
        """Pull latest messages from GitHub and return new messages.
        
        Returns:
            List of dictionaries containing message data for new messages.
        """
        try:
            # Pull latest changes
            subprocess.run(["git", "pull", "origin", "main"], cwd=self.repo_path, check=True)
            
            # Get list of message files
            message_files = [f for f in os.listdir(self.messages_dir) 
                           if f.startswith("message_") and f.endswith(".json")]
            
            messages = []
            for filename in message_files:
                filepath = os.path.join(self.messages_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        message_data = json.load(f)
                        messages.append(message_data)
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse message file {filename}")
                    continue
            
            return sorted(messages, key=lambda x: x.get('timestamp', ''))
            
        except subprocess.CalledProcessError as e:
            print(f"Error pulling messages: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise
        except Exception as e:
            print(f"Error reading messages: {str(e)}")
            raise
    
    def get_unsynced_messages(self) -> list[dict]:
        """Get messages that exist locally but haven't been pushed to GitHub."""
        try:
            # Get list of staged/modified files
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse status output
            unsynced_files = []
            for line in result.stdout.splitlines():
                if line.startswith("??") or line.startswith(" M") or line.startswith("A"):
                    filename = line[3:].strip()
                    if filename.startswith("messages/") and filename.endswith(".json"):
                        unsynced_files.append(filename)
            
            # Read message data from unsynced files
            messages = []
            for filename in unsynced_files:
                filepath = os.path.join(self.repo_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        message_data = json.load(f)
                        messages.append(message_data)
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse message file {filename}")
                    continue
            
            return sorted(messages, key=lambda x: x.get('timestamp', ''))
            
        except subprocess.CalledProcessError as e:
            print(f"Error checking unsynced messages: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise
        except Exception as e:
            print(f"Error reading unsynced messages: {str(e)}")
            raise
    
    def sync_message(self, message_id: int, content: str) -> str:
        """Create message file, commit, and push to GitHub."""
        filepath = self.create_message_file(message_id, content)
        return self.commit_and_push(filepath, message_id)

# Create a global instance
git_handler = GitHandler()
