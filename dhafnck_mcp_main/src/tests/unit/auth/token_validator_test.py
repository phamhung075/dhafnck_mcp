"""
Test cases for token validator with rate limiting.
"""

import pytest
import time
from collections import deque
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, AsyncMock, patch

from fastmcp.auth.token_validator import (
    TokenValidator, TokenValidationError, RateLimitError,
    RateLimitConfig
)
from fastmcp.auth.supabase_client import TokenInfo


# Module-level fixtures for all test classes
@pytest.fixture
def mock_supabase_client():
    """Create mock Supabase client."""
    client = Mock()
    client.validate_token = AsyncMock()
    client.log_security_event = AsyncMock()
    client.revoke_token = AsyncMock()
    client._hash_token = Mock(side_effect=lambda token: f"hash_{token}")
    return client

@pytest.fixture
def mock_token_info():
    """Create mock token info."""
    return TokenInfo(
        token_hash="hash_test-token",
        user_id="test-user-123",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        usage_count=5,
        last_used=datetime.now(UTC)
    )

@pytest.fixture
def mock_mcp_token_info():
    """Create mock MCP token info."""
    from fastmcp.auth.services.mcp_token_service import MCPToken
    return MCPToken(
        token="mcp_test123",
        user_id="mcp-user-456",
        email="test@example.com",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        metadata={},
        is_active=True
    )

@pytest.fixture
def rate_limit_config():
    """Create custom rate limit config."""
    return RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        burst_limit=5,
        window_size=60
    )

@pytest.fixture
def token_validator(mock_supabase_client, rate_limit_config):
    """Create token validator with mocked dependencies."""
    with patch('fastmcp.auth.token_validator.SupabaseTokenClient', return_value=mock_supabase_client):
        validator = TokenValidator(rate_limit_config)
        return validator


class TestTokenValidator:
    """Test cases for TokenValidator class."""
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, token_validator, mock_supabase_client, mock_token_info):
        """Test successful token validation."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        result = await token_validator.validate_token("test-token", {"source": "test"})
        
        assert result == mock_token_info
        mock_supabase_client.validate_token.assert_called_once_with("test-token")
        mock_supabase_client.log_security_event.assert_called_once_with(
            "token_validated",
            "hash_test-token",
            {
                "user_id": "test-user-123",
                "client_info": {"source": "test"},
                "usage_count": 5
            }
        )
    
    @pytest.mark.asyncio
    async def test_validate_token_no_token(self, token_validator):
        """Test validation with no token provided."""
        with pytest.raises(TokenValidationError, match="Token is required"):
            await token_validator.validate_token("")
        
        with pytest.raises(TokenValidationError, match="Token is required"):
            await token_validator.validate_token(None)
    
    @pytest.mark.asyncio
    async def test_validate_token_with_bearer_prefix(self, token_validator, mock_supabase_client, mock_token_info):
        """Test validation with Bearer prefix stripping."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        result = await token_validator.validate_token("Bearer test-token")
        
        assert result == mock_token_info
        mock_supabase_client.validate_token.assert_called_once_with("test-token")
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, token_validator, mock_supabase_client):
        """Test validation with invalid token."""
        mock_supabase_client.validate_token.return_value = None
        
        with pytest.raises(TokenValidationError, match="Invalid or expired token"):
            await token_validator.validate_token("invalid-token")
        
        # Check failed attempt was logged
        mock_supabase_client.log_security_event.assert_called()
        call_args = mock_supabase_client.log_security_event.call_args[0]
        assert call_args[0] == "validation_failed"
        assert call_args[2]["reason"] == "invalid_token"
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_success(self, token_validator, mock_supabase_client, mock_mcp_token_info, mock_token_info):
        """Test successful MCP token validation."""
        # Mock MCP token service
        mock_mcp_service = Mock()
        mock_mcp_service.validate_mcp_token = AsyncMock(return_value=mock_mcp_token_info)
        
        with patch('fastmcp.auth.token_validator.mcp_token_service', mock_mcp_service):
            # Supabase validation should not be called for MCP tokens
            mock_supabase_client.validate_token.return_value = None
            
            result = await token_validator.validate_token("mcp_test123")
            
            assert result.user_id == "mcp-user-456"
            assert result.token_hash == "hash_mcp_test123"
            mock_mcp_service.validate_mcp_token.assert_called_once_with("mcp_test123")
            mock_supabase_client.validate_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_validate_mcp_token_fallback_to_supabase(self, token_validator, mock_supabase_client, mock_token_info):
        """Test MCP token validation falls back to Supabase."""
        # Mock MCP service failure
        mock_mcp_service = Mock()
        mock_mcp_service.validate_mcp_token = AsyncMock(return_value=None)
        
        with patch('fastmcp.auth.token_validator.mcp_token_service', mock_mcp_service):
            mock_supabase_client.validate_token.return_value = mock_token_info
            
            result = await token_validator.validate_token("mcp_invalid")
            
            assert result == mock_token_info
            mock_mcp_service.validate_mcp_token.assert_called_once()
            mock_supabase_client.validate_token.assert_called_once_with("mcp_invalid")
    
    @pytest.mark.asyncio
    async def test_token_caching(self, token_validator, mock_supabase_client, mock_token_info):
        """Test token caching functionality."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # First validation - should hit Supabase
        result1 = await token_validator.validate_token("test-token")
        assert mock_supabase_client.validate_token.call_count == 1
        
        # Second validation - should use cache
        result2 = await token_validator.validate_token("test-token")
        assert mock_supabase_client.validate_token.call_count == 1  # Not called again
        assert result2 == result1
    
    @pytest.mark.asyncio
    async def test_token_cache_expiry(self, token_validator, mock_supabase_client, mock_token_info):
        """Test token cache expiry after TTL."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # First validation
        await token_validator.validate_token("test-token")
        assert mock_supabase_client.validate_token.call_count == 1
        
        # Mock time passing beyond cache TTL
        with patch('time.time', return_value=time.time() + 400):  # 400 seconds later
            await token_validator.validate_token("test-token")
            assert mock_supabase_client.validate_token.call_count == 2  # Called again
    
    @pytest.mark.asyncio
    async def test_rate_limiting_per_minute(self, token_validator, mock_supabase_client, mock_token_info):
        """Test per-minute rate limiting."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # Make requests up to the limit
        for i in range(10):  # rate_limit_config.requests_per_minute
            await token_validator.validate_token("test-token")
        
        # Next request should exceed rate limit
        with pytest.raises(RateLimitError, match="Rate limit exceeded.*requests per minute"):
            await token_validator.validate_token("test-token")
        
        # Check failed attempt was logged
        mock_supabase_client.log_security_event.assert_called()
        call_args = mock_supabase_client.log_security_event.call_args[0]
        assert call_args[0] == "validation_failed"
        assert call_args[2]["reason"] == "rate_limit_exceeded"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_burst(self, token_validator, mock_supabase_client, mock_token_info):
        """Test burst rate limiting."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # Make rapid requests up to burst limit
        for i in range(5):  # rate_limit_config.burst_limit
            await token_validator.validate_token("test-token")
        
        # Next request should exceed burst limit
        with pytest.raises(RateLimitError, match="Burst limit exceeded.*requests per 10 seconds"):
            await token_validator.validate_token("test-token")
    
    @pytest.mark.asyncio
    async def test_rate_limiting_cleanup(self, token_validator, mock_supabase_client, mock_token_info):
        """Test that old rate limit entries are cleaned up."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # Add old requests to rate limit
        token_hash = "hash_test-token"
        old_time = time.time() - 3700  # More than 1 hour old
        token_validator._rate_limits[token_hash].extend([old_time, old_time, old_time])
        
        # Make a new request
        await token_validator.validate_token("test-token")
        
        # Old requests should be removed
        requests = token_validator._rate_limits[token_hash]
        assert all(req_time > old_time for req_time in requests)
    
    @pytest.mark.asyncio
    async def test_failed_attempts_logging(self, token_validator, mock_supabase_client):
        """Test failed attempt logging and alerting."""
        mock_supabase_client.validate_token.return_value = None
        
        # Make multiple failed attempts
        for i in range(5):
            with pytest.raises(TokenValidationError):
                await token_validator.validate_token("bad-token")
        
        # Check security event was logged with high failure count
        last_call = mock_supabase_client.log_security_event.call_args_list[-1]
        assert last_call[0][2]["failure_count"] == 5
    
    @pytest.mark.asyncio
    async def test_failed_attempts_cleanup(self, token_validator, mock_supabase_client):
        """Test that old failed attempts are cleaned up."""
        mock_supabase_client.validate_token.return_value = None
        
        # Add old failed attempts
        token_hash = "hash_bad-token"
        old_time = time.time() - 3700  # More than 1 hour old
        token_validator._failed_attempts[token_hash].extend([old_time, old_time])
        
        # Make a new failed attempt
        with pytest.raises(TokenValidationError):
            await token_validator.validate_token("bad-token")
        
        # Old attempts should be removed
        failures = token_validator._failed_attempts[token_hash]
        assert len(failures) == 1  # Only the new failure
    
    @pytest.mark.asyncio
    async def test_revoke_token_success(self, token_validator, mock_supabase_client):
        """Test successful token revocation."""
        mock_supabase_client.revoke_token.return_value = True
        
        # Add token to cache first
        token_hash = "hash_test-token"
        mock_token_info = Mock()
        token_validator._token_cache[token_hash] = (mock_token_info, time.time())
        
        result = await token_validator.revoke_token("test-token")
        
        assert result is True
        assert token_hash not in token_validator._token_cache
        mock_supabase_client.revoke_token.assert_called_once_with("test-token")
        mock_supabase_client.log_security_event.assert_called_once_with(
            "token_revoked",
            token_hash,
            {"revoked_at": pytest.Approximately(datetime.now(UTC).isoformat(), abs=timedelta(seconds=5))}
        )
    
    @pytest.mark.asyncio
    async def test_revoke_token_failure(self, token_validator, mock_supabase_client):
        """Test failed token revocation."""
        mock_supabase_client.revoke_token.return_value = False
        
        result = await token_validator.revoke_token("test-token")
        
        assert result is False
        # Security event should not be logged for failed revocation
        mock_supabase_client.log_security_event.assert_not_called()
    
    def test_get_rate_limit_status(self, token_validator):
        """Test getting rate limit status."""
        token_hash = "hash_test-token"
        current_time = time.time()
        
        # Add some requests
        token_validator._rate_limits[token_hash].extend([
            current_time - 30,  # 30 seconds ago
            current_time - 20,  # 20 seconds ago
            current_time - 10,  # 10 seconds ago
            current_time - 1800,  # 30 minutes ago
            current_time - 7200,  # 2 hours ago (should be ignored)
        ])
        
        status = token_validator.get_rate_limit_status("test-token")
        
        assert status["requests_per_minute"] == 3  # Only last 3 within minute
        assert status["minute_limit"] == 10
        assert status["requests_per_hour"] == 4  # Last 4 within hour
        assert status["hour_limit"] == 100
        assert status["remaining_minute"] == 7
        assert status["remaining_hour"] == 96
    
    def test_clear_cache(self, token_validator):
        """Test cache clearing."""
        # Add items to cache
        token_validator._token_cache["hash1"] = (Mock(), time.time())
        token_validator._token_cache["hash2"] = (Mock(), time.time())
        
        token_validator.clear_cache()
        
        assert len(token_validator._token_cache) == 0
    
    def test_get_cache_stats(self, token_validator):
        """Test getting cache statistics."""
        # Add test data
        token_validator._token_cache["hash1"] = (Mock(), time.time())
        token_validator._rate_limits["hash2"].append(time.time())
        token_validator._failed_attempts["hash3"].append(time.time())
        
        stats = token_validator.get_cache_stats()
        
        assert stats["cached_tokens"] == 1
        assert stats["rate_limited_tokens"] == 1
        assert stats["failed_attempt_records"] == 1
    
    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, token_validator, mock_supabase_client):
        """Test handling of unexpected errors."""
        mock_supabase_client.validate_token.side_effect = Exception("Unexpected error")
        
        with pytest.raises(TokenValidationError, match="Token validation failed"):
            await token_validator.validate_token("test-token")
        
        # Check failed attempt was logged
        mock_supabase_client.log_security_event.assert_called()
        call_args = mock_supabase_client.log_security_event.call_args[0]
        assert call_args[0] == "validation_failed"
        assert call_args[2]["reason"] == "validation_error"


class TestRateLimitConfig:
    """Test cases for RateLimitConfig."""
    
    def test_default_config(self):
        """Test default rate limit configuration."""
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 100
        assert config.requests_per_hour == 1000
        assert config.burst_limit == 20
        assert config.window_size == 60
    
    def test_custom_config(self):
        """Test custom rate limit configuration."""
        config = RateLimitConfig(
            requests_per_minute=50,
            requests_per_hour=500,
            burst_limit=10,
            window_size=30
        )
        
        assert config.requests_per_minute == 50
        assert config.requests_per_hour == 500
        assert config.burst_limit == 10
        assert config.window_size == 30


class TestLogging:
    """Test cases for logging behavior."""
    
    @pytest.mark.asyncio
    async def test_initialization_logging(self):
        """Test initialization logging."""
        with patch('fastmcp.auth.token_validator.SupabaseTokenClient'):
            with patch('fastmcp.auth.token_validator.logger') as mock_logger:
                TokenValidator()
                mock_logger.info.assert_called_with(
                    "Token validator initialized with rate limit: 100/min"
                )
    
    @pytest.mark.asyncio
    async def test_cache_hit_logging(self, token_validator, mock_supabase_client, mock_token_info):
        """Test cache hit logging."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # First call to populate cache
        await token_validator.validate_token("test-token")
        
        with patch('fastmcp.auth.token_validator.logger') as mock_logger:
            # Second call should hit cache
            await token_validator.validate_token("test-token")
            mock_logger.debug.assert_called_with("Token found in cache")
    
    @pytest.mark.asyncio
    async def test_mcp_token_logging(self, token_validator, mock_supabase_client, mock_mcp_token_info):
        """Test MCP token validation logging."""
        mock_mcp_service = Mock()
        mock_mcp_service.validate_mcp_token = AsyncMock(return_value=mock_mcp_token_info)
        
        with patch('fastmcp.auth.token_validator.mcp_token_service', mock_mcp_service):
            with patch('fastmcp.auth.token_validator.logger') as mock_logger:
                await token_validator.validate_token("mcp_test123")
                mock_logger.debug.assert_called_with("MCP token validated for user mcp-user-456")
    
    @pytest.mark.asyncio
    async def test_rate_limit_logging(self, token_validator, mock_supabase_client, mock_token_info):
        """Test rate limit logging."""
        mock_supabase_client.validate_token.return_value = mock_token_info
        
        # Fill up rate limit
        for i in range(10):
            await token_validator.validate_token("test-token")
        
        with patch('fastmcp.auth.token_validator.logger') as mock_logger:
            with pytest.raises(RateLimitError):
                await token_validator.validate_token("test-token")
            
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Rate limit exceeded for token" in warning_call
    
    @pytest.mark.asyncio
    async def test_multiple_failures_logging(self, token_validator, mock_supabase_client):
        """Test logging for multiple failed attempts."""
        mock_supabase_client.validate_token.return_value = None
        
        # Make 4 failed attempts
        for i in range(4):
            with pytest.raises(TokenValidationError):
                await token_validator.validate_token("bad-token")
        
        with patch('fastmcp.auth.token_validator.logger') as mock_logger:
            # 5th attempt should trigger warning
            with pytest.raises(TokenValidationError):
                await token_validator.validate_token("bad-token")
            
            mock_logger.warning.assert_called_with(
                "Multiple failed attempts for token: 5 failures in last hour"
            )