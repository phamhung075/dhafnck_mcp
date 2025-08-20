"""
Tests for JWT Authentication Backend for MCP Integration

This module tests the integration between JWT authentication system
and the MCP server infrastructure.
"""

import pytest
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import jwt

from mcp.server.auth.provider import AccessToken
from fastmcp.auth.mcp_integration.jwt_auth_backend import (
    JWTAuthBackend,
    MCPUserContext,
    create_jwt_auth_backend
)
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.infrastructure.repositories.user_repository import UserRepository
from fastmcp.auth.domain.entities.user import User, UserRole
from fastmcp.auth.domain.value_objects import UserId


class TestMCPUserContext:
    """Test suite for MCPUserContext dataclass"""
    
    def test_user_context_creation(self):
        """Test creating user context with all fields"""
        context = MCPUserContext(
            user_id="user123",
            email="test@example.com",
            username="testuser",
            roles=["admin", "user"],
            scopes=["read", "write"]
        )
        
        assert context.user_id == "user123"
        assert context.email == "test@example.com"
        assert context.username == "testuser"
        assert context.roles == ["admin", "user"]
        assert context.scopes == ["read", "write"]


class TestJWTAuthBackend:
    """Test suite for JWTAuthBackend"""
    
    @pytest.fixture
    def jwt_service(self):
        """Create mock JWT service"""
        service = Mock(spec=JWTService)
        service.secret_key = "test-secret-key"
        service.ALGORITHM = "HS256"
        return service
    
    @pytest.fixture
    def user_repository(self):
        """Create mock user repository"""
        return Mock(spec=UserRepository)
    
    @pytest.fixture
    def auth_backend(self, jwt_service, user_repository, monkeypatch):
        """Create JWT auth backend with mocked services"""
        # Set required environment variable
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
        
        backend = JWTAuthBackend(
            jwt_service=jwt_service,
            user_repository=user_repository,
            required_scopes=["mcp:access"]
        )
        return backend
    
    def test_init_requires_jwt_secret(self, monkeypatch):
        """Test that initialization requires JWT_SECRET_KEY env var"""
        # Remove the env var if set
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        
        with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable not set"):
            JWTAuthBackend()
    
    def test_init_with_defaults(self, monkeypatch):
        """Test initialization with default values"""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
        monkeypatch.setenv("JWT_ISSUER", "test-issuer")
        monkeypatch.setenv("JWT_AUDIENCE", "test-audience")
        
        backend = JWTAuthBackend()
        
        assert backend._jwt_service is not None
        assert backend._user_repository is None
        assert backend._auth_service is None
    
    def test_secret_key_property(self, auth_backend, jwt_service):
        """Test secret_key property returns JWT service secret"""
        assert auth_backend.secret_key == "test-secret-key"
    
    def test_algorithm_property(self, auth_backend, jwt_service):
        """Test algorithm property returns JWT service algorithm"""
        assert auth_backend.algorithm == "HS256"
    
    @pytest.mark.asyncio
    async def test_load_access_token_valid(self, auth_backend, jwt_service):
        """Test loading valid access token"""
        # Mock JWT service to return valid payload
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "scopes": ["read", "write"],
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        jwt_service.verify_token.return_value = payload
        
        result = await auth_backend.load_access_token("valid.token.here")
        
        assert result is not None
        assert isinstance(result, AccessToken)
        assert result.client_id == "user123"
        assert "mcp:access" in result.scopes  # Base scope added
        assert "mcp:read" in result.scopes  # Default user scope
        assert result.expires_at == payload["exp"]
        
        # Verify token validation was called
        jwt_service.verify_token.assert_called()
    
    @pytest.mark.asyncio
    async def test_load_access_token_api_token_fallback(self, auth_backend, jwt_service):
        """Test loading api_token type as fallback"""
        # First call returns None (access type), second returns payload (api_token type)
        payload = {
            "sub": "user123",
            "type": "api_token",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        jwt_service.verify_token.side_effect = [None, payload]
        
        result = await auth_backend.load_access_token("api.token.here")
        
        assert result is not None
        assert result.client_id == "user123"
        assert jwt_service.verify_token.call_count == 2
    
    @pytest.mark.asyncio
    async def test_load_access_token_user_id_fallback(self, auth_backend, jwt_service):
        """Test using user_id field when sub is not present"""
        payload = {
            "user_id": "user123",  # Using user_id instead of sub
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        jwt_service.verify_token.return_value = payload
        
        result = await auth_backend.load_access_token("valid.token.here")
        
        assert result is not None
        assert result.client_id == "user123"
    
    @pytest.mark.asyncio
    async def test_load_access_token_invalid(self, auth_backend, jwt_service):
        """Test loading invalid token returns None"""
        jwt_service.verify_token.return_value = None
        
        result = await auth_backend.load_access_token("invalid.token")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_load_access_token_missing_user_id(self, auth_backend, jwt_service):
        """Test token without user ID returns None"""
        payload = {
            "email": "test@example.com",  # No sub or user_id
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        jwt_service.verify_token.return_value = payload
        
        result = await auth_backend.load_access_token("token.without.userid")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_load_access_token_string_scopes(self, auth_backend, jwt_service):
        """Test handling scopes as string instead of array"""
        payload = {
            "sub": "user123",
            "scopes": "read write admin",  # String instead of array
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        jwt_service.verify_token.return_value = payload
        
        result = await auth_backend.load_access_token("token.with.string.scopes")
        
        assert result is not None
        assert "read" in result.scopes
        assert "write" in result.scopes
        assert "admin" in result.scopes
    
    @pytest.mark.asyncio
    async def test_get_user_context_from_repository(self, auth_backend, user_repository):
        """Test getting user context from repository"""
        # Mock user entity
        user = Mock(spec=User)
        user.id = UserId("user123")
        user.email = "test@example.com"
        user.username = "testuser"
        user.roles = [UserRole.ADMIN, UserRole.USER]
        
        user_repository.find_by_id.return_value = user
        
        context = await auth_backend._get_user_context("user123")
        
        assert context is not None
        assert context.user_id == "user123"
        assert context.email == "test@example.com"
        assert context.username == "testuser"
        assert "UserRole.ADMIN" in context.roles
        assert "UserRole.USER" in context.roles
    
    @pytest.mark.asyncio
    async def test_get_user_context_cache(self, auth_backend, user_repository):
        """Test user context caching"""
        # Mock user entity
        user = Mock(spec=User)
        user.id = UserId("user123")
        user.email = "test@example.com"
        user.username = "testuser"
        user.roles = [UserRole.USER]
        
        user_repository.find_by_id.return_value = user
        
        # First call should hit repository
        context1 = await auth_backend._get_user_context("user123")
        assert user_repository.find_by_id.call_count == 1
        
        # Second call should use cache
        context2 = await auth_backend._get_user_context("user123")
        assert user_repository.find_by_id.call_count == 1  # Still 1
        assert context1 == context2
    
    @pytest.mark.asyncio
    async def test_get_user_context_cache_expiry(self, auth_backend, user_repository):
        """Test user context cache expiration"""
        user = Mock(spec=User)
        user.id = UserId("user123")
        user.email = "test@example.com"
        user.username = "testuser"
        user.roles = [UserRole.USER]
        
        user_repository.find_by_id.return_value = user
        
        # First call
        await auth_backend._get_user_context("user123")
        
        # Simulate cache expiry
        auth_backend._cache_timestamps["user123"] = time.time() - 400  # Expired
        
        # Should hit repository again
        await auth_backend._get_user_context("user123")
        assert user_repository.find_by_id.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_user_context_fallback(self, auth_backend):
        """Test user context fallback when repository is None"""
        auth_backend._user_repository = None
        
        context = await auth_backend._get_user_context("user123")
        
        assert context is not None
        assert context.user_id == "user123"
        assert context.email == ""
        assert context.username == "user123"
        assert context.roles == ["user"]
        assert context.scopes == []
    
    @pytest.mark.asyncio
    async def test_get_user_context_repository_error(self, auth_backend, user_repository):
        """Test handling repository errors gracefully"""
        user_repository.find_by_id.side_effect = Exception("DB error")
        
        context = await auth_backend._get_user_context("user123")
        
        # Should return fallback context
        assert context is not None
        assert context.user_id == "user123"
        assert context.roles == ["user"]
    
    def test_map_roles_to_scopes(self, auth_backend):
        """Test mapping user roles to MCP scopes"""
        # Admin gets all scopes
        scopes = auth_backend._map_roles_to_scopes(["admin"])
        assert "mcp:access" in scopes
        assert "mcp:admin" in scopes
        assert "mcp:write" in scopes
        assert "mcp:read" in scopes
        
        # Developer gets write and read
        scopes = auth_backend._map_roles_to_scopes(["developer"])
        assert "mcp:access" in scopes
        assert "mcp:write" in scopes
        assert "mcp:read" in scopes
        assert "mcp:admin" not in scopes
        
        # User gets only read
        scopes = auth_backend._map_roles_to_scopes(["user"])
        assert "mcp:access" in scopes
        assert "mcp:read" in scopes
        assert "mcp:write" not in scopes
        assert "mcp:admin" not in scopes
        
        # Multiple roles
        scopes = auth_backend._map_roles_to_scopes(["user", "developer"])
        assert "mcp:access" in scopes
        assert "mcp:read" in scopes
        assert "mcp:write" in scopes
        
        # Unknown role
        scopes = auth_backend._map_roles_to_scopes(["unknown"])
        assert scopes == ["mcp:access"]  # Only base scope
        
        # Case insensitive
        scopes = auth_backend._map_roles_to_scopes(["ADMIN"])
        assert "mcp:admin" in scopes
    
    def test_get_current_user_id(self, auth_backend):
        """Test extracting user ID without full validation"""
        # Create a test token
        payload = {"sub": "user123"}
        token = jwt.encode(payload, "any-secret", algorithm="HS256")
        
        user_id = auth_backend.get_current_user_id(token)
        assert user_id == "user123"
        
        # Invalid token
        user_id = auth_backend.get_current_user_id("invalid.token")
        assert user_id is None


class TestCreateJWTAuthBackend:
    """Test suite for create_jwt_auth_backend factory function"""
    
    def test_create_without_jwt_secret(self, monkeypatch):
        """Test factory raises error without JWT_SECRET_KEY"""
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        
        with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable not set"):
            create_jwt_auth_backend()
    
    def test_create_with_defaults(self, monkeypatch):
        """Test factory creates backend with defaults"""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
        
        backend = create_jwt_auth_backend()
        
        assert isinstance(backend, JWTAuthBackend)
        assert backend._jwt_service is not None
        assert backend._user_repository is None
        assert backend._auth_service is None
    
    def test_create_with_database(self, monkeypatch):
        """Test factory creates backend with database session"""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
        
        mock_session_factory = Mock()
        backend = create_jwt_auth_backend(
            database_session_factory=mock_session_factory,
            required_scopes=["custom:scope"]
        )
        
        assert isinstance(backend, JWTAuthBackend)
        assert backend._user_repository is not None
    
    @pytest.mark.asyncio
    async def test_integration_full_flow(self, monkeypatch):
        """Test full integration flow with real JWT tokens"""
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
        
        # Create backend
        backend = create_jwt_auth_backend()
        
        # Create a real JWT token
        jwt_service = JWTService(secret_key="test-secret-key")
        token = jwt_service.create_access_token(
            user_id="user123",
            email="test@example.com",
            roles=["developer"],
            additional_claims={"scopes": ["custom:read"]}
        )
        
        # Load and validate token
        access_token = await backend.load_access_token(token)
        
        assert access_token is not None
        assert access_token.client_id == "user123"
        assert "mcp:access" in access_token.scopes
        assert "mcp:write" in access_token.scopes
        assert "mcp:read" in access_token.scopes
        assert "custom:read" in access_token.scopes