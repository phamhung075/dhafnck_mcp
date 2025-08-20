"""
Tests for Thread Context Manager for MCP Operations

This module tests the ThreadContextManager which provides utilities for properly 
propagating user context across thread boundaries in MCP controllers.
"""

import pytest
import asyncio
import threading
import logging
from unittest.mock import Mock, patch, MagicMock
from contextvars import ContextVar

from fastmcp.auth.mcp_integration.thread_context_manager import (
    ThreadContextManager,
    ContextPropagationMixin,
    create_thread_context_manager,
    run_async_with_context,
    verify_context_propagation
)
from fastmcp.auth.mcp_integration.user_context_middleware import MCPUserContext, current_user_context


class TestThreadContextManager:
    """Test suite for ThreadContextManager"""
    
    @pytest.fixture
    def mock_user_context(self):
        """Create a mock user context"""
        return MCPUserContext(
            user_id="test-user-123",
            email="test@example.com",
            username="testuser",
            roles=["user", "developer"]
        )
    
    @pytest.fixture
    def context_manager(self):
        """Create a ThreadContextManager instance"""
        return ThreadContextManager()
    
    def test_capture_context_with_user(self, context_manager, mock_user_context):
        """Test capturing context when user context is available"""
        # Set user context
        current_user_context.set(mock_user_context)
        
        # Capture context
        result = context_manager.capture_context()
        
        # Verify
        assert result is context_manager  # Method chaining
        assert context_manager._captured_context == mock_user_context
        assert context_manager._captured_user_id == "test-user-123"
        assert context_manager.has_captured_context() is True
        assert context_manager.get_captured_user_id() == "test-user-123"
        
        # Clean up
        current_user_context.set(None)
    
    def test_capture_context_without_user(self, context_manager):
        """Test capturing context when no user context is available"""
        # Ensure no user context
        current_user_context.set(None)
        
        # Capture context
        result = context_manager.capture_context()
        
        # Verify
        assert result is context_manager
        assert context_manager._captured_context is None
        assert context_manager._captured_user_id is None
        assert context_manager.has_captured_context() is False
        assert context_manager.get_captured_user_id() is None
    
    @patch('fastmcp.auth.mcp_integration.thread_context_manager.get_current_user_context')
    def test_capture_context_with_exception(self, mock_get_context, context_manager):
        """Test capturing context when an exception occurs"""
        # Make get_current_user_context raise an exception
        mock_get_context.side_effect = Exception("Test error")
        
        # Capture context
        with patch.object(context_manager.__class__.__module__ + '.logger', 'warning') as mock_logger:
            result = context_manager.capture_context()
            
            # Verify warning was logged
            mock_logger.assert_called_once()
            assert "Failed to capture user context" in str(mock_logger.call_args)
        
        # Verify state
        assert result is context_manager
        assert context_manager._captured_context is None
        assert context_manager._captured_user_id is None
    
    def test_restore_context_success(self, context_manager, mock_user_context):
        """Test restoring captured context successfully"""
        # Manually set captured context
        context_manager._captured_context = mock_user_context
        context_manager._captured_user_id = "test-user-123"
        
        # Clear current context
        current_user_context.set(None)
        
        # Restore context
        result = context_manager.restore_context()
        
        # Verify
        assert result is True
        assert current_user_context.get() == mock_user_context
        
        # Clean up
        current_user_context.set(None)
    
    def test_restore_context_no_context(self, context_manager):
        """Test restoring when no context was captured"""
        # Ensure no captured context
        context_manager._captured_context = None
        
        # Restore context
        result = context_manager.restore_context()
        
        # Verify
        assert result is False
    
    @patch('fastmcp.auth.mcp_integration.user_context_middleware.current_user_context.set')
    def test_restore_context_with_exception(self, mock_set, context_manager, mock_user_context):
        """Test restoring context when an exception occurs"""
        # Set captured context
        context_manager._captured_context = mock_user_context
        
        # Make set raise an exception
        mock_set.side_effect = Exception("Test error")
        
        # Restore context
        with patch.object(context_manager.__class__.__module__ + '.logger', 'warning') as mock_logger:
            result = context_manager.restore_context()
            
            # Verify warning was logged
            mock_logger.assert_called_once()
            assert "Failed to restore user context" in str(mock_logger.call_args)
        
        # Verify result
        assert result is False
    
    @pytest.mark.asyncio
    async def test_run_async_with_context_success(self, context_manager, mock_user_context):
        """Test running async function with context propagation"""
        # Set user context
        current_user_context.set(mock_user_context)
        
        # Define async function that checks context
        captured_context = None
        captured_thread_id = None
        
        async def test_async_func(value):
            nonlocal captured_context, captured_thread_id
            captured_context = current_user_context.get()
            captured_thread_id = threading.current_thread().ident
            await asyncio.sleep(0.01)  # Simulate async work
            return value * 2
        
        # Get main thread ID
        main_thread_id = threading.current_thread().ident
        
        # Run with context
        result = context_manager.run_async_with_context(test_async_func, 5)
        
        # Verify
        assert result == 10
        assert captured_context is not None
        assert captured_context.user_id == "test-user-123"
        assert captured_thread_id != main_thread_id  # Ran in different thread
        
        # Clean up
        current_user_context.set(None)
    
    @pytest.mark.asyncio
    async def test_run_async_with_context_exception(self, context_manager, mock_user_context):
        """Test running async function that raises exception"""
        # Set user context
        current_user_context.set(mock_user_context)
        
        # Define async function that raises exception
        async def test_async_func():
            raise ValueError("Test exception")
        
        # Run with context and expect exception
        with pytest.raises(ValueError, match="Test exception"):
            context_manager.run_async_with_context(test_async_func)
        
        # Clean up
        current_user_context.set(None)
    
    @pytest.mark.asyncio
    async def test_run_async_with_context_no_context(self, context_manager):
        """Test running async function without user context"""
        # Ensure no user context
        current_user_context.set(None)
        
        # Define async function
        async def test_async_func():
            return "success"
        
        # Run with context
        result = context_manager.run_async_with_context(test_async_func)
        
        # Verify function still runs
        assert result == "success"
    
    def test_context_isolation_between_threads(self, context_manager):
        """Test that context is properly isolated between threads"""
        # Create different contexts for different threads
        context1 = MCPUserContext(
            user_id="user-1",
            email="user1@example.com",
            username="user1",
            roles=["role1"]
        )
        
        context2 = MCPUserContext(
            user_id="user-2",
            email="user2@example.com",
            username="user2",
            roles=["role2"]
        )
        
        results = {}
        
        async def check_context(thread_name):
            context = current_user_context.get()
            results[thread_name] = context.user_id if context else None
        
        # Set context1 in main thread
        current_user_context.set(context1)
        
        # Run first async function
        manager1 = ThreadContextManager()
        manager1.run_async_with_context(check_context, "thread1")
        
        # Change context in main thread
        current_user_context.set(context2)
        
        # Run second async function
        manager2 = ThreadContextManager()
        manager2.run_async_with_context(check_context, "thread2")
        
        # Verify each thread got the correct context
        assert results["thread1"] == "user-1"
        assert results["thread2"] == "user-2"
        
        # Clean up
        current_user_context.set(None)


class TestContextPropagationMixin:
    """Test the ContextPropagationMixin"""
    
    class TestController(ContextPropagationMixin):
        """Test controller with mixin"""
        pass
    
    @pytest.mark.asyncio
    async def test_mixin_run_async_with_context(self):
        """Test mixin provides _run_async_with_context method"""
        controller = self.TestController()
        
        # Define async function
        async def test_func():
            return "mixin_success"
        
        # Run using mixin method
        result = controller._run_async_with_context(test_func)
        
        # Verify
        assert result == "mixin_success"


class TestFactoryFunctions:
    """Test factory and convenience functions"""
    
    def test_create_thread_context_manager(self):
        """Test factory creates ThreadContextManager instance"""
        manager = create_thread_context_manager()
        assert isinstance(manager, ThreadContextManager)
    
    @pytest.mark.asyncio
    async def test_run_async_with_context_convenience(self):
        """Test convenience function for running async with context"""
        # Define async function
        async def test_func(x, y):
            return x + y
        
        # Run using convenience function
        result = run_async_with_context(test_func, 3, 4)
        
        # Verify
        assert result == 7


class TestVerifyContextPropagation:
    """Test context verification utility"""
    
    def test_verify_context_with_user(self):
        """Test verification when user context is available"""
        # Set user context
        user_context = MCPUserContext(
            user_id="verify-user-123",
            email="verify@example.com",
            username="verifyuser",
            roles=["admin", "tester"]
        )
        current_user_context.set(user_context)
        
        # Verify
        result = verify_context_propagation()
        
        # Check results
        assert result["context_available"] is True
        assert result["user_id"] == "verify-user-123"
        assert result["user_context"]["user_id"] == "verify-user-123"
        assert result["user_context"]["email"] == "verify@example.com"
        assert result["user_context"]["roles"] == ["admin", "tester"]
        assert result["verification_successful"] is True
        
        # Clean up
        current_user_context.set(None)
    
    def test_verify_context_without_user(self):
        """Test verification when no user context is available"""
        # Ensure no user context
        current_user_context.set(None)
        
        # Verify
        result = verify_context_propagation()
        
        # Check results
        assert result["context_available"] is False
        assert result["user_id"] is None
        assert result["user_context"] is None
        assert result["verification_successful"] is True
    
    @patch('fastmcp.auth.mcp_integration.thread_context_manager.get_current_user_context')
    def test_verify_context_with_exception(self, mock_get_context):
        """Test verification when an exception occurs"""
        # Make get_current_user_context raise an exception
        mock_get_context.side_effect = Exception("Verification error")
        
        # Verify
        result = verify_context_propagation()
        
        # Check results
        assert result["context_available"] is False
        assert result["user_id"] is None
        assert result["user_context"] is None
        assert result["verification_successful"] is False
        assert result["error"] == "Verification error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])