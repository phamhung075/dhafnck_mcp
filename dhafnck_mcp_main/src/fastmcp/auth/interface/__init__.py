"""Authentication Interface Layer"""

from .auth_endpoints import router as auth_router
from .auth_middleware import (
    AuthenticationMiddleware,
    require_auth,
    require_roles,
    get_current_user_id,
    get_current_user_email,
    get_current_user_roles,
    is_authenticated,
    has_role,
    is_admin
)

__all__ = [
    "auth_router",
    "AuthenticationMiddleware",
    "require_auth",
    "require_roles",
    "get_current_user_id",
    "get_current_user_email", 
    "get_current_user_roles",
    "is_authenticated",
    "has_role",
    "is_admin"
]