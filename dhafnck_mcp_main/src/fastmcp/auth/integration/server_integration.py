"""
Authentication Server Integration

This module provides integration of authentication with the FastMCP server.
"""

import os
from typing import Optional, List
from starlette.middleware import Middleware
from starlette.routing import BaseRoute, Mount
from starlette.applications import Starlette

from ..interface.auth_endpoints import router as auth_router
from ..interface.auth_middleware import AuthenticationMiddleware


def setup_authentication(
    app: Starlette,
    jwt_secret_key: Optional[str] = None,
    excluded_paths: Optional[List[str]] = None
) -> None:
    """
    Set up authentication for the FastMCP server
    
    Args:
        app: Starlette/FastAPI application
        jwt_secret_key: Secret key for JWT signing
        excluded_paths: Paths to exclude from authentication
    """
    # Set JWT secret if provided
    if jwt_secret_key:
        os.environ["JWT_SECRET_KEY"] = jwt_secret_key
    
    # Add authentication middleware
    auth_middleware = AuthenticationMiddleware(
        app,
        excluded_paths=excluded_paths
    )
    
    # Note: In Starlette, middleware is added to the app differently
    # The middleware should be added during app creation


def get_auth_routes() -> List[BaseRoute]:
    """
    Get authentication routes for mounting
    
    Returns:
        List of authentication routes
    """
    # Convert FastAPI router to Starlette routes
    # This would need proper conversion from FastAPI to Starlette
    # For now, return empty list - routes should be mounted differently
    return []


def get_auth_middleware(
    excluded_paths: Optional[List[str]] = None
) -> List[Middleware]:
    """
    Get authentication middleware for the server
    
    Args:
        excluded_paths: Paths to exclude from authentication
        
    Returns:
        List of middleware instances
    """
    return [
        Middleware(
            AuthenticationMiddleware,
            excluded_paths=excluded_paths or [
                "/api/auth/register",
                "/api/auth/login", 
                "/api/auth/password-reset",
                "/api/auth/password-reset/confirm",
                "/api/auth/verify-email",
                "/api/auth/health",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/",
            ]
        )
    ]


def create_auth_app() -> Starlette:
    """
    Create a standalone authentication Starlette app
    
    This can be mounted as a sub-application
    
    Returns:
        Starlette app with authentication endpoints
    """
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def register(request):
        """Register endpoint stub"""
        return JSONResponse({"message": "Registration endpoint"})
    
    async def login(request):
        """Login endpoint stub"""
        return JSONResponse({"message": "Login endpoint"})
    
    async def health(request):
        """Health check endpoint"""
        return JSONResponse({"status": "healthy"})
    
    routes = [
        Route("/register", register, methods=["POST"]),
        Route("/login", login, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
    ]
    
    app = Starlette(routes=routes)
    return app