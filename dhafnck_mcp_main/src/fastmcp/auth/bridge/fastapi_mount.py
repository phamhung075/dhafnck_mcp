"""
Mount FastAPI auth endpoints on Starlette application

This module provides utilities to mount FastAPI routers (specifically auth endpoints)
onto a Starlette application, enabling OAuth2 authentication endpoints to be served
alongside MCP protocol endpoints.
"""

import logging
from typing import List, Optional

from starlette.applications import Starlette
from starlette.routing import BaseRoute, Mount
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import FastAPI
from fastapi.routing import APIRouter

# Import our auth router
from ..interface.auth_endpoints import router as auth_router

logger = logging.getLogger(__name__)


def create_fastapi_sub_app() -> FastAPI:
    """
    Create a FastAPI sub-application containing auth endpoints.
    
    This FastAPI app will be mounted as a sub-application on the
    main Starlette app used by the MCP server.
    
    Returns:
        FastAPI app with auth endpoints
    """
    # Create FastAPI app for auth endpoints
    fastapi_app = FastAPI(
        title="Authentication API",
        description="OAuth2 authentication endpoints",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Include the auth router
    fastapi_app.include_router(auth_router)
    
    # Add a health check endpoint
    @fastapi_app.get("/health")
    async def auth_health():
        return {"status": "healthy", "service": "auth"}
    
    logger.info("Created FastAPI sub-app with auth endpoints")
    
    return fastapi_app


def mount_fastapi_auth_on_starlette(
    starlette_routes: List[BaseRoute],
    mount_path: str = "/api/auth"
) -> List[BaseRoute]:
    """
    Mount FastAPI auth endpoints on Starlette routes.
    
    Args:
        starlette_routes: Existing Starlette routes to add to
        mount_path: Path prefix for auth endpoints (default: /api/auth)
        
    Returns:
        Updated routes list with FastAPI auth mounted
    """
    # Create the FastAPI sub-app
    fastapi_app = create_fastapi_sub_app()
    
    # Mount the FastAPI app as a sub-application
    auth_mount = Mount(mount_path, app=fastapi_app)
    
    # Add to routes
    starlette_routes.append(auth_mount)
    
    logger.info(f"Mounted FastAPI auth endpoints at {mount_path}")
    
    return starlette_routes


def add_auth_routes_to_http_server(
    server_routes: List[BaseRoute],
    enable_oauth2: bool = True,
    enable_docs: bool = True
) -> List[BaseRoute]:
    """
    Add OAuth2 auth routes to the HTTP server routes.
    
    This is the main integration point for adding FastAPI OAuth2
    endpoints to the MCP server's Starlette application.
    
    Args:
        server_routes: Existing server routes
        enable_oauth2: Whether to enable OAuth2 endpoints
        enable_docs: Whether to enable API documentation endpoints
        
    Returns:
        Updated routes with auth endpoints
    """
    if not enable_oauth2:
        logger.info("OAuth2 endpoints disabled")
        return server_routes
    
    # Create a sub-app for auth
    auth_app = FastAPI(
        title="DhafnckMCP Authentication",
        description="OAuth2 authentication for REST API endpoints",
        version="1.0.0",
        docs_url="/api/auth/docs" if enable_docs else None,
        redoc_url="/api/auth/redoc" if enable_docs else None,
        openapi_url="/api/auth/openapi.json" if enable_docs else None
    )
    
    # Include our auth router
    auth_app.include_router(auth_router)
    
    # Include protected task routes
    try:
        from fastmcp.server.routes.protected_task_routes import router as task_router
        auth_app.include_router(task_router)
        logger.info("Added protected task routes with OAuth2")
    except ImportError as e:
        logger.warning(f"Could not import protected task routes: {e}")
    
    # Mount at /api/auth (the router already has /api/auth prefix, so we mount at root)
    # But since the router has the prefix, we need to mount without it
    auth_mount = Mount("/", app=auth_app)
    
    server_routes.append(auth_mount)
    
    logger.info("Added OAuth2 auth routes to HTTP server")
    
    return server_routes


def integrate_auth_with_mcp_server(
    server_routes: List[BaseRoute],
    server_middleware: List[Middleware],
    enable_bridge: bool = True
) -> tuple[List[BaseRoute], List[Middleware]]:
    """
    Full integration of OAuth2 auth with MCP server.
    
    This function adds both the auth routes and any necessary
    middleware for the auth bridge to work properly.
    
    Args:
        server_routes: Existing server routes
        server_middleware: Existing server middleware
        enable_bridge: Whether to enable the auth bridge
        
    Returns:
        Tuple of (updated_routes, updated_middleware)
    """
    if enable_bridge:
        # Add OAuth2 auth routes
        server_routes = add_auth_routes_to_http_server(
            server_routes,
            enable_oauth2=True,
            enable_docs=True
        )
        
        # Note: We don't add middleware here as the bridge handles
        # auth at the endpoint level using FastAPI dependencies
        
        logger.info("Integrated OAuth2 auth with MCP server using bridge pattern")
    
    return server_routes, server_middleware