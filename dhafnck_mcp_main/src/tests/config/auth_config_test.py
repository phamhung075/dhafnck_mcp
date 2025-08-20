"""Test suite for AuthConfig module.

Tests authentication configuration including:
- Default user permissions
- Environment variable handling
- Fallback user ID generation
- Security enforcement
- Migration readiness validation
"""

import os
import pytest
import logging
from unittest.mock import patch, MagicMock
from fastmcp.config.auth_config import AuthConfig
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError
)


class TestAuthConfig:
    """Test cases for AuthConfig class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Store original environment variables
        self.original_env = os.environ.copy()
        # Clear relevant environment variables
        os.environ.pop('ALLOW_DEFAULT_USER', None)
        os.environ.pop('ENVIRONMENT', None)
    
    def teardown_method(self):
        """Clean up after tests."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_is_default_user_allowed_default_false(self):
        """Test that default user is not allowed by default."""
        # No environment variable set
        assert AuthConfig.is_default_user_allowed() is False
    
    def test_is_default_user_allowed_true_values(self):
        """Test various true values for ALLOW_DEFAULT_USER."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES', 'on', 'On', 'ON']
        
        for value in true_values:
            os.environ['ALLOW_DEFAULT_USER'] = value
            assert AuthConfig.is_default_user_allowed() is True, f"Failed for value: {value}"
    
    def test_is_default_user_allowed_false_values(self):
        """Test various false values for ALLOW_DEFAULT_USER."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', 'off', 'Off', 'OFF', 'invalid', '']
        
        for value in false_values:
            os.environ['ALLOW_DEFAULT_USER'] = value
            assert AuthConfig.is_default_user_allowed() is False, f"Failed for value: {value}"
    
    def test_is_default_user_allowed_logging_warning(self, caplog):
        """Test that warning is logged when default user is allowed."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        with caplog.at_level(logging.WARNING):
            result = AuthConfig.is_default_user_allowed()
        
        assert result is True
        assert "DEFAULT USER IS ALLOWED - This is a security risk!" in caplog.text
        assert "Set ALLOW_DEFAULT_USER=false in production" in caplog.text
    
    def test_get_fallback_user_id_allowed(self):
        """Test getting fallback user ID when allowed."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        user_id = AuthConfig.get_fallback_user_id()
        
        assert user_id == "compatibility-default-user"
    
    def test_get_fallback_user_id_not_allowed(self):
        """Test getting fallback user ID when not allowed raises exception."""
        os.environ['ALLOW_DEFAULT_USER'] = 'false'
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            AuthConfig.get_fallback_user_id()
        
        assert "Authentication required" in str(exc_info.value)
        assert "default user is not allowed" in str(exc_info.value)
    
    def test_get_fallback_user_id_logging_warning(self, caplog):
        """Test that warning is logged when using fallback user ID."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        with caplog.at_level(logging.WARNING):
            user_id = AuthConfig.get_fallback_user_id()
        
        assert user_id == "compatibility-default-user"
        assert "Using fallback user ID 'compatibility-default-user'" in caplog.text
        assert "this is temporary and will be removed in future versions" in caplog.text
    
    def test_should_enforce_authentication_default(self):
        """Test that authentication is enforced by default."""
        assert AuthConfig.should_enforce_authentication() is True
    
    def test_should_enforce_authentication_compatibility_mode(self):
        """Test that authentication is not enforced in compatibility mode."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        assert AuthConfig.should_enforce_authentication() is False
    
    def test_log_authentication_bypass(self, caplog):
        """Test authentication bypass logging."""
        with caplog.at_level(logging.WARNING):
            AuthConfig.log_authentication_bypass("test_operation", "test reason")
        
        assert "Authentication bypassed for 'test_operation': test reason" in caplog.text
        assert "This should be fixed before production deployment" in caplog.text
    
    def test_validate_migration_readiness_ready(self):
        """Test migration readiness when system is ready."""
        # Default state - no compatibility mode
        result = AuthConfig.validate_migration_readiness()
        
        assert result['ready'] is True
        assert len(result['issues']) == 0
        assert result['compatibility_mode'] is False
    
    def test_validate_migration_readiness_not_ready(self):
        """Test migration readiness when system is not ready."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        result = AuthConfig.validate_migration_readiness()
        
        assert result['ready'] is False
        assert "ALLOW_DEFAULT_USER is still enabled" in result['issues']
        assert result['compatibility_mode'] is True
    
    def test_validate_migration_readiness_production_warning(self):
        """Test migration readiness with production environment warning."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        os.environ['ENVIRONMENT'] = 'production'
        
        result = AuthConfig.validate_migration_readiness()
        
        assert result['ready'] is False
        assert "ALLOW_DEFAULT_USER is still enabled" in result['issues']
        assert "Default user is allowed in production environment!" in result['issues']
        assert result['environment'] == 'production'
    
    def test_validate_migration_readiness_environment_variations(self):
        """Test migration readiness with different environment names."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        for env in ['prod', 'PRODUCTION', 'PROD']:
            os.environ['ENVIRONMENT'] = env
            result = AuthConfig.validate_migration_readiness()
            
            assert result['ready'] is False
            assert "Default user is allowed in production environment!" in result['issues']
    
    def test_validate_migration_readiness_unknown_environment(self):
        """Test migration readiness with unknown environment."""
        # No ENVIRONMENT variable set
        result = AuthConfig.validate_migration_readiness()
        
        assert result['environment'] == 'unknown'
    
    def test_multiple_method_interaction(self):
        """Test interaction between multiple AuthConfig methods."""
        # Start with compatibility mode enabled
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        # Check that methods are consistent
        assert AuthConfig.is_default_user_allowed() is True
        assert AuthConfig.should_enforce_authentication() is False
        
        # Should be able to get fallback user
        user_id = AuthConfig.get_fallback_user_id()
        assert user_id == "compatibility-default-user"
        
        # Migration not ready
        readiness = AuthConfig.validate_migration_readiness()
        assert readiness['ready'] is False
        
        # Disable compatibility mode
        os.environ['ALLOW_DEFAULT_USER'] = 'false'
        
        # Check that methods are consistent
        assert AuthConfig.is_default_user_allowed() is False
        assert AuthConfig.should_enforce_authentication() is True
        
        # Should not be able to get fallback user
        with pytest.raises(UserAuthenticationRequiredError):
            AuthConfig.get_fallback_user_id()
        
        # Migration ready
        readiness = AuthConfig.validate_migration_readiness()
        assert readiness['ready'] is True
    
    @patch('fastmcp.config.auth_config.logger')
    def test_logging_stack_trace_when_allowed(self, mock_logger):
        """Test that stack trace is logged when default user is allowed."""
        os.environ['ALLOW_DEFAULT_USER'] = 'true'
        
        AuthConfig.is_default_user_allowed()
        
        # Check that warning was called
        mock_logger.warning.assert_called()
        # Check that debug was called with stack trace
        mock_logger.debug.assert_called()
        debug_call_args = mock_logger.debug.call_args[0][0]
        assert "Default user check called from:" in debug_call_args
    
    def test_thread_safety(self):
        """Test thread safety of AuthConfig methods."""
        import threading
        import time
        
        results = []
        errors = []
        
        def check_config():
            try:
                # Each thread does multiple operations
                for _ in range(10):
                    is_allowed = AuthConfig.is_default_user_allowed()
                    should_enforce = AuthConfig.should_enforce_authentication()
                    readiness = AuthConfig.validate_migration_readiness()
                    
                    # Results should be consistent
                    assert is_allowed == (not should_enforce)
                    assert readiness['compatibility_mode'] == is_allowed
                    
                    results.append((is_allowed, should_enforce, readiness['ready']))
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=check_config)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check no errors occurred
        assert len(errors) == 0, f"Thread errors occurred: {errors}"
        
        # All results should be consistent
        if results:
            first_result = results[0]
            for result in results:
                assert result == first_result, "Inconsistent results across threads"