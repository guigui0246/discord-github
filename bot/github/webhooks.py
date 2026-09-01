"""
GitHub webhook handling and verification
"""
import hmac
import hashlib
from typing import Dict, Any


class WebhookVerifier:
    """Verify GitHub webhook signatures"""

    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify webhook signature using HMAC-SHA256

        GitHub sends: X-Hub-Signature-256: sha256=<hash>
        """
        if not signature.startswith("sha256="):
            return False

        expected_signature = signature.split("=", 1)[1]
        computed_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_signature, expected_signature)


class WebhookParser:
    """Parse GitHub webhook payloads"""

    @staticmethod
    def parse_pull_request_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PR details from pull_request event"""
        pr = payload["pull_request"]

        return {
            "action": payload["action"],  # opened, closed, reopened, synchronize, etc.
            "pr_number": pr["number"],
            "pr_title": pr["title"],
            "pr_body": pr["body"],
            "author": pr["user"]["login"],
            "status": "closed" if pr["merged"] else ("closed" if pr["state"] == "closed" else "open"),
            "url": pr["html_url"],
            "repo_owner": payload["repository"]["owner"]["login"],
            "repo_name": payload["repository"]["name"],
            "repo_full_name": payload["repository"]["full_name"],
        }

    @staticmethod
    def parse_issue_comment_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comment details from issue_comment event"""
        issue = payload["issue"]
        comment = payload["comment"]

        return {
            "action": payload["action"],  # created, edited, deleted
            "pr_number": issue["number"] if "pull_request" in issue else None,
            "comment_id": comment["id"],
            "comment_body": comment["body"],
            "author": comment["user"]["login"],
            "url": comment["html_url"],
            "repo_owner": payload["repository"]["owner"]["login"],
            "repo_name": payload["repository"]["name"],
            "repo_full_name": payload["repository"]["full_name"],
            "is_pr": "pull_request" in issue,
        }

    @staticmethod
    def parse_issue_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract issue details from an issues event."""
        issue = payload["issue"]
        return {
            "action": payload["action"],
            "issue_number": issue["number"],
            "issue_title": issue["title"],
            "issue_body": issue.get("body") or "",
            "author": issue["user"]["login"],
            "status": issue["state"],
            "url": issue["html_url"],
            "repo_full_name": payload["repository"]["full_name"],
        }

    @staticmethod
    def parse_workflow_run_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract workflow run details from workflow_run event"""
        run = payload["workflow_run"]

        return {
            "action": payload["action"],  # requested, completed
            "workflow_run_id": run["id"],
            "workflow_name": run["name"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "branch": run["head_branch"],
            "head_sha": run["head_sha"],
            "url": run["html_url"],
            "repo_owner": payload["repository"]["owner"]["login"],
            "repo_name": payload["repository"]["name"],
            "repo_full_name": payload["repository"]["full_name"],
        }

    @staticmethod
    def parse_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract push details from push event"""
        return {
            "ref": payload["ref"],
            "before": payload["before"],
            "after": payload["after"],
            "commits": payload["commits"],
            "pusher": payload["pusher"]["name"],
            "repo_owner": payload["repository"]["owner"]["login"],
            "repo_name": payload["repository"]["name"],
            "repo_full_name": payload["repository"]["full_name"],
        }
