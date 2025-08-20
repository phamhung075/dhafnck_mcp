"""
Test for TokenVerifierAdapter that bridges OAuthProvider to TokenVerifier interface.
"""

import pytest
from unittest.mock import AsyncMock, Mock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastmcp.server.http_server import TokenVerifierAdapter
from mcp.server.auth.provider import AccessToken


class TestTokenVerifierAdapter:
    """Test the TokenVerifierAdapter functionality."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock OAuth provider."""
        provider = Mock()
        provider.load_access_token = AsyncMock()
        return provider
    
    @pytest.fixture
    def adapter(self, mock_provider):
        """Create a TokenVerifierAdapter instance."""
        return TokenVerifierAdapter(mock_provider)
    
    @pytest.mark.asyncio
    async def test_verify_token_delegates_to_provider(self, adapter, mock_provider):
        """Test that verify_token delegates to provider's load_access_token."""
        # Setup
        test_token = "test-jwt-token-123"
        expected_access_token = AccessToken(
            token=test_token,
            client_id="test-user",
            scopes=["mcp:read", "mcp:write"],
            expires_at=1234567890
        )
        mock_provider.load_access_token.return_value = expected_access_token
        
        # Execute
        result = await adapter.verify_token(test_token)
        
        # Verify
        assert result == expected_access_token
        mock_provider.load_access_token.assert_called_once_with(test_token)
    
    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_invalid_token(self, adapter, mock_provider):
        """Test that verify_token returns None when provider returns None."""
        # Setup
        test_token = "invalid-token"
        mock_provider.load_access_token.return_value = None
        
        # Execute
        result = await adapter.verify_token(test_token)
        
        # Verify
        assert result is None
        mock_provider.load_access_token.assert_called_once_with(test_token)
    
    @pytest.mark.asyncio
    async def test_verify_token_propagates_exceptions(self, adapter, mock_provider):
        """Test that exceptions from provider are propagated."""
        # Setup
        test_token = "error-token"
        mock_provider.load_access_token.side_effect = Exception("Provider error")
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await adapter.verify_token(test_token)
        
        assert str(exc_info.value) == "Provider error"
        mock_provider.load_access_token.assert_called_once_with(test_token)
    
    def test_adapter_stores_provider_reference(self, mock_provider):
        """Test that adapter correctly stores the provider reference."""
        # Execute
        adapter = TokenVerifierAdapter(mock_provider)
        
        # Verify
        assert adapter.provider is mock_provider
    
    @pytest.mark.asyncio
    async def test_adapter_works_with_real_oauth_provider_interface(self):
        """Test that adapter works with a mock that mimics real OAuthProvider."""
        # Create a more realistic mock that mimics OAuthProvider
        class MockOAuthProvider:
            async def load_access_token(self, token: str) -> AccessToken | None:
                if token == "valid-token":
                    return AccessToken(
                        token=token,
                        client_id="user-123",
                        scopes=["mcp:access"],
                        expires_at=9999999999
                    )
                return None
        
        # Setup
        provider = MockOAuthProvider()
        adapter = TokenVerifierAdapter(provider)
        
        # Test valid token
        valid_result = await adapter.verify_token("valid-token")
        assert valid_result is not None
        assert valid_result.client_id == "user-123"
        assert "mcp:access" in valid_result.scopes
        
        # Test invalid token
        invalid_result = await adapter.verify_token("invalid-token")
        assert invalid_result is None