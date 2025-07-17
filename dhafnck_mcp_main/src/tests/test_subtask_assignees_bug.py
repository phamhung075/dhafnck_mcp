"""
Test to reproduce the exact 'str' object has no attribute 'copy' bug
This simulates what happens without the defensive checks
"""

import pytest
from datetime import datetime, timezone

from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority


def test_reproduce_string_copy_error():
    """Reproduce the exact error: 'str' object has no attribute 'copy'"""
    # Create a task
    task = Task(
        id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
        title="Test Task",
        description="Test Description",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Simulate corrupted subtask data (string instead of dict)
    task.subtasks = ["invalid string subtask"]
    
    # Create a mock update_subtask method without defensive checks
    def unsafe_update_subtask(subtask_id, updates):
        for subtask in task.subtasks:
            # This will fail because string doesn't have .copy() method
            old_subtask = subtask.copy()  # This line causes the error!
            subtask.update(updates)
        return True
    
    # This should raise AttributeError: 'str' object has no attribute 'copy'
    with pytest.raises(AttributeError, match="'str' object has no attribute 'copy'"):
        unsafe_update_subtask("any-id", {"assignees": ["user1"]})


def test_current_implementation_handles_strings():
    """Test that current implementation properly handles string subtasks"""
    # Create a task
    task = Task(
        id=TaskId.from_string("12345678-1234-5678-1234-567812345678"),
        title="Test Task",
        description="Test Description",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Mix valid and invalid subtasks
    task.subtasks = [
        "invalid string",
        {
            "id": "sub-1",
            "title": "Valid Subtask",
            "assignees": ["old_user"]
        }
    ]
    
    # This should work without error
    result = task.update_subtask("sub-1", {"assignees": ["new_user"]})
    assert result is True
    
    # Find the valid subtask
    valid_subtask = next(s for s in task.subtasks if isinstance(s, dict) and s.get("id") == "sub-1")
    assert valid_subtask["assignees"] == ["new_user"]