#!/bin/bash

# Ultra-fast Docker development script
# Optimized for maximum hot reload performance

# Check for dev mode flag
if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
  echo "🚀 Starting Ultra-Fast Docker dev mode with optimized hot reload..."
  
  # Activate the virtual environment
  if [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    echo "Virtual environment (.venv) not found. Please create it with 'python3 -m venv .venv' and install dependencies."
    exit 1
  fi
  
  # Start containers in ultra-fast dev mode
  echo "🔧 Using optimized bind mounts for maximum performance..."
  docker compose -f dhafnck_mcp_main/docker/docker-compose.yml -f dhafnck_mcp_main/docker/docker-compose.dev-fast.yml up -d --build
  
  # Wait for containers to be ready (shorter wait time)
  echo "⏳ Waiting for containers to be ready..."
  sleep 3
  
  # Start MCP inspector in background
  echo "🔍 Starting MCP inspector..."
  npx @modelcontextprotocol/inspector dhafnck_mcp_main/run_mcp_server.sh &
  INSPECTOR_PID=$!
  
  # Show container logs
  echo "📋 Starting optimized log monitoring (Ctrl+C to stop)..."
  docker compose -f dhafnck_mcp_main/docker/docker-compose.yml -f dhafnck_mcp_main/docker/docker-compose.dev-fast.yml logs -f dhafnck-mcp &
  LOGS_PID=$!
  
  # Display development information
  echo ""
  echo "🎯 Development server ready!"
  echo "   📡 MCP Server: http://localhost:8000"
  echo "   🔧 Debug Port: http://localhost:8001"
  echo "   📊 Redis: localhost:6379"
  echo "   🔥 Hot Reload: ENABLED (0.05s detection)"
  echo "   📁 Source mounted with bind mounts for maximum speed"
  echo ""
  echo "💡 Tips for fastest development:"
  echo "   • Save files and see changes in ~50ms"
  echo "   • Use 'docker exec -it dhafnck-mcp-server /bin/bash' for shell access"
  echo "   • Check logs above for any file change detection issues"
  echo ""
  
  # Trap Ctrl+C to clean up background processes
  trap 'echo "🛑 Stopping ultra-fast dev mode..."; kill $INSPECTOR_PID $LOGS_PID 2>/dev/null; exit' INT
  
  # Keep script running
  wait
else
  # Fallback to standard mode
  echo "Using standard mode. Use -d or --dev for ultra-fast hot reload."
  if [ -d ".venv" ]; then
    source .venv/bin/activate
    python mcp-docker.py
  else
    echo "Virtual environment (.venv) not found. Please create it with 'python3 -m venv .venv' and install dependencies."
    exit 1
  fi
fi