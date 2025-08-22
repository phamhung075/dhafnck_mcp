"""
Test cases for dual authentication middleware.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request

from fastmcp.auth.middleware.dual_auth_middleware import DualAuthMiddleware, create_dual_auth_middleware
from fastmcp.auth.token_validator import TokenValidationError, RateLimitError
from fastmcp.auth.supabase_client import TokenInfo


# Test app setup
async def test_endpoint(request: Request):
    """Test endpoint that returns auth info."""
    return JSONResponse({
        "user_id": getattr(request.state, 'user_id', None),
        "auth_type": getattr(request.state, 'auth_type', None),
        "path": str(request.url.path)
    })


async def mcp_endpoint(request: Request):
    """MCP endpoint that returns JSON-RPC response."""
    body = await request.json()
    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {
            "tools": ["tool1", "tool2"],
            "user_id": getattr(request.state, 'user_id', None)
        },
        "id": body.get("id", 1)
    })


def create_test_app():
    """Create test application with routes."""
    app = Starlette(
        routes=[
            Route("/api/v2/test", test_endpoint),
            Route("/mcp", mcp_endpoint, methods=["POST"]),
            Route("/health", lambda r: JSONResponse({"status": "ok"})),
            Route("/test", test_endpoint)
        ]
    )
    return app


class TestDualAuthMiddleware:
    """Test cases for DualAuthMiddleware class."""
    
    @pytest.fixture
    def mock_supabase_auth(self):
        """Create mock Supabase auth service."""
        auth = Mock()
        auth.verify_token = AsyncMock()
        return auth
    
    @pytest.fixture
    def mock_token_validator(self):
        """Create mock token validator."""
        validator = Mock()
        validator.validate_token = AsyncMock()
        return validator
    
    @pytest.fixture
    def mock_token_info(self):
        """Create mock token info."""
        return TokenInfo(
            user_id="test-user-123",
            email="test@example.com",
            token_type="mcp_token",
            expires_at=datetime.now().timestamp() + 3600,
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_supabase_user(self):
        """Create mock Supabase user."""
        user = Mock()
        user.id = "supabase-user-123"
        user.email = "user@example.com"
        return user
    
    @pytest.fixture
    def app_with_middleware(self, mock_supabase_auth, mock_token_validator):
        """Create app with mocked middleware."""
        with patch('fastmcp.auth.middleware.dual_auth_middleware.SupabaseAuthService', return_value=mock_supabase_auth):
            with patch('fastmcp.auth.middleware.dual_auth_middleware.TokenValidator', return_value=mock_token_validator):
                app = create_test_app()
                app.add_middleware(DualAuthMiddleware)
                return app, mock_supabase_auth, mock_token_validator
    
    def test_request_type_detection_mcp_path(self, app_with_middleware):
        """Test MCP request detection by path."""
        app, _, _ = app_with_middleware
        client = TestClient(app)
        
        # Create middleware instance for testing
        middleware = DualAuthMiddleware(app)
        
        # Mock request with MCP path
        request = Mock()
        request.url.path = "/mcp/tools/list"
        request.headers = {}
        
        assert middleware._detect_request_type(request) == 'mcp'
    
    def test_request_type_detection_mcp_header(self, app_with_middleware):
        """Test MCP request detection by protocol header."""
        app, _, _ = app_with_middleware
        middleware = DualAuthMiddleware(app)
        
        request = Mock()
        request.url.path = "/api/test"
        request.headers = {'mcp-protocol-version': '2025-06-18'}
        
        assert middleware._detect_request_type(request) == 'mcp'
    
    def test_request_type_detection_frontend_api(self, app_with_middleware):
        """Test frontend request detection by API path."""
        app, _, _ = app_with_middleware
        middleware = DualAuthMiddleware(app)
        
        request = Mock()
        request.url.path = "/api/v2/tasks"
        request.headers = {}
        
        assert middleware._detect_request_type(request) == 'frontend'
    
    def test_request_type_detection_browser_agent(self, app_with_middleware):
        """Test frontend request detection by user agent."""
        app, _, _ = app_with_middleware
        middleware = DualAuthMiddleware(app)
        
        request = Mock()
        request.url.path = "/dashboard"
        request.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
            'content-type': 'text/html'
        }
        
        assert middleware._detect_request_type(request) == 'frontend'
    
    def test_request_type_detection_json_rpc(self, app_with_middleware):
        """Test MCP request detection by JSON-RPC content."""
        app, _, _ = app_with_middleware
        middleware = DualAuthMiddleware(app)
        
        request = Mock()
        request.url.path = "/rpc"
        request.headers = {
            'content-type': 'application/json',
            'accept': 'application/json, application/jsonrpc'
        }
        
        assert middleware._detect_request_type(request) == 'mcp'
    
    def test_request_type_detection_unknown(self, app_with_middleware):
        """Test unknown request type detection."""
        app, _, _ = app_with_middleware
        middleware = DualAuthMiddleware(app)
        
        request = Mock()
        request.url.path = "/unknown"
        request.headers = {}
        
        assert middleware._detect_request_type(request) == 'unknown'
    
    def test_should_skip_auth(self, app_with_middleware):
        """Test auth skip logic for specific paths."""
        app, _, _ = app_with_middleware
        middleware = DualAuthMiddleware(app)
        
        # Paths that should skip auth
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/static/test.js"]
        for path in skip_paths:
            request = Mock()
            request.url.path = path
            assert middleware._should_skip_auth(request) is True
        
        # Paths that should not skip auth
        no_skip_paths = ["/api/v2/test", "/mcp", "/test"]
        for path in no_skip_paths:
            request = Mock()
            request.url.path = path
            assert middleware._should_skip_auth(request) is False
    
    @pytest.mark.asyncio
    async def test_frontend_auth_bearer_token(self, app_with_middleware, mock_supabase_user):
        """Test frontend authentication with Bearer token."""
        app, supabase_auth, _ = app_with_middleware
        
        # Mock successful auth
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = mock_supabase_user
        supabase_auth.verify_token.return_value = auth_result
        
        client = TestClient(app)
        response = client.get(
            "/api/v2/test",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "supabase-user-123"
        assert data["auth_type"] == "frontend"
        
        supabase_auth.verify_token.assert_called_once_with("test-token")
    
    @pytest.mark.asyncio
    async def test_frontend_auth_cookie(self, app_with_middleware, mock_supabase_user):
        """Test frontend authentication with cookie."""
        app, supabase_auth, _ = app_with_middleware
        
        # Mock successful auth
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = mock_supabase_user
        supabase_auth.verify_token.return_value = auth_result
        
        client = TestClient(app)
        response = client.get(
            "/api/v2/test",
            cookies={"access_token": "cookie-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "supabase-user-123"
        assert data["auth_type"] == "frontend"
        
        supabase_auth.verify_token.assert_called_once_with("cookie-token")
    
    @pytest.mark.asyncio
    async def test_frontend_auth_failure(self, app_with_middleware):
        """Test frontend authentication failure."""
        app, supabase_auth, _ = app_with_middleware
        
        # Mock failed auth
        auth_result = Mock()
        auth_result.success = False
        auth_result.user = None
        supabase_auth.verify_token.return_value = auth_result
        
        client = TestClient(app)
        response = client.get(
            "/api/v2/test",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        # Should still return 200 as auth is optional by default
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
    
    @pytest.mark.asyncio
    async def test_mcp_auth_bearer_token(self, app_with_middleware, mock_token_info):
        """Test MCP authentication with Bearer token."""
        app, _, token_validator = app_with_middleware
        
        token_validator.validate_token.return_value = mock_token_info
        
        client = TestClient(app)
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"Authorization": "Bearer mcp-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["user_id"] == "test-user-123"
        
        token_validator.validate_token.assert_called_once()
        args = token_validator.validate_token.call_args[0]
        assert args[0] == "mcp-token"
    
    @pytest.mark.asyncio
    async def test_mcp_auth_custom_header(self, app_with_middleware, mock_token_info):
        """Test MCP authentication with custom header."""
        app, _, token_validator = app_with_middleware
        
        token_validator.validate_token.return_value = mock_token_info
        
        client = TestClient(app)
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"X-MCP-Token": "mcp-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["user_id"] == "test-user-123"
    
    @pytest.mark.asyncio
    async def test_mcp_auth_query_param(self, app_with_middleware, mock_token_info):
        """Test MCP authentication with query parameter."""
        app, _, token_validator = app_with_middleware
        
        token_validator.validate_token.return_value = mock_token_info
        
        client = TestClient(app)
        response = client.post(
            "/mcp?token=query-token",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["user_id"] == "test-user-123"
        
        token_validator.validate_token.assert_called_once()
        args = token_validator.validate_token.call_args[0]
        assert args[0] == "query-token"
    
    @pytest.mark.asyncio
    async def test_mcp_auth_failure(self, app_with_middleware):
        """Test MCP authentication failure."""
        app, _, token_validator = app_with_middleware
        
        token_validator.validate_token.side_effect = TokenValidationError("Invalid token")
        
        client = TestClient(app)
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32001
        assert "Authentication failed" in data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_mcp_rate_limit_error(self, app_with_middleware):
        """Test MCP rate limit error handling."""
        app, _, token_validator = app_with_middleware
        
        token_validator.validate_token.side_effect = RateLimitError("Rate limit exceeded")
        
        client = TestClient(app)
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Rate limit exceeded" in data["error"]["data"]["detail"]
    
    @pytest.mark.asyncio
    async def test_unknown_request_type_fallback(self, app_with_middleware, mock_token_info):
        """Test unknown request type tries both auth methods."""
        app, supabase_auth, token_validator = app_with_middleware
        
        # Mock MCP auth success
        token_validator.validate_token.return_value = mock_token_info
        
        # Mock Supabase auth failure
        auth_result = Mock()
        auth_result.success = False
        supabase_auth.verify_token.return_value = auth_result
        
        client = TestClient(app)
        response = client.get(
            "/test",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-123"
        assert data["auth_type"] == "unknown"
        
        # Should have tried MCP auth
        token_validator.validate_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skip_auth_paths(self, app_with_middleware):
        """Test that certain paths skip authentication."""
        app, supabase_auth, token_validator = app_with_middleware
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        # No auth methods should be called
        supabase_auth.verify_token.assert_not_called()
        token_validator.validate_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_error_response_formats(self, app_with_middleware):
        """Test different error response formats for different request types."""
        app, supabase_auth, token_validator = app_with_middleware
        
        # Mock auth failures
        token_validator.validate_token.side_effect = TokenValidationError("Invalid MCP token")
        auth_result = Mock()
        auth_result.success = False
        supabase_auth.verify_token.return_value = auth_result
        
        client = TestClient(app)
        
        # Test MCP error format
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "test", "id": 1},
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "jsonrpc" in data
        assert data["error"]["code"] == -32001
        
        # Test frontend error format
        token_validator.validate_token.side_effect = TokenValidationError("Invalid token")
        response = client.get(
            "/api/v2/test",
            headers={"Authorization": "Bearer invalid"}
        )
        # Should return 200 as auth failure is handled gracefully
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_user_data_variations(self, app_with_middleware):
        """Test handling of different user data formats."""
        app, supabase_auth, _ = app_with_middleware
        
        # Test with dict user data
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = {"id": "dict-user-123", "email": "dict@example.com"}
        supabase_auth.verify_token.return_value = auth_result
        
        client = TestClient(app)
        response = client.get(
            "/api/v2/test",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "dict-user-123"
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, app_with_middleware):
        """Test handling of unexpected exceptions."""
        app, _, token_validator = app_with_middleware
        
        # Mock unexpected exception
        token_validator.validate_token.side_effect = Exception("Unexpected error")
        
        client = TestClient(app)
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "test", "id": 1},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication system error" in str(data)
    
    def test_create_dual_auth_middleware_factory(self):
        """Test the factory function."""
        middleware_class = create_dual_auth_middleware()
        assert middleware_class == DualAuthMiddleware


class TestLogging:
    """Test cases for logging behavior."""
    
    @pytest.mark.asyncio
    async def test_initialization_logging(self):
        """Test that initialization is logged."""
        with patch('fastmcp.auth.middleware.dual_auth_middleware.SupabaseAuthService'):
            with patch('fastmcp.auth.middleware.dual_auth_middleware.TokenValidator'):
                with patch('fastmcp.auth.middleware.dual_auth_middleware.logger') as mock_logger:
                    app = create_test_app()
                    DualAuthMiddleware(app)
                    
                    mock_logger.info.assert_called_with("Dual authentication middleware initialized")
    
    @pytest.mark.asyncio
    async def test_request_logging(self, app_with_middleware):
        """Test request processing logging."""
        app, _, _ = app_with_middleware
        
        with patch('fastmcp.auth.middleware.dual_auth_middleware.logger') as mock_logger:
            client = TestClient(app)
            client.get("/api/v2/test")
            
            # Check debug logs
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("Request type detected: frontend" in call for call in debug_calls)
            assert any("Path: /api/v2/test" in call for call in debug_calls)
    
    @pytest.mark.asyncio
    async def test_auth_success_logging(self, app_with_middleware, mock_token_info):
        """Test successful authentication logging."""
        app, _, token_validator = app_with_middleware
        token_validator.validate_token.return_value = mock_token_info
        
        with patch('fastmcp.auth.middleware.dual_auth_middleware.logger') as mock_logger:
            client = TestClient(app)
            client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "test", "id": 1},
                headers={"Authorization": "Bearer test-token"}
            )
            
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("Authenticated user test-user-123 via mcp" in call for call in debug_calls)
    
    @pytest.mark.asyncio
    async def test_auth_failure_logging(self, app_with_middleware):
        """Test authentication failure logging."""
        app, _, token_validator = app_with_middleware
        token_validator.validate_token.side_effect = TokenValidationError("Test error")
        
        with patch('fastmcp.auth.middleware.dual_auth_middleware.logger') as mock_logger:
            client = TestClient(app)
            client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "test", "id": 1},
                headers={"Authorization": "Bearer invalid"}
            )
            
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any("Authentication failed for mcp: Test error" in call for call in warning_calls)