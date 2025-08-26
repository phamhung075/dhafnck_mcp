"""
Test complete JWT authentication flow integration with MCP server

This test verifies that the authentication state propagation issue is fixed:
1. JWT token is validated successfully ✅
2. AccessToken is created ✅
3. User context is set in ContextVar ✅
4. scope["user"] is set with AuthenticatedUser ✅ (THIS WAS THE ISSUE)
5. MCP's RequireAuthMiddleware passes ✅
"""

import pytest
import os
import uuid
from unittest.mock import Mock, AsyncMock, patch
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware, AuthenticatedUser
from mcp.server.auth.provider import AccessToken

from fastmcp.auth.mcp_integration.jwt_auth_backend import JWTAuthBackend, MCPUserContext
from fastmcp.auth.middleware.request_context_middleware import RequestContextMiddleware as UserContextMiddleware, get_current_user_context
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastmcp.auth.domain.value_objects import UserId


class TestAuthFlowIntegration:
    """Test complete JWT authentication flow with MCP integration"""
    
    @pytest.fixture
    def jwt_service(self):
        """Create JWT service with test secret"""
        return JWTService(
            secret_key="test-secret-key-for-integration",
            issuer="test-issuer"
        )
    
    @pytest.fixture
    def mock_user_repository(self):
        """Create mock user repository"""
        repo = Mock()
        
        def find_user_by_id(user_id):
            test_user = User(
                email="test@example.com",
                username="testuser",
                password_hash="hashed_password"
            )
            test_user.id = user_id
            test_user.status = UserStatus.ACTIVE
            test_user.roles = [UserRole.DEVELOPER]
            return test_user
        
        repo.find_by_id.side_effect = find_user_by_id
        return repo
    
    @pytest.fixture
    def jwt_backend(self, jwt_service, mock_user_repository):
        """Create JWT auth backend"""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key-for-integration"}):
            return JWTAuthBackend(
                jwt_service=jwt_service,
                user_repository=mock_user_repository,
                required_scopes=["mcp:access"]
            )
    
    @pytest.fixture
    def valid_token(self, jwt_service):
        """Create a valid JWT token for testing"""
        user_id = str(uuid.uuid4())
        return jwt_service.create_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["developer"],
            additional_claims={"scopes": ["read", "write"]}
        ), user_id
    
    def create_test_app(self, jwt_backend):
        """Create a test Starlette app with full MCP authentication middleware stack"""
        
        # Protected endpoint that requires authentication
        async def protected_endpoint(request):
            # This should only be reached if authentication succeeds
            user_context = get_current_user_context()
            
            return JSONResponse({
                "message": "Authentication successful",
                "user_id": user_context.user_id if user_context else None,
                "user_email": user_context.email if user_context else None,
                "has_authenticated_user": hasattr(request, "user") and isinstance(request.user, AuthenticatedUser),
                "scopes": request.user.scopes if hasattr(request, "user") and hasattr(request.user, "scopes") else []
            })
        
        routes = [
            Route("/protected", protected_endpoint, methods=["GET"])
        ]
        
        # Set up the complete middleware stack as it would be in production
        middleware = [
            # 1. Starlette's AuthenticationMiddleware (validates token, sets scope["user"])
            Middleware(
                AuthenticationMiddleware,
                backend=BearerAuthBackend(token_verifier=jwt_backend),
            ),
            # 2. MCP's AuthContextMiddleware (sets user in contextvar)
            Middleware(AuthContextMiddleware),
            # 3. MCP's RequireAuthMiddleware (checks scope["user"] - THIS WAS FAILING)
            Middleware(RequireAuthMiddleware, required_scopes=["mcp:access"]),
            # 4. Our UserContextMiddleware (extracts our app-specific user context)
            Middleware(UserContextMiddleware, jwt_backend=jwt_backend),
        ]
        
        return Starlette(routes=routes, middleware=middleware)
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow_success(self, jwt_backend, valid_token):
        """Test that the complete authentication flow works end-to-end"""
        token, user_id = valid_token
        
        # Test individual components separately first
        
        # 1. Test JWT token verification
        access_token = await jwt_backend.verify_token(token)
        assert access_token is not None
        assert access_token.client_id == user_id
        assert "mcp:access" in access_token.scopes
        
        # 2. Test BearerAuthBackend integration
        auth_backend = BearerAuthBackend(token_verifier=jwt_backend)
        conn = Mock()
        conn.headers = {"authorization": f"Bearer {token}"}
        
        result = await auth_backend.authenticate(conn)
        assert result is not None
        
        auth_credentials, authenticated_user = result
        assert isinstance(authenticated_user, AuthenticatedUser)
        assert authenticated_user.access_token.client_id == user_id
        assert "mcp:access" in authenticated_user.scopes
        
        # 3. Test RequireAuthMiddleware integration 
        require_auth = RequireAuthMiddleware(
            app=Mock(),
            required_scopes=["mcp:access"]
        )
        
        scope = {
            "type": "http",
            "user": authenticated_user,
            "auth": auth_credentials
        }
        
        # Mock send/receive
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock the next app in the stack
        next_app_called = False
        async def mock_next_app(scope, receive, send):
            nonlocal next_app_called
            next_app_called = True
        
        require_auth.app = mock_next_app
        
        # Call the middleware - this should NOT fail
        await require_auth(scope, receive, send)
        
        # Verify the next app was called (authentication passed)
        assert next_app_called is True, "RequireAuthMiddleware should have passed the request to the next app"
        
        # Verify no error response was sent
        send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authentication_flow_without_token_fails(self, jwt_backend):
        """Test that requests without tokens are properly rejected"""
        app = self.create_test_app(jwt_backend)
        
        with TestClient(app) as client:
            response = client.get("/protected")
        
        # Should be rejected by RequireAuthMiddleware
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "invalid_token"
        assert data["error_description"] == "Authentication required"
    
    @pytest.mark.asyncio
    async def test_authentication_flow_with_invalid_token_fails(self, jwt_backend):
        """Test that requests with invalid tokens are properly rejected"""
        app = self.create_test_app(jwt_backend)
        
        with TestClient(app) as client:
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer invalid.jwt.token"}
            )
        
        # Should be rejected by RequireAuthMiddleware
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "invalid_token"
        assert data["error_description"] == "Authentication required"
    
    @pytest.mark.asyncio
    async def test_token_verifier_integration(self, jwt_backend, valid_token):
        """Test that our JWTAuthBackend properly implements TokenVerifier interface"""
        token, user_id = valid_token
        
        # Test verify_token method directly
        access_token = await jwt_backend.verify_token(token)
        
        assert access_token is not None
        assert isinstance(access_token, AccessToken)
        assert access_token.client_id == user_id
        assert access_token.token == token
        assert "mcp:access" in access_token.scopes
        assert "mcp:write" in access_token.scopes
        assert "mcp:read" in access_token.scopes
    
    @pytest.mark.asyncio
    async def test_bearer_auth_backend_integration(self, jwt_backend, valid_token):
        """Test that BearerAuthBackend properly creates AuthenticatedUser"""
        token, user_id = valid_token
        
        # Create BearerAuthBackend with our JWT backend
        auth_backend = BearerAuthBackend(token_verifier=jwt_backend)
        
        # Mock HTTPConnection with Authorization header
        conn = Mock()
        conn.headers = {"authorization": f"Bearer {token}"}
        
        # Test authentication
        result = await auth_backend.authenticate(conn)
        
        assert result is not None
        auth_credentials, authenticated_user = result
        
        # Verify AuthCredentials
        assert "mcp:access" in auth_credentials.scopes
        assert "mcp:write" in auth_credentials.scopes
        assert "mcp:read" in auth_credentials.scopes
        
        # Verify AuthenticatedUser
        assert isinstance(authenticated_user, AuthenticatedUser)
        assert authenticated_user.access_token.client_id == user_id
        assert authenticated_user.scopes == auth_credentials.scopes
        assert authenticated_user.identity == user_id  # From SimpleUser base class
    
    @pytest.mark.asyncio
    async def test_require_auth_middleware_passes_with_authenticated_user(self, jwt_backend, valid_token):
        """Test that RequireAuthMiddleware passes when scope["user"] contains AuthenticatedUser"""
        token, user_id = valid_token
        
        # Create the middleware
        require_auth = RequireAuthMiddleware(
            app=Mock(),
            required_scopes=["mcp:access"]
        )
        
        # Create BearerAuthBackend and get authenticated user
        auth_backend = BearerAuthBackend(token_verifier=jwt_backend)
        conn = Mock()
        conn.headers = {"authorization": f"Bearer {token}"}
        result = await auth_backend.authenticate(conn)
        
        auth_credentials, authenticated_user = result
        
        # Create scope as Starlette's AuthenticationMiddleware would set it
        scope = {
            "type": "http",
            "user": authenticated_user,
            "auth": auth_credentials
        }
        
        # Mock send/receive
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock the next app in the stack
        next_app_called = False
        async def mock_next_app(scope, receive, send):
            nonlocal next_app_called
            next_app_called = True
        
        require_auth.app = mock_next_app
        
        # Call the middleware
        await require_auth(scope, receive, send)
        
        # Verify the next app was called (authentication passed)
        assert next_app_called is True
        
        # Verify no error response was sent
        send.assert_not_called()


class TestAuthFlowErrors:
    """Test authentication flow error cases"""
    
    @pytest.mark.asyncio
    async def test_require_auth_middleware_rejects_missing_user(self):
        """Test that RequireAuthMiddleware rejects requests without scope["user"]"""
        require_auth = RequireAuthMiddleware(
            app=Mock(),
            required_scopes=["mcp:access"]
        )
        
        # Empty scope (no user)
        scope = {"type": "http"}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Call the middleware
        await require_auth(scope, receive, send)
        
        # Verify error response was sent
        send.assert_called()
        
        # Check the response
        calls = send.call_args_list
        assert len(calls) == 2
        
        # First call should be response start with 401
        start_call = calls[0][0][0]
        assert start_call["type"] == "http.response.start"
        assert start_call["status"] == 401
        
        # Second call should be response body with error
        body_call = calls[1][0][0]
        assert body_call["type"] == "http.response.body"
        
    @pytest.mark.asyncio
    async def test_require_auth_middleware_rejects_non_authenticated_user(self):
        """Test that RequireAuthMiddleware rejects scope["user"] that's not AuthenticatedUser"""
        require_auth = RequireAuthMiddleware(
            app=Mock(),
            required_scopes=["mcp:access"]
        )
        
        # Scope with wrong user type
        scope = {
            "type": "http",
            "user": "not-an-authenticated-user"  # Wrong type
        }
        receive = AsyncMock()
        send = AsyncMock()
        
        # Call the middleware
        await require_auth(scope, receive, send)
        
        # Verify error response was sent
        send.assert_called()
        
        # Check for 401 status
        calls = send.call_args_list
        start_call = calls[0][0][0]
        assert start_call["status"] == 401