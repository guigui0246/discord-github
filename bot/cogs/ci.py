"""
CI/CD cog for workflow notifications
"""
import discord
from discord.ext import commands
from discord import app_commands


class CICog(commands.Cog):
    """CI/CD and workflow-related commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="workflows", description="Show recent workflow runs")
    async def workflows(self, interaction: discord.Interaction):
        """Display recent workflow runs"""
        embed = discord.Embed(
            title="Workflow Runs",
            description="Recent CI/CD workflows",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="No workflows",
            value="Workflow runs will appear here",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Load CI cog"""
    await bot.add_cog(CICog(bot))
