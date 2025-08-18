from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import (
    BearerAuthBackend,
    RequireAuthMiddleware,
)
from mcp.server.auth.routes import create_auth_routes
from mcp.server.lowlevel.server import LifespanResultT
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import EventStore
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route
from starlette.types import Lifespan, Receive, Scope, Send
from starlette.middleware.cors import CORSMiddleware

from fastmcp.server.auth.auth import OAuthProvider
from fastmcp.utilities.logging import get_logger
# Temporarily disable error middleware to fix circular import
# from .error_middleware import ErrorHandlingMiddleware

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

logger = get_logger(__name__)


_current_http_request: ContextVar[Request | None] = ContextVar(
    "http_request",
    default=None,
)


class StarletteWithLifespan(Starlette):
    @property
    def lifespan(self) -> Lifespan:
        return self.router.lifespan_context


@contextmanager
def set_http_request(request: Request) -> Generator[Request, None, None]:
    token = _current_http_request.set(request)
    try:
        yield request
    finally:
        _current_http_request.reset(token)


class RequestContextMiddleware:
    """
    Middleware that stores each request in a ContextVar
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            with set_http_request(Request(scope)):
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


def setup_auth_middleware_and_routes(
    auth: OAuthProvider,
) -> tuple[list[Middleware], list[BaseRoute], list[str]]:
    """Set up authentication middleware and routes if auth is enabled.

    Args:
        auth: The OAuthProvider authorization server provider

    Returns:
        Tuple of (middleware, auth_routes, required_scopes)
    """
    middleware: list[Middleware] = []
    auth_routes: list[BaseRoute] = []
    required_scopes: list[str] = []

    middleware = [
        Middleware(
            AuthenticationMiddleware,
            backend=BearerAuthBackend(provider=auth),
        ),
        Middleware(AuthContextMiddleware),
    ]

    required_scopes = auth.required_scopes or []

    auth_routes.extend(
        create_auth_routes(
            provider=auth,
            issuer_url=auth.issuer_url,
            service_documentation_url=auth.service_documentation_url,
            client_registration_options=auth.client_registration_options,
            revocation_options=auth.revocation_options,
        )
    )

    return middleware, auth_routes, required_scopes


def create_base_app(
    routes: list[BaseRoute],
    middleware: list[Middleware],
    debug: bool = False,
    lifespan: Callable | None = None,
    cors_origins: list[str] | None = None,
) -> StarletteWithLifespan:
    """Create a base Starlette app with common middleware and routes.

    Args:
        routes: List of routes to include in the app
        middleware: List of middleware to include in the app
        debug: Whether to enable debug mode
        lifespan: Optional lifespan manager for the app
        cors_origins: List of allowed CORS origins, defaults to ["http://localhost:3000"]

    Returns:
        A Starlette application
    """
    # Always add RequestContextMiddleware as the outermost middleware
    middleware.append(Middleware(RequestContextMiddleware))
    
    # Add error handling middleware
    # Temporarily disabled to fix circular import
    # middleware.append(Middleware(ErrorHandlingMiddleware))
    
    # Add CORS middleware to allow requests from frontend
    if cors_origins is None:
        cors_origins = ["http://localhost:3000", "http://localhost:3800"]
    
    middleware.append(
        Middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    )
    return StarletteWithLifespan(
        routes=routes,
        middleware=middleware,
        debug=debug,
        lifespan=lifespan,
    )


def create_http_server_factory(
    server: FastMCP[LifespanResultT],
    auth: OAuthProvider | None = None,
    debug: bool = False,
    routes: list[BaseRoute] | None = None,
    middleware: list[Middleware] | None = None,
    cors_origins: list[str] | None = None,
) -> tuple[list[BaseRoute], list[Middleware], list[str]]:
    """Factory function to create common server components for both SSE and Streamable HTTP apps.
    
    Args:
        server: The FastMCP server instance
        auth: Optional OAuth provider for authentication
        debug: Whether to enable debug mode
        routes: Optional additional routes to include
        middleware: Optional additional middleware to include
        cors_origins: List of allowed CORS origins
        
    Returns:
        Tuple of (server_routes, server_middleware, required_scopes)
    """
    if cors_origins is None:
        cors_origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3800"]
    
    # Initialize base components
    server_routes: list[BaseRoute] = []
    server_middleware: list[Middleware] = []
    required_scopes: list[str] = []
    
    # Add custom routes if provided
    if routes:
        server_routes.extend(routes)
    
    # Add custom middleware if provided
    if middleware:
        server_middleware.extend(middleware)
    
    # Set up authentication if provided
    if auth:
        auth_middleware, auth_routes, auth_scopes = setup_auth_middleware_and_routes(auth)
        server_middleware.extend(auth_middleware)
        server_routes.extend(auth_routes)
        required_scopes.extend(auth_scopes)
    
    return server_routes, server_middleware, required_scopes


def create_sse_app(
    server: FastMCP[LifespanResultT],
    message_path: str,
    sse_path: str,
    auth: OAuthProvider | None = None,
    debug: bool = False,
    routes: list[BaseRoute] | None = None,
    middleware: list[Middleware] | None = None,
    cors_origins: list[str] | None = None,
) -> StarletteWithLifespan:
    """Return an instance of the SSE server app.

    Args:
        server: The FastMCP server instance
        message_path: Path for SSE messages
        sse_path: Path for SSE connections
        auth: Optional auth provider
        debug: Whether to enable debug mode
        routes: Optional list of custom routes
        middleware: Optional list of middleware
        cors_origins: List of allowed CORS origins
    Returns:
        A Starlette application with RequestContextMiddleware
    """

    # Ensure the message_path ends with a trailing slash to avoid automatic redirects
    if not message_path.endswith("/"):
        message_path = message_path + "/"

    # Use factory to get common components
    server_routes, server_middleware, required_scopes = create_http_server_factory(
        server=server,
        auth=auth,
        debug=debug,
        routes=routes,
        middleware=middleware,
        cors_origins=cors_origins,
    )

    # Add server's additional HTTP routes
    server_routes.extend(server._additional_http_routes)
    
    # Add auth integration routes for SSE app
    try:
        from .routes.auth_integration import create_auth_integration_routes
        auth_routes = create_auth_integration_routes()
        if auth_routes:
            server_routes.extend(auth_routes)
            logger.info("Auth API routes integrated into SSE server at /api/auth/*")
    except ImportError as e:
        logger.warning(f"Could not import auth integration routes: {e}")
    
    # Add Supabase auth integration routes
    try:
        from .routes.supabase_auth_integration import create_supabase_auth_integration_routes
        supabase_auth_routes = create_supabase_auth_integration_routes()
        if supabase_auth_routes:
            server_routes.extend(supabase_auth_routes)
            logger.info(f"Supabase auth routes integrated into SSE server at /auth/supabase/* ({len(supabase_auth_routes)} routes)")
    except ImportError as e:
        logger.warning(f"Could not import Supabase auth integration routes: {e}")
    
    # Add task summary routes for lazy loading optimization
    try:
        from .routes.task_summary_routes import task_summary_routes
        server_routes.extend(task_summary_routes)
        logger.info("Task summary routes registered for lazy loading optimization")
    except ImportError as e:
        logger.warning(f"Could not import task summary routes: {e}")
    
    # Add OAuth2 auth endpoints using bridge pattern
    try:
        from fastmcp.auth.bridge.fastapi_mount import integrate_auth_with_mcp_server
        server_routes, server_middleware = integrate_auth_with_mcp_server(
            server_routes,
            server_middleware,
            enable_bridge=True
        )
        logger.info("OAuth2 auth endpoints mounted via bridge pattern")
    except ImportError as e:
        logger.warning(f"Could not mount OAuth2 auth endpoints: {e}")

    # Set up SSE transport
    sse = SseServerTransport(message_path)

    # Create handler for SSE connections
    async def handle_sse(scope: Scope, receive: Receive, send: Send) -> Response:
        async with sse.connect_sse(scope, receive, send) as streams:
            await server._mcp_server.run(
                streams[0],
                streams[1],
                server._mcp_server.create_initialization_options(),
            )
        return Response()

    # Add SSE-specific routes with or without auth
    if auth:
        # Auth is enabled, wrap endpoints with RequireAuthMiddleware
        server_routes.append(
            Route(
                sse_path,
                endpoint=RequireAuthMiddleware(handle_sse, required_scopes),
                methods=["GET"],
            )
        )
        server_routes.append(
            Mount(
                message_path,
                app=RequireAuthMiddleware(sse.handle_post_message, required_scopes),
            )
        )
    else:
        # No auth required
        async def sse_endpoint(request: Request) -> Response:
            return await handle_sse(request.scope, request.receive, request._send)  # type: ignore[reportPrivateUsage]

        server_routes.append(
            Route(
                sse_path,
                endpoint=sse_endpoint,
                methods=["GET"],
            )
        )
        server_routes.append(
            Mount(
                message_path,
                app=sse.handle_post_message,
            )
        )

    # Create and return the app
    app = create_base_app(
        routes=server_routes,
        middleware=server_middleware,
        debug=debug,
        cors_origins=cors_origins,
    )
    # Store the FastMCP server instance on the Starlette app state
    app.state.fastmcp_server = server
    app.state.path = sse_path

    return app


class MCPHeaderValidationMiddleware:
    """
    Middleware to enforce MCP protocol header requirements for Streamable HTTP endpoints.
    """
    def __init__(self, app, cors_origins: list[str] | None = None):
        self.app = app
        self.cors_origins = cors_origins or ["http://localhost:3000", "http://localhost:3800"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "").upper()
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        async def send_error(status_code, detail):
            from starlette.responses import JSONResponse
            response = JSONResponse({"error": detail}, status_code=status_code)
            # Add CORS headers to error responses
            origin = headers.get("origin", "")
            if origin in self.cors_origins or "*" in self.cors_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
            elif self.cors_origins:
                response.headers["Access-Control-Allow-Origin"] = self.cors_origins[0]
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            await response(scope, receive, send)

        # Only enforce for /mcp endpoints
        if path.startswith("/mcp"):
            # Always require Content-Type and Accept for POST
            if method == "POST":
                if headers.get("content-type", "") != "application/json":
                    await send_error(415, "Content-Type must be application/json")
                    return
                if "application/json" not in headers.get("accept", "") or "text/event-stream" not in headers.get("accept", ""):
                    await send_error(406, "Accept header must include both application/json and text/event-stream")
                    return

                # /mcp/initialize only needs Content-Type and Accept
                if path == "/mcp/initialize":
                    await self.app(scope, receive, send)
                    return

                # For other /mcp POST requests, also pass through after validation
                await self.app(scope, receive, send)
                return
                
            # For GET (SSE), require Accept
            elif method == "GET":
                if "text/event-stream" not in headers.get("accept", ""):
                    await send_error(406, "Accept header must include text/event-stream for SSE")
                    return
        await self.app(scope, receive, send)


def create_streamable_http_app(
    server: FastMCP[LifespanResultT],
    streamable_http_path: str,
    event_store: EventStore | None = None,
    auth: OAuthProvider | None = None,
    json_response: bool = False,
    stateless_http: bool = False,
    debug: bool = False,
    routes: list[BaseRoute] | None = None,
    middleware: list[Middleware] | None = None,
    cors_origins: list[str] | None = None,
) -> StarletteWithLifespan:
    """Return an instance of the streamable HTTP server app."""
    server_routes: list[BaseRoute] = []
    server_middleware: list[Middleware] = []

    if auth:
        auth_middleware, auth_routes, required_scopes = (
            setup_auth_middleware_and_routes(auth)
        )
        server_routes.extend(auth_routes)
        server_middleware.extend(auth_middleware)

    session_manager = StreamableHTTPSessionManager(
        server._mcp_server,
        event_store=event_store,
        json_response=json_response,
        stateless=stateless_http,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle streamable HTTP requests."""
        if auth and "user" not in scope:
            # This should not happen if RequireAuthMiddleware is used
            raise RuntimeError("User not found in scope")

        await session_manager.handle_request(scope, receive, send)

    if auth:
        # Auth is enabled, wrap endpoint with RequireAuthMiddleware
        server_routes.append(
            Route(
                streamable_http_path,
                endpoint=RequireAuthMiddleware(
                    handle_streamable_http, required_scopes=required_scopes
                ),
                methods=["POST"],
            )
        )
    else:
        # No auth required - create a proper Starlette endpoint wrapper
        async def streamable_http_endpoint(request: Request) -> Response:
            """Starlette endpoint wrapper for streamable HTTP requests."""
            # Since handle_streamable_http manages the response directly via ASGI,
            # we need to return an empty Response to satisfy Starlette's expectations
            await handle_streamable_http(request.scope, request.receive, request._send)  # type: ignore[reportPrivateUsage]
            return Response(content=b"", status_code=200)
        
        server_routes.append(
            Route(streamable_http_path, endpoint=streamable_http_endpoint, methods=["POST"])
        )

    # Add custom routes with lowest precedence
    if routes:
        server_routes.extend(routes)
    server_routes.extend(server._additional_http_routes)
    
    # Add auth integration routes
    try:
        from .routes.auth_integration import create_auth_integration_routes
        auth_routes = create_auth_integration_routes()
        if auth_routes:
            server_routes.extend(auth_routes)
            logger.info("Auth API routes integrated into MCP server at /api/auth/*")
    except ImportError as e:
        logger.warning(f"Could not import auth integration routes: {e}")
    
    # Add Supabase auth integration routes
    try:
        from .routes.supabase_auth_integration import create_supabase_auth_integration_routes
        supabase_auth_routes = create_supabase_auth_integration_routes()
        if supabase_auth_routes:
            server_routes.extend(supabase_auth_routes)
            logger.info(f"Supabase auth routes integrated into MCP server at /auth/supabase/* ({len(supabase_auth_routes)} routes)")
    except ImportError as e:
        logger.warning(f"Could not import Supabase auth integration routes: {e}")
    
    # Add task summary routes for lazy loading optimization
    try:
        from .routes.task_summary_routes import task_summary_routes
        server_routes.extend(task_summary_routes)
        logger.info("Task summary routes registered for streamable HTTP optimization")
    except ImportError as e:
        logger.warning(f"Could not import task summary routes: {e}")
    
    # Add branch summary routes for sidebar optimization
    try:
        from .routes.branch_summary_routes import branch_summary_routes
        server_routes.extend(branch_summary_routes)
        logger.info("Branch summary routes registered for sidebar performance optimization")
    except ImportError as e:
        logger.warning(f"Could not import branch summary routes: {e}")

    if middleware:
        server_middleware.extend(middleware)

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:
        # Lifespan context for the app
        # Initialize and run session manager with proper lifecycle management
        async with session_manager.run():
            yield

    # Always add MCPHeaderValidationMiddleware as one of the outermost middleware
    if cors_origins is None:
        cors_origins = ["http://localhost:3000", "http://localhost:3800"]
    server_middleware.append(Middleware(MCPHeaderValidationMiddleware, cors_origins=cors_origins))

    app = create_base_app(
        routes=server_routes,
        middleware=server_middleware,
        debug=debug,
        lifespan=lifespan,
        cors_origins=cors_origins,
    )
    # Store the FastMCP server instance and path on the Starlette app state
    app.state.fastmcp_server = server
    app.state.path = streamable_http_path
    
    return app
