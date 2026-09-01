# Dockerfile for Discord-GitHub Bot

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/

# Create non-root user
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Default command runs the webhook server (which also starts the Discord bot)
CMD ["python", "-m", "bot.webhooks_server"]
