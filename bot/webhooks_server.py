"""
FastAPI webhook server for GitHub events
"""
import asyncio
import json
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn

from bot.config import Config
from bot.github.webhooks import WebhookVerifier, WebhookParser
from bot.github.client import GitHubAppAuth, GitHubClient
from bot.database import SessionLocal, Repository, PullRequest
from bot.main import create_bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Discord-GitHub Bot Webhook Server")

# Global bot instance (will be set during startup)
bot = None
webhook_verifier = WebhookVerifier()
webhook_parser = WebhookParser()


@app.on_event("startup")
async def startup_event():
    """Initialize bot and other resources on startup"""
    global bot

    logger.info("Starting webhook server...")

    # Validate configuration
    Config.validate()

    # Create bot instance
    bot = create_bot()

    # Start bot in background
    asyncio.create_task(bot.start(Config.DISCORD_TOKEN))

    logger.info("Webhook server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bot
    if bot:
        await bot.close()


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
    if not webhook_verifier.verify_signature(body, signature, Config.GITHUB_WEBHOOK_SECRET):
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


async def handle_pull_request(payload: dict):
    """Handle pull request events"""
    try:
        pr_data = webhook_parser.parse_pull_request_event(payload)
        logger.info(f"PR {pr_data['pr_number']}: {pr_data['action']}")

        # TODO: Implement PR synchronization
        # - Create Discord channel if PR opened
        # - Post PR details
        # - Post initial message
        # - Delete channel if PR closed/merged

    except Exception as e:
        logger.error(f"Error handling PR event: {e}", exc_info=True)


async def handle_issue_comment(payload: dict):
    """Handle issue/PR comment events"""
    try:
        comment_data = webhook_parser.parse_issue_comment_event(payload)

        if comment_data["is_pr"]:
            logger.info(f"PR {comment_data['pr_number']} comment: {comment_data['action']}")
            # TODO: Implement comment synchronization
        else:
            logger.debug(f"Issue comment (not a PR): {comment_data['action']}")

    except Exception as e:
        logger.error(f"Error handling comment event: {e}", exc_info=True)


async def handle_workflow_run(payload: dict):
    """Handle workflow run events"""
    try:
        workflow_data = webhook_parser.parse_workflow_run_event(payload)
        logger.info(f"Workflow {workflow_data['workflow_name']}: {workflow_data['action']}")

        # TODO: Implement workflow notifications
        # - Send notification to PR channel if associated
        # - Update workflow status

    except Exception as e:
        logger.error(f"Error handling workflow event: {e}", exc_info=True)


async def handle_push(payload: dict):
    """Handle push events"""
    try:
        push_data = webhook_parser.parse_push_event(payload)
        logger.info(f"Push to {push_data['repo_full_name']}: {len(push_data['commits'])} commit(s)")

        # TODO: Implement push notifications

    except Exception as e:
        logger.error(f"Error handling push event: {e}", exc_info=True)


async def handle_installation(payload: dict):
    """Handle GitHub App installation events"""
    try:
        action = payload["action"]
        installation = payload["installation"]

        logger.info(f"Installation {action}: {installation['account']['login']}")

        # TODO: Implement installation handling
        # - Store installation ID in database
        # - Discover available repositories
        # - Update installation config

    except Exception as e:
        logger.error(f"Error handling installation event: {e}", exc_info=True)


@app.get("/health")
async def health_check():
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
