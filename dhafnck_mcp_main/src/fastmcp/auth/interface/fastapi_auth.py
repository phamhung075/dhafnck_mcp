"""
FastAPI OAuth2PasswordBearer Authentication

This module provides OAuth2PasswordBearer authentication for FastAPI endpoints,
replacing the custom middleware with FastAPI's built-in OAuth2 support.
"""

import logging
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..domain.services.jwt_service import JWTService
from ..domain.entities.user import User
from ..application.services.auth_service import AuthService
from ..infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# OAuth2 scheme for token-based authentication
# tokenUrl points to the login endpoint that returns tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Initialize services
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
jwt_service = JWTService(JWT_SECRET_KEY)

# Database configuration - lazy loaded
_db_config = None

def get_db_config():
    """Get database config (lazy loaded)"""
    global _db_config
    if _db_config is None:
        from ...task_management.infrastructure.database.database_config import DatabaseConfig
        _db_config = DatabaseConfig()
    return _db_config


def get_db() -> Session:
    """Get database session"""
    db_config = get_db_config()
    db = db_config.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate token and return current user
    
    This is the main dependency for protected endpoints.
    It extracts the token using OAuth2PasswordBearer and validates it.
    
    Args:
        token: JWT token extracted by OAuth2PasswordBearer
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Validate token using existing JWT service
        payload = jwt_service.verify_access_token(token)
        if not payload:
            raise credentials_exception
        
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
            
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception
    
    # Get user from database
    user_repository = UserRepository(db)
    user = user_repository.find_by_id(user_id)
    
    if not user:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    
    Ensures the user is active and not disabled.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_roles(*required_roles: str):
    """
    Factory function for role-based access control
    
    Creates a dependency that checks if the user has required roles.
    
    Args:
        required_roles: Roles required for access
        
    Returns:
        Dependency function that validates roles
        
    Example:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])
        async def admin_endpoint():
            return {"message": "Admin only"}
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """
        Check if user has required roles
        
        Args:
            current_user: Active user from dependency
            
        Returns:
            User if authorized
            
        Raises:
            HTTPException: 403 if user lacks required roles
        """
        user_roles = [r.value if hasattr(r, 'value') else str(r) for r in current_user.roles]
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


# Convenience functions for common role checks
require_admin = require_roles("admin")
require_user = require_roles("user")


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get optional current user
    
    For endpoints that work with or without authentication.
    Returns None if no valid token is provided.
    
    Args:
        token: Optional JWT token
        db: Database session
        
    Returns:
        User object or None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


# For OAuth2PasswordRequestForm compatibility
async def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Get authentication service with dependencies
    
    Args:
        db: Database session
        
    Returns:
        Configured AuthService instance
    """
    user_repository = UserRepository(db)
    return AuthService(user_repository, jwt_service)