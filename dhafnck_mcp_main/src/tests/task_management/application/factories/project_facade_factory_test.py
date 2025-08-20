"""Test suite for ProjectFacadeFactory.

Tests the project facade factory including:
- Facade creation with authentication
- Dependency injection
- Caching mechanisms
- Error handling
- Authentication validation
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
from fastmcp.task_management.application.facades.project_application_facade import ProjectApplicationFacade
from fastmcp.task_management.application.services.project_management_service import ProjectManagementService
from fastmcp.task_management.infrastructure.repositories.project_repository_factory import (
    ProjectRepositoryFactory,
    GlobalRepositoryManager
)
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError,
    InvalidUserIdError
)


class TestProjectFacadeFactory:
    """Test cases for ProjectFacadeFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_project_repository_factory = Mock(spec=ProjectRepositoryFactory)
        self.mock_project_repository = Mock()
        self.mock_project_repository_factory.create.return_value = self.mock_project_repository
        
        self.factory = ProjectFacadeFactory(self.mock_project_repository_factory)
    
    def test_init(self):
        """Test factory initialization."""
        factory = ProjectFacadeFactory()
        assert factory._project_repository_factory is None
        assert factory._facades_cache == {}
        
        factory = ProjectFacadeFactory(self.mock_project_repository_factory)
        assert factory._project_repository_factory == self.mock_project_repository_factory
        assert factory._facades_cache == {}
    
    def test_create_project_facade_success(self):
        """Test successful facade creation with valid user."""
        user_id = "valid-user-123"
        
        facade = self.factory.create_project_facade(user_id=user_id)
        
        assert isinstance(facade, ProjectApplicationFacade)
        # Verify repository factory was called with correct parameters
        self.mock_project_repository_factory.create.assert_called_once_with(user_id=user_id)
        # Verify facade is cached
        assert f"{user_id}" in self.factory._facades_cache
    
    def test_create_project_facade_no_user_id(self):
        """Test facade creation without user ID raises error."""
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            self.factory.create_project_facade(user_id=None)
        
        assert "Project facade creation" in str(exc_info.value)
    
    def test_create_project_facade_empty_user_id(self):
        """Test facade creation with empty user ID raises error."""
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            self.factory.create_project_facade(user_id="")
        
        assert "Project facade creation" in str(exc_info.value)
    
    def test_create_project_facade_default_user_prohibited(self):
        """Test facade creation with prohibited default user ID."""
        with pytest.raises(DefaultUserProhibitedError):
            self.factory.create_project_facade(user_id="default_id")
        
        with pytest.raises(DefaultUserProhibitedError):
            self.factory.create_project_facade(user_id="00000000-0000-0000-0000-000000000000")
    
    def test_create_project_facade_cache_hit(self):
        """Test facade creation returns cached instance."""
        user_id = "user-123"
        
        # Create first facade
        facade1 = self.factory.create_project_facade(user_id=user_id)
        
        # Create second facade with same parameters
        facade2 = self.factory.create_project_facade(user_id=user_id)
        
        # Should be the same instance
        assert facade1 is facade2
        # Repository factory should only be called once
        self.mock_project_repository_factory.create.assert_called_once()
    
    @patch('fastmcp.task_management.application.factories.project_facade_factory.GlobalRepositoryManager')
    def test_create_project_facade_no_factory_uses_global(self, mock_global_manager):
        """Test facade creation without repository factory uses global manager."""
        factory = ProjectFacadeFactory()  # No repository factory
        mock_repo = Mock()
        mock_global_manager.get_default.return_value = mock_repo
        
        user_id = "user-123"
        facade = factory.create_project_facade(user_id=user_id)
        
        assert isinstance(facade, ProjectApplicationFacade)
        mock_global_manager.get_default.assert_called_once()
    
    def test_clear_cache(self):
        """Test clearing the facade cache."""
        user_id = "user-123"
        
        # Create facade to populate cache
        self.factory.create_project_facade(user_id=user_id)
        assert len(self.factory._facades_cache) == 1
        
        # Clear cache
        self.factory.clear_cache()
        assert len(self.factory._facades_cache) == 0
    
    def test_get_cached_facade_exists(self):
        """Test getting cached facade when it exists."""
        user_id = "user-123"
        
        # Create facade first
        original_facade = self.factory.create_project_facade(user_id=user_id)
        
        # Get from cache
        cached_facade = self.factory.get_cached_facade(user_id=user_id)
        
        assert cached_facade is original_facade
    
    def test_get_cached_facade_not_exists(self):
        """Test getting cached facade when it doesn't exist."""
        user_id = "user-123"
        
        cached_facade = self.factory.get_cached_facade(user_id=user_id)
        
        assert cached_facade is None
    
    def test_get_cached_facade_requires_auth(self):
        """Test getting cached facade requires authentication."""
        with pytest.raises(UserAuthenticationRequiredError):
            self.factory.get_cached_facade(user_id=None)
        
        with pytest.raises(UserAuthenticationRequiredError):
            self.factory.get_cached_facade(user_id="")
        
        with pytest.raises(DefaultUserProhibitedError):
            self.factory.get_cached_facade(user_id="default_id")
    
    @patch('fastmcp.task_management.application.factories.project_facade_factory.AuthConfig')
    def test_create_project_facade_compatibility_mode(self, mock_auth_config):
        """Test facade creation in compatibility mode."""
        # Configure compatibility mode
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "compatibility-default-user"
        
        factory = ProjectFacadeFactory(self.mock_project_repository_factory)
        
        # Create facade without user ID
        facade = factory.create_project_facade(user_id=None)
        
        assert isinstance(facade, ProjectApplicationFacade)
        # Verify compatibility mode was used
        mock_auth_config.is_default_user_allowed.assert_called()
        mock_auth_config.get_fallback_user_id.assert_called()
        mock_auth_config.log_authentication_bypass.assert_called_with(
            "Project facade creation", "compatibility mode"
        )
        # Verify repository was created with fallback user
        self.mock_project_repository_factory.create.assert_called_once_with(
            user_id="compatibility-default-user"
        )
    
    def test_create_project_facade_logging(self, caplog):
        """Test logging during facade creation."""
        user_id = "user-123"
        
        with caplog.at_level(logging.INFO):
            facade = self.factory.create_project_facade(user_id=user_id)
        
        assert f"Created new project facade for {user_id}" in caplog.text
        
        # Test cache hit logging
        with caplog.at_level(logging.DEBUG):
            facade2 = self.factory.create_project_facade(user_id=user_id)
        
        assert f"Returning cached project facade for {user_id}" in caplog.text
    
    def test_facade_service_injection(self):
        """Test that facades are created with proper service injection."""
        user_id = "user-123"
        
        # Spy on service creation
        with patch('fastmcp.task_management.application.factories.project_facade_factory.ProjectManagementService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            facade = self.factory.create_project_facade(user_id=user_id)
            
            # Verify service was created with repository
            mock_service_class.assert_called_once_with(project_repo=self.mock_project_repository)
    
    def test_thread_safety(self):
        """Test thread safety of facade creation and caching."""
        import threading
        
        results = []
        errors = []
        
        def create_facade(user_id):
            try:
                facade = self.factory.create_project_facade(user_id=user_id)
                results.append((user_id, facade))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads with same user ID
        user_id = "user-123"
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_facade, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check no errors
        assert len(errors) == 0
        
        # All facades should be the same instance (cached)
        if results:
            first_facade = results[0][1]
            for _, facade in results:
                assert facade is first_facade
    
    def test_cache_key_generation(self):
        """Test cache key generation for different users."""
        user1 = "user-123"
        user2 = "user-456"
        
        facade1 = self.factory.create_project_facade(user_id=user1)
        facade2 = self.factory.create_project_facade(user_id=user2)
        
        # Different facades for different users
        assert facade1 is not facade2
        assert len(self.factory._facades_cache) == 2
        assert user1 in self.factory._facades_cache
        assert user2 in self.factory._facades_cache
    
    def test_special_characters_in_user_id(self):
        """Test handling of special characters in user ID."""
        special_user_ids = [
            "user@example.com",
            "user-with-dashes",
            "user_with_underscores",
            "user.with.dots",
            "user+plus@example.com"
        ]
        
        for user_id in special_user_ids:
            facade = self.factory.create_project_facade(user_id=user_id)
            assert isinstance(facade, ProjectApplicationFacade)
            assert user_id in self.factory._facades_cache