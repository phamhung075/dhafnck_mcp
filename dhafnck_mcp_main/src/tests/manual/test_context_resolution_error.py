#!/usr/bin/env python3
"""Test script to reproduce the context resolution error"""

import asyncio
import logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.fastmcp.task_management.interface.controllers.context_mcp_controller import ContextMCPController
from src.fastmcp.task_management.application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_context_resolution():
    """Test the manage_hierarchical_context resolve action"""
    try:
        # Create controller
        facade_factory = HierarchicalContextFacadeFactory()
        controller = ContextMCPController(facade_factory)
        
        # Test data
        test_params = {
            "action": "resolve",
            "level": "task",
            "context_id": "test-task-123",
            "force_refresh": False,
            "propagate_changes": True
        }
        
        # Mock MCP server
        class MockMCP:
            def tool(self, name, description):
                def decorator(func):
                    return func
                return decorator
        
        mcp = MockMCP()
        controller.register_tools(mcp)
        
        # Call the function directly
        result = await controller.manage_hierarchical_context(**test_params)
        
        print(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_context_resolution())