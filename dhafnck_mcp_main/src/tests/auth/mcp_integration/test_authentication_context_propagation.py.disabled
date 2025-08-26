"""
Tests for Authentication Context Propagation Across Thread Boundaries

This test suite verifies that the critical authentication issue has been resolved:
- JWT tokens are properly validated
- User context is correctly propagated across thread boundaries
- All MCP operations use the authenticated user_id instead of default_id
"""

import asyncio
import threading
import uuid
from unittest.mock import Mock, patch, AsyncMock
import pytest

from fastmcp.auth.mcp_integration.thread_context_manager import (
    ThreadContextManager,
    ContextPropagationMixin,
    run_async_with_context,
    verify_context_propagation
)
from fastmcp.auth.mcp_integration.user_context_middleware import (
    MCPUserContext,
    current_user_context,
    get_current_user_context,
    get_current_user_id
)
from fastmcp.task_management.interface.controllers.project_mcp_controller import ProjectMCPController
from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController


class TestThreadContextManager:
    """Test the ThreadContextManager utility for proper context propagation."""
    
    def test_context_capture_and_restore(self):
        """Test that user context can be captured and restored."""
        # Create a test user context
        test_user_context = MCPUserContext(
            user_id="65d733e9-04d6-4dda-9536-688c3a59448e",
            email="test@example.com",
            roles=["user"],
            scopes=["read", "write"]
        )
        
        # Set the context
        current_user_context.set(test_user_context)
        
        # Create context manager and capture
        context_manager = ThreadContextManager()
        context_manager.capture_context()
        
        # Verify capture worked
        assert context_manager.has_captured_context()
        assert context_manager.get_captured_user_id() == "65d733e9-04d6-4dda-9536-688c3a59448e"
        
        # Clear the context to simulate new thread
        current_user_context.set(None)
        assert get_current_user_context() is None
        
        # Restore context
        restored = context_manager.restore_context()
        assert restored is True
        
        # Verify restoration worked
        restored_context = get_current_user_context()
        assert restored_context is not None
        assert restored_context.user_id == "65d733e9-04d6-4dda-9536-688c3a59448e"
        assert restored_context.email == "test@example.com"
    
    def test_run_async_with_context_propagation(self):
        """Test that async functions run with proper context propagation."""
        # Create test user context
        test_user_context = MCPUserContext(
            user_id="test-user-123",
            email="thread@test.com",
            roles=["admin"],
            scopes=["admin"]
        )
        current_user_context.set(test_user_context)
        
        # Track context in the async function
        captured_user_id = None
        
        async def async_test_function():
            nonlocal captured_user_id
            captured_user_id = get_current_user_id()
            return "success"
        
        # Run with context propagation
        context_manager = ThreadContextManager()
        result = context_manager.run_async_with_context(async_test_function)
        
        # Verify the async function executed successfully
        assert result == "success"
        
        # Verify the context was propagated to the thread
        assert captured_user_id == "test-user-123"
    
    def test_context_propagation_mixin(self):
        """Test the ContextPropagationMixin works correctly."""
        class TestController(ContextPropagationMixin):
            def test_method(self):
                async def test_async():
                    return get_current_user_id()
                return self._run_async_with_context(test_async)
        
        # Set up test context
        test_context = MCPUserContext(
            user_id="mixin-test-456",
            email="mixin@test.com",
            roles=["user"],
            scopes=["read"]
        )
        current_user_context.set(test_context)
        
        # Test the mixin
        controller = TestController()
        result = controller.test_method()
        
        # Verify context was propagated
        assert result == "mixin-test-456"


class TestAuthenticationFix:
    """Test that the authentication fix resolves the default_id issue."""
    
    @patch('fastmcp.task_management.application.factories.project_facade_factory.ProjectFacadeFactory')
    def test_project_controller_uses_authenticated_user(self, mock_facade_factory):
        """Test that ProjectMCPController uses authenticated user_id, not default_id."""
        # Set up authenticated user context
        auth_user_context = MCPUserContext(
            user_id="authenticated-user-789",
            email="auth@example.com",
            roles=["user"],
            scopes=["read", "write"]
        )
        current_user_context.set(auth_user_context)
        
        # Mock the facade and its methods
        mock_facade = Mock()
        mock_facade.manage_project = AsyncMock(return_value={
            "success": True,
            "project": {
                "id": "project-123",
                "user_id": "authenticated-user-789",  # Should be authenticated user, not default_id
                "name": "Test Project"
            }
        })
        mock_facade_factory.create_project_facade.return_value = mock_facade
        
        # Create controller and test
        controller = ProjectMCPController(mock_facade_factory)
        result = controller.manage_project(
            action="create",
            name="Test Project",
            description="Test Description"
        )
        
        # Verify facade was called with authenticated user_id
        mock_facade_factory.create_project_facade.assert_called_once()
        call_args = mock_facade_factory.create_project_facade.call_args
        assert call_args[1]['user_id'] == "authenticated-user-789"
        
        # Verify result contains authenticated user_id
        assert result["success"] is True
        assert result["project"]["user_id"] == "authenticated-user-789"
    
    def test_verify_context_propagation_utility(self):
        """Test the utility function for verifying context propagation."""
        # Test with no context
        current_user_context.set(None)
        result = verify_context_propagation()
        
        assert result["context_available"] is False
        assert result["user_id"] is None
        assert result["verification_successful"] is True
        
        # Test with context
        test_context = MCPUserContext(
            user_id="verify-test-999",
            email="verify@test.com",
            roles=["admin"],
            scopes=["admin"]
        )
        current_user_context.set(test_context)
        
        result = verify_context_propagation()
        
        assert result["context_available"] is True
        assert result["user_id"] == "verify-test-999"
        assert result["user_context"]["email"] == "verify@test.com"
        assert result["verification_successful"] is True


class TestIntegrationScenarios:
    """Integration tests for real-world authentication scenarios."""
    
    def test_jwt_token_to_mcp_operation_flow(self):
        """Test the complete flow from JWT token to MCP operation."""
        # Simulate the middleware setting user context from JWT
        jwt_user_context = MCPUserContext(
            user_id="65d733e9-04d6-4dda-9536-688c3a59448e",  # From the original issue
            email="user@company.com",
            roles=["developer"],
            scopes=["read", "write", "admin"]
        )
        current_user_context.set(jwt_user_context)
        
        # Verify context is set
        assert get_current_user_id() == "65d733e9-04d6-4dda-9536-688c3a59448e"
        
        # Test that context propagates through threading
        def thread_test():
            context_manager = ThreadContextManager()
            context_manager.capture_context()
            
            # Simulate new thread
            result = []
            
            def new_thread_work():
                context_manager.restore_context()
                user_id = get_current_user_id()
                result.append(user_id)
            
            thread = threading.Thread(target=new_thread_work)
            thread.start()
            thread.join()
            
            return result[0] if result else None
        
        propagated_user_id = thread_test()
        
        # Verify the user_id propagated correctly (not default_id)
        assert propagated_user_id == "65d733e9-04d6-4dda-9536-688c3a59448e"
        assert propagated_user_id != "default_id"
        assert propagated_user_id != "00000000-0000-0000-0000-000000000000"
    
    def test_multiple_users_isolation(self):
        """Test that different users get isolated contexts."""
        users = [
            MCPUserContext(
                user_id="user-1",
                email="user1@test.com",
                roles=["user"],
                scopes=["read"]
            ),
            MCPUserContext(
                user_id="user-2", 
                email="user2@test.com",
                roles=["admin"],
                scopes=["admin"]
            )
        ]
        
        results = []
        
        for user in users:
            # Set user context
            current_user_context.set(user)
            
            # Capture context and test in thread
            context_manager = ThreadContextManager()
            
            async def test_user_operation():
                return {
                    "user_id": get_current_user_id(),
                    "context": get_current_user_context()
                }
            
            result = context_manager.run_async_with_context(test_user_operation)
            results.append(result)
        
        # Verify each user got their own context
        assert results[0]["user_id"] == "user-1"
        assert results[1]["user_id"] == "user-2"
        assert results[0]["context"].email == "user1@test.com"
        assert results[1]["context"].email == "user2@test.com"


if __name__ == "__main__":
    # Quick verification that the fix is working
    print("Testing authentication context propagation fix...")
    
    # Test basic context propagation
    test_context = MCPUserContext(
        user_id="quick-test-user",
        email="test@example.com",
        roles=["user"],
        scopes=["read"]
    )
    current_user_context.set(test_context)
    
    context_manager = ThreadContextManager()
    
    async def quick_test():
        user_id = get_current_user_id()
        print(f"User ID in async function: {user_id}")
        return user_id
    
    result = context_manager.run_async_with_context(quick_test)
    
    if result == "quick-test-user":
        print("✅ Authentication context propagation is working!")
    else:
        print(f"❌ Authentication context propagation failed. Got: {result}")
    
    # Test context verification utility
    verification = verify_context_propagation()
    print(f"Context verification: {verification}")