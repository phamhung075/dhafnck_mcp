"""
Authentication Bridge for MCP and OAuth2PasswordBearer

This module provides a bridge pattern implementation to allow both MCP's native
authentication (BearerAuthBackend) and FastAPI's OAuth2PasswordBearer to coexist.
This enables MCP protocol operations to continue using their native auth while
REST API endpoints can use OAuth2PasswordBearer.
"""

import logging
from typing import Optional, Union, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request
from sqlalchemy.orm import Session

# Import MCP auth components
try:
    from mcp.server.auth.provider import AccessToken
    from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
except ImportError:
    # Fallback if MCP is not available
    AccessToken = None
    BearerAuthBackend = None

# Import our OAuth2 components
from ..interface.fastapi_auth import oauth2_scheme, get_current_user, get_current_active_user, get_db
from ..domain.entities.user import User
from ..domain.services.jwt_service import JWTService

logger = logging.getLogger(__name__)


class AuthBridge:
    """
    Bridge class that can validate tokens from both MCP's BearerAuthBackend
    and FastAPI's OAuth2PasswordBearer authentication systems.
    
    This allows both authentication systems to coexist:
    - MCP protocol operations use BearerAuthBackend
    - REST API endpoints use OAuth2PasswordBearer
    """
    
    def __init__(
        self,
        jwt_service: Optional[JWTService] = None,
        mcp_backend: Optional[BearerAuthBackend] = None,
        enable_mcp: bool = True,
        enable_oauth2: bool = True
    ):
        """
        Initialize the AuthBridge with both authentication backends.
        
        Args:
            jwt_service: JWT service for OAuth2 token validation
            mcp_backend: MCP's bearer authentication backend
            enable_mcp: Whether to enable MCP authentication
            enable_oauth2: Whether to enable OAuth2 authentication
        """
        self.jwt_service = jwt_service or self._create_jwt_service()
        self.mcp_backend = mcp_backend
        self.enable_mcp = enable_mcp and (BearerAuthBackend is not None)
        self.enable_oauth2 = enable_oauth2
        
        # Cache for validated tokens
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"AuthBridge initialized - MCP: {self.enable_mcp}, OAuth2: {self.enable_oauth2}")
    
    def _create_jwt_service(self) -> JWTService:
        """Create a default JWT service."""
        import os
        secret_key = os.environ.get("JWT_SECRET_KEY", "default-secret-key-change-in-production")
        return JWTService(secret_key=secret_key)
    
    async def validate_token(
        self,
        token: str,
        prefer_oauth2: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a token using either OAuth2 or MCP authentication.
        
        Args:
            token: The bearer token to validate
            prefer_oauth2: Whether to try OAuth2 first (default: True)
            
        Returns:
            Dict containing user information and auth method used
            
        Raises:
            HTTPException: If token validation fails
        """
        # Check cache first
        if token in self._token_cache:
            cached = self._token_cache[token]
            # Simple cache expiry check (5 minutes)
            if (datetime.utcnow() - cached.get("cached_at", datetime.min)).seconds < 300:
                return cached
        
        result = None
        
        # Try OAuth2 first if preferred and enabled
        if prefer_oauth2 and self.enable_oauth2:
            result = await self._validate_oauth2_token(token)
            if result:
                result["auth_method"] = "oauth2"
        
        # Try MCP if OAuth2 failed or not preferred
        if not result and self.enable_mcp:
            result = await self._validate_mcp_token(token)
            if result:
                result["auth_method"] = "mcp"
        
        # Try the other method if the first failed
        if not result:
            if not prefer_oauth2 and self.enable_oauth2:
                result = await self._validate_oauth2_token(token)
                if result:
                    result["auth_method"] = "oauth2"
            elif prefer_oauth2 and self.enable_mcp:
                result = await self._validate_mcp_token(token)
                if result:
                    result["auth_method"] = "mcp"
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Cache the result
        result["cached_at"] = datetime.utcnow()
        self._token_cache[token] = result
        
        return result
    
    async def _validate_oauth2_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate token using OAuth2PasswordBearer.
        
        Args:
            token: The bearer token
            
        Returns:
            User information if valid, None otherwise
        """
        try:
            # Validate the JWT token
            payload = self.jwt_service.verify_access_token(token)
            if not payload:
                return None
            
            # Get user information
            user_id = payload.get("sub")
            email = payload.get("email")
            roles = payload.get("roles", [])
            
            return {
                "user_id": user_id,
                "email": email,
                "roles": roles,
                "scopes": self._roles_to_scopes(roles),
                "token_type": "access",
                "auth_method": "oauth2"
            }
            
        except Exception as e:
            logger.debug(f"OAuth2 token validation failed: {e}")
            return None
    
    async def _validate_mcp_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate token using MCP's BearerAuthBackend.
        
        Args:
            token: The bearer token
            
        Returns:
            User information if valid, None otherwise
        """
        if not self.mcp_backend:
            return None
        
        try:
            # Use MCP's bearer backend to validate
            access_token = await self.mcp_backend.load_access_token(token)
            
            if not access_token:
                return None
            
            return {
                "user_id": access_token.client_id,
                "email": None,  # MCP doesn't provide email
                "roles": [],  # MCP uses scopes instead of roles
                "scopes": list(access_token.scopes),
                "token_type": "bearer",
                "auth_method": "mcp"
            }
            
        except Exception as e:
            logger.debug(f"MCP token validation failed: {e}")
            return None
    
    def _roles_to_scopes(self, roles: list) -> list:
        """Convert user roles to MCP-compatible scopes."""
        scope_map = {
            "admin": ["mcp:admin", "mcp:write", "mcp:read", "mcp:access"],
            "developer": ["mcp:write", "mcp:read", "mcp:access"],
            "user": ["mcp:read", "mcp:access"],
            "guest": ["mcp:access"]
        }
        
        scopes = set()
        for role in roles:
            scopes.update(scope_map.get(role.lower(), []))
        
        return list(scopes)
    
    def clear_cache(self, token: Optional[str] = None):
        """
        Clear the token cache.
        
        Args:
            token: Specific token to clear, or None to clear all
        """
        if token:
            self._token_cache.pop(token, None)
        else:
            self._token_cache.clear()


# Dependency injection functions for FastAPI
_auth_bridge: Optional[AuthBridge] = None


def get_auth_bridge() -> AuthBridge:
    """Get or create the global AuthBridge instance."""
    global _auth_bridge
    
    if _auth_bridge is None:
        # Try to get MCP backend if available
        mcp_backend = None
        if BearerAuthBackend is not None:
            try:
                # This would need to be properly initialized with MCP provider
                # For now, we'll leave it as None and let OAuth2 handle everything
                pass
            except Exception as e:
                logger.warning(f"Could not initialize MCP backend: {e}")
        
        _auth_bridge = AuthBridge(
            mcp_backend=mcp_backend,
            enable_mcp=bool(mcp_backend),
            enable_oauth2=True
        )
    
    return _auth_bridge


async def get_current_user_from_bridge(
    request: Request,
    auth_bridge: AuthBridge = Depends(get_auth_bridge)
) -> Dict[str, Any]:
    """
    Dependency to get current user from either auth system.
    
    This can be used in FastAPI endpoints to accept tokens from
    either MCP or OAuth2 authentication.
    """
    # Extract token from Authorization header
    authorization = request.headers.get("Authorization", "")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Validate token through the bridge
    user_info = await auth_bridge.validate_token(token)
    
    return user_info


# Alias for backward compatibility
get_bridged_user = get_current_user_from_bridge