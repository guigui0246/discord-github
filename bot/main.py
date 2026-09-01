"""
Main Discord bot with webhook server
"""
from typing import Any

import discord
from discord.ext import commands
import logging
from pathlib import Path

from bot.config import Config
from bot.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordGitHubBot(commands.Bot):
    """Main Discord bot class"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.dm_messages = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Called when bot is starting"""
        logger.info("Bot starting up...")

        # Initialize database
        init_db()
        logger.info("Database initialized")

        # Load all cogs
        await self.load_cogs()

    async def load_cogs(self):
        """Load all cogs from cogs directory"""
        cogs_path = Path(__file__).parent / "cogs"

        for cog_file in cogs_path.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue

            cog_name = cog_file.stem
            try:
                await self.load_extension(f"bot.cogs.{cog_name}")
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot logged in as {self.user}")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any):
        """Error handler"""
        logger.error(f"Error in {event_method}", exc_info=True)

    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a guild"""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")

    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot leaves a guild"""
        logger.info(f"Left guild: {guild.name} ({guild.id})")


def create_bot():
    """Factory function to create bot instance"""
    return DiscordGitHubBot()


if __name__ == "__main__":
    bot = create_bot()
    assert isinstance(Config.DISCORD_TOKEN, str) and Config.DISCORD_TOKEN, "DISCORD_TOKEN must be set in config"
    bot.run(Config.DISCORD_TOKEN)
