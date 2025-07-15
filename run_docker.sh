#!/bin/bash

# This script manages the startup of Docker environments for the project.
# It supports two primary modes: development (--dev or -d) and normal mode.
# - Development mode integrates additional tools like MCP inspector for debugging and hot reload.
# - Normal mode runs the standard Docker setup via dhafnck_mcp_main/docker/mcp-docker.py for production-like or standard operations.
# The script handles environment activation and process management, ensuring dependencies are met before execution.

# Check for dev mode flag
if [ "$1" = "--dev" ] || [ "$1" = "-d" ]; then
  echo "Starting Docker dev mode with MCP inspector..."
  
  # Activate the virtual environment
  # This step is critical as it ensures all Python dependencies are available
  # Must run before any Python-based operations or Docker Compose commands that rely on the environment
  if [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    echo "Virtual environment (.venv) not found. Please create it with 'python3 -m venv .venv' and install dependencies."
    exit 1
  fi
  
  # Start containers in dev mode (detached with volumes for hot reload)
  # This command uses specific compose files for base setup and Redis persistence
  # Run after environment activation to ensure Docker Compose has access to necessary tools
  docker compose -f dhafnck_mcp_main/docker/docker-compose.yml -f dhafnck_mcp_main/docker/docker-compose.redis.yml up -d --build
  
  # Wait for containers to be ready
  # A delay is necessary to ensure containers are fully initialized before additional tools are started
  # Run after container startup to avoid race conditions with dependent services
  echo "Waiting for containers to be ready..."
  sleep 5
  
  # Start MCP inspector in background
  # MCP inspector is a debugging tool that monitors and interacts with the running containers
  # Run after containers are up to ensure there are services to inspect
  echo "Starting MCP inspector..."
  npx @modelcontextprotocol/inspector dhafnck_mcp_main/run_mcp_server.sh &
  INSPECTOR_PID=$!
  
  # Show container logs including frontend
  # Logs provide real-time feedback on container status and errors
  # Run after starting containers and inspector to capture all relevant output
  echo "Starting log monitoring (Ctrl+C to stop)..."
  echo "Frontend will be available at http://localhost:3800"
  docker compose -f dhafnck_mcp_main/docker/docker-compose.yml -f dhafnck_mcp_main/docker/docker-compose.redis.yml logs -f &
  LOGS_PID=$!
  
  # Trap Ctrl+C to clean up background processes
  # Ensures that background processes (inspector and logs) are terminated cleanly on script interruption
  # Set up after starting background tasks to handle user interruption
  trap 'echo "Stopping dev mode..."; kill $INSPECTOR_PID $LOGS_PID 2>/dev/null; exit' INT
  
  # Keep script running
  # Waits for background processes to complete or for user interruption
  # Run as the final step to maintain script execution until stopped
  wait
else
  # Normal mode - activate the virtual environment and run dhafnck_mcp_main/docker/mcp-docker.py
  # Normal mode delegates to dhafnck_mcp_main/docker/mcp-docker.py for standard Docker operations
  # Environment activation must run first to ensure dependencies are available for the Python script
  if [ -d ".venv" ]; then
    source .venv/bin/activate
    python dhafnck_mcp_main/docker/mcp-docker.py
  else
    echo "Virtual environment (.venv) not found. Please create it with 'python3 -m venv .venv' and install dependencies."
    exit 1
  fi
fi