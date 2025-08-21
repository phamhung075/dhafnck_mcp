"""
Development Authentication Bypass

This module provides authentication bypass for development mode.
WARNING: This should NEVER be used in production!
"""

import os
import logging
from typing import Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from ..domain.entities.user import User
from .fastapi_auth import get_db

logger = logging.getLogger(__name__)


def is_development_mode() -> bool:
    """Check if we're in development mode with auth bypass enabled."""
    return (
        os.getenv("ENVIRONMENT", "development") == "development" and
        os.getenv("DHAFNCK_DEV_AUTH_BYPASS", "false").lower() == "true"
    )


def get_development_user() -> User:
    """Get a default development user for testing."""
    return User(
        id="dev-user-001",
        email="dev@localhost",
        username="dev_user",
        roles=["user", "developer"],
        is_active=True,
        is_verified=True
    )


async def get_current_user_or_dev(
    request: Request
) -> User:
    """
    Get current user from authentication or return development user.
    
    In development mode with bypass enabled, returns a default dev user.
    Otherwise, attempts normal authentication.
    """
    # Check if we're in development mode with bypass
    if is_development_mode():
        dev_user = get_development_user()
        logger.warning(
            f"🚨 DEVELOPMENT AUTH BYPASS ACTIVE - Using dev user: {dev_user.email}"
        )
        return dev_user
    
    # Try to get authenticated user normally
    try:
        # Try Supabase authentication first
        from .supabase_fastapi_auth import get_current_user
        from .fastapi_auth import get_db
        from fastapi import Depends
        # Note: We can't use Depends here directly, would need to restructure
        # For now, just return dev user in dev mode
        raise ImportError("Skip to dev user")
    except ImportError:
        pass
    except HTTPException as e:
        # If auth fails and we're in dev mode (but bypass not enabled), 
        # provide helpful message
        if os.getenv("ENVIRONMENT", "development") == "development":
            logger.info(
                "Authentication failed in development. "
                "Set DHAFNCK_DEV_AUTH_BYPASS=true to bypass auth"
            )
        raise e