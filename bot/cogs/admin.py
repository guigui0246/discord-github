"""
Admin cog for bot management
"""
from typing import Any

import discord
from discord.ext import commands


class AdminCog(commands.Cog):
    """Administrative commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction | commands.Context[Any]):
        """Ping the bot"""
        latency = round(self.bot.latency * 1000)
        if isinstance(interaction, commands.Context):
            await interaction.reply(f"🏓 Pong! ({latency}ms)")
        else:
            await interaction.response.send_message(f"🏓 Pong! ({latency}ms)")

    @commands.hybrid_command(name="status", description="Show bot status")
    async def status(self, interaction: discord.Interaction | commands.Context[Any]):
        """Display bot status"""
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.green()
        )
        embed.add_field(name="Status", value="✅ Online", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)

        if isinstance(interaction, commands.Context):
            await interaction.reply(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="sync", description="Sync slash commands")
    async def sync(self, interaction: discord.Interaction | commands.Context[Any]):
        """Sync slash commands with Discord"""
        msg = None
        if isinstance(interaction, commands.Context):
            msg = await interaction.reply("Syncing commands...")
        else:
            await interaction.response.defer(ephemeral=True)

        try:
            synced = await self.bot.tree.sync()
            if isinstance(interaction, commands.Context):
                assert msg is not None
                await msg.edit(content=f"✅ Synced {len(synced)} command(s)")
            else:
                await interaction.followup.send(
                    f"✅ Synced {len(synced)} command(s)",
                    ephemeral=True
                )
        except Exception as e:
            if isinstance(interaction, commands.Context):
                assert msg is not None
                await msg.edit(content=f"❌ Failed to sync: {str(e)}")
            else:
                await interaction.followup.send(
                    f"❌ Failed to sync: {str(e)}",
                    ephemeral=True
                )


async def setup(bot: commands.Bot):
    """Load Admin cog"""
    await bot.add_cog(AdminCog(bot))
