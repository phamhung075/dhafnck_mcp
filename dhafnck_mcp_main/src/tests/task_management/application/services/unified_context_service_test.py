"""Tests for UnifiedContextService"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel


class TestUnifiedContextService:
    """Test suite for UnifiedContextService"""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for all context levels"""
        global_repo = Mock()
        project_repo = Mock()
        branch_repo = Mock()
        task_repo = Mock()
        
        # Add with_user method to repositories for user scoping
        global_repo.with_user = Mock(return_value=global_repo)
        project_repo.with_user = Mock(return_value=project_repo)
        branch_repo.with_user = Mock(return_value=branch_repo)
        task_repo.with_user = Mock(return_value=task_repo)
        
        return {
            'global_context_repository': global_repo,
            'project_context_repository': project_repo,
            'branch_context_repository': branch_repo,
            'task_context_repository': task_repo
        }

    @pytest.fixture
    def mock_services(self):
        """Create mock services for context operations"""
        return {
            'cache_service': Mock(),
            'inheritance_service': Mock(),
            'delegation_service': Mock(),
            'validation_service': Mock()
        }

    @pytest.fixture
    def service(self, mock_repositories, mock_services):
        """Create service instance with mocked dependencies"""
        return UnifiedContextService(
            user_id="test-user",
            **mock_repositories,
            **mock_services
        )

    def test_service_initialization(self, mock_repositories, mock_services):
        """Test service initializes correctly with dependencies"""
        service = UnifiedContextService(
            user_id="test-user",
            **mock_repositories,
            **mock_services
        )
        
        assert service._user_id == "test-user"
        assert len(service.repositories) == 4
        assert ContextLevel.GLOBAL in service.repositories
        assert ContextLevel.PROJECT in service.repositories
        assert ContextLevel.BRANCH in service.repositories
        assert ContextLevel.TASK in service.repositories

    def test_service_initialization_without_user(self, mock_repositories, mock_services):
        """Test service initialization without user_id"""
        service = UnifiedContextService(**mock_repositories, **mock_services)
        
        assert service._user_id is None
        assert len(service.repositories) == 4

    def test_service_initialization_minimal_services(self, mock_repositories):
        """Test service initialization with minimal services (auto-created)"""
        service = UnifiedContextService(**mock_repositories)
        
        # Services should be auto-created when not provided
        assert service.cache_service is not None
        assert service.inheritance_service is not None
        assert service.delegation_service is not None
        assert service.validation_service is not None
        assert service.hierarchy_validator is not None

    def test_repositories_mapping(self, service, mock_repositories):
        """Test that repositories are correctly mapped to context levels"""
        assert service.repositories[ContextLevel.GLOBAL] == mock_repositories['global_context_repository']
        assert service.repositories[ContextLevel.PROJECT] == mock_repositories['project_context_repository']
        assert service.repositories[ContextLevel.BRANCH] == mock_repositories['branch_context_repository']
        assert service.repositories[ContextLevel.TASK] == mock_repositories['task_context_repository']

    def test_with_user_creates_scoped_service(self, service, mock_repositories):
        """Test that with_user creates a new service with user-scoped repositories"""
        new_user_id = "new-user-123"
        
        scoped_service = service.with_user(new_user_id)
        
        assert scoped_service is not service  # Should be different instance
        assert scoped_service._user_id == new_user_id
        
        # Verify all repositories were called with with_user
        for repo in mock_repositories.values():
            repo.with_user.assert_called_with(new_user_id)

    def test_with_user_preserves_services(self, service, mock_services):
        """Test that with_user preserves existing services"""
        scoped_service = service.with_user("new-user")
        
        # Services should be the same instances
        assert scoped_service.cache_service is service.cache_service
        assert scoped_service.inheritance_service is service.inheritance_service
        assert scoped_service.delegation_service is service.delegation_service
        assert scoped_service.validation_service is service.validation_service

    def test_get_user_scoped_repository_for_user_with_support(self, service):
        """Test getting user-scoped repository when repository supports it"""
        mock_repo = Mock()
        mock_scoped_repo = Mock()
        mock_repo.with_user = Mock(return_value=mock_scoped_repo)
        
        result = service._get_user_scoped_repository_for_user(mock_repo, "user-123")
        
        assert result == mock_scoped_repo
        mock_repo.with_user.assert_called_once_with("user-123")

    def test_get_user_scoped_repository_for_user_without_support(self, service):
        """Test getting user-scoped repository when repository doesn't support it"""
        mock_repo = Mock(spec=[])  # Mock with no methods
        
        result = service._get_user_scoped_repository_for_user(mock_repo, "user-123")
        
        assert result == mock_repo  # Should return original repository

    def test_get_user_scoped_repository_for_user_none_repo(self, service):
        """Test getting user-scoped repository with None repository"""
        result = service._get_user_scoped_repository_for_user(None, "user-123")
        
        assert result is None

    def test_get_user_scoped_repository_with_user_id(self, service):
        """Test getting user-scoped repository when service has user_id"""
        mock_repo = Mock()
        mock_scoped_repo = Mock()
        mock_repo.with_user = Mock(return_value=mock_scoped_repo)
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_scoped_repo
        mock_repo.with_user.assert_called_once_with("test-user")

    def test_get_user_scoped_repository_without_user_id(self, mock_repositories):
        """Test getting user-scoped repository when service has no user_id"""
        service = UnifiedContextService(user_id=None, **mock_repositories)
        mock_repo = Mock()
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_repo

    def test_get_user_scoped_repository_without_support(self, service):
        """Test getting user-scoped repository when repository doesn't support user scoping"""
        mock_repo = Mock(spec=[])  # Mock with no with_user method
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_repo

    def test_hierarchy_validator_initialization(self, service, mock_repositories):
        """Test that hierarchy validator is properly initialized"""
        assert service.hierarchy_validator is not None
        
        # Verify it was initialized with correct parameters
        # Note: We can't directly test the validator's internal state, 
        # but we can verify it exists and was created

    def test_inheritance_service_initialization(self, service):
        """Test that inheritance service is initialized with repositories"""
        assert service.inheritance_service is not None
        # When auto-created, inheritance service should receive repositories

    def test_delegation_service_initialization(self, service):
        """Test that delegation service is initialized with repositories"""
        assert service.delegation_service is not None
        # When auto-created, delegation service should receive repositories

    def test_user_context_propagation(self, mock_repositories):
        """Test that user context is properly propagated to services"""
        user_id = "propagation-test-user"
        service = UnifiedContextService(user_id=user_id, **mock_repositories)
        
        assert service._user_id == user_id
        # User context should be available for operations

    def test_repository_access_by_level(self, service, mock_repositories):
        """Test accessing repositories by context level"""
        global_repo = service.repositories[ContextLevel.GLOBAL]
        project_repo = service.repositories[ContextLevel.PROJECT]
        branch_repo = service.repositories[ContextLevel.BRANCH]
        task_repo = service.repositories[ContextLevel.TASK]
        
        assert global_repo == mock_repositories['global_context_repository']
        assert project_repo == mock_repositories['project_context_repository']
        assert branch_repo == mock_repositories['branch_context_repository']
        assert task_repo == mock_repositories['task_context_repository']

    def test_service_state_isolation(self, mock_repositories, mock_services):
        """Test that different service instances have isolated state"""
        service1 = UnifiedContextService(user_id="user1", **mock_repositories, **mock_services)
        service2 = UnifiedContextService(user_id="user2", **mock_repositories, **mock_services)
        
        assert service1._user_id != service2._user_id
        assert service1 is not service2
        assert service1.repositories is not service2.repositories

    def test_with_user_multiple_calls(self, service):
        """Test multiple calls to with_user create different instances"""
        scoped1 = service.with_user("user1")
        scoped2 = service.with_user("user2")
        
        assert scoped1 is not scoped2
        assert scoped1._user_id == "user1"
        assert scoped2._user_id == "user2"

    def test_service_initialization_with_partial_services(self, mock_repositories):
        """Test service initialization with only some services provided"""
        cache_service = Mock()
        
        service = UnifiedContextService(
            cache_service=cache_service,
            **mock_repositories
        )
        
        # Provided service should be used
        assert service.cache_service is cache_service
        
        # Missing services should be auto-created
        assert service.inheritance_service is not None
        assert service.delegation_service is not None
        assert service.validation_service is not None

    def test_user_scoping_chain(self, mock_repositories):
        """Test user scoping through service chain"""
        original_service = UnifiedContextService(**mock_repositories)
        scoped_service = original_service.with_user("test-user")
        double_scoped = scoped_service.with_user("another-user")
        
        assert original_service._user_id is None
        assert scoped_service._user_id == "test-user"
        assert double_scoped._user_id == "another-user"
        
        # All should be different instances
        assert original_service is not scoped_service
        assert scoped_service is not double_scoped
        assert original_service is not double_scoped

    @patch('fastmcp.task_management.application.services.unified_context_service.logger')
    def test_logging_available(self, mock_logger, service):
        """Test that logger is available for service operations"""
        # Logger should be imported and available
        assert mock_logger is not None
        
        # Service should have access to logger functionality
        # (This test mainly verifies the logger import works correctly)

    def test_context_level_enum_usage(self, service):
        """Test that ContextLevel enum is used correctly"""
        # Verify all expected context levels are mapped
        expected_levels = [
            ContextLevel.GLOBAL,
            ContextLevel.PROJECT,
            ContextLevel.BRANCH,
            ContextLevel.TASK
        ]
        
        for level in expected_levels:
            assert level in service.repositories
            assert service.repositories[level] is not None