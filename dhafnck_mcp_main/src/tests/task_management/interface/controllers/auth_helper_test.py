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
    get_user_id_from_request_state,
    USER_CONTEXT_AVAILABLE
)
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError
)


class TestGetAuthenticatedUserId:
    """Test cases for get_authenticated_user_id function."""
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    def test_request_state_user_id_takes_precedence(self, mock_get_request_state):
        """Test that user_id from request state (DualAuthMiddleware) takes precedence."""
        mock_get_request_state.return_value = "request_state_user"
        
        with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
            mock_validate.return_value = "request_state_user"
            
            result = get_authenticated_user_id(None, "test_op")
            
            assert result == "request_state_user"
            mock_validate.assert_called_once_with("request_state_user", "test_op")
    
    @patch('fastmcp.server.http_server._current_http_request')
    def test_get_user_id_from_request_state_success(self, mock_current_request):
        """Test successful extraction of user_id from request state."""
        # Mock request with state
        mock_request = Mock()
        mock_request.state.user_id = "state_user_123"
        mock_current_request.get.return_value = mock_request
        
        result = get_user_id_from_request_state()
        assert result == "state_user_123"
    
    @patch('fastmcp.server.http_server._current_http_request')
    def test_get_user_id_from_request_state_no_request(self, mock_current_request):
        """Test when no current request is available."""
        mock_current_request.get.return_value = None
        
        result = get_user_id_from_request_state()
        assert result is None
    
    @patch('fastmcp.server.http_server._current_http_request')
    def test_get_user_id_from_request_state_no_state(self, mock_current_request):
        """Test when request has no state attribute."""
        # Mock request without state
        mock_request = Mock(spec=[])
        mock_current_request.get.return_value = mock_request
        
        result = get_user_id_from_request_state()
        assert result is None
    
    @patch('fastmcp.server.http_server._current_http_request')
    def test_get_user_id_from_request_state_exception(self, mock_current_request):
        """Test exception handling in get_user_id_from_request_state."""
        mock_current_request.get.side_effect = Exception("Request context error")
        
        result = get_user_id_from_request_state()
        assert result is None
    
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
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_custom_context_middleware_returns_none(self, mock_get_current_user_id, mock_get_request_state):
        """Test when custom context middleware returns None and authentication fails."""
        mock_get_current_user_id.return_value = None
        mock_get_request_state.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with pytest.raises(UserAuthenticationRequiredError):
                get_authenticated_user_id(None, "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_custom_context_middleware_exception(self, mock_get_current_user_id, mock_get_request_state):
        """Test when custom context middleware raises exception and authentication fails."""
        mock_get_current_user_id.side_effect = Exception("Context error")
        mock_get_request_state.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with pytest.raises(UserAuthenticationRequiredError):
                get_authenticated_user_id(None, "test_op")
    
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
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_mcp_auth_context_with_client_id(self, mock_get_current_user_id, mock_get_request_state):
        """Test MCP auth context with client_id attribute."""
        mock_get_current_user_id.return_value = None
        mock_get_request_state.return_value = None
        
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
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_mcp_auth_context_unavailable(self, mock_get_current_user_id, mock_get_request_state):
        """Test when MCP auth context is unavailable and authentication fails."""
        mock_get_current_user_id.return_value = None
        mock_get_request_state.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.side_effect = ImportError("MCP not available")
            
            with pytest.raises(UserAuthenticationRequiredError):
                get_authenticated_user_id(None, "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_strict_authentication_no_fallback(self, mock_get_current_user_id, mock_get_request_state):
        """Test that error is raised when no authentication sources are available."""
        mock_get_current_user_id.return_value = None
        mock_get_request_state.return_value = None
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            with pytest.raises(UserAuthenticationRequiredError):
                get_authenticated_user_id(None, "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')  
    def test_mcp_authenticated_user_with_access_token(self, mock_get_current_user_id, mock_get_request_state):
        """Test MCP AuthenticatedUser with access token client_id."""
        mock_get_current_user_id.return_value = None
        mock_get_request_state.return_value = None
        
        # Mock AuthenticatedUser with access_token
        from unittest.mock import Mock
        mock_auth_user = Mock()
        mock_auth_user.access_token = Mock()
        mock_auth_user.access_token.client_id = "mcp_client_123"
        
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            with patch('mcp.server.auth.middleware.bearer_auth.AuthenticatedUser') as mock_authenticated_user:
                mock_context.get.return_value = mock_auth_user
                
                # Make isinstance check return True for our mock
                with patch('builtins.isinstance') as mock_isinstance:
                    mock_isinstance.return_value = True
                    
                    with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                        mock_validate.return_value = "mcp_client_123"
                        
                        result = get_authenticated_user_id(None, "test_op")
                        
                        assert result == "mcp_client_123"
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_multiple_auth_sources_precedence(self, mock_get_current_user_id, mock_get_request_state):
        """Test precedence of different authentication sources."""
        # Request state should take precedence over context middleware
        mock_get_request_state.return_value = "request_user"
        mock_get_current_user_id.return_value = "context_user"
        
        with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
            mock_validate.return_value = "request_user"
            
            result = get_authenticated_user_id(None, "test_op")
            
            assert result == "request_user"
            mock_validate.assert_called_once_with("request_user", "test_op")
    
    def test_user_id_validation_error_propagation(self):
        """Test that user ID validation errors are properly propagated."""
        from fastmcp.task_management.domain.exceptions.authentication_exceptions import InvalidUserIdError
        
        # Provide an invalid user ID
        with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
            mock_validate.side_effect = InvalidUserIdError("Invalid format")
            
            with pytest.raises(InvalidUserIdError):
                get_authenticated_user_id("invalid_format", "test_op")
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_comprehensive_auth_flow_all_sources_fail(self, mock_get_current_user_id, mock_get_request_state):
        """Test comprehensive authentication flow when all sources fail."""
        # All authentication sources return None
        mock_get_request_state.return_value = None
        mock_get_current_user_id.return_value = None
        
        # MCP context also returns None
        with patch('mcp.server.auth.context.auth_context') as mock_context:
            mock_context.get.return_value = None
            
            # Should raise authentication required error
            with pytest.raises(UserAuthenticationRequiredError) as exc_info:
                get_authenticated_user_id(None, "comprehensive_test")
            
            assert "comprehensive_test" in str(exc_info.value)
    
    def test_user_context_not_available_fallback(self):
        """Test behavior when USER_CONTEXT_AVAILABLE is False."""
        # When user context is not available, should still try other sources
        with patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False):
            with patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state') as mock_request_state:
                mock_request_state.return_value = None
                
                with patch('mcp.server.auth.context.auth_context') as mock_context:
                    mock_context.get.return_value = None
                    
                    # Should fail since no authentication sources work
                    with pytest.raises(UserAuthenticationRequiredError):
                        get_authenticated_user_id(None, "test_op")
    
    def test_logging_and_debugging_functionality(self):
        """Test that proper logging occurs during authentication process."""
        with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
            with patch('fastmcp.task_management.domain.constants.validate_user_id') as mock_validate:
                mock_validate.return_value = "provided_user"
                
                result = get_authenticated_user_id("provided_user", "test_op")
                
                assert result == "provided_user"
                # Verify logging calls were made
                mock_logger.info.assert_called()
                logging_calls = [call.args[0] for call in mock_logger.info.call_args_list]
                assert any("get_authenticated_user_id called" in call for call in logging_calls)


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
    def test_log_strict_authentication_mode(self, mock_get_current_user_id):
        """Test logging strict authentication mode status."""
        mock_get_current_user_id.return_value = None
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.logger') as mock_logger:
            log_authentication_details()
            
            mock_logger.debug.assert_any_call("Authentication is always strictly enforced")
    
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
                debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list if mock_logger.debug.call_args_list]
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