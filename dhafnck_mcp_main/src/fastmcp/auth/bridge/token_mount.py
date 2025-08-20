"""
Mount FastAPI token router on Starlette application

This module provides utilities to mount the FastAPI token management router
onto the Starlette MCP server, eliminating the need for the Starlette bridge layer.
"""

import logging
from typing import List

from starlette.routing import BaseRoute, Mount
from starlette.middleware import Middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def create_token_fastapi_app() -> FastAPI:
    """
    Create a FastAPI sub-application for token management.
    
    This replaces the Starlette bridge layer with direct FastAPI integration.
    
    Returns:
        FastAPI app with token management endpoints
    """
    # Create FastAPI app for token management
    token_app = FastAPI(
        title="Token Management API",
        description="API token management endpoints",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware to match server configuration
    token_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3800"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include the token router
    from fastmcp.server.routes.token_router import router as token_router
    token_app.include_router(token_router)
    
    # Add a health check endpoint
    @token_app.get("/health")
    async def token_health():
        return {"status": "healthy", "service": "token-management"}
    
    logger.info("Created FastAPI token management app")
    
    return token_app


def mount_token_router_on_starlette(
    server_routes: List[BaseRoute],
    mount_path: str = "/api/v2/tokens"
) -> List[BaseRoute]:
    """
    Mount FastAPI token router on Starlette routes.
    
    This replaces the Starlette bridge pattern with direct FastAPI mounting.
    
    Args:
        server_routes: Existing Starlette routes to add to
        mount_path: Path prefix for token endpoints (default: /api/v2/tokens)
        
    Returns:
        Updated routes list with FastAPI token router mounted
    """
    # Create the FastAPI token app
    token_app = create_token_fastapi_app()
    
    # Mount the FastAPI app as a sub-application
    # The token router already has /api/v2/tokens prefix, so we mount at root
    # This allows the FastAPI app to handle all its routes including the prefix
    token_mount = Mount("/", app=token_app)
    
    # Add to routes
    server_routes.append(token_mount)
    
    logger.info(f"Mounted FastAPI token router at {mount_path} (eliminating Starlette bridge)")
    
    return server_routes


def integrate_token_router_with_mcp_server(
    server_routes: List[BaseRoute],
    server_middleware: List[Middleware],
    enable_token_router: bool = True
) -> tuple[List[BaseRoute], List[Middleware]]:
    """
    Full integration of token management with MCP server using FastAPI router.
    
    This function replaces the Starlette bridge layer with direct FastAPI integration.
    
    Args:
        server_routes: Existing server routes
        server_middleware: Existing server middleware
        enable_token_router: Whether to enable the token router
        
    Returns:
        Tuple of (updated_routes, updated_middleware)
    """
    if enable_token_router:
        # Mount token router using FastAPI
        server_routes = mount_token_router_on_starlette(
            server_routes,
            mount_path="/api/v2/tokens"
        )
        
        logger.info("Integrated token management with MCP server using FastAPI router")
        logger.info("✅ Starlette bridge layer eliminated - using direct FastAPI integration")
    
    return server_routes, server_middleware