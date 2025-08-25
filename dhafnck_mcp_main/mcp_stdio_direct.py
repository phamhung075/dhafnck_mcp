#!/usr/bin/env python3
"""
Direct STDIO MCP Server for DhafnckMCP
This script starts the MCP server in STDIO mode without authentication.
It directly exposes the DDD-compliant tools for Claude Code integration.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Set environment for STDIO mode
os.environ["FASTMCP_TRANSPORT"] = "stdio"
os.environ["FASTMCP_LOG_LEVEL"] = "WARNING"  # Reduce noise in STDIO mode

# Configure logging to file only (not stderr which interferes with STDIO)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_stdio_direct.log')
    ]
)

logger = logging.getLogger('mcp_stdio_direct')

def main():
    """Main entry point for STDIO MCP server"""
    try:
        logger.info("Starting STDIO MCP server...")
        
        # Import FastMCP
        from fastmcp.server.server import FastMCP
        
        # Create server instance without authentication
        mcp = FastMCP(
            "dhafnck-mcp-stdio",
            enable_task_management=False  # We'll add tools manually
        )
        
        logger.info("FastMCP server created")
        
        # Import and register DDD-compliant tools
        from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
        
        # Create tools instance
        tools = DDDCompliantMCPTools()
        logger.info("DDDCompliantMCPTools instance created")
        
        # Register all tool methods
        tool_methods = [
            # Core management tools
            "manage_project",
            "manage_task", 
            "manage_subtask",
            "manage_context",
            "manage_git_branch",
            "manage_connection",
            "manage_agent",
            "manage_compliance",
            "manage_rule",
            
            # Advanced tools
            "call_agent",
            "complete_task_with_update",
            "quick_task_update",
            "report_progress",
            "get_workflow_hints",
            "get_vision_alignment",
            "complete_task_with_context",
            "get_task_with_reminders",
            "manage_hierarchical_context",
            "manage_delegation_queue",
            "validate_context_inheritance",
            "validate_rules",
            
            # Utility tools
            "health_check",
            "get_server_capabilities"
        ]
        
        # Register each tool
        for method_name in tool_methods:
            if hasattr(tools, method_name):
                method = getattr(tools, method_name)
                mcp.tool()(method)
                logger.info(f"Registered tool: {method_name}")
            else:
                logger.warning(f"Tool method not found: {method_name}")
        
        logger.info(f"Registered {len(tool_methods)} tools")
        
        # Run the server
        logger.info("Starting MCP server main loop...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()