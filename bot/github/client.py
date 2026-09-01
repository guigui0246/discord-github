"""
GitHub App authentication and client management
"""
import jwt
import requests
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, List


class GitHubAppAuth:
    """Handle GitHub App JWT authentication"""

    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._token_cache: Dict[str, Dict[Any, Any]] = {}

    def get_jwt(self) -> str:
        """Generate JWT for GitHub App"""
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=10)

        payload: Dict[str, Any] = {
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "iss": self.app_id
        }

        return jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256"
        )

    def get_installation_token(self, installation_id: str) -> str:
        """Get access token for a specific installation"""
        cache_key = f"token_{installation_id}"

        # Check cache
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if datetime.now(timezone.utc) < cached["expires_at"]:
                return cached["token"]

        # Get new token
        jwt_token = self.get_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

        # Cache token
        self._token_cache[cache_key] = {
            "token": token,
            "expires_at": expires_at
        }

        return token


class GitHubClient:
    """GitHub API client for bot operations"""

    def __init__(self, auth: GitHubAppAuth, installation_id: str):
        self.auth = auth
        self.installation_id = installation_id
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        token = self.auth.get_installation_token(self.installation_id)
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_user(self) -> Dict[str, Any]:
        """Get authenticated user/app info"""
        response = requests.get(
            f"{self.base_url}/app",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_installation_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories available to this installation"""
        repos: List[Dict[str, Any]] = []
        page = 1
        per_page = 100

        while True:
            response = requests.get(
                f"{self.base_url}/installation/repositories",
                headers=self._get_headers(),
                params={"page": page, "per_page": per_page}
            )
            response.raise_for_status()
            data = response.json()

            repos.extend(data.get("repositories", []))

            if len(data.get("repositories", [])) < per_page:
                break
            page += 1

        return repos

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get pull request details"""
        response = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_pull_request_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get all comments on a pull request"""
        response = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            headers=self._get_headers(),
            params={"per_page": 100}
        )
        response.raise_for_status()
        return response.json()

    def create_pull_request_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on a pull request"""
        response = requests.post(
            f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            headers=self._get_headers(),
            json={"body": body}
        )
        response.raise_for_status()
        return response.json()

    def update_pull_request_comment(self, owner: str, repo: str, comment_id: str, body: str) -> Dict[str, Any]:
        """Update a pull request comment"""
        response = requests.patch(
            f"{self.base_url}/repos/{owner}/{repo}/issues/comments/{comment_id}",
            headers=self._get_headers(),
            json={"body": body}
        )
        response.raise_for_status()
        return response.json()

    def get_workflow_runs(self, owner: str, repo: str, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflow runs for a repository"""
        params: Dict[str, Any] = {"per_page": 30}
        if branch:
            params["branch"] = branch

        response = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/actions/runs",
            headers=self._get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json().get("workflow_runs", [])
