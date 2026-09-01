#!/bin/bash
# Setup script for Discord-GitHub Bot

set -e

echo "🤖 Discord-GitHub Bot Setup"
echo "==========================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✅ Python $PYTHON_VERSION found"

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python -m migrations.001_initial_schema

# Copy env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your configuration:"
    echo "   - DISCORD_TOKEN"
    echo "   - GITHUB_APP_ID"
    echo "   - GITHUB_PRIVATE_KEY"
    echo "   - GITHUB_WEBHOOK_SECRET"
    echo ""
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env with your credentials"
echo "   2. Run: source venv/bin/activate"
echo "   3. Run: cd bot && python webhooks_server.py"
echo ""
