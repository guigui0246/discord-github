#!/usr/bin/env python3
"""
Run the Discord-GitHub bot

Usage:
    python run.py              # Start webhook server and bot
    python run.py dev          # Start with debug logging
    python run.py migrate      # Run migrations
    python run.py shell        # Interactive Python shell
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup environment
from dotenv import load_dotenv
load_dotenv()

from config import Config

def run_bot():
    """Run the bot"""
    print("🤖 Starting Discord-GitHub Bot")
    print("=" * 40)

    try:
        Config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    # Import and run
    from bot.webhooks_server import app, startup_event
    import uvicorn

    print(f"🔗 Webhook server: http://localhost:{Config.WEBHOOK_PORT}")
    print(f"🌐 External URL: {Config.WEBHOOK_URL}")
    print("")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=Config.WEBHOOK_PORT,
        log_level="debug" if Config.DEBUG else "info"
    )

def run_migrations():
    """Run database migrations"""
    from migrate import run_migrations

    print("🔄 Running migrations...")
    if run_migrations():
        print("✅ Migrations completed successfully")
    else:
        print("❌ Migrations failed")
        sys.exit(1)

def run_shell():
    """Interactive Python shell with bot context"""
    import code
    from bot.config import Config
    from bot.database import SessionLocal, Repository, PullRequest
    from bot.github.client import GitHubAppAuth

    banner = """
Discord-GitHub Bot Interactive Shell
=====================================

Available:
  - Config: Configuration object
  - db: Database session
  - Repository, PullRequest: ORM models
  - GitHubAppAuth: GitHub authentication

Type 'help()' for more information.
"""

    local_vars = {
        "Config": Config,
        "db": SessionLocal(),
        "Repository": Repository,
        "PullRequest": PullRequest,
        "GitHubAppAuth": GitHubAppAuth,
    }

    code.interact(banner, local=local_vars)

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "default"

    if command == "dev":
        os.environ["DEBUG"] = "true"
        run_bot()
    elif command == "migrate":
        run_migrations()
    elif command == "shell":
        run_shell()
    elif command in ["default", None, ""]:
        run_bot()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python run.py [dev|migrate|shell]")
        sys.exit(1)
