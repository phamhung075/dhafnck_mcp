"""Tests for User Context Middleware

This module tests the UserContextMiddleware that extracts user context
from JWT tokens and makes it available for filtering MCP operations by user.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from contextvars import copy_context

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

from fastmcp.auth.mcp_integration.user_context_middleware import (
    UserContextMiddleware,
    current_user_context,
    get_current_user_context,
    get_current_user_id,
    require_user_context,
    has_scope,
    has_role,
    has_any_role,
    has_all_scopes
)
from fastmcp.auth.mcp_integration.jwt_auth_backend import MCPUserContext, JWTAccessToken


class TestUserContextMiddleware:
    """Test cases for UserContextMiddleware class."""
    
    @pytest.fixture
    def mock_jwt_backend(self):
        """Create a mock JWT backend."""
        backend = Mock()
        backend.load_access_token = AsyncMock()
        backend._get_user_context = AsyncMock()
        return backend
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def middleware(self, mock_jwt_backend):
        """Create middleware instance with mock backend."""
        app = FastAPI()
        return UserContextMiddleware(app, jwt_backend=mock_jwt_backend)
    
    def test_init_with_backend(self, mock_jwt_backend):
        """Test middleware initialization with provided backend."""
        app = FastAPI()
        middleware = UserContextMiddleware(app, jwt_backend=mock_jwt_backend)
        assert middleware.jwt_backend == mock_jwt_backend
    
    @patch('fastmcp.auth.mcp_integration.user_context_middleware.create_jwt_auth_backend')
    def test_init_without_backend(self, mock_create_backend):
        """Test middleware initialization creates default backend."""
        mock_backend = Mock()
        mock_create_backend.return_value = mock_backend
        
        app = FastAPI()
        middleware = UserContextMiddleware(app)
        
        mock_create_backend.assert_called_once()
        assert middleware.jwt_backend == mock_backend
    
    @pytest.mark.asyncio
    async def test_dispatch_no_auth_header(self, middleware):
        """Test dispatch with no Authorization header."""
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        
        call_next = AsyncMock(return_value=Mock(spec=Response))
        
        response = await middleware.dispatch(request, call_next)
        
        call_next.assert_called_once_with(request)
        middleware.jwt_backend.load_access_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_dispatch_invalid_auth_header(self, middleware):
        """Test dispatch with invalid Authorization header."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Invalid token"}
        request.state = Mock()
        request.method = "GET"
        request.url = "http://test.com/test"
        
        call_next = AsyncMock(return_value=Mock(spec=Response))
        
        response = await middleware.dispatch(request, call_next)
        
        call_next.assert_called_once_with(request)
        middleware.jwt_backend.load_access_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_dispatch_valid_token_no_access_token(self, middleware):
        """Test dispatch with valid token but no access token returned."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        request.state = Mock()
        request.method = "GET"
        request.url = "http://test.com/test"
        
        middleware.jwt_backend.load_access_token.return_value = None
        call_next = AsyncMock(return_value=Mock(spec=Response))
        
        response = await middleware.dispatch(request, call_next)
        
        call_next.assert_called_once_with(request)
        middleware.jwt_backend.load_access_token.assert_called_once_with("valid_token")
    
    @pytest.mark.asyncio
    async def test_dispatch_successful_authentication(self, middleware):
        """Test dispatch with successful authentication and user context."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        request.state = Mock()
        request.method = "GET"
        request.url = "http://test.com/test"
        
        # Mock access token
        access_token = Mock(spec=JWTAccessToken)
        access_token.client_id = "user123"
        access_token.scopes = ["read", "write"]
        middleware.jwt_backend.load_access_token.return_value = access_token
        
        # Mock user context
        user_context = Mock(spec=MCPUserContext)
        user_context.user_id = "user123"
        user_context.email = "test@example.com"
        user_context.roles = ["user"]
        middleware.jwt_backend._get_user_context.return_value = user_context
        
        call_next = AsyncMock(return_value=Mock(spec=Response))
        
        response = await middleware.dispatch(request, call_next)
        
        # Verify token was loaded and user context was retrieved
        middleware.jwt_backend.load_access_token.assert_called_once_with("valid_token")
        middleware.jwt_backend._get_user_context.assert_called_once_with("user123")
        
        # Verify request state was updated
        assert request.state.user_id == "user123"
        assert request.state.user_email == "test@example.com"
        assert request.state.user_roles == ["user"]
        assert request.state.user_scopes == ["read", "write"]
        
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_dispatch_no_user_context(self, middleware):
        """Test dispatch when user context cannot be retrieved."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        request.state = Mock()
        request.method = "GET"
        request.url = "http://test.com/test"
        
        # Mock access token
        access_token = Mock(spec=JWTAccessToken)
        access_token.client_id = "user123"
        middleware.jwt_backend.load_access_token.return_value = access_token
        
        # Mock no user context returned
        middleware.jwt_backend._get_user_context.return_value = None
        
        call_next = AsyncMock(return_value=Mock(spec=Response))
        
        response = await middleware.dispatch(request, call_next)
        
        middleware.jwt_backend.load_access_token.assert_called_once_with("valid_token")
        middleware.jwt_backend._get_user_context.assert_called_once_with("user123")
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_dispatch_exception_handling(self, middleware):
        """Test dispatch handles exceptions gracefully."""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        request.state = Mock()
        request.method = "GET"
        request.url = "http://test.com/test"
        
        # Mock exception in token loading
        middleware.jwt_backend.load_access_token.side_effect = Exception("Token error")
        
        call_next = AsyncMock(return_value=Mock(spec=Response))
        
        response = await middleware.dispatch(request, call_next)
        
        # Should continue without user context
        call_next.assert_called_once_with(request)


class TestContextFunctions:
    """Test cases for context utility functions."""
    
    def test_get_current_user_context_none(self):
        """Test get_current_user_context returns None when no context."""
        result = get_current_user_context()
        assert result is None
    
    def test_get_current_user_context_with_context(self):
        """Test get_current_user_context returns context when set."""
        user_context = Mock(spec=MCPUserContext)
        user_context.user_id = "user123"
        
        # Use context variable copy to isolate test
        ctx = copy_context()
        current_user_context.set(user_context)
        
        result = get_current_user_context()
        assert result == user_context
    
    def test_get_current_user_id_none(self):
        """Test get_current_user_id returns None when no context."""
        result = get_current_user_id()
        assert result is None
    
    def test_get_current_user_id_with_context(self):
        """Test get_current_user_id returns user ID when context set."""
        user_context = Mock(spec=MCPUserContext)
        user_context.user_id = "user123"
        
        current_user_context.set(user_context)
        
        result = get_current_user_id()
        assert result == "user123"
    
    def test_require_user_context_none_raises_error(self):
        """Test require_user_context raises error when no context."""
        with pytest.raises(RuntimeError, match="No user context available"):
            require_user_context()
    
    def test_require_user_context_with_context(self):
        """Test require_user_context returns context when available."""
        user_context = Mock(spec=MCPUserContext)
        user_context.user_id = "user123"
        
        current_user_context.set(user_context)
        
        result = require_user_context()
        assert result == user_context
    
    def test_has_scope_no_context(self):
        """Test has_scope returns False when no context."""
        result = has_scope("read")
        assert result is False
    
    def test_has_scope_with_context(self):
        """Test has_scope checks scopes correctly."""
        user_context = Mock(spec=MCPUserContext)
        user_context.scopes = ["read", "write"]
        
        current_user_context.set(user_context)
        
        assert has_scope("read") is True
        assert has_scope("admin") is False
    
    def test_has_role_no_context(self):
        """Test has_role returns False when no context."""
        result = has_role("admin")
        assert result is False
    
    def test_has_role_with_context(self):
        """Test has_role checks roles correctly."""
        user_context = Mock(spec=MCPUserContext)
        user_context.roles = ["user", "moderator"]
        
        current_user_context.set(user_context)
        
        assert has_role("user") is True
        assert has_role("admin") is False
    
    def test_has_any_role_no_context(self):
        """Test has_any_role returns False when no context."""
        result = has_any_role(["admin", "moderator"])
        assert result is False
    
    def test_has_any_role_with_context(self):
        """Test has_any_role checks multiple roles correctly."""
        user_context = Mock(spec=MCPUserContext)
        user_context.roles = ["user", "moderator"]
        
        current_user_context.set(user_context)
        
        assert has_any_role(["admin", "moderator"]) is True
        assert has_any_role(["admin", "superuser"]) is False
    
    def test_has_all_scopes_no_context(self):
        """Test has_all_scopes returns False when no context."""
        result = has_all_scopes(["read", "write"])
        assert result is False
    
    def test_has_all_scopes_with_context(self):
        """Test has_all_scopes checks multiple scopes correctly."""
        user_context = Mock(spec=MCPUserContext)
        user_context.scopes = ["read", "write", "admin"]
        
        current_user_context.set(user_context)
        
        assert has_all_scopes(["read", "write"]) is True
        assert has_all_scopes(["read", "super_admin"]) is False


class TestUserContextMiddlewareIntegration:
    """Integration tests for UserContextMiddleware."""
    
    @pytest.fixture
    def app_with_middleware(self, mock_jwt_backend):
        """Create app with middleware for integration testing."""
        app = FastAPI()
        app.add_middleware(UserContextMiddleware, jwt_backend=mock_jwt_backend)
        
        @app.get("/protected")
        async def protected_endpoint():
            user_context = get_current_user_context()
            if not user_context:
                return {"error": "No user context"}
            return {"user_id": user_context.user_id, "roles": user_context.roles}
        
        return app, mock_jwt_backend
    
    def test_integration_no_token(self, app_with_middleware):
        """Test integration without token."""
        app, _ = app_with_middleware
        client = TestClient(app)
        
        response = client.get("/protected")
        assert response.status_code == 200
        assert response.json() == {"error": "No user context"}
    
    def test_integration_with_valid_token(self, app_with_middleware):
        """Test integration with valid token."""
        app, mock_backend = app_with_middleware
        
        # Mock successful authentication
        access_token = Mock(spec=JWTAccessToken)
        access_token.client_id = "user123"
        access_token.scopes = ["read"]
        mock_backend.load_access_token.return_value = access_token
        
        user_context = Mock(spec=MCPUserContext)
        user_context.user_id = "user123"
        user_context.roles = ["user"]
        mock_backend._get_user_context.return_value = user_context
        
        client = TestClient(app)
        
        response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        assert response.status_code == 200
        assert response.json() == {"user_id": "user123", "roles": ["user"]}


if __name__ == "__main__":
    pytest.main([__file__])