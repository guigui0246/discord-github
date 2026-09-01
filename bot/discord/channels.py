"""
Discord channel management utilities
"""
import discord
from typing import Optional


class ChannelManager:
    """Manage Discord channels for PRs and categories"""
    
    @staticmethod
    async def get_or_create_category(
        guild: discord.Guild,
        category_name: str
    ) -> discord.CategoryChannel:
        """Get existing category or create new one"""
        # Look for existing category
        for category in guild.categories:
            if category.name.lower() == category_name.lower():
                return category
        
        # Create new category
        return await guild.create_category(category_name)
    
    @staticmethod
    async def get_or_create_pr_channel(
        guild: discord.Guild,
        category: discord.CategoryChannel,
        pr_number: int,
        pr_title: str
    ) -> discord.TextChannel:
        """Get existing PR channel or create new one"""
        channel_name = f"pr-{pr_number}-{pr_title[:30].lower().replace(' ', '-').replace('/', '-')}"
        channel_name = channel_name[:100]  # Discord channel name limit
        
        # Look for existing channel
        for channel in category.channels:
            if isinstance(channel, discord.TextChannel) and channel.name == channel_name:
                return channel
        
        # Create new channel
        return await guild.create_text_channel(
            channel_name,
            category=category,
            topic=f"Pull Request #{pr_number}"
        )
    
    @staticmethod
    async def delete_channel(channel: discord.TextChannel) -> bool:
        """Delete a Discord channel"""
        try:
            await channel.delete()
            return True
        except discord.Forbidden:
            return False
        except discord.NotFound:
            return True  # Already deleted
    
    @staticmethod
    async def send_pr_message(
        channel: discord.TextChannel,
        pr_number: int,
        pr_title: str,
        pr_author: str,
        pr_url: str,
        pr_body: str
    ) -> discord.Message:
        """Send initial PR embed message"""
        embed = discord.Embed(
            title=f"Pull Request #{pr_number}",
            description=pr_body[:2000] if pr_body else "No description provided",
            color=discord.Color.blue(),
            url=pr_url
        )
        embed.add_field(name="Title", value=pr_title, inline=False)
        embed.add_field(name="Author", value=pr_author, inline=True)
        embed.set_footer(text="GitHub PR Discussion Thread")
        
        return await channel.send(embed=embed)
    
    @staticmethod
    async def send_workflow_notification(
        channel: discord.TextChannel,
        workflow_name: str,
        status: str,
        conclusion: Optional[str],
        url: str,
        branch: str
    ) -> discord.Message:
        """Send workflow run notification"""
        color_map = {
            "success": discord.Color.green(),
            "failure": discord.Color.red(),
            "neutral": discord.Color.greyple(),
            "cancelled": discord.Color.from_rgb(255, 165, 0),
            "in_progress": discord.Color.gold(),
        }
        
        color = color_map.get(conclusion or status, discord.Color.blurple())
        
        embed = discord.Embed(
            title=f"Workflow: {workflow_name}",
            description=f"Status: **{conclusion or status}**",
            color=color,
            url=url
        )
        embed.add_field(name="Branch", value=branch, inline=True)
        embed.add_field(name="Status", value=conclusion or status, inline=True)
        
        return await channel.send(embed=embed)
