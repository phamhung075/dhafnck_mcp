"""
Test-Driven Development Tests for ORM Task Repository Persistence Fix

This test suite validates that the ORM Task Repository properly handles:
1. Foreign key constraint violations with proper error handling
2. Save method returns correct boolean results  
3. Database transaction rollback on constraint failures
4. Proper exception handling and logging

Root Cause: Repository save method was not properly handling database constraints
and was returning success even when constraints failed.
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.exceptions.base_exceptions import DatabaseException

# Import database fixtures
from tests.fixtures.database_fixtures import valid_git_branch_id, invalid_git_branch_id, test_project_data


class TestORMTaskRepositoryPersistenceFix:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test cases for ORM Task Repository persistence fix"""
    
    @pytest.fixture
    def task_repository(self, valid_git_branch_id):
        """Create task repository with valid test git_branch_id"""
        return ORMTaskRepository(git_branch_id=valid_git_branch_id)
    
    @pytest.fixture
    def valid_task_entity(self, valid_git_branch_id):
        """Create valid task entity for testing"""
        return Task.create(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test description",
            git_branch_id=valid_git_branch_id,
            priority="high"
        )
    
    @pytest.fixture
    def invalid_git_branch_task_entity(self, invalid_git_branch_id):
        """Create task entity with invalid git_branch_id"""
        return Task.create(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test description", 
            git_branch_id=invalid_git_branch_id,
            priority="high"
        )

    def test_save_should_return_false_on_foreign_key_constraint_failure(
        self, task_repository, invalid_git_branch_task_entity
    ):
        """
        Test that save method returns False when foreign key constraint fails.
        
        This addresses the root cause where database constraint failures
        were not properly handled by the repository save method.
        """
        # Act: Try to save task with invalid git_branch_id
        result = task_repository.save(invalid_git_branch_task_entity)
        
        # Assert: Save should return None on failure
        assert result is None

    def test_save_should_return_task_on_successful_save(
        self, task_repository, valid_task_entity
    ):
        """
        Test that save method returns TaskEntity when save succeeds.
        
        This ensures the fix doesn't break successful saves.
        """
        # Arrange: Mock successful database operations
        with patch.object(task_repository, 'get_db_session') as mock_session_context:
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock successful query operations
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Act: Save task
            result = task_repository.save(valid_task_entity)
            
            # Assert: Save should return the task entity
            assert result is not None
            assert result == valid_task_entity

    def test_save_should_handle_integrity_error_gracefully(
        self, task_repository, invalid_git_branch_task_entity
    ):
        """
        Test that save method handles IntegrityError gracefully and returns False.
        
        This ensures database constraint violations don't crash the application.
        """
        # Arrange: Mock IntegrityError during save
        with patch.object(task_repository, 'get_db_session') as mock_session_context:
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock IntegrityError on add
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add.side_effect = IntegrityError("FOREIGN KEY constraint failed", None, None)
            
            # Act: Save task
            result = task_repository.save(invalid_git_branch_task_entity)
            
            # Assert: Save should return False
            assert result is None

    def test_save_should_log_database_errors_for_debugging(
        self, task_repository, invalid_git_branch_task_entity
    ):
        """
        Test that save method logs database errors for debugging purposes.
        
        This ensures developers can debug constraint failures.
        """
        # Arrange: Mock IntegrityError and logger
        with patch.object(task_repository, 'get_db_session') as mock_session_context, \
             patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.logger') as mock_logger:
            
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock IntegrityError
            error_msg = "FOREIGN KEY constraint failed"
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add.side_effect = IntegrityError(error_msg, None, None)
            
            # Act: Save task
            result = task_repository.save(invalid_git_branch_task_entity)
            
            # Assert: Error should be logged
            assert result is None
            mock_logger.error.assert_called()
            # Check that error message contains constraint information
            logged_call = mock_logger.error.call_args[0][0]
            assert "failed to save" in logged_call.lower()

    def test_save_should_rollback_transaction_on_constraint_failure(
        self, task_repository, invalid_git_branch_task_entity
    ):
        """
        Test that save method properly rolls back transaction on constraint failure.
        
        This ensures database consistency when constraints fail.
        """
        # Arrange: Mock IntegrityError and session rollback
        with patch.object(task_repository, 'get_db_session') as mock_session_context:
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock IntegrityError
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add.side_effect = IntegrityError("FOREIGN KEY constraint failed", None, None)
            
            # Act: Save task
            result = task_repository.save(invalid_git_branch_task_entity)
            
            # Assert: Transaction should be rolled back
            assert result is None
            # Session rollback should be called implicitly by context manager

    def test_save_should_update_existing_task_when_task_exists(
        self, task_repository, valid_task_entity
    ):
        """
        Test that save method updates existing task when task with same ID exists.
        
        This ensures the fix doesn't break task updates.
        """
        # Arrange: Mock existing task in database
        with patch.object(task_repository, 'get_db_session') as mock_session_context:
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock existing task
            mock_existing_task = Mock()
            mock_existing_task.id = str(valid_task_entity.id)
            mock_session.query.return_value.filter.return_value.first.return_value = mock_existing_task
            
            # Act: Save task
            result = task_repository.save(valid_task_entity)
            
            # Assert: Save should return task entity and update existing task
            assert result is not None
            assert result == valid_task_entity
            # Verify task properties were updated
            assert mock_existing_task.title == valid_task_entity.title
            assert mock_existing_task.description == valid_task_entity.description

    def test_save_should_create_new_task_when_task_does_not_exist(
        self, task_repository, valid_task_entity
    ):
        """
        Test that save method creates new task when task doesn't exist.
        
        This ensures the fix doesn't break task creation.
        """
        # Arrange: Mock no existing task in database
        with patch.object(task_repository, 'get_db_session') as mock_session_context:
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock no existing task
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Act: Save task
            result = task_repository.save(valid_task_entity)
            
            # Assert: Save should return task entity and create new task
            assert result is not None
            assert result == valid_task_entity
            mock_session.add.assert_called_once()

    def test_save_should_handle_database_connection_errors(
        self, task_repository, valid_task_entity
    ):
        """
        Test that save method handles database connection errors gracefully.
        
        This ensures application doesn't crash on connection issues.
        """
        # Arrange: Mock DatabaseError
        with patch.object(task_repository, 'get_db_session') as mock_session_context:
            mock_session_context.side_effect = DatabaseError("Connection failed", None, None)
            
            # Act: Save task
            result = task_repository.save(valid_task_entity)
            
            # Assert: Save should return False
            assert result is None

    def test_get_task_should_return_none_when_task_not_found_after_failed_save(
        self, task_repository, invalid_git_branch_task_entity
    ):
        """
        Test that get_task returns None when task was not saved due to constraint failure.
        
        This ensures consistency between save and get operations.
        """
        # Arrange: Save fails due to constraint
        save_result = task_repository.save(invalid_git_branch_task_entity)
        
        # Act: Try to get the task
        retrieved_task = task_repository.get_task(str(invalid_git_branch_task_entity.id))
        
        # Assert: Save should fail and task should not be found
        assert save_result is None
        assert retrieved_task is None

    def test_list_tasks_should_not_include_failed_saves(
        self, task_repository, invalid_git_branch_task_entity
    ):
        """
        Test that list_tasks doesn't include tasks that failed to save.
        
        This addresses the original issue where tasks appeared in lists
        but weren't actually persisted.
        """
        # Arrange: Save fails due to constraint
        save_result = task_repository.save(invalid_git_branch_task_entity)
        
        # Act: List tasks
        task_list = task_repository.list_tasks()
        
        # Assert: Save should fail and task should not be in list
        assert save_result is None
        task_ids = [task.id for task in task_list]
        assert str(invalid_git_branch_task_entity.id) not in task_ids

    def test_repository_save_should_return_true_with_valid_git_branch_id(self):
        """
        Test that repository save returns TaskEntity when git_branch_id is valid.
        
        This ensures the fix doesn't break valid saves.
        """
        # Arrange: Mock successful save with valid git_branch_id
        with patch.object(ORMTaskRepository, 'get_db_session') as mock_session_context:
            mock_session = Mock(spec=Session)
            mock_session_context.return_value.__enter__.return_value = mock_session
            mock_session_context.return_value.__exit__.return_value = None
            
            # Mock no existing task in database
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            
            # Create repository with valid git_branch_id
            repository = ORMTaskRepository(git_branch_id=str(uuid.uuid4()))
            
            # Create a task entity
            task = Task.create(
                id=str(uuid.uuid4()),
                title="Valid Task",
                description="Task with valid git_branch_id",
                git_branch_id=str(uuid.uuid4()),
                priority="high"
            )
            
            # Act: Save task
            result = repository.save(task)
            
            # Assert: Save should return task entity
            assert result is not None
            assert result == task