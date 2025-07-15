#!/bin/bash

# DhafnckMCP Docker Runner Script
# Handles both detached (-d) and interactive modes

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Container name
CONTAINER_NAME="dhafnck-mcp-server"

# Check if -d flag is provided
DETACHED=false
if [[ "$1" == "-d" ]]; then
    DETACHED=true
    shift # Remove -d from arguments
fi

echo -e "${BLUE}🚀 Starting DhafnckMCP Server${NC}"
echo "=================================================="

# Change to project directory
cd "$PROJECT_ROOT"

# Check if container is already running
if docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}⚠️  Container '${CONTAINER_NAME}' is already running${NC}"
    echo "🌐 Server should be available at: http://localhost:8000"
    exit 0
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/tasks data/projects data/rules logs

# Set permissions
echo "🔐 Setting permissions..."
chmod -R 755 data logs 2>/dev/null || echo "⚠️  Permission warnings ignored (normal in WSL)"

if [ "$DETACHED" = true ]; then
    echo -e "${GREEN}🔄 Starting container in detached mode (ALL TOOLS ENABLED)...${NC}"
    # Use only base compose file to avoid disabling tools
    docker-compose -f docker/docker-compose.yml up --build -d
    
    echo ""
    echo -e "${GREEN}✅ DhafnckMCP Server is running in background!${NC}"
    echo "🌐 Server URL: http://localhost:8000"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo "📊 Server Capabilities: http://localhost:8000/capabilities"
    echo ""
    echo "💡 To view logs: docker logs -f ${CONTAINER_NAME}"
    echo "💡 To stop: docker stop ${CONTAINER_NAME}"
    echo "💡 To restart: docker restart ${CONTAINER_NAME}"
else
    echo -e "${GREEN}🔄 Starting container in interactive mode (SOME TOOLS DISABLED)...${NC}"
    echo "📝 Note: Using local development config - some cursor tools disabled"
    echo "💡 For all tools, use: $0 -d"
    echo ""
    
    # Use local development config which disables some tools
    docker-compose -f docker/docker-compose.yml -f docker/docker-compose.local.yml up --build
fi