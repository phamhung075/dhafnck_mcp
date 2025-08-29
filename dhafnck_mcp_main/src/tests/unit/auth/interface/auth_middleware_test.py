"""
Unit tests for auth middleware (deprecated utilities).

This module tests the deprecated auth middleware utility functions
that are kept for backward compatibility.
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi import Request
from fastmcp.auth.interface.auth_middleware import (
    get_current_user_id,
    get_current_user_email,
    get_current_user_roles,
    is_authenticated,
    has_role,
    is_admin
)
from fastmcp.auth.domain.entities.user import UserRole


class TestAuthMiddlewareUtilities:
    """Test suite for deprecated auth middleware utilities."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.state = Mock()
        return request
    
    def test_get_current_user_id_with_authenticated_user(self, mock_request):
        """Test getting user ID when user is authenticated."""
        # Arrange
        mock_request.state.user_id = "test_user_123"
        
        # Act
        result = get_current_user_id(mock_request)
        
        # Assert
        assert result == "test_user_123"
    
    def test_get_current_user_id_without_authentication(self, mock_request):
        """Test getting user ID when user is not authenticated."""
        # Arrange - no user_id in state
        delattr(mock_request.state, 'user_id')
        
        # Act
        result = get_current_user_id(mock_request)
        
        # Assert
        assert result is None
    
    def test_get_current_user_email_with_authenticated_user(self, mock_request):
        """Test getting user email when user is authenticated."""
        # Arrange
        mock_request.state.user_email = "test@example.com"
        
        # Act
        result = get_current_user_email(mock_request)
        
        # Assert
        assert result == "test@example.com"
    
    def test_get_current_user_email_without_authentication(self, mock_request):
        """Test getting user email when user is not authenticated."""
        # Arrange - no user_email in state
        delattr(mock_request.state, 'user_email')
        
        # Act
        result = get_current_user_email(mock_request)
        
        # Assert
        assert result is None
    
    def test_get_current_user_roles_with_authenticated_user(self, mock_request):
        """Test getting user roles when user is authenticated."""
        # Arrange
        mock_request.state.user_roles = ["user", "admin"]
        
        # Act
        result = get_current_user_roles(mock_request)
        
        # Assert
        assert result == ["user", "admin"]
    
    def test_get_current_user_roles_without_authentication(self, mock_request):
        """Test getting user roles when user is not authenticated."""
        # Arrange - no user_roles in state
        delattr(mock_request.state, 'user_roles')
        
        # Act
        result = get_current_user_roles(mock_request)
        
        # Assert
        assert result == []
    
    def test_is_authenticated_with_authenticated_user(self, mock_request):
        """Test checking authentication when user is authenticated."""
        # Arrange
        mock_request.state.user_id = "test_user_123"
        
        # Act
        result = is_authenticated(mock_request)
        
        # Assert
        assert result is True
    
    def test_is_authenticated_without_authentication(self, mock_request):
        """Test checking authentication when user is not authenticated."""
        # Arrange - no user_id in state
        delattr(mock_request.state, 'user_id')
        
        # Act
        result = is_authenticated(mock_request)
        
        # Assert
        assert result is False
    
    def test_has_role_with_matching_role(self, mock_request):
        """Test checking role when user has the specified role."""
        # Arrange
        mock_request.state.user_roles = ["user", "admin", "moderator"]
        
        # Act
        result = has_role(mock_request, "admin")
        
        # Assert
        assert result is True
    
    def test_has_role_without_matching_role(self, mock_request):
        """Test checking role when user doesn't have the specified role."""
        # Arrange
        mock_request.state.user_roles = ["user"]
        
        # Act
        result = has_role(mock_request, "admin")
        
        # Assert
        assert result is False
    
    def test_has_role_without_authentication(self, mock_request):
        """Test checking role when user is not authenticated."""
        # Arrange - no user_roles in state
        delattr(mock_request.state, 'user_roles')
        
        # Act
        result = has_role(mock_request, "admin")
        
        # Assert
        assert result is False
    
    def test_is_admin_with_admin_role(self, mock_request):
        """Test checking admin status when user is admin."""
        # Arrange
        mock_request.state.user_roles = ["user", UserRole.ADMIN.value]
        
        # Act
        result = is_admin(mock_request)
        
        # Assert
        assert result is True
    
    def test_is_admin_without_admin_role(self, mock_request):
        """Test checking admin status when user is not admin."""
        # Arrange
        mock_request.state.user_roles = ["user", "moderator"]
        
        # Act
        result = is_admin(mock_request)
        
        # Assert
        assert result is False
    
    def test_is_admin_without_authentication(self, mock_request):
        """Test checking admin status when user is not authenticated."""
        # Arrange - no user_roles in state
        delattr(mock_request.state, 'user_roles')
        
        # Act
        result = is_admin(mock_request)
        
        # Assert
        assert result is False
    
    def test_deprecated_exports(self):
        """Test that deprecated exports are properly set."""
        from fastmcp.auth.interface import auth_middleware
        
        # These should be None as they're removed
        assert auth_middleware.require_auth is None
        assert auth_middleware.AuthenticationMiddleware is None
        
        # These should be imported from fastapi_auth
        assert auth_middleware.require_roles is not None
        assert auth_middleware.require_admin is not None