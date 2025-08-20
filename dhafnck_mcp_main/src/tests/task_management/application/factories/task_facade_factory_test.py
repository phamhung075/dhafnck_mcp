"""
Tests for Task Facade Factory

This module tests the TaskFacadeFactory which creates task application facades
with proper dependency injection following DDD patterns.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock

from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory


class TestTaskFacadeFactory:
    """Test suite for TaskFacadeFactory"""
    
    @pytest.fixture
    def mock_task_repository_factory(self):
        """Create a mock task repository factory"""
        factory = Mock(spec=TaskRepositoryFactory)
        factory.create_repository = Mock()
        factory.create_repository_with_git_branch_id = Mock()
        return factory
    
    @pytest.fixture
    def mock_subtask_repository_factory(self):
        """Create a mock subtask repository factory"""
        factory = Mock(spec=SubtaskRepositoryFactory)
        factory.create_subtask_repository = Mock()
        return factory
    
    @pytest.fixture
    def mock_context_service_factory(self):
        """Create a mock context service factory"""
        factory = Mock()
        factory.create_facade = Mock()
        return factory
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton state before each test"""
        TaskFacadeFactory._instance = None
        TaskFacadeFactory._initialized = False
        yield
        # Clean up after test
        TaskFacadeFactory._instance = None
        TaskFacadeFactory._initialized = False
    
    def test_singleton_pattern(self, mock_task_repository_factory, mock_subtask_repository_factory):
        """Test that TaskFacadeFactory implements singleton pattern"""
        # Create first instance
        factory1 = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
        
        # Create second instance
        factory2 = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
        
        # Verify they are the same instance
        assert factory1 is factory2
    
    def test_get_instance_first_call(self, mock_task_repository_factory, mock_subtask_repository_factory):
        """Test get_instance on first call with required parameters"""
        factory = TaskFacadeFactory.get_instance(
            repository_factory=mock_task_repository_factory,
            subtask_repository_factory=mock_subtask_repository_factory
        )
        
        assert isinstance(factory, TaskFacadeFactory)
        assert factory._repository_factory == mock_task_repository_factory
        assert factory._subtask_repository_factory == mock_subtask_repository_factory
    
    def test_get_instance_without_required_factory(self):
        """Test get_instance on first call without required repository_factory"""
        with pytest.raises(ValueError, match="repository_factory is required for first initialization"):
            TaskFacadeFactory.get_instance()
    
    def test_get_instance_subsequent_calls(self, mock_task_repository_factory):
        """Test get_instance returns same instance on subsequent calls"""
        # First call with factory
        factory1 = TaskFacadeFactory.get_instance(repository_factory=mock_task_repository_factory)
        
        # Second call without factory (should return same instance)
        factory2 = TaskFacadeFactory.get_instance()
        
        assert factory1 is factory2
    
    @patch('fastmcp.task_management.application.factories.task_facade_factory.ContextServiceFactory')
    def test_initialization_with_context_factory(self, mock_context_factory_class, 
                                               mock_task_repository_factory, 
                                               mock_subtask_repository_factory,
                                               mock_context_service_factory):
        """Test initialization with successful context service factory creation"""
        # Setup mock
        mock_context_factory_class.get_instance.return_value = mock_context_service_factory
        
        # Create factory
        factory = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
        
        # Verify
        assert factory._repository_factory == mock_task_repository_factory
        assert factory._subtask_repository_factory == mock_subtask_repository_factory
        assert factory._context_service_factory == mock_context_service_factory
        mock_context_factory_class.get_instance.assert_called_once()
    
    @patch('fastmcp.task_management.application.factories.task_facade_factory.ContextServiceFactory')
    def test_initialization_context_factory_failure(self, mock_context_factory_class,
                                                  mock_task_repository_factory,
                                                  mock_subtask_repository_factory):
        """Test initialization when context service factory fails"""
        # Setup mock to raise exception
        mock_context_factory_class.get_instance.side_effect = Exception("Database not available")
        
        # Create factory
        with patch.object(TaskFacadeFactory.__module__ + '.logger', 'warning') as mock_logger:
            factory = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
            
            # Verify warnings were logged
            assert mock_logger.call_count == 2
            assert "Could not initialize ContextServiceFactory" in str(mock_logger.call_args_list[0])
            assert "Context operations will not be available" in str(mock_logger.call_args_list[1])
        
        # Verify factory still works but without context service
        assert factory._repository_factory == mock_task_repository_factory
        assert factory._subtask_repository_factory == mock_subtask_repository_factory
        assert factory._context_service_factory is None
    
    @patch('fastmcp.task_management.application.factories.task_facade_factory.get_default_user_id')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.normalize_user_id')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.TaskApplicationFacade')
    def test_create_task_facade_with_default_user(self, mock_facade_class, mock_normalize, mock_get_default,
                                                 mock_task_repository_factory,
                                                 mock_subtask_repository_factory,
                                                 mock_context_service_factory):
        """Test creating task facade with default user ID"""
        # Setup mocks
        mock_get_default.return_value = "00000000-0000-0000-0000-000000000000"
        mock_normalize.return_value = "00000000-0000-0000-0000-000000000000"
        mock_task_repo = Mock()
        mock_subtask_repo = Mock()
        mock_context_service = Mock()
        mock_task_repository_factory.create_repository.return_value = mock_task_repo
        mock_subtask_repository_factory.create_subtask_repository.return_value = mock_subtask_repo
        mock_context_service_factory.create_facade.return_value = mock_context_service
        
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        
        # Create factory with context service
        with patch('fastmcp.task_management.application.factories.task_facade_factory.ContextServiceFactory') as mock_context_factory_class:
            mock_context_factory_class.get_instance.return_value = mock_context_service_factory
            factory = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
        
        # Create facade
        result = factory.create_task_facade(project_id="test-project", git_branch_id="branch-123")
        
        # Verify
        mock_get_default.assert_called_once()
        mock_normalize.assert_called_once_with("00000000-0000-0000-0000-000000000000")
        mock_task_repository_factory.create_repository.assert_called_once_with(
            "test-project", "main", "00000000-0000-0000-0000-000000000000"
        )
        mock_subtask_repository_factory.create_subtask_repository.assert_called_once_with("test-project")
        mock_context_service_factory.create_facade.assert_called_once_with(
            user_id="00000000-0000-0000-0000-000000000000",
            project_id="test-project",
            git_branch_id="branch-123"
        )
        mock_facade_class.assert_called_once_with(mock_task_repo, mock_subtask_repo, mock_context_service)
        assert result == mock_facade
    
    @patch('fastmcp.task_management.application.factories.task_facade_factory.normalize_user_id')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.TaskApplicationFacade')
    def test_create_task_facade_with_specific_user(self, mock_facade_class, mock_normalize,
                                                  mock_task_repository_factory):
        """Test creating task facade with specific user ID"""
        # Setup mocks
        mock_normalize.return_value = "user-123-normalized"
        mock_task_repo = Mock()
        mock_task_repository_factory.create_repository.return_value = mock_task_repo
        
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        
        # Create factory without subtask or context factories
        factory = TaskFacadeFactory(mock_task_repository_factory)
        
        # Create facade
        result = factory.create_task_facade(
            project_id="test-project",
            git_branch_id="branch-456",
            user_id="user-123"
        )
        
        # Verify
        mock_normalize.assert_called_once_with("user-123")
        mock_task_repository_factory.create_repository.assert_called_once_with(
            "test-project", "main", "user-123-normalized"
        )
        mock_facade_class.assert_called_once_with(mock_task_repo, None, None)
        assert result == mock_facade
    
    @patch('fastmcp.task_management.application.factories.task_facade_factory.get_default_user_id')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.normalize_user_id')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.TaskApplicationFacade')
    def test_create_task_facade_with_git_branch_id(self, mock_facade_class, mock_normalize, mock_get_default,
                                                   mock_task_repository_factory,
                                                   mock_subtask_repository_factory):
        """Test creating task facade with specific git_branch_id"""
        # Setup mocks
        mock_get_default.return_value = "00000000-0000-0000-0000-000000000000"
        mock_normalize.return_value = "00000000-0000-0000-0000-000000000000"
        mock_task_repo = Mock()
        mock_subtask_repo = Mock()
        mock_task_repository_factory.create_repository_with_git_branch_id.return_value = mock_task_repo
        mock_subtask_repository_factory.create_subtask_repository.return_value = mock_subtask_repo
        
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        
        # Create factory
        factory = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
        
        # Create facade with git_branch_id
        result = factory.create_task_facade_with_git_branch_id(
            project_id="test-project",
            git_branch_name="feature-branch",
            user_id=None,
            git_branch_id="branch-uuid-123"
        )
        
        # Verify
        mock_get_default.assert_called_once()
        mock_task_repository_factory.create_repository_with_git_branch_id.assert_called_once_with(
            "test-project", "feature-branch", "00000000-0000-0000-0000-000000000000", "branch-uuid-123"
        )
        mock_subtask_repository_factory.create_subtask_repository.assert_called_once_with("test-project")
        mock_facade_class.assert_called_once_with(mock_task_repo, mock_subtask_repo, None)
        assert result == mock_facade
    
    @patch('fastmcp.task_management.application.factories.task_facade_factory.normalize_user_id')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.TaskApplicationFacade')
    @patch('fastmcp.task_management.application.factories.task_facade_factory.ContextServiceFactory')
    def test_create_task_facade_with_git_branch_id_and_context(self, mock_context_factory_class, 
                                                               mock_facade_class, mock_normalize,
                                                               mock_task_repository_factory,
                                                               mock_context_service_factory):
        """Test creating task facade with git_branch_id and context service"""
        # Setup mocks
        mock_normalize.return_value = "user-456-normalized"
        mock_task_repo = Mock()
        mock_context_service = Mock()
        mock_task_repository_factory.create_repository_with_git_branch_id.return_value = mock_task_repo
        mock_context_service_factory.create_facade.return_value = mock_context_service
        mock_context_factory_class.get_instance.return_value = mock_context_service_factory
        
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        
        # Create factory
        factory = TaskFacadeFactory(mock_task_repository_factory)
        
        # Create facade
        result = factory.create_task_facade_with_git_branch_id(
            project_id="test-project",
            git_branch_name="hotfix-branch",
            user_id="user-456",
            git_branch_id="branch-uuid-789"
        )
        
        # Verify
        mock_normalize.assert_called_once_with("user-456")
        mock_task_repository_factory.create_repository_with_git_branch_id.assert_called_once_with(
            "test-project", "hotfix-branch", "user-456-normalized", "branch-uuid-789"
        )
        mock_context_service_factory.create_facade.assert_called_once_with(
            user_id="user-456-normalized",
            project_id="test-project",
            git_branch_id="branch-uuid-789"
        )
        mock_facade_class.assert_called_once_with(mock_task_repo, None, mock_context_service)
        assert result == mock_facade
    
    def test_singleton_prevents_reinitialization(self, mock_task_repository_factory, 
                                                mock_subtask_repository_factory):
        """Test that singleton pattern prevents reinitialization"""
        # Create first instance
        factory1 = TaskFacadeFactory(mock_task_repository_factory, mock_subtask_repository_factory)
        
        # Try to create second instance with different factories
        mock_other_task_factory = Mock(spec=TaskRepositoryFactory)
        mock_other_subtask_factory = Mock(spec=SubtaskRepositoryFactory)
        factory2 = TaskFacadeFactory(mock_other_task_factory, mock_other_subtask_factory)
        
        # Verify second initialization was skipped
        assert factory1 is factory2
        assert factory2._repository_factory == mock_task_repository_factory  # Original factory
        assert factory2._subtask_repository_factory == mock_subtask_repository_factory  # Original factory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])