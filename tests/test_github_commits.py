import unittest
from utils.github_commits import GitHubCommitFetcher, CommitInfo
from github import GithubException
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TestGitHubCommitFetcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Skip all tests if no GitHub token
        if not os.getenv('GITHUB_TOKEN'):
            raise unittest.SkipTest("GITHUB_TOKEN not set")
        cls.fetcher = GitHubCommitFetcher()
        # Use a public repository for testing
        cls.test_repo_url = "https://github.com/pallets/flask"
    
    def test_parse_repo_url_https(self):
        """Test parsing HTTPS repository URLs."""
        urls = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("https://github.com/owner/repo.git", ("owner", "repo")),
            ("https://github.com/owner/repo/", ("owner", "repo")),
        ]
        
        for url, expected in urls:
            with self.subTest(url=url):
                result = self.fetcher.parse_repo_url(url)
                self.assertEqual(result, expected)
    
    def test_parse_repo_url_ssh(self):
        """Test parsing SSH repository URLs."""
        urls = [
            ("git@github.com:owner/repo.git", ("owner", "repo")),
            ("git@github.com:owner/repo", ("owner", "repo")),
        ]
        
        for url, expected in urls:
            with self.subTest(url=url):
                result = self.fetcher.parse_repo_url(url)
                self.assertEqual(result, expected)
    
    def test_parse_repo_url_invalid(self):
        """Test parsing invalid repository URLs."""
        invalid_urls = [
            "https://github.com/invalid",
            "https://github.com",
            "git@github.com:invalid",
            "invalid_url",
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.fetcher.parse_repo_url(url)
    
    def test_get_commits(self):
        """Test fetching commits from repository."""
        commits = self.fetcher.get_commits(self.test_repo_url, max_count=5)
        
        # Verify we got some commits
        self.assertTrue(len(commits) > 0)
        
        # Verify commit structure
        for commit in commits:
            self.assertIsInstance(commit, CommitInfo)
            self.assertTrue(commit.sha)
            self.assertTrue(commit.message)
            self.assertTrue(commit.author_name)
            self.assertTrue(commit.author_email)
            self.assertTrue(commit.timestamp)
            self.assertTrue(commit.url)
            self.assertIsInstance(commit.changed_files, list)
    
    def test_get_commits_with_path(self):
        """Test fetching commits filtered by path."""
        # Get commits for a specific path
        path = "src/flask"
        commits = self.fetcher.get_commits(self.test_repo_url, path=path, max_count=5)
        
        # Verify commits are related to the path
        for commit in commits:
            path_related = False
            for file in commit.changed_files:
                if file.startswith(path):
                    path_related = True
                    break
            self.assertTrue(path_related)
    
    def test_get_commit_by_sha(self):
        """Test fetching a specific commit by SHA."""
        # First get a list of commits
        commits = self.fetcher.get_commits(self.test_repo_url, max_count=1)
        self.assertTrue(len(commits) > 0)
        
        # Get the first commit's SHA
        commit_sha = commits[0].sha
        
        # Fetch that specific commit
        commit = self.fetcher.get_commit_by_sha(self.test_repo_url, commit_sha)
        
        # Verify it's the same commit
        self.assertIsNotNone(commit)
        self.assertEqual(commit.sha, commit_sha)
    
    def test_get_commit_by_sha_nonexistent(self):
        """Test fetching a nonexistent commit."""
        # Try to fetch a nonexistent commit
        commit = self.fetcher.get_commit_by_sha(self.test_repo_url, "a" * 40)
        self.assertIsNone(commit)
    
    def test_get_commits_invalid_repo(self):
        """Test fetching commits from an invalid repository."""
        with self.assertRaises(GithubException):
            self.fetcher.get_commits("https://github.com/invalid/repo")

if __name__ == '__main__':
    unittest.main()
