"""
Authentication Middleware

This module provides middleware for protecting routes with JWT authentication.
"""

import logging
import os
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..domain.services.jwt_service import JWTService
from ..domain.entities.user import UserRole

logger = logging.getLogger(__name__)

# Initialize JWT service
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
jwt_service = JWTService(JWT_SECRET_KEY)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication
    
    This middleware checks for valid JWT tokens on protected routes.
    """
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        """
        Initialize authentication middleware
        
        Args:
            app: FastAPI application
            excluded_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
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
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through authentication
        
        Args:
            request: Incoming request
            call_next: Next middleware or endpoint
            
        Returns:
            Response from next handler or error
        """
        # Check if path is excluded
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token
        try:
            token = jwt_service.extract_token_from_header(auth_header)
            if not token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authorization header format"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Verify token
            payload = jwt_service.verify_access_token(token)
            if not payload:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.user_roles = payload.get("roles", [])
            
            # Continue to next handler
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Authentication error"}
            )


def require_auth(credentials: HTTPAuthorizationCredentials = HTTPBearer()) -> dict:
    """
    Dependency for requiring authentication
    
    Use this in endpoint dependencies to require valid JWT token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        Decoded JWT payload
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = jwt_service.verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload


def require_roles(*required_roles: str):
    """
    Dependency factory for requiring specific roles
    
    Args:
        required_roles: Roles required for access
        
    Returns:
        Dependency function that checks roles
    """
    def role_checker(payload: dict = require_auth) -> dict:
        """
        Check if user has required roles
        
        Args:
            payload: JWT payload with user info
            
        Returns:
            JWT payload if authorized
            
        Raises:
            HTTPException: If user lacks required roles
        """
        user_roles = payload.get("roles", [])
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return payload
    
    return role_checker


def get_current_user_id(request: Request) -> Optional[str]:
    """
    Get current user ID from request state
    
    Args:
        request: FastAPI request
        
    Returns:
        User ID if authenticated, None otherwise
    """
    return getattr(request.state, "user_id", None)


def get_current_user_email(request: Request) -> Optional[str]:
    """
    Get current user email from request state
    
    Args:
        request: FastAPI request
        
    Returns:
        User email if authenticated, None otherwise
    """
    return getattr(request.state, "user_email", None)


def get_current_user_roles(request: Request) -> list[str]:
    """
    Get current user roles from request state
    
    Args:
        request: FastAPI request
        
    Returns:
        User roles if authenticated, empty list otherwise
    """
    return getattr(request.state, "user_roles", [])


def is_authenticated(request: Request) -> bool:
    """
    Check if request is authenticated
    
    Args:
        request: FastAPI request
        
    Returns:
        True if authenticated, False otherwise
    """
    return hasattr(request.state, "user_id")


def has_role(request: Request, role: str) -> bool:
    """
    Check if authenticated user has specific role
    
    Args:
        request: FastAPI request
        role: Role to check
        
    Returns:
        True if user has role, False otherwise
    """
    roles = get_current_user_roles(request)
    return role in roles


def is_admin(request: Request) -> bool:
    """
    Check if authenticated user is admin
    
    Args:
        request: FastAPI request
        
    Returns:
        True if user is admin, False otherwise
    """
    return has_role(request, UserRole.ADMIN.value)