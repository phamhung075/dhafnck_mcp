"""
Dual Authentication Middleware

This middleware handles two types of authentication:
1. Frontend requests (API V2) - Uses Supabase cookies
2. MCP requests - Uses generated tokens from frontend

The middleware automatically detects the request type and applies
the appropriate authentication method.
"""

import logging
import json
from typing import Optional, Dict, Any, Union
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

from ..infrastructure.supabase_auth import SupabaseAuthService
from ..token_validator import TokenValidator, TokenValidationError, RateLimitError
from ..supabase_client import TokenInfo

logger = logging.getLogger(__name__)


class DualAuthMiddleware(BaseHTTPMiddleware):
    """
    Dual authentication middleware that handles both Supabase cookies
    for frontend requests and generated tokens for MCP requests.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.supabase_auth = SupabaseAuthService()
        self.token_validator = TokenValidator()
        logger.info("Dual authentication middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and apply appropriate authentication.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Detect request type
        request_type = self._detect_request_type(request)
        
        # Add debug logging
        logger.debug(f"🔍 DUAL AUTH: Request type detected: {request_type}")
        logger.debug(f"🔍 DUAL AUTH: Path: {request.url.path}")
        logger.debug(f"🔍 DUAL AUTH: Method: {request.method}")
        
        # Skip authentication for certain paths
        if self._should_skip_auth(request):
            logger.debug("🔍 DUAL AUTH: Skipping authentication for this path")
            return await call_next(request)
        
        try:
            # Apply appropriate authentication
            auth_result = await self._authenticate_request(request, request_type)
            
            if auth_result:
                # Add authentication info to request state
                request.state.user_id = auth_result.get('user_id')
                request.state.auth_type = request_type
                request.state.auth_info = auth_result
                
                logger.debug(f"✅ DUAL AUTH: Authenticated user {auth_result.get('user_id')} via {request_type}")
            else:
                logger.debug("🔍 DUAL AUTH: No authentication required or MVP mode")
            
            # Continue to next middleware
            response = await call_next(request)
            return response
            
        except (TokenValidationError, RateLimitError) as e:
            logger.warning(f"❌ DUAL AUTH: Authentication failed for {request_type}: {e}")
            return self._create_auth_error_response(request_type, str(e))
        except Exception as e:
            logger.error(f"❌ DUAL AUTH: Unexpected error: {e}")
            return self._create_auth_error_response(request_type, "Authentication system error")
    
    def _detect_request_type(self, request: Request) -> str:
        """
        Detect whether this is a frontend or MCP request.
        
        Args:
            request: HTTP request
            
        Returns:
            Request type: 'frontend', 'mcp', or 'unknown'
        """
        path = request.url.path
        content_type = request.headers.get('content-type', '').lower()
        user_agent = request.headers.get('user-agent', '').lower()
        
        # MCP requests characteristics
        if path.startswith('/mcp'):
            return 'mcp'
        
        # Check for MCP protocol headers
        if 'mcp-protocol-version' in request.headers:
            return 'mcp'
        
        # Check for JSON-RPC content (MCP uses JSON-RPC)
        if 'application/json' in content_type and 'jsonrpc' in str(request.headers.get('accept', '')):
            return 'mcp'
        
        # Frontend API requests
        if path.startswith('/api/v2/'):
            return 'frontend'
        
        # Check user agent for browser-like requests
        browser_indicators = ['mozilla', 'chrome', 'safari', 'firefox', 'edge']
        if any(indicator in user_agent for indicator in browser_indicators):
            return 'frontend'
        
        # Default to frontend for HTTP API requests
        if path.startswith('/api/'):
            return 'frontend'
        
        return 'unknown'
    
    def _should_skip_auth(self, request: Request) -> bool:
        """
        Check if authentication should be skipped for this request.
        
        Args:
            request: HTTP request
            
        Returns:
            True if authentication should be skipped
        """
        skip_paths = [
            '/health',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/favicon.ico',
            '/static/',
        ]
        
        path = request.url.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _authenticate_request(self, request: Request, request_type: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate request based on its type.
        
        Args:
            request: HTTP request
            request_type: Type of request ('frontend' or 'mcp')
            
        Returns:
            Authentication result or None
        """
        if request_type == 'frontend':
            return await self._authenticate_frontend_request(request)
        elif request_type == 'mcp':
            return await self._authenticate_mcp_request(request)
        else:
            # Unknown request type - try both methods
            logger.debug("🔍 DUAL AUTH: Unknown request type, trying both auth methods")
            
            # Try MCP first (Bearer token)
            try:
                result = await self._authenticate_mcp_request(request)
                if result:
                    return result
            except:
                pass
            
            # Try frontend (cookies)
            try:
                return await self._authenticate_frontend_request(request)
            except:
                pass
            
            return None
    
    async def _authenticate_frontend_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate frontend request using Supabase cookies or Bearer token.
        
        Args:
            request: HTTP request
            
        Returns:
            Authentication result
        """
        # Try Bearer token first (for API calls)
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
            logger.debug("🔍 FRONTEND AUTH: Using Bearer token")
            
            try:
                result = await self.supabase_auth.verify_token(token)
                if result.success and result.user:
                    user_id = result.user.id if hasattr(result.user, 'id') else result.user.get('id')
                    email = result.user.email if hasattr(result.user, 'email') else result.user.get('email')
                    
                    return {
                        'user_id': user_id,
                        'email': email,
                        'auth_method': 'supabase_bearer',
                        'user_data': result.user
                    }
            except Exception as e:
                logger.debug(f"🔍 FRONTEND AUTH: Bearer token failed: {e}")
        
        # Try cookies (for browser requests)
        cookies = request.cookies
        access_token = cookies.get('access_token')
        
        if access_token:
            logger.debug("🔍 FRONTEND AUTH: Using access_token cookie")
            
            try:
                result = await self.supabase_auth.verify_token(access_token)
                if result.success and result.user:
                    user_id = result.user.id if hasattr(result.user, 'id') else result.user.get('id')
                    email = result.user.email if hasattr(result.user, 'email') else result.user.get('email')
                    
                    return {
                        'user_id': user_id,
                        'email': email,
                        'auth_method': 'supabase_cookie',
                        'user_data': result.user
                    }
            except Exception as e:
                logger.debug(f"🔍 FRONTEND AUTH: Cookie authentication failed: {e}")
        
        # No valid authentication found
        logger.debug("🔍 FRONTEND AUTH: No valid authentication found")
        return None
    
    async def _authenticate_mcp_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate MCP request using generated tokens.
        
        Args:
            request: HTTP request
            
        Returns:
            Authentication result
        """
        # Extract token from various sources
        token = None
        
        # Check Authorization header
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        elif auth_header.startswith('Token '):
            token = auth_header[6:].strip()
        
        # Check custom headers
        if not token:
            token = request.headers.get('x-mcp-token') or request.headers.get('mcp-token')
        
        # Check query parameters (less secure, only for testing)
        if not token and 'token' in request.query_params:
            token = request.query_params['token']
            logger.warning("🔍 MCP AUTH: Using token from query parameter (insecure)")
        
        if not token:
            logger.debug("🔍 MCP AUTH: No token found in MCP request")
            return None
        
        logger.debug(f"🔍 MCP AUTH: Validating MCP token (first 20 chars): {token[:20]}...")
        
        # Special handling for JWT tokens (local development)
        if token.startswith('eyJ'):  # JWT tokens start with this
            logger.info("🔍 MCP AUTH: Detected JWT token, trying dual secret validation")
            
            # Try both JWT secrets to handle the mismatch between frontend and backend
            import os
            from ..domain.services.jwt_service import JWTService
            
            # Get both potential secrets
            jwt_secret = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
            supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
            
            # List of secrets to try (prioritize SUPABASE_JWT_SECRET since frontend uses it)
            secrets_to_try = []
            if supabase_jwt_secret:
                secrets_to_try.append(("SUPABASE_JWT_SECRET", supabase_jwt_secret))
            if jwt_secret and jwt_secret != "default-secret-key-change-in-production":
                secrets_to_try.append(("JWT_SECRET_KEY", jwt_secret))
            
            # Try each secret until one works
            for secret_name, secret_value in secrets_to_try:
                try:
                    logger.debug(f"🔍 MCP AUTH: Trying JWT validation with {secret_name} (length: {len(secret_value)})")
                    jwt_service = JWTService(secret_key=secret_value)
                    
                    # Try multiple token types for compatibility
                    payload = None
                    for token_type in ["api_token", "access"]:
                        try:
                            payload = jwt_service.verify_token(token, expected_type=token_type)
                            if payload:
                                logger.info(f"✅ MCP AUTH: JWT token validated with {secret_name} as {token_type} type")
                                break
                        except Exception as type_error:
                            logger.debug(f"🔍 MCP AUTH: Token type {token_type} failed with {secret_name}: {type_error}")
                            continue
                    
                    if payload:
                        # Extract user_id from either 'user_id' or 'sub' fields
                        user_id = payload.get('user_id') or payload.get('sub')
                        return {
                            'user_id': user_id,
                            'auth_method': 'local_jwt',
                            'jwt_secret_used': secret_name,
                            'token_id': payload.get('token_id') or payload.get('jti'),
                            'scopes': payload.get('scopes', []),
                            'type': payload.get('type', 'api_token'),
                            'email': payload.get('email'),
                            'roles': payload.get('roles', [])
                        }
                        
                except Exception as jwt_error:
                    logger.debug(f"🔍 MCP AUTH: JWT validation with {secret_name} failed: {jwt_error}")
                    continue
            
            logger.warning("🔍 MCP AUTH: All JWT secret validation attempts failed, will try other methods")
            # Fall through to try other validation methods
        
        try:
            # Validate token using TokenValidator (for Supabase tokens)
            client_info = {
                'user_agent': request.headers.get('user-agent', ''),
                'path': request.url.path,
                'method': request.method
            }
            
            token_info = await self.token_validator.validate_token(token, client_info)
            
            return {
                'user_id': token_info.user_id,
                'auth_method': 'mcp_token',
                'token_info': token_info,
                'created_at': token_info.created_at.isoformat() if token_info.created_at else None,
                'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None
            }
            
        except Exception as e:
            logger.debug(f"🔍 MCP AUTH: Token validation failed: {e}")
            raise
    
    def _create_auth_error_response(self, request_type: str, error_message: str) -> Response:
        """
        Create appropriate error response based on request type.
        
        Args:
            request_type: Type of request
            error_message: Error message
            
        Returns:
            Error response
        """
        if request_type == 'mcp':
            # MCP JSON-RPC error response
            error_data = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,  # Custom auth error code
                    "message": "Authentication failed",
                    "data": {
                        "detail": error_message,
                        "auth_type": "mcp_token_required"
                    }
                },
                "id": None
            }
            return JSONResponse(
                content=error_data,
                status_code=401,
                headers={"Content-Type": "application/json"}
            )
        else:
            # Standard HTTP error response for frontend
            return JSONResponse(
                content={
                    "detail": error_message,
                    "auth_type": "bearer_or_cookie_required"
                },
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"}
            )


def create_dual_auth_middleware():
    """
    Factory function to create dual authentication middleware.
    
    Returns:
        Configured middleware class
    """
    return DualAuthMiddleware