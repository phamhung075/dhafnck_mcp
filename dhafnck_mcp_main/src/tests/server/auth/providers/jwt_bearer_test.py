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


class TestJWTBearerAuthProviderVerifyToken:
    """Test cases for verify_token method."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider(check_database=False)
            # Mock the JWT backend verify_token method
            provider.jwt_backend = Mock()
            provider.jwt_backend.verify_token = AsyncMock()
            return provider

    @pytest.fixture
    def provider_with_db(self):
        """Create a provider instance with database checking enabled."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider(check_database=True)
            return provider

    @pytest.mark.asyncio
    async def test_verify_token_delegates_to_jwt_backend(self, provider):
        """Test that verify_token delegates to JWT backend."""
        # Mock the expected AccessToken response
        mock_access_token = Mock(spec=AccessToken)
        mock_access_token.client_id = "test-user-id"
        mock_access_token.scopes = ["mcp:access", "mcp:read"]
        provider.jwt_backend.verify_token.return_value = mock_access_token
        
        # Test verify_token
        result = await provider.verify_token("test-token")
        
        # Verify delegation
        provider.jwt_backend.verify_token.assert_called_once_with("test-token")
        assert result == mock_access_token

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_invalid(self, provider):
        """Test that verify_token returns None for invalid token."""
        # Mock JWT backend to return None
        provider.jwt_backend.verify_token.return_value = None
        
        # Test verify_token
        result = await provider.verify_token("invalid-token")
        
        # Verify delegation and result
        provider.jwt_backend.verify_token.assert_called_once_with("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_access_token_delegates_to_verify_token(self, provider):
        """Test that load_access_token delegates to verify_token."""
        # Mock the expected AccessToken response
        mock_access_token = Mock(spec=AccessToken)
        provider.jwt_backend.verify_token.return_value = mock_access_token
        
        # Test load_access_token
        result = await provider.load_access_token("test-token")
        
        # Verify delegation
        provider.jwt_backend.verify_token.assert_called_once_with("test-token")
        assert result == mock_access_token

    @pytest.mark.asyncio
    async def test_verify_token_with_supabase_token(self, provider):
        """Test verifying Supabase-style token."""
        # Mock a Supabase-style AccessToken
        mock_access_token = Mock(spec=AccessToken)
        mock_access_token.client_id = "supabase-user-id"
        mock_access_token.scopes = ["mcp:access", "mcp:read"]
        provider.jwt_backend.verify_token.return_value = mock_access_token
        
        # Test with Supabase-style token
        result = await provider.verify_token("supabase-jwt-token")
        
        # Verify result
        assert result == mock_access_token
        assert result.client_id == "supabase-user-id"

    @pytest.mark.asyncio
    async def test_verify_token_with_local_jwt(self, provider):
        """Test verifying local JWT token."""
        # Mock a local JWT AccessToken
        mock_access_token = Mock(spec=AccessToken)
        mock_access_token.client_id = "local-user-id"
        mock_access_token.scopes = ["mcp:access", "mcp:write", "mcp:read"]
        provider.jwt_backend.verify_token.return_value = mock_access_token
        
        # Test with local JWT token
        result = await provider.verify_token("local-jwt-token")
        
        # Verify result
        assert result == mock_access_token
        assert "mcp:write" in result.scopes

    @pytest.mark.asyncio
    async def test_jwt_backend_initialization(self):
        """Test that JWT backend is properly initialized."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            with patch('fastmcp.auth.mcp_integration.jwt_auth_backend.create_jwt_auth_backend') as mock_create:
                mock_backend = Mock()
                mock_create.return_value = mock_backend
                
                provider = JWTBearerAuthProvider(required_scopes=["custom:scope"])
                
                # Verify JWT backend was created with proper scopes
                mock_create.assert_called_once_with(required_scopes=["custom:scope"])
                assert provider.jwt_backend == mock_backend






class TestJWTBearerAuthProviderValidateUserToken:
    """Test cases for _validate_user_token method."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            return JWTBearerAuthProvider(check_database=False)

    @pytest.mark.asyncio
    async def test_validate_user_token_valid_access_token(self, provider):
        """Test validating a valid user access token."""
        payload = {
            "token_type": "access",
            "sub": "user-123",
            "email": "user@example.com",
            "roles": ["developer"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        
        result = await provider._validate_user_token("token", payload)
        
        assert isinstance(result, AccessToken)
        assert result.client_id == "user-123"
        assert "mcp:access" in result.scopes
        assert "mcp:read" in result.scopes
        assert "mcp:write" in result.scopes
        assert result.metadata["token_type"] == "user_token"
        assert result.metadata["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_validate_user_token_wrong_type(self, provider):
        """Test validating token with wrong token_type."""
        payload = {
            "token_type": "refresh",  # Not "access"
            "sub": "user-123",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        
        result = await provider._validate_user_token("token", payload)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_user_token_admin_role(self, provider):
        """Test validating user token with admin role."""
        payload = {
            "token_type": "access",
            "sub": "admin-user",
            "email": "admin@example.com",
            "roles": ["admin"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        
        result = await provider._validate_user_token("token", payload)
        
        assert isinstance(result, AccessToken)
        assert "mcp:admin" in result.scopes
        assert "mcp:write" in result.scopes
        assert "mcp:read" in result.scopes

    @pytest.mark.asyncio
    async def test_validate_user_token_user_role(self, provider):
        """Test validating user token with basic user role."""
        payload = {
            "token_type": "access",
            "sub": "basic-user",
            "roles": ["user"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        
        result = await provider._validate_user_token("token", payload)
        
        assert isinstance(result, AccessToken)
        assert "mcp:access" in result.scopes
        assert "mcp:read" in result.scopes
        assert "mcp:write" not in result.scopes
        assert "mcp:admin" not in result.scopes
    
    @pytest.mark.asyncio
    async def test_validate_user_token_missing_user_id(self, provider):
        """Test validating token without user ID."""
        payload = {
            "token_type": "access",
            "email": "user@example.com",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        
        result = await provider._validate_user_token("token", payload)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_user_token_exception_handling(self, provider):
        """Test exception handling in _validate_user_token."""
        # Invalid payload that will cause exception
        payload = None
        
        result = await provider._validate_user_token("token", payload)
        
        assert result is None


class TestJWTBearerAuthProviderScopeMapping:
    """Test cases for _map_scopes_to_mcp method."""
    
    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            return JWTBearerAuthProvider()
    
    def test_map_scopes_to_mcp_read_write(self, provider):
        """Test mapping read/write scopes."""
        scopes = ["read:tasks", "write:tasks", "read:context"]
        result = provider._map_scopes_to_mcp(scopes)
        
        assert "mcp:read" in result
        assert "mcp:write" in result
        assert len(result) == 2  # Duplicates removed
    
    def test_map_scopes_to_mcp_execute(self, provider):
        """Test mapping execute scope."""
        scopes = ["execute:mcp"]
        result = provider._map_scopes_to_mcp(scopes)
        
        assert "mcp:execute" in result
    
    def test_map_scopes_to_mcp_unknown_scopes(self, provider):
        """Test mapping unknown scopes."""
        scopes = ["unknown:scope", "another:unknown"]
        result = provider._map_scopes_to_mcp(scopes)
        
        assert len(result) == 0
    
    def test_map_scopes_to_mcp_mixed(self, provider):
        """Test mapping mixed known and unknown scopes."""
        scopes = ["read:tasks", "unknown:scope", "write:agents", "admin:all"]
        result = provider._map_scopes_to_mcp(scopes)
        
        assert "mcp:read" in result
        assert "mcp:write" in result
        assert "admin:all" not in result  # Admin scope mapping removed


class TestJWTBearerAuthProviderIntegration:
    """Integration tests for JWTBearerAuthProvider."""

    @pytest.mark.asyncio
    async def test_full_authentication_flow_with_jwt_backend(self):
        """Test the complete authentication flow with JWT backend."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "integration-test-secret"}):
            with patch('fastmcp.auth.mcp_integration.jwt_auth_backend.create_jwt_auth_backend') as mock_create:
                # Mock JWT backend
                mock_jwt_backend = Mock()
                mock_access_token = Mock(spec=AccessToken)
                mock_access_token.client_id = "integration-user-id"
                mock_access_token.scopes = ["mcp:access", "mcp:read", "mcp:write"]
                mock_access_token.expires_at = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
                mock_jwt_backend.verify_token = AsyncMock(return_value=mock_access_token)
                mock_create.return_value = mock_jwt_backend
                
                provider = JWTBearerAuthProvider()
                
                # Test verify_token
                result = await provider.verify_token("test-token")
                assert result == mock_access_token
                assert result.client_id == "integration-user-id"
                
                # Test load_access_token (should delegate)
                result2 = await provider.load_access_token("test-token")
                assert result2 == mock_access_token

    @pytest.mark.asyncio
    async def test_provider_with_different_configurations(self):
        """Test provider with different configurations."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            # Test with custom issuer and audience
            provider1 = JWTBearerAuthProvider(
                issuer="custom-issuer",
                audience=["aud1", "aud2"],
                required_scopes=["custom:read", "custom:write"]
            )
            assert provider1.issuer == "custom-issuer"
            assert provider1.audience == ["aud1", "aud2"]
            assert provider1.required_scopes == ["custom:read", "custom:write"]
            
            # Test with database checking disabled
            provider2 = JWTBearerAuthProvider(check_database=False)
            assert provider2.check_database is False
            
            # Test with default configuration
            provider3 = JWTBearerAuthProvider()
            assert provider3.issuer == "dhafnck-mcp"
            assert provider3.required_scopes == ["mcp:access"]
            assert provider3.check_database is True


class TestJWTBearerAuthProviderDatabaseValidation:
    """Test cases for database validation."""
    
    @pytest.mark.asyncio
    async def test_validate_token_in_database_active(self):
        """Test validating active token in database."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider()
            
            # Mock database components
            with patch('fastmcp.auth.interface.fastapi_auth.get_db') as mock_get_db:
                mock_db = Mock()
                mock_token = Mock()
                mock_token.id = "test-token-id"
                mock_token.is_active = True
                mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
                mock_token.last_used_at = None
                mock_token.usage_count = 0
                mock_token.rate_limit = None
                
                mock_db.query.return_value.filter.return_value.first.return_value = mock_token
                mock_get_db.return_value = iter([mock_db])
                
                result = await provider._validate_token_in_database("test-token-id")
                
                assert result is True
                assert mock_token.usage_count == 1
                assert mock_token.last_used_at is not None
                mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_token_in_database_expired(self):
        """Test validating expired token in database."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider()
            
            with patch('fastmcp.auth.interface.fastapi_auth.get_db') as mock_get_db:
                mock_db = Mock()
                mock_token = Mock()
                mock_token.id = "test-token-id"
                mock_token.is_active = True
                mock_token.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
                
                mock_db.query.return_value.filter.return_value.first.return_value = mock_token
                mock_get_db.return_value = iter([mock_db])
                
                result = await provider._validate_token_in_database("test-token-id")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_token_in_database_not_found(self):
        """Test validating non-existent token in database."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider()
            
            with patch('fastmcp.auth.interface.fastapi_auth.get_db') as mock_get_db:
                mock_db = Mock()
                mock_db.query.return_value.filter.return_value.first.return_value = None
                mock_get_db.return_value = iter([mock_db])
                
                result = await provider._validate_token_in_database("non-existent-token")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_token_in_database_exception(self):
        """Test exception handling in database validation."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider()
            
            with patch('fastmcp.auth.interface.fastapi_auth.get_db') as mock_get_db:
                mock_get_db.side_effect = Exception("Database error")
                
                result = await provider._validate_token_in_database("test-token-id")
                
                assert result is False


class TestJWTBearerAuthProviderEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_malformed_jwt_tokens(self):
        """Test various malformed JWT tokens."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider()
            # Mock JWT backend to return None for invalid tokens
            provider.jwt_backend = Mock()
            provider.jwt_backend.verify_token = AsyncMock(return_value=None)
            
            malformed_tokens = [
                "not.a.jwt",
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Missing parts
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..",  # Empty parts
                "a.b.c.d",  # Too many parts
                "",  # Empty string
                "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.payload.signature",  # With Bearer prefix
            ]
            
            for token in malformed_tokens:
                result = await provider.verify_token(token)
                assert result is None
                provider.jwt_backend.verify_token.assert_called_with(token)

    @pytest.mark.asyncio
    async def test_dual_jwt_validation_with_jwt_backend(self):
        """Test that provider supports both Supabase and local JWT tokens via backend."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret", "SUPABASE_JWT_SECRET": "supabase-secret"}):
            provider = JWTBearerAuthProvider()
            
            # Test should verify JWT backend handles both token types
            # Mock different responses for different token types
            
            # Local token
            local_access_token = Mock(spec=AccessToken)
            local_access_token.client_id = "local-user"
            local_access_token.scopes = ["mcp:access", "mcp:read"]
            
            # Supabase token  
            supabase_access_token = Mock(spec=AccessToken)
            supabase_access_token.client_id = "supabase-user"
            supabase_access_token.scopes = ["mcp:access", "mcp:write"]
            
            provider.jwt_backend = Mock()
            provider.jwt_backend.verify_token = AsyncMock(side_effect=[local_access_token, supabase_access_token])
            
            # Test local token
            result1 = await provider.verify_token("local-token")
            assert result1.client_id == "local-user"
            
            # Test Supabase token
            result2 = await provider.verify_token("supabase-token") 
            assert result2.client_id == "supabase-user"

    @pytest.mark.asyncio
    async def test_concurrent_token_verification(self):
        """Test concurrent token verification requests."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            provider = JWTBearerAuthProvider()
            
            # Create mock responses for concurrent requests
            mock_tokens = []
            for i in range(5):
                mock_token = Mock(spec=AccessToken)
                mock_token.client_id = f"user-{i}"
                mock_token.scopes = ["mcp:access", "mcp:read"]
                mock_tokens.append(mock_token)
            
            provider.jwt_backend = Mock()
            provider.jwt_backend.verify_token = AsyncMock(side_effect=mock_tokens)
            
            # Simulate concurrent requests
            import asyncio
            
            async def verify_token(token_id):
                return await provider.verify_token(f"token-{token_id}")
            
            results = await asyncio.gather(
                *[verify_token(i) for i in range(5)]
            )
            
            # All should return valid AccessTokens
            for i, result in enumerate(results):
                assert result.client_id == f"user-{i}"
                assert "mcp:access" in result.scopes

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-🔑"}):
            provider = JWTBearerAuthProvider()
            
            # Mock AccessToken with Unicode
            mock_token = Mock(spec=AccessToken)
            mock_token.client_id = "user-😀"
            mock_token.scopes = ["mcp:access"]
            mock_token.metadata = {"custom_field": "中文测试"}
            
            provider.jwt_backend = Mock()
            provider.jwt_backend.verify_token = AsyncMock(return_value=mock_token)
            
            result = await provider.verify_token("unicode-token")
            
            assert result.client_id == "user-😀"
            assert result.metadata["custom_field"] == "中文测试"
    
    @pytest.mark.asyncio  
    async def test_provider_initialization_errors(self):
        """Test provider initialization error cases."""
        # Test without JWT_SECRET_KEY
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY must be provided"):
                JWTBearerAuthProvider()
        
        # Test with empty secret
        with patch.dict(os.environ, {"JWT_SECRET_KEY": ""}, clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY must be provided"):
                JWTBearerAuthProvider()