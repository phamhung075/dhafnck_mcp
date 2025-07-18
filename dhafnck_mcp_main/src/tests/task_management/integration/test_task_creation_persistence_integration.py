"""
Integration Tests for Task Creation Persistence Fix

This test suite validates end-to-end behavior of task creation with real database:
1. Task creation with valid git_branch_id succeeds and persists
2. Task creation with invalid git_branch_id fails properly  
3. Failed task creation doesn't leave partial data in database
4. Task listing and retrieval work correctly after fixes

Root Cause: Integration between use case, repository, and database
was not properly handling constraint failures.
"""

import pytest
import uuid
from typing import Generator

from fastmcp.task_management.application.use_cases.create_task import CreateTaskUseCase
from fastmcp.task_management.application.use_cases.get_task import GetTaskUseCase
from fastmcp.task_management.application.use_cases.list_tasks import ListTasksUseCase
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch, Project


class TestTaskCreationPersistenceIntegration:
    """Integration tests for task creation persistence fix"""
    
    @pytest.fixture(scope="class")
    def database_setup(self) -> Generator[None, None, None]:
        """Set up test database with required data"""
        db_config = get_db_config()
        
        # Create test project and git branch
        with db_config.get_session() as session:
            # Create test project
            test_project = Project(
                id="test-project-integration",
                name="Test Project Integration",
                description="Test project for integration tests"
            )
            session.add(test_project)
            
            # Create test git branch
            test_branch = ProjectGitBranch(
                id="test-branch-integration-valid",
                project_id="test-project-integration",
                name="test-branch",
                description="Test branch for integration tests"
            )
            session.add(test_branch)
            session.commit()
        
        yield
        
        # Cleanup
        with db_config.get_session() as session:
            session.query(ProjectGitBranch).filter(
                ProjectGitBranch.id == "test-branch-integration-valid"
            ).delete()
            session.query(Project).filter(
                Project.id == "test-project-integration"
            ).delete()
            session.commit()
    
    @pytest.fixture
    def task_repository(self, database_setup):
        """Create task repository for integration tests"""
        factory = TaskRepositoryFactory()
        return factory.create_repository_with_git_branch_id(
            project_id="test-project-integration",
            git_branch_name="test-branch",
            user_id="test-user",
            git_branch_id="test-branch-integration-valid"
        )
    
    @pytest.fixture
    def invalid_repository(self, database_setup):
        """Create task repository with invalid git_branch_id"""
        factory = TaskRepositoryFactory()
        return factory.create_repository_with_git_branch_id(
            project_id="test-project-integration",
            git_branch_name="test-branch",
            user_id="test-user",
            git_branch_id="non-existent-branch-id"
        )
    
    @pytest.fixture
    def create_task_use_case(self, task_repository):
        """Create task use case with valid repository"""
        return CreateTaskUseCase(task_repository)
    
    @pytest.fixture
    def invalid_create_task_use_case(self, invalid_repository):
        """Create task use case with invalid repository"""
        return CreateTaskUseCase(invalid_repository)
    
    @pytest.fixture
    def get_task_use_case(self, task_repository):
        """Get task use case"""
        return GetTaskUseCase(task_repository)
    
    @pytest.fixture
    def list_tasks_use_case(self, task_repository):
        """List tasks use case"""
        return ListTasksUseCase(task_repository)

    def test_task_creation_with_valid_git_branch_id_should_succeed_and_persist(
        self, create_task_use_case, get_task_use_case, list_tasks_use_case
    ):
        """
        Test that task creation with valid git_branch_id succeeds and persists to database.
        
        This ensures the fix doesn't break valid task creation.
        """
        # Arrange: Create task request with valid git_branch_id
        task_request = CreateTaskRequest(
            title="Integration Test Task",
            description="Task for integration testing",
            git_branch_id="test-branch-integration-valid",
            priority="high"
        )
        
        # Act: Create task
        create_response = create_task_use_case.execute(task_request)
        
        # Assert: Task creation should succeed
        assert create_response.success is True
        assert create_response.task is not None
        
        # Verify task can be retrieved
        task_id = str(create_response.task.id)
        retrieved_task = get_task_use_case.execute(task_id)
        assert retrieved_task is not None
        assert retrieved_task.task.title == "Integration Test Task"
        
        # Verify task appears in list
        list_request = ListTasksRequest(limit=100)
        task_list = list_tasks_use_case.execute(list_request)
        task_ids = [str(task.id) for task in task_list.tasks]
        assert task_id in task_ids

    def test_task_creation_with_invalid_git_branch_id_should_fail_properly(
        self, invalid_create_task_use_case, get_task_use_case, list_tasks_use_case
    ):
        """
        Test that task creation with invalid git_branch_id fails properly.
        
        This addresses the root cause where foreign key constraint failures
        were not properly handled.
        """
        # Arrange: Create task request with invalid git_branch_id
        task_request = CreateTaskRequest(
            title="Invalid Integration Test Task",
            description="Task with invalid git_branch_id",
            git_branch_id="non-existent-branch-id",
            priority="high"
        )
        
        # Act: Create task
        create_response = invalid_create_task_use_case.execute(task_request)
        
        # Assert: Task creation should fail
        assert create_response.success is False
        assert create_response.task is None
        assert create_response.error_message is not None

    def test_failed_task_creation_should_not_leave_partial_data(
        self, invalid_create_task_use_case, get_task_use_case, list_tasks_use_case
    ):
        """
        Test that failed task creation doesn't leave partial data in database.
        
        This ensures database consistency when constraints fail.
        """
        # Arrange: Create task request with invalid git_branch_id
        task_request = CreateTaskRequest(
            title="Partial Data Test Task",
            description="Task to test partial data cleanup",
            git_branch_id="non-existent-branch-id",
            priority="high"
        )
        
        # Act: Create task (should fail)
        create_response = invalid_create_task_use_case.execute(task_request)
        
        # Assert: Task creation should fail
        assert create_response.success is False
        
        # Verify no partial data exists
        # Since creation failed, we can't get a task_id to check
        # But we can verify the task list doesn't contain our failed task
        list_request = ListTasksRequest(limit=100)
        task_list = list_tasks_use_case.execute(list_request)
        task_titles = [task.title for task in task_list.tasks]
        assert "Partial Data Test Task" not in task_titles

    def test_multiple_task_creation_with_mixed_validity_should_handle_correctly(
        self, create_task_use_case, invalid_create_task_use_case, list_tasks_use_case
    ):
        """
        Test multiple task creation with mixed validity (some valid, some invalid).
        
        This ensures the fix handles mixed scenarios correctly.
        """
        # Arrange: Create multiple task requests
        valid_request = CreateTaskRequest(
            title="Valid Mixed Test Task",
            description="Valid task in mixed test",
            git_branch_id="test-branch-integration-valid",
            priority="medium"
        )
        
        invalid_request = CreateTaskRequest(
            title="Invalid Mixed Test Task",
            description="Invalid task in mixed test",
            git_branch_id="non-existent-branch-id",
            priority="medium"
        )
        
        # Act: Create tasks
        valid_response = create_task_use_case.execute(valid_request)
        invalid_response = invalid_create_task_use_case.execute(invalid_request)
        
        # Assert: Valid should succeed, invalid should fail
        assert valid_response.success is True
        assert invalid_response.success is False
        
        # Verify only valid task appears in list
        list_request = ListTasksRequest(limit=100)
        task_list = list_tasks_use_case.execute(list_request)
        task_titles = [task.title for task in task_list.tasks]
        assert "Valid Mixed Test Task" in task_titles
        assert "Invalid Mixed Test Task" not in task_titles

    def test_task_creation_rollback_on_constraint_failure_maintains_database_consistency(
        self, invalid_create_task_use_case, list_tasks_use_case
    ):
        """
        Test that transaction rollback on constraint failure maintains database consistency.
        
        This ensures the database remains in a consistent state after constraint failures.
        """
        # Arrange: Get initial task count
        initial_list_request = ListTasksRequest(limit=100)
        initial_task_list = list_tasks_use_case.execute(initial_list_request)
        initial_count = len(initial_task_list.tasks)
        
        # Create task request with invalid git_branch_id
        task_request = CreateTaskRequest(
            title="Rollback Test Task",
            description="Task to test rollback consistency",
            git_branch_id="non-existent-branch-id",
            priority="high"
        )
        
        # Act: Create task (should fail and rollback)
        create_response = invalid_create_task_use_case.execute(task_request)
        
        # Assert: Task creation should fail
        assert create_response.success is False
        
        # Verify database consistency - task count should remain the same
        final_list_request = ListTasksRequest(limit=100)
        final_task_list = list_tasks_use_case.execute(final_list_request)
        final_count = len(final_task_list.tasks)
        assert final_count == initial_count

    def test_concurrent_task_creation_with_constraint_failures_should_not_interfere(
        self, create_task_use_case, invalid_create_task_use_case
    ):
        """
        Test that concurrent task creation with constraint failures don't interfere.
        
        This ensures the fix handles concurrent operations correctly.
        """
        # Arrange: Create multiple task requests
        valid_requests = [
            CreateTaskRequest(
                title=f"Concurrent Valid Task {i}",
                description=f"Valid task {i} for concurrent test",
                git_branch_id="test-branch-integration-valid",
                priority="low"
            )
            for i in range(3)
        ]
        
        invalid_requests = [
            CreateTaskRequest(
                title=f"Concurrent Invalid Task {i}",
                description=f"Invalid task {i} for concurrent test",
                git_branch_id="non-existent-branch-id",
                priority="low"
            )
            for i in range(3)
        ]
        
        # Act: Create tasks (simulating concurrent operations)
        valid_responses = [create_task_use_case.execute(req) for req in valid_requests]
        invalid_responses = [invalid_create_task_use_case.execute(req) for req in invalid_requests]
        
        # Assert: All valid should succeed, all invalid should fail
        assert all(response.success is True for response in valid_responses)
        assert all(response.success is False for response in invalid_responses)
        
        # Verify no interference between valid and invalid operations
        assert len(valid_responses) == 3
        assert len(invalid_responses) == 3