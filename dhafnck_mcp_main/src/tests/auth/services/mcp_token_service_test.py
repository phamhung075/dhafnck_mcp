"""
Test cases for MCP token generation service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
import time
import hashlib

from fastmcp.auth.services.mcp_token_service import MCPTokenService, MCPToken
from fastmcp.auth.infrastructure.supabase_auth import SupabaseAuthService


class TestMCPTokenService:
    """Test cases for MCPTokenService class."""
    
    @pytest.fixture
    def mock_supabase_auth(self):
        """Create mock Supabase auth service."""
        auth = Mock(spec=SupabaseAuthService)
        auth.verify_token = AsyncMock()
        return auth
    
    @pytest.fixture
    def mock_supabase_user(self):
        """Create mock Supabase user."""
        user = Mock()
        user.id = "test-user-123"
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mcp_token_service(self, mock_supabase_auth):
        """Create MCP token service with mocked dependencies."""
        with patch('fastmcp.auth.services.mcp_token_service.SupabaseAuthService', return_value=mock_supabase_auth):
            service = MCPTokenService()
            return service
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_supabase_success(self, mcp_token_service, mock_supabase_auth, mock_supabase_user):
        """Test successful MCP token generation from Supabase token."""
        # Mock successful Supabase verification
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = mock_supabase_user
        mock_supabase_auth.verify_token.return_value = auth_result
        
        # Generate token
        result = await mcp_token_service.generate_mcp_token_from_supabase("supabase-token", expires_in_hours=24)
        
        # Verify result
        assert isinstance(result, MCPToken)
        assert result.token.startswith("mcp_")
        assert len(result.token) == 52  # mcp_ + 48 chars
        assert result.user_id == "test-user-123"
        assert result.source_type == "supabase"
        assert result.metadata["email"] == "test@example.com"
        assert result.metadata["source_token_type"] == "supabase_jwt"
        assert "generated_at" in result.metadata
        
        # Verify expiration
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        assert abs((result.expires_at - expected_expiry).total_seconds()) < 5
        
        # Verify caching
        assert result.token in mcp_token_service._token_cache
        assert mcp_token_service._user_tokens["test-user-123"] == result.token
        
        mock_supabase_auth.verify_token.assert_called_once_with("supabase-token")
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_supabase_user_dict(self, mcp_token_service, mock_supabase_auth):
        """Test token generation with user data as dictionary."""
        # Mock successful verification with dict user
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = {"id": "dict-user-456", "email": "dict@example.com"}
        mock_supabase_auth.verify_token.return_value = auth_result
        
        result = await mcp_token_service.generate_mcp_token_from_supabase("supabase-token")
        
        assert result.user_id == "dict-user-456"
        assert result.metadata["email"] == "dict@example.com"
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_supabase_invalid_token(self, mcp_token_service, mock_supabase_auth):
        """Test token generation with invalid Supabase token."""
        # Mock failed verification
        auth_result = Mock()
        auth_result.success = False
        auth_result.user = None
        mock_supabase_auth.verify_token.return_value = auth_result
        
        with pytest.raises(ValueError, match="Invalid Supabase token"):
            await mcp_token_service.generate_mcp_token_from_supabase("invalid-token")
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_supabase_no_user_id(self, mcp_token_service, mock_supabase_auth):
        """Test token generation when user ID cannot be extracted."""
        # Mock successful verification but no user ID
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = Mock()
        auth_result.user.id = None
        auth_result.user.get = Mock(return_value=None)
        mock_supabase_auth.verify_token.return_value = auth_result
        
        with pytest.raises(ValueError, match="Unable to extract user ID"):
            await mcp_token_service.generate_mcp_token_from_supabase("token")
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_supabase_replaces_old_token(self, mcp_token_service, mock_supabase_auth, mock_supabase_user):
        """Test that generating a new token invalidates the old one."""
        # Mock successful verification
        auth_result = Mock()
        auth_result.success = True
        auth_result.user = mock_supabase_user
        mock_supabase_auth.verify_token.return_value = auth_result
        
        # Generate first token
        token1 = await mcp_token_service.generate_mcp_token_from_supabase("token1")
        assert token1.token in mcp_token_service._token_cache
        
        # Generate second token for same user
        token2 = await mcp_token_service.generate_mcp_token_from_supabase("token2")
        
        # Verify old token is removed
        assert token1.token not in mcp_token_service._token_cache
        assert token2.token in mcp_token_service._token_cache
        assert mcp_token_service._user_tokens["test-user-123"] == token2.token
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_user_id(self, mcp_token_service):
        """Test direct MCP token generation from user ID."""
        user_id = "direct-user-789"
        email = "direct@example.com"
        metadata = {"role": "admin", "source": "api"}
        
        result = await mcp_token_service.generate_mcp_token_from_user_id(
            user_id, email, expires_in_hours=12, metadata=metadata
        )
        
        # Verify result
        assert isinstance(result, MCPToken)
        assert result.token.startswith("mcp_")
        assert result.user_id == user_id
        assert result.source_type == "user_authenticated"
        assert result.metadata["email"] == email
        assert result.metadata["source_token_type"] == "user_authenticated"
        assert result.metadata["role"] == "admin"
        assert result.metadata["source"] == "api"
        
        # Verify expiration
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=12)
        assert abs((result.expires_at - expected_expiry).total_seconds()) < 5
        
        # Verify caching
        assert result.token in mcp_token_service._token_cache
        assert mcp_token_service._user_tokens[user_id] == result.token
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_from_user_id_no_metadata(self, mcp_token_service):
        """Test token generation without additional metadata."""
        result = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com"
        )
        
        assert result.metadata["email"] == "user@example.com"
        assert result.metadata["source_token_type"] == "user_authenticated"
        assert "generated_at" in result.metadata
        assert len(result.metadata) == 3  # Only default fields
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_valid(self, mcp_token_service):
        """Test validation of valid MCP token."""
        # Generate a token
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com", expires_in_hours=1
        )
        
        # Validate it
        validated = await mcp_token_service.validate_mcp_token(token_obj.token)
        
        assert validated is not None
        assert validated.token == token_obj.token
        assert validated.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_expired(self, mcp_token_service):
        """Test validation of expired MCP token."""
        # Generate a token that's already expired
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com", expires_in_hours=0
        )
        
        # Manually set expiration to past
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Validate it
        validated = await mcp_token_service.validate_mcp_token(token_obj.token)
        
        assert validated is None
        assert token_obj.token not in mcp_token_service._token_cache
        assert "user-123" not in mcp_token_service._user_tokens
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_not_found(self, mcp_token_service):
        """Test validation of non-existent token."""
        validated = await mcp_token_service.validate_mcp_token("non-existent-token")
        assert validated is None
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_no_expiry(self, mcp_token_service):
        """Test validation of token without expiry."""
        # Generate token and remove expiry
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com"
        )
        token_obj.expires_at = None
        
        # Validate it
        validated = await mcp_token_service.validate_mcp_token(token_obj.token)
        
        assert validated is not None
        assert validated.token == token_obj.token
    
    @pytest.mark.asyncio
    async def test_revoke_mcp_token_success(self, mcp_token_service):
        """Test successful token revocation."""
        # Generate a token
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com"
        )
        
        # Revoke it
        result = await mcp_token_service.revoke_mcp_token(token_obj.token)
        
        assert result is True
        assert token_obj.token not in mcp_token_service._token_cache
        assert "user-123" not in mcp_token_service._user_tokens
    
    @pytest.mark.asyncio
    async def test_revoke_mcp_token_not_found(self, mcp_token_service):
        """Test revocation of non-existent token."""
        result = await mcp_token_service.revoke_mcp_token("non-existent-token")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_single_token(self, mcp_token_service):
        """Test revoking all tokens for a user with single token."""
        # Generate a token
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com"
        )
        
        # Revoke user tokens
        result = await mcp_token_service.revoke_user_tokens("user-123")
        
        assert result is True
        assert token_obj.token not in mcp_token_service._token_cache
        assert "user-123" not in mcp_token_service._user_tokens
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_orphaned_tokens(self, mcp_token_service):
        """Test revoking orphaned tokens (not in user mapping)."""
        # Generate a token
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com"
        )
        
        # Manually create orphaned token
        orphaned_token = MCPToken(
            token="orphaned-token",
            user_id="user-123",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            source_type="test",
            metadata={}
        )
        mcp_token_service._token_cache["orphaned-token"] = orphaned_token
        
        # Revoke user tokens
        result = await mcp_token_service.revoke_user_tokens("user-123")
        
        assert result is True
        assert token_obj.token not in mcp_token_service._token_cache
        assert "orphaned-token" not in mcp_token_service._token_cache
        assert "user-123" not in mcp_token_service._user_tokens
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_no_tokens(self, mcp_token_service):
        """Test revoking tokens for user with no tokens."""
        result = await mcp_token_service.revoke_user_tokens("user-with-no-tokens")
        assert result is False
    
    def test_get_token_stats(self, mcp_token_service):
        """Test getting token statistics."""
        # Manually create tokens with different states
        now = datetime.now(timezone.utc)
        
        # Active token
        active_token = MCPToken(
            token="active-token",
            user_id="user-1",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            source_type="test",
            metadata={}
        )
        mcp_token_service._token_cache["active-token"] = active_token
        mcp_token_service._user_tokens["user-1"] = "active-token"
        
        # Expired token
        expired_token = MCPToken(
            token="expired-token",
            user_id="user-2",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
            source_type="test",
            metadata={}
        )
        mcp_token_service._token_cache["expired-token"] = expired_token
        mcp_token_service._user_tokens["user-2"] = "expired-token"
        
        # Token without expiry
        no_expiry_token = MCPToken(
            token="no-expiry-token",
            user_id="user-3",
            created_at=now,
            expires_at=None,
            source_type="test",
            metadata={}
        )
        mcp_token_service._token_cache["no-expiry-token"] = no_expiry_token
        mcp_token_service._user_tokens["user-3"] = "no-expiry-token"
        
        # Get stats
        stats = mcp_token_service.get_token_stats()
        
        assert stats["total_tokens"] == 3
        assert stats["active_tokens"] == 2  # active + no-expiry
        assert stats["expired_tokens"] == 1
        assert stats["unique_users"] == 3
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, mcp_token_service):
        """Test cleanup of expired tokens."""
        now = datetime.now(timezone.utc)
        
        # Create mix of tokens
        # Active token
        active_token = MCPToken(
            token="active-token",
            user_id="user-1",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            source_type="test",
            metadata={}
        )
        mcp_token_service._token_cache["active-token"] = active_token
        mcp_token_service._user_tokens["user-1"] = "active-token"
        
        # Expired tokens
        for i in range(3):
            expired_token = MCPToken(
                token=f"expired-token-{i}",
                user_id=f"user-{i+2}",
                created_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
                source_type="test",
                metadata={}
            )
            mcp_token_service._token_cache[f"expired-token-{i}"] = expired_token
            mcp_token_service._user_tokens[f"user-{i+2}"] = f"expired-token-{i}"
        
        # Run cleanup
        cleaned = await mcp_token_service.cleanup_expired_tokens()
        
        assert cleaned == 3
        assert len(mcp_token_service._token_cache) == 1
        assert "active-token" in mcp_token_service._token_cache
        assert len(mcp_token_service._user_tokens) == 1
        assert "user-1" in mcp_token_service._user_tokens
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_none_expired(self, mcp_token_service):
        """Test cleanup when no tokens are expired."""
        # Generate active token
        await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "user@example.com", expires_in_hours=24
        )
        
        cleaned = await mcp_token_service.cleanup_expired_tokens()
        
        assert cleaned == 0
        assert len(mcp_token_service._token_cache) == 1
    
    def test_generate_secure_token_format(self, mcp_token_service):
        """Test secure token generation format."""
        with patch('time.time', return_value=1234567890):
            with patch('secrets.token_bytes', return_value=b'test-random-bytes'):
                token = mcp_token_service._generate_secure_token("user-123")
                
                assert token.startswith("mcp_")
                assert len(token) == 52  # mcp_ + 48 chars
                
                # Verify it's a valid hex string after prefix
                token_hex = token[4:]
                try:
                    int(token_hex, 16)
                except ValueError:
                    pytest.fail("Token is not valid hexadecimal")
    
    def test_generate_secure_token_uniqueness(self, mcp_token_service):
        """Test that generated tokens are unique."""
        tokens = set()
        for i in range(100):
            token = mcp_token_service._generate_secure_token(f"user-{i}")
            tokens.add(token)
        
        assert len(tokens) == 100  # All tokens should be unique
    
    def test_remove_token_from_cache(self, mcp_token_service):
        """Test internal cache removal function."""
        # Create token
        token_obj = MCPToken(
            token="test-token",
            user_id="user-123",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            source_type="test",
            metadata={}
        )
        
        # Add to caches
        mcp_token_service._token_cache["test-token"] = token_obj
        mcp_token_service._user_tokens["user-123"] = "test-token"
        
        # Remove token
        mcp_token_service._remove_token_from_cache("test-token")
        
        assert "test-token" not in mcp_token_service._token_cache
        assert "user-123" not in mcp_token_service._user_tokens
    
    def test_remove_token_from_cache_mismatch(self, mcp_token_service):
        """Test cache removal when user mapping doesn't match."""
        # Create token
        token_obj = MCPToken(
            token="test-token",
            user_id="user-123",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            source_type="test",
            metadata={}
        )
        
        # Add to token cache
        mcp_token_service._token_cache["test-token"] = token_obj
        
        # Add different token to user mapping
        mcp_token_service._user_tokens["user-123"] = "different-token"
        
        # Remove token
        mcp_token_service._remove_token_from_cache("test-token")
        
        assert "test-token" not in mcp_token_service._token_cache
        assert mcp_token_service._user_tokens["user-123"] == "different-token"  # Should not be removed


class TestLogging:
    """Test cases for logging behavior."""
    
    @pytest.mark.asyncio
    async def test_initialization_logging(self):
        """Test initialization logging."""
        with patch('fastmcp.auth.services.mcp_token_service.SupabaseAuthService'):
            with patch('fastmcp.auth.services.mcp_token_service.logger') as mock_logger:
                MCPTokenService()
                mock_logger.info.assert_called_with("MCP Token Service initialized")
    
    @pytest.mark.asyncio
    async def test_token_generation_logging(self, mcp_token_service):
        """Test token generation logging."""
        with patch('fastmcp.auth.services.mcp_token_service.logger') as mock_logger:
            await mcp_token_service.generate_mcp_token_from_user_id(
                "user-123", "test@example.com", expires_in_hours=12
            )
            
            mock_logger.info.assert_called_with(
                "Generated MCP token for user test@example.com (expires in 12h)"
            )
    
    @pytest.mark.asyncio
    async def test_validation_logging(self, mcp_token_service):
        """Test token validation logging."""
        # Generate token
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "test@example.com"
        )
        
        with patch('fastmcp.auth.services.mcp_token_service.logger') as mock_logger:
            # Valid token
            await mcp_token_service.validate_mcp_token(token_obj.token)
            mock_logger.debug.assert_called_with("MCP token validated for user user-123")
            
            # Non-existent token
            await mcp_token_service.validate_mcp_token("non-existent")
            mock_logger.debug.assert_called_with("MCP token not found in cache")
            
            # Expired token
            token_obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            await mcp_token_service.validate_mcp_token(token_obj.token)
            mock_logger.debug.assert_called_with("MCP token expired for user user-123")
    
    @pytest.mark.asyncio
    async def test_revocation_logging(self, mcp_token_service):
        """Test token revocation logging."""
        # Generate token
        token_obj = await mcp_token_service.generate_mcp_token_from_user_id(
            "user-123", "test@example.com"
        )
        
        with patch('fastmcp.auth.services.mcp_token_service.logger') as mock_logger:
            # Revoke single token
            await mcp_token_service.revoke_mcp_token(token_obj.token)
            mock_logger.info.assert_called_with("Revoked MCP token for user user-123")
            
            # Generate new token for user revocation test
            await mcp_token_service.generate_mcp_token_from_user_id(
                "user-456", "user456@example.com"
            )
            
            # Revoke user tokens
            await mcp_token_service.revoke_user_tokens("user-456")
            mock_logger.info.assert_called_with("Revoked all MCP tokens for user user-456")
    
    @pytest.mark.asyncio
    async def test_cleanup_logging(self, mcp_token_service):
        """Test cleanup logging."""
        # Create expired tokens
        now = datetime.now(timezone.utc)
        for i in range(3):
            expired_token = MCPToken(
                token=f"expired-{i}",
                user_id=f"user-{i}",
                created_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
                source_type="test",
                metadata={}
            )
            mcp_token_service._token_cache[f"expired-{i}"] = expired_token
        
        with patch('fastmcp.auth.services.mcp_token_service.logger') as mock_logger:
            await mcp_token_service.cleanup_expired_tokens()
            mock_logger.info.assert_called_with("Cleaned up 3 expired MCP tokens")