"""
JWT Authentication Backend for MCP Integration

This module provides the integration between our JWT authentication system
and the MCP server infrastructure.
"""

import os
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from mcp.server.auth.provider import AccessToken
from fastmcp.server.auth.providers.bearer import BearerAuthProvider

from ..domain.services.jwt_service import JWTService
from ..application.services.auth_service import AuthService
from ..infrastructure.repositories.user_repository import UserRepository


@dataclass
class MCPUserContext:
    """User context for MCP operations"""
    user_id: str
    email: str
    username: str
    roles: List[str]
    scopes: List[str]


class JWTAuthBackend(BearerAuthProvider):
    """
    JWT Authentication Backend that integrates our authentication system
    with the MCP server infrastructure.
    
    This backend:
    1. Validates JWT tokens using our JWTService
    2. Extracts user context from tokens
    3. Provides user filtering for MCP operations
    """
    
    def __init__(
        self,
        jwt_service: Optional[JWTService] = None,
        auth_service: Optional[AuthService] = None,
        user_repository: Optional[UserRepository] = None,
        required_scopes: Optional[List[str]] = None
    ):
        """
        Initialize the JWT auth backend.
        
        Args:
            jwt_service: Service for JWT operations
            auth_service: Authentication service
            user_repository: User repository for user lookups
            required_scopes: List of required scopes for MCP access
        """
        # Get JWT secret from environment
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            raise ValueError("JWT_SECRET_KEY environment variable not set")
        
        # Initialize services if not provided
        self._jwt_service = jwt_service or JWTService(secret_key=jwt_secret)
        self._auth_service = auth_service
        self._user_repository = user_repository
        
        # Get issuer and audience from environment
        issuer = os.getenv("JWT_ISSUER", "dhafnck-mcp")
        audience = os.getenv("JWT_AUDIENCE", "mcp-server")
        
        # Initialize parent with a dummy public key since we handle validation ourselves
        # The parent class requires either public_key or jwks_uri, but we use symmetric keys
        # So we provide a dummy RSA public key that won't be used
        dummy_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tRgeLezV6ffAt0gunVTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u
+qKhbwKfBstIs+bMY2Zkp18gnTxKLxoS2tFczGkPLPgizskuemMghRniWaoLcyeh
kd3qqGElvW/VDL5AaWTg0nLVkjRo9z+40RQzuVaE8AkAFmxZzow3x+VJYKdjykkJ
0iT9wCS0DRTXu269V264Vf/3jvredZiKRkgwlL9xNAwxXFg0x/XFw005UWVRIkdg
cKWTjpBP2dPwVZ4WWC+9aGVd+Gyn1o0CLelf4rEjGoXbAAEgAqeGUxrcIlbjXfbc
mwIDAQAB
-----END PUBLIC KEY-----"""
        
        super().__init__(
            public_key=dummy_public_key,  # Dummy key, we override validation
            jwks_uri=None,
            issuer=issuer,
            audience=audience,
            required_scopes=required_scopes or ["mcp:access"]
        )
        
        # Cache for user contexts
        self._user_context_cache: Dict[str, MCPUserContext] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, float] = {}
    
    async def load_access_token(self, token: str) -> Optional[AccessToken]:
        """
        Validate JWT token and return AccessToken for MCP.
        
        Args:
            token: JWT token string
            
        Returns:
            AccessToken if valid, None otherwise
        """
        try:
            # Validate token using our JWT service
            payload = self._jwt_service.verify_token(token, expected_type="access")
            if not payload:
                return None
            
            # Extract user information
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Get or cache user context
            user_context = await self._get_user_context(user_id)
            if not user_context:
                return None
            
            # Extract scopes from token
            scopes = payload.get("scopes", [])
            if isinstance(scopes, str):
                scopes = scopes.split()
            
            # Add MCP-specific scopes based on user roles
            mcp_scopes = self._map_roles_to_scopes(user_context.roles)
            all_scopes = list(set(scopes + mcp_scopes))
            
            # Get expiration
            exp = payload.get("exp")
            
            # Return AccessToken for MCP
            return AccessToken(
                token=token,
                client_id=user_id,  # Use user_id as client_id
                scopes=all_scopes,
                expires_at=int(exp) if exp else None
            )
            
        except Exception as e:
            # Log error but don't expose internal details
            import logging
            logging.getLogger(__name__).error(f"Token validation failed: {e}")
            return None
    
    async def _get_user_context(self, user_id: str) -> Optional[MCPUserContext]:
        """
        Get user context, using cache if available.
        
        Args:
            user_id: User ID to get context for
            
        Returns:
            User context or None if user not found
        """
        # Check cache
        now = time.time()
        if user_id in self._user_context_cache:
            cache_time = self._cache_timestamps.get(user_id, 0)
            if now - cache_time < self._cache_ttl:
                return self._user_context_cache[user_id]
        
        # Load from repository if available
        if self._user_repository:
            try:
                from fastmcp.auth.domain.value_objects import UserId
                domain_user_id = UserId(user_id)
                user = self._user_repository.find_by_id(domain_user_id)
                
                if user:
                    context = MCPUserContext(
                        user_id=str(user.id.value),
                        email=user.email,
                        username=user.username,
                        roles=[str(role) for role in user.roles],
                        scopes=[]  # Scopes come from token
                    )
                    
                    # Cache the context
                    self._user_context_cache[user_id] = context
                    self._cache_timestamps[user_id] = now
                    
                    return context
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load user {user_id}: {e}")
        
        # Fallback: Create minimal context from token data
        # This allows the system to work even without database access
        return MCPUserContext(
            user_id=user_id,
            email="",
            username=user_id,
            roles=["user"],
            scopes=[]
        )
    
    def _map_roles_to_scopes(self, roles: List[str]) -> List[str]:
        """
        Map user roles to MCP scopes.
        
        Args:
            roles: List of user roles
            
        Returns:
            List of MCP scopes
        """
        scope_mapping = {
            "admin": ["mcp:admin", "mcp:write", "mcp:read"],
            "developer": ["mcp:write", "mcp:read"],
            "user": ["mcp:read"]
        }
        
        scopes = ["mcp:access"]  # Base scope for all authenticated users
        
        for role in roles:
            role_lower = role.lower()
            if role_lower in scope_mapping:
                scopes.extend(scope_mapping[role_lower])
        
        return list(set(scopes))  # Remove duplicates
    
    def get_current_user_id(self, token: str) -> Optional[str]:
        """
        Extract user ID from token without full validation.
        Useful for filtering operations by user.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID or None
        """
        try:
            # Decode without verification for quick user extraction
            # This is safe for filtering, not for authentication
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub")
        except:
            return None


def create_jwt_auth_backend(
    database_session_factory=None,
    required_scopes: Optional[List[str]] = None
) -> JWTAuthBackend:
    """
    Factory function to create JWT auth backend with dependencies.
    
    Args:
        database_session_factory: Database session factory
        required_scopes: Required scopes for MCP access
        
    Returns:
        Configured JWT auth backend
    """
    # Initialize services
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise ValueError("JWT_SECRET_KEY environment variable not set")
    
    jwt_service = JWTService(secret_key=jwt_secret)
    
    # Initialize repositories if database is available
    user_repository = None
    auth_service = None
    
    if database_session_factory:
        user_repository = UserRepository(database_session_factory)
        # AuthService initialization would go here if needed
    
    return JWTAuthBackend(
        jwt_service=jwt_service,
        auth_service=auth_service,
        user_repository=user_repository,
        required_scopes=required_scopes
    )