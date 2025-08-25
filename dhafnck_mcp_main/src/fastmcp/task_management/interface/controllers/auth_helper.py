"""Authentication Helper for MCP Controllers

This module provides common authentication functionality for all MCP controllers
to extract user_id from JWT tokens and various authentication contexts.
"""

import os
import logging
from typing import Optional

from ...domain.constants import validate_user_id
from ...domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError
from ....config.auth_config import AuthConfig

logger = logging.getLogger(__name__)

# Try to import user context utilities - gracefully handle if not available
try:
    from fastmcp.auth.mcp_integration.user_context_middleware import get_current_user_id
    USER_CONTEXT_AVAILABLE = True
except ImportError:
    logger.warning("User context middleware not available - using fallback user ID extraction")
    get_current_user_id = lambda: None
    USER_CONTEXT_AVAILABLE = False

# Try to import Starlette request context for dual auth
try:
    from starlette.requests import Request
    from starlette.middleware.base import RequestCycle
    STARLETTE_AVAILABLE = True
except ImportError:
    logger.debug("Starlette not available - request state not accessible")
    STARLETTE_AVAILABLE = False


def get_user_id_from_request_state() -> Optional[str]:
    """
    Try to get user_id from the current request state (set by DualAuthMiddleware).
    
    Returns:
        User ID from request state or None
    """
    try:
        # Try to get the current request from context
        from fastmcp.server.http_server import _current_http_request
        request = _current_http_request.get()
        
        if request and hasattr(request, 'state') and hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
            logger.debug(f"Got user_id from request state: {user_id}")
            return user_id
        elif request:
            logger.debug(f"Request found but no user_id in state. State attributes: {dir(request.state) if hasattr(request, 'state') else 'No state'}")
        else:
            logger.debug("No current HTTP request found in context")
    except ImportError as e:
        logger.debug(f"Could not import _current_http_request: {e}")
    except Exception as e:
        logger.debug(f"Could not get user_id from request state: {e}")
    
    return None


def get_authenticated_user_id(provided_user_id: Optional[str] = None, operation_name: str = "Operation") -> str:
    """
    Get authenticated user ID from various sources with proper validation.
    
    This function tries to extract user_id from:
    1. Provided user_id parameter
    2. Custom user context middleware 
    3. MCP authentication context
    4. Compatibility mode (if enabled)
    
    Args:
        provided_user_id: User ID provided explicitly (takes precedence)
        operation_name: Name of the operation for error messages
        
    Returns:
        Validated user ID string
        
    Raises:
        UserAuthenticationRequiredError: If no valid authentication is found
        DefaultUserProhibitedError: If prohibited user ID is used
        InvalidUserIdError: If user ID format is invalid
    """
    logger.info(f"🔍 get_authenticated_user_id called for operation: {operation_name}")
    logger.info(f"📝 Provided user_id: {provided_user_id}")
    logger.info(f"🔧 USER_CONTEXT_AVAILABLE: {USER_CONTEXT_AVAILABLE}")
    print(f"DEBUG: get_authenticated_user_id called for {operation_name} with provided_user_id={provided_user_id}")
    
    user_id = provided_user_id
    
    # If no user ID provided, try to extract from authentication context
    if user_id is None:
        logger.info("🔍 No user_id provided, trying authentication context sources...")
        
        # Try request state first (set by DualAuthMiddleware)
        user_id = get_user_id_from_request_state()
        if user_id:
            logger.info(f"✅ Got user_id from request state (DualAuthMiddleware): {user_id}")
        
        # Try custom user context middleware if no user_id yet
        if user_id is None and USER_CONTEXT_AVAILABLE:
            logger.info("🔧 Trying custom user context middleware...")
            try:
                context_user_id = get_current_user_id()
                logger.info(f"🎯 Custom context middleware returned: {context_user_id}")
                if context_user_id:
                    user_id = context_user_id
                    logger.info(f"✅ Got user_id from custom context middleware: {user_id}")
                else:
                    logger.warning("⚠️ Custom context middleware returned None")
            except Exception as e:
                logger.error(f"❌ Error calling get_current_user_id(): {e}")
                import traceback
                logger.debug(f"Full traceback: {traceback.format_exc()}")
        else:
            logger.warning("⚠️ User context middleware not available")
        
        # Try MCP authentication context
        if user_id is None:
            logger.info("🔧 Trying MCP authentication context...")
            try:
                from mcp.server.auth.context import auth_context
                from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
                
                mcp_auth_context = auth_context.get()
                logger.info(f"🎯 MCP auth context type: {type(mcp_auth_context)}")
                
                if isinstance(mcp_auth_context, AuthenticatedUser):
                    # We have an AuthenticatedUser from MCP
                    if hasattr(mcp_auth_context, 'access_token') and mcp_auth_context.access_token:
                        user_id = mcp_auth_context.access_token.client_id
                        logger.info(f"✅ Got user_id from MCP AuthenticatedUser.access_token: {user_id}")
                    elif hasattr(mcp_auth_context, 'identity'):
                        user_id = mcp_auth_context.identity
                        logger.info(f"✅ Got user_id from MCP AuthenticatedUser.identity: {user_id}")
                elif mcp_auth_context and hasattr(mcp_auth_context, 'user_id'):
                    user_id = mcp_auth_context.user_id
                    logger.info(f"✅ Got user_id from MCP auth context: {user_id}")
                elif mcp_auth_context and hasattr(mcp_auth_context, 'client_id'):
                    user_id = mcp_auth_context.client_id
                    logger.info(f"✅ Got user_id from MCP auth client_id: {user_id}")
                elif mcp_auth_context:
                    logger.warning(f"⚠️ MCP auth context available but no user_id/client_id: {dir(mcp_auth_context)}")
                else:
                    logger.warning("⚠️ No MCP auth context available")
            except Exception as e:
                logger.info(f"⚠️ Could not access MCP auth context: {e}")
        
        # If still no user ID, throw authentication error
        if user_id is None:
            logger.error(f"❌ No authentication found for {operation_name}")
            raise UserAuthenticationRequiredError(operation_name)
    else:
        logger.info(f"✅ Using provided user_id: {user_id}")
    
    # Validate the user ID (will throw if invalid)
    logger.info(f"🔍 Validating user_id: {user_id}")
    user_id = validate_user_id(user_id, operation_name)
    logger.info(f"✅ Final validated user_id: {user_id}")
    
    return user_id


def log_authentication_details():
    """
    Log current authentication state for debugging purposes.
    """
    try:
        # Check custom context
        if USER_CONTEXT_AVAILABLE:
            context_user_id = get_current_user_id()
            logger.debug(f"Custom context user_id: {context_user_id}")
        
        # Check MCP context
        try:
            from mcp.server.auth.context import auth_context
            mcp_auth_context = auth_context.get()
            if mcp_auth_context:
                logger.debug(f"MCP auth context type: {type(mcp_auth_context)}")
                logger.debug(f"MCP auth context attributes: {dir(mcp_auth_context)}")
                if hasattr(mcp_auth_context, 'user_id'):
                    logger.debug(f"MCP user_id: {mcp_auth_context.user_id}")
                if hasattr(mcp_auth_context, 'client_id'):
                    logger.debug(f"MCP client_id: {mcp_auth_context.client_id}")
            else:
                logger.debug("No MCP auth context available")
        except Exception as e:
            logger.debug(f"Error accessing MCP auth context: {e}")
        
        # Authentication is always required
        logger.debug("Authentication is always strictly enforced")
        
    except Exception as e:
        logger.error(f"Error logging authentication details: {e}")