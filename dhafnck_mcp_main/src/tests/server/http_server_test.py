"""
Tests for HTTP server factory and creation utilities.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from fastmcp.server.http_server import (
    create_http_server_factory,
    create_sse_app,
    create_streamable_http_app,
    TokenVerifierAdapter,
    MCPHeaderValidationMiddleware,
    RequestContextMiddleware,
    setup_auth_middleware_and_routes,
    create_base_app,
)


class TestTokenVerifierAdapter:
    """Test the TokenVerifierAdapter class."""

    @pytest.mark.asyncio
    async def test_verify_token_with_verify_token_method(self):
        """Test adapter with provider that has verify_token method."""
        provider = Mock()
        provider.verify_token = AsyncMock(return_value=Mock(token="test_token"))
        
        adapter = TokenVerifierAdapter(provider)
        result = await adapter.verify_token("test_token")
        
        assert result.token == "test_token"
        provider.verify_token.assert_called_once_with("test_token")

    @pytest.mark.asyncio
    async def test_verify_token_with_load_access_token_method(self):
        """Test adapter with OAuth provider that has load_access_token method."""
        provider = Mock()
        provider.load_access_token = AsyncMock(return_value=Mock(token="oauth_token"))
        
        adapter = TokenVerifierAdapter(provider)
        result = await adapter.verify_token("oauth_token")
        
        assert result.token == "oauth_token"
        provider.load_access_token.assert_called_once_with("oauth_token")

    @pytest.mark.asyncio
    async def test_verify_token_with_jwt_middleware_provider(self):
        """Test adapter with JWT middleware provider."""
        provider = Mock()
        provider.extract_user_from_token = Mock(return_value="user123")
        
        adapter = TokenVerifierAdapter(provider)
        result = await adapter.verify_token("jwt_token")
        
        assert result.token == "jwt_token"
        assert result.client_id == "user123"
        assert result.scopes == ['execute:mcp']
        provider.extract_user_from_token.assert_called_once_with("jwt_token")

    @pytest.mark.asyncio
    async def test_verify_token_with_unknown_provider(self):
        """Test adapter with unknown provider type."""
        provider = Mock()  # No recognized methods
        
        adapter = TokenVerifierAdapter(provider)
        result = await adapter.verify_token("unknown_token")
        
        assert result is None


class TestSetupAuthMiddlewareAndRoutes:
    """Test the setup_auth_middleware_and_routes function."""

    def test_setup_with_oauth_provider(self):
        """Test setup with OAuth provider."""
        auth = Mock()
        auth.required_scopes = ['read', 'write']
        
        middleware, auth_routes, required_scopes = setup_auth_middleware_and_routes(auth)
        
        assert isinstance(middleware, list)
        assert isinstance(auth_routes, list)
        assert required_scopes == ['read', 'write']

    @patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', True)
    def test_setup_with_request_context_middleware(self):
        """Test setup includes RequestContextMiddleware when available."""
        auth = Mock()
        auth.required_scopes = []
        
        middleware, auth_routes, required_scopes = setup_auth_middleware_and_routes(auth)
        
        # Should have RequestContextMiddleware
        assert len(middleware) == 1
        assert middleware[0].cls == RequestContextMiddleware


class TestCreateBaseApp:
    """Test the create_base_app function."""

    def test_create_base_app_basic(self):
        """Test basic app creation."""
        routes = [Route("/test", endpoint=lambda r: None)]
        middleware = []
        
        app = create_base_app(routes, middleware)
        
        assert app.routes[0].path == "/test"
        # RequestContextMiddleware should be added automatically
        assert any(m.cls == RequestContextMiddleware for m in app.middleware_stack)

    def test_create_base_app_with_cors(self):
        """Test app creation with CORS middleware."""
        routes = []
        middleware = []
        cors_origins = ["http://example.com"]
        
        app = create_base_app(routes, middleware, cors_origins=cors_origins)
        
        # Should have CORS middleware
        assert any(m.cls == CORSMiddleware for m in app.middleware_stack)


class TestCreateHttpServerFactory:
    """Test the create_http_server_factory function."""

    def test_factory_without_auth(self):
        """Test factory without authentication."""
        server = Mock()
        
        routes, middleware, scopes = create_http_server_factory(server)
        
        assert isinstance(routes, list)
        assert isinstance(middleware, list)
        assert scopes == []

    def test_factory_with_auth(self):
        """Test factory with authentication provider."""
        server = Mock()
        auth = Mock()
        auth.required_scopes = ['execute']
        
        routes, middleware, scopes = create_http_server_factory(server, auth=auth)
        
        assert isinstance(routes, list)
        assert isinstance(middleware, list)
        assert scopes == ['execute']

    def test_factory_with_custom_routes_and_middleware(self):
        """Test factory with custom routes and middleware."""
        server = Mock()
        custom_routes = [Route("/custom", endpoint=lambda r: None)]
        custom_middleware = [Middleware(Mock)]
        
        routes, middleware, scopes = create_http_server_factory(
            server,
            routes=custom_routes,
            middleware=custom_middleware
        )
        
        assert custom_routes[0] in routes
        assert custom_middleware[0] in middleware


class TestCreateSSEApp:
    """Test the create_sse_app function."""

    def test_create_sse_app_basic(self):
        """Test basic SSE app creation."""
        server = Mock()
        server._additional_http_routes = []
        server._mcp_server = Mock()
        
        app = create_sse_app(server, "/messages", "/sse")
        
        assert hasattr(app.state, 'fastmcp_server')
        assert app.state.fastmcp_server == server
        assert app.state.path == "/sse"

    def test_create_sse_app_ensures_trailing_slash(self):
        """Test SSE app ensures trailing slash on message path."""
        server = Mock()
        server._additional_http_routes = []
        server._mcp_server = Mock()
        
        app = create_sse_app(server, "/messages", "/sse")
        
        # Check that message path has trailing slash in routes
        message_routes = [r for r in app.routes if isinstance(r, Mount)]
        assert any("/messages/" in str(r.path) for r in message_routes)


class TestCreateStreamableHttpApp:
    """Test the create_streamable_http_app function."""

    def test_create_streamable_http_app_basic(self):
        """Test basic streamable HTTP app creation."""
        server = Mock()
        server._additional_http_routes = []
        server._mcp_server = Mock()
        
        app = create_streamable_http_app(server, "/mcp")
        
        assert hasattr(app.state, 'fastmcp_server')
        assert app.state.fastmcp_server == server
        assert app.state.path == "/mcp"

    def test_streamable_app_has_validation_middleware(self):
        """Test streamable HTTP app includes header validation middleware."""
        server = Mock()
        server._additional_http_routes = []
        server._mcp_server = Mock()
        
        app = create_streamable_http_app(server, "/mcp")
        
        # Should have MCPHeaderValidationMiddleware
        assert any(m.cls == MCPHeaderValidationMiddleware for m in app.middleware_stack)


class TestMCPHeaderValidationMiddleware:
    """Test the MCPHeaderValidationMiddleware class."""

    @pytest.mark.asyncio
    async def test_validates_post_content_type(self):
        """Test middleware validates Content-Type for POST requests."""
        app = Mock()
        middleware = MCPHeaderValidationMiddleware(app)
        
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [(b"content-type", b"text/plain")]
        }
        
        send_called = False
        async def mock_send(message):
            nonlocal send_called
            if message["type"] == "http.response.start":
                assert message["status"] == 415
                send_called = True
        
        receive = AsyncMock()
        await middleware(scope, receive, mock_send)
        assert send_called

    @pytest.mark.asyncio
    async def test_validates_post_accept_header(self):
        """Test middleware validates Accept header for POST requests."""
        app = Mock()
        middleware = MCPHeaderValidationMiddleware(app)
        
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [
                (b"content-type", b"application/json"),
                (b"accept", b"application/json")  # Missing text/event-stream
            ]
        }
        
        send_called = False
        async def mock_send(message):
            nonlocal send_called
            if message["type"] == "http.response.start":
                assert message["status"] == 406
                send_called = True
        
        receive = AsyncMock()
        await middleware(scope, receive, mock_send)
        assert send_called

    @pytest.mark.asyncio
    async def test_allows_valid_post_request(self):
        """Test middleware allows valid POST requests."""
        app = AsyncMock()
        middleware = MCPHeaderValidationMiddleware(app)
        
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [
                (b"content-type", b"application/json"),
                (b"accept", b"application/json, text/event-stream")
            ]
        }
        
        receive = AsyncMock()
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_validates_get_accept_header(self):
        """Test middleware validates Accept header for GET requests."""
        app = Mock()
        middleware = MCPHeaderValidationMiddleware(app)
        
        scope = {
            "type": "http",
            "path": "/mcp/sse",
            "method": "GET",
            "headers": [(b"accept", b"text/html")]  # Wrong accept type
        }
        
        send_called = False
        async def mock_send(message):
            nonlocal send_called
            if message["type"] == "http.response.start":
                assert message["status"] == 406
                send_called = True
        
        receive = AsyncMock()
        await middleware(scope, receive, mock_send)
        assert send_called


class TestRequestContextMiddleware:
    """Test the RequestContextMiddleware class."""

    @pytest.mark.asyncio
    async def test_sets_request_context_for_http(self):
        """Test middleware sets request context for HTTP requests."""
        app = AsyncMock()
        middleware = RequestContextMiddleware(app)
        
        scope = {
            "type": "http",
            "path": "/test",
            "method": "GET",
            "headers": []
        }
        
        receive = AsyncMock()
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        app.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_non_http_requests(self):
        """Test middleware skips non-HTTP requests."""
        app = AsyncMock()
        middleware = RequestContextMiddleware(app)
        
        scope = {
            "type": "websocket",
            "path": "/ws"
        }
        
        receive = AsyncMock()
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        app.assert_called_once_with(scope, receive, send)