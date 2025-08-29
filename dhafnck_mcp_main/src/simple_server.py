#!/usr/bin/env python
"""Simple health check server for testing"""

from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="DhafnckMCP Health Check Server")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "dhafnck-mcp", "version": "simplified"}

@app.get("/")
async def root():
    return {"message": "DhafnckMCP Server Running (Simplified Mode)"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("simple_server:app", host="0.0.0.0", port=port, reload=False)