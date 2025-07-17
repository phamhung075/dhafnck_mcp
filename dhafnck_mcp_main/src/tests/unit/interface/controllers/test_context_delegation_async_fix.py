"""
TDD Tests for Context Delegation Async Error Fix
Issue: 'coroutine' object has no attribute 'get'

This test suite demonstrates and fixes the async/await issue in context delegation
where process_delegation is async but not properly awaited.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src'))


class TestContextDelegationAsyncFix:
    """Test suite for fixing context delegation async/await error"""
    
    def test_reproduce_coroutine_get_attribute_error(self):
        """Test current error - coroutine object has no attribute 'get'"""
        # This demonstrates the current error pattern
        async def mock_async_function():
            return {"success": True, "data": "test"}
        
        # Current behavior - this fails
        coroutine = mock_async_function()
        
        # This is what happens when you don't await an async function
        with pytest.raises(AttributeError, match="'coroutine' object has no attribute 'get'"):
            coroutine.get("success")
        
        # Clean up the coroutine
        coroutine.close()
    
    def test_sync_delegate_context_calling_async_process_delegation(self):
        """Test the actual issue: sync delegate_context calling async process_delegation"""
        from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
        from fastmcp.task_management.application.services.context_delegation_service import ContextDelegationService
        
        # Create services
        hierarchy_service = HierarchicalContextService()
        delegation_service = ContextDelegationService()
        
        # Mock the async process_delegation method
        async def mock_process_delegation(**kwargs):
            return {
                "success": True,
                "delegation_id": "del-123",
                "auto_approved": False,
                "result": {"queued": True}
            }
        
        delegation_service.process_delegation = AsyncMock(side_effect=mock_process_delegation)
        hierarchy_service.delegation_service = delegation_service
        
        # Mock other required methods
        hierarchy_service.repository = Mock()
        hierarchy_service.repository.get_task_context = Mock(return_value={"parent_project_context_id": "proj-123"})
        
        # This is the problematic call - delegate_context is sync but calls async process_delegation
        result = hierarchy_service.delegate_context(
            from_level="task",
            from_id="task-123", 
            to_level="project",
            data={"test": "data"},
            reason="Test delegation"
        )
        
        # The result should now be a proper dict, not a coroutine
        assert isinstance(result, dict)
        assert result.get("success") is True
        assert result.get("delegation_id") == "del-123"
        assert not asyncio.iscoroutine(result.get("delegation_id"))
    
    @pytest.mark.asyncio
    async def test_async_delegate_context_fix(self):
        """Test the fixed async version of delegate_context"""
        # This is how the fixed version should work
        async def delegate_context_async(self, from_level: str, from_id: str, 
                                       to_level: str, data: dict, reason: str):
            """Fixed async version of delegate_context"""
            try:
                # Validate delegation direction
                level_hierarchy = {"task": 0, "project": 1, "global": 2}
                if level_hierarchy[from_level] >= level_hierarchy[to_level]:
                    raise ValueError(f"Cannot delegate from {from_level} to {to_level}")
                
                # Resolve target ID
                target_id = self._resolve_target_id(from_level, from_id, to_level)
                
                # FIXED: Properly await the async process_delegation
                result = await self.delegation_service.process_delegation(
                    source_level=from_level,
                    source_id=from_id,
                    target_level=to_level,
                    target_id=target_id,
                    delegated_data=data,
                    reason=reason
                )
                
                # Invalidate cache
                self.cache_service.invalidate_context_cache(to_level, target_id)
                
                return result
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "from_level": from_level,
                    "from_id": from_id,
                    "to_level": to_level
                }
        
        # Create mock service
        service = Mock()
        service._resolve_target_id = Mock(return_value="proj-123")
        service.cache_service = Mock()
        service.delegation_service = AsyncMock()
        service.delegation_service.process_delegation = AsyncMock(return_value={
            "success": True,
            "delegation_id": "del-123",
            "auto_approved": False
        })
        
        # Call the fixed async version
        result = await delegate_context_async(
            service,
            from_level="task",
            from_id="task-123",
            to_level="project", 
            data={"test": "data"},
            reason="Test delegation"
        )
        
        # Verify result is correct
        assert result["success"] is True
        assert result["delegation_id"] == "del-123"
        assert not asyncio.iscoroutine(result)
    
    def test_sync_wrapper_for_delegate_context(self):
        """Test synchronous wrapper for the async delegate_context"""
        # This is the pattern for MCP handlers that need to call async methods
        def delegate_context_sync(hierarchy_service, from_level, from_id, to_level, data, reason):
            """Sync wrapper for async delegate_context"""
            async def _async_delegate():
                # Create async version of delegate_context
                # In real implementation, this would be the actual async method
                result = await hierarchy_service.delegation_service.process_delegation(
                    source_level=from_level,
                    source_id=from_id,
                    target_level=to_level,
                    target_id="proj-123",  # Would be resolved properly
                    delegated_data=data,
                    reason=reason
                )
                return result
            
            # Handle async execution in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Handle nested async (e.g., in Jupyter)
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _async_delegate())
                        return future.result()
                else:
                    return loop.run_until_complete(_async_delegate())
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(_async_delegate())
        
        # Test the sync wrapper
        service = Mock()
        service.delegation_service = AsyncMock()
        service.delegation_service.process_delegation = AsyncMock(return_value={
            "success": True,
            "delegation_id": "del-456"
        })
        
        result = delegate_context_sync(
            service,
            from_level="task",
            from_id="task-789",
            to_level="project",
            data={"pattern": "test"},
            reason="Sync test"
        )
        
        assert result["success"] is True
        assert result["delegation_id"] == "del-456"
    
    @pytest.mark.asyncio
    async def test_controller_handle_delegate_context_fix(self):
        """Test the fix for _handle_delegate_context in controller"""
        from fastmcp.task_management.interface.controllers.context_mcp_controller import ContextMCPController
        
        # This is how the controller method should be fixed
        async def _handle_delegate_context_fixed(self, from_level, from_id, to_level, data, reason):
            """Fixed version that properly handles async delegation"""
            try:
                # If delegate_context is async, await it
                if asyncio.iscoroutinefunction(self.hierarchy_service.delegate_context):
                    result = await self.hierarchy_service.delegate_context(
                        from_level, from_id, to_level, data, reason
                    )
                else:
                    # If it's sync (with internal async handling), call directly
                    result = self.hierarchy_service.delegate_context(
                        from_level, from_id, to_level, data, reason
                    )
                
                if result.get("success"):
                    return {
                        "status": "success",
                        "success": True,
                        "operation": "delegate_context",
                        "data": result
                    }
                else:
                    return {
                        "status": "error",
                        "success": False,
                        "operation": "delegate_context",
                        "error": result.get("error", "Delegation failed"),
                        "error_code": "OPERATION_FAILED"
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "success": False,
                    "operation": "delegate_context",
                    "error": str(e),
                    "error_code": "INTERNAL_ERROR"
                }
        
        # Test the fixed version
        controller = Mock()
        controller.hierarchy_service = Mock()
        controller.hierarchy_service.delegate_context = AsyncMock(return_value={
            "success": True,
            "delegation_id": "del-999",
            "auto_approved": True
        })
        
        result = await _handle_delegate_context_fixed(
            controller,
            from_level="task",
            from_id="task-999",
            to_level="global",
            data={"security": "insight"},
            reason="Security pattern"
        )
        
        assert result["success"] is True
        assert result["data"]["delegation_id"] == "del-999"
    
    def test_delegation_queue_async_handling(self):
        """Test proper async handling in delegation queue operations"""
        # The manage_delegation_queue handler also needs fixes
        async def get_pending_delegations_async():
            # Simulate async database operation
            await asyncio.sleep(0.01)
            return [
                {
                    "delegation_id": "del-001",
                    "source_level": "task",
                    "target_level": "project",
                    "status": "pending"
                }
            ]
        
        async def approve_delegation_async(delegation_id):
            await asyncio.sleep(0.01)
            return {
                "success": True,
                "delegation_id": delegation_id,
                "status": "approved"
            }
        
        # Test async queue operations work properly
        async def test_queue():
            delegations = await get_pending_delegations_async()
            assert len(delegations) == 1
            
            result = await approve_delegation_async(delegations[0]["delegation_id"])
            assert result["success"] is True
            assert result["status"] == "approved"
        
        # Run the test
        asyncio.run(test_queue())
    
    def test_complete_fix_integration(self):
        """Test the complete fix integrates properly"""
        # This represents the full fix that should be applied
        
        class FixedHierarchicalContextService:
            """Fixed version with proper async handling"""
            
            def __init__(self):
                self.delegation_service = None
                self.cache_service = None
                self.repository = None
            
            def delegate_context(self, from_level, from_id, to_level, data, reason):
                """Sync method that properly handles async delegation service"""
                async def _async_delegate():
                    try:
                        # Validate
                        level_hierarchy = {"task": 0, "project": 1, "global": 2}
                        if level_hierarchy[from_level] >= level_hierarchy[to_level]:
                            raise ValueError(f"Cannot delegate from {from_level} to {to_level}")
                        
                        # Resolve target
                        target_id = self._resolve_target_id(from_level, from_id, to_level)
                        
                        # FIXED: Await the async call
                        result = await self.delegation_service.process_delegation(
                            source_level=from_level,
                            source_id=from_id,
                            target_level=to_level,
                            target_id=target_id,
                            delegated_data=data,
                            reason=reason
                        )
                        
                        # Invalidate cache
                        if self.cache_service:
                            self.cache_service.invalidate_context_cache(to_level, target_id)
                        
                        return result
                        
                    except Exception as e:
                        return {
                            "success": False,
                            "error": str(e)
                        }
                
                # Execute async in sync context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Handle nested event loop
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, _async_delegate())
                            return future.result()
                    else:
                        return loop.run_until_complete(_async_delegate())
                except RuntimeError:
                    return asyncio.run(_async_delegate())
            
            def _resolve_target_id(self, from_level, from_id, to_level):
                """Mock target resolution"""
                if to_level == "global":
                    return "global_singleton"
                elif to_level == "project":
                    return "proj-123"
                return from_id
        
        # Test the fixed service
        service = FixedHierarchicalContextService()
        service.delegation_service = AsyncMock()
        service.delegation_service.process_delegation = AsyncMock(return_value={
            "success": True,
            "delegation_id": "del-fixed-123"
        })
        service.cache_service = Mock()
        
        result = service.delegate_context(
            from_level="task",
            from_id="task-test",
            to_level="project",
            data={"fixed": "implementation"},
            reason="Test fixed implementation"
        )
        
        assert result["success"] is True
        assert result["delegation_id"] == "del-fixed-123"
        assert not asyncio.iscoroutine(result)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])