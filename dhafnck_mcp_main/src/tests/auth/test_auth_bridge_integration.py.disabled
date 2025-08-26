"""
Integration tests for Authentication Bridge

Tests the auth bridge pattern that allows MCP's native authentication
and FastAPI's OAuth2PasswordBearer to coexist.
"""

import pytest
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import jwt

from fastmcp.auth.bridge.auth_bridge import (
    AuthBridge,
    get_auth_bridge,
    get_current_user_from_bridge
)
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastapi import HTTPException
from starlette.requests import Request


class TestAuthBridge:
    """Test the AuthBridge class"""
    
    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing"""
        return JWTService(
            secret_key="test-secret-key-for-testing",
            issuer="test-issuer"
        )
    
    @pytest.fixture
    def mock_mcp_backend(self):
        """Create mock MCP backend"""
        backend = AsyncMock()
        
        # Mock successful MCP token validation
        mock_token = Mock()
        mock_token.client_id = "mcp-user-123"
        mock_token.scopes = ["mcp:read", "mcp:write", "mcp:access"]
        
        backend.load_access_token.return_value = mock_token
        return backend
    
    @pytest.fixture
    def auth_bridge(self, jwt_service, mock_mcp_backend):
        """Create AuthBridge with both backends"""
        return AuthBridge(
            jwt_service=jwt_service,
            mcp_backend=mock_mcp_backend,
            enable_mcp=True,
            enable_oauth2=True
        )
    
    @pytest.mark.asyncio
    async def test_validate_oauth2_token(self, auth_bridge, jwt_service):
        """Test validation of OAuth2 JWT token"""
        # Create a valid OAuth2 token
        user_id = str(uuid.uuid4())
        token = jwt_service.create_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["developer"],
            additional_claims={"custom": "claim"}
        )
        
        # Validate through bridge
        result = await auth_bridge.validate_token(token, prefer_oauth2=True)
        
        # Verify result
        assert result is not None
        assert result["user_id"] == user_id
        assert result["email"] == "test@example.com"
        assert result["auth_method"] == "oauth2"
        assert "developer" in result["roles"]
        assert "mcp:write" in result["scopes"]  # Developer role includes write scope
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token(self, auth_bridge, mock_mcp_backend):
        """Test validation of MCP bearer token"""
        # Use a mock MCP token
        mcp_token = "mcp-bearer-token-123"
        
        # Validate through bridge (prefer MCP)
        result = await auth_bridge.validate_token(mcp_token, prefer_oauth2=False)
        
        # Verify result
        assert result is not None
        assert result["user_id"] == "mcp-user-123"
        assert result["auth_method"] == "mcp"
        assert "mcp:read" in result["scopes"]
        assert "mcp:write" in result["scopes"]
        
        # Verify MCP backend was called
        mock_mcp_backend.load_access_token.assert_called_once_with(mcp_token)
    
    @pytest.mark.asyncio
    async def test_fallback_to_mcp_when_oauth2_fails(self, auth_bridge, mock_mcp_backend):
        """Test fallback to MCP when OAuth2 validation fails"""
        # Use an invalid OAuth2 token that MCP will accept
        invalid_oauth_token = "not-a-jwt-token"
        
        # Validate through bridge (prefer OAuth2 but it will fail)
        result = await auth_bridge.validate_token(invalid_oauth_token, prefer_oauth2=True)
        
        # Should fallback to MCP and succeed
        assert result is not None
        assert result["auth_method"] == "mcp"
        assert result["user_id"] == "mcp-user-123"
    
    @pytest.mark.asyncio
    async def test_fallback_to_oauth2_when_mcp_fails(self, auth_bridge, jwt_service, mock_mcp_backend):
        """Test fallback to OAuth2 when MCP validation fails"""
        # Make MCP backend reject the token
        mock_mcp_backend.load_access_token.return_value = None
        
        # Create a valid OAuth2 token
        user_id = str(uuid.uuid4())
        token = jwt_service.create_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        # Validate through bridge (prefer MCP but it will fail)
        result = await auth_bridge.validate_token(token, prefer_oauth2=False)
        
        # Should fallback to OAuth2 and succeed
        assert result is not None
        assert result["auth_method"] == "oauth2"
        assert result["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_both_validations_fail(self, auth_bridge, mock_mcp_backend):
        """Test when both OAuth2 and MCP validation fail"""
        # Make MCP backend reject the token
        mock_mcp_backend.load_access_token.return_value = None
        
        # Use an invalid token for both systems
        invalid_token = "completely-invalid-token"
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await auth_bridge.validate_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_token_caching(self, auth_bridge, jwt_service):
        """Test that validated tokens are cached"""
        # Create a valid OAuth2 token
        user_id = str(uuid.uuid4())
        token = jwt_service.create_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user"]
        )
        
        # Validate token twice
        result1 = await auth_bridge.validate_token(token)
        result2 = await auth_bridge.validate_token(token)
        
        # Results should be the same (from cache)
        assert result1["user_id"] == result2["user_id"]
        assert result1["auth_method"] == result2["auth_method"]
        
        # Clear cache and validate again
        auth_bridge.clear_cache(token)
        result3 = await auth_bridge.validate_token(token)
        
        # Should still work but not from cache
        assert result3["user_id"] == user_id
    
    def test_role_to_scope_mapping(self, auth_bridge):
        """Test role to MCP scope conversion"""
        # Test admin role
        admin_scopes = auth_bridge._roles_to_scopes(["admin"])
        assert "mcp:admin" in admin_scopes
        assert "mcp:write" in admin_scopes
        assert "mcp:read" in admin_scopes
        assert "mcp:access" in admin_scopes
        
        # Test developer role
        dev_scopes = auth_bridge._roles_to_scopes(["developer"])
        assert "mcp:admin" not in dev_scopes
        assert "mcp:write" in dev_scopes
        assert "mcp:read" in dev_scopes
        assert "mcp:access" in dev_scopes
        
        # Test user role
        user_scopes = auth_bridge._roles_to_scopes(["user"])
        assert "mcp:admin" not in user_scopes
        assert "mcp:write" not in user_scopes
        assert "mcp:read" in user_scopes
        assert "mcp:access" in user_scopes
        
        # Test multiple roles
        multi_scopes = auth_bridge._roles_to_scopes(["user", "developer"])
        assert "mcp:write" in multi_scopes  # From developer
        assert "mcp:read" in multi_scopes   # From both
        assert "mcp:access" in multi_scopes # From both


class TestAuthBridgeDependency:
    """Test the FastAPI dependency injection for auth bridge"""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request with auth header"""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer test-token-123"}
        return request
    
    @pytest.fixture
    def mock_auth_bridge(self):
        """Create mock auth bridge"""
        bridge = AsyncMock(spec=AuthBridge)
        bridge.validate_token.return_value = {
            "user_id": "user-123",
            "email": "test@example.com",
            "roles": ["developer"],
            "scopes": ["mcp:write", "mcp:read"],
            "auth_method": "oauth2"
        }
        return bridge
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_bridge(self, mock_request, mock_auth_bridge):
        """Test the FastAPI dependency for getting current user"""
        with patch('fastmcp.auth.bridge.auth_bridge.get_auth_bridge', return_value=mock_auth_bridge):
            # Call the dependency
            user_info = await get_current_user_from_bridge(
                request=mock_request,
                auth_bridge=mock_auth_bridge
            )
            
            # Verify result
            assert user_info is not None
            assert user_info["user_id"] == "user-123"
            assert user_info["email"] == "test@example.com"
            assert user_info["auth_method"] == "oauth2"
            
            # Verify bridge was called with correct token
            mock_auth_bridge.validate_token.assert_called_once_with("test-token-123")
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, mock_auth_bridge):
        """Test when Authorization header is missing"""
        request = Mock(spec=Request)
        request.headers = {}  # No Authorization header
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_bridge(
                request=request,
                auth_bridge=mock_auth_bridge
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self, mock_auth_bridge):
        """Test when Authorization header has wrong format"""
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}  # Basic auth instead of Bearer
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_bridge(
                request=request,
                auth_bridge=mock_auth_bridge
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header" in str(exc_info.value.detail)


class TestAuthBridgeIntegration:
    """Full integration tests with both auth systems"""
    
    @pytest.mark.asyncio
    async def test_dual_auth_system_coexistence(self):
        """Test that both auth systems can work together"""
        # Create JWT service
        jwt_service = JWTService(
            secret_key="integration-test-secret",
            issuer="test-issuer"
        )
        
        # Create mock MCP backend
        mock_mcp = AsyncMock()
        mock_mcp_token = Mock()
        mock_mcp_token.client_id = "mcp-client-456"
        mock_mcp_token.scopes = ["mcp:admin", "mcp:write", "mcp:read"]
        mock_mcp.load_access_token.return_value = mock_mcp_token
        
        # Create bridge with both systems
        bridge = AuthBridge(
            jwt_service=jwt_service,
            mcp_backend=mock_mcp,
            enable_mcp=True,
            enable_oauth2=True
        )
        
        # Test OAuth2 token
        oauth2_token = jwt_service.create_access_token(
            user_id="oauth-user-789",
            email="oauth@example.com",
            roles=["admin"]
        )
        
        oauth2_result = await bridge.validate_token(oauth2_token)
        assert oauth2_result["auth_method"] == "oauth2"
        assert oauth2_result["user_id"] == "oauth-user-789"
        assert "mcp:admin" in oauth2_result["scopes"]
        
        # Test MCP token
        mcp_token = "mcp-token-xyz"
        mcp_result = await bridge.validate_token(mcp_token, prefer_oauth2=False)
        assert mcp_result["auth_method"] == "mcp"
        assert mcp_result["user_id"] == "mcp-client-456"
        assert "mcp:admin" in mcp_result["scopes"]
        
        # Both systems work independently
        assert oauth2_result["user_id"] != mcp_result["user_id"]
        assert oauth2_result["auth_method"] != mcp_result["auth_method"]
    
    @pytest.mark.asyncio
    async def test_auth_bridge_singleton(self):
        """Test that get_auth_bridge returns singleton"""
        bridge1 = get_auth_bridge()
        bridge2 = get_auth_bridge()
        
        # Should be the same instance
        assert bridge1 is bridge2
        
        # Clear singleton for other tests
        import fastmcp.auth.bridge.auth_bridge
        fastmcp.auth.bridge.auth_bridge._auth_bridge = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])