import pytest
import jwt
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, Optional

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))


if __name__ == "__main__":
    # Run tests when executing the file directly
    pytest.main([__file__, "-v"])

from fastmcp.server.auth.providers.jwt_bearer import JWTBearerAuthProvider
from mcp.server.auth.provider import AccessToken


class TestJWTBearerAuthProviderInit:
    """Test cases for JWTBearerAuthProvider initialization."""

    def test_init_with_secret(self):
        """Test initialization with a secret."""
        provider = JWTBearerAuthProvider(secret_key="test-secret")
        assert provider.secret_key == "test-secret"
        assert provider.check_database is True
        assert provider.issuer == "dhafnck-mcp"
        assert provider.required_scopes == ["mcp:access"]

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "env-secret"})
    def test_init_with_env_secret(self):
        """Test initialization with environment variable secret."""
        provider = JWTBearerAuthProvider()
        assert provider.secret_key == "env-secret"

    def test_init_without_secret_raises_error(self):
        """Test initialization without secret raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY must be provided"):
                JWTBearerAuthProvider()

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        provider = JWTBearerAuthProvider(
            secret_key="test-secret",
            issuer="custom-issuer",
            audience=["audience1", "audience2"],
            required_scopes=["read", "write"],
            check_database=False
        )
        assert provider.issuer == "custom-issuer"
        assert provider.audience == ["audience1", "audience2"]
        assert provider.required_scopes == ["read", "write"]
        assert provider.check_database is False


class TestJWTBearerAuthProviderLoadAccessToken:
    """Test cases for load_access_token method."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider(check_database=False)
            return provider

    @pytest.fixture
    def provider_with_db(self):
        """Create a provider instance with database checking enabled."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider(check_database=True)
            return provider

    @pytest.mark.asyncio
    async def test_load_access_token_valid_api_token(self, provider):
        """Test loading a valid API token."""
        # Create a valid API token
        payload = {
            "type": "api_token",
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "scopes": ["read:tasks", "write:tasks"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Test loading token
        result = await provider.load_access_token(token)
        
        assert isinstance(result, AccessToken)
        assert result.client_id == "test-user-id"
        assert "mcp:access" in result.scopes
        assert "mcp:read" in result.scopes
        assert "mcp:write" in result.scopes
        assert result.metadata["token_id"] == "test-token-id"
        assert result.metadata["token_type"] == "api_token"

    @pytest.mark.asyncio
    async def test_load_access_token_valid_user_token(self, provider):
        """Test loading a valid user token."""
        # Create a valid user token
        payload = {
            "token_type": "access",
            "sub": "user-123",
            "email": "user@example.com",
            "roles": ["developer"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Test loading token
        result = await provider.load_access_token(token)
        
        assert isinstance(result, AccessToken)
        assert result.client_id == "user-123"
        assert "mcp:access" in result.scopes
        assert "mcp:read" in result.scopes
        assert "mcp:write" in result.scopes
        assert result.metadata["token_type"] == "user_token"
        assert result.metadata["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_load_access_token_invalid_format(self, provider):
        """Test loading token with invalid format."""
        result = await provider.load_access_token("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_access_token_expired(self, provider):
        """Test loading an expired token."""
        # Create an expired token
        payload = {
            "type": "api_token",
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        result = await provider.load_access_token(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_load_access_token_wrong_secret(self, provider):
        """Test loading token signed with wrong secret."""
        payload = {
            "type": "api_token",
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        result = await provider.load_access_token(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_load_access_token_with_db_check_inactive(self, provider_with_db):
        """Test loading token that is inactive in database."""
        payload = {
            "type": "api_token",
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "scopes": ["read:tasks"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Mock database check
        with patch.object(provider_with_db, '_validate_token_in_database', return_value=False):
            result = await provider_with_db.load_access_token(token)
            assert result is None

    @pytest.mark.asyncio
    async def test_load_access_token_with_db_check_valid(self, provider_with_db):
        """Test loading token that is valid in database."""
        payload = {
            "type": "api_token",
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "scopes": ["read:tasks"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Mock database check
        with patch.object(provider_with_db, '_validate_token_in_database', return_value=True):
            result = await provider_with_db.load_access_token(token)
            assert isinstance(result, AccessToken)
            assert result.client_id == "test-user-id"

    @pytest.mark.asyncio
    async def test_load_access_token_missing_required_fields(self, provider):
        """Test loading API token missing required fields."""
        # Token without token_id
        payload = {
            "type": "api_token",
            "user_id": "test-user-id",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        result = await provider.load_access_token(token)
        assert result is None
        
        # Token without user_id
        payload = {
            "type": "api_token",
            "token_id": "test-token-id",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        result = await provider.load_access_token(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_load_access_token_admin_role(self, provider):
        """Test loading user token with admin role."""
        payload = {
            "token_type": "access",
            "sub": "admin-user",
            "roles": ["admin"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        result = await provider.load_access_token(token)
        assert isinstance(result, AccessToken)
        assert "mcp:admin" in result.scopes
        assert "mcp:write" in result.scopes
        assert "mcp:read" in result.scopes

    @pytest.mark.asyncio
    async def test_load_access_token_unknown_token_type(self, provider):
        """Test loading token with unknown type."""
        payload = {
            "type": "unknown_type",
            "user_id": "test-user-id",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        result = await provider.load_access_token(token)
        assert result is None


class TestJWTBearerProviderCheckPermission:
    """Test cases for check_permission method."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        return JWTBearerProvider(secret="test-secret")

    @pytest.mark.asyncio
    async def test_check_permission_authenticated_user(self, provider):
        """Test permission check for authenticated user."""
        auth_context = {
            "authenticated": True,
            "metadata": {"user_id": "test-user", "token_id": "test-token"}
        }
        resource = Resource(uri="test://resource", name="Test Resource")
        
        result = await provider.check_permission(auth_context, resource, "read")
        
        assert result["allowed"] is True
        assert result["reason"] == "Authenticated users have access to all resources"

    @pytest.mark.asyncio
    async def test_check_permission_unauthenticated_user(self, provider):
        """Test permission check for unauthenticated user."""
        auth_context = {
            "authenticated": False,
            "reason": "No token provided"
        }
        resource = Resource(uri="test://resource", name="Test Resource")
        
        result = await provider.check_permission(auth_context, resource, "read")
        
        assert result["allowed"] is False
        assert result["reason"] == "Authentication required"

    @pytest.mark.asyncio
    async def test_check_permission_various_actions(self, provider):
        """Test permission check with various actions."""
        auth_context = {
            "authenticated": True,
            "metadata": {"user_id": "test-user", "token_id": "test-token"}
        }
        resource = Resource(uri="test://resource", name="Test Resource")
        
        actions = ["read", "write", "delete", "execute", "custom_action"]
        
        for action in actions:
            result = await provider.check_permission(auth_context, resource, action)
            assert result["allowed"] is True
            assert result["reason"] == "Authenticated users have access to all resources"

    @pytest.mark.asyncio
    async def test_check_permission_different_resources(self, provider):
        """Test permission check with different resource types."""
        auth_context = {
            "authenticated": True,
            "metadata": {"user_id": "test-user", "token_id": "test-token"}
        }
        
        resources = [
            Resource(uri="file://test.txt", name="File Resource"),
            Resource(uri="http://api.example.com", name="API Resource"),
            Resource(uri="database://table", name="Database Resource"),
        ]
        
        for resource in resources:
            result = await provider.check_permission(auth_context, resource, "read")
            assert result["allowed"] is True


class TestJWTBearerProviderIntegration:
    """Integration tests for JWTBearerProvider."""

    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """Test the complete authentication flow."""
        secret = "integration-test-secret"
        provider = JWTBearerProvider(secret=secret)
        
        # Mock database
        provider._db_facade = Mock()
        
        # Create a valid token
        token_id = "integration-token-id"
        user_id = "integration-user-id"
        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Mock database response
        provider._db_facade.get_token_by_id.return_value = {
            "id": token_id,
            "is_active": True,
            "user_id": user_id
        }
        
        # Authenticate
        auth_result = await provider.authenticate({"token": token})
        assert auth_result["authenticated"] is True
        
        # Check permission
        resource = Resource(uri="test://resource", name="Test Resource")
        perm_result = await provider.check_permission(auth_result, resource, "read")
        assert perm_result["allowed"] is True

    @pytest.mark.asyncio
    async def test_token_lifecycle(self):
        """Test token lifecycle scenarios."""
        secret = "lifecycle-test-secret"
        provider = JWTBearerProvider(secret=secret)
        provider._db_facade = Mock()
        
        token_id = "lifecycle-token-id"
        user_id = "lifecycle-user-id"
        
        # Scenario 1: New active token
        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        provider._db_facade.get_token_by_id.return_value = {
            "id": token_id,
            "is_active": True,
            "user_id": user_id
        }
        
        result = await provider.authenticate({"token": token})
        assert result["authenticated"] is True
        
        # Scenario 2: Token becomes inactive
        provider._db_facade.get_token_by_id.return_value = {
            "id": token_id,
            "is_active": False,
            "user_id": user_id
        }
        
        result = await provider.authenticate({"token": token})
        assert result["authenticated"] is False
        assert "Token is not active" in result["reason"]
        
        # Scenario 3: Token is deleted from database
        provider._db_facade.get_token_by_id.return_value = None
        
        result = await provider.authenticate({"token": token})
        assert result["authenticated"] is False
        assert "Token not found" in result["reason"]


class TestJWTBearerProviderEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_malformed_jwt_tokens(self):
        """Test various malformed JWT tokens."""
        provider = JWTBearerProvider(secret="test-secret")
        
        malformed_tokens = [
            "not.a.jwt",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Missing parts
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..",  # Empty parts
            "a.b.c.d",  # Too many parts
            "",  # Empty string
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.payload.signature",  # With Bearer prefix
        ]
        
        for token in malformed_tokens:
            result = await provider.authenticate({"token": token})
            assert result["authenticated"] is False
            assert "Invalid token" in result["reason"] or "No token provided" in result["reason"]

    @pytest.mark.asyncio
    async def test_jwt_with_different_algorithms(self):
        """Test JWT tokens with different algorithms."""
        provider = JWTBearerProvider(secret="test-secret")
        provider._db_facade = Mock()
        
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        
        # Try different algorithms
        algorithms = ["HS384", "HS512"]
        
        for algo in algorithms:
            token = jwt.encode(payload, "test-secret", algorithm=algo)
            result = await provider.authenticate({"token": token})
            # Should fail because provider expects HS256
            assert result["authenticated"] is False
            assert "Invalid token" in result["reason"]

    @pytest.mark.asyncio
    async def test_concurrent_authentication_requests(self):
        """Test concurrent authentication requests."""
        provider = JWTBearerProvider(secret="test-secret")
        provider._db_facade = Mock()
        
        # Create multiple tokens
        tokens = []
        for i in range(5):
            payload = {
                "token_id": f"token-{i}",
                "user_id": f"user-{i}",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            }
            token = jwt.encode(payload, "test-secret", algorithm="HS256")
            tokens.append((token, payload))
        
        # Mock database to return active tokens
        def get_token_by_id(token_id):
            return {
                "id": token_id,
                "is_active": True,
                "user_id": token_id.replace("token-", "user-")
            }
        
        provider._db_facade.get_token_by_id.side_effect = get_token_by_id
        
        # Simulate concurrent requests
        import asyncio
        
        async def authenticate_token(token):
            return await provider.authenticate({"token": token})
        
        results = await asyncio.gather(
            *[authenticate_token(token) for token, _ in tokens]
        )
        
        # All should be authenticated
        for result in results:
            assert result["authenticated"] is True

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        provider = JWTBearerProvider(secret="test-secret-🔑")
        provider._db_facade = Mock()
        
        # Token with Unicode in payload
        payload = {
            "token_id": "token-αβγ",
            "user_id": "user-😀",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "custom_field": "中文测试"
        }
        
        token = jwt.encode(payload, "test-secret-🔑", algorithm="HS256")
        
        provider._db_facade.get_token_by_id.return_value = {
            "id": "token-αβγ",
            "is_active": True,
            "user_id": "user-😀"
        }
        
        result = await provider.authenticate({"token": token})
        assert result["authenticated"] is True
        assert result["metadata"]["user_id"] == "user-😀"