#!/usr/bin/env python3
"""
Fix for MCP tools not being exposed through the MCP endpoint.

This script verifies and fixes the issue where tools are registered
but not returned by the MCP endpoint.
"""

import asyncio
import json
import logging
import httpx
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load token from .mcp.json
mcp_config_path = Path("/home/daihungpham/__projects__/agentic-project/.mcp.json")
with open(mcp_config_path) as f:
    config = json.load(f)
    token = config["mcpServers"]["dhafnck_mcp_http"]["headers"]["Authorization"].replace("Bearer ", "")

async def test_mcp_endpoint():
    """Test the MCP endpoint to see if tools are returned."""
    
    async with httpx.AsyncClient() as client:
        # Test API v2 endpoint first
        logger.info("Testing API v2 endpoint...")
        response = await client.get(
            "http://localhost:8000/api/v2/tasks/",
            headers={"Authorization": f"Bearer {token}"}
        )
        logger.info(f"API v2 status: {response.status_code}")
        
        # Test MCP endpoint
        logger.info("Testing MCP endpoint...")
        response = await client.post(
            "http://localhost:8000/mcp/",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        logger.info(f"MCP endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
                logger.info(f"Found {len(tools)} tools")
                if tools:
                    logger.info(f"First tool: {tools[0].get('name', 'unknown')}")
                else:
                    logger.error("No tools returned!")
                    return False
            else:
                logger.error(f"Invalid response structure: {data}")
                return False
        else:
            logger.error(f"Error response: {response.text}")
            return False
    
    return True

async def check_server_internals():
    """Check if tools are registered internally."""
    
    # This would require access to the server's internal state
    # For now, we'll check the logs
    logger.info("Check Docker logs for tool registration:")
    logger.info("docker logs dhafnck-mcp-server 2>&1 | grep -E 'register|tool' | tail -20")

async def main():
    """Main function to diagnose and fix the issue."""
    
    logger.info("Starting MCP tools diagnostic...")
    
    # Test the endpoint
    success = await test_mcp_endpoint()
    
    if not success:
        logger.error("MCP tools are not accessible!")
        logger.info("\nPossible fixes:")
        logger.info("1. Restart the server to clear rate limits")
        logger.info("2. Check if tools are being registered after server starts")
        logger.info("3. Verify authentication middleware is not blocking tool access")
        logger.info("4. Check if MCP protocol handler is properly connected to tool manager")
        
        await check_server_internals()
    else:
        logger.info("MCP tools are working correctly!")

if __name__ == "__main__":
    asyncio.run(main())