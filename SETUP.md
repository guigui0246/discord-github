"""
Setup guide for Discord-GitHub Bot

This guide walks you through:
1. Creating a Discord bot
2. Creating a GitHub App
3. Configuring the bot
4. Running locally or deploying
"""

# SETUP GUIDE

## Prerequisites

- Python 3.11 or later
- A Discord server (for testing)
- A GitHub account with repository access
- Optionally: Docker and Docker Compose

## Step 1: Create Discord Bot

1. Visit https://discord.com/developers/applications
2. Click "New Application"
3. Give it a name (e.g., "GitHub Bot")
4. Go to the "Bot" tab
5. Click "Add Bot"
6. Under "TOKEN", click "Copy" to save your bot token

Enable Privileged Intents:
- Message Content Intent
- Server Members Intent

7. Go to OAuth2 → URL Generator
8. Select scopes: bot
9. Select permissions:
   - Send Messages
   - Embed Links
   - Manage Messages
   - Manage Channels
   - Read Message History

10. Copy the URL and open it to invite the bot to your server

Save your DISCORD_TOKEN for later!

## Step 2: Create GitHub App

1. Go to https://github.com/settings/apps
2. Click "New GitHub App"
3. Fill in:
   - App name: discord-github-bot
   - Homepage URL: https://github.com/yourusername/discord-github
   - Webhook URL: https://your-domain.com/webhook (or http://localhost:8000/webhook for dev)
   - Webhook secret: Generate a secure random string
   - Webhook active: ✓

4. Repository Permissions:
   - Pull requests: Read & Write
   - Issues: Read & Write
   - Contents: Read
   - Actions: Read
   - Checks: Read

5. Subscribe to events:
   - Pull request
   - Issue comment
   - Pull request review
   - Workflow run
   - Push

6. Generate private key:
   - At the bottom, click "Generate a private key"
   - Save the .pem file securely

Save these:
- GITHUB_APP_ID
- GITHUB_PRIVATE_KEY (contents of .pem)
- GITHUB_WEBHOOK_SECRET

## Step 3: Configure Bot

Clone or create the project:
```bash
cd discord-github
cp .env.example .env
```

Edit .env and fill in:
```env
DISCORD_TOKEN=your_discord_token
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...
GITHUB_WEBHOOK_SECRET=your_webhook_secret
DISCORD_GUILD_ID=your_server_id
WEBHOOK_URL=https://your-domain.com  # or http://localhost:8000 for dev
```

To get DISCORD_GUILD_ID:
- Enable Developer Mode in Discord
- Right-click your server → Copy Server ID

## Step 4: Run Locally (Development)

### Option A: Direct Python

```bash
# Setup (one time)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
python -m migrations.001_initial_schema

# Run
cd bot
python webhooks_server.py
```

The bot will start on http://localhost:8000

### Option B: Using Docker

```bash
docker-compose up -d
docker-compose logs -f bot
```

### Option C: Using Setup Script

On Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
cd bot && python webhooks_server.py
```

On Windows:
```bash
setup.bat
cd bot && python webhooks_server.py
```

## Step 5: Test Locally with ngrok

For local testing with GitHub webhooks:

1. Install ngrok: https://ngrok.com/download
2. Expose local port:
   ```bash
   ngrok http 8000
   ```
3. Copy the HTTPS URL (e.g., https://random-id.ngrok.io)
4. Update GitHub App webhook URL to: https://random-id.ngrok.io/webhook
5. Run bot locally

Now GitHub webhooks will reach your local bot!

## Step 6: Deploy to EC2

1. Launch Ubuntu 22.04 LTS EC2 instance
2. SSH into instance:
   ```bash
   ssh -i key.pem ubuntu@your-instance-ip
   ```

3. Install Docker:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   ```

4. Clone and configure:
   ```bash
   git clone https://github.com/yourusername/discord-github.git
   cd discord-github
   cp .env.example .env
   # Edit .env with your values
   nano .env
   ```

5. Start:
   ```bash
   docker-compose up -d
   ```

6. Setup HTTPS (required for GitHub webhooks):
   ```bash
   sudo apt-get install -y nginx certbot python3-certbot-nginx
   sudo certbot certonly --standalone -d your-domain.com

   # Create nginx config at /etc/nginx/sites-available/default
   # with reverse proxy to localhost:8000
   ```

## Verification

Once running, verify with:

```bash
# Check bot is up
curl http://localhost:8000/health

# In Discord, try slash commands
/ping
/status
/github
```

If commands don't appear, run:
```bash
# In Discord server
/sync
```

## Troubleshooting

### Bot won't start
- Check DISCORD_TOKEN is set and valid
- Check GITHUB_APP_ID and GITHUB_PRIVATE_KEY are set
- Check logs: `docker-compose logs bot`

### Webhooks not firing
- Verify WEBHOOK_URL is HTTPS (required by GitHub)
- Check GitHub App webhook deliveries in settings
- Verify webhook secret matches
- Check firewall rules

### Commands not showing
- Run `/sync` command in Discord
- Check bot permissions in server settings

### Database errors
```bash
rm bot.db  # Reset database
python -m migrations.001_initial_schema
```

## Next Steps

After setup is complete:

1. Install a repository via GitHub App
2. Create a pull request to test
3. Check if Discord channel is created automatically
4. Add more repositories as needed
5. Customize commands in bot/cogs/

## Support

For help:
1. Check README.md
2. Review logs: `docker-compose logs -f`
3. Check GitHub App webhook deliveries
4. Verify all environment variables are set

Happy coding! 🚀
