"""
FastAPI webhook server for GitHub events
"""
import asyncio
import json
import logging
import discord
from contextlib import asynccontextmanager
from typing import Any, Optional, cast
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn

from bot.config import Config
from bot.github.webhooks import WebhookVerifier, WebhookParser
from bot.database import SessionLocal, GitHubInstallation, Repository, PullRequest, Issue, Comment, WorkflowRun
from bot.main import create_bot
from bot.discord.channels import ChannelManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
# Global bot instance (will be set during startup)
bot = None
webhook_verifier = WebhookVerifier()
webhook_parser = WebhookParser()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize bot and other resources on startup"""
    global bot

    logger.info("Starting webhook server...")

    # Validate configuration
    Config.validate()

    # Create bot instance
    bot = create_bot()

    # Start bot in background
    token = Config.DISCORD_TOKEN
    if token is None:
        raise RuntimeError("DISCORD_TOKEN is not configured")
    asyncio.create_task(bot.start(token))

    logger.info("Webhook server started")
    try:
        yield
    finally:
        if bot:
            await bot.close()


app = FastAPI(title="Discord-GitHub Bot Webhook Server", lifespan=lifespan)


def get_text_channel(channel_id: str) -> Optional[discord.TextChannel]:
    """Return a cached text channel, excluding categories and private channels."""
    if bot is None:
        return None
    channel = bot.get_channel(int(channel_id))
    return channel if isinstance(channel, discord.TextChannel) else None


@app.post("/webhook")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events

    GitHub sends these headers:
    - X-Hub-Signature-256: sha256=<hash>
    - X-GitHub-Event: event_type
    - X-GitHub-Delivery: delivery_id
    """

    # Get headers
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")

    # Get raw body
    body = await request.body()

    # Verify signature
    secret = Config.GITHUB_WEBHOOK_SECRET
    if secret is None or not webhook_verifier.verify_signature(body, signature, secret):
        logger.warning(f"Invalid signature for delivery {delivery_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Parse JSON
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )

    logger.info(f"Received webhook: {event_type} ({delivery_id})")

    # Route to appropriate handler
    try:
        if event_type == "pull_request":
            await handle_pull_request(payload)
        elif event_type == "issues":
            await handle_issue(payload)
        elif event_type == "issue_comment":
            await handle_issue_comment(payload)
        elif event_type == "workflow_run":
            await handle_workflow_run(payload)
        elif event_type == "push":
            await handle_push(payload)
        elif event_type == "installation":
            await handle_installation(payload)
        else:
            logger.debug(f"Unhandled event type: {event_type}")
    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    return JSONResponse({"status": "ok"})


async def handle_pull_request(payload: dict[str, Any]):
    """Handle pull request events"""
    try:
        pr_data = webhook_parser.parse_pull_request_event(payload)
        logger.info(f"PR {pr_data['pr_number']}: {pr_data['action']}")

        db = SessionLocal()
        try:
            repository = cast(Any, db.query(Repository).filter_by(
                repo_full_name=pr_data["repo_full_name"], active=True
            ).first())
            if repository is None or bot is None:
                return

            record = cast(Any, db.query(PullRequest).filter_by(
                repository_id=repository.id, pr_number=pr_data["pr_number"]
            ).first())
            if record is None:
                record = cast(Any, PullRequest(repository_id=repository.id, pr_number=pr_data["pr_number"]))
                db.add(record)
            record.pr_title = pr_data["pr_title"]
            record.github_url = pr_data["url"]
            record.author = pr_data["author"]
            record.status = (
                "merged" if payload["pull_request"].get("merged") else pr_data["status"]
            )

            category = bot.get_channel(int(cast(str, repository.discord_category_id)))
            if category is None or not isinstance(category, discord.CategoryChannel):
                db.commit()
                return

            guild = category.guild
            channel_id = record.discord_channel_id
            channel = get_text_channel(cast(str, channel_id)) if channel_id else None
            if channel is None:
                channel = await ChannelManager.get_or_create_pr_channel(
                    guild, category, cast(int, record.pr_number), cast(str, record.pr_title)
                )
                record.discord_channel_id = str(channel.id)
                await ChannelManager.send_pr_message(
                    channel, cast(int, record.pr_number), cast(str, record.pr_title), cast(str, record.author),
                    record.github_url, pr_data["pr_body"]
                )
            elif pr_data["action"] in {"reopened", "synchronize"}:
                await channel.send(f"GitHub updated PR #{record.pr_number}: **{record.pr_title}**")
            if record.status in {"closed", "merged"}:
                await channel.send(f"PR #{record.pr_number} was {record.status} on GitHub.")
            db.commit()
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error handling PR event: {e}", exc_info=True)


async def handle_issue_comment(payload: dict[str, Any]):
    """Handle issue/PR comment events"""
    try:
        comment_data = webhook_parser.parse_issue_comment_event(payload)

        if comment_data["is_pr"]:
            logger.info(f"PR {comment_data['pr_number']} comment: {comment_data['action']}")
            db = SessionLocal()
            try:
                pull_request = cast(Any, db.query(PullRequest).join(Repository).filter(
                    Repository.repo_full_name == comment_data["repo_full_name"],
                    PullRequest.pr_number == comment_data["pr_number"],
                ).first())
                if pull_request is None or not pull_request.discord_channel_id or bot is None:
                    return
                channel = get_text_channel(cast(str, pull_request.discord_channel_id))
                if channel is None:
                    return
                tracked = cast(Any, db.query(Comment).filter_by(github_comment_id=str(comment_data["comment_id"])).first())
                if comment_data["action"] == "created" and tracked is None:
                    message = await channel.send(
                        f"**{comment_data['author']}** (GitHub):\n{comment_data['comment_body']}\n{comment_data['url']}"
                    )
                    db.add(Comment(
                        pull_request_id=pull_request.id,
                        github_comment_id=str(comment_data["comment_id"]),
                        discord_message_id=str(message.id),
                        author=comment_data["author"], source="github",
                    ))
                elif tracked is not None and comment_data["action"] == "edited":
                    message = await channel.fetch_message(int(tracked.discord_message_id))
                    await message.edit(
                        content=(
                            f"**{comment_data['author']}** (GitHub):\n"
                            f"{comment_data['comment_body']}\n{comment_data['url']}"
                        )
                    )
                elif tracked is not None and comment_data["action"] == "deleted":
                    message = await channel.fetch_message(int(tracked.discord_message_id))
                    await message.delete()
                    db.delete(tracked)
                db.commit()
            finally:
                db.close()
        else:
            logger.info(f"Issue {comment_data['issue_number']} comment: {comment_data['action']}")
            db = SessionLocal()
            try:
                issue = cast(Any, db.query(Issue).join(Repository).filter(
                    Repository.repo_full_name == comment_data["repo_full_name"],
                    Issue.issue_number == comment_data["issue_number"],
                ).first())
                if issue is None or not issue.discord_channel_id or bot is None:
                    return
                channel = get_text_channel(cast(str, issue.discord_channel_id))
                if channel is None:
                    return
                tracked = cast(Any, db.query(Comment).filter_by(
                    github_comment_id=str(comment_data["comment_id"])
                ).first())
                content = (
                    f"**{comment_data['author']}** (GitHub):\n"
                    f"{comment_data['comment_body']}\n{comment_data['url']}"
                )
                if comment_data["action"] == "created" and tracked is None:
                    message = await channel.send(content)
                    db.add(Comment(
                        pull_request_id=None,
                        github_comment_id=str(comment_data["comment_id"]),
                        discord_message_id=str(message.id),
                        author=comment_data["author"], source="github",
                    ))
                elif tracked is not None and comment_data["action"] == "edited":
                    message = await channel.fetch_message(int(tracked.discord_message_id))
                    await message.edit(content=content)
                elif tracked is not None and comment_data["action"] == "deleted":
                    message = await channel.fetch_message(int(tracked.discord_message_id))
                    await message.delete()
                    db.delete(tracked)
                db.commit()
            finally:
                db.close()

    except Exception as e:
        logger.error(f"Error handling comment event: {e}", exc_info=True)


async def handle_issue(payload: dict[str, Any]):
    """Create and update Discord channels for GitHub issues."""
    issue_data = webhook_parser.parse_issue_event(payload)
    logger.info(f"Issue #{issue_data['issue_number']}: {issue_data['action']}")

    db = SessionLocal()
    try:
        repository = cast(Any, db.query(Repository).filter_by(
            repo_full_name=issue_data["repo_full_name"], active=True
        ).first())
        if repository is None or bot is None:
            return

        issue = cast(Any, db.query(Issue).filter_by(
            repository_id=repository.id, issue_number=issue_data["issue_number"]
        ).first())
        if issue is None:
            issue = cast(Any, Issue(
                repository_id=repository.id,
                issue_number=issue_data["issue_number"],
            ))
            db.add(issue)
        issue.issue_title = issue_data["issue_title"]
        issue.github_url = issue_data["url"]
        issue.author = issue_data["author"]
        issue.status = issue_data["status"]

        category = bot.get_channel(int(cast(str, repository.discord_category_id)))
        if not isinstance(category, discord.CategoryChannel):
            db.commit()
            return

        channel = get_text_channel(cast(str, issue.discord_channel_id)) if issue.discord_channel_id else None
        if channel is None:
            channel = await ChannelManager.get_or_create_pr_channel(
                category.guild, category, issue.issue_number, issue.issue_title
            )
            issue.discord_channel_id = str(channel.id)
            embed = discord.Embed(
                title=f"Issue #{issue.issue_number}: {issue.issue_title}",
                description=issue_data["issue_body"][:2000] or "No description provided",
                url=issue.github_url,
                color=discord.Color.orange(),
            )
            embed.add_field(name="Author", value=issue.author, inline=True)
            await channel.send(embed=embed)
        elif issue_data["action"] == "labeled":
            labels = payload["issue"].get("labels", [])
            label_names = ", ".join(label.get("name", "") for label in labels) or "none"
            await channel.send(f"Issue #{issue.issue_number} labels: {label_names}")
        elif issue_data["action"] in {"closed", "reopened"}:
            await channel.send(f"Issue #{issue.issue_number} was {issue.status} on GitHub.")
        db.commit()
    finally:
        db.close()


async def handle_workflow_run(payload: dict[str, Any]):
    """Handle workflow run events"""
    try:
        workflow_data = webhook_parser.parse_workflow_run_event(payload)
        logger.info(f"Workflow {workflow_data['workflow_name']}: {workflow_data['action']}")

        db = SessionLocal()
        try:
            repository = cast(Any, db.query(Repository).filter_by(
                repo_full_name=workflow_data["repo_full_name"], active=True
            ).first())
            if repository is None or bot is None:
                return
            run = cast(Any, db.query(WorkflowRun).filter_by(workflow_run_id=str(workflow_data["workflow_run_id"])).first())
            if run is None:
                run = cast(Any, WorkflowRun(
                    repository_id=repository.id,
                    workflow_run_id=str(workflow_data["workflow_run_id"]),
                ))
                db.add(run)
            run.repository_id = repository.id
            run.workflow_name = workflow_data["workflow_name"]
            run.branch = cast(str, workflow_data["branch"] or "unknown")
            run.status = workflow_data["status"]
            run.conclusion = workflow_data["conclusion"]
            for pull_request in db.query(PullRequest).filter_by(repository_id=repository.id, status="open").all():
                channel = get_text_channel(cast(str, pull_request.discord_channel_id))
                if channel:
                    message = await ChannelManager.send_workflow_notification(
                        channel, run.workflow_name, run.status, run.conclusion,
                        workflow_data["url"], run.branch
                    )
                    run.discord_message_id = str(message.id)
            db.commit()
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error handling workflow event: {e}", exc_info=True)


async def handle_push(payload: dict[str, Any]):
    """Handle push events"""
    try:
        push_data = webhook_parser.parse_push_event(payload)
        logger.info(f"Push to {push_data['repo_full_name']}: {len(push_data['commits'])} commit(s)")

        db = SessionLocal()
        try:
            repository = cast(Any, db.query(Repository).filter_by(
                repo_full_name=push_data["repo_full_name"], active=True
            ).first())
            if repository is None or bot is None:
                return
            branch = push_data["ref"].split("/")[-1]
            summary = (
                f"**{push_data['pusher']}** pushed {len(push_data['commits'])} commit(s) "
                f"to `{branch}`."
            )
            for pull_request in db.query(PullRequest).filter_by(repository_id=repository.id, status="open").all():
                channel = get_text_channel(cast(str, pull_request.discord_channel_id))
                if channel:
                    await channel.send(summary)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error handling push event: {e}", exc_info=True)


async def handle_installation(payload: dict[str, Any]):
    """Handle GitHub App installation events"""
    try:
        action = payload["action"]
        installation = payload["installation"]

        logger.info(f"Installation {action}: {installation['account']['login']}")

        db = SessionLocal()
        try:
            account = installation["account"]
            record = cast(Any, db.query(GitHubInstallation).filter_by(installation_id=str(installation["id"])).first())
            if record is None:
                record = GitHubInstallation(installation_id=str(installation["id"]))
                db.add(record)
            record.account_name = account["login"]
            record.account_type = account.get("type", "User")
            db.commit()
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error handling installation event: {e}", exc_info=True)


@app.get("/health")
async def health_check() -> dict[str, object]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "bot_ready": bot.is_ready() if bot else False
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=Config.WEBHOOK_PORT,
        log_level="info"
    )
