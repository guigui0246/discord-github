"""
Test configuration and fixtures
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def mock_discord_bot():
    """Mock Discord bot"""
    bot = MagicMock()
    bot.user = MagicMock(name="TestBot#1234")
    return bot


@pytest.fixture
def mock_github_client():
    """Mock GitHub client"""
    client = MagicMock()
    client.get_pull_request = AsyncMock()
    client.get_pull_request_comments = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_webhook_payload():
    """Sample webhook payload"""
    return {
        "action": "opened",
        "pull_request": {
            "number": 1,
            "title": "Test PR",
            "body": "Test PR body",
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
