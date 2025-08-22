"""
Test cases for authentication middleware.
"""

import pytest
import os
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from fastmcp.auth.middleware import AuthMiddleware, require_auth, authenticate_request
from fastmcp.auth.token_validator import TokenValidationError, RateLimitError
from fastmcp.auth.supabase_client import TokenInfo


class TestAuthMiddleware:
    """Test cases for AuthMiddleware class."""
    
    @pytest.fixture
    def mock_token_validator(self):
        """Create a mock token validator."""
        validator = Mock()
        validator.validate_token = AsyncMock()
        validator.get_rate_limit_status = Mock()
        validator.revoke_token = AsyncMock()
        validator.get_cache_stats = Mock(return_value={"hits": 10, "misses": 5})
        validator.supabase_client = Mock()
        validator.supabase_client.enabled = True
        return validator
    
    @pytest.fixture
    def mock_token_info(self):
        """Create mock token info."""
        return TokenInfo(
            user_id="test-user-123",
            email="test@example.com",
            token_type="mcp_token",
            expires_at=datetime.now().timestamp() + 3600
        )
    
    @pytest.fixture
    def auth_middleware(self, mock_token_validator):
        """Create auth middleware with mocked dependencies."""
        with patch('fastmcp.auth.middleware.TokenValidator', return_value=mock_token_validator):
            middleware = AuthMiddleware()
            return middleware
    
    def test_init_always_enabled(self):
        """Test that authentication is always enabled."""
        with patch('fastmcp.auth.middleware.TokenValidator'):
            # Test with explicit enabled=False (should still be enabled)
            middleware = AuthMiddleware(enabled=False)
            assert middleware.enabled is True
            
            # Test with enabled=True
            middleware = AuthMiddleware(enabled=True)
            assert middleware.enabled is True
            
            # Test with no argument
            middleware = AuthMiddleware()
            assert middleware.enabled is True
    
    def test_init_mvp_mode(self):
        """Test MVP mode initialization."""
        with patch('fastmcp.auth.middleware.TokenValidator'):
            # Test MVP mode disabled (default)
            with patch.dict(os.environ, {}, clear=True):
                middleware = AuthMiddleware()
                assert middleware.mvp_mode is False
            
            # Test MVP mode enabled
            with patch.dict(os.environ, {"DHAFNCK_MVP_MODE": "true"}):
                middleware = AuthMiddleware()
                assert middleware.mvp_mode is True
            
            # Test MVP mode case insensitive
            with patch.dict(os.environ, {"DHAFNCK_MVP_MODE": "TRUE"}):
                middleware = AuthMiddleware()
                assert middleware.mvp_mode is True
    
    @pytest.mark.asyncio
    async def test_authenticate_request_success(self, auth_middleware, mock_token_info):
        """Test successful authentication."""
        token = "valid-token"
        client_info = {"source": "test"}
        
        auth_middleware.token_validator.validate_token.return_value = mock_token_info
        
        result = await auth_middleware.authenticate_request(token, client_info)
        
        assert result == mock_token_info
        auth_middleware.token_validator.validate_token.assert_called_once_with(token, client_info)
    
    @pytest.mark.asyncio
    async def test_authenticate_request_no_token(self, auth_middleware):
        """Test authentication without token."""
        with pytest.raises(TokenValidationError, match="Authentication token required"):
            await auth_middleware.authenticate_request(None)
    
    @pytest.mark.asyncio
    async def test_authenticate_request_mvp_mode_no_token(self, auth_middleware):
        """Test MVP mode allows requests without tokens."""
        auth_middleware.mvp_mode = True
        
        result = await auth_middleware.authenticate_request(None)
        
        assert result is None
        auth_middleware.token_validator.validate_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_request_mvp_mode_with_token(self, auth_middleware, mock_token_info):
        """Test MVP mode still validates tokens when provided."""
        auth_middleware.mvp_mode = True
        token = "valid-token"
        
        auth_middleware.token_validator.validate_token.return_value = mock_token_info
        
        result = await auth_middleware.authenticate_request(token)
        
        assert result == mock_token_info
        auth_middleware.token_validator.validate_token.assert_called_once_with(token, None)
    
    @pytest.mark.asyncio
    async def test_authenticate_request_validation_error(self, auth_middleware):
        """Test authentication with invalid token."""
        token = "invalid-token"
        error_msg = "Invalid token format"
        
        auth_middleware.token_validator.validate_token.side_effect = TokenValidationError(error_msg)
        
        with pytest.raises(TokenValidationError, match=error_msg):
            await auth_middleware.authenticate_request(token)
    
    @pytest.mark.asyncio
    async def test_authenticate_request_rate_limit_error(self, auth_middleware):
        """Test authentication with rate limit exceeded."""
        token = "valid-token"
        error_msg = "Rate limit exceeded"
        
        auth_middleware.token_validator.validate_token.side_effect = RateLimitError(error_msg)
        
        with pytest.raises(RateLimitError, match=error_msg):
            await auth_middleware.authenticate_request(token)
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_success(self, auth_middleware, mock_token_info):
        """Test require_auth decorator with successful authentication."""
        auth_middleware.token_validator.validate_token.return_value = mock_token_info
        
        call_count = 0
        
        @auth_middleware.require_auth
        async def protected_function(arg1, arg2, **kwargs):
            nonlocal call_count
            call_count += 1
            assert arg1 == "test1"
            assert arg2 == "test2"
            assert kwargs.get('_auth_token_info') == mock_token_info
            return "success"
        
        result = await protected_function("test1", "test2", token="valid-token")
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_failure(self, auth_middleware):
        """Test require_auth decorator with authentication failure."""
        error_msg = "Invalid token"
        auth_middleware.token_validator.validate_token.side_effect = TokenValidationError(error_msg)
        
        @auth_middleware.require_auth
        async def protected_function(**kwargs):
            return "should not reach here"
        
        with pytest.raises(TokenValidationError, match=error_msg):
            await protected_function(token="invalid-token")
    
    def test_extract_token_various_sources(self, auth_middleware):
        """Test token extraction from various sources."""
        # Test token parameter
        kwargs = {"token": "token1"}
        assert auth_middleware._extract_token(kwargs) == "token1"
        
        # Test auth_token parameter
        kwargs = {"auth_token": "token2"}
        assert auth_middleware._extract_token(kwargs) == "token2"
        
        # Test authorization parameter
        kwargs = {"authorization": "token3"}
        assert auth_middleware._extract_token(kwargs) == "token3"
        
        # Test environment variable
        with patch.dict(os.environ, {"DHAFNCK_TOKEN": "env-token"}):
            kwargs = {}
            assert auth_middleware._extract_token(kwargs) == "env-token"
        
        # Test priority (first found wins)
        kwargs = {"token": "token1", "auth_token": "token2"}
        assert auth_middleware._extract_token(kwargs) == "token1"
        
        # Test stripping whitespace
        kwargs = {"token": "  token-with-spaces  "}
        assert auth_middleware._extract_token(kwargs) == "token-with-spaces"
        
        # Test no token found
        kwargs = {}
        assert auth_middleware._extract_token(kwargs) is None
    
    def test_extract_client_info(self, auth_middleware):
        """Test client info extraction."""
        # Mock logger to test timestamp extraction
        mock_handler = Mock()
        mock_formatter = Mock()
        mock_formatter.formatTime = Mock(return_value="2024-01-01 12:00:00")
        mock_handler.formatter = mock_formatter
        
        with patch('fastmcp.auth.middleware.logger') as mock_logger:
            mock_logger.handlers = [mock_handler]
            mock_logger.name = "test"
            mock_logger.makeRecord = Mock(return_value=Mock())
            
            kwargs = {
                "__name__": "test_function",
                "arg1": "value1",
                "arg2": "value2"
            }
            
            client_info = auth_middleware._extract_client_info(kwargs)
            
            assert client_info["function"] == "test_function"
            assert client_info["args_count"] == 3
            assert client_info["timestamp"] == "2024-01-01 12:00:00"
        
        # Test without logger handlers
        with patch('fastmcp.auth.middleware.logger') as mock_logger:
            mock_logger.handlers = []
            
            kwargs = {}
            client_info = auth_middleware._extract_client_info(kwargs)
            
            assert client_info["function"] == "unknown"
            assert client_info["args_count"] == 0
            assert client_info["timestamp"] is None
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, auth_middleware):
        """Test getting rate limit status."""
        token = "test-token"
        mock_status = {
            "requests_remaining": 100,
            "reset_at": "2024-01-01T12:00:00Z"
        }
        
        auth_middleware.token_validator.get_rate_limit_status.return_value = mock_status
        
        status = await auth_middleware.get_rate_limit_status(token)
        
        assert status["enabled"] is True
        assert status["requests_remaining"] == 100
        assert status["reset_at"] == "2024-01-01T12:00:00Z"
        
        auth_middleware.token_validator.get_rate_limit_status.assert_called_once_with(token)
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status_no_validator(self, auth_middleware):
        """Test rate limit status when validator is not available."""
        auth_middleware.token_validator = None
        
        status = await auth_middleware.get_rate_limit_status("token")
        
        assert status["enabled"] is True
        assert status["error"] == "Token validator not available"
    
    @pytest.mark.asyncio
    async def test_revoke_token_success(self, auth_middleware):
        """Test successful token revocation."""
        token = "test-token"
        auth_middleware.token_validator.revoke_token.return_value = True
        
        result = await auth_middleware.revoke_token(token)
        
        assert result is True
        auth_middleware.token_validator.revoke_token.assert_called_once_with(token)
    
    @pytest.mark.asyncio
    async def test_revoke_token_failure(self, auth_middleware):
        """Test failed token revocation."""
        token = "test-token"
        auth_middleware.token_validator.revoke_token.return_value = False
        
        result = await auth_middleware.revoke_token(token)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_revoke_token_no_validator(self, auth_middleware):
        """Test token revocation when validator is not available."""
        auth_middleware.token_validator = None
        
        with patch('fastmcp.auth.middleware.logger') as mock_logger:
            result = await auth_middleware.revoke_token("token")
            
            assert result is False
            mock_logger.error.assert_called_once_with(
                "Cannot revoke token: token validator not available"
            )
    
    def test_get_auth_status(self, auth_middleware):
        """Test getting authentication status."""
        status = auth_middleware.get_auth_status()
        
        assert status["enabled"] is True
        assert status["mvp_mode"] is False
        assert status["supabase_enabled"] is True
        assert status["cache_stats"] == {"hits": 10, "misses": 5}
    
    def test_get_auth_status_mvp_mode(self, auth_middleware):
        """Test getting authentication status in MVP mode."""
        auth_middleware.mvp_mode = True
        
        status = auth_middleware.get_auth_status()
        
        assert status["enabled"] is True
        assert status["mvp_mode"] is True
    
    def test_get_auth_status_no_validator(self, auth_middleware):
        """Test getting authentication status without validator."""
        auth_middleware.token_validator = None
        
        status = auth_middleware.get_auth_status()
        
        assert status["enabled"] is True
        assert status["supabase_enabled"] is False
        assert status["cache_stats"] == {}


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    @pytest.mark.asyncio
    async def test_global_require_auth_decorator(self):
        """Test the global require_auth decorator."""
        with patch('fastmcp.auth.middleware.auth_middleware') as mock_middleware:
            mock_decorator = Mock(return_value=lambda f: f)
            mock_middleware.require_auth = mock_decorator
            
            @require_auth
            async def test_function():
                return "test"
            
            mock_decorator.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_global_authenticate_request(self):
        """Test the global authenticate_request function."""
        token = "test-token"
        client_info = {"source": "test"}
        mock_token_info = TokenInfo(
            user_id="user-123",
            email="test@example.com",
            token_type="mcp_token",
            expires_at=datetime.now().timestamp() + 3600
        )
        
        with patch('fastmcp.auth.middleware.auth_middleware') as mock_middleware:
            mock_middleware.authenticate_request = AsyncMock(return_value=mock_token_info)
            
            result = await authenticate_request(token, client_info)
            
            assert result == mock_token_info
            mock_middleware.authenticate_request.assert_called_once_with(token, client_info)


class TestLogging:
    """Test cases for logging behavior."""
    
    @pytest.mark.asyncio
    async def test_authentication_logging(self):
        """Test that authentication events are logged."""
        with patch('fastmcp.auth.middleware.TokenValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_token_info = TokenInfo(
                user_id="test-user",
                email="test@example.com",
                token_type="mcp_token",
                expires_at=datetime.now().timestamp() + 3600
            )
            mock_validator.validate_token = AsyncMock(return_value=mock_token_info)
            mock_validator_class.return_value = mock_validator
            
            with patch('fastmcp.auth.middleware.logger') as mock_logger:
                middleware = AuthMiddleware()
                
                # Test successful authentication logging
                await middleware.authenticate_request("valid-token")
                mock_logger.debug.assert_called_with("Request authenticated for user: test-user")
                
                # Test MVP mode logging
                middleware.mvp_mode = True
                await middleware.authenticate_request(None)
                mock_logger.debug.assert_called_with("MVP mode: allowing request without token")
    
    @pytest.mark.asyncio
    async def test_decorator_logging(self):
        """Test that decorator logs authentication failures."""
        with patch('fastmcp.auth.middleware.TokenValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_token = AsyncMock(side_effect=TokenValidationError("Invalid"))
            mock_validator_class.return_value = mock_validator
            
            with patch('fastmcp.auth.middleware.logger') as mock_logger:
                middleware = AuthMiddleware()
                
                @middleware.require_auth
                async def test_func(**kwargs):
                    return "success"
                
                with pytest.raises(TokenValidationError):
                    await test_func(token="invalid")
                
                mock_logger.warning.assert_called_with("Authentication failed: Invalid")
    
    def test_initialization_logging(self):
        """Test initialization logging."""
        with patch('fastmcp.auth.middleware.TokenValidator'):
            with patch('fastmcp.auth.middleware.logger') as mock_logger:
                # Test normal mode
                with patch.dict(os.environ, {}, clear=True):
                    AuthMiddleware()
                    mock_logger.info.assert_called_with(
                        "Authentication middleware initialized - authentication always enabled"
                    )
                
                # Test MVP mode
                with patch.dict(os.environ, {"DHAFNCK_MVP_MODE": "true"}):
                    AuthMiddleware()
                    mock_logger.info.assert_called_with(
                        "MVP mode enabled - simplified authentication but auth always enabled"
                    )