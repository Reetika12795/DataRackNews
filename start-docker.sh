#!/bin/bash
# Quick Docker startup script for macOS

echo "🐳 Starting Docker Desktop..."

# Check if Docker Desktop is already running
if docker info > /dev/null 2>&1; then
    echo "✅ Docker Desktop is already running"
    exit 0
fi

# Check if Docker Desktop is installed
if [ ! -d "/Applications/Docker.app" ]; then
    echo "❌ Docker Desktop not found in /Applications/"
    echo "📥 Please install Docker Desktop from:"
    echo "   https://docs.docker.com/desktop/install/mac/"
    exit 1
fi

echo "🚀 Starting Docker Desktop..."
open -a Docker

echo "⏳ Waiting for Docker Desktop to start..."
echo "   (This may take 30-60 seconds)"

# Wait for Docker to start (max 2 minutes)
for i in {1..24}; do
    if docker info > /dev/null 2>&1; then
        echo "✅ Docker Desktop is now running!"
        echo "🎯 You can now run: docker compose up -d"
        exit 0
    fi
    echo "   Waiting... ($i/24)"
    sleep 5
done

echo "⚠️  Docker Desktop is taking longer than expected to start"
echo "💡 Please check:"
echo "   - Docker Desktop app in your Applications"
echo "   - System resources (RAM, CPU)"
echo "   - Try restarting Docker Desktop manually"
exit 1