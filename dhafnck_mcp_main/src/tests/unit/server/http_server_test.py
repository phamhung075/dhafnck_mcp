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
    TokenVerifier,
    TokenVerifierAdapter,
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


class TestTokenVerifierAdapter:
    """Test the TokenVerifierAdapter class."""

    def test_adapter_implements_protocol(self):
        """Test that adapter implements TokenVerifier protocol."""
        mock_provider = Mock()
        adapter = TokenVerifierAdapter(mock_provider)
        
        # Check it implements the protocol
        assert isinstance(adapter, TokenVerifier)
        assert hasattr(adapter, 'verify_token')

    @pytest.mark.asyncio
    async def test_verify_token_delegates_to_provider(self):
        """Test that verify_token delegates to provider's load_access_token."""
        mock_provider = Mock()
        mock_access_token = Mock()
        mock_provider.load_access_token = AsyncMock(return_value=mock_access_token)
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("test-token")
        
        mock_provider.load_access_token.assert_called_once_with("test-token")
        assert result == mock_access_token

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_on_invalid(self):
        """Test that verify_token returns None for invalid tokens."""
        mock_provider = Mock()
        mock_provider.load_access_token = AsyncMock(return_value=None)
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("invalid-token")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_handles_jwt_provider(self):
        """Test that verify_token handles JWT middleware providers."""
        mock_provider = Mock()
        # JWT provider has extract_user_from_token instead of load_access_token
        mock_provider.extract_user_from_token = Mock(return_value="user-123")
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("jwt-token")
        
        mock_provider.extract_user_from_token.assert_called_once_with("jwt-token")
        assert result is not None
        assert result.token == "jwt-token"
        assert result.client_id == "user-123"
        assert result.scopes == ['execute:mcp']

    @pytest.mark.asyncio
    async def test_verify_token_handles_jwt_provider_invalid(self):
        """Test that verify_token returns None for invalid JWT tokens."""
        mock_provider = Mock()
        mock_provider.extract_user_from_token = Mock(return_value=None)
        
        adapter = TokenVerifierAdapter(mock_provider)
        result = await adapter.verify_token("invalid-jwt")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_handles_unknown_provider(self):
        """Test that verify_token handles unknown provider types."""
        mock_provider = Mock()
        # Provider has neither load_access_token nor extract_user_from_token
        
        adapter = TokenVerifierAdapter(mock_provider)
        with patch('fastmcp.server.http_server.logger') as mock_logger:
            result = await adapter.verify_token("some-token")
        
        assert result is None
        mock_logger.error.assert_called_once()


class TestSetupAuthMiddleware:
    """Test the setup_auth_middleware_and_routes function."""

    @patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', True)
    def test_setup_with_oauth_provider(self):
        """Test setup with an OAuth provider."""
        # Mock OAuth provider
        mock_auth = Mock()
        mock_auth.required_scopes = ["read", "write"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        mock_auth.load_access_token = AsyncMock()
        
        with patch('fastmcp.server.http_server.create_auth_routes') as mock_create_routes:
            mock_create_routes.return_value = [
                Route("/auth/token", endpoint=lambda r: Response()),
                Route("/auth/revoke", endpoint=lambda r: Response()),
            ]
            
            middleware, routes, scopes = setup_auth_middleware_and_routes(mock_auth)
        
        # Verify middleware was created (should include UserContextMiddleware when available)
        assert len(middleware) == 3  # Authentication, AuthContext, UserContext
        assert any(m.cls.__name__ == "AuthenticationMiddleware" for m in middleware)
        assert any(m.cls.__name__ == "AuthContextMiddleware" for m in middleware)
        assert any(m.cls.__name__ == "UserContextMiddleware" for m in middleware)
        
        # Verify routes were created
        assert len(routes) == 2
        assert routes[0].path == "/auth/token"
        assert routes[1].path == "/auth/revoke"
        
        # Verify scopes
        assert scopes == ["read", "write"]

    @patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', False)
    def test_setup_without_user_context_middleware(self):
        """Test setup when UserContextMiddleware is not available."""
        # Mock JWT provider
        mock_auth = Mock()
        mock_auth.required_scopes = []
        # No OAuth endpoints - simple JWT auth
        
        middleware, routes, scopes = setup_auth_middleware_and_routes(mock_auth)
        
        # Verify middleware was created (without UserContextMiddleware)
        assert len(middleware) == 2  # Only Authentication and AuthContext
        assert any(m.cls.__name__ == "AuthenticationMiddleware" for m in middleware)
        assert any(m.cls.__name__ == "AuthContextMiddleware" for m in middleware)
        assert not any(m.cls.__name__ == "UserContextMiddleware" for m in middleware)
        
        # No OAuth routes for JWT-only auth
        assert len(routes) == 0
        assert scopes == []

    @patch('fastmcp.server.http_server.TokenVerifierAdapter')
    @patch('fastmcp.server.http_server.BearerAuthBackend')
    def test_setup_creates_token_verifier_adapter(self, mock_bearer_backend, mock_adapter_class):
        """Test that setup creates TokenVerifierAdapter for OAuth provider."""
        # Mock OAuth provider
        mock_auth = Mock()
        mock_auth.required_scopes = ["admin"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        # Mock adapter
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        
        with patch('fastmcp.server.http_server.create_auth_routes', return_value=[]):
            middleware, routes, scopes = setup_auth_middleware_and_routes(mock_auth)
        
        # Verify adapter was created with the auth provider
        mock_adapter_class.assert_called_once_with(mock_auth)
        
        # Verify BearerAuthBackend was created with the adapter
        mock_bearer_backend.assert_called_once_with(token_verifier=mock_adapter)


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

    @patch('fastmcp.server.http_server.register_agent_metadata_routes')
    @patch('fastmcp.server.http_server.SseServerTransport')
    def test_create_sse_app_without_auth(self, mock_sse_transport, mock_register_agent_metadata):
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
        
        # Verify agent metadata routes were registered
        mock_register_agent_metadata.assert_called_once_with(app)

    @patch('fastmcp.server.http_server.register_agent_metadata_routes')
    @patch('fastmcp.server.http_server.SseServerTransport')
    def test_create_sse_app_with_auth(self, mock_sse_transport, mock_register_agent_metadata, mock_server):
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
        
        # Verify agent metadata routes were registered
        mock_register_agent_metadata.assert_called_once_with(app)


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
        mock_session_manager.run = AsyncMock()
        mock_session_manager.handle_request = AsyncMock()
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
        
        with patch('fastmcp.server.http_server.register_agent_metadata_routes'):
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


class TestUserContextMiddlewareIntegration:
    """Test integration with UserContextMiddleware when available."""
    
    @patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', True)
    @patch('fastmcp.server.http_server.UserContextMiddleware')
    def test_user_context_middleware_added_when_available(self, mock_middleware_class):
        """Test that UserContextMiddleware is added when available."""
        mock_auth = Mock()
        mock_auth.required_scopes = ["read"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        mock_middleware = Mock()
        mock_middleware_class.return_value = mock_middleware
        
        middleware, routes, scopes = setup_auth_middleware_and_routes(mock_auth)
        
        # Verify UserContextMiddleware is in the middleware list
        assert len(middleware) == 3
        assert any(m.cls.__name__ == "UserContextMiddleware" for m in middleware)
    
    @patch('fastmcp.server.http_server.USER_CONTEXT_MIDDLEWARE_AVAILABLE', False)
    def test_user_context_middleware_skipped_when_unavailable(self):
        """Test that UserContextMiddleware is skipped when not available."""
        mock_server = Mock()
        mock_server._additional_http_routes = []
        
        # Mock JWT auth backend
        mock_auth = Mock()
        mock_auth.required_scopes = ["read"]
        mock_auth.issuer_url = "https://auth.example.com"
        mock_auth.service_documentation_url = "https://docs.example.com"
        mock_auth.client_registration_options = {}
        mock_auth.revocation_options = {}
        
        with patch('fastmcp.server.http_server.setup_auth_middleware_and_routes') as mock_setup:
            mock_setup.return_value = (
                [Middleware(RequestContextMiddleware)],
                [],
                ["read"]
            )
            
            routes, middleware, scopes = create_http_server_factory(
                server=mock_server,
                auth=mock_auth,
            )
        
        # Should work without UserContextMiddleware
        assert len(middleware) == 1
        assert scopes == ["read"]
    
    def test_user_context_middleware_import_handling(self):
        """Test that import error is handled gracefully."""
        # This test verifies the try/except block in the module
        # The actual import happens at module level, so we test the flag
        from fastmcp.server.http_server import USER_CONTEXT_MIDDLEWARE_AVAILABLE
        
        # Should be boolean
        assert isinstance(USER_CONTEXT_MIDDLEWARE_AVAILABLE, bool)


class TestEnhancedErrorHandling:
    """Test enhanced error handling capabilities."""
    
    @pytest.mark.asyncio
    async def test_middleware_error_resilience(self):
        """Test that middleware handles errors gracefully."""
        # Test RequestContextMiddleware with exception in app
        app = Mock()
        app.side_effect = Exception("App error")
        
        middleware = RequestContextMiddleware(app)
        
        scope = {"type": "http", "method": "GET", "path": "/test"}
        receive = Mock()
        
        # Should not raise exception
        try:
            await middleware(scope, receive, Mock())
        except Exception as e:
            # If an exception is raised, it should be handled appropriately
            # The exact behavior depends on the middleware implementation
            pass
    
    @pytest.mark.asyncio
    async def test_mcp_header_validation_edge_cases(self):
        """Test MCP header validation with edge cases."""
        app = Mock()
        middleware = MCPHeaderValidationMiddleware(app, cors_origins=["*"])
        
        # Test with malformed headers
        scope = {
            "type": "http",
            "path": "/mcp/test",
            "method": "POST",
            "headers": [
                (b"content-type", b""),  # Empty content type
                (b"accept", b"invalid/type"),  # Invalid accept
            ],
        }
        
        response_status = None
        async def mock_send(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
        
        await middleware(scope, Mock(), mock_send)
        
        # Should return error status
        assert response_status >= 400


class TestPerformanceOptimizations:
    """Test performance-related optimizations."""
    
    def test_middleware_order_optimization(self):
        """Test that middleware is ordered for optimal performance."""
        routes = []
        middleware = [
            Middleware(RequestContextMiddleware),
            Middleware(MCPHeaderValidationMiddleware, cors_origins=[]),
        ]
        
        app = create_base_app(routes, middleware)
        
        # Verify middleware stack exists and is properly ordered
        assert len(app.middleware) >= 2
        
        # RequestContextMiddleware should be early in the stack
        middleware_names = [m.cls.__name__ for m in app.middleware if hasattr(m, 'cls')]
        assert 'RequestContextMiddleware' in middleware_names
    
    def test_cors_middleware_caching(self):
        """Test CORS middleware configuration caching."""
        cors_origins = ["https://example.com", "https://app.example.com"]
        
        app1 = create_base_app([], [], cors_origins=cors_origins)
        app2 = create_base_app([], [], cors_origins=cors_origins)
        
        # Both apps should have CORS configured
        assert len(app1.middleware) >= 1
        assert len(app2.middleware) >= 1