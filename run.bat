@echo off
REM --- ESG Platform Startup Script (Windows) ---

echo ==========================================
echo 🌿 Starting ESG Platform (Windows)
echo ==========================================

cd /d %~dp0

REM Check for .env file
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo ✅ .env created. Please edit it with your API keys if needed.
)

REM Check for arguments
if "%1"=="--docker" goto :docker
if "%1"=="--local" goto :local

:choice
echo How would you like to run the project?
echo 1) Docker (Recommended - requires Docker Desktop)
echo 2) Local (Requires Node.js ^& Python)
set /p choice="Choice [1-2]: "

if "%choice%"=="1" goto :docker
if "%choice%"=="2" goto :local
echo ❌ Invalid choice.
goto :choice

:docker
echo 🐳 Launching with Docker Compose...
docker-compose up --build
if %errorlevel% neq 0 (
    docker compose up --build
)
pause
exit

:local
echo 🚀 Launching locally (Frontend + Backend + RAG)...
npm run dev:full
pause
exit
