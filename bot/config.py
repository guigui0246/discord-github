"""
Configuration management for Discord-GitHub bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Base configuration"""

    # Discord
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

    # GitHub
    GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
    GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
    GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")

    # Webhook
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")

    # Debug
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ["DISCORD_TOKEN", "GITHUB_APP_ID", "GITHUB_PRIVATE_KEY", "GITHUB_WEBHOOK_SECRET"]
        missing = [key for key in required if not getattr(cls, key, None)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True
