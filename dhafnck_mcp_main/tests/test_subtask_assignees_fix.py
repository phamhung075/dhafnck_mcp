"""
Test to verify the subtask assignees fix works correctly
"""

import pytest
from datetime import datetime, timezone

from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority


class TestSubtaskAssigneesFix:
    """Test the fixes for subtask assignees issues"""
    
    def test_clean_subtask_assignees_empty_string_array(self):
        """Test cleaning '[]' string to empty array"""
        # Create a task with subtasks having '[]' as assignees
        task = Task(
            id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
            description="Test",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add subtasks with various invalid assignees formats
        task.subtasks = [
            {
                "id": "sub-1",
                "title": "Subtask 1",
                "assignees": "[]"  # String representation of empty array
            },
            {
                "id": "sub-2",
                "title": "Subtask 2",
                "assignees": '["user1", "user2"]'  # JSON string
            },
            {
                "id": "sub-3",
                "title": "Subtask 3",
                "assignees": ""  # Empty string
            },
            {
                "id": "sub-4",
                "title": "Subtask 4",
                "assignees": None  # None value
            },
            {
                "id": "sub-5",
                "title": "Subtask 5",
                "assignees": "single_user"  # Single string
            },
            {
                "id": "sub-6",
                "title": "Subtask 6",
                "assignees": 123  # Invalid type
            }
        ]
        
        # Clean the assignees
        fixed_count = task.clean_subtask_assignees()
        
        # Assert all were fixed
        assert fixed_count == 6
        
        # Verify results
        assert task.subtasks[0]["assignees"] == []  # '[]' -> []
        assert task.subtasks[1]["assignees"] == ["user1", "user2"]  # JSON parsed
        assert task.subtasks[2]["assignees"] == []  # '' -> []
        assert task.subtasks[3]["assignees"] == []  # None -> []
        assert task.subtasks[4]["assignees"] == ["single_user"]  # string -> [string]
        assert task.subtasks[5]["assignees"] == []  # invalid type -> []
        
    def test_update_subtask_with_string_assignees(self):
        """Test updating subtask handles string assignees correctly"""
        task = Task(
            id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
            description="Test",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add a subtask with string assignees
        task.subtasks = [
            {
                "id": "sub-1",
                "title": "Subtask 1",
                "assignees": "[]"
            }
        ]
        
        # Update with new assignees
        result = task.update_subtask("sub-1", {"assignees": ["user1", "user2"]})
        
        assert result is True
        assert task.subtasks[0]["assignees"] == ["user1", "user2"]
        
    def test_update_subtask_with_empty_string_assignees(self):
        """Test updating subtask with '[]' string converts to empty list"""
        task = Task(
            id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
            description="Test",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add a subtask
        task.subtasks = [
            {
                "id": "sub-1",
                "title": "Subtask 1",
                "assignees": ["user1"]
            }
        ]
        
        # Update with '[]' string
        result = task.update_subtask("sub-1", {"assignees": "[]"})
        
        assert result is True
        assert task.subtasks[0]["assignees"] == []
        
    def test_clean_subtask_assignees_preserves_valid_lists(self):
        """Test that cleaning doesn't modify already valid assignees"""
        task = Task(
            id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
            description="Test",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add subtasks with valid assignees
        task.subtasks = [
            {
                "id": "sub-1",
                "title": "Subtask 1",
                "assignees": []
            },
            {
                "id": "sub-2",
                "title": "Subtask 2",
                "assignees": ["user1", "user2"]
            }
        ]
        
        # Clean the assignees
        fixed_count = task.clean_subtask_assignees()
        
        # Nothing should be fixed
        assert fixed_count == 0
        
        # Values should be unchanged
        assert task.subtasks[0]["assignees"] == []
        assert task.subtasks[1]["assignees"] == ["user1", "user2"]