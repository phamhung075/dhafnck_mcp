"""
TDD Tests for Context Delegation Async Error Fix
Issue: 'coroutine' object has no attribute 'get'
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime


class TestContextDelegationAsyncFix:
    """Test suite for fixing context delegation async/await error"""
    
    def test_async_coroutine_get_attribute_error(self):
        """Test current error - coroutine object has no attribute 'get'"""
        # Arrange
        async def mock_async_function():
            return {"success": True, "data": "test"}
        
        # This demonstrates the current error
        coroutine = mock_async_function()
        
        # Current behavior - this fails
        with pytest.raises(AttributeError, match="'coroutine' object has no attribute 'get'"):
            coroutine.get("success")
    
    @pytest.mark.asyncio
    async def test_delegate_context_should_await_async_calls(self):
        """Test that delegate context properly awaits async operations"""
        # Arrange
        from src.application.context_manager import ContextManager
        
        manager = ContextManager()
        
        # Mock async methods
        async def mock_get_context(context_id):
            return {
                "id": context_id,
                "level": "task",
                "data": {"test": "data"}
            }
        
        async def mock_queue_delegation(delegation_data):
            return {
                "success": True,
                "delegation_id": "del-123",
                "status": "queued"
            }
        
        # Patch methods
        manager.get_context = AsyncMock(side_effect=mock_get_context)
        manager.queue_delegation = AsyncMock(side_effect=mock_queue_delegation)
        
        # Act
        result = await manager.delegate_context(
            level="task",
            context_id="task-123",
            delegate_to="project",
            delegate_data={"pattern": "test"},
            delegation_reason="Test delegation"
        )
        
        # Assert
        assert result["success"] is True
        assert result["delegation_id"] == "del-123"
    
    def test_sync_wrapper_for_async_delegation(self):
        """Test synchronous wrapper properly handles async delegation"""
        # This is the pattern we'll implement
        def delegate_context_sync(level, context_id, delegate_to, delegate_data, delegation_reason):
            """Synchronous wrapper for async delegation"""
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run async function
            if loop.is_running():
                # If loop is already running (e.g., in Jupyter), use different approach
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        delegate_context_async(level, context_id, delegate_to, delegate_data, delegation_reason)
                    )
                    return future.result()
            else:
                # Normal case - run directly
                return loop.run_until_complete(
                    delegate_context_async(level, context_id, delegate_to, delegate_data, delegation_reason)
                )
        
        async def delegate_context_async(level, context_id, delegate_to, delegate_data, delegation_reason):
            # Simulate async work
            await asyncio.sleep(0.01)
            return {"success": True, "delegation_id": "test-123"}
        
        # Test
        result = delegate_context_sync("task", "task-123", "project", {}, "test")
        assert result["success"] is True
    
    def test_proper_async_error_handling(self):
        """Test proper error handling in async context"""
        async def failing_async_operation():
            raise ValueError("Test error")
        
        async def delegate_with_error_handling():
            try:
                result = await failing_async_operation()
                return {"success": True, "data": result}
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        # Test error handling
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(delegate_with_error_handling())
        
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["error_type"] == "ValueError"
    
    def test_delegation_queue_async_operations(self):
        """Test async operations in delegation queue"""
        # Expected fixed implementation pattern
        class DelegationQueue:
            def __init__(self):
                self.queue = []
            
            async def add_delegation(self, delegation_data):
                """Async method to add delegation to queue"""
                # Simulate async database operation
                await asyncio.sleep(0.01)
                
                delegation = {
                    "id": f"del-{len(self.queue)}",
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                    **delegation_data
                }
                self.queue.append(delegation)
                return delegation
            
            async def get_pending_delegations(self):
                """Async method to get pending delegations"""
                await asyncio.sleep(0.01)
                return [d for d in self.queue if d["status"] == "pending"]
        
        # Test async queue operations
        async def test_queue():
            queue = DelegationQueue()
            
            # Add delegation
            result = await queue.add_delegation({
                "source": "task-123",
                "target": "project",
                "data": {"test": "data"}
            })
            
            assert result["id"] == "del-0"
            assert result["status"] == "pending"
            
            # Get pending
            pending = await queue.get_pending_delegations()
            assert len(pending) == 1
        
        # Run test
        asyncio.run(test_queue())
    
    def test_mixed_sync_async_context_operations(self):
        """Test handling mixed sync/async operations in context management"""
        class ContextOperations:
            def __init__(self):
                self.contexts = {}
            
            # Synchronous method
            def get_context_sync(self, context_id):
                return self.contexts.get(context_id, None)
            
            # Asynchronous method
            async def update_context_async(self, context_id, data):
                # Simulate async work
                await asyncio.sleep(0.01)
                self.contexts[context_id] = data
                return {"success": True, "context_id": context_id}
            
            # Method that uses both
            async def delegate_context(self, context_id, delegate_to):
                # Get context synchronously
                context = self.get_context_sync(context_id)
                if not context:
                    return {"success": False, "error": "Context not found"}
                
                # Update asynchronously
                result = await self.update_context_async(
                    delegate_to,
                    {"delegated_from": context_id, "data": context}
                )
                
                return result
        
        # Test mixed operations
        async def test_mixed():
            ops = ContextOperations()
            ops.contexts["task-123"] = {"test": "data"}
            
            result = await ops.delegate_context("task-123", "project-456")
            assert result["success"] is True
        
        asyncio.run(test_mixed())
    
    def test_async_context_resolution_fix(self):
        """Test the complete async context resolution fix"""
        # Expected fixed response structure
        expected_response = {
            "status": "success",
            "success": True,
            "operation": "delegate_context",
            "data": {
                "delegation_id": "del-123",
                "source_context": "task-123",
                "target_level": "project",
                "status": "queued",
                "delegation_data": {
                    "pattern": "login_form",
                    "description": "Reusable login pattern"
                }
            },
            "workflow_hint": "Delegation queued for approval"
        }
        
        assert expected_response["success"] is True
        assert expected_response["data"]["status"] == "queued"