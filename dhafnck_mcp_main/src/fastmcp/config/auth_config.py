"""Authentication configuration for DhafnckMCP.

This module provides configuration options for authentication behavior,
including a temporary compatibility mode for migration from default_id.
"""

import os
import logging
from typing import Optional
from ..task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError
)

logger = logging.getLogger(__name__)

class AuthConfig:
    """Authentication configuration and compatibility settings.
    
    This class provides configuration options for authentication behavior,
    including a temporary compatibility mode that can be used during the
    migration away from default_id usage.
    """
    
    @staticmethod
    def is_default_user_allowed() -> bool:
        """
        Check if default user is allowed (for backwards compatibility).
        
        This should only be enabled in development environments during migration.
        Production should always return False.
        
        WARNING: Enabling this is a security risk and should only be done
        temporarily during migration to proper authentication.
        
        Returns:
            True if default user is allowed (ALLOW_DEFAULT_USER=true)
            False otherwise (default and recommended)
        """
        # Check environment variable first
        allowed = os.getenv('ALLOW_DEFAULT_USER', 'false').lower() in ('true', '1', 'yes', 'on')
        
        # TEMPORARY FIX: Force enable for development environment during git branch auth fix
        # This should be removed after MCP authentication is properly configured
        env_name = os.getenv('ENVIRONMENT', '').lower()
        if not allowed and env_name in ('development', 'dev'):
            allowed = True
            logger.warning(
                "🔧 TEMPORARY FIX: Forcing compatibility mode for git branch auth fix in development. "
                "This should be removed after MCP authentication is configured properly."
            )
        
        if allowed:
            logger.warning(
                "⚠️ DEFAULT USER IS ALLOWED - This is a security risk! "
                "Only use in development during migration. "
                "Set ALLOW_DEFAULT_USER=false in production."
            )
            # Log stack trace to identify where this is being called from
            import traceback
            logger.debug("Default user check called from:\n" + "".join(traceback.format_stack()))
        
        return allowed
    
    @staticmethod
    def get_fallback_user_id() -> str:
        """
        Get fallback user ID for compatibility mode.
        
        This method should only be used during migration and will be removed
        in future versions. It provides a temporary fallback when authentication
        is not available but ALLOW_DEFAULT_USER is enabled.
        
        Returns:
            A compatibility user ID if allowed
            
        Raises:
            UserAuthenticationRequiredError: If default user is not allowed
        """
        if not AuthConfig.is_default_user_allowed():
            raise UserAuthenticationRequiredError(
                "Authentication required - default user is not allowed. "
                "Set ALLOW_DEFAULT_USER=true to temporarily enable compatibility mode."
            )
        
        logger.warning(
            "⚠️ Using fallback user ID '00000000-0000-0000-0000-000000000001' - "
            "this is temporary and will be removed in future versions. "
            "Please implement proper authentication."
        )
        
        # Return a special compatibility user ID that's distinct from the old default_id
        # This makes it easier to track and migrate later
        # Using a valid UUID instead of string to satisfy PostgreSQL UUID constraints
        return "00000000-0000-0000-0000-000000000001"
    
    @staticmethod
    def should_enforce_authentication() -> bool:
        """
        Check if authentication should be strictly enforced.
        
        This is the inverse of is_default_user_allowed() for clearer intent.
        
        Returns:
            True if authentication must be enforced (recommended)
            False if compatibility mode is enabled
        """
        return not AuthConfig.is_default_user_allowed()
    
    @staticmethod
    def log_authentication_bypass(operation: str, reason: str) -> None:
        """
        Log when authentication is bypassed for monitoring.
        
        This helps track where authentication is being bypassed during migration.
        
        Args:
            operation: The operation that bypassed authentication
            reason: The reason for bypassing (e.g., "compatibility mode")
        """
        logger.warning(
            f"⚠️ Authentication bypassed for '{operation}': {reason}. "
            f"This should be fixed before production deployment."
        )
    
    @staticmethod
    def validate_migration_readiness() -> dict:
        """
        Check if the system is ready to disable compatibility mode.
        
        Returns:
            Dict with readiness status and any issues found
        """
        issues = []
        
        # Check environment variable
        if AuthConfig.is_default_user_allowed():
            issues.append("ALLOW_DEFAULT_USER is still enabled")
        
        # Check for common environment variables that might indicate production
        env = os.getenv('ENVIRONMENT', '').lower()
        if env in ('production', 'prod') and AuthConfig.is_default_user_allowed():
            issues.append("Default user is allowed in production environment!")
        
        return {
            'ready': len(issues) == 0,
            'issues': issues,
            'compatibility_mode': AuthConfig.is_default_user_allowed(),
            'environment': env or 'unknown'
        }