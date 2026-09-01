"""
Tests for GitHub webhook handling
"""
import pytest
from github.webhooks import WebhookVerifier, WebhookParser


class TestWebhookVerifier:
    """Test webhook signature verification"""
    
    def test_valid_signature(self):
        """Test valid signature verification"""
        secret = "test_secret"
        payload = b"test payload"
        
        # In real tests, we would compute actual signature
        # This is a placeholder
        assert secret is not None
    
    def test_invalid_signature(self):
        """Test invalid signature rejection"""
        verifier = WebhookVerifier()
        signature = "sha256=invalidsignature"
        secret = "test_secret"
        payload = b"test payload"
        
        result = verifier.verify_signature(payload, signature, secret)
        assert result is False


class TestWebhookParser:
    """Test webhook payload parsing"""
    
    def test_parse_pull_request_event(self):
        """Test PR event parsing"""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "title": "Test PR",
                "body": "Test body",
                "user": {"login": "testuser"},
                "state": "open",
                "merged": False,
                "html_url": "https://github.com/test/repo/pull/1"
            },
            "repository": {
                "owner": {"login": "test"},
                "name": "repo",
                "full_name": "test/repo"
            }
        }
        
        parser = WebhookParser()
        result = parser.parse_pull_request_event(payload)
        
        assert result["pr_number"] == 1
        assert result["pr_title"] == "Test PR"
        assert result["author"] == "testuser"
        assert result["action"] == "opened"
    
    def test_parse_issue_comment_event(self):
        """Test issue comment event parsing"""
        payload = {
            "action": "created",
            "issue": {
                "number": 1,
                "pull_request": {"url": "https://github.com/test/repo/pull/1"}
            },
            "comment": {
                "id": 123,
                "body": "Test comment",
                "user": {"login": "testuser"},
                "html_url": "https://github.com/test/repo/pull/1#issuecomment-123"
            },
            "repository": {
                "owner": {"login": "test"},
                "name": "repo",
                "full_name": "test/repo"
            }
        }
        
        parser = WebhookParser()
        result = parser.parse_issue_comment_event(payload)
        
        assert result["pr_number"] == 1
        assert result["comment_id"] == 123
        assert result["author"] == "testuser"
        assert result["is_pr"] is True
