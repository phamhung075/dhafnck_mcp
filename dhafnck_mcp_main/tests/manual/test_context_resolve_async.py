"""
Manual test to reproduce the 'coroutine' object is not subscriptable error
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from fastmcp.task_management.interface.controllers.context_mcp_controller import ContextMCPController
from fastmcp.task_management.application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory
from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
from fastmcp.task_management.application.services.context_inheritance_service import ContextInheritanceService
from fastmcp.task_management.application.services.context_delegation_service import ContextDelegationService
from fastmcp.task_management.application.services.context_cache_service import ContextCacheService

async def test_context_resolution():
    """Test context resolution to reproduce the error"""
    
    # Create services
    hierarchy_service = HierarchicalContextService()
    inheritance_service = ContextInheritanceService()
    delegation_service = ContextDelegationService()
    cache_service = ContextCacheService()
    
    # Create facade factory
    facade_factory = HierarchicalContextFacadeFactory()
    
    # Create controller
    controller = ContextMCPController(
        hierarchical_context_facade_factory=facade_factory,
        hierarchy_service=hierarchy_service,
        inheritance_service=inheritance_service,
        delegation_service=delegation_service,
        cache_service=cache_service
    )
    
    # Try to resolve a context
    print("Testing context resolution...")
    
    try:
        # Call the async handler directly
        result = await controller._handle_resolve_context(
            level="task",
            context_id="test-task-id",
            force_refresh=False
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context_resolution())