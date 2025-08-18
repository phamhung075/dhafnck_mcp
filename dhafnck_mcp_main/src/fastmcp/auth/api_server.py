#!/usr/bin/env python3
"""
Standalone Authentication API Server

This module provides a FastAPI server for authentication endpoints.
It runs alongside the MCP server to handle auth requests.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the auth router
from fastmcp.auth.interface.auth_endpoints import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DhafnckMCP Authentication API",
    description="Authentication service for DhafnckMCP platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3800", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "DhafnckMCP Authentication API", "version": "1.0.0"}

def main():
    """Run the authentication API server"""
    host = os.getenv("AUTH_API_HOST", "0.0.0.0")
    port = int(os.getenv("AUTH_API_PORT", "8001"))
    
    logger.info(f"Starting Authentication API server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()