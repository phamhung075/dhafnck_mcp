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

# Import user context from RequestContextMiddleware
# Try to import the new RequestContextMiddleware context functions
try:
    from fastmcp.auth.middleware.request_context_middleware import (
        get_current_user_id as get_user_from_request_context,
        get_current_user_email,
        get_current_auth_method,
        is_request_authenticated,
        get_authentication_context
    )
    REQUEST_CONTEXT_AVAILABLE = True
    logger.info("✅ RequestContextMiddleware context functions imported successfully")
except ImportError as e:
    logger.warning(f"RequestContextMiddleware context functions not available: {e}")
    get_user_from_request_context = lambda: None
    get_current_user_email = lambda: None
    get_current_auth_method = lambda: None
    is_request_authenticated = lambda: False
    get_authentication_context = lambda: {}
    REQUEST_CONTEXT_AVAILABLE = False

# Try to import custom user context middleware
try:
    from fastmcp.auth.middleware.user_context_middleware import get_current_user_id
    USER_CONTEXT_AVAILABLE = True
    logger.info("✅ User context middleware functions imported successfully")
except ImportError as e:
    logger.warning(f"User context middleware functions not available: {e}")
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
        
        logger.info(f"🔍 Request state check: request exists = {request is not None}")
        
        if request and hasattr(request, 'state'):
            logger.info(f"🔍 Request has state, attributes: {dir(request.state)}")
            if hasattr(request.state, 'user_id'):
                user_id = request.state.user_id
                logger.info(f"✅ Got user_id from request state: {user_id}")
                return user_id
            else:
                logger.warning("⚠️ Request state exists but no user_id attribute")
        elif request:
            logger.warning(f"⚠️ Request exists but no state. Request type: {type(request)}")
        else:
            logger.warning("❌ No current HTTP request found in ContextVar")
    except ImportError as e:
        logger.error(f"❌ Could not import _current_http_request: {e}")
    except Exception as e:
        logger.error(f"❌ Error getting user_id from request state: {e}")
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
    
    return None


def get_authenticated_user_id(provided_user_id: Optional[str] = None, operation_name: str = "Operation") -> str:
    """
    Get authenticated user ID from various sources with proper validation.
    
    This function tries to extract user_id from (in priority order):
    1. Provided user_id parameter
    2. RequestContextMiddleware context variables (NEW - set by DualAuthMiddleware)
    3. Legacy request state (old method)
    4. Custom user context middleware 
    5. MCP authentication context
    
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
    logger.info(f"🔧 REQUEST_CONTEXT_AVAILABLE: {REQUEST_CONTEXT_AVAILABLE}")
    logger.info(f"🔧 USER_CONTEXT_AVAILABLE: {USER_CONTEXT_AVAILABLE}")
    print(f"DEBUG: get_authenticated_user_id called for {operation_name} with provided_user_id={provided_user_id}")
    
    user_id = provided_user_id
    
    # If no user ID provided, try to extract from authentication context
    if user_id is None:
        logger.info("🔍 No user_id provided, trying authentication context sources...")
        
        # PRIORITY 1: Try RequestContextMiddleware context variables (NEW METHOD)
        if REQUEST_CONTEXT_AVAILABLE:
            logger.info("🆕 Trying RequestContextMiddleware context variables...")
            try:
                context_user_id = get_user_from_request_context()
                logger.info(f"🎯 RequestContextMiddleware returned: {context_user_id}")
                if context_user_id:
                    user_id = context_user_id
                    logger.info(f"✅ Got user_id from RequestContextMiddleware: {user_id}")
                    
                    # Log additional context info for debugging
                    if is_request_authenticated():
                        auth_method = get_current_auth_method()
                        logger.info(f"🔐 Authentication method: {auth_method}")
                else:
                    logger.warning("⚠️ RequestContextMiddleware returned None - request not authenticated")
            except Exception as e:
                logger.error(f"❌ Error accessing RequestContextMiddleware context: {e}")
                import traceback
                logger.debug(f"Full traceback: {traceback.format_exc()}")
        else:
            logger.warning("⚠️ RequestContextMiddleware context not available")
        
        # PRIORITY 2: Try legacy request state (set by DualAuthMiddleware)
        if user_id is None:
            logger.info("🔧 Trying legacy request state...")
            user_id = get_user_id_from_request_state()
            if user_id:
                logger.info(f"✅ Got user_id from legacy request state: {user_id}")
        
        # PRIORITY 3: Try custom user context middleware if no user_id yet
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
            if user_id is None:
                logger.warning("⚠️ User context middleware not available")
        
        # PRIORITY 4: Try MCP authentication context (gracefully handle missing module)
        if user_id is None:
            logger.info("🔧 Trying MCP authentication context...")
            try:
                # Try importing MCP auth context - this may fail if module doesn't exist
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
            except ImportError as import_e:
                logger.info(f"⚠️ MCP auth context module not available: {import_e}")
                logger.info("⚠️ This is expected if using DualAuthMiddleware instead of MCP auth system")
            except Exception as e:
                logger.info(f"⚠️ Could not access MCP auth context: {e}")
        
        # If still no user ID, throw authentication error
        if user_id is None:
            logger.error(f"❌ No authentication found for {operation_name}")
            # Log all available context for debugging
            if REQUEST_CONTEXT_AVAILABLE:
                auth_context = get_authentication_context()
                logger.error(f"❌ Full authentication context: {auth_context}")
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