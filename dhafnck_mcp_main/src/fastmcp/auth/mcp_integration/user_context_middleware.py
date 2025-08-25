"""
User Context Middleware for MCP Operations

This middleware extracts user context from JWT tokens and makes it available
for filtering MCP operations by user.
"""

import logging
from typing import Optional
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser

from .jwt_auth_backend import JWTAuthBackend, MCPUserContext

logger = logging.getLogger(__name__)

# Context variable to store current user context
current_user_context: ContextVar[Optional[MCPUserContext]] = ContextVar(
    "current_user_context",
    default=None
)


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts user context from JWT tokens and stores it
    in a context variable for use throughout the request lifecycle.
    """
    
    def __init__(self, app, jwt_backend: Optional[JWTAuthBackend] = None):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            jwt_backend: JWT authentication backend
        """
        super().__init__(app)
        self.jwt_backend = jwt_backend or self._create_default_backend()
    
    def _create_default_backend(self) -> JWTAuthBackend:
        """Create a default JWT backend if none provided."""
        from .jwt_auth_backend import create_jwt_auth_backend
        return create_jwt_auth_backend()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Extract user context from MCP authenticated user and store in context variable.
        
        This middleware runs after MCP's AuthenticationMiddleware, so we can rely
        on the authenticated user being available in request.user if authentication succeeded.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler
            
        Returns:
            Response from the next handler
        """
        logger.info(f"🔍 UserContextMiddleware processing request: {request.method} {request.url}")
        
        # Reset context for this request
        token_value = current_user_context.set(None)
        
        try:
            # Log request details for debugging
            logger.info(f"📋 Request headers: Authorization={request.headers.get('Authorization', 'None')}")
            logger.info(f"📋 Request user exists: {hasattr(request, 'user')}")
            if hasattr(request, 'user'):
                logger.info(f"📋 Request user type: {type(request.user)}")
                logger.info(f"📋 Request user value: {request.user}")
            
            # Check if MCP authentication middleware has set an authenticated user
            if hasattr(request, 'user') and isinstance(request.user, AuthenticatedUser):
                auth_user = request.user
                user_id = auth_user.access_token.client_id
                
                logger.info(f"🔑 Found authenticated user from MCP: {user_id}")
                
                # Get user context from our JWT backend
                user_context = await self.jwt_backend._get_user_context(user_id)
                
                if user_context:
                    # Store in context variable for our application code
                    current_user_context.set(user_context)
                    
                    # Add user info to request state for backward compatibility
                    request.state.user_id = user_context.user_id
                    request.state.user_email = user_context.email
                    request.state.user_roles = user_context.roles
                    request.state.user_scopes = auth_user.scopes
                    
                    # CRITICAL FIX: Also set MCP auth context for tool calls
                    # This ensures MCP tools can access the authenticated user
                    try:
                        from mcp.server.auth.context import auth_context
                        auth_context.set(auth_user)
                        logger.info(f"✅ MCP auth_context set for user {user_context.user_id}")
                    except Exception as e:
                        logger.warning(f"Could not set MCP auth_context: {e}")
                    
                    logger.info(f"🎉 User context set for user {user_context.user_id} in ContextVar")
                    logger.debug(f"Request state updated: user_id={request.state.user_id}")
                else:
                    logger.warning(f"❌ Could not get user context for user_id: {user_id}")
            else:
                logger.debug("No authenticated user found from MCP authentication")
            
            # Process the request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in UserContextMiddleware: {e}")
            import traceback
            logger.debug(f"Full error trace:\n{traceback.format_exc()}")
            # Continue without user context on error
            response = await call_next(request)
            return response
        finally:
            # Reset context after request
            current_user_context.reset(token_value)
            
            # Also reset MCP auth context
            try:
                from mcp.server.auth.context import auth_context
                auth_context.reset()
                logger.debug("🔄 MCP auth context reset after request")
            except Exception as e:
                logger.debug(f"Could not reset MCP auth_context: {e}")
            
            logger.debug("🔄 User context reset after request")


def get_current_user_context() -> Optional[MCPUserContext]:
    """
    Get the current user context from the context variable.
    
    Returns:
        Current user context or None if not authenticated
    """
    return current_user_context.get()


def get_current_user_id() -> Optional[str]:
    """
    Get the current user ID from the context.
    
    Returns:
        Current user ID or None if not authenticated
    """
    context = get_current_user_context()
    return context.user_id if context else None


def require_user_context() -> MCPUserContext:
    """
    Get the current user context, raising an error if not authenticated.
    
    Returns:
        Current user context
        
    Raises:
        RuntimeError: If no user context is available
    """
    context = get_current_user_context()
    if not context:
        raise RuntimeError("No user context available. User must be authenticated.")
    return context


def has_scope(scope: str) -> bool:
    """
    Check if the current user has a specific scope.
    
    Args:
        scope: The scope to check
        
    Returns:
        True if user has the scope, False otherwise
    """
    context = get_current_user_context()
    if not context:
        return False
    return scope in context.scopes


def has_role(role: str) -> bool:
    """
    Check if the current user has a specific role.
    
    Args:
        role: The role to check
        
    Returns:
        True if user has the role, False otherwise
    """
    context = get_current_user_context()
    if not context:
        return False
    return role in context.roles


def has_any_role(roles: list[str]) -> bool:
    """
    Check if the current user has any of the specified roles.
    
    Args:
        roles: List of roles to check
        
    Returns:
        True if user has any of the roles, False otherwise
    """
    context = get_current_user_context()
    if not context:
        return False
    return any(role in context.roles for role in roles)


def has_all_scopes(scopes: list[str]) -> bool:
    """
    Check if the current user has all of the specified scopes.
    
    Args:
        scopes: List of scopes to check
        
    Returns:
        True if user has all scopes, False otherwise
    """
    context = get_current_user_context()
    if not context:
        return False
    return all(scope in context.scopes for scope in scopes)