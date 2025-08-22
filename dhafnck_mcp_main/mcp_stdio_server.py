#!/usr/bin/env python3
"""
MCP STDIO Server for DhafnckMCP
This script starts the MCP server in STDIO mode for Claude Code integration.
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for STDIO mode
os.environ["FASTMCP_TRANSPORT"] = "stdio"
os.environ["FASTMCP_LOG_LEVEL"] = "INFO"

# Import and run the MCP entry point
from fastmcp.server.mcp_entry_point import main

if __name__ == "__main__":
    main()