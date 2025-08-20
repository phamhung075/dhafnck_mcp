"""Domain Constants for Task Management

This module defines domain-level constants used throughout the task management system.
"""

from uuid import UUID

# Default user UUID for unauthenticated or system operations
# Using a special UUID that's recognizable as the default user
DEFAULT_USER_UUID = UUID("00000000-0000-0000-0000-000000000000")
DEFAULT_USER_UUID_STR = str(DEFAULT_USER_UUID)

# Legacy default user ID for backward compatibility
LEGACY_DEFAULT_USER_ID = "default_id"

def get_default_user_id() -> str:
    """Get the default user ID to use for unauthenticated operations.
    
    Returns:
        The default user UUID as a string
    """
    return DEFAULT_USER_UUID_STR

def is_default_user(user_id: str) -> bool:
    """Check if a user ID represents the default/unauthenticated user.
    
    Args:
        user_id: The user ID to check
        
    Returns:
        True if this is a default user ID
    """
    return user_id in (DEFAULT_USER_UUID_STR, LEGACY_DEFAULT_USER_ID, "default_id")

def normalize_user_id(user_id: str) -> str:
    """Normalize a user ID to ensure consistency.
    
    Converts legacy default IDs to the standard UUID format.
    
    Args:
        user_id: The user ID to normalize
        
    Returns:
        Normalized user ID (UUID string format)
    """
    if is_default_user(user_id):
        return DEFAULT_USER_UUID_STR
    return user_id