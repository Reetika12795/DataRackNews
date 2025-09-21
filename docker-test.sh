#!/bin/bash
# Docker Build and Test Script for DataRackNews

echo "🐳 DataRackNews Docker Setup Test"
echo "=================================="

# Check if Docker is installed
if ! command -v docker > /dev/null 2>&1; then
    echo "❌ Docker is not installed. Please install Docker Desktop from:"
    echo "   https://docs.docker.com/desktop/install/mac/"
    exit 1
fi

echo "✅ Docker is installed"

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running."
    echo ""
    echo "🔧 To fix this issue:"
    echo "   1. Start Docker Desktop application"
    echo "   2. Wait for Docker to fully start (whale icon in menu bar)"
    echo "   3. You can start Docker Desktop by:"
    echo "      - Opening Applications -> Docker"
    echo "      - Or running: open -a Docker"
    echo ""
    echo "💡 If Docker Desktop is already running:"
    echo "   - Restart Docker Desktop"
    echo "   - Check Docker Desktop settings"
    echo "   - Try: docker system prune (to clean up)"
    echo ""
    exit 1
fi

echo "✅ Docker daemon is running"

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo "✅ Docker Compose is available"

# Build the Docker image
echo "📦 Building Docker image..."
if ! docker build -t datarack-news .; then
    echo "❌ Failed to build Docker image"
    echo "💡 Common fixes:"
    echo "   - Check Dockerfile syntax"
    echo "   - Ensure all required files exist"
    echo "   - Try: docker system prune -f"
    exit 1
fi

echo "✅ Docker image built successfully"

# Test docker-compose configuration
echo "🔧 Validating docker-compose.yml..."
if ! docker compose config > /dev/null; then
    echo "❌ docker-compose.yml validation failed"
    exit 1
fi

echo "✅ docker-compose.yml is valid"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env with your actual API keys before running:"
    echo "   nano .env"
    echo ""
fi

echo ""
echo "🚀 Setup complete! To start the application:"
echo "   docker compose up -d"
echo ""
echo "🌐 Access the application at: http://localhost:7860"
echo ""
echo "📊 To view logs:"
echo "   docker compose logs -f datarack-web"
echo ""
echo "🛑 To stop:"
echo "   docker compose down"
echo ""
echo "🔧 If you encounter issues:"
echo "   docker compose logs     # View all logs"
echo "   docker system prune     # Clean up Docker"
echo "   ./docker-test.sh        # Re-run this test"