#!/bin/bash

# Production Deployment Script for Betting Bot
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="betting-bot"
DOCKER_IMAGE="$PROJECT_NAME:$ENVIRONMENT"

echo "🚀 Deploying $PROJECT_NAME to $ENVIRONMENT environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy env.production to .env and configure it."
    exit 1
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.production -t $DOCKER_IMAGE .

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.production.yml down || true

# Start new containers
echo "🚀 Starting new containers..."
docker-compose -f docker-compose.production.yml up -d

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check if bot is running
if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
    echo "✅ Deployment successful!"
    echo "📊 Monitoring available at: http://localhost:3000 (Grafana)"
    echo "📈 Metrics available at: http://localhost:9090 (Prometheus)"
    echo "🤖 Bot is running in production mode"
else
    echo "❌ Deployment failed. Check logs:"
    docker-compose -f docker-compose.production.yml logs
    exit 1
fi

# Show running containers
echo "📋 Running containers:"
docker-compose -f docker-compose.production.yml ps

echo "🎉 Deployment complete!"
