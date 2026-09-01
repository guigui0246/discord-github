@echo off
REM Setup script for Discord-GitHub Bot (Windows)

echo.
echo 🤖 Discord-GitHub Bot Setup
echo ===========================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

REM Create venv
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
python -m pip -q install --upgrade pip
python -m pip -q install -r requirements.txt

REM Initialize database
echo 🗄️  Initializing database...
python -m migrations.001_initial_schema

REM Copy env file
if not exist ".env" (
    echo 📝 Creating .env file...
    copy .env.example .env
    echo.
    echo ⚠️  Please edit .env and add your configuration:
    echo    - DISCORD_TOKEN
    echo    - GITHUB_APP_ID
    echo    - GITHUB_PRIVATE_KEY
    echo    - GITHUB_WEBHOOK_SECRET
    echo.
)

echo.
echo ✅ Setup complete!
echo.
echo 📝 Next steps:
echo    1. Edit .env with your credentials
echo    2. Run: venv\Scripts\activate.bat
echo    3. Run: cd bot ^&^& python webhooks_server.py
echo.
