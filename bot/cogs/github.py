"""
GitHub cog for pull request management
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from typing import Any, cast

from bot.config import Config
from bot.database import SessionLocal, GitHubInstallation, Repository, PullRequest, Issue, Comment
from bot.github.client import GitHubAppAuth, GitHubClient


logger = logging.getLogger(__name__)


class GitHubCog(commands.Cog):
    """GitHub-related commands and handlers"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _github_client(installation_id: str) -> GitHubClient:
        if not Config.GITHUB_APP_ID:
            raise RuntimeError("GITHUB_APP_ID is not configured")
        private_key = Config.get_github_private_key()
        auth = GitHubAppAuth(Config.GITHUB_APP_ID, private_key)
        return GitHubClient(auth, installation_id)

    @app_commands.command(name="github", description="Show GitHub integration status")
    async def github(self, interaction: discord.Interaction):
        """Display GitHub integration information"""
        embed = discord.Embed(
            title="GitHub Integration",
            description="Discord-GitHub bot is active and monitoring repositories",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Features",
            value="• Pull Request synchronization\n• Comment threading\n• Workflow notifications\n• Multi-repository support",
            inline=False
        )
        embed.add_field(
            name="Status",
            value="✅ Connected",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="link_repo",
        description="Link a GitHub repository to this channel"
    )
    @app_commands.describe(
        repo="Repository in owner/name format",
        category="Discord category for PR channels"
    )
    async def link_repo(
        self,
        interaction: discord.Interaction,
        repo: str,
        category: discord.CategoryChannel
    ):
        """Link a GitHub repository to Discord"""
        # Validate format
        if "/" not in repo:
            await interaction.response.send_message(
                "❌ Repository must be in `owner/name` format",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        owner, name = (part.strip() for part in repo.split("/", 1))
        if not owner or not name or "/" in name:
            await interaction.followup.send(
                "❌ Repository must be in `owner/name` format", ephemeral=True
            )
            return

        if interaction.guild is None:
            await interaction.followup.send("❌ This command can only be used in a server", ephemeral=True)
            return

        db = SessionLocal()
        try:
            installation = db.query(GitHubInstallation).order_by(GitHubInstallation.updated_at.desc()).first()
            if installation is None and Config.GITHUB_INSTALLATION_ID:
                installation = GitHubInstallation(
                    installation_id=Config.GITHUB_INSTALLATION_ID,
                    account_name="configured-installation",
                    account_type="Unknown",
                )
                db.add(installation)
                db.commit()
            if installation is None:
                await interaction.followup.send(
                    "❌ No GitHub App installation is registered yet. Install the app and retry.",
                    ephemeral=True,
                )
                return

            client = self._github_client(cast(str, installation.installation_id))
            repositories = await asyncio.to_thread(client.get_installation_repositories)
            github_repo = next(
                (item for item in repositories if item.get("full_name", "").lower() == f"{owner}/{name}".lower()),
                None,
            )
            if github_repo is None:
                await interaction.followup.send(
                    f"❌ `{owner}/{name}` is not available to the GitHub App installation.",
                    ephemeral=True,
                )
                return

            linked = db.query(Repository).filter_by(repo_full_name=github_repo["full_name"]).first()
            if linked is None:
                linked = Repository(
                    installation_id=installation.id,
                    repo_owner=owner,
                    repo_name=name,
                    repo_full_name=github_repo["full_name"],
                    discord_category_id=str(category.id),
                )
                db.add(linked)
            else:
                linked_record = cast(Any, linked)
                linked_record.installation_id = installation.id
                linked_record.discord_category_id = str(category.id)
                linked_record.active = True
            db.commit()
        except Exception as error:
            db.rollback()
            await interaction.followup.send(f"❌ Could not link repository: {error}", ephemeral=True)
            return
        finally:
            db.close()

        await interaction.followup.send(
            f"✅ Repository `{github_repo['full_name']}` linked to category `{category.name}`",
            ephemeral=True
        )

    @app_commands.command(
        name="repo_status",
        description="Check status of linked repositories"
    )
    async def repo_status(self, interaction: discord.Interaction):
        """Display status of all linked repositories"""
        embed = discord.Embed(
            title="Linked Repositories",
            color=discord.Color.blurple()
        )

        db = SessionLocal()
        try:
            repositories = db.query(Repository).filter_by(active=True).all()
            if not repositories:
                embed.add_field(name="No repositories linked", value="Use `/link_repo` to add a repository", inline=False)
            else:
                for repository in repositories:
                    category = self.bot.get_channel(int(cast(str, repository.discord_category_id)))
                    pr_count = db.query(PullRequest).filter_by(repository_id=repository.id, status="open").count()
                    embed.add_field(
                        name=repository.repo_full_name,
                        value=(
                            f"Category: {category.mention if isinstance(category, discord.CategoryChannel) else 'missing'}\n"
                            f"Open PRs: {pr_count}"
                        ),
                        inline=False,
                    )
        finally:
            db.close()

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Mirror human messages in PR channels back to GitHub as comments."""
        logger.info(
            "Discord message received: channel=%s author=%s content_length=%s",
            message.channel.id,
            message.author.id,
            len(message.content),
        )
        if message.author.bot or message.guild is None:
            return

        db = SessionLocal()
        try:
            pull_request = db.query(PullRequest).filter_by(discord_channel_id=str(message.channel.id)).first()
            issue = None if pull_request else db.query(Issue).filter_by(
                discord_channel_id=str(message.channel.id)
            ).first()
            if pull_request is None and issue is None:
                return
            if pull_request is not None and cast(str, pull_request.status) != "open":
                return
            if issue is not None and cast(str, issue.status) != "open":
                return

            mapping = cast(Any, pull_request or issue)
            repository = db.query(Repository).filter_by(id=mapping.repository_id, active=True).first()
            if repository is None or repository.installation is None:
                return

            client = self._github_client(repository.installation.installation_id)
            body = f"**{message.author.display_name}** (Discord):\n{message.content}"
            owner = cast(str, repository.repo_owner)
            repo_name = cast(str, repository.repo_name)
            if pull_request is not None:
                comment = await asyncio.to_thread(
                    client.create_pull_request_comment,
                    owner,
                    repo_name,
                    cast(int, pull_request.pr_number),
                    body,
                )
            else:
                issue_record = cast(Any, issue)
                comment = await asyncio.to_thread(
                    client.create_issue_comment,
                    owner,
                    repo_name,
                    cast(int, issue_record.issue_number),
                    body,
                )
            db.add(Comment(
                pull_request_id=pull_request.id if pull_request else None,
                github_comment_id=str(comment["id"]),
                discord_message_id=str(message.id),
                author=message.author.display_name,
                source="discord",
            ))
            db.commit()
        except Exception:
            logger.exception("Failed to synchronize Discord message %s to GitHub", message.id)
            db.rollback()
        finally:
            db.close()


async def setup(bot: commands.Bot):
    """Load GitHub cog"""
    await bot.add_cog(GitHubCog(bot))
