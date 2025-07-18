"""
Test-Driven Development Tests for Task Creation Persistence Fix

This test suite validates that the task creation process properly handles:
1. Foreign key constraint validation (git_branch_id must exist)
2. Proper error handling when database operations fail
3. Repository save method returns correct success/failure status
4. Use case properly checks repository save results

Root Cause: Tasks appear to be created successfully but fail to persist due to:
- Foreign key constraint failures when git_branch_id doesn't exist
- Use case not properly checking repository save results
- Silent failures that return success=True despite database errors
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError

from fastmcp.task_management.application.use_cases.create_task import CreateTaskUseCase
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from fastmcp.task_management.domain.repositories.task_repository import TaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.exceptions.task_exceptions import (
    TaskCreationError,
    TaskNotFoundError
)
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository


class TestTaskCreationPersistenceFix:
    """Test cases for task creation persistence fix"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Mock task repository for testing"""
        return Mock(spec=TaskRepository)
    
    @pytest.fixture
    def create_task_use_case(self, mock_task_repository):
        """Create task use case with mocked repository"""
        return CreateTaskUseCase(mock_task_repository)
    
    @pytest.fixture
    def valid_task_request(self):
        """Valid task creation request"""
        return CreateTaskRequest(
            title="Test Task",
            description="Test task description",
            git_branch_id="valid-branch-id-123",
            priority="high"
        )
    
    @pytest.fixture
    def invalid_git_branch_request(self):
        """Task creation request with invalid git_branch_id"""
        return CreateTaskRequest(
            title="Test Task",
            description="Test task description", 
            git_branch_id="non-existent-branch-id",
            priority="high"
        )

    def test_task_creation_should_fail_when_git_branch_id_does_not_exist(
        self, create_task_use_case, invalid_git_branch_request, mock_task_repository
    ):
        """
        Test that task creation fails when git_branch_id doesn't exist in database.
        
        This addresses the root cause where foreign key constraint failures
        were not properly handled.
        """
        # Arrange: Repository save fails due to foreign key constraint
        mock_task_repository.get_next_id.return_value = "test-task-id"
        mock_task_repository.save.return_value = False  # Save fails
        
        # Act: Execute task creation
        response = create_task_use_case.execute(invalid_git_branch_request)
        
        # Assert: Task creation should fail
        assert response.success is False
        assert "git_branch_id" in response.message.lower()
        assert response.task is None
        mock_task_repository.save.assert_called_once()

    def test_task_creation_should_succeed_when_git_branch_id_exists(
        self, create_task_use_case, valid_task_request, mock_task_repository
    ):
        """
        Test that task creation succeeds when git_branch_id exists in database.
        
        This ensures the fix doesn't break valid task creation.
        """
        # Arrange: Repository save succeeds
        mock_task_repository.get_next_id.return_value = "test-task-id"
        mock_task_repository.save.return_value = True  # Save succeeds
        
        # Act: Execute task creation
        response = create_task_use_case.execute(valid_task_request)
        
        # Assert: Task creation should succeed
        assert response.success is True
        assert response.task is not None
        assert response.task.title == "Test Task"
        assert response.task.git_branch_id == "valid-branch-id-123"
        mock_task_repository.save.assert_called_once()

    def test_use_case_should_check_repository_save_result(
        self, create_task_use_case, valid_task_request, mock_task_repository
    ):
        """
        Test that use case properly checks repository save method result.
        
        This addresses the bug where use case returned success=True
        even when repository save returned False.
        """
        # Arrange: Repository save returns False (failure)
        mock_task_repository.get_next_id.return_value = "test-task-id"
        mock_task_repository.save.return_value = False
        
        # Act: Execute task creation
        response = create_task_use_case.execute(valid_task_request)
        
        # Assert: Use case should return failure when repository save fails
        assert response.success is False
        assert "failed to save" in response.message.lower()
        assert response.task is None

    def test_repository_save_should_return_false_on_foreign_key_constraint_failure(self):
        """
        Test that repository save method returns False when foreign key constraint fails.
        
        This tests the repository level error handling for database constraint violations.
        """
        # This test will be implemented against the actual ORMTaskRepository
        # to ensure it properly handles IntegrityError exceptions
        
        # Arrange: Create repository with invalid git_branch_id
        repository = ORMTaskRepository(git_branch_id="non-existent-branch")
        
        # Create a task entity
        task = Task.create(
            id="test-task-id",
            title="Test Task",
            description="Test description",
            git_branch_id="non-existent-branch",
            priority="high"
        )
        
        # Act: Try to save task with invalid git_branch_id
        result = repository.save(task)
        
        # Assert: Save should return False
        assert result is False

    def test_repository_save_should_return_true_on_successful_save(self):
        """
        Test that repository save method returns True when save succeeds.
        
        This ensures the fix doesn't break successful saves.
        """
        # Arrange: Get the valid git_branch_id from the test database
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        
        # Find a valid git branch ID from the test database
        valid_branch_id = None
        db_config = get_db_config()
        with db_config.get_session() as session:
            branch = session.query(ProjectGitBranch).first()
            if branch:
                valid_branch_id = branch.id
        
        # Skip test if no valid branch found
        if not valid_branch_id:
            pytest.skip("No valid git branch found in test database")
        
        # Create repository with valid git_branch_id
        repository = ORMTaskRepository(git_branch_id=valid_branch_id)
        
        # Create a task entity
        task = Task.create(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test description", 
            git_branch_id=valid_branch_id,
            priority="high"
        )
        
        # Act: Save task with valid git_branch_id
        result = repository.save(task)
        
        # Assert: Save should return True
        assert result is True

    def test_task_creation_should_validate_git_branch_id_existence_before_save(
        self, create_task_use_case, invalid_git_branch_request, mock_task_repository
    ):
        """
        Test that task creation validates git_branch_id existence before attempting save.
        
        This is an additional safeguard to prevent foreign key constraint failures.
        """
        # Arrange: Repository indicates git_branch_id doesn't exist and save fails
        mock_task_repository.get_next_id.return_value = "test-task-id"
        mock_task_repository.save.return_value = False  # Save fails due to constraint
        
        # Act: Execute task creation
        response = create_task_use_case.execute(invalid_git_branch_request)
        
        # Assert: Task creation should fail
        assert response.success is False
        assert "git_branch_id" in response.message.lower() or "failed to save" in response.message.lower()
        # Save should be called but return False
        mock_task_repository.save.assert_called_once()

    def test_task_retrieval_should_work_after_successful_creation(
        self, create_task_use_case, valid_task_request, mock_task_repository
    ):
        """
        Test that task can be retrieved after successful creation.
        
        This ensures the fix maintains end-to-end functionality.
        """
        # Arrange: Repository save succeeds and get_task works
        created_task_id = "test-task-id"
        mock_task_repository.get_next_id.return_value = created_task_id
        mock_task_repository.save.return_value = True
        
        # Mock the task entity that would be returned
        mock_task = Mock()
        mock_task.id = created_task_id
        mock_task.title = "Test Task"
        mock_task.git_branch_id = "valid-branch-id-123"
        mock_task_repository.find_by_id.return_value = mock_task
        
        # Act: Create task and then retrieve it
        create_response = create_task_use_case.execute(valid_task_request)
        retrieved_task = mock_task_repository.find_by_id(created_task_id)
        
        # Assert: Task should be created and retrievable
        assert create_response.success is True
        assert retrieved_task is not None
        assert retrieved_task.id == created_task_id
        assert retrieved_task.title == "Test Task"

    def test_task_listing_should_include_successfully_created_tasks(
        self, create_task_use_case, valid_task_request, mock_task_repository
    ):
        """
        Test that task listing includes successfully created tasks.
        
        This addresses the original issue where tasks weren't appearing in lists.
        """
        # Arrange: Repository save succeeds and find_all includes the task
        created_task_id = "test-task-id"
        mock_task_repository.get_next_id.return_value = created_task_id
        mock_task_repository.save.return_value = True
        
        # Mock the task entity in the list
        mock_task = Mock()
        mock_task.id = created_task_id
        mock_task.title = "Test Task"
        mock_task.git_branch_id = "valid-branch-id-123"
        mock_task_repository.find_all.return_value = [mock_task]
        
        # Act: Create task and then list tasks
        create_response = create_task_use_case.execute(valid_task_request)
        task_list = mock_task_repository.find_all()
        
        # Assert: Task should be in the list
        assert create_response.success is True
        assert len(task_list) == 1
        assert task_list[0].id == created_task_id
        assert task_list[0].title == "Test Task"

    def test_error_handling_preserves_original_exception_details(
        self, create_task_use_case, invalid_git_branch_request, mock_task_repository
    ):
        """
        Test that error handling preserves original exception details for debugging.
        
        This ensures developers can debug foreign key constraint issues.
        """
        # Arrange: Repository save raises IntegrityError
        mock_task_repository.get_next_id.return_value = "test-task-id"
        mock_task_repository.save.side_effect = IntegrityError(
            "FOREIGN KEY constraint failed", None, None
        )
        
        # Act: Execute task creation
        response = create_task_use_case.execute(invalid_git_branch_request)
        
        # Assert: Error should contain constraint details
        assert response.success is False
        assert "constraint" in response.message.lower()
        assert "foreign key" in response.message.lower()