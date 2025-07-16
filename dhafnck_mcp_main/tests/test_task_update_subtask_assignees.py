"""
Test suite specifically for Task entity's update_subtask method
Focuses on the 'str' object has no attribute 'copy' error
"""

import pytest
from datetime import datetime, timezone

from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority


class TestTaskUpdateSubtaskMethod:
    """Test the Task entity's update_subtask method"""
    
    def test_update_subtask_with_valid_dict_subtask(self):
        """Test updating a subtask that is a proper dictionary"""
        # Arrange
        task = self._create_test_task()
        subtask = {
            "id": "sub-1",
            "title": "Original Subtask",
            "assignees": ["user1"]
        }
        task.subtasks.append(subtask)
        
        # Act
        result = task.update_subtask("sub-1", {"assignees": ["user2", "user3"]})
        
        # Assert
        assert result is True
        assert task.subtasks[0]["assignees"] == ["user2", "user3"]
        assert task.subtasks[0]["title"] == "Original Subtask"  # Other fields preserved
        
    def test_update_subtask_with_string_subtasks_present(self):
        """Test updating when some subtasks are strings (corrupted data)"""
        # Arrange
        task = self._create_test_task()
        # Mix of valid and invalid subtasks
        task.subtasks = [
            "invalid string subtask",  # This should be skipped
            {
                "id": "sub-1",
                "title": "Valid Subtask",
                "assignees": ["user1"]
            },
            "another invalid string"  # This should be skipped
        ]
        
        # Act
        result = task.update_subtask("sub-1", {"assignees": ["user2", "user3"]})
        
        # Assert
        assert result is True
        # The dict subtask should be updated
        valid_subtask = next(s for s in task.subtasks if isinstance(s, dict) and s.get("id") == "sub-1")
        assert valid_subtask["assignees"] == ["user2", "user3"]
        
    def test_update_subtask_all_strings_returns_false(self):
        """Test updating when all subtasks are strings (completely corrupted)"""
        # Arrange
        task = self._create_test_task()
        task.subtasks = ["string1", "string2", "string3"]
        
        # Act
        result = task.update_subtask("any-id", {"assignees": ["user1"]})
        
        # Assert
        assert result is False  # No valid subtask found
        
    def test_update_subtask_with_nested_dict_updates(self):
        """Test that update doesn't fail when updating with complex data"""
        # Arrange
        task = self._create_test_task()
        subtask = {
            "id": "sub-1",
            "title": "Subtask",
            "metadata": {"key": "value"}
        }
        task.subtasks.append(subtask)
        
        # Act
        result = task.update_subtask("sub-1", {
            "assignees": ["user1", "user2"],
            "metadata": {"key": "new_value", "extra": "data"}
        })
        
        # Assert
        assert result is True
        assert task.subtasks[0]["assignees"] == ["user1", "user2"]
        assert task.subtasks[0]["metadata"] == {"key": "new_value", "extra": "data"}
        
    def test_update_subtask_preserves_subtask_reference(self):
        """Test that subtask update modifies in place without creating new objects"""
        # Arrange
        task = self._create_test_task()
        subtask = {
            "id": "sub-1",
            "title": "Subtask",
            "assignees": []
        }
        task.subtasks.append(subtask)
        original_subtask_obj = task.subtasks[0]
        
        # Act
        task.update_subtask("sub-1", {"assignees": ["user1"]})
        
        # Assert
        assert task.subtasks[0] is original_subtask_obj  # Same object reference
        assert task.subtasks[0]["assignees"] == ["user1"]
        
    def test_update_subtask_with_integer_id(self):
        """Test updating subtask using integer ID"""
        # Arrange
        task = self._create_test_task()
        subtask = {
            "id": 123,  # Integer ID
            "title": "Subtask",
            "assignees": ["user1"]
        }
        task.subtasks.append(subtask)
        
        # Act
        result = task.update_subtask(123, {"assignees": ["user2"]})
        
        # Assert
        assert result is True
        assert task.subtasks[0]["assignees"] == ["user2"]
        
    def test_update_subtask_with_hierarchical_id(self):
        """Test updating subtask using hierarchical ID format"""
        # Arrange
        task = self._create_test_task()
        subtask = {
            "id": "proj-123.task-456.sub-789",  # Hierarchical ID
            "title": "Subtask",
            "assignees": []
        }
        task.subtasks.append(subtask)
        
        # Act
        result = task.update_subtask("sub-789", {"assignees": ["user1", "user2"]})
        
        # Assert
        assert result is True
        assert task.subtasks[0]["assignees"] == ["user1", "user2"]
        
    def test_clean_invalid_subtasks_method(self):
        """Test the clean_invalid_subtasks method removes string subtasks"""
        # Arrange
        task = self._create_test_task()
        task.subtasks = [
            "invalid1",
            {"id": "sub-1", "title": "Valid 1"},
            "invalid2",
            {"id": "sub-2", "title": "Valid 2"},
            "invalid3"
        ]
        
        # Act
        removed_count = task.clean_invalid_subtasks()
        
        # Assert
        assert removed_count == 3
        assert len(task.subtasks) == 2
        assert all(isinstance(s, dict) for s in task.subtasks)
        assert task.subtasks[0]["id"] == "sub-1"
        assert task.subtasks[1]["id"] == "sub-2"
        
    def _create_test_task(self):
        """Helper to create a test task"""
        return Task(
            id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )