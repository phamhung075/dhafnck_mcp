import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from starlette.testclient import TestClient
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
import json

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastmcp.server.http_server import (
    create_sse_app,
    create_streamable_http_app,
    create_base_app,
    setup_auth_middleware_and_routes,
    create_http_server_factory,
    RequestContextMiddleware,
    MCPHeaderValidationMiddleware,
    StarletteWithLifespan,
    set_http_request,
    _current_http_request,
)


class TestRequestContextMiddleware:
    """Test the RequestContextMiddleware functionality."""

    @pytest.fixture
    def middleware(self):
        """Create a RequestContextMiddleware instance."""
        app = Mock()
        return RequestContextMiddleware(app)

    @pytest.mark.asyncio
    async def test_http_request_context_set(self, middleware):
        """Test that HTTP requests are properly stored in context."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
        }
        receive = Mock()
        send = Mock()
        
        # Mock the app to check context
        context_request = None
        async def mock_app(scope, receive, send):
            nonlocal context_request
            context_request = _current_http_request.get()
        
        middleware.app = mock_app
        
        await middleware(scope, receive, send)
        
        # Verify request was set in context
        assert context_request is not None
        assert context_request.scope == scope

    @pytest.mark.asyncio
    async def test_non_http_request_passthrough(self, middleware):
        """Test that non-HTTP requests pass through without context."""
        scope = {
            "type": "websocket",
            "path": "/ws",
        }
        receive = Mock()
        send = Mock()
        
        # Track if app was called
        app_called = False
        async def mock_app(scope, receive, send):
            nonlocal app_called
            app_called = True
            # Context should not be set for non-HTTP
            assert _current_http_request.get() is None
        
        middleware.app = mock_app
        
        await middleware(scope, receive, send)
        
        assert app_called

    def test_set_http_request_context_manager(self):
        """Test the set_http_request context manager."""
        # Create a mock request
        mock_request = Mock(spec=Request)
        
        # Verify initial state
        assert _current_http_request.get() is None
        
        # Use context manager
        with set_http_request(mock_request) as request:
            assert request == mock_request
            assert _current_http_request.get() == mock_request
        
        # Verify context is reset after exit
        assert _current_http_request.get() is None


class TestMCPHeaderValidationMiddleware:
    """Test the MCPHeaderValidationMiddleware functionality."""

    @pytest.fixture
    def middleware(self):
        """Create an MCPHeaderValidationMiddleware instance."""
        app = Mock()
        return MCPHeaderValidationMiddleware(app, cors_origins=["http://localhost:3000"])

    @pytest.mark.asyncio
    async def test_non_http_passthrough(self, middleware):
        """Test that non-HTTP requests pass through."""
        scope = {"type": "websocket"}
        receive = Mock()
        send = Mock()
        
        middleware.app = AsyncMock()
        
        await middleware(scope, receive, send)
        
        middleware.app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_non_mcp_path_passthrough(self, middleware):
        """Test that non-MCP paths pass through without validation."""
        scope = {
            "type": "http",
            "path": "/api/test",
            "method": "POST",
            "headers": [],
        }
        receive = Mock()
        send = Mock()
        
        middleware.app = AsyncMock()
        
        await middleware(scope, receive, send)
        
        middleware.app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_mcp_post_missing_content_type(self, middleware):
        """Test MCP POST request with missing Content-Type header."""
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [(b"accept", b"application/json, text/event-stream")],
        }
        receive = Mock()
        
        # Capture the response
        response_started = False
        response_body = b""
        
        async def mock_send(message):
            nonlocal response_started, response_body
            if message["type"] == "http.response.start":
                response_started = True
                assert message["status"] == 415
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
        
        await middleware(scope, receive, mock_send)
        
        assert response_started
        assert b"Content-Type must be application/json" in response_body

    @pytest.mark.asyncio
    async def test_mcp_post_invalid_accept(self, middleware):
        """Test MCP POST request with invalid Accept header."""
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [
                (b"content-type", b"application/json"),
                (b"accept", b"text/html"),
            ],
        }
        receive = Mock()
        
        # Capture the response
        response_status = None
        response_body = b""
        
        async def mock_send(message):
            nonlocal response_status, response_body
            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
        
        await middleware(scope, receive, mock_send)
        
        assert response_status == 406
        assert b"Accept header must include both application/json and text/event-stream" in response_body

    @pytest.mark.asyncio
    async def test_mcp_initialize_valid_headers(self, middleware):
        """Test /mcp/initialize with valid headers."""
        scope = {
            "type": "http",
            "path": "/mcp/initialize",
            "method": "POST",
            "headers": [
                (b"content-type", b"application/json"),
                (b"accept", b"application/json, text/event-stream"),
            ],
        }
        receive = Mock()
        send = Mock()
        
        middleware.app = AsyncMock()
        
        await middleware(scope, receive, send)
        
        # Should pass through to app
        middleware.app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_mcp_get_missing_accept(self, middleware):
        """Test MCP GET request without text/event-stream Accept."""
        scope = {
            "type": "http",
            "path": "/mcp/stream",
            "method": "GET",
            "headers": [(b"accept", b"text/html")],
        }
        receive = Mock()
        
        response_status = None
        
        async def mock_send(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
        
        await middleware(scope, receive, mock_send)
        
        assert response_status == 406

    @pytest.mark.asyncio
    async def test_cors_headers_in_error_response(self, middleware):
        """Test that CORS headers are included in error responses."""
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [
                (b"origin", b"http://localhost:3000"),
                (b"content-type", b"text/plain"),
            ],
        }
        receive = Mock()
        
        response_headers = {}
        
        async def mock_send(message):
            if message["type"] == "http.response.start":
                for name, value in message.get("headers", []):
                    response_headers[name.decode()] = value.decode()
        
        await middleware(scope, receive, mock_send)
        
        # Check CORS headers
        assert response_headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert response_headers.get("access-control-allow-credentials") == "true"
        assert response_headers.get("access-control-allow-methods") == "*"
        assert response_headers.get("access-control-allow-headers") == "*"


class TestSetupAuthMiddleware:
    """Test the setup_auth_middleware_and_routes function."""

    def test_setup_with_oauth_provider(self):
        """Test setup with an OAuth provider."""
        # Mock OAuth provider
        mock_auth = Mock()
        mock_auth.required_scopes = ["read", "write"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        with patch('fastmcp.server.http_server.create_auth_routes') as mock_create_routes:
            mock_create_routes.return_value = [
                Route("/auth/token", endpoint=lambda r: Response()),
                Route("/auth/revoke", endpoint=lambda r: Response()),
            ]
            
            middleware, routes, scopes = setup_auth_middleware_and_routes(mock_auth)
        
        # Verify middleware was created
        assert len(middleware) == 2
        assert any(m.cls.__name__ == "AuthenticationMiddleware" for m in middleware)
        assert any(m.cls.__name__ == "AuthContextMiddleware" for m in middleware)
        
        # Verify routes were created
        assert len(routes) == 2
        assert routes[0].path == "/auth/token"
        assert routes[1].path == "/auth/revoke"
        
        # Verify scopes
        assert scopes == ["read", "write"]


class TestCreateBaseApp:
    """Test the create_base_app function."""

    def test_create_app_with_defaults(self):
        """Test creating app with default settings."""
        routes = [Route("/test", endpoint=lambda r: Response())]
        middleware = []
        
        app = create_base_app(routes, middleware)
        
        assert isinstance(app, StarletteWithLifespan)
        assert len(app.routes) == 1
        # Check that default middleware was added
        assert len(app.middleware) >= 2  # RequestContext + CORS at minimum

    def test_create_app_with_custom_cors(self):
        """Test creating app with custom CORS origins."""
        routes = []
        middleware = []
        cors_origins = ["https://example.com", "https://app.example.com"]
        
        app = create_base_app(routes, middleware, cors_origins=cors_origins)
        
        # Find CORS middleware
        cors_middleware = None
        for m in app.middleware:
            if hasattr(m, 'cls') and m.cls.__name__ == 'CORSMiddleware':
                cors_middleware = m
                break
        
        assert cors_middleware is not None
        assert cors_middleware.kwargs['allow_origins'] == cors_origins

    def test_create_app_with_debug(self):
        """Test creating app with debug mode."""
        routes = []
        middleware = []
        
        app = create_base_app(routes, middleware, debug=True)
        
        assert app.debug is True


class TestCreateHTTPServerFactory:
    """Test the create_http_server_factory function."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock FastMCP server."""
        server = Mock()
        server._additional_http_routes = []
        return server

    def test_factory_without_auth(self, mock_server):
        """Test factory without authentication."""
        routes, middleware, scopes = create_http_server_factory(
            server=mock_server,
            auth=None,
            routes=[Route("/custom", endpoint=lambda r: Response())],
            middleware=[Middleware(RequestContextMiddleware)],
        )
        
        assert len(routes) == 1
        assert routes[0].path == "/custom"
        assert len(middleware) == 1
        assert len(scopes) == 0

    def test_factory_with_auth(self, mock_server):
        """Test factory with authentication."""
        mock_auth = Mock()
        mock_auth.required_scopes = ["admin"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        with patch('fastmcp.server.http_server.setup_auth_middleware_and_routes') as mock_setup:
            mock_setup.return_value = (
                [Middleware(RequestContextMiddleware)],
                [Route("/auth", endpoint=lambda r: Response())],
                ["admin"]
            )
            
            routes, middleware, scopes = create_http_server_factory(
                server=mock_server,
                auth=mock_auth,
            )
        
        assert len(routes) == 1
        assert routes[0].path == "/auth"
        assert len(middleware) == 1
        assert scopes == ["admin"]


class TestCreateSSEApp:
    """Test the create_sse_app function."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock FastMCP server."""
        server = Mock()
        server._additional_http_routes = []
        server._mcp_server = Mock()
        server._mcp_server.create_initialization_options = Mock(return_value={})
        server._mcp_server.run = AsyncMock()
        return server

    @patch('fastmcp.server.http_server.SseServerTransport')
    def test_create_sse_app_without_auth(self, mock_sse_transport, mock_server):
        """Test creating SSE app without authentication."""
        mock_sse = Mock()
        mock_sse.connect_sse = AsyncMock()
        mock_sse.handle_post_message = Mock()
        mock_sse_transport.return_value = mock_sse
        
        app = create_sse_app(
            server=mock_server,
            message_path="/messages",
            sse_path="/sse",
        )
        
        assert isinstance(app, StarletteWithLifespan)
        assert app.state.fastmcp_server == mock_server
        assert app.state.path == "/sse"
        
        # Check routes were added
        sse_route_found = False
        message_mount_found = False
        for route in app.routes:
            if hasattr(route, 'path'):
                if route.path == "/sse":
                    sse_route_found = True
                elif route.path == "/messages/":
                    message_mount_found = True
        
        assert sse_route_found
        assert message_mount_found

    @patch('fastmcp.server.http_server.SseServerTransport')
    def test_create_sse_app_with_auth(self, mock_sse_transport, mock_server):
        """Test creating SSE app with authentication."""
        mock_auth = Mock()
        mock_auth.required_scopes = ["stream"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        mock_sse = Mock()
        mock_sse_transport.return_value = mock_sse
        
        with patch('fastmcp.server.http_server.setup_auth_middleware_and_routes') as mock_setup:
            mock_setup.return_value = (
                [Middleware(RequestContextMiddleware)],
                [Route("/auth", endpoint=lambda r: Response())],
                ["stream"]
            )
            
            app = create_sse_app(
                server=mock_server,
                message_path="/messages",
                sse_path="/sse",
                auth=mock_auth,
            )
        
        # With auth, endpoints should be wrapped with RequireAuthMiddleware
        sse_route_found = False
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/sse":
                sse_route_found = True
                # The endpoint should be wrapped
                assert hasattr(route.endpoint, '__name__')
        
        assert sse_route_found


class TestCreateStreamableHTTPApp:
    """Test the create_streamable_http_app function."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock FastMCP server."""
        server = Mock()
        server._additional_http_routes = []
        server._mcp_server = Mock()
        return server

    @patch('fastmcp.server.http_server.StreamableHTTPSessionManager')
    def test_create_streamable_app_without_auth(self, mock_session_manager_class, mock_server):
        """Test creating streamable HTTP app without authentication."""
        mock_session_manager = Mock()
        mock_session_manager.handle_request = AsyncMock()
        mock_session_manager.run = AsyncMock()
        mock_session_manager_class.return_value = mock_session_manager
        
        app = create_streamable_http_app(
            server=mock_server,
            streamable_http_path="/mcp",
        )
        
        assert isinstance(app, StarletteWithLifespan)
        assert app.state.fastmcp_server == mock_server
        assert app.state.path == "/mcp"
        
        # Check that streamable route was added
        mcp_route_found = False
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/mcp":
                mcp_route_found = True
                assert "POST" in route.methods
        
        assert mcp_route_found

    @patch('fastmcp.server.http_server.StreamableHTTPSessionManager')
    def test_create_streamable_app_with_auth(self, mock_session_manager_class, mock_server):
        """Test creating streamable HTTP app with authentication."""
        mock_auth = Mock()
        mock_auth.required_scopes = ["execute"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        
        with patch('fastmcp.server.http_server.setup_auth_middleware_and_routes') as mock_setup:
            mock_setup.return_value = (
                [Middleware(RequestContextMiddleware)],
                [Route("/auth", endpoint=lambda r: Response())],
                ["execute"]
            )
            
            app = create_streamable_http_app(
                server=mock_server,
                streamable_http_path="/mcp",
                auth=mock_auth,
            )
        
        # Check auth routes were added
        auth_route_found = False
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/auth":
                auth_route_found = True
        
        assert auth_route_found

    @patch('fastmcp.server.http_server.StreamableHTTPSessionManager')
    def test_create_streamable_app_with_event_store(self, mock_session_manager_class, mock_server):
        """Test creating streamable HTTP app with event store."""
        mock_event_store = Mock()
        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager
        
        app = create_streamable_http_app(
            server=mock_server,
            streamable_http_path="/mcp",
            event_store=mock_event_store,
            json_response=True,
            stateless_http=True,
        )
        
        # Verify session manager was created with correct params
        mock_session_manager_class.assert_called_once_with(
            mock_server._mcp_server,
            event_store=mock_event_store,
            json_response=True,
            stateless=True,
        )


class TestStarletteWithLifespan:
    """Test the StarletteWithLifespan class."""

    def test_lifespan_property(self):
        """Test that lifespan property returns router's lifespan_context."""
        app = StarletteWithLifespan()
        
        # Mock router with lifespan_context
        mock_router = Mock()
        mock_lifespan = Mock()
        mock_router.lifespan_context = mock_lifespan
        app.router = mock_router
        
        assert app.lifespan == mock_lifespan


class TestIntegrationScenarios:
    """Test integration scenarios with actual client requests."""

    def test_sse_app_health_check(self):
        """Test SSE app responds to basic requests."""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        # Add a health check route
        health_route = Route("/health", endpoint=lambda r: Response(content="OK"))
        
        with patch('fastmcp.server.http_server.SseServerTransport'):
            app = create_sse_app(
                server=mock_server,
                message_path="/messages",
                sse_path="/sse",
                routes=[health_route],
            )
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.text == "OK"

    def test_streamable_app_cors_headers(self):
        """Test streamable HTTP app includes CORS headers."""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        mock_server._mcp_server = Mock()
        
        # Add a test route
        test_route = Route("/test", endpoint=lambda r: Response(content="test"), methods=["GET"])
        
        with patch('fastmcp.server.http_server.StreamableHTTPSessionManager'):
            app = create_streamable_http_app(
                server=mock_server,
                streamable_http_path="/mcp",
                routes=[test_route],
                cors_origins=["https://example.com"],
            )
        
        client = TestClient(app)
        response = client.get(
            "/test",
            headers={"Origin": "https://example.com"}
        )
        
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://example.com"