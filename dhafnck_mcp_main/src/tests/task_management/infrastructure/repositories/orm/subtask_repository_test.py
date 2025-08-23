"""
Test cases for ORM Subtask Repository Implementation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.infrastructure.database.models import TaskSubtask
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.exceptions.base_exceptions import DatabaseException


class TestORMSubtaskRepository:
    """Test cases for ORMSubtaskRepository class."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock(spec=Session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        return session
    
    @pytest.fixture
    def subtask_repository(self, mock_session):
        """Create subtask repository with mocked session."""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.subtask_repository.get_session', 
                   return_value=mock_session):
            repo = ORMSubtaskRepository(session=mock_session, user_id="test-user-123")
            repo.get_db_session = Mock(return_value=mock_session)
            return repo
    
    @pytest.fixture
    def mock_subtask_model(self):
        """Create mock subtask model."""
        model = Mock(spec=TaskSubtask)
        model.id = "subtask-123"
        model.task_id = "task-456"
        model.title = "Test Subtask"
        model.description = "Test description"
        model.status = "todo"
        model.priority = "medium"
        model.assignees = ["@user1", "@user2"]
        model.progress_percentage = 25
        model.created_at = datetime.now(timezone.utc)
        model.updated_at = datetime.now(timezone.utc)
        model.completed_at = None
        return model
    
    @pytest.fixture
    def subtask_entity(self):
        """Create subtask domain entity."""
        return Subtask(
            id=SubtaskId("subtask-123"),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId("task-456"),
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            assignees=["@user1", "@user2"],
            progress_percentage=25,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def test_save_new_subtask(self, subtask_repository, mock_session, subtask_entity):
        """Test saving a new subtask without ID."""
        # Remove ID to simulate new subtask
        subtask_entity.id = None
        
        mock_session.add = Mock()
        mock_session.flush = Mock()
        mock_session.refresh = Mock(side_effect=lambda s: setattr(s, 'id', 'new-subtask-id'))
        
        with patch.object(subtask_repository, 'get_next_id', return_value=SubtaskId("new-subtask-id")):
            result = subtask_repository.save(subtask_entity)
        
        assert result is True
        assert subtask_entity.id.value == "new-subtask-id"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
    
    def test_save_existing_subtask(self, subtask_repository, mock_session, subtask_entity, mock_subtask_model):
        """Test updating an existing subtask."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_subtask_model
        mock_session.flush = Mock()
        
        result = subtask_repository.save(subtask_entity)
        
        assert result is True
        assert mock_subtask_model.title == subtask_entity.title
        assert mock_subtask_model.updated_at is not None
        mock_session.flush.assert_called_once()
    
    def test_save_subtask_with_id_not_exists(self, subtask_repository, mock_session, subtask_entity):
        """Test saving subtask with ID that doesn't exist in database."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = Mock()
        mock_session.flush = Mock()
        mock_session.refresh = Mock()
        
        result = subtask_repository.save(subtask_entity)
        
        assert result is True
        mock_session.add.assert_called_once()
    
    def test_save_database_error(self, subtask_repository, mock_session, subtask_entity):
        """Test save with database error."""
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(DatabaseException, match="Failed to save subtask"):
            subtask_repository.save(subtask_entity)
    
    def test_find_by_id_success(self, subtask_repository, mock_session, mock_subtask_model):
        """Test finding subtask by ID."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_subtask_model
        
        result = subtask_repository.find_by_id("subtask-123")
        
        assert result is not None
        assert isinstance(result, Subtask)
        assert result.id.value == "subtask-123"
        assert result.title == "Test Subtask"
    
    def test_find_by_id_not_found(self, subtask_repository, mock_session):
        """Test finding non-existent subtask."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = subtask_repository.find_by_id("nonexistent")
        
        assert result is None
    
    def test_find_by_parent_task_id(self, subtask_repository, mock_session):
        """Test finding subtasks by parent task ID."""
        mock_subtasks = [
            Mock(id=f"subtask-{i}", title=f"Subtask {i}", task_id="task-456",
                 description="", status="todo", priority="medium", assignees=[],
                 progress_percentage=0, created_at=datetime.now(timezone.utc),
                 updated_at=datetime.now(timezone.utc))
            for i in range(3)
        ]
        
        # Mock the query chain with apply_user_filter
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_subtasks
        
        # Mock apply_user_filter to return the same query
        with patch.object(subtask_repository, 'apply_user_filter', return_value=mock_query):
            result = subtask_repository.find_by_parent_task_id(TaskId("task-456"))
        
        assert len(result) == 3
        assert all(isinstance(s, Subtask) for s in result)
        assert all(s.parent_task_id.value == "task-456" for s in result)
    
    def test_find_by_assignee(self, subtask_repository, mock_session, mock_subtask_model):
        """Test finding subtasks by assignee."""
        # Mock the query chain with apply_user_filter
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_subtask_model]
        
        # Mock apply_user_filter to return the same query
        with patch.object(subtask_repository, 'apply_user_filter', return_value=mock_query):
            result = subtask_repository.find_by_assignee("@user1")
        
        assert len(result) == 1
        assert result[0].assignees == ["@user1", "@user2"]
    
    def test_find_by_status(self, subtask_repository, mock_session):
        """Test finding subtasks by status."""
        mock_done_subtasks = [
            Mock(id=f"done-{i}", title=f"Done {i}", task_id="task-456",
                 description="", status="done", priority="medium", assignees=[],
                 progress_percentage=100, created_at=datetime.now(timezone.utc),
                 updated_at=datetime.now(timezone.utc))
            for i in range(2)
        ]
        
        # Mock the query chain with apply_user_filter
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_done_subtasks
        
        # Mock apply_user_filter to return the same query
        with patch.object(subtask_repository, 'apply_user_filter', return_value=mock_query):
            result = subtask_repository.find_by_status("done")
        
        assert len(result) == 2
        assert all(s.status.value == "done" for s in result)
    
    def test_find_completed(self, subtask_repository, mock_session):
        """Test finding completed subtasks."""
        completed_at = datetime.now(timezone.utc)
        mock_completed = [
            Mock(id="completed-1", title="Completed Task", task_id="task-456",
                 description="", status="done", priority="medium", assignees=[],
                 progress_percentage=100, created_at=datetime.now(timezone.utc),
                 updated_at=datetime.now(timezone.utc), completed_at=completed_at)
        ]
        
        # Mock the query chain with apply_user_filter
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_completed
        
        # Mock apply_user_filter to return the same query
        with patch.object(subtask_repository, 'apply_user_filter', return_value=mock_query):
            result = subtask_repository.find_completed(TaskId("task-456"))
        
        assert len(result) == 1
        assert result[0].status.value == "done"
    
    def test_find_pending(self, subtask_repository, mock_session):
        """Test finding pending subtasks."""
        mock_pending = [
            Mock(id="pending-1", title="Todo", task_id="task-456",
                 description="", status="todo", priority="medium", assignees=[],
                 progress_percentage=0, created_at=datetime.now(timezone.utc),
                 updated_at=datetime.now(timezone.utc)),
            Mock(id="pending-2", title="In Progress", task_id="task-456",
                 description="", status="in_progress", priority="high", assignees=[],
                 progress_percentage=50, created_at=datetime.now(timezone.utc),
                 updated_at=datetime.now(timezone.utc)),
            Mock(id="pending-3", title="Blocked", task_id="task-456",
                 description="", status="blocked", priority="low", assignees=[],
                 progress_percentage=30, created_at=datetime.now(timezone.utc),
                 updated_at=datetime.now(timezone.utc))
        ]
        
        # Mock the query chain with apply_user_filter
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_pending
        
        # Mock apply_user_filter to return the same query
        with patch.object(subtask_repository, 'apply_user_filter', return_value=mock_query):
            result = subtask_repository.find_pending(TaskId("task-456"))
        
        assert len(result) == 3
        assert all(s.status.value in ["todo", "in_progress", "blocked"] for s in result)
    
    def test_delete_success(self, subtask_repository, mock_session):
        """Test successful subtask deletion."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 1
        
        result = subtask_repository.delete("subtask-123")
        
        assert result is True
        mock_session.query.return_value.filter.return_value.delete.assert_called_once()
    
    def test_delete_not_found(self, subtask_repository, mock_session):
        """Test deleting non-existent subtask."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 0
        
        result = subtask_repository.delete("nonexistent")
        
        assert result is False
    
    def test_delete_by_parent_task_id(self, subtask_repository, mock_session):
        """Test deleting all subtasks for a parent task."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 3
        
        result = subtask_repository.delete_by_parent_task_id(TaskId("task-456"))
        
        assert result is True
    
    def test_exists(self, subtask_repository, mock_session, mock_subtask_model):
        """Test checking if subtask exists."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_subtask_model
        
        result = subtask_repository.exists("subtask-123")
        
        assert result is True
    
    def test_exists_not_found(self, subtask_repository, mock_session):
        """Test checking if non-existent subtask exists."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = subtask_repository.exists("nonexistent")
        
        assert result is False
    
    def test_count_by_parent_task_id(self, subtask_repository, mock_session):
        """Test counting subtasks for parent task."""
        mock_session.query.return_value.filter.return_value.count.return_value = 5
        
        result = subtask_repository.count_by_parent_task_id(TaskId("task-456"))
        
        assert result == 5
    
    def test_count_completed_by_parent_task_id(self, subtask_repository, mock_session):
        """Test counting completed subtasks."""
        mock_session.query.return_value.filter.return_value.count.return_value = 3
        
        result = subtask_repository.count_completed_by_parent_task_id(TaskId("task-456"))
        
        assert result == 3
    
    def test_get_next_id(self, subtask_repository):
        """Test getting next subtask ID."""
        with patch('fastmcp.task_management.domain.value_objects.subtask_id.SubtaskId.generate_new') as mock_generate:
            mock_generate.return_value = SubtaskId("new-id-123")
            
            result = subtask_repository.get_next_id(TaskId("task-456"))
            
            assert result.value == "new-id-123"
    
    def test_get_subtask_progress(self, subtask_repository, mock_session):
        """Test getting subtask progress statistics."""
        # Mock counts
        mock_session.query.return_value.filter.return_value.count.side_effect = [
            10,  # total
            4,   # completed
            3,   # in_progress
            1    # blocked
        ]
        
        # Mock average progress
        mock_session.query.return_value.filter.return_value.scalar.return_value = 45.5
        
        result = subtask_repository.get_subtask_progress(TaskId("task-456"))
        
        assert result["total_subtasks"] == 10
        assert result["completed_subtasks"] == 4
        assert result["in_progress_subtasks"] == 3
        assert result["blocked_subtasks"] == 1
        assert result["pending_subtasks"] == 2  # 10 - 4 - 3 - 1
        assert result["completion_percentage"] == 40.0  # 4/10 * 100
        assert result["average_progress"] == 45.5
        assert result["has_blockers"] is True
    
    def test_get_subtask_progress_no_subtasks(self, subtask_repository, mock_session):
        """Test progress statistics with no subtasks."""
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.scalar.return_value = None
        
        result = subtask_repository.get_subtask_progress(TaskId("task-456"))
        
        assert result["total_subtasks"] == 0
        assert result["completion_percentage"] == 0
        assert result["average_progress"] == 0
    
    def test_bulk_update_status_to_done(self, subtask_repository, mock_session):
        """Test bulk updating status to done."""
        mock_session.query.return_value.filter.return_value.update.return_value = 5
        
        result = subtask_repository.bulk_update_status(TaskId("task-456"), "done")
        
        assert result is True
        
        # Check update data included completion fields
        update_call = mock_session.query.return_value.filter.return_value.update.call_args[0][0]
        assert TaskSubtask.status in update_call
        assert TaskSubtask.completed_at in update_call
        assert TaskSubtask.progress_percentage in update_call
        assert update_call[TaskSubtask.progress_percentage] == 100
    
    def test_bulk_update_status_to_pending(self, subtask_repository, mock_session):
        """Test bulk updating status to pending state."""
        mock_session.query.return_value.filter.return_value.update.return_value = 3
        
        result = subtask_repository.bulk_update_status(TaskId("task-456"), "todo")
        
        assert result is True
        
        # Check completed_at was cleared
        update_call = mock_session.query.return_value.filter.return_value.update.call_args[0][0]
        assert update_call[TaskSubtask.completed_at] is None
    
    def test_bulk_complete(self, subtask_repository, mock_session):
        """Test bulk completing subtasks."""
        with patch.object(subtask_repository, 'bulk_update_status', return_value=True) as mock_bulk:
            result = subtask_repository.bulk_complete(TaskId("task-456"))
            
            assert result is True
            mock_bulk.assert_called_once_with(TaskId("task-456"), "done")
    
    def test_remove_subtask(self, subtask_repository, mock_session):
        """Test removing specific subtask from parent task."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 1
        
        result = subtask_repository.remove_subtask("task-456", "subtask-123")
        
        assert result is True
    
    def test_update_progress(self, subtask_repository, mock_session):
        """Test updating subtask progress."""
        mock_session.query.return_value.filter.return_value.update.return_value = 1
        
        result = subtask_repository.update_progress("subtask-123", 75, "Almost done")
        
        assert result is True
        
        # Check update data
        update_call = mock_session.query.return_value.filter.return_value.update.call_args[0][0]
        assert update_call[TaskSubtask.progress_percentage] == 75
        assert update_call[TaskSubtask.progress_notes] == "Almost done"
    
    def test_update_progress_clamping(self, subtask_repository, mock_session):
        """Test progress percentage is clamped to 0-100."""
        mock_session.query.return_value.filter.return_value.update.return_value = 1
        
        # Test over 100
        subtask_repository.update_progress("subtask-123", 150, "")
        update_call = mock_session.query.return_value.filter.return_value.update.call_args[0][0]
        assert update_call[TaskSubtask.progress_percentage] == 100
        
        # Test under 0
        subtask_repository.update_progress("subtask-123", -50, "")
        update_call = mock_session.query.return_value.filter.return_value.update.call_args[0][0]
        assert update_call[TaskSubtask.progress_percentage] == 0
    
    def test_complete_subtask(self, subtask_repository, mock_session):
        """Test completing a subtask with metadata."""
        mock_session.query.return_value.filter.return_value.update.return_value = 1
        
        result = subtask_repository.complete_subtask(
            "subtask-123",
            completion_summary="Fixed the bug",
            impact_on_parent="Unblocks deployment",
            insights_found=["Performance issue found", "Need refactoring"]
        )
        
        assert result is True
        
        # Check update data
        update_call = mock_session.query.return_value.filter.return_value.update.call_args[0][0]
        assert update_call[TaskSubtask.status] == "done"
        assert update_call[TaskSubtask.progress_percentage] == 100
        assert update_call[TaskSubtask.completion_summary] == "Fixed the bug"
        assert update_call[TaskSubtask.impact_on_parent] == "Unblocks deployment"
        assert update_call[TaskSubtask.insights_found] == ["Performance issue found", "Need refactoring"]
    
    def test_get_subtasks_by_assignee_with_limit(self, subtask_repository, mock_session):
        """Test getting subtasks by assignee with limit."""
        mock_subtasks = [Mock() for _ in range(3)]
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_subtasks
        
        result = subtask_repository.get_subtasks_by_assignee("@user1", limit=5)
        
        assert len(result) == 3
        mock_query.limit.assert_called_once_with(5)
    
    def test_database_error_handling(self, subtask_repository, mock_session):
        """Test database error handling across methods."""
        mock_session.query.side_effect = SQLAlchemyError("Connection lost")
        
        with pytest.raises(DatabaseException, match="Failed to find subtask by id"):
            subtask_repository.find_by_id("test")
        
        with pytest.raises(DatabaseException, match="Failed to find subtasks for task"):
            subtask_repository.find_by_parent_task_id(TaskId("test"))
        
        with pytest.raises(DatabaseException, match="Failed to get subtask progress"):
            subtask_repository.get_subtask_progress(TaskId("test"))


class TestEntityConversion:
    """Test cases for entity conversion methods."""
    
    def test_to_model_data_conversion(self, subtask_repository, subtask_entity):
        """Test converting domain entity to model data."""
        model_data = subtask_repository._to_model_data(subtask_entity)
        
        assert model_data["task_id"] == "task-456"
        assert model_data["title"] == "Test Subtask"
        assert model_data["description"] == "Test description"
        assert model_data["status"] == "todo"
        assert model_data["priority"] == "medium"
        assert model_data["assignees"] == ["@user1", "@user2"]
        assert model_data["progress_percentage"] == 25
        assert "created_at" in model_data
        assert "updated_at" in model_data
        assert model_data["user_id"] == "test-user-123"  # User scoping
    
    def test_to_model_data_with_agent_roles(self, subtask_repository):
        """Test conversion with AgentRole enums."""
        mock_agent_role = Mock()
        mock_agent_role.value = "coding_agent"
        
        subtask = Subtask(
            title="Test",
            parent_task_id=TaskId("task-123"),
            assignees=[mock_agent_role, "regular_user"]
        )
        
        model_data = subtask_repository._to_model_data(subtask)
        
        assert model_data["assignees"] == ["@coding_agent", "regular_user"]
    
    def test_to_domain_entity_conversion(self, subtask_repository, mock_subtask_model):
        """Test converting ORM model to domain entity."""
        entity = subtask_repository._to_domain_entity(mock_subtask_model)
        
        assert isinstance(entity, Subtask)
        assert entity.id.value == "subtask-123"
        assert entity.title == "Test Subtask"
        assert entity.parent_task_id.value == "task-456"
        assert entity.status == TaskStatus.TODO
        assert entity.priority == Priority.MEDIUM
        assert entity.assignees == ["@user1", "@user2"]
        assert entity.progress_percentage == 25