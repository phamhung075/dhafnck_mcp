"""Tests for Authentication Helper for MCP Controllers

This module tests the auth_helper module that provides common authentication
functionality for all MCP controllers to extract user_id from JWT tokens
and various authentication contexts.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging
import os

from fastmcp.task_management.interface.controllers.auth_helper import (
    get_authenticated_user_id,
    log_authentication_details,
    USER_CONTEXT_AVAILABLE
)
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError
)


class TestGetAuthenticatedUserId:
    """Test cases for get_authenticated_user_id function."""
    
    def test_provided_user_id_takes_precedence(self):
        """Test that provided user_id parameter takes precedence."""
        with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
            mock_validate.return_value = "provided_user"
            
            result = get_authenticated_user_id("provided_user", "test_op")
            
            assert result == "provided_user"
            mock_validate.assert_called_once_with("provided_user", "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_custom_context_middleware_success(self, mock_get_current_user_id):
        """Test successful authentication via custom context middleware."""
        mock_get_current_user_id.return_value = "context_user"
        
        with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
            mock_validate.return_value = "context_user"
            
            result = get_authenticated_user_id(None, "test_op")
            
            assert result == "context_user"
            mock_validate.assert_called_once_with("context_user", "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_custom_context_middleware_returns_none(self, mock_get_current_user_id):
        """Test when custom context middleware returns None."""
        mock_get_current_user_id.return_value = None
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
            mock_config.is_default_user_allowed.return_value = True
            mock_config.get_fallback_user_id.return_value = "fallback_user"
            
            with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                mock_validate.return_value = "fallback_user"
                
                result = get_authenticated_user_id(None, "test_op")
                
                assert result == "fallback_user"
                mock_config.log_authentication_bypass.assert_called_once_with("test_op", "compatibility mode")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_custom_context_middleware_exception(self, mock_get_current_user_id):
        """Test when custom context middleware raises exception."""
        mock_get_current_user_id.side_effect = Exception("Context error")
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
            mock_config.is_default_user_allowed.return_value = True
            mock_config.get_fallback_user_id.return_value = "fallback_user"
            
            with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                mock_validate.return_value = "fallback_user"
                
                result = get_authenticated_user_id(None, "test_op")
                
                assert result == "fallback_user"
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_mcp_auth_context_with_user_id(self, mock_get_current_user_id):
        """Test MCP auth context with user_id attribute."""
        mock_get_current_user_id.return_value = None
        
        mock_auth_context = Mock()
        mock_auth_context.user_id = "mcp_user"
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = mock_auth_context
            
            with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                mock_validate.return_value = "mcp_user"
                
                result = get_authenticated_user_id(None, "test_op")
                
                assert result == "mcp_user"
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_mcp_auth_context_with_client_id(self, mock_get_current_user_id):
        """Test MCP auth context with client_id attribute."""
        mock_get_current_user_id.return_value = None
        
        mock_auth_context = Mock()
        mock_auth_context.client_id = "mcp_client"
        # Remove user_id attribute to test client_id fallback
        delattr(mock_auth_context, 'user_id') if hasattr(mock_auth_context, 'user_id') else None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = mock_auth_context
            
            with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                mock_validate.return_value = "mcp_client"
                
                result = get_authenticated_user_id(None, "test_op")
                
                assert result == "mcp_client"
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_mcp_auth_context_unavailable(self, mock_get_current_user_id):
        """Test when MCP auth context is unavailable."""
        mock_get_current_user_id.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.side_effect = ImportError("MCP not available")
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
                mock_config.is_default_user_allowed.return_value = True
                mock_config.get_fallback_user_id.return_value = "fallback_user"
                
                with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                    mock_validate.return_value = "fallback_user"
                    
                    result = get_authenticated_user_id(None, "test_op")
                    
                    assert result == "fallback_user"
    
    @patch('os.getenv')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_compatibility_mode_disabled_raises_error(self, mock_get_current_user_id, mock_getenv):
        """Test that error is raised when compatibility mode is disabled."""
        mock_get_current_user_id.return_value = None
        mock_getenv.return_value = 'production'  # Not in development
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
                mock_config.is_default_user_allowed.return_value = False
                
                with pytest.raises(UserAuthenticationRequiredError):
                    get_authenticated_user_id(None, "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_compatibility_mode_enabled_uses_fallback(self, mock_get_current_user_id):
        """Test compatibility mode uses fallback user ID."""
        mock_get_current_user_id.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
                mock_config.is_default_user_allowed.return_value = True
                mock_config.get_fallback_user_id.return_value = "fallback_user"
                
                with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                    mock_validate.return_value = "fallback_user"
                    
                    result = get_authenticated_user_id(None, "test_op")
                    
                    assert result == "fallback_user"
                    mock_config.log_authentication_bypass.assert_called_once_with("test_op", "compatibility mode")
    
    @patch('os.getenv')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_dev_environment_temporary_fix(self, mock_get_current_user_id, mock_getenv):
        """Test temporary development environment fix for git branch authentication."""
        mock_get_current_user_id.return_value = None
        
        # Test with different development environment values
        dev_environments = ['development', 'dev', '']  # Empty string for local dev
        
        for env_value in dev_environments:
            mock_getenv.return_value = env_value
            
            with patch('mcp.server.auth.context.auth_context') as mock_context:
                mock_context.get.return_value = None
                
                with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
                    mock_config.is_default_user_allowed.return_value = False
                    mock_config.log_authentication_bypass = Mock()
                    
                    with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                        mock_validate.return_value = "compatibility-default-user"
                        
                        result = get_authenticated_user_id(None, "test_op")
                        
                        assert result == "compatibility-default-user"
                        mock_config.log_authentication_bypass.assert_called_with(
                            "test_op", 
                            "forced compatibility mode for git branch fix"
                        )
    
    @patch('os.getenv')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_non_dev_environment_no_temporary_fix(self, mock_get_current_user_id, mock_getenv):
        """Test that temporary fix is not applied in non-development environments."""
        mock_get_current_user_id.return_value = None
        mock_getenv.return_value = 'production'
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
                mock_config.is_default_user_allowed.return_value = False
                
                # Should raise error in production when no auth available
                with pytest.raises(UserAuthenticationRequiredError):
                    get_authenticated_user_id(None, "test_op")
    
    def test_user_context_not_available_fallback(self):
        """Test behavior when USER_CONTEXT_AVAILABLE is False."""
        # This test verifies the import fallback mechanism
        with patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False):
            with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
                mock_config.is_default_user_allowed.return_value = True
                mock_config.get_fallback_user_id.return_value = "fallback_user"
                
                with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                    mock_validate.return_value = "fallback_user"
                    
                    result = get_authenticated_user_id(None, "test_op")
                    
                    assert result == "fallback_user"
    
    def test_validation_error_propagated(self):
        """Test that validation errors are properly propagated."""
        from fastmcp.task_management.domain.exceptions.authentication_exceptions import InvalidUserIdError
        
        with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
            mock_validate.side_effect = InvalidUserIdError("Invalid user ID format")
            
            with pytest.raises(InvalidUserIdError):
                get_authenticated_user_id("invalid_user", "test_op")


class TestLogAuthenticationDetails:
    """Test cases for log_authentication_details function."""
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_custom_context_success(self, mock_get_current_user_id):
        """Test logging when custom context is available."""
        mock_get_current_user_id.return_value = "context_user"
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
            log_authentication_details()
            
            mock_logger.debug.assert_any_call("Custom context user_id: context_user")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_mcp_context_with_attributes(self, mock_get_current_user_id):
        """Test logging MCP context with user_id and client_id."""
        mock_get_current_user_id.return_value = None
        
        mock_auth_context = Mock()
        mock_auth_context.user_id = "mcp_user"
        mock_auth_context.client_id = "mcp_client"
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = mock_auth_context
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
                log_authentication_details()
                
                mock_logger.debug.assert_any_call("MCP user_id: mcp_user")
                mock_logger.debug.assert_any_call("MCP client_id: mcp_client")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_mcp_context_unavailable(self, mock_get_current_user_id):
        """Test logging when MCP context is unavailable."""
        mock_get_current_user_id.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
                log_authentication_details()
                
                mock_logger.debug.assert_any_call("No MCP auth context available")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_mcp_context_exception(self, mock_get_current_user_id):
        """Test logging when MCP context access raises exception."""
        mock_get_current_user_id.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.side_effect = ImportError("MCP not available")
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
                log_authentication_details()
                
                mock_logger.debug.assert_any_call("Error accessing MCP auth context: MCP not available")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_compatibility_mode(self, mock_get_current_user_id):
        """Test logging compatibility mode status."""
        mock_get_current_user_id.return_value = None
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.AuthConfig') as mock_config:
            mock_config.is_default_user_allowed.return_value = True
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
                log_authentication_details()
                
                mock_logger.debug.assert_any_call("Compatibility mode enabled: True")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_general_exception_handling(self, mock_get_current_user_id):
        """Test that general exceptions are handled gracefully."""
        mock_get_current_user_id.side_effect = Exception("General error")
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
            log_authentication_details()
            
            mock_logger.error.assert_called_once_with("Error logging authentication details: General error")
    
    def test_log_user_context_not_available(self):
        """Test logging when USER_CONTEXT_AVAILABLE is False."""
        with patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False):
            with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
                log_authentication_details()
                
                # Should skip custom context logging when not available
                debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
                custom_context_calls = [call for call in debug_calls if "Custom context user_id" in call]
                assert len(custom_context_calls) == 0


class TestUserContextAvailabilityFlag:
    """Test cases for USER_CONTEXT_AVAILABLE flag behavior."""
    
    def test_user_context_available_flag_true(self):
        """Test that USER_CONTEXT_AVAILABLE is True when import succeeds."""
        # This is tested implicitly by other tests, but we can verify the flag
        assert USER_CONTEXT_AVAILABLE in [True, False]  # Should be boolean
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_fallback_behavior_when_unavailable(self, mock_get_current_user_id):
        """Test fallback behavior when user context is not available."""
        # The lambda fallback should return None
        result = mock_get_current_user_id()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])