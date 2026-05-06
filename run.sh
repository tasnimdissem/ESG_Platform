#!/bin/bash

# --- ESG Platform Startup Script (Linux) ---

echo "=========================================="
echo "🌿 Starting ESG Platform (Linux)"
echo "=========================================="

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your API keys if needed."
fi

# Function to run via Docker
run_docker() {
    echo "🐳 Launching with Docker Compose..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up --build
    else
        docker compose up --build
    fi
}

# Function to run locally
run_local() {
    echo "🚀 Launching locally (Frontend + Backend + RAG)..."
    npm run dev:full
}

# Check for arguments
if [ "$1" == "--docker" ]; then
    run_docker
    exit 0
elif [ "$1" == "--local" ]; then
    run_local
    exit 0
fi

# Interactive choice
echo "How would you like to run the project?"
echo "1) Docker (Recommended - requires Docker & Compose)"
echo "2) Local (Requires Node.js & Python)"
read -p "Choice [1-2]: " choice

case $choice in
    1) run_docker ;;
    2) run_local ;;
    *) echo "❌ Invalid choice."; exit 1 ;;
esac
