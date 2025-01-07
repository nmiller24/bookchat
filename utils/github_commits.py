from datetime import datetime
import os
from typing import List, Dict, Optional
from github import Github, GithubException
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass
class CommitInfo:
    """Structured information about a commit."""
    sha: str
    message: str
    author_name: str
    author_email: str
    timestamp: str
    url: str
    changed_files: List[str]

class GitHubCommitFetcher:
    """Fetches and structures commit information from GitHub repositories."""
    
    def __init__(self):
        """Initialize with GitHub token from environment."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        
        self.github = Github(self.github_token)
    
    def parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        """Parse repository owner and name from URL.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
            
        Example URLs supported:
            - https://github.com/owner/repo
            - git@github.com:owner/repo.git
            - https://github.com/owner/repo.git
        """
        # Handle SSH URLs
        if repo_url.startswith('git@'):
            path = repo_url.split(':', 1)[1]
            if path.endswith('.git'):
                path = path[:-4]
            owner, repo = path.split('/')
            return owner, repo
        
        # Handle HTTPS URLs
        parsed = urlparse(repo_url)
        path = parsed.path.strip('/')
        if path.endswith('.git'):
            path = path[:-4]
        owner, repo = path.split('/')
        return owner, repo
    
    def get_commits(self, repo_url: str, branch: str = "main", 
                   path: Optional[str] = None, max_count: int = 100) -> List[CommitInfo]:
        """Get commits from a GitHub repository.
        
        Args:
            repo_url: Full URL to the GitHub repository
            branch: Branch to get commits from (default: main)
            path: Optional path to filter commits by
            max_count: Maximum number of commits to return (default: 100)
            
        Returns:
            List of CommitInfo objects containing structured commit data
            
        Raises:
            GithubException: If there's an error accessing the repository
            ValueError: If the repository URL is invalid
        """
        try:
            # Parse repository owner and name
            owner, repo_name = self.parse_repo_url(repo_url)
            
            # Get repository
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Get commits
            commits = []
            kwargs = {"sha": branch}
            if path is not None:
                kwargs["path"] = path
            
            for commit in repo.get_commits(**kwargs)[:max_count]:
                # Get list of changed files
                changed_files = [file.filename for file in commit.files]
                
                # Create CommitInfo object
                commit_info = CommitInfo(
                    sha=commit.sha,
                    message=commit.commit.message,
                    author_name=commit.commit.author.name,
                    author_email=commit.commit.author.email,
                    timestamp=commit.commit.author.date.isoformat(),
                    url=commit.html_url,
                    changed_files=changed_files
                )
                commits.append(commit_info)
            
            return commits
            
        except GithubException as e:
            print(f"GitHub API error: {e.data.get('message', str(e))}")
            raise
        except Exception as e:
            print(f"Error fetching commits: {str(e)}")
            raise
    
    def get_commit_by_sha(self, repo_url: str, commit_sha: str) -> Optional[CommitInfo]:
        """Get a specific commit by its SHA.
        
        Args:
            repo_url: Full URL to the GitHub repository
            commit_sha: SHA of the commit to fetch
            
        Returns:
            CommitInfo object if found, None if not found
            
        Raises:
            GithubException: If there's an error accessing the repository
            ValueError: If the repository URL is invalid
        """
        try:
            # Parse repository owner and name
            owner, repo_name = self.parse_repo_url(repo_url)
            
            # Get repository
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Get commit
            try:
                commit = repo.get_commit(commit_sha)
            except GithubException as e:
                if e.status in [404, 422]:  # 404: Not Found, 422: Validation Failed
                    return None
                raise
            
            # Get list of changed files
            changed_files = [file.filename for file in commit.files]
            
            # Create and return CommitInfo object
            return CommitInfo(
                sha=commit.sha,
                message=commit.commit.message,
                author_name=commit.commit.author.name,
                author_email=commit.commit.author.email,
                timestamp=commit.commit.author.date.isoformat(),
                url=commit.html_url,
                changed_files=changed_files
            )
            
        except GithubException as e:
            print(f"GitHub API error: {e.data.get('message', str(e))}")
            raise
        except Exception as e:
            print(f"Error fetching commit: {str(e)}")
            raise
