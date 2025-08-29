#!/usr/bin/env python
"""Test server for MCP functionality"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set environment variables
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://dhafnck_user:dev_password@postgres:5432/dhafnck_mcp')

try:
    from fastapi import FastAPI
    import uvicorn
    
    # Create a simple FastAPI app for testing
    app = FastAPI(title="DhafnckMCP Test Server")
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "dhafnck-mcp-test", "version": "test"}
    
    @app.get("/")
    async def root():
        return {"message": "DhafnckMCP Test Server Running"}
    
    # Try to import and use MCP tools
    mcp_error = None
    try:
        from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
        tools = DDDCompliantMCPTools()
        
        @app.get("/test-mcp")
        async def test_mcp():
            return {"status": "MCP tools loaded successfully", "tools_available": True}
    except Exception as e:
        mcp_error = str(e)
        print(f"Warning: Could not load MCP tools: {mcp_error}")
        
        @app.get("/test-mcp")
        async def test_mcp():
            return {"status": "MCP tools not available", "error": mcp_error}
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
        
except Exception as e:
    print(f"Failed to start test server: {e}")
    # Fallback to simple server
    from simple_server import app
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)