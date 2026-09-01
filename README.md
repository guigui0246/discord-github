# Discord-GitHub Bot

A Python-based Discord bot that synchronizes GitHub pull requests, comments, and CI/CD workflow status with Discord channels. Designed for multi-repository support with GitHub App authentication.

## Features

- 🔗 **Multi-Repository Support**: Manage pull requests from multiple repositories
- 📦 **Organized Categories**: Automatic Discord category creation per repository
- 💬 **Two-Way Synchronization**: PR comments sync between GitHub and Discord
- 🔔 **Workflow Notifications**: CI/CD status updates in Discord
- 🔐 **GitHub App Auth**: Narrowly-scoped, installation-aware authentication
- 🐳 **Docker Ready**: Deploy easily with Docker Compose
- 🗂️ **Persistent Mapping**: SQLite database for channel/PR relationships
- 🔄 **Webhook Signature Verification**: Secure GitHub webhook handling

## Architecture

```
Internet
   │
   ├──────────────► GitHub Webhooks
   │                    │
   │              HTTPS POST
   │                    │
   ▼                    ▼
┌──────────────────────────────┐
│      Discord-GitHub Bot      │
│     (EC2 Instance/Home)      │
│                              │
│  ┌────────────────────────┐  │
│  │ FastAPI Webhook Server │  │
│  │ (Port 8000)           │  │
│  └────────────────────────┘  │
│           │                  │
│           ▼                  │
│  ┌────────────────────────┐  │
│  │   Discord.py Bot      │  │
│  │   (Cogs & Commands)   │  │
│  └────────────────────────┘  │
│           │                  │
│           ▼                  │
│  ┌────────────────────────┐  │
│  │   SQLite Database     │  │
│  │   (PR Mappings, etc)  │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
         │         │
         ▼         ▼
      Discord    GitHub
```

## Project Structure

```
discord-github-bot/
├── bot/
│   ├── main.py                 # Main Discord bot
│   ├── config.py               # Configuration management
│   ├── database.py             # SQLAlchemy models
│   ├── webhooks_server.py      # FastAPI webhook server
│   │
│   ├── cogs/
│   │   ├── github.py           # GitHub commands
│   │   ├── admin.py            # Admin commands
│   │   └── ci.py               # CI/CD commands
│   │
│   ├── github/
│   │   ├── client.py           # GitHub API client
│   │   └── webhooks.py         # Webhook handling
│   │
│   └── discord/
│       └── channels.py         # Discord channel utilities
│
├── migrations/                 # Database migrations
├── tests/                      # Test suite
├── Dockerfile                  # Container image
├── docker-compose.yml          # Docker Compose setup
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
└── README.md                   # This file
```

## Prerequisites

- **Python 3.11+**
- **Discord Server** (for bot testing)
- **GitHub App** (for repository access)
- **GitHub Webhooks** endpoint (HTTPS URL for EC2/home server)
- **Docker** (optional, for containerized deployment)

## Quick Start

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name your bot (e.g., "GitHub Bot")
4. Go to "Bot" → Click "Add Bot"
5. Under "TOKEN", click "Copy" to get your bot token
6. Enable these **Privileged Gateway Intents**:
   - Message Content Intent
   - Server Members Intent
7. Go to "OAuth2" → "URL Generator"
8. Select scopes: `bot`
9. Select permissions:
   - `Send Messages`
   - `Embed Links`
   - `Manage Messages`
   - `Manage Channels`
   - `Manage Guild Expressions`
   - `Read Message History`
10. Copy the generated URL and open it to invite the bot to your server

### 2. Create GitHub App

1. Go to your GitHub account settings → [Developer settings](https://github.com/settings/apps)
2. Click "New GitHub App"
3. Fill in the form:
   - **App name**: `discord-github-bot`
   - **Homepage URL**: `https://github.com/yourusername/discord-github`
   - **Webhook URL**: `https://your-ec2-domain.com/webhook` (or `http://localhost:8000/webhook` for testing)
   - **Webhook active**: ✅ Checked
   - **Webhook secret**: Generate a random secret (copy this for later)

4. Under "Repository permissions":
   - Pull requests: `Read & Write`
   - Issues: `Read & Write`
   - Contents: `Read`
   - Actions: `Read`
   - Checks: `Read`

5. Under "Subscribe to events":
   - Pull request
   - Issue comment
   - Pull request review
   - Workflow run
   - Push

6. Generate a private key (at the bottom):
   - Click "Generate a private key"
   - Save the `.pem` file securely

7. Copy your **App ID** and note your **Installation ID** (from the URL when you install it)

### 3. Environment Configuration

Clone or create the project:

```bash
# Copy the example environment file
cp .env.example .env
```

Fill in `.env` with your values:

```env
# Discord Bot
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_discord_server_id_here

# GitHub App
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Deployment
WEBHOOK_URL=https://your-ec2-domain.com
WEBHOOK_PORT=8000
DATABASE_URL=sqlite:///./data/bot.db
DEBUG=False
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Locally (Development)

```bash
# Initialize database
python migrations/001_initial_schema.py

# Run webhook server (which also starts the Discord bot)
cd bot
python webhooks_server.py
```

The server will start on `http://localhost:8000`

### 6. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

## GitHub Webhook Configuration

Your GitHub App needs an HTTPS endpoint to receive webhooks.

### Option A: Using EC2

1. **Get domain/DNS**:
   - Use Route 53 or your DNS provider
   - Point it to your EC2 instance

2. **Setup HTTPS**:
   ```bash
   # Using Let's Encrypt with certbot
   sudo apt-get update
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot certonly --standalone -d your-domain.com
   ```

3. **Forward traffic** (using nginx or similar):
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

       location /webhook {
           proxy_pass http://localhost:8000/webhook;
       }
   }
   ```

### Option B: Using ngrok (Development)

```bash
# Install ngrok
# https://ngrok.com/download

# Expose local port
ngrok http 8000

# Use the HTTPS URL in GitHub App webhook settings
# https://random-id.ngrok.io/webhook
```

## Usage

### Slash Commands

#### GitHub Commands

- `/github` - Show GitHub integration status
- `/link_repo owner/repo category_name` - Link a repository
- `/repo_status` - Show linked repositories

#### Admin Commands

- `/ping` - Bot latency
- `/status` - Bot health status
- `/sync` - Sync slash commands with Discord

#### CI/CD Commands

- `/workflows` - Show recent workflow runs

### Automatic Features

1. **PR Created**: Bot creates a Discord channel in the repository category
2. **PR Updated**: Channel topic and embeds updated
3. **PR Closed/Merged**: Channel can be archived or deleted (configurable)
4. **Comments**: GitHub comments appear as Discord messages
5. **Discord Messages**: Messages in PR channel can sync back to GitHub
6. **Workflows**: CI/CD status updates appear in relevant PR channels

## Database Schema

### Tables

- **github_installations** - GitHub App installations
- **repositories** - Linked GitHub repositories
- **pull_requests** - PR to Discord channel mappings
- **comments** - Comment synchronization tracking
- **workflow_runs** - CI/CD workflow status

## Configuration Details

### Config Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DISCORD_TOKEN` | Discord bot token | `token_here` |
| `GITHUB_APP_ID` | GitHub App ID | `123456` |
| `GITHUB_PRIVATE_KEY` | GitHub App private key (RSA) | `-----BEGIN...` |
| `GITHUB_WEBHOOK_SECRET` | Webhook signature secret | `super_secret` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./bot.db` |
| `WEBHOOK_PORT` | Port for webhook server | `8000` |
| `WEBHOOK_URL` | External webhook URL | `https://domain.com` |
| `DEBUG` | Enable debug logging | `False` |

## API Endpoints

### Health Check

```
GET /health
```

Returns bot status and readiness.

### GitHub Webhooks

```
POST /webhook

Headers:
  X-Hub-Signature-256: sha256=<hash>
  X-GitHub-Event: pull_request
  X-GitHub-Delivery: <uuid>

Body: JSON webhook payload
```

Handles all GitHub events. Signature is verified using HMAC-SHA256.

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest

# Run with coverage
pytest --cov=bot
```

### Adding New Commands

Create a new cog in `bot/cogs/`:

```python
# bot/cogs/my_commands.py
import discord
from discord.ext import commands
from discord import app_commands

class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mycommand")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

async def setup(bot: commands.Bot):
    await bot.add_cog(MyCog(bot))
```

The bot automatically loads all cogs from `bot/cogs/`.

### Adding New Webhook Handlers

1. Update `bot/github/webhooks.py` with parser logic
2. Add handler in `bot/webhooks_server.py`
3. Subscribe to event in GitHub App settings

## Deployment Guide

### AWS EC2 Deployment

1. **Launch EC2 Instance**:
   ```bash
   # Ubuntu 22.04 LTS t3.micro or larger
   # Security Group: Allow 443 (HTTPS), 22 (SSH), 8000 (optional)
   ```

2. **SSH and Setup**:
   ```bash
   ssh -i key.pem ubuntu@your-instance

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu

   # Clone repository
   git clone https://github.com/yourusername/discord-github.git
   cd discord-github
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   nano .env
   ```

4. **Start Bot**:
   ```bash
   docker-compose up -d
   docker-compose logs -f
   ```

5. **Setup HTTPS** (for webhooks):
   ```bash
   sudo apt-get update
   sudo apt-get install -y nginx certbot python3-certbot-nginx

   # Create nginx config
   sudo nano /etc/nginx/sites-available/default
   # Add webhook proxy (see section above)

   # Get SSL certificate
   sudo certbot certonly --nginx -d your-domain.com
   ```

### Home Server Deployment

The bot is designed to be portable - moving from EC2 to home server requires:

1. Update `.env` with new `WEBHOOK_URL`
2. Update DNS to point to home server
3. Setup HTTPS reverse proxy (nginx/Caddy)
4. Copy Docker Compose deployment

No code changes needed!

## Troubleshooting

### Bot Won't Start

```bash
# Check logs
docker-compose logs bot

# Verify config
echo $DISCORD_TOKEN  # Should not be empty
```

### Webhook Not Triggering

1. Verify GitHub App webhook URL is HTTPS and accessible
2. Check webhook deliveries in GitHub App settings
3. Verify signature secret matches
4. Check firewall/security group rules

### Commands Not Appearing

```bash
# Resync commands
# Run /sync command in Discord, or:
python -c "
import asyncio
from bot.main import create_bot
from bot.config import Config

bot = create_bot()

async def sync():
    async with bot:
        await bot.tree.sync()

asyncio.run(sync())
"
```

### Database Issues

```bash
# Reset database
rm data/bot.db

# Reinitialize
python migrations/001_initial_schema.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Two-way comment synchronization
- [ ] Advanced PR filtering/search
- [ ] Webhook event replay
- [ ] Custom embed templates
- [ ] PostgreSQL support
- [ ] Scheduled syncs
- [ ] Discord thread support for comments
- [ ] GitHub status checks dashboard
- [ ] Rate limit monitoring

## Security Considerations

- 🔐 **Never commit `.env`** - use `.env.example` as template
- 🔐 **Webhook Secret**: Use strong random value
- 🔐 **GitHub App Private Key**: Store securely, rotate periodically
- 🔐 **Discord Token**: Treat as secret, never share
- 🔐 **Database**: Backup regularly, especially before migrations
- 🔐 **Webhook Verification**: Always verify HMAC-SHA256 signature (implemented)

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:

1. Check [GitHub Issues](https://github.com/yourusername/discord-github/issues)
2. Open a new issue with detailed description
3. Include logs and configuration (without secrets!)

## Related

- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [GitHub App Guide](https://docs.github.com/en/apps/creating-github-apps)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
