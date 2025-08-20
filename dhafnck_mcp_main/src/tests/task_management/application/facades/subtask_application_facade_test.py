"""
Tests for Subtask Application Facade

This module tests the SubtaskApplicationFacade functionality including:
- Subtask CRUD operations (create, read, update, delete, complete)
- Context derivation from task IDs
- Repository factory integration
- Backward compatibility with static repositories
- Error handling and validation
- Parameter normalization and legacy support
"""

import pytest
import sqlite3
import tempfile
from unittest.mock import Mock, patch, MagicMock

from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.domain.exceptions import TaskNotFoundError
from fastmcp.task_management.domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError


class TestSubtaskApplicationFacade:
    """Test suite for SubtaskApplicationFacade"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        repo = Mock()
        repo.find_by_id = Mock()
        return repo
    
    @pytest.fixture
    def mock_subtask_repository(self):
        """Create a mock subtask repository"""
        return Mock()
    
    @pytest.fixture
    def mock_task_repository_factory(self):
        """Create a mock task repository factory"""
        factory = Mock()
        factory.create_repository = Mock()
        factory.create_system_repository = Mock()
        return factory
    
    @pytest.fixture
    def mock_subtask_repository_factory(self):
        """Create a mock subtask repository factory"""
        factory = Mock()
        factory.create_subtask_repository = Mock()
        return factory
    
    @pytest.fixture
    def facade_static(self, mock_task_repository, mock_subtask_repository):
        """Create facade instance with static repositories (backward compatibility)"""
        return SubtaskApplicationFacade(
            task_repository=mock_task_repository,
            subtask_repository=mock_subtask_repository
        )
    
    @pytest.fixture
    def facade_factory(self, mock_task_repository_factory, mock_subtask_repository_factory):
        """Create facade instance with repository factories"""
        return SubtaskApplicationFacade(
            task_repository_factory=mock_task_repository_factory,
            subtask_repository_factory=mock_subtask_repository_factory
        )
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task"""
        task = Mock()
        task.git_branch_id = "branch-123"
        return task
    
    @pytest.fixture
    def mock_add_subtask_response(self):
        """Create a mock add subtask response"""
        response = Mock()
        response.subtask = {"id": "subtask-123", "title": "Test Subtask"}
        response.task_id = "task-123"
        response.progress = {"completed": 0, "total": 1}
        return response
    
    @pytest.fixture
    def mock_update_subtask_response(self):
        """Create a mock update subtask response"""
        response = Mock()
        response.to_dict.return_value = {"id": "subtask-123", "title": "Updated Subtask"}
        return response


class TestSubtaskApplicationFacadeStaticRepositories:
    """Test suite for static repository usage (backward compatibility)"""
    
    @pytest.fixture
    def mock_task_repository(self):
        repo = Mock()
        return repo
    
    @pytest.fixture
    def mock_subtask_repository(self):
        return Mock()
    
    @pytest.fixture
    def facade(self, mock_task_repository, mock_subtask_repository):
        return SubtaskApplicationFacade(
            task_repository=mock_task_repository,
            subtask_repository=mock_subtask_repository
        )
    
    def test_initialization_with_static_repositories(self, facade, mock_task_repository, mock_subtask_repository):
        """Test facade initialization with static repositories"""
        assert facade._task_repository == mock_task_repository
        assert facade._subtask_repository == mock_subtask_repository
        assert facade._add_subtask_use_case is not None
        assert facade._update_subtask_use_case is not None
        assert facade._remove_subtask_use_case is not None
        assert facade._get_subtask_use_case is not None
        assert facade._get_subtasks_use_case is not None
        assert facade._complete_subtask_use_case is not None
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.AddSubtaskUseCase')
    def test_handle_create_subtask_static(self, mock_add_subtask_use_case, facade, mock_add_subtask_response):
        """Test subtask creation with static repositories"""
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = mock_add_subtask_response
        mock_add_subtask_use_case.return_value = mock_use_case_instance
        
        subtask_data = {
            "title": "Test Subtask",
            "description": "Test Description",
            "assignees": ["user-1"],
            "priority": "high"
        }
        
        result = facade.handle_manage_subtask("create", "task-123", subtask_data)
        
        assert result["success"] is True
        assert result["action"] == "create"
        assert result["subtask"] == mock_add_subtask_response.subtask
        assert result["task_id"] == mock_add_subtask_response.task_id
        assert result["progress"] == mock_add_subtask_response.progress
        assert "Test Subtask" in result["message"]
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.UpdateSubtaskUseCase')
    def test_handle_update_subtask_static(self, mock_update_subtask_use_case, facade, mock_update_subtask_response):
        """Test subtask update with static repositories"""
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = mock_update_subtask_response
        mock_update_subtask_use_case.return_value = mock_use_case_instance
        
        subtask_data = {
            "subtask_id": "subtask-123",
            "title": "Updated Subtask",
            "status": "in_progress",
            "progress_percentage": 50
        }
        
        result = facade.handle_manage_subtask("update", "task-123", subtask_data)
        
        assert result["success"] is True
        assert result["action"] == "update"
        assert result["subtask"] == mock_update_subtask_response.to_dict()
        assert "subtask-123" in result["message"]
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.RemoveSubtaskUseCase')
    def test_handle_delete_subtask_static(self, mock_remove_subtask_use_case, facade):
        """Test subtask deletion with static repositories"""
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = {
            "success": True,
            "progress": {"completed": 0, "total": 0}
        }
        mock_remove_subtask_use_case.return_value = mock_use_case_instance
        
        subtask_data = {"subtask_id": "subtask-123"}
        
        result = facade.handle_manage_subtask("delete", "task-123", subtask_data)
        
        assert result["success"] is True
        assert result["action"] == "delete"
        assert "subtask-123" in result["message"]
        assert "progress" in result
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.GetSubtasksUseCase')
    def test_handle_list_subtasks_static(self, mock_get_subtasks_use_case, facade):
        """Test listing subtasks with static repositories"""
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = {
            "subtasks": [{"id": "subtask-1"}, {"id": "subtask-2"}],
            "progress": {"completed": 1, "total": 2}
        }
        mock_get_subtasks_use_case.return_value = mock_use_case_instance
        
        result = facade.handle_manage_subtask("list", "task-123")
        
        assert result["success"] is True
        assert result["action"] == "list"
        assert len(result["subtasks"]) == 2
        assert "progress" in result
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.GetSubtaskUseCase')
    def test_handle_get_subtask_static(self, mock_get_subtask_use_case, facade):
        """Test getting specific subtask with static repositories"""
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = {
            "subtask": {"id": "subtask-123", "title": "Test Subtask"},
            "progress": {"completed": 0, "total": 1}
        }
        mock_get_subtask_use_case.return_value = mock_use_case_instance
        
        subtask_data = {"subtask_id": "subtask-123"}
        
        result = facade.handle_manage_subtask("get", "task-123", subtask_data)
        
        assert result["success"] is True
        assert result["action"] == "get"
        assert result["subtask"]["id"] == "subtask-123"
        assert "progress" in result
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.CompleteSubtaskUseCase')
    def test_handle_complete_subtask_static(self, mock_complete_subtask_use_case, facade):
        """Test completing subtask with static repositories"""
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = {
            "success": True,
            "progress": {"completed": 1, "total": 1}
        }
        mock_complete_subtask_use_case.return_value = mock_use_case_instance
        
        subtask_data = {"subtask_id": "subtask-123"}
        
        result = facade.handle_manage_subtask("complete", "task-123", subtask_data)
        
        assert result["success"] is True
        assert result["action"] == "complete"
        assert result["subtask"]["completed"] is True
        assert "progress" in result


class TestSubtaskApplicationFacadeFactoryRepositories:
    """Test suite for factory-based repository usage"""
    
    @pytest.fixture
    def mock_task_repository_factory(self):
        factory = Mock()
        factory.create_repository = Mock()
        factory.create_system_repository = Mock()
        return factory
    
    @pytest.fixture
    def mock_subtask_repository_factory(self):
        factory = Mock()
        factory.create_subtask_repository = Mock()
        return factory
    
    @pytest.fixture
    def facade(self, mock_task_repository_factory, mock_subtask_repository_factory):
        return SubtaskApplicationFacade(
            task_repository_factory=mock_task_repository_factory,
            subtask_repository_factory=mock_subtask_repository_factory
        )
    
    def test_initialization_with_factories(self, facade, mock_task_repository_factory, mock_subtask_repository_factory):
        """Test facade initialization with repository factories"""
        assert facade._task_repository_factory == mock_task_repository_factory
        assert facade._subtask_repository_factory == mock_subtask_repository_factory
        assert facade._add_subtask_use_case is None  # Created dynamically
        assert facade._update_subtask_use_case is None
        assert facade._remove_subtask_use_case is None
    
    @patch('fastmcp.task_management.application.facades.subtask_application_facade.AddSubtaskUseCase')
    def test_handle_create_subtask_with_context_derivation(self, mock_add_subtask_use_case, facade, mock_task_repository_factory, mock_subtask_repository_factory, mock_add_subtask_response):
        """Test subtask creation with context derivation"""
        # Mock task for context derivation
        mock_task = Mock()
        mock_task.git_branch_id = "branch-123"
        
        # Mock system repository
        mock_system_repo = Mock()
        mock_system_repo.find_by_id.return_value = mock_task
        mock_task_repository_factory.create_system_repository.return_value = mock_system_repo
        
        # Mock context repositories
        mock_task_repo = Mock()
        mock_subtask_repo = Mock()
        mock_task_repository_factory.create_repository.return_value = mock_task_repo
        mock_subtask_repository_factory.create_subtask_repository.return_value = mock_subtask_repo
        
        # Mock use case
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = mock_add_subtask_response
        mock_add_subtask_use_case.return_value = mock_use_case_instance
        
        # Mock database access for context derivation
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.get_database_path') as mock_get_db_path:
            with patch('sqlite3.connect') as mock_connect:
                mock_get_db_path.return_value = "/test/db.sqlite"
                
                # Mock database connection and rows
                mock_conn = Mock()
                mock_connect.return_value.__enter__.return_value = mock_conn
                
                mock_branch_row = {'project_id': 'project-123', 'name': 'feature-branch'}
                mock_project_row = {'user_id': 'user-123'}
                
                mock_conn.execute.side_effect = [
                    Mock(fetchone=Mock(return_value=mock_branch_row)),  # branch query
                    Mock(fetchone=Mock(return_value=mock_project_row))  # project query
                ]
                
                subtask_data = {"title": "Test Subtask"}
                
                result = facade.handle_manage_subtask("create", "task-123", subtask_data)
                
                # Verify context was derived and repositories were created
                mock_task_repository_factory.create_repository.assert_called_once_with(
                    "project-123", "feature-branch", "user-123"
                )
                mock_subtask_repository_factory.create_subtask_repository.assert_called_once_with(
                    "project-123", "feature-branch", "user-123"
                )
                
                assert result["success"] is True


class TestSubtaskApplicationFacadeParameterHandling:
    """Test suite for parameter handling and validation"""
    
    @pytest.fixture
    def facade(self):
        return SubtaskApplicationFacade(
            task_repository=Mock(),
            subtask_repository=Mock()
        )
    
    def test_missing_task_id_validation(self, facade):
        """Test validation when task_id is missing"""
        with pytest.raises(ValueError, match="Task ID is required"):
            facade.handle_manage_subtask("create", "")
    
    def test_invalid_action_validation(self, facade):
        """Test validation for invalid actions"""
        with pytest.raises(ValueError, match="Unsupported subtask action"):
            facade.handle_manage_subtask("invalid_action", "task-123")
    
    def test_create_missing_title_validation(self, facade):
        """Test validation when creating subtask without title"""
        with pytest.raises(ValueError, match="subtask_data with title is required"):
            facade.handle_manage_subtask("create", "task-123", {})
    
    def test_update_missing_subtask_id_validation(self, facade):
        """Test validation when updating without subtask_id"""
        with pytest.raises(ValueError, match="subtask_data with subtask_id is required"):
            facade.handle_manage_subtask("update", "task-123", {"title": "New Title"})
    
    def test_delete_missing_subtask_id_validation(self, facade):
        """Test validation when deleting without subtask_id"""
        with pytest.raises(ValueError, match="subtask_data with subtask_id is required"):
            facade.handle_manage_subtask("delete", "task-123", {})
    
    def test_get_missing_subtask_id_validation(self, facade):
        """Test validation when getting subtask without subtask_id"""
        with pytest.raises(ValueError, match="subtask_data with subtask_id is required"):
            facade.handle_manage_subtask("get", "task-123", {})
    
    def test_complete_missing_subtask_id_validation(self, facade):
        """Test validation when completing without subtask_id"""
        with pytest.raises(ValueError, match="subtask_data with subtask_id is required"):
            facade.handle_manage_subtask("complete", "task-123", {})
    
    def test_action_normalization(self, facade):
        """Test action normalization (add -> create)"""
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.AddSubtaskUseCase'):
            subtask_data = {"title": "Test Subtask"}
            
            # Should normalize 'add' to 'create'
            result = facade.handle_manage_subtask("add", "task-123", subtask_data)
            assert result["action"] == "create"
    
    def test_legacy_parameter_shuffle(self, facade):
        """Test backward compatibility parameter shuffle"""
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.AddSubtaskUseCase'):
            subtask_data = {"title": "Test Subtask"}
            
            # Legacy call style: (action, task_id, subtask_data)
            # Should be detected and handled correctly
            result = facade.handle_manage_subtask("create", "task-123", subtask_data)
            assert result["action"] == "create"


class TestSubtaskApplicationFacadeContextDerivation:
    """Test suite for context derivation functionality"""
    
    @pytest.fixture
    def mock_task_repository_factory(self):
        factory = Mock()
        factory.create_system_repository = Mock()
        return factory
    
    @pytest.fixture
    def facade(self, mock_task_repository_factory):
        return SubtaskApplicationFacade(
            task_repository_factory=mock_task_repository_factory,
            subtask_repository_factory=Mock()
        )
    
    def test_derive_context_from_task_success(self, facade, mock_task_repository_factory):
        """Test successful context derivation from task"""
        mock_task = Mock()
        mock_task.git_branch_id = "branch-123"
        
        mock_system_repo = Mock()
        mock_system_repo.find_by_id.return_value = mock_task
        mock_task_repository_factory.create_system_repository.return_value = mock_system_repo
        
        with patch.object(facade, '_derive_context_from_git_branch_id') as mock_derive_branch:
            mock_derive_branch.return_value = {
                "project_id": "project-123",
                "git_branch_name": "feature-branch",
                "user_id": "user-123"
            }
            
            result = facade._derive_context_from_task("task-123")
            
            mock_derive_branch.assert_called_once_with("branch-123")
            assert result["project_id"] == "project-123"
    
    def test_derive_context_from_task_not_found(self, facade, mock_task_repository_factory):
        """Test context derivation when task not found"""
        mock_system_repo = Mock()
        mock_system_repo.find_by_id.return_value = None
        mock_task_repository_factory.create_system_repository.return_value = mock_system_repo
        
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.AuthConfig') as mock_auth_config:
            mock_auth_config.is_default_user_allowed.return_value = True
            mock_auth_config.get_fallback_user_id.return_value = "default_user"
            
            result = facade._derive_context_from_task("nonexistent-task")
            
            assert result["project_id"] == "default_project"
            assert result["git_branch_name"] == "main"
            assert result["user_id"] == "default_user"
    
    def test_derive_context_from_git_branch_id_success(self, facade):
        """Test successful context derivation from git branch ID"""
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.get_database_path') as mock_get_db_path:
            with patch('sqlite3.connect') as mock_connect:
                mock_get_db_path.return_value = "/test/db.sqlite"
                
                mock_conn = Mock()
                mock_connect.return_value.__enter__.return_value = mock_conn
                
                mock_branch_row = {'project_id': 'project-123', 'name': 'feature-branch'}
                mock_project_row = {'user_id': 'user-123'}
                
                mock_conn.execute.side_effect = [
                    Mock(fetchone=Mock(return_value=mock_branch_row)),
                    Mock(fetchone=Mock(return_value=mock_project_row))
                ]
                
                result = facade._derive_context_from_git_branch_id("branch-123")
                
                assert result["project_id"] == "project-123"
                assert result["git_branch_name"] == "feature-branch"
                assert result["user_id"] == "user-123"
    
    def test_derive_context_from_git_branch_id_not_found(self, facade):
        """Test context derivation when git branch not found"""
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.get_database_path') as mock_get_db_path:
            with patch('sqlite3.connect') as mock_connect:
                mock_get_db_path.return_value = "/test/db.sqlite"
                
                mock_conn = Mock()
                mock_connect.return_value.__enter__.return_value = mock_conn
                mock_conn.execute.return_value.fetchone.return_value = None
                
                with patch('fastmcp.task_management.application.facades.subtask_application_facade.AuthConfig') as mock_auth_config:
                    mock_auth_config.is_default_user_allowed.return_value = True
                    mock_auth_config.get_fallback_user_id.return_value = "default_user"
                    
                    result = facade._derive_context_from_git_branch_id("nonexistent-branch")
                    
                    assert result["project_id"] == "default_project"
                    assert result["git_branch_name"] == "main"
                    assert result["user_id"] == "default_user"
    
    def test_authentication_required_when_default_not_allowed(self, facade):
        """Test that authentication error is raised when default user not allowed"""
        with patch('fastmcp.task_management.application.facades.subtask_application_facade.AuthConfig') as mock_auth_config:
            mock_auth_config.is_default_user_allowed.return_value = False
            
            with pytest.raises(UserAuthenticationRequiredError):
                facade._derive_context_from_task("task-123")


class TestSubtaskApplicationFacadeRepositorySelection:
    """Test suite for repository selection logic"""
    
    def test_get_context_repositories_with_factories_and_context(self):
        """Test repository selection with factories and full context"""
        mock_task_factory = Mock()
        mock_subtask_factory = Mock()
        mock_task_repo = Mock()
        mock_subtask_repo = Mock()
        
        mock_task_factory.create_repository.return_value = mock_task_repo
        mock_subtask_factory.create_subtask_repository.return_value = mock_subtask_repo
        
        facade = SubtaskApplicationFacade(
            task_repository_factory=mock_task_factory,
            subtask_repository_factory=mock_subtask_factory
        )
        
        task_repo, subtask_repo = facade._get_context_repositories(
            project_id="project-123",
            git_branch_name="feature-branch",
            user_id="user-123"
        )
        
        assert task_repo == mock_task_repo
        assert subtask_repo == mock_subtask_repo
        mock_task_factory.create_repository.assert_called_once_with(
            "project-123", "feature-branch", "user-123"
        )
        mock_subtask_factory.create_subtask_repository.assert_called_once_with(
            "project-123", "feature-branch", "user-123"
        )
    
    def test_get_context_repositories_fallback_to_static(self):
        """Test repository selection fallback to static repositories"""
        mock_task_repo = Mock()
        mock_subtask_repo = Mock()
        
        facade = SubtaskApplicationFacade(
            task_repository=mock_task_repo,
            subtask_repository=mock_subtask_repo
        )
        
        task_repo, subtask_repo = facade._get_context_repositories(
            project_id="project-123",
            git_branch_name="feature-branch",
            user_id="user-123"
        )
        
        assert task_repo == mock_task_repo
        assert subtask_repo == mock_subtask_repo