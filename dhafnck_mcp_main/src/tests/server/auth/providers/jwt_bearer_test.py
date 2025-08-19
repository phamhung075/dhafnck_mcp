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

from fastmcp.server.auth.providers.jwt_bearer import JWTBearerProvider
from fastmcp.resources import Resource


class TestJWTBearerProviderInit:
    """Test cases for JWTBearerProvider initialization."""

    def test_init_with_secret(self):
        """Test initialization with a secret."""
        provider = JWTBearerProvider(secret="test-secret")
        assert provider.secret == "test-secret"
        assert provider._db_facade is not None

    def test_init_without_secret(self):
        """Test initialization without a secret."""
        provider = JWTBearerProvider()
        assert provider.secret is None
        assert provider._db_facade is not None

    @patch('fastmcp.server.auth.providers.jwt_bearer.TokenDbApplicationFacade')
    def test_init_with_custom_db_facade(self, mock_facade_class):
        """Test initialization with custom database facade."""
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        
        provider = JWTBearerProvider(secret="test-secret")
        
        assert provider._db_facade == mock_facade
        mock_facade_class.assert_called_once()


class TestJWTBearerProviderAuthenticate:
    """Test cases for authenticate method."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        return JWTBearerProvider(secret="test-secret")

    @pytest.fixture
    def mock_db_facade(self, provider):
        """Mock the database facade."""
        provider._db_facade = Mock()
        return provider._db_facade

    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self, provider, mock_db_facade):
        """Test authentication with a valid token."""
        # Create a valid token
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Mock database response
        mock_db_facade.get_token_by_id.return_value = {
            "id": "test-token-id",
            "is_active": True,
            "user_id": "test-user-id"
        }
        
        # Test authentication
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is True
        assert result["metadata"]["user_id"] == "test-user-id"
        assert result["metadata"]["token_id"] == "test-token-id"
        mock_db_facade.get_token_by_id.assert_called_once_with("test-token-id")

    @pytest.mark.asyncio
    async def test_authenticate_no_credentials(self, provider):
        """Test authentication with no credentials."""
        result = await provider.authenticate({})
        
        assert result["authenticated"] is False
        assert "No token provided" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token_format(self, provider):
        """Test authentication with invalid token format."""
        result = await provider.authenticate({"token": "invalid-token"})
        
        assert result["authenticated"] is False
        assert "Invalid token" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_expired_token(self, provider, mock_db_facade):
        """Test authentication with an expired token."""
        # Create an expired token
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "Token has expired" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_wrong_secret(self, provider, mock_db_facade):
        """Test authentication with token signed with wrong secret."""
        # Create token with different secret
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "Invalid token" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_inactive_token(self, provider, mock_db_facade):
        """Test authentication with an inactive token in database."""
        # Create a valid token
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Mock database response with inactive token
        mock_db_facade.get_token_by_id.return_value = {
            "id": "test-token-id",
            "is_active": False,
            "user_id": "test-user-id"
        }
        
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "Token is not active" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_token_not_in_database(self, provider, mock_db_facade):
        """Test authentication when token is not found in database."""
        # Create a valid token
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Mock database response - token not found
        mock_db_facade.get_token_by_id.return_value = None
        
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "Token not found" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_missing_token_id_in_payload(self, provider, mock_db_facade):
        """Test authentication with token missing token_id in payload."""
        # Create token without token_id
        payload = {
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "Invalid token payload" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_no_secret_configured(self, mock_db_facade):
        """Test authentication when no secret is configured."""
        provider = JWTBearerProvider()  # No secret
        provider._db_facade = mock_db_facade
        
        token = "some-token"
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "JWT secret not configured" in result["reason"]

    @pytest.mark.asyncio
    async def test_authenticate_database_error(self, provider, mock_db_facade):
        """Test authentication when database raises an error."""
        # Create a valid token
        payload = {
            "token_id": "test-token-id",
            "user_id": "test-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        # Mock database error
        mock_db_facade.get_token_by_id.side_effect = Exception("Database error")
        
        result = await provider.authenticate({"token": token})
        
        assert result["authenticated"] is False
        assert "Authentication failed" in result["reason"]


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