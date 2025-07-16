"""
Test suite for subtask assignees update functionality
This test ensures that assignees can be properly updated for subtasks
without encountering the 'str' object has no attribute 'copy' error
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority
from src.fastmcp.task_management.application.use_cases.update_subtask import UpdateSubtaskUseCase
from src.fastmcp.task_management.application.dtos.subtask import UpdateSubtaskRequest


class TestSubtaskAssigneesUpdate:
    """Test suite for updating subtask assignees"""
    
    def test_update_subtask_assignees_with_list(self):
        """Test updating subtask assignees with a list of strings"""
        # Arrange
        task_id = TaskId.from_string("12345678-1234-5678-1234-567812345678")
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add a subtask with proper dictionary structure
        subtask_data = {
            "id": "subtask-1",
            "title": "Test Subtask",
            "description": "Test subtask description",
            "status": "todo",
            "priority": "medium",
            "assignees": ["user1"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        task.subtasks.append(subtask_data)
        
        # Create mock repository
        task_repository = Mock()
        task_repository.find_by_id.return_value = task
        task_repository.save.return_value = task
        
        # Create use case
        use_case = UpdateSubtaskUseCase(task_repository)
        
        # Create update request with new assignees
        request = UpdateSubtaskRequest(
            task_id="12345678-1234-5678-1234-567812345678",
            id="subtask-1",
            assignees=["user2", "user3"]
        )
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.subtask["assignees"] == ["user2", "user3"]
        assert task_repository.save.called
        
    def test_update_subtask_assignees_with_empty_list(self):
        """Test updating subtask assignees with an empty list"""
        # Arrange
        task_id = TaskId.from_string("12345678-1234-5678-1234-567812345678")
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add a subtask with assignees
        subtask_data = {
            "id": "subtask-1",
            "title": "Test Subtask",
            "description": "Test subtask description",
            "status": "todo",
            "priority": "medium",
            "assignees": ["user1", "user2"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        task.subtasks.append(subtask_data)
        
        # Create mock repository
        task_repository = Mock()
        task_repository.find_by_id.return_value = task
        task_repository.save.return_value = task
        
        # Create use case
        use_case = UpdateSubtaskUseCase(task_repository)
        
        # Create update request with empty assignees
        request = UpdateSubtaskRequest(
            task_id="12345678-1234-5678-1234-567812345678",
            id="subtask-1",
            assignees=[]
        )
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.subtask["assignees"] == []
        assert task_repository.save.called
        
    def test_update_subtask_assignees_preserves_other_fields(self):
        """Test that updating assignees preserves other subtask fields"""
        # Arrange
        task_id = TaskId.from_string("12345678-1234-5678-1234-567812345678")
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add a subtask with all fields
        subtask_data = {
            "id": "subtask-1",
            "title": "Original Title",
            "description": "Original Description",
            "status": "in_progress",
            "priority": "high",
            "assignees": ["user1"],
            "custom_field": "custom_value",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        task.subtasks.append(subtask_data)
        
        # Create mock repository
        task_repository = Mock()
        task_repository.find_by_id.return_value = task
        task_repository.save.return_value = task
        
        # Create use case
        use_case = UpdateSubtaskUseCase(task_repository)
        
        # Create update request with only assignees
        request = UpdateSubtaskRequest(
            task_id="12345678-1234-5678-1234-567812345678",
            id="subtask-1",
            assignees=["user2", "user3", "user4"]
        )
        
        # Act
        response = use_case.execute(request)
        
        # Assert
        assert response.subtask["assignees"] == ["user2", "user3", "user4"]
        assert response.subtask["title"] == "Original Title"
        assert response.subtask["description"] == "Original Description"
        assert response.subtask["status"] == "in_progress"
        assert response.subtask["priority"] == "high"
        assert response.subtask["custom_field"] == "custom_value"
        
    def test_update_subtask_with_string_subtasks_in_list(self):
        """Test updating subtask when task contains invalid string subtasks"""
        # Arrange
        task_id = TaskId.from_string("12345678-1234-5678-1234-567812345678")
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add mixed subtasks - some strings, some dicts (simulating corrupted data)
        task.subtasks = [
            "invalid string subtask",  # This should be skipped
            {
                "id": "subtask-1",
                "title": "Valid Subtask",
                "description": "Test subtask description",
                "status": "todo",
                "priority": "medium",
                "assignees": ["user1"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "another invalid string",  # This should also be skipped
        ]
        
        # Create mock repository
        task_repository = Mock()
        task_repository.find_by_id.return_value = task
        task_repository.save.return_value = task
        
        # Create use case
        use_case = UpdateSubtaskUseCase(task_repository)
        
        # Create update request
        request = UpdateSubtaskRequest(
            task_id="12345678-1234-5678-1234-567812345678",
            id="subtask-1",
            assignees=["user2", "user3"]
        )
        
        # Act
        response = use_case.execute(request)
        
        # Assert - should successfully update the valid subtask
        assert response.subtask["assignees"] == ["user2", "user3"]
        assert task_repository.save.called
        
    def test_update_subtask_assignees_with_none_value(self):
        """Test that None assignees value doesn't update the field"""
        # Arrange
        task_id = TaskId.from_string("12345678-1234-5678-1234-567812345678")
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add a subtask with assignees
        subtask_data = {
            "id": "subtask-1",
            "title": "Test Subtask",
            "description": "Test subtask description",
            "status": "todo",
            "priority": "medium",
            "assignees": ["existing_user"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        task.subtasks.append(subtask_data)
        
        # Create mock repository
        task_repository = Mock()
        task_repository.find_by_id.return_value = task
        task_repository.save.return_value = task
        
        # Create use case
        use_case = UpdateSubtaskUseCase(task_repository)
        
        # Create update request with None assignees
        request = UpdateSubtaskRequest(
            task_id="12345678-1234-5678-1234-567812345678",
            id="subtask-1",
            assignees=None,
            title="New Title"  # Update something else
        )
        
        # Act
        response = use_case.execute(request)
        
        # Assert - assignees should remain unchanged
        assert response.subtask["assignees"] == ["existing_user"]
        assert response.subtask["title"] == "New Title"
        
    def test_update_nonexistent_subtask_raises_error(self):
        """Test that updating a non-existent subtask raises appropriate error"""
        # Arrange
        task_id = TaskId.from_string("12345678-1234-5678-1234-567812345678")
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create mock repository
        task_repository = Mock()
        task_repository.find_by_id.return_value = task
        
        # Create use case
        use_case = UpdateSubtaskUseCase(task_repository)
        
        # Create update request for non-existent subtask
        request = UpdateSubtaskRequest(
            task_id="12345678-1234-5678-1234-567812345678",
            id="non-existent-subtask",
            assignees=["user1"]
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Subtask non-existent-subtask not found"):
            use_case.execute(request)