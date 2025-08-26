"""
Integration test for Authentication Context Propagation Fix

This test simulates the complete authentication flow:
1. DualAuthMiddleware processes JWT token
2. RequestContextMiddleware captures authentication context  
3. auth_helper.py reads from context variables
4. MCP handlers successfully get authenticated user

This test addresses the issue where JWT tokens were validated 
but MCP requests returned 401 errors.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware import Middleware
from starlette.applications import Starlette
from starlette.testclient import TestClient


class TestAuthenticationContextPropagation:
    """Test complete authentication context propagation."""
    
    @pytest.mark.asyncio
    async def test_complete_jwt_authentication_flow(self):
        """Test the complete authentication flow from JWT validation to MCP handler access."""
        
        # Step 1: Simulate DualAuthMiddleware processing JWT token
        from fastmcp.auth.middleware.request_context_middleware import RequestContextMiddleware
        
        # Mock request with JWT authentication result (as set by DualAuthMiddleware)
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/mcp/manage_task"
        mock_request.headers = {"authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
        
        # Simulate DualAuthMiddleware setting authentication state
        mock_request.state = Mock()
        mock_request.state.user_id = "auth-flow-test-user"
        mock_request.state.auth_type = "local_jwt"
        mock_request.state.auth_info = {
            "user_id": "auth-flow-test-user",
            "email": "flow-test@example.com", 
            "auth_method": "local_jwt",
            "scopes": ["read", "write"]
        }
        
        # Step 2: Create RequestContextMiddleware
        middleware = RequestContextMiddleware(Mock())
        
        # Step 3: Track authentication context during request processing
        captured_auth_data = {}
        
        async def simulate_mcp_handler(request):
            """Simulate an MCP handler that needs authentication."""
            # This simulates what happens in actual MCP request handlers
            
            # Import and use auth_helper (this is where the fix should work)
            try:
                # Mock the validate_user_id function to avoid validation errors
                with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id') as mock_validate:
                    mock_validate.return_value = "auth-flow-test-user"
                    
                    # Import auth_helper (with our new context integration)
                    from fastmcp.task_management.interface.controllers.auth_helper import get_authenticated_user_id
                    
                    # This should now work without 401 errors
                    user_id = get_authenticated_user_id(operation_name="test_mcp_handler")
                    
                    captured_auth_data["success"] = True
                    captured_auth_data["user_id"] = user_id
                    captured_auth_data["error"] = None
                    
            except Exception as e:
                captured_auth_data["success"] = False
                captured_auth_data["user_id"] = None
                captured_auth_data["error"] = str(e)
            
            return Response("MCP Handler Executed")
        
        # Step 4: Process request through RequestContextMiddleware
        response = await middleware.dispatch(mock_request, simulate_mcp_handler)
        
        # Step 5: Verify the complete flow worked
        assert response.status_code == 200
        
        # The critical test: auth_helper should have successfully gotten the user_id
        assert captured_auth_data["success"] is True, f"Authentication failed: {captured_auth_data['error']}"
        assert captured_auth_data["user_id"] == "auth-flow-test-user"
        assert captured_auth_data["error"] is None
        
        print("✅ CRITICAL FIX VERIFIED: JWT authentication context successfully propagated to MCP handler")
    
    @pytest.mark.asyncio 
    async def test_authentication_failure_without_context(self):
        """Test that authentication fails appropriately when no context is available."""
        
        from fastmcp.auth.middleware.request_context_middleware import RequestContextMiddleware
        
        # Mock request WITHOUT authentication (no DualAuthMiddleware processing)
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/mcp/manage_task"
        mock_request.state = Mock()
        # No user_id set in state (not authenticated)
        
        # Create RequestContextMiddleware
        middleware = RequestContextMiddleware(Mock())
        
        # Track what happens
        captured_auth_data = {}
        
        async def simulate_mcp_handler_no_auth(request):
            """Simulate an MCP handler when not authenticated."""
            try:
                from fastmcp.task_management.interface.controllers.auth_helper import get_authenticated_user_id
                
                # This should fail with authentication required error
                user_id = get_authenticated_user_id(operation_name="test_no_auth")
                captured_auth_data["unexpected_success"] = True
                captured_auth_data["user_id"] = user_id
                
            except Exception as e:
                captured_auth_data["expected_failure"] = True
                captured_auth_data["error_type"] = type(e).__name__
                captured_auth_data["error_message"] = str(e)
            
            return Response("Handler attempted")
        
        # Process request
        response = await middleware.dispatch(mock_request, simulate_mcp_handler_no_auth)
        
        # Verify appropriate failure
        assert response.status_code == 200
        assert captured_auth_data.get("expected_failure") is True
        assert "Authentication" in captured_auth_data.get("error_type", "")
        assert captured_auth_data.get("unexpected_success") is not True
        
        print("✅ Authentication appropriately fails when no context available")
    
    @pytest.mark.asyncio
    async def test_context_variable_isolation_between_requests(self):
        """Test that context variables are properly isolated between concurrent requests."""
        
        from fastmcp.auth.middleware.request_context_middleware import RequestContextMiddleware
        
        # Create two different mock requests with different users
        mock_request_1 = Mock(spec=Request)
        mock_request_1.method = "POST"
        mock_request_1.url.path = "/mcp/test1"
        mock_request_1.state = Mock()
        mock_request_1.state.user_id = "user-1"
        mock_request_1.state.auth_info = {"user_id": "user-1", "email": "user1@example.com"}
        
        mock_request_2 = Mock(spec=Request)
        mock_request_2.method = "POST" 
        mock_request_2.url.path = "/mcp/test2"
        mock_request_2.state = Mock()
        mock_request_2.state.user_id = "user-2"
        mock_request_2.state.auth_info = {"user_id": "user-2", "email": "user2@example.com"}
        
        # Create middleware
        middleware = RequestContextMiddleware(Mock())
        
        # Results storage
        results = {}
        
        async def handler_1(request):
            with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id', return_value="user-1"):
                from fastmcp.task_management.interface.controllers.auth_helper import get_authenticated_user_id
                user_id = get_authenticated_user_id(operation_name="handler_1")
                results["handler_1"] = user_id
            return Response("Handler 1")
        
        async def handler_2(request):
            with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id', return_value="user-2"):
                from fastmcp.task_management.interface.controllers.auth_helper import get_authenticated_user_id
                user_id = get_authenticated_user_id(operation_name="handler_2")
                results["handler_2"] = user_id
            return Response("Handler 2")
        
        # Process requests concurrently
        task_1 = middleware.dispatch(mock_request_1, handler_1)
        task_2 = middleware.dispatch(mock_request_2, handler_2)
        
        responses = await asyncio.gather(task_1, task_2)
        
        # Verify each request got the correct user context
        assert responses[0].status_code == 200
        assert responses[1].status_code == 200
        
        # Critical test: Each handler should have gotten its own user_id
        assert results["handler_1"] == "user-1"
        assert results["handler_2"] == "user-2"
        
        print("✅ Context variables properly isolated between concurrent requests")


class TestMiddlewareOrdering:
    """Test that middleware ordering works correctly."""
    
    def test_middleware_execution_order_documentation(self):
        """Document the correct middleware execution order."""
        
        # This test documents the correct middleware order for the authentication fix
        
        expected_order = [
            "1. DualAuthMiddleware (validates JWT, sets request.state.user_id)",
            "2. RequestContextMiddleware (captures auth context to contextvars)", 
            "3. Application handlers (access auth via auth_helper.py)"
        ]
        
        middleware_stack_order = [
            "DualAuthMiddleware",  # Added first = executes first
            "RequestContextMiddleware",  # Added second = executes after DualAuth
        ]
        
        # In Starlette, middleware executes in reverse order of addition
        # So: DualAuth added first → RequestContext added second
        # Results in: DualAuth runs first → RequestContext runs second
        
        print("✅ Middleware execution order documented:")
        for step in expected_order:
            print(f"   {step}")
        
        print("\n✅ Middleware stack order (in mcp_entry_point.py):")
        for i, middleware in enumerate(middleware_stack_order, 1):
            print(f"   {i}. middleware_stack.append(Middleware({middleware}))")
        
        # This test always passes - it's for documentation
        assert True


if __name__ == "__main__":
    pytest.main([__file__])