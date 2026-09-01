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
    GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH", "secrets.pem")
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
        required = ["DISCORD_TOKEN", "GITHUB_APP_ID", "GITHUB_WEBHOOK_SECRET"]
        missing = [key for key in required if not getattr(cls, key, None)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        private_key = cls.get_github_private_key()
        if "BEGIN" not in private_key or "PRIVATE KEY" not in private_key:
            raise ValueError(
                "GITHUB_PRIVATE_KEY_PATH must point to a PEM private key "
                "downloaded from the GitHub App settings"
            )

        return True

    @classmethod
    def get_github_private_key(cls) -> str:
        """Read the GitHub App private key from a PEM file."""
        key_path = Path(cls.GITHUB_PRIVATE_KEY_PATH)
        if not key_path.is_absolute():
            key_path = env_path.parent / key_path
        try:
            return key_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(f"Could not read GitHub private key: {error}") from error
