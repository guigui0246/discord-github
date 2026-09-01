"""
Admin cog for bot management
"""
import discord
from discord.ext import commands
from discord import app_commands


class AdminCog(commands.Cog):
    """Administrative commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Ping the bot"""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! ({latency}ms)")

    @app_commands.command(name="status", description="Show bot status")
    async def status(self, interaction: discord.Interaction):
        """Display bot status"""
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="✅ Online", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="Sync slash commands")
    async def sync(self, interaction: discord.Interaction):
        """Sync slash commands with Discord"""
        await interaction.response.defer(ephemeral=True)

        try:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(
                f"✅ Synced {len(synced)} command(s)",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to sync: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Load Admin cog"""
    await bot.add_cog(AdminCog(bot))
