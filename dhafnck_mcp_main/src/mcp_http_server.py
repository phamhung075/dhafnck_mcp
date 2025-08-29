#!/usr/bin/env python
"""HTTP Server for MCP Tools - Exposes MCP functionality via REST API"""

import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DhafnckMCP HTTP Server",
    description="REST API for MCP Task Management Tools",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP tools
mcp_tools = None
try:
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    mcp_tools = DDDCompliantMCPTools()
    logger.info("MCP tools initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP tools: {e}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dhafnck-mcp",
        "version": "1.0.0",
        "mcp_tools": mcp_tools is not None
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DhafnckMCP HTTP Server Running",
        "endpoints": {
            "/health": "Health check",
            "/mcp/manage_task": "Task management",
            "/mcp/manage_context": "Context management",
            "/mcp/manage_project": "Project management",
            "/mcp/manage_git_branch": "Git branch management",
            "/mcp/manage_subtask": "Subtask management"
        }
    }

@app.post("/mcp/manage_task")
async def manage_task(request: Dict[str, Any]):
    """Manage tasks"""
    if not mcp_tools:
        raise HTTPException(status_code=503, detail="MCP tools not available")
    
    try:
        result = mcp_tools.manage_task(**request)
        return result
    except Exception as e:
        logger.error(f"Error in manage_task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/manage_context")
async def manage_context(request: Dict[str, Any]):
    """Manage context"""
    if not mcp_tools:
        raise HTTPException(status_code=503, detail="MCP tools not available")
    
    try:
        result = mcp_tools.manage_context(**request)
        return result
    except Exception as e:
        logger.error(f"Error in manage_context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/manage_project")
async def manage_project(request: Dict[str, Any]):
    """Manage projects"""
    if not mcp_tools:
        raise HTTPException(status_code=503, detail="MCP tools not available")
    
    try:
        result = mcp_tools.manage_project(**request)
        return result
    except Exception as e:
        logger.error(f"Error in manage_project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/manage_git_branch")
async def manage_git_branch(request: Dict[str, Any]):
    """Manage git branches"""
    if not mcp_tools:
        raise HTTPException(status_code=503, detail="MCP tools not available")
    
    try:
        result = mcp_tools.manage_git_branch(**request)
        return result
    except Exception as e:
        logger.error(f"Error in manage_git_branch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/manage_subtask")
async def manage_subtask(request: Dict[str, Any]):
    """Manage subtasks"""
    if not mcp_tools:
        raise HTTPException(status_code=503, detail="MCP tools not available")
    
    try:
        result = mcp_tools.manage_subtask(**request)
        return result
    except Exception as e:
        logger.error(f"Error in manage_subtask: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    if not mcp_tools:
        return {"tools": [], "error": "MCP tools not initialized"}
    
    try:
        # Get list of available tools
        tools = []
        for attr_name in dir(mcp_tools):
            if not attr_name.startswith('_') and callable(getattr(mcp_tools, attr_name)):
                tools.append(attr_name)
        return {"tools": tools}
    except Exception as e:
        return {"tools": [], "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting MCP HTTP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)