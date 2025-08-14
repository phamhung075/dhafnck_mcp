#!/bin/bash
# Script to rebuild and restart Supabase configuration

echo "🛑 Stopping existing containers..."
docker stop dhafnck-backend dhafnck-frontend 2>/dev/null
docker rm dhafnck-backend dhafnck-frontend 2>/dev/null

echo "🔧 Rebuilding Docker images..."
cd docker-system/docker

# Build backend with fresh code
echo "Building backend..."
docker build -t dhafnck-backend \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -f ../../dhafnck_mcp_main/docker/Dockerfile \
  ../..

echo "🚀 Starting with Supabase configuration..."
docker-compose --env-file ../../.env -f docker-compose.supabase.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Services restarted. Testing connection..."
curl -s http://localhost:8000/health || echo "Backend not ready yet"

echo ""
echo "📊 To check logs:"
echo "  docker logs dhafnck-backend --tail 50"
echo ""
echo "🔍 To verify Supabase connection:"
echo "  docker exec dhafnck-backend env | grep SUPABASE"
