#!/usr/bin/env python3
"""
Unit tests for SubtaskApplicationFacade
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid

from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.application.dtos.subtask.create_subtask_request import CreateSubtaskRequest
from fastmcp.task_management.application.dtos.subtask.update_subtask_request import UpdateSubtaskRequest
from fastmcp.task_management.domain.entities.subtask import Subtask as SubtaskEntity
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


@pytest.fixture
def mock_subtask_repository():
    """Create a mock subtask repository"""
    return Mock()


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository"""
    return Mock()


@pytest.fixture
def mock_context_service():
    """Create a mock context service"""
    return Mock()


@pytest.fixture
def subtask_facade(mock_subtask_repository, mock_task_repository, mock_context_service):
    """Create a SubtaskApplicationFacade with mocked dependencies"""
    facade = SubtaskApplicationFacade(
        subtask_repository=mock_subtask_repository,
        task_repository=mock_task_repository,
        context_service=mock_context_service
    )
    return facade


@pytest.fixture
def sample_subtask_entity():
    """Create a sample subtask entity"""
    return SubtaskEntity(
        id=str(uuid.uuid4()),
        task_id=str(uuid.uuid4()),
        title="Test Subtask",
        description="Test Subtask Description",
        status="todo",
        priority="medium",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_task_entity():
    """Create a sample parent task entity"""
    return TaskEntity(
        id=TaskId(str(uuid.uuid4())),
        title="Parent Task",
        description="Parent Task Description",
        git_branch_id=str(uuid.uuid4()),
        status=TaskStatus("in_progress"),
        priority=Priority("high"),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestSubtaskApplicationFacade:
    """Test suite for SubtaskApplicationFacade"""
    
    @pytest.mark.unit
    def test_create_subtask_success(self, subtask_facade, mock_subtask_repository, mock_task_repository, 
                                   sample_subtask_entity, sample_task_entity):
        """Test successful subtask creation"""
        # Arrange
        task_id = str(uuid.uuid4())
        request = CreateSubtaskRequest(
            task_id=task_id,
            title="New Subtask",
            description="New Subtask Description",
            priority="high"
        )
        
        # Mock parent task exists
        mock_task_repository.find_by_id.return_value = sample_task_entity
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.subtask = sample_subtask_entity
        mock_response.message = "Subtask created successfully"
        
        subtask_facade._create_subtask_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = subtask_facade.create_subtask(request)
        
        # Assert
        assert result["success"] is True
        assert "subtask" in result
        subtask_facade._create_subtask_use_case.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_create_subtask_parent_not_found(self, subtask_facade, mock_task_repository):
        """Test subtask creation when parent task doesn't exist"""
        # Arrange
        task_id = str(uuid.uuid4())
        request = CreateSubtaskRequest(
            task_id=task_id,
            title="New Subtask",
            description="Description"
        )
        
        # Mock parent task not found
        mock_task_repository.find_by_id.return_value = None
        
        # Act
        result = subtask_facade.create_subtask(request)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "parent task not found" in result["error"].lower()
    
    @pytest.mark.unit
    def test_update_subtask_success(self, subtask_facade, mock_subtask_repository, sample_subtask_entity):
        """Test successful subtask update"""
        # Arrange
        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        request = UpdateSubtaskRequest(
            task_id=task_id,
            subtask_id=subtask_id,
            title="Updated Title",
            status="in_progress",
            progress_percentage=50
        )
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.subtask = sample_subtask_entity
        
        subtask_facade._update_subtask_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = subtask_facade.update_subtask(task_id, subtask_id, request)
        
        # Assert
        assert result["success"] is True
        assert "subtask" in result
        subtask_facade._update_subtask_use_case.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_update_subtask_progress_mapping(self, subtask_facade):
        """Test that progress_percentage is properly mapped"""
        # Arrange
        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        request = UpdateSubtaskRequest(
            task_id=task_id,
            subtask_id=subtask_id,
            progress_percentage=75
        )
        
        # Mock the use case
        mock_response = Mock()
        mock_response.success = True
        mock_response.subtask = Mock()
        mock_response.subtask.status = "in_progress"
        
        subtask_facade._update_subtask_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = subtask_facade.update_subtask(task_id, subtask_id, request)
        
        # Assert
        assert result["success"] is True
        # Verify the use case was called with the request containing progress
        call_args = subtask_facade._update_subtask_use_case.execute.call_args[0][0]
        assert call_args.progress_percentage == 75
    
    @pytest.mark.unit
    def test_get_subtask_success(self, subtask_facade, mock_subtask_repository, sample_subtask_entity):
        """Test successful subtask retrieval"""
        # Arrange
        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        
        # Mock repository response
        mock_subtask_repository.get_subtask.return_value = sample_subtask_entity
        
        # Act
        result = subtask_facade.get_subtask(task_id, subtask_id)
        
        # Assert
        assert result["success"] is True
        assert "subtask" in result
        mock_subtask_repository.get_subtask.assert_called_once_with(task_id, subtask_id)
    
    @pytest.mark.unit
    def test_delete_subtask_success(self, subtask_facade, mock_subtask_repository):
        """Test successful subtask deletion"""
        # Arrange
        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        
        # Mock the use case response
        subtask_facade._delete_subtask_use_case.execute = Mock(return_value=True)
        
        # Act
        result = subtask_facade.delete_subtask(task_id, subtask_id)
        
        # Assert
        assert result["success"] is True
        assert "deleted successfully" in result["message"].lower()
    
    @pytest.mark.unit
    def test_list_subtasks(self, subtask_facade, mock_subtask_repository):
        """Test listing subtasks for a task"""
        # Arrange
        task_id = str(uuid.uuid4())
        mock_subtasks = [Mock() for _ in range(4)]
        
        # Mock repository response
        mock_subtask_repository.get_subtasks_for_task.return_value = mock_subtasks
        
        # Act
        result = subtask_facade.list_subtasks(task_id)
        
        # Assert
        assert result["success"] is True
        assert "subtasks" in result
        assert result["count"] == 4
        mock_subtask_repository.get_subtasks_for_task.assert_called_once_with(task_id)
    
    @pytest.mark.unit
    def test_complete_subtask_success(self, subtask_facade, mock_subtask_repository, mock_task_repository,
                                     sample_subtask_entity, sample_task_entity):
        """Test completing a subtask"""
        # Arrange
        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        completion_summary = "Subtask completed successfully"
        
        # Mock parent task and subtask exist
        mock_task_repository.find_by_id.return_value = sample_task_entity
        mock_subtask_repository.get_subtask.return_value = sample_subtask_entity
        
        # Mock update repository
        mock_subtask_repository.update_subtask.return_value = sample_subtask_entity
        
        # Act
        result = subtask_facade.complete_subtask(
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary=completion_summary
        )
        
        # Assert
        assert result["success"] is True
        assert "completed" in result["message"].lower()
        # Verify update was called with done status
        mock_subtask_repository.update_subtask.assert_called()
    
    @pytest.mark.unit
    def test_update_parent_progress(self, subtask_facade, mock_subtask_repository, mock_task_repository):
        """Test that parent task progress is updated when subtasks change"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        # Create mock subtasks with different statuses
        subtasks = [
            Mock(status="done", progress_percentage=100),
            Mock(status="done", progress_percentage=100),
            Mock(status="in_progress", progress_percentage=50),
            Mock(status="todo", progress_percentage=0)
        ]
        
        mock_subtask_repository.get_subtasks_for_task.return_value = subtasks
        
        # Mock parent task
        parent_task = Mock()
        mock_task_repository.find_by_id.return_value = parent_task
        mock_task_repository.save.return_value = True
        
        # Act
        subtask_facade.update_parent_progress(task_id)
        
        # Assert
        # Average progress should be (100 + 100 + 50 + 0) / 4 = 62.5
        mock_task_repository.save.assert_called_once()
        saved_task = mock_task_repository.save.call_args[0][0]
        assert saved_task.overall_progress == 62.5
    
    @pytest.mark.unit
    def test_get_progress_summary(self, subtask_facade, mock_subtask_repository):
        """Test getting progress summary for subtasks"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        # Create mock subtasks
        subtasks = [
            Mock(status="done"),
            Mock(status="done"),
            Mock(status="in_progress"),
            Mock(status="todo"),
            Mock(status="blocked")
        ]
        
        mock_subtask_repository.get_subtasks_for_task.return_value = subtasks
        
        # Act
        result = subtask_facade.get_progress_summary(task_id)
        
        # Assert
        assert result["success"] is True
        assert result["summary"]["total"] == 5
        assert result["summary"]["completed"] == 2
        assert result["summary"]["in_progress"] == 1
        assert result["summary"]["todo"] == 1
        assert result["summary"]["blocked"] == 1
        assert result["summary"]["completion_percentage"] == 40.0  # 2/5 = 40%
    
    @pytest.mark.unit
    def test_error_handling(self, subtask_facade, mock_subtask_repository):
        """Test error handling in facade methods"""
        # Arrange
        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        
        # Mock repository to raise an exception
        mock_subtask_repository.get_subtask.side_effect = Exception("Database error")
        
        # Act
        result = subtask_facade.get_subtask(task_id, subtask_id)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "database error" in result["error"].lower() or "unexpected error" in result["error"].lower()