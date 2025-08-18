"""
Authentication Bridge Module

Provides a bridge pattern implementation to allow both MCP's native
authentication and FastAPI's OAuth2PasswordBearer to coexist.
"""

from .auth_bridge import (
    AuthBridge,
    get_auth_bridge,
    get_current_user_from_bridge,
    get_bridged_user
)

__all__ = [
    "AuthBridge",
    "get_auth_bridge",
    "get_current_user_from_bridge",
    "get_bridged_user"
]