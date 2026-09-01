"""
Entry point for running the bot as a module

Usage:
    python -m bot
"""

if __name__ == "__main__":
    from bot.webhooks_server import app
    import uvicorn
    from bot.config import Config

    print("🤖 Starting Discord-GitHub Bot")
    print(f"🔗 Webhook server: http://0.0.0.0:{Config.WEBHOOK_PORT}")
    print(f"🌐 External URL: {Config.WEBHOOK_URL}")
    print("")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=Config.WEBHOOK_PORT,
        log_level="debug" if Config.DEBUG else "info"
    )
