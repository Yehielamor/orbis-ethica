#!/bin/bash
echo "🚀 Deploying Orbis Ethica to Production..."

# 1. Pull latest changes (if git repo)
# git pull origin main

# 2. Build and Start Containers
echo "📦 Building Containers..."
docker-compose up -d --build

# 3. Health Check
echo "🏥 Checking Health..."
sleep 10
if curl -f http://localhost:8000/health; then
    echo "✅ Backend is Healthy!"
else
    echo "❌ Backend Health Check Failed!"
    exit 1
fi

echo "✅ Deployment Complete! Access at http://localhost:80"
