"""Test suite for MCP Authentication Configuration module.

Tests the MCP authentication configuration functions including:
- Authentication provider creation
- Default provider selection
- Server configuration
- Environment variable handling
- Edge cases and error conditions
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from fastmcp.server.auth.mcp_auth_config import (
    create_mcp_auth_provider,
    get_default_auth_provider,
    configure_mcp_server_auth,
)


class TestCreateMcpAuthProvider:
    """Test cases for create_mcp_auth_provider function."""

    def test_create_none_provider(self):
        """Test creating no authentication provider."""
        result = create_mcp_auth_provider(auth_type="none")
        assert result is None

    def test_create_env_provider(self):
        """Test creating environment Bearer auth provider."""
        # Test with mock import to avoid dependency issues
        with patch('fastmcp.server.auth.mcp_auth_config.EnvBearerAuthProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            
            result = create_mcp_auth_provider(auth_type="env")
            
            assert result == mock_instance
            mock_provider.assert_called_once_with()

    def test_create_jwt_provider_default(self):
        """Test creating JWT auth provider with defaults."""
        with patch('fastmcp.server.auth.mcp_auth_config.JWTBearerAuthProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            
            result = create_mcp_auth_provider(auth_type="jwt")
            
            assert result == mock_instance
            mock_provider.assert_called_once_with(
                secret_key=None,
                required_scopes=["mcp:access"],
                check_database=True,
            )

    def test_create_jwt_provider_custom(self):
        """Test creating JWT auth provider with custom parameters."""
        with patch('fastmcp.server.auth.mcp_auth_config.JWTBearerAuthProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            
            result = create_mcp_auth_provider(
                auth_type="jwt",
                secret_key="custom-secret",
                required_scopes=["read", "write"],
                check_database=False,
            )
            
            assert result == mock_instance
            mock_provider.assert_called_once_with(
                secret_key="custom-secret",
                required_scopes=["read", "write"],
                check_database=False,
            )

    def test_create_unknown_provider(self):
        """Test creating provider with unknown type."""
        with pytest.raises(ValueError) as exc_info:
            create_mcp_auth_provider(auth_type="unknown")
        
        assert "Unknown auth_type: unknown" in str(exc_info.value)


class TestGetDefaultAuthProvider:
    """Test cases for get_default_auth_provider function."""

    @patch.dict(os.environ, {"DHAFNCK_AUTH_ENABLED": "false"}, clear=True)
    def test_auth_disabled(self):
        """Test when authentication is explicitly disabled."""
        result = get_default_auth_provider()
        assert result is None

    @patch.dict(os.environ, {"MCP_AUTH_TYPE": "none"}, clear=True)
    def test_explicit_none_type(self):
        """Test when auth type is explicitly set to none."""
        result = get_default_auth_provider()
        assert result is None

    @patch.dict(os.environ, {"MCP_AUTH_TYPE": "env"}, clear=True)
    def test_explicit_env_type(self):
        """Test when auth type is explicitly set to env."""
        with patch('fastmcp.server.auth.mcp_auth_config.create_mcp_auth_provider') as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider
            
            result = get_default_auth_provider()
            
            assert result == mock_provider
            mock_create.assert_called_once_with(auth_type="env")

    @patch.dict(os.environ, {"MCP_AUTH_TYPE": "jwt"}, clear=True)
    def test_explicit_jwt_type(self):
        """Test when auth type is explicitly set to jwt."""
        with patch('fastmcp.server.auth.mcp_auth_config.create_mcp_auth_provider') as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider
            
            result = get_default_auth_provider()
            
            assert result == mock_provider
            mock_create.assert_called_once_with(auth_type="jwt")

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "secret"}, clear=True)
    def test_auto_detect_jwt(self):
        """Test auto-detection of JWT when JWT_SECRET_KEY is set."""
        with patch('fastmcp.server.auth.mcp_auth_config.create_mcp_auth_provider') as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider
            
            result = get_default_auth_provider()
            
            assert result == mock_provider
            mock_create.assert_called_once_with(auth_type="jwt")

    @patch.dict(os.environ, {"MCP_BEARER_TOKEN": "token"}, clear=True)
    def test_auto_detect_env(self):
        """Test auto-detection of env auth when MCP_BEARER_TOKEN is set."""
        with patch('fastmcp.server.auth.mcp_auth_config.create_mcp_auth_provider') as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider
            
            result = get_default_auth_provider()
            
            assert result == mock_provider
            mock_create.assert_called_once_with(auth_type="env")

    @patch.dict(os.environ, {}, clear=True)
    def test_auto_detect_none(self):
        """Test auto-detection defaults to none when no auth config."""
        with patch('fastmcp.server.auth.mcp_auth_config.create_mcp_auth_provider') as mock_create:
            mock_create.return_value = None
            
            result = get_default_auth_provider()
            
            assert result is None
            mock_create.assert_called_once_with(auth_type="none")


class TestConfigureMcpServerAuth:
    """Test cases for configure_mcp_server_auth function."""

    def test_configure_with_existing_auth(self):
        """Test configuring server that already has auth."""
        mock_server = MagicMock()
        mock_auth = MagicMock()
        mock_server.auth = mock_auth
        
        result = configure_mcp_server_auth(mock_server)
        
        assert result == mock_server
        assert mock_server.auth == mock_auth  # Should not change

    def test_configure_without_auth(self):
        """Test configuring server without auth."""
        with patch('fastmcp.server.auth.mcp_auth_config.get_default_auth_provider') as mock_get_default:
            with patch('fastmcp.server.auth.mcp_auth_config.get_logger') as mock_get_logger:
                mock_server = MagicMock()
                mock_server.auth = None
                mock_provider = MagicMock()
                mock_provider.__class__.__name__ = 'JWTBearerAuthProvider'
                mock_get_default.return_value = mock_provider
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                result = configure_mcp_server_auth(mock_server)
                
                assert result == mock_server
                assert mock_server.auth == mock_provider
                mock_get_default.assert_called_once()
                mock_logger.info.assert_called_once_with(
                    "MCP server configured with JWTBearerAuthProvider authentication"
                )

    def test_configure_with_no_default_auth(self):
        """Test configuring server when default auth is None."""
        with patch('fastmcp.server.auth.mcp_auth_config.get_default_auth_provider') as mock_get_default:
            mock_server = MagicMock()
            mock_server.auth = None
            mock_get_default.return_value = None
            
            result = configure_mcp_server_auth(mock_server)
            
            assert result == mock_server
            assert mock_server.auth is None  # Should remain None
            mock_get_default.assert_called_once()


class TestIntegration:
    """Integration tests for MCP auth config functions."""

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret", "MCP_AUTH_TYPE": "jwt"}, clear=True)
    def test_full_jwt_flow(self):
        """Test full JWT authentication flow."""
        with patch('fastmcp.server.auth.mcp_auth_config.JWTBearerAuthProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            
            # Get default provider
            provider = get_default_auth_provider()
            assert provider == mock_instance
            
            # Configure server
            mock_server = MagicMock()
            mock_server.auth = None
            
            with patch('fastmcp.server.auth.mcp_auth_config.get_logger'):
                result = configure_mcp_server_auth(mock_server)
            
            assert result.auth == mock_instance

    @patch.dict(os.environ, {"MCP_BEARER_TOKEN": "test-token"}, clear=True)
    def test_full_env_flow(self):
        """Test full environment Bearer authentication flow."""
        with patch('fastmcp.server.auth.mcp_auth_config.EnvBearerAuthProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            
            # Get default provider
            provider = get_default_auth_provider()
            assert provider == mock_instance
            
            # Configure server
            mock_server = MagicMock()
            mock_server.auth = None
            
            with patch('fastmcp.server.auth.mcp_auth_config.get_logger'):
                result = configure_mcp_server_auth(mock_server)
            
            assert result.auth == mock_instance

    @patch.dict(os.environ, {"DHAFNCK_AUTH_ENABLED": "false"}, clear=True)
    def test_disabled_auth_flow(self):
        """Test flow when authentication is disabled."""
        # Get default provider
        provider = get_default_auth_provider()
        assert provider is None
        
        # Configure server
        mock_server = MagicMock()
        mock_server.auth = None
        
        result = configure_mcp_server_auth(mock_server)
        
        assert result.auth is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch.dict(os.environ, {"DHAFNCK_AUTH_ENABLED": "FALSE"}, clear=True)
    def test_auth_disabled_case_insensitive(self):
        """Test auth disabled with case insensitive value."""
        result = get_default_auth_provider()
        assert result is None

    @patch.dict(os.environ, {"MCP_AUTH_TYPE": "JWT"}, clear=True)
    def test_auth_type_case_sensitivity(self):
        """Test that auth type is case sensitive."""
        # Should fail because "JWT" != "jwt"
        with pytest.raises(ValueError) as exc_info:
            create_mcp_auth_provider(auth_type="JWT")
        assert "Unknown auth_type: JWT" in str(exc_info.value)

    def test_create_provider_with_empty_scopes(self):
        """Test creating JWT provider with empty scopes list."""
        with patch('fastmcp.server.auth.mcp_auth_config.JWTBearerAuthProvider') as mock_jwt:
            mock_instance = MagicMock()
            mock_jwt.return_value = mock_instance
            
            result = create_mcp_auth_provider(
                auth_type="jwt",
                required_scopes=[]
            )
            
            mock_jwt.assert_called_once_with(
                secret_key=None,
                required_scopes=[],
                check_database=True,
            )

    def test_configure_server_with_multiple_calls(self):
        """Test configuring server multiple times."""
        mock_server = MagicMock()
        mock_auth1 = MagicMock()
        mock_auth1.__class__.__name__ = 'Auth1'
        
        # First call - server has auth
        mock_server.auth = mock_auth1
        result1 = configure_mcp_server_auth(mock_server)
        assert result1.auth == mock_auth1
        
        # Second call - auth unchanged
        result2 = configure_mcp_server_auth(mock_server)
        assert result2.auth == mock_auth1

    @patch.dict(os.environ, {"DHAFNCK_AUTH_ENABLED": "true", "JWT_SECRET_KEY": "test", "MCP_BEARER_TOKEN": "token"}, clear=True)
    def test_jwt_priority_over_env(self):
        """Test that JWT auth has priority over env auth when both are available."""
        with patch('fastmcp.server.auth.mcp_auth_config.create_mcp_auth_provider') as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider
            
            result = get_default_auth_provider()
            
            # Should create JWT provider, not env provider
            mock_create.assert_called_once_with(auth_type="jwt")

    def test_create_provider_with_none_scopes(self):
        """Test creating JWT provider with None scopes."""
        with patch('fastmcp.server.auth.mcp_auth_config.JWTBearerAuthProvider') as mock_jwt:
            mock_instance = MagicMock()
            mock_jwt.return_value = mock_instance
            
            result = create_mcp_auth_provider(
                auth_type="jwt",
                required_scopes=None
            )
            
            # Should default to ["mcp:access"]
            mock_jwt.assert_called_once_with(
                secret_key=None,
                required_scopes=["mcp:access"],
                check_database=True,
            )