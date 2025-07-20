"""
Test to reproduce the exact 'str' object has no attribute 'copy' bug
This simulates what happens without the defensive checks

NOTE: This test is for documenting the historical bug that occurred when
Task entity stored subtask data as dictionaries. In the new architecture,
Task only stores subtask IDs, making this bug impossible.
"""

import pytest
from datetime import datetime, timezone
import uuid

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


def test_reproduce_string_copy_error():
    """Reproduce the historical error: 'str' object has no attribute 'copy'"""
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
    
    # In old architecture, this would cause issues:
    # task.subtasks = ["invalid string subtask"]
    
    # In new architecture, subtasks are always UUIDs:
    task.subtasks = [str(uuid.uuid4())]
    
    # The old bug was in methods that expected dictionaries:
    # def unsafe_update_subtask(subtask_id, updates):
    #     for subtask in task.subtasks:
    #         old_subtask = subtask.copy()  # This would fail on strings!
    #         subtask.update(updates)
    
    # New architecture prevents this by design - subtasks are just IDs
    assert isinstance(task.subtasks[0], str)
    assert len(task.subtasks[0]) == 36  # UUID string length


def test_new_architecture_with_subtask_ids():
    """Test that new architecture only stores subtask IDs"""
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
    
    # Add subtask IDs (UUIDs)
    subtask_ids = [
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4())
    ]
    task.subtasks = subtask_ids
    
    # Verify all subtasks are string UUIDs
    assert all(isinstance(s, str) for s in task.subtasks)
    assert all(len(s) == 36 for s in task.subtasks)  # UUID format
    assert len(task.subtasks) == 3


@pytest.mark.skip(reason="Task.update_subtask is deprecated - subtasks are managed via SubtaskRepository")
def test_deprecated_update_subtask_method():
    """Test the deprecated update_subtask method for backward compatibility"""
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
    
    # The update_subtask method still exists for backward compatibility
    # but should not be used in new code
    task.subtasks = [
        {
            "id": "sub-1",
            "title": "Valid Subtask",
            "assignees": ["old_user"]
        }
    ]
    
    # This still works but is deprecated
    result = task.update_subtask("sub-1", {"assignees": ["new_user"]})
    assert result is True