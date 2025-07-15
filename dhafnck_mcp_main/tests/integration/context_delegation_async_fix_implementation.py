"""
Context Delegation Async Fix Implementation

This file demonstrates the complete fix for the async/await issue in context delegation
where process_delegation is async but not properly awaited.

Issue: 'coroutine' object has no attribute 'get'
Location: manage_hierarchical_context delegate action
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import concurrent.futures

logger = logging.getLogger(__name__)


class ContextDelegationAsyncFix:
    """
    Demonstrates the fixes needed for context delegation async issues.
    
    The main issue is that delegate_context in HierarchicalContextService
    calls process_delegation which is async, but doesn't await it properly.
    """
    
    @staticmethod
    def fix_hierarchical_context_service():
        """
        Fix for HierarchicalContextService.delegate_context method
        
        Current issue: The method is synchronous but calls async process_delegation
        """
        
        # OPTION 1: Make delegate_context async (breaks API compatibility)
        async def delegate_context_async(self, from_level: str, from_id: str,
                                       to_level: str, data: Dict[str, Any],
                                       reason: str = "Manual delegation") -> Dict[str, Any]:
            """Async version of delegate_context"""
            try:
                logger.info(f"Delegating from {from_level}:{from_id} to {to_level}")
                
                # Validate delegation direction
                level_hierarchy = {"task": 0, "project": 1, "global": 2}
                if level_hierarchy[from_level] >= level_hierarchy[to_level]:
                    raise ValueError(f"Cannot delegate from {from_level} to {to_level}")
                
                # Determine target ID
                target_id = self._resolve_target_id(from_level, from_id, to_level)
                
                # FIXED: Properly await async call
                result = await self.delegation_service.process_delegation(
                    source_level=from_level,
                    source_id=from_id,
                    target_level=to_level,
                    target_id=target_id,
                    delegated_data=data,
                    reason=reason
                )
                
                # Invalidate affected caches
                self.cache_service.invalidate_context_cache(to_level, target_id)
                
                logger.info(f"Delegation completed: {result.get('delegation_id')}")
                return result
                
            except Exception as e:
                logger.error(f"Error in delegation: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "from_level": from_level,
                    "from_id": from_id,
                    "to_level": to_level
                }
        
        # OPTION 2: Keep sync API but handle async internally (preferred)
        def delegate_context_sync_wrapper(self, from_level: str, from_id: str,
                                        to_level: str, data: Dict[str, Any],
                                        reason: str = "Manual delegation") -> Dict[str, Any]:
            """Sync wrapper that handles async delegation internally"""
            
            async def _async_delegate():
                try:
                    logger.info(f"Delegating from {from_level}:{from_id} to {to_level}")
                    
                    # Validate delegation direction
                    level_hierarchy = {"task": 0, "project": 1, "global": 2}
                    if level_hierarchy[from_level] >= level_hierarchy[to_level]:
                        raise ValueError(f"Cannot delegate from {from_level} to {to_level}")
                    
                    # Determine target ID
                    target_id = self._resolve_target_id(from_level, from_id, to_level)
                    
                    # FIXED: Properly await async call
                    result = await self.delegation_service.process_delegation(
                        source_level=from_level,
                        source_id=from_id,
                        target_level=to_level,
                        target_id=target_id,
                        delegated_data=data,
                        reason=reason
                    )
                    
                    # Invalidate affected caches
                    self.cache_service.invalidate_context_cache(to_level, target_id)
                    
                    logger.info(f"Delegation completed: {result.get('delegation_id')}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in delegation: {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": str(e),
                        "from_level": from_level,
                        "from_id": from_id,
                        "to_level": to_level
                    }
            
            # Execute async function in sync context
            return self._run_async_in_sync(_async_delegate())
        
        return delegate_context_sync_wrapper
    
    @staticmethod
    def fix_context_mcp_controller():
        """
        Fix for ContextMCPController._handle_delegate_context method
        
        Current issue: Not awaiting the result if delegate_context becomes async
        """
        
        async def _handle_delegate_context_fixed(self, from_level: str, from_id: str, 
                                               to_level: str, data: Dict[str, Any], 
                                               reason: str) -> Dict[str, Any]:
            """Fixed version that handles both sync and async delegate_context"""
            try:
                # Check if delegate_context is async
                if asyncio.iscoroutinefunction(self.hierarchy_service.delegate_context):
                    # If async, await it
                    result = await self.hierarchy_service.delegate_context(
                        from_level, from_id, to_level, data, reason
                    )
                else:
                    # If sync (with internal async handling), call directly
                    result = self.hierarchy_service.delegate_context(
                        from_level, from_id, to_level, data, reason
                    )
                
                if result.get("success"):
                    return {
                        "status": "success",
                        "success": True,
                        "operation": "delegate_context",
                        "data": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "success": False,
                        "operation": "delegate_context",
                        "error": result.get("error", "Delegation failed"),
                        "error_code": "OPERATION_FAILED",
                        "details": result
                    }
                    
            except Exception as e:
                logger.error(f"Error delegating context: {e}")
                return {
                    "status": "error",
                    "success": False,
                    "operation": "delegate_context",
                    "error": str(e),
                    "error_code": "INTERNAL_ERROR"
                }
        
        return _handle_delegate_context_fixed
    
    @staticmethod
    def create_async_sync_helper():
        """
        Helper method to run async code in sync context
        This should be added to HierarchicalContextService
        """
        
        def _run_async_in_sync(self, coro):
            """
            Run async coroutine in sync context safely.
            Handles nested event loops and various runtime scenarios.
            """
            try:
                # Try to get current event loop
                loop = asyncio.get_event_loop()
                
                if loop.is_running():
                    # We're in a running event loop (e.g., Jupyter, some web frameworks)
                    # Use ThreadPoolExecutor to run in separate thread
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, coro)
                        return future.result()
                else:
                    # We have a loop but it's not running
                    return loop.run_until_complete(coro)
                    
            except RuntimeError:
                # No event loop exists, create one
                return asyncio.run(coro)
            except Exception as e:
                logger.error(f"Error running async in sync: {e}")
                raise
        
        return _run_async_in_sync
    
    @staticmethod
    def fix_delegation_queue_operations():
        """
        Fix for manage_delegation_queue operations
        
        These are currently stubbed but should handle async delegation service
        """
        
        async def manage_delegation_queue_fixed(self, action: str, **kwargs) -> Dict[str, Any]:
            """Fixed version that properly handles async delegation operations"""
            try:
                if action == "list":
                    # Properly await async operations
                    delegations = await self.delegation_service.get_pending_delegations(
                        target_level=kwargs.get("target_level"),
                        target_id=kwargs.get("target_id")
                    )
                    return {
                        "status": "success",
                        "success": True,
                        "operation": "manage_delegation_queue",
                        "data": {
                            "pending_delegations": delegations,
                            "count": len(delegations)
                        }
                    }
                
                elif action == "approve":
                    delegation_id = kwargs.get("delegation_id")
                    if not delegation_id:
                        return {
                            "status": "error",
                            "success": False,
                            "operation": "manage_delegation_queue",
                            "error": "delegation_id is required for approve action",
                            "error_code": "MISSING_FIELD"
                        }
                    
                    result = await self.delegation_service.approve_delegation(
                        delegation_id,
                        approver=kwargs.get("approver", "system")
                    )
                    
                    return {
                        "status": "success" if result["success"] else "error",
                        "success": result["success"],
                        "operation": "manage_delegation_queue",
                        "data": result
                    }
                
                elif action == "reject":
                    delegation_id = kwargs.get("delegation_id")
                    if not delegation_id:
                        return {
                            "status": "error",
                            "success": False,
                            "operation": "manage_delegation_queue",
                            "error": "delegation_id is required for reject action",
                            "error_code": "MISSING_FIELD"
                        }
                    
                    result = await self.delegation_service.reject_delegation(
                        delegation_id,
                        reason=kwargs.get("rejection_reason", "No reason provided"),
                        rejector=kwargs.get("rejector", "system")
                    )
                    
                    return {
                        "status": "success" if result["success"] else "error",
                        "success": result["success"],
                        "operation": "manage_delegation_queue",
                        "data": result
                    }
                
                elif action == "get_status":
                    status = await self.delegation_service.get_queue_status()
                    return {
                        "status": "success",
                        "success": True,
                        "operation": "manage_delegation_queue",
                        "data": status
                    }
                
                else:
                    return {
                        "status": "error",
                        "success": False,
                        "operation": "manage_delegation_queue",
                        "error": f"Unknown action: {action}",
                        "error_code": "VALIDATION_ERROR"
                    }
                    
            except Exception as e:
                logger.error(f"Error in manage_delegation_queue: {e}", exc_info=True)
                return {
                    "status": "error",
                    "success": False,
                    "operation": "manage_delegation_queue",
                    "error": str(e),
                    "error_code": "INTERNAL_ERROR"
                }
        
        return manage_delegation_queue_fixed


# Example usage and testing
if __name__ == "__main__":
    # Demonstrate the fixes
    fixer = ContextDelegationAsyncFix()
    
    print("Context Delegation Async Fix Implementation")
    print("=" * 50)
    print("\n1. HierarchicalContextService Fix:")
    print("   - Add _run_async_in_sync helper method")
    print("   - Modify delegate_context to use sync wrapper")
    print("   - Properly await async process_delegation")
    
    print("\n2. ContextMCPController Fix:")
    print("   - Check if delegate_context is async")
    print("   - Await if necessary")
    print("   - Handle both sync and async versions")
    
    print("\n3. Delegation Queue Fix:")
    print("   - Properly await all async delegation service calls")
    print("   - Return consistent response format")
    
    print("\n4. Key Pattern:")
    print("   - Keep public API synchronous for MCP compatibility")
    print("   - Handle async operations internally with wrapper")
    print("   - Use _run_async_in_sync helper for safe execution")
    
    # Test the async sync helper
    async def test_async_operation():
        await asyncio.sleep(0.1)
        return {"success": True, "test": "passed"}
    
    # Mock service to test helper
    class MockService:
        def _run_async_in_sync(self, coro):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, coro)
                        return future.result()
                else:
                    return loop.run_until_complete(coro)
            except RuntimeError:
                return asyncio.run(coro)
    
    service = MockService()
    result = service._run_async_in_sync(test_async_operation())
    print(f"\n5. Test Result: {result}")
    print("\n✅ Fix implementation complete!")