"""Domain Constants for Task Management

This module defines domain-level constants and validation functions for the task management system.

MVP MODE SUPPORT: This module now supports MVP mode where authentication can be bypassed
for development and testing purposes. When MVP mode is enabled, a default user ID is used.
When MVP mode is disabled, proper user authentication is required.
"""

import os
from typing import Optional
from .exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError,
    InvalidUserIdError
)

# MVP Mode Configuration
MVP_MODE_ENABLED = os.environ.get("DHAFNCK_MVP_MODE", "false").lower() in ("true", "1", "yes", "on")
# Use a valid UUID format for MVP mode to satisfy database constraints
MVP_DEFAULT_USER_ID = "00000000-0000-0000-0000-000000012345"

# List of prohibited default user identifiers that should never be used (except in MVP mode)
PROHIBITED_DEFAULT_IDS = {
    'default_id',
    '00000000-0000-0000-0000-000000000000',
    'default',
    'default_user',
    'system',
    'anonymous',
    'unauthenticated'
}

def validate_user_id(user_id: Optional[str], operation: str = "This operation") -> str:
    """
    Validate that a user ID is provided and valid, with MVP mode support.
    
    In MVP mode: Returns a default user ID if none provided
    In auth mode: Enforces authentication requirements by ensuring:
    1. A user ID is provided (not None or empty)
    2. The user ID is not a prohibited default value
    3. The user ID is a valid non-empty string
    
    Args:
        user_id: The user ID to validate
        operation: Description of the operation requiring authentication
        
    Returns:
        The validated user ID (or MVP default user ID if in MVP mode)
        
    Raises:
        UserAuthenticationRequiredError: If user_id is None or empty (when not in MVP mode)
        DefaultUserProhibitedError: If user_id is a prohibited default value (when not in MVP mode)
        InvalidUserIdError: If user_id is invalid format
    """
    # MVP MODE: Return default user ID if none provided
    if MVP_MODE_ENABLED:
        if user_id is None or str(user_id).strip() == "":
            return MVP_DEFAULT_USER_ID
        # If user_id is provided in MVP mode, still validate it
        user_id_str = str(user_id).strip()
        return user_id_str if user_id_str else MVP_DEFAULT_USER_ID
    
    # AUTHENTICATION MODE: Enforce strict authentication
    # Check if user_id is provided
    if user_id is None:
        raise UserAuthenticationRequiredError(operation)
    
    # Convert to string and strip whitespace
    user_id_str = str(user_id).strip()
    
    # Check if empty after stripping
    if not user_id_str:
        raise UserAuthenticationRequiredError(operation)
    
    # Check for prohibited default IDs (case-insensitive)
    if user_id_str.lower() in PROHIBITED_DEFAULT_IDS:
        raise DefaultUserProhibitedError()
    
    # Additional validation for UUID format if it looks like a UUID
    if len(user_id_str) == 36 and user_id_str.count('-') == 4:
        # Check if it's the zero UUID
        if user_id_str == '00000000-0000-0000-0000-000000000000':
            raise DefaultUserProhibitedError()
    
    return user_id_str

def require_authenticated_user(user_id: Optional[str], operation: str = "This operation") -> str:
    """
    Alias for validate_user_id for clearer intent in code.
    
    Use this when you want to explicitly show that authentication is required.
    
    Args:
        user_id: The user ID to validate
        operation: Description of the operation requiring authentication
        
    Returns:
        The validated user ID
        
    Raises:
        UserAuthenticationRequiredError: If user_id is None or empty
        DefaultUserProhibitedError: If user_id is a prohibited default value
        InvalidUserIdError: If user_id is invalid format
    """
    return validate_user_id(user_id, operation)

def is_mvp_mode() -> bool:
    """
    Check if MVP mode is enabled.
    
    Returns:
        True if MVP mode is enabled, False otherwise
    """
    return MVP_MODE_ENABLED

def get_mvp_user_id() -> str:
    """
    Get the MVP default user ID.
    
    Returns:
        The MVP default user ID
    """
    return MVP_DEFAULT_USER_ID

# RESTORED FUNCTIONS FOR MVP MODE:
# These functions are now available when MVP mode is enabled
def get_default_user_id() -> Optional[str]:
    """Get default user ID if in MVP mode, None otherwise."""
    return MVP_DEFAULT_USER_ID if MVP_MODE_ENABLED else None

# REMOVED FUNCTIONS (for documentation purposes):
# - is_default_user(): No longer needed - default users are prohibited in auth mode
# - normalize_user_id(): No longer needed - no normalization to defaults in auth mode
# - DEFAULT_USER_UUID: Now available as MVP_DEFAULT_USER_ID in MVP mode
# - DEFAULT_USER_UUID_STR: Now available as MVP_DEFAULT_USER_ID in MVP mode
# - LEGACY_DEFAULT_USER_ID: No legacy support for defaults in auth mode