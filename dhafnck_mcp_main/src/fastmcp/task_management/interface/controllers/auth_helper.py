"""Authentication Helper for MCP Controllers

This module provides common authentication functionality for all MCP controllers
to extract user_id from JWT tokens and various authentication contexts.
"""

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
    
    user_id = provided_user_id
    
    # If no user ID provided, try to extract from authentication context
    if user_id is None:
        logger.info("🔍 No user_id provided, trying authentication context sources...")
        
        # Try custom user context middleware first
        if USER_CONTEXT_AVAILABLE:
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
                mcp_auth_context = auth_context.get()
                logger.info(f"🎯 MCP auth context: {mcp_auth_context}")
                if mcp_auth_context and hasattr(mcp_auth_context, 'user_id'):
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
        
        # If still no user ID, check compatibility mode
        if user_id is None:
            logger.info("🔧 Checking compatibility mode...")
            if AuthConfig.is_default_user_allowed():
                user_id = AuthConfig.get_fallback_user_id()
                logger.info(f"✅ Using compatibility mode user_id: {user_id}")
                AuthConfig.log_authentication_bypass(operation_name, "compatibility mode")
            else:
                logger.error(f"❌ No authentication found and compatibility mode disabled for {operation_name}")
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
        
        # Check compatibility mode
        logger.debug(f"Compatibility mode enabled: {AuthConfig.is_default_user_allowed()}")
        
    except Exception as e:
        logger.error(f"Error logging authentication details: {e}")