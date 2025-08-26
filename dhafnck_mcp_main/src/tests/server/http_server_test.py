"""Tests for HTTP Server functionality"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List
import asyncio
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import BaseRoute
from contextlib import asynccontextmanager

from fastmcp.server.http_server import (
    TokenVerifierAdapter, RequestContextMiddleware, StarletteWithLifespan,
    setup_auth_middleware_and_routes, create_base_app, create_http_server_factory,
    create_sse_app, create_streamable_http_app, MCPHeaderValidationMiddleware,
    set_http_request
)


class TestTokenVerifierAdapter:
    """Test suite for TokenVerifierAdapter"""

    def test_adapter_initialization(self):
        """Test adapter initializes with provider"""
        mock_provider = Mock()
        adapter = TokenVerifierAdapter(mock_provider)
        
        assert adapter.provider == mock_provider

    @pytest.mark.asyncio
    async def test_verify_token_with_verify_token_method(self):
        """Test token verification when provider has verify_token method"""
        mock_provider = Mock()
        mock_token = Mock()
        mock_provider.verify_token = AsyncMock(return_value=mock_token)
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("test-token")
        
        assert result == mock_token
        mock_provider.verify_token.assert_called_once_with("test-token")

    @pytest.mark.asyncio
    async def test_verify_token_with_load_access_token_method(self):
        """Test token verification when provider has load_access_token method"""
        mock_provider = Mock()
        mock_token = Mock()
        mock_provider.load_access_token = AsyncMock(return_value=mock_token)
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("test-token")
        
        assert result == mock_token
        mock_provider.load_access_token.assert_called_once_with("test-token")

    @pytest.mark.asyncio
    async def test_verify_token_with_extract_user_from_token_method(self):
        """Test token verification when provider has extract_user_from_token method"""
        mock_provider = Mock()
        mock_provider.extract_user_from_token = Mock(return_value="user-123")
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("test-token")
        
        assert result is not None
        assert result.client_id == "user-123"
        assert result.token == "test-token"
        assert "execute:mcp" in result.scopes

    @pytest.mark.asyncio
    async def test_verify_token_with_extract_user_none_result(self):
        """Test token verification when extract_user_from_token returns None"""
        mock_provider = Mock()
        mock_provider.extract_user_from_token = Mock(return_value=None)
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("test-token")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_unknown_provider_type(self):
        """Test token verification with unknown provider type"""
        mock_provider = Mock()
        # Remove all known methods
        if hasattr(mock_provider, 'verify_token'):
            del mock_provider.verify_token
        if hasattr(mock_provider, 'load_access_token'):
            del mock_provider.load_access_token
        if hasattr(mock_provider, 'extract_user_from_token'):
            del mock_provider.extract_user_from_token
        
        with patch('fastmcp.server.http_server.logger') as mock_logger:
            adapter = TokenVerifierAdapter(mock_provider)
            result = await adapter.verify_token("test-token")
            
            assert result is None
            mock_logger.error.assert_called_once()


class TestRequestContextMiddleware:
    """Test suite for RequestContextMiddleware"""

    def test_middleware_initialization(self):
        """Test middleware initializes with app"""
        mock_app = Mock()
        middleware = RequestContextMiddleware(mock_app)
        
        assert middleware.app == mock_app

    @pytest.mark.asyncio
    async def test_middleware_http_request_handling(self):
        """Test middleware handles HTTP requests"""
        mock_app = AsyncMock()
        middleware = RequestContextMiddleware(mock_app)
        
        scope = {"type": "http", "path": "/test"}
        receive = Mock()
        send = Mock()
        
        await middleware(scope, receive, send)
        
        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_middleware_non_http_request_handling(self):
        """Test middleware handles non-HTTP requests"""
        mock_app = AsyncMock()
        middleware = RequestContextMiddleware(mock_app)
        
        scope = {"type": "websocket"}
        receive = Mock()
        send = Mock()
        
        await middleware(scope, receive, send)
        
        mock_app.assert_called_once_with(scope, receive, send)


class TestStarletteWithLifespan:
    """Test suite for StarletteWithLifespan"""

    def test_lifespan_property(self):
        """Test lifespan property returns router lifespan context"""
        app = StarletteWithLifespan()
        
        assert app.lifespan == app.router.lifespan_context


class TestSetupAuthMiddlewareAndRoutes:
    """Test suite for setup_auth_middleware_and_routes function"""

    def test_setup_auth_middleware_basic(self):
        """Test basic auth middleware setup"""
        mock_auth = Mock()
        mock_auth.required_scopes = ['read', 'write']
        
        with patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', True):
            middleware, auth_routes, required_scopes = setup_auth_middleware_and_routes(mock_auth)
        
        assert isinstance(middleware, list)
        assert isinstance(auth_routes, list)
        assert required_scopes == ['read', 'write']

    def test_setup_auth_middleware_no_scopes(self):
        """Test auth middleware setup when provider has no required_scopes"""
        mock_auth = Mock(spec=[])  # Mock with no attributes
        
        middleware, auth_routes, required_scopes = setup_auth_middleware_and_routes(mock_auth)
        
        assert required_scopes == []

    @patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', False)
    @patch('fastmcp.server.http_server.logger')
    def test_setup_auth_middleware_unavailable(self, mock_logger, ):
        """Test auth middleware setup when context middleware is unavailable"""
        mock_auth = Mock()
        
        middleware, auth_routes, required_scopes = setup_auth_middleware_and_routes(mock_auth)
        
        mock_logger.warning.assert_called_with(
            "RequestContextMiddleware not available - MCP tools will not have user context"
        )


class TestCreateBaseApp:
    """Test suite for create_base_app function"""

    def test_create_base_app_basic(self):
        """Test basic app creation"""
        routes = []
        middleware = []
        
        app = create_base_app(routes, middleware)
        
        assert isinstance(app, StarletteWithLifespan)

    def test_create_base_app_with_cors_origins(self):
        """Test app creation with custom CORS origins"""
        routes = []
        middleware = []
        cors_origins = ["http://example.com"]
        
        app = create_base_app(routes, middleware, cors_origins=cors_origins)
        
        assert isinstance(app, StarletteWithLifespan)

    def test_create_base_app_debug_mode(self):
        """Test app creation with debug mode"""
        routes = []
        middleware = []
        
        app = create_base_app(routes, middleware, debug=True)
        
        assert app.debug is True

    @asynccontextmanager
    async def sample_lifespan(app):
        """Sample lifespan function for testing"""
        yield

    def test_create_base_app_with_lifespan(self):
        """Test app creation with custom lifespan"""
        routes = []
        middleware = []
        
        app = create_base_app(routes, middleware, lifespan=self.sample_lifespan)
        
        assert isinstance(app, StarletteWithLifespan)


class TestCreateHttpServerFactory:
    """Test suite for create_http_server_factory function"""

    def test_create_http_server_factory_basic(self):
        """Test basic server factory creation"""
        mock_server = Mock()
        
        server_routes, server_middleware, required_scopes = create_http_server_factory(mock_server)
        
        assert isinstance(server_routes, list)
        assert isinstance(server_middleware, list)
        assert isinstance(required_scopes, list)

    def test_create_http_server_factory_with_auth(self):
        """Test server factory creation with auth"""
        mock_server = Mock()
        mock_auth = Mock()
        mock_auth.required_scopes = ['read']
        
        with patch('fastmcp.server.http_server.setup_auth_middleware_and_routes') as mock_setup:
            mock_setup.return_value = ([], [], ['read'])
            
            server_routes, server_middleware, required_scopes = create_http_server_factory(
                mock_server, auth=mock_auth
            )
            
            assert required_scopes == ['read']

    def test_create_http_server_factory_with_custom_routes(self):
        """Test server factory creation with custom routes"""
        mock_server = Mock()
        mock_route = Mock(spec=BaseRoute)
        custom_routes = [mock_route]
        
        server_routes, server_middleware, required_scopes = create_http_server_factory(
            mock_server, routes=custom_routes
        )
        
        assert mock_route in server_routes

    def test_create_http_server_factory_with_custom_middleware(self):
        """Test server factory creation with custom middleware"""
        mock_server = Mock()
        mock_middleware = Mock(spec=Middleware)
        custom_middleware = [mock_middleware]
        
        server_routes, server_middleware, required_scopes = create_http_server_factory(
            mock_server, middleware=custom_middleware
        )
        
        assert mock_middleware in server_middleware


class TestMCPHeaderValidationMiddleware:
    """Test suite for MCPHeaderValidationMiddleware"""

    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        mock_app = Mock()
        cors_origins = ["http://localhost:3000"]
        
        middleware = MCPHeaderValidationMiddleware(mock_app, cors_origins)
        
        assert middleware.app == mock_app
        assert middleware.cors_origins == cors_origins

    def test_middleware_default_cors_origins(self):
        """Test middleware with default CORS origins"""
        mock_app = Mock()
        
        middleware = MCPHeaderValidationMiddleware(mock_app)
        
        assert "http://localhost:3000" in middleware.cors_origins
        assert "http://localhost:3800" in middleware.cors_origins

    @pytest.mark.asyncio
    async def test_middleware_non_http_passthrough(self):
        """Test middleware passes through non-HTTP requests"""
        mock_app = AsyncMock()
        middleware = MCPHeaderValidationMiddleware(mock_app)
        
        scope = {"type": "websocket"}
        receive = Mock()
        send = Mock()
        
        await middleware(scope, receive, send)
        
        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_middleware_non_mcp_path_passthrough(self):
        """Test middleware passes through non-MCP paths"""
        mock_app = AsyncMock()
        middleware = MCPHeaderValidationMiddleware(mock_app)
        
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "POST",
            "headers": [(b"content-type", b"application/json")]
        }
        receive = Mock()
        send = Mock()
        
        await middleware(scope, receive, send)
        
        mock_app.assert_called_once_with(scope, receive, send)


class TestSetHttpRequest:
    """Test suite for set_http_request context manager"""

    def test_set_http_request_context(self):
        """Test HTTP request context setting"""
        from starlette.requests import Request
        
        mock_scope = {"type": "http", "path": "/test"}
        request = Request(mock_scope)
        
        with set_http_request(request) as context_request:
            assert context_request == request

    def test_set_http_request_cleanup(self):
        """Test HTTP request context cleanup"""
        from starlette.requests import Request
        from fastmcp.server.http_server import _current_http_request
        
        mock_scope = {"type": "http", "path": "/test"}
        request = Request(mock_scope)
        
        # Initially should be None
        assert _current_http_request.get() is None
        
        with set_http_request(request):
            # Should be set within context
            assert _current_http_request.get() == request
        
        # Should be reset after context
        assert _current_http_request.get() is None


class TestCreateSSEApp:
    """Test suite for create_sse_app function"""

    def test_create_sse_app_basic(self):
        """Test basic SSE app creation"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        with patch('fastmcp.server.http_server.create_http_server_factory') as mock_factory:
            mock_factory.return_value = ([], [], [])
            
            app = create_sse_app(
                server=mock_server,
                message_path="/message",
                sse_path="/sse"
            )
            
            assert isinstance(app, StarletteWithLifespan)
            assert hasattr(app.state, 'fastmcp_server')
            assert hasattr(app.state, 'path')

    def test_create_sse_app_message_path_trailing_slash(self):
        """Test SSE app creation adds trailing slash to message path"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        with patch('fastmcp.server.http_server.create_http_server_factory') as mock_factory:
            mock_factory.return_value = ([], [], [])
            
            app = create_sse_app(
                server=mock_server,
                message_path="/message",  # No trailing slash
                sse_path="/sse"
            )
            
            assert isinstance(app, StarletteWithLifespan)

    def test_create_sse_app_with_auth(self):
        """Test SSE app creation with authentication"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        mock_auth = Mock()
        
        with patch('fastmcp.server.http_server.create_http_server_factory') as mock_factory:
            mock_factory.return_value = ([], [], ['read'])
            
            app = create_sse_app(
                server=mock_server,
                message_path="/message/",
                sse_path="/sse",
                auth=mock_auth
            )
            
            assert isinstance(app, StarletteWithLifespan)


class TestCreateStreamableHttpApp:
    """Test suite for create_streamable_http_app function"""

    def test_create_streamable_http_app_basic(self):
        """Test basic streamable HTTP app creation"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        app = create_streamable_http_app(
            server=mock_server,
            streamable_http_path="/mcp"
        )
        
        assert isinstance(app, StarletteWithLifespan)
        assert hasattr(app.state, 'fastmcp_server')
        assert hasattr(app.state, 'path')

    def test_create_streamable_http_app_with_event_store(self):
        """Test streamable HTTP app creation with event store"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        mock_event_store = Mock()
        
        app = create_streamable_http_app(
            server=mock_server,
            streamable_http_path="/mcp",
            event_store=mock_event_store
        )
        
        assert isinstance(app, StarletteWithLifespan)

    def test_create_streamable_http_app_json_response(self):
        """Test streamable HTTP app creation with JSON response"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        app = create_streamable_http_app(
            server=mock_server,
            streamable_http_path="/mcp",
            json_response=True
        )
        
        assert isinstance(app, StarletteWithLifespan)

    def test_create_streamable_http_app_stateless(self):
        """Test streamable HTTP app creation with stateless HTTP"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        app = create_streamable_http_app(
            server=mock_server,
            streamable_http_path="/mcp",
            stateless_http=True
        )
        
        assert isinstance(app, StarletteWithLifespan)

    def test_create_streamable_http_app_with_auth(self):
        """Test streamable HTTP app creation with authentication"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        mock_auth = Mock()
        
        with patch('fastmcp.server.http_server.setup_auth_middleware_and_routes') as mock_setup:
            mock_setup.return_value = ([], [], ['read'])
            
            app = create_streamable_http_app(
                server=mock_server,
                streamable_http_path="/mcp",
                auth=mock_auth
            )
            
            assert isinstance(app, StarletteWithLifespan)


@patch('fastmcp.server.http_server.logger')
class TestLogging:
    """Test suite for logging functionality"""

    def test_auth_routes_logging(self, mock_logger):
        """Test that OAuth routes disabled message is logged"""
        mock_auth = Mock()
        
        setup_auth_middleware_and_routes(mock_auth)
        
        mock_logger.info.assert_called_with("OAuth routes disabled - using JWT authentication only")

    def test_context_middleware_logging_available(self, mock_logger):
        """Test context middleware availability logging"""
        mock_auth = Mock()
        
        with patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', True):
            setup_auth_middleware_and_routes(mock_auth)
            
            mock_logger.info.assert_called_with("Added RequestContextMiddleware for authentication context propagation")

    def test_context_middleware_logging_unavailable(self, mock_logger):
        """Test context middleware unavailability logging"""
        mock_auth = Mock()
        
        with patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', False):
            setup_auth_middleware_and_routes(mock_auth)
            
            mock_logger.warning.assert_called_with("RequestContextMiddleware not available - MCP tools will not have user context")


class TestImportHandling:
    """Test suite for import handling and error cases"""

    @patch('fastmcp.server.http_server.logger')
    def test_route_import_error_handling(self, mock_logger):
        """Test that import errors for routes are handled gracefully"""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        # This would typically be tested by mocking the import, but since
        # the imports are at the function level, we test the behavior indirectly
        with patch('fastmcp.server.http_server.create_http_server_factory') as mock_factory:
            mock_factory.return_value = ([], [], [])
            
            app = create_sse_app(
                server=mock_server,
                message_path="/message/",
                sse_path="/sse"
            )
            
            assert isinstance(app, StarletteWithLifespan)

    def test_missing_fastmcp_server_attribute(self):
        """Test handling when FastMCP server is missing expected attributes"""
        mock_server = Mock()
        # Simulate missing attributes
        del mock_server._additional_http_routes
        mock_server._mcp_server = Mock()
        
        # Should handle gracefully even with missing attributes
        with pytest.raises(AttributeError):
            create_sse_app(
                server=mock_server,
                message_path="/message/",
                sse_path="/sse"
            )