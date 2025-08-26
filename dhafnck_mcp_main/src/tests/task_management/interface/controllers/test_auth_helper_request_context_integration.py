"""
Tests for auth_helper.py Integration with RequestContextMiddleware

These tests verify that the updated auth_helper.py correctly uses
the new RequestContextMiddleware context variables with proper
priority and fallback behavior.
"""

import pytest
from unittest.mock import patch, Mock
from fastmcp.task_management.interface.controllers.auth_helper import (
    get_authenticated_user_id,
    log_authentication_details
)
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError
)


class TestAuthHelperRequestContextIntegration:
    """Test auth_helper.py integration with RequestContextMiddleware."""
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_from_request_context')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.is_request_authenticated')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_auth_method')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id')
    def test_priority_1_request_context_middleware_success(
        self, mock_validate, mock_auth_method, mock_authenticated, mock_get_user
    ):
        """Test Priority 1: RequestContextMiddleware context variables work and take precedence."""
        # Setup mocks
        test_user_id = "context-user-123"
        mock_get_user.return_value = test_user_id
        mock_authenticated.return_value = True
        mock_auth_method.return_value = "local_jwt"
        mock_validate.return_value = test_user_id  # Validation passes
        
        # Call auth helper
        result = get_authenticated_user_id(operation_name="test_priority_1")
        
        # Verify RequestContextMiddleware was used
        mock_get_user.assert_called_once()
        mock_authenticated.assert_called_once()
        mock_auth_method.assert_called_once()
        mock_validate.assert_called_once_with(test_user_id, "test_priority_1")
        
        assert result == test_user_id
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_from_request_context')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id')
    def test_priority_2_fallback_to_request_state(
        self, mock_validate, mock_request_state, mock_context
    ):
        """Test Priority 2: Falls back to legacy request state when context returns None."""
        # Setup mocks
        test_user_id = "request-state-user-456"
        mock_context.return_value = None  # RequestContextMiddleware returns None
        mock_request_state.return_value = test_user_id  # Legacy method works
        mock_validate.return_value = test_user_id
        
        # Call auth helper
        result = get_authenticated_user_id(operation_name="test_priority_2")
        
        # Verify fallback path was used
        mock_context.assert_called_once()
        mock_request_state.assert_called_once()
        mock_validate.assert_called_once_with(test_user_id, "test_priority_2")
        
        assert result == test_user_id
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', False)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id')
    def test_priority_3_fallback_to_custom_context(
        self, mock_validate, mock_custom_context, mock_request_state
    ):
        """Test Priority 3: Falls back to custom user context when RequestContext not available."""
        # Setup mocks
        test_user_id = "custom-context-user-789"
        mock_request_state.return_value = None  # Request state fails
        mock_custom_context.return_value = test_user_id  # Custom context works
        mock_validate.return_value = test_user_id
        
        # Call auth helper
        result = get_authenticated_user_id(operation_name="test_priority_3")
        
        # Verify custom context was used
        mock_request_state.assert_called_once()
        mock_custom_context.assert_called_once()
        mock_validate.assert_called_once_with(test_user_id, "test_priority_3")
        
        assert result == test_user_id
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_from_request_context')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_authentication_context')
    def test_error_context_logging_on_failure(self, mock_full_context, mock_get_user):
        """Test that full authentication context is logged when authentication fails."""
        # Setup mocks to simulate complete auth failure
        mock_get_user.return_value = None
        mock_full_context.return_value = {
            "user_id": None,
            "email": None,
            "auth_method": None,
            "authenticated": False
        }
        
        # Mock all other auth methods to fail too
        with patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state', return_value=None), \
             patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False):
            
            # Should raise authentication error
            with pytest.raises(UserAuthenticationRequiredError):
                get_authenticated_user_id(operation_name="test_error_logging")
            
            # Verify full context was retrieved for logging
            mock_full_context.assert_called_once()
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_from_request_context')
    def test_request_context_exception_handling(self, mock_get_user):
        """Test that exceptions in RequestContextMiddleware are handled gracefully."""
        # Setup mock to raise exception
        mock_get_user.side_effect = Exception("Context access error")
        
        # Mock fallback method to work
        with patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state', return_value="fallback-user"), \
             patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id', return_value="fallback-user"):
            
            # Should still work via fallback
            result = get_authenticated_user_id(operation_name="test_exception_handling")
            assert result == "fallback-user"
            
            # Verify exception in context access was attempted
            mock_get_user.assert_called_once()
    
    def test_provided_user_id_takes_precedence(self):
        """Test that explicitly provided user_id takes precedence over all context methods."""
        provided_user_id = "explicit-user-999"
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id', return_value=provided_user_id):
            result = get_authenticated_user_id(
                provided_user_id=provided_user_id,
                operation_name="test_explicit_precedence"
            )
            
            assert result == provided_user_id
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_from_request_context')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_auth_method')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.is_request_authenticated')
    def test_detailed_logging_with_request_context(
        self, mock_authenticated, mock_auth_method, mock_get_user
    ):
        """Test that detailed authentication context is logged when available."""
        # Setup mocks
        test_user_id = "logging-test-user"
        mock_get_user.return_value = test_user_id
        mock_authenticated.return_value = True
        mock_auth_method.return_value = "supabase_jwt"
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id', return_value=test_user_id):
            result = get_authenticated_user_id(operation_name="test_detailed_logging")
            
            # Verify context methods were called for logging
            mock_authenticated.assert_called_once()
            mock_auth_method.assert_called_once()
            
            assert result == test_user_id


class TestLogAuthenticationDetails:
    """Test the log_authentication_details function with new context integration."""
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_authentication_context')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', True)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_current_user_id')
    def test_log_authentication_details_with_all_contexts(
        self, mock_custom_context, mock_full_context
    ):
        """Test logging authentication details when all context types are available."""
        # Setup mocks
        mock_full_context.return_value = {
            "user_id": "log-test-user",
            "email": "log@example.com",
            "auth_method": "local_jwt",
            "authenticated": True
        }
        mock_custom_context.return_value = "log-test-user"
        
        # Should not raise exception
        log_authentication_details()
        
        # Verify context methods were called
        mock_full_context.assert_called_once()
        mock_custom_context.assert_called_once()
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', False)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False)
    def test_log_authentication_details_with_no_contexts(self):
        """Test logging authentication details when no special contexts are available."""
        # Should not raise exception even with no contexts
        log_authentication_details()


class TestBackwardCompatibility:
    """Test backward compatibility with existing authentication methods."""
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', False)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state')
    @patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id')
    def test_backward_compatibility_request_state_only(self, mock_validate, mock_request_state):
        """Test that the system still works with only legacy request state."""
        test_user_id = "legacy-user-compatibility"
        mock_request_state.return_value = test_user_id
        mock_validate.return_value = test_user_id
        
        result = get_authenticated_user_id(operation_name="test_backward_compatibility")
        
        mock_request_state.assert_called_once()
        mock_validate.assert_called_once_with(test_user_id, "test_backward_compatibility")
        assert result == test_user_id
    
    @patch('fastmcp.task_management.interface.controllers.auth_helper.REQUEST_CONTEXT_AVAILABLE', False)
    @patch('fastmcp.task_management.interface.controllers.auth_helper.USER_CONTEXT_AVAILABLE', False)
    def test_mcp_auth_context_fallback_still_works(self):
        """Test that MCP auth context fallback still works when new contexts are unavailable."""
        # Mock MCP context to be available
        mock_auth_context = Mock()
        mock_auth_context.user_id = "mcp-context-user"
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.get_user_id_from_request_state', return_value=None), \
             patch('mcp.server.auth.context.auth_context.get', return_value=mock_auth_context), \
             patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id', return_value="mcp-context-user"):
            
            result = get_authenticated_user_id(operation_name="test_mcp_fallback")
            assert result == "mcp-context-user"


if __name__ == "__main__":
    pytest.main([__file__])