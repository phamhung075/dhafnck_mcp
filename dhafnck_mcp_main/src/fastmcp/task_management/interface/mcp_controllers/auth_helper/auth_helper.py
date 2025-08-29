"""Authentication Helper for MCP Controllers

This module provides common authentication functionality for all MCP controllers
to extract user_id from JWT tokens and various authentication contexts.
"""

import os
import logging
from typing import Optional

from .services import AuthenticationService, ContextImportService, DebugService
from .extractors import RequestStateExtractor, ContextObjectExtractor

logger = logging.getLogger(__name__)

# Create singleton instances for backward compatibility
_auth_service = None
_context_service = None
_debug_service = None

def _get_auth_service():
    """Get or create authentication service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service

def _get_context_service():
    """Get or create context import service singleton"""
    global _context_service
    if _context_service is None:
        _context_service = ContextImportService()
    return _context_service

def _get_debug_service():
    """Get or create debug service singleton"""
    global _debug_service
    if _debug_service is None:
        _debug_service = DebugService(_get_context_service())
    return _debug_service

# Backward compatibility exports
REQUEST_CONTEXT_AVAILABLE = property(lambda self: _get_context_service().request_context_available)
USER_CONTEXT_AVAILABLE = property(lambda self: _get_context_service().user_context_available)
STARLETTE_AVAILABLE = property(lambda self: _get_context_service().starlette_available)

# Create module-level variables for backward compatibility
def _update_globals():
    """Update global variables based on context service state"""
    ctx = _get_context_service()
    globals()['REQUEST_CONTEXT_AVAILABLE'] = ctx.request_context_available
    globals()['USER_CONTEXT_AVAILABLE'] = ctx.user_context_available
    globals()['STARLETTE_AVAILABLE'] = ctx.starlette_available
    globals()['get_user_from_request_context'] = ctx.get_user_from_request_context
    globals()['get_current_user_email'] = ctx.get_current_user_email
    globals()['get_current_auth_method'] = ctx.get_current_auth_method
    globals()['is_request_authenticated'] = ctx.is_request_authenticated
    globals()['get_authentication_context'] = ctx.get_authentication_context
    globals()['get_current_user_id'] = ctx.get_current_user_id

# Initialize on module load
_update_globals()

# Backward compatibility functions
def get_user_id_from_request_state() -> Optional[str]:
    """
    Try to get user_id from the current request state (set by DualAuthMiddleware).
    
    Returns:
        User ID from request state or None
    """
    return RequestStateExtractor.extract_user_id()

def _extract_user_id_from_context_object(context_obj) -> Optional[str]:
    """
    Extract user_id string from various context object types.
    
    Args:
        context_obj: Context object that might contain user_id
        
    Returns:
        User ID string or None if extraction fails
    """
    return ContextObjectExtractor.extract_user_id(context_obj)

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
    return _get_auth_service().get_authenticated_user_id(provided_user_id, operation_name)

def log_authentication_details(user_id=None, operation=None):
    """
    Log current authentication state for debugging purposes.
    
    Args:
        user_id: Optional user ID for context
        operation: Optional operation name for context
    """
    _get_debug_service().log_authentication_details(user_id, operation)