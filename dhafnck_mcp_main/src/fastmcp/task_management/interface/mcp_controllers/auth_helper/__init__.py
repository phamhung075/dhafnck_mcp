"""Authentication Helper Module - Modular Architecture"""

from .auth_helper import (
    get_authenticated_user_id,
    get_user_id_from_request_state,
    log_authentication_details,
    _extract_user_id_from_context_object,
    REQUEST_CONTEXT_AVAILABLE,
    USER_CONTEXT_AVAILABLE,
    STARLETTE_AVAILABLE,
    get_user_from_request_context,
    get_current_user_email,
    get_current_auth_method,
    is_request_authenticated,
    get_authentication_context,
    get_current_user_id
)

__all__ = [
    'get_authenticated_user_id',
    'get_user_id_from_request_state',
    'log_authentication_details',
    '_extract_user_id_from_context_object',
    'REQUEST_CONTEXT_AVAILABLE',
    'USER_CONTEXT_AVAILABLE',
    'STARLETTE_AVAILABLE',
    'get_user_from_request_context',
    'get_current_user_email',
    'get_current_auth_method',
    'is_request_authenticated',
    'get_authentication_context',
    'get_current_user_id'
]