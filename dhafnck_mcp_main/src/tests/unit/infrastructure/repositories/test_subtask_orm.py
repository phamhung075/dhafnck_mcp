"""
Unit tests for ORM Subtask Repository

Tests the ORM implementation of the SubtaskRepository interface
with comprehensive coverage of all operations.
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from src.fastmcp.task_management.infrastructure.database.models import TaskSubtask, Base
from src.fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from src.fastmcp.task_management.domain.entities.subtask import Subtask
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority
from src.fastmcp.task_management.domain.exceptions.base_exceptions import (
    DatabaseException,
    ResourceNotFoundException,
    ValidationException
)


class TestORMSubtaskRepository:
    """Test suite for ORM subtask repository"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = Mock(spec=Session)
        
        # Create a mock query object with proper chaining
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_query.delete.return_value = 0
        mock_query.update.return_value = 0
        mock_query.scalar.return_value = None
        
        # Setup session to return the mock query
        session.query.return_value = mock_query
        session.add.return_value = None
        session.flush.return_value = None
        session.refresh.return_value = None
        session.commit.return_value = None
        session.rollback.return_value = None
        session.close.return_value = None
        
        return session
    
    @pytest.fixture
    def repository(self):
        """Create repository instance for testing"""
        return ORMSubtaskRepository()
    
    @pytest.fixture
    def sample_subtask(self):
        """Create a sample subtask for testing"""
        return Subtask(
            id=SubtaskId.generate_new(),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId.generate_new(),
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=["@coding_agent", "@test_agent"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_orm_model(self, sample_subtask):
        """Create a sample ORM model for testing"""
        return TaskSubtask(
            id=sample_subtask.id.value,
            task_id=sample_subtask.parent_task_id.value,
            title=sample_subtask.title,
            description=sample_subtask.description,
            status=sample_subtask.status.value,
            priority=sample_subtask.priority.value,
            assignees=sample_subtask.assignees,
            progress_percentage=0,
            created_at=sample_subtask.created_at,
            updated_at=sample_subtask.updated_at
        )
    
    def test_save_new_subtask(self, repository, mock_session, sample_subtask):
        """Test saving a new subtask"""
        # Remove ID to simulate new subtask
        sample_subtask.id = None
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Mock successful save
            new_model = TaskSubtask(
                id="new-id",
                task_id=sample_subtask.parent_task_id.value,
                title=sample_subtask.title
            )
            mock_session.add.return_value = None
            mock_session.flush.return_value = None
            mock_session.refresh.return_value = None
            
            # Mock the TaskSubtask constructor to return our mock
            with patch('src.fastmcp.task_management.infrastructure.repositories.orm.subtask_repository.TaskSubtask') as mock_model_class:
                mock_model_class.return_value = new_model
                
                result = repository.save(sample_subtask)
                
                assert result is True
                assert sample_subtask.id is not None
                mock_session.add.assert_called_once()
    
    def test_save_existing_subtask(self, repository, mock_session, sample_subtask, sample_orm_model):
        """Test updating an existing subtask"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_model
            
            result = repository.save(sample_subtask)
            
            assert result is True
            mock_session.flush.assert_called_once()
    
    def test_save_database_error(self, repository, mock_session, sample_subtask):
        """Test save operation with database error"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.side_effect = SQLAlchemyError("Database error")
            
            with pytest.raises(DatabaseException):
                repository.save(sample_subtask)
    
    def test_find_by_id_success(self, repository, mock_session, sample_orm_model):
        """Test finding subtask by ID successfully"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_model
            
            result = repository.find_by_id(sample_orm_model.id)
            
            assert result is not None
            assert isinstance(result, Subtask)
            assert result.id.value == sample_orm_model.id
            assert result.title == sample_orm_model.title
    
    def test_find_by_id_not_found(self, repository, mock_session):
        """Test finding subtask by ID when not found"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            result = repository.find_by_id("nonexistent-id")
            
            assert result is None
    
    def test_find_by_parent_task_id(self, repository, mock_session, sample_orm_model):
        """Test finding subtasks by parent task ID"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_orm_model]
            
            result = repository.find_by_parent_task_id(parent_task_id)
            
            assert len(result) == 1
            assert isinstance(result[0], Subtask)
    
    def test_find_by_assignee(self, repository, mock_session, sample_orm_model):
        """Test finding subtasks by assignee"""
        assignee = "@coding_agent"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_orm_model]
            
            result = repository.find_by_assignee(assignee)
            
            assert len(result) == 1
            assert isinstance(result[0], Subtask)
    
    def test_find_by_status(self, repository, mock_session, sample_orm_model):
        """Test finding subtasks by status"""
        status = "todo"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_orm_model]
            
            result = repository.find_by_status(status)
            
            assert len(result) == 1
            assert isinstance(result[0], Subtask)
    
    def test_find_completed(self, repository, mock_session, sample_orm_model):
        """Test finding completed subtasks"""
        parent_task_id = TaskId.generate_new()
        sample_orm_model.status = "done"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_orm_model]
            
            result = repository.find_completed(parent_task_id)
            
            assert len(result) == 1
            assert isinstance(result[0], Subtask)
    
    def test_find_pending(self, repository, mock_session, sample_orm_model):
        """Test finding pending subtasks"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_orm_model]
            
            result = repository.find_pending(parent_task_id)
            
            assert len(result) == 1
            assert isinstance(result[0], Subtask)
    
    def test_delete_success(self, repository, mock_session):
        """Test deleting subtask successfully"""
        subtask_id = "test-id"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.delete.return_value = 1
            
            result = repository.delete(subtask_id)
            
            assert result is True
    
    def test_delete_not_found(self, repository, mock_session):
        """Test deleting subtask when not found"""
        subtask_id = "nonexistent-id"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.delete.return_value = 0
            
            result = repository.delete(subtask_id)
            
            assert result is False
    
    def test_delete_by_parent_task_id(self, repository, mock_session):
        """Test deleting all subtasks for a parent task"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.delete.return_value = 3
            
            result = repository.delete_by_parent_task_id(parent_task_id)
            
            assert result is True
    
    def test_exists_true(self, repository, mock_session, sample_orm_model):
        """Test checking if subtask exists - returns True"""
        subtask_id = "test-id"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = sample_orm_model
            
            result = repository.exists(subtask_id)
            
            assert result is True
    
    def test_exists_false(self, repository, mock_session):
        """Test checking if subtask exists - returns False"""
        subtask_id = "nonexistent-id"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            result = repository.exists(subtask_id)
            
            assert result is False
    
    def test_count_by_parent_task_id(self, repository, mock_session):
        """Test counting subtasks for a parent task"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.count.return_value = 5
            
            result = repository.count_by_parent_task_id(parent_task_id)
            
            assert result == 5
    
    def test_count_completed_by_parent_task_id(self, repository, mock_session):
        """Test counting completed subtasks for a parent task"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.count.return_value = 3
            
            result = repository.count_completed_by_parent_task_id(parent_task_id)
            
            assert result == 3
    
    def test_get_next_id(self, repository):
        """Test generating next subtask ID"""
        parent_task_id = TaskId.generate_new()
        
        result = repository.get_next_id(parent_task_id)
        
        assert isinstance(result, SubtaskId)
        assert result.value is not None
    
    def test_get_subtask_progress(self, repository, mock_session):
        """Test getting subtask progress statistics"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            # Create separate mocks for each count query
            total_count = 10
            completed_count = 6
            in_progress_count = 2
            blocked_count = 1
            
            # Track which query we're on
            query_call_count = 0
            counts = [total_count, completed_count, in_progress_count, blocked_count]
            
            def count_side_effect():
                nonlocal query_call_count
                result = counts[query_call_count] if query_call_count < len(counts) else 0
                query_call_count += 1
                return result
            
            # Mock for count queries
            count_mock = Mock()
            count_mock.count.side_effect = count_side_effect
            
            # Mock for average query
            avg_mock = Mock()
            avg_mock.scalar.return_value = 65.5
            
            # Setup query to return appropriate mock based on arguments
            def query_side_effect(*args):
                # Check if this is an average query
                if args and 'avg' in str(args[0]):
                    filter_mock = Mock()
                    filter_mock.scalar.return_value = 65.5
                    return Mock(filter=Mock(return_value=filter_mock))
                else:
                    # This is a count query
                    return Mock(filter=Mock(return_value=count_mock))
            
            mock_session.query.side_effect = query_side_effect
            
            result = repository.get_subtask_progress(parent_task_id)
            
            assert isinstance(result, dict)
            assert result["total_subtasks"] == total_count
            assert result["completed_subtasks"] == completed_count
            assert result["in_progress_subtasks"] == in_progress_count
            assert result["blocked_subtasks"] == blocked_count
            assert result["completion_percentage"] == 60.0  # 6/10 * 100
            assert result["average_progress"] == 65.5
    
    def test_bulk_update_status(self, repository, mock_session):
        """Test bulk updating status of subtasks"""
        parent_task_id = TaskId.generate_new()
        new_status = "in_progress"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.update.return_value = 3
            
            result = repository.bulk_update_status(parent_task_id, new_status)
            
            assert result is True
    
    def test_bulk_complete(self, repository, mock_session):
        """Test bulk completing subtasks"""
        parent_task_id = TaskId.generate_new()
        
        with patch.object(repository, 'bulk_update_status') as mock_bulk_update:
            mock_bulk_update.return_value = True
            
            result = repository.bulk_complete(parent_task_id)
            
            assert result is True
            mock_bulk_update.assert_called_once_with(parent_task_id, 'done')
    
    def test_remove_subtask(self, repository, mock_session):
        """Test removing a specific subtask"""
        parent_task_id = "parent-id"
        subtask_id = "subtask-id"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.delete.return_value = 1
            
            result = repository.remove_subtask(parent_task_id, subtask_id)
            
            assert result is True
    
    def test_update_progress(self, repository, mock_session):
        """Test updating subtask progress"""
        subtask_id = "test-id"
        progress = 75
        notes = "Making good progress"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.update.return_value = 1
            
            result = repository.update_progress(subtask_id, progress, notes)
            
            assert result is True
    
    def test_complete_subtask(self, repository, mock_session):
        """Test completing a subtask with metadata"""
        subtask_id = "test-id"
        summary = "Task completed successfully"
        impact = "Enables next phase"
        insights = ["Learned about X", "Need to consider Y"]
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.update.return_value = 1
            
            result = repository.complete_subtask(subtask_id, summary, impact, insights)
            
            assert result is True
    
    def test_get_subtasks_by_assignee(self, repository, mock_session, sample_orm_model):
        """Test getting subtasks by assignee with limit"""
        assignee = "@coding_agent"
        limit = 10
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            query_mock = Mock()
            query_mock.order_by.return_value.limit.return_value.all.return_value = [sample_orm_model]
            mock_session.query.return_value.filter.return_value = query_mock
            
            result = repository.get_subtasks_by_assignee(assignee, limit)
            
            assert len(result) == 1
            assert isinstance(result[0], Subtask)
    
    def test_to_model_data(self, repository, sample_subtask):
        """Test converting domain entity to model data"""
        result = repository._to_model_data(sample_subtask)
        
        assert isinstance(result, dict)
        assert result["task_id"] == sample_subtask.parent_task_id.value
        assert result["title"] == sample_subtask.title
        assert result["description"] == sample_subtask.description
        assert result["status"] == sample_subtask.status.value
        assert result["priority"] == sample_subtask.priority.value
        assert result["assignees"] == sample_subtask.assignees
    
    def test_to_domain_entity(self, repository, sample_orm_model):
        """Test converting ORM model to domain entity"""
        result = repository._to_domain_entity(sample_orm_model)
        
        assert isinstance(result, Subtask)
        assert result.id.value == sample_orm_model.id
        assert result.title == sample_orm_model.title
        assert result.description == sample_orm_model.description
        assert result.parent_task_id.value == sample_orm_model.task_id
        assert result.status.value == sample_orm_model.status
        assert result.priority.value == sample_orm_model.priority
        assert result.assignees == sample_orm_model.assignees
    
    def test_database_exception_handling(self, repository, mock_session, sample_subtask):
        """Test that database exceptions are properly wrapped"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.side_effect = SQLAlchemyError("Connection failed")
            
            with pytest.raises(DatabaseException) as exc_info:
                repository.save(sample_subtask)
            
            assert "Failed to save subtask" in str(exc_info.value)
            assert exc_info.value.context.get("operation") == "save_subtask"
            assert exc_info.value.context.get("table") == "task_subtasks"


class TestORMSubtaskRepositoryIntegration:
    """Integration tests for ORM subtask repository"""
    
    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
    
    @pytest.fixture
    def repository_with_db(self, in_memory_db):
        """Create repository with real database session"""
        repository = ORMSubtaskRepository()
        
        # Mock the get_db_session to use our test session
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = in_memory_db
            mock_get_session.return_value.__exit__.return_value = None
            yield repository
    
    def test_full_crud_cycle(self, repository_with_db, in_memory_db):
        """Test complete CRUD cycle with real database"""
        # Create subtask
        subtask = Subtask(
            title="Integration Test Subtask",
            description="Testing full CRUD cycle",
            parent_task_id=TaskId.generate_new(),
            status=TaskStatus.todo(),
            priority=Priority.high(),
            assignees=["@coding_agent"]
        )
        
        # Save subtask
        with patch.object(repository_with_db, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = in_memory_db
            
            # Save
            result = repository_with_db.save(subtask)
            assert result is True
            assert subtask.id is not None
            
            # Find by ID
            found_subtask = repository_with_db.find_by_id(subtask.id.value)
            assert found_subtask is not None
            assert found_subtask.title == subtask.title
            
            # Update
            subtask.title = "Updated Title"
            update_result = repository_with_db.save(subtask)
            assert update_result is True
            
            # Verify update
            updated_subtask = repository_with_db.find_by_id(subtask.id.value)
            assert updated_subtask.title == "Updated Title"
            
            # Delete
            delete_result = repository_with_db.delete(subtask.id.value)
            assert delete_result is True
            
            # Verify deletion
            deleted_subtask = repository_with_db.find_by_id(subtask.id.value)
            assert deleted_subtask is None


if __name__ == "__main__":
    pytest.main([__file__])