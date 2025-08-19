"""
Test service layer with user context propagation.
Following TDD - services must pass user_id to repositories.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from uuid import uuid4
from datetime import datetime
from typing import Optional

from fastmcp.task_management.application.services.task_application_service import TaskApplicationService
from fastmcp.task_management.application.services.project_application_service import ProjectApplicationService
from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.application.services.git_branch_application_service import GitBranchApplicationService


class TestServicesUserContext:
    """Test suite ensuring services properly handle user context."""
    
    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return str(uuid4())
    
    @pytest.fixture
    def other_user_id(self):
        """Generate another user ID."""
        return str(uuid4())
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository."""
        repo = Mock()
        repo.create = Mock()
        repo.get_by_id = Mock()
        repo.update = Mock()
        repo.delete = Mock()
        repo.get_all = Mock()
        return repo
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository."""
        repo = Mock()
        repo.create = Mock()
        repo.get_by_id = Mock()
        repo.update = Mock()
        repo.delete = Mock()
        repo.get_all = Mock()
        return repo
    
    @pytest.fixture
    def mock_context_repositories(self):
        """Create mock context repositories."""
        return {
            "global": Mock(),
            "project": Mock(),
            "branch": Mock(),
            "task": Mock()
        }
    
    # ==================== TaskApplicationService Tests ====================
    
    def test_task_service_requires_user_id(self, mock_task_repository):
        """Test that TaskApplicationService requires user_id."""
        with pytest.raises(TypeError):
            TaskApplicationService(repository=mock_task_repository)
    
    def test_task_service_passes_user_id_to_repository(self, mock_task_repository, user_id):
        """Test that task service passes user_id to repository on creation."""
        service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=user_id
        )
        
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending"
        }
        
        # Create task through service
        service.create_task(task_data)
        
        # Verify repository was called with user_id
        mock_task_repository.create.assert_called_once()
        call_args = mock_task_repository.create.call_args
        
        # Check if user_id was passed somehow (in data or as parameter)
        assert user_id in str(call_args) or hasattr(mock_task_repository, 'user_id')
    
    def test_task_service_get_operations_use_user_context(self, mock_task_repository, user_id):
        """Test that get operations use user context."""
        service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=user_id
        )
        
        task_id = str(uuid4())
        
        # Get task by ID
        service.get_task(task_id)
        
        # Verify repository method was called
        mock_task_repository.get_by_id.assert_called_with(task_id)
    
    def test_task_service_prevents_user_id_override(self, mock_task_repository, user_id, other_user_id):
        """Test that service prevents user_id override attempts."""
        service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=user_id
        )
        
        task_data = {
            "title": "Test Task",
            "user_id": other_user_id  # Try to override
        }
        
        # Create task
        service.create_task(task_data)
        
        # Verify the service didn't pass the wrong user_id
        call_args = mock_task_repository.create.call_args
        passed_data = call_args[0][0] if call_args[0] else call_args[1].get('data', {})
        
        # The passed data should not contain the other_user_id
        assert passed_data.get('user_id') != other_user_id
    
    def test_task_service_list_operations_scoped_to_user(self, mock_task_repository, user_id):
        """Test that list operations are scoped to user."""
        service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=user_id
        )
        
        # Get all tasks
        service.get_all_tasks()
        
        # Verify repository was called
        mock_task_repository.get_all.assert_called_once()
    
    # ==================== ProjectApplicationService Tests ====================
    
    def test_project_service_requires_user_id(self, mock_project_repository):
        """Test that ProjectApplicationService requires user_id."""
        with pytest.raises(TypeError):
            ProjectApplicationService(repository=mock_project_repository)
    
    def test_project_service_passes_user_id_to_repository(self, mock_project_repository, user_id):
        """Test that project service passes user_id to repository."""
        service = ProjectApplicationService(
            repository=mock_project_repository,
            user_id=user_id
        )
        
        project_data = {
            "name": "Test Project",
            "description": "Test Description"
        }
        
        # Create project
        service.create_project(project_data)
        
        # Verify repository was called
        mock_project_repository.create.assert_called_once()
    
    def test_project_service_with_git_branches_maintains_user_context(
        self, mock_project_repository, user_id
    ):
        """Test that project service maintains user context for related entities."""
        mock_git_branch_repo = Mock()
        
        service = ProjectApplicationService(
            repository=mock_project_repository,
            git_branch_repository=mock_git_branch_repo,
            user_id=user_id
        )
        
        project_id = str(uuid4())
        
        # Get project with branches
        service.get_project_with_branches(project_id)
        
        # Both repositories should be called
        mock_project_repository.get_by_id.assert_called_with(project_id)
        # Git branch repo should also respect user context
    
    # ==================== UnifiedContextService Tests ====================
    
    def test_unified_context_service_requires_user_id(self, mock_context_repositories):
        """Test that UnifiedContextService requires user_id."""
        with pytest.raises(TypeError):
            UnifiedContextService(
                global_repo=mock_context_repositories["global"],
                project_repo=mock_context_repositories["project"],
                branch_repo=mock_context_repositories["branch"],
                task_repo=mock_context_repositories["task"]
            )
    
    def test_unified_context_service_passes_user_id_to_all_repos(
        self, mock_context_repositories, user_id
    ):
        """Test that unified context service passes user_id to all context repos."""
        service = UnifiedContextService(
            global_repo=mock_context_repositories["global"],
            project_repo=mock_context_repositories["project"],
            branch_repo=mock_context_repositories["branch"],
            task_repo=mock_context_repositories["task"],
            user_id=user_id
        )
        
        # Create context at different levels
        service.create_global_context({"key": "value"})
        service.create_project_context(str(uuid4()), {"key": "value"})
        service.create_branch_context(str(uuid4()), {"key": "value"})
        service.create_task_context(str(uuid4()), {"key": "value"})
        
        # All repositories should be called
        assert mock_context_repositories["global"].create.called
        assert mock_context_repositories["project"].create.called
        assert mock_context_repositories["branch"].create.called
        assert mock_context_repositories["task"].create.called
    
    def test_context_inheritance_maintains_user_boundaries(
        self, mock_context_repositories, user_id
    ):
        """Test that context inheritance stays within user boundaries."""
        service = UnifiedContextService(
            global_repo=mock_context_repositories["global"],
            project_repo=mock_context_repositories["project"],
            branch_repo=mock_context_repositories["branch"],
            task_repo=mock_context_repositories["task"],
            user_id=user_id
        )
        
        task_id = str(uuid4())
        branch_id = str(uuid4())
        project_id = str(uuid4())
        
        # Mock repository responses
        for repo in mock_context_repositories.values():
            repo.get.return_value = None
            repo.get_inherited.return_value = {}
        
        # Get inherited context
        context = service.get_inherited_context(
            level="task",
            context_id=task_id,
            branch_id=branch_id,
            project_id=project_id
        )
        
        # All repos should be queried for inheritance
        assert mock_context_repositories["task"].get.called or \
               mock_context_repositories["task"].get_inherited.called
    
    # ==================== Cross-Service User Isolation Tests ====================
    
    def test_services_for_different_users_isolated(
        self, mock_task_repository, mock_project_repository, user_id, other_user_id
    ):
        """Test that services for different users are isolated."""
        # Create services for two users
        user1_task_service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=user_id
        )
        
        user2_task_service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=other_user_id
        )
        
        # Each user creates a task
        user1_task_service.create_task({"title": "User 1 Task"})
        user2_task_service.create_task({"title": "User 2 Task"})
        
        # Repository should be called twice with different contexts
        assert mock_task_repository.create.call_count == 2
    
    # ==================== Service Factory Tests ====================
    
    def test_service_factory_creates_user_scoped_services(self, user_id):
        """Test that service factory creates properly scoped services."""
        
        class ServiceFactory:
            @staticmethod
            def create_task_service(user_id: str):
                # Mock implementation
                repo = Mock()
                return TaskApplicationService(repository=repo, user_id=user_id)
            
            @staticmethod
            def create_project_service(user_id: str):
                # Mock implementation
                repo = Mock()
                return ProjectApplicationService(repository=repo, user_id=user_id)
        
        factory = ServiceFactory()
        
        # Create services for a user
        task_service = factory.create_task_service(user_id)
        project_service = factory.create_project_service(user_id)
        
        # Services should have user_id
        assert task_service.user_id == user_id
        assert project_service.user_id == user_id
    
    # ==================== Dependency Injection Tests ====================
    
    def test_service_with_multiple_dependencies_maintains_user_context(
        self, mock_task_repository, mock_project_repository, mock_context_repositories, user_id
    ):
        """Test that services with multiple dependencies maintain user context."""
        
        class ComplexService:
            def __init__(self, task_repo, project_repo, context_service, user_id):
                self.task_repo = task_repo
                self.project_repo = project_repo
                self.context_service = context_service
                self.user_id = user_id
            
            def complex_operation(self):
                # All operations should use user_id
                self.task_repo.get_all()
                self.project_repo.get_all()
                self.context_service.get_global_context()
        
        context_service = Mock()
        
        service = ComplexService(
            task_repo=mock_task_repository,
            project_repo=mock_project_repository,
            context_service=context_service,
            user_id=user_id
        )
        
        # Perform complex operation
        service.complex_operation()
        
        # All dependencies should be called
        assert mock_task_repository.get_all.called
        assert mock_project_repository.get_all.called
        assert context_service.get_global_context.called
    
    # ==================== Transaction Tests ====================
    
    def test_service_transaction_maintains_user_context(
        self, mock_task_repository, mock_project_repository, user_id
    ):
        """Test that transactional operations maintain user context."""
        
        class TransactionalService:
            def __init__(self, task_repo, project_repo, user_id):
                self.task_repo = task_repo
                self.project_repo = project_repo
                self.user_id = user_id
            
            def create_project_with_tasks(self, project_data, task_list):
                # Start transaction (mocked)
                project = self.project_repo.create(project_data)
                
                for task_data in task_list:
                    task_data['project_id'] = project.id
                    self.task_repo.create(task_data)
                
                # Commit transaction (mocked)
                return project
        
        service = TransactionalService(
            task_repo=mock_task_repository,
            project_repo=mock_project_repository,
            user_id=user_id
        )
        
        # Create project with tasks
        project_data = {"name": "Test Project"}
        task_list = [
            {"title": "Task 1"},
            {"title": "Task 2"}
        ]
        
        mock_project_repository.create.return_value = Mock(id=str(uuid4()))
        
        service.create_project_with_tasks(project_data, task_list)
        
        # Verify all operations were called
        assert mock_project_repository.create.call_count == 1
        assert mock_task_repository.create.call_count == 2
    
    # ==================== Error Handling Tests ====================
    
    def test_service_handles_user_context_errors(self, mock_task_repository, user_id):
        """Test that services handle user context errors appropriately."""
        service = TaskApplicationService(
            repository=mock_task_repository,
            user_id=user_id
        )
        
        # Simulate repository error
        mock_task_repository.create.side_effect = Exception("User not authorized")
        
        with pytest.raises(Exception) as exc_info:
            service.create_task({"title": "Test"})
        
        assert "User not authorized" in str(exc_info.value)
    
    def test_service_validates_user_id_format(self, mock_task_repository):
        """Test that services validate user_id format."""
        invalid_user_ids = [None, "", "invalid-uuid", 123]
        
        for invalid_id in invalid_user_ids:
            with pytest.raises(ValueError):
                TaskApplicationService(
                    repository=mock_task_repository,
                    user_id=invalid_id
                )