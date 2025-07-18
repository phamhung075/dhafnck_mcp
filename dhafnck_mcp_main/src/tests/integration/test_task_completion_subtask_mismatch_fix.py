"""Test to reproduce and fix the subtask type mismatch issue"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.services.task_completion_service import TaskCompletionService
from fastmcp.task_management.domain.exceptions.task_exceptions import TaskCompletionError


class MockSubtaskRepository:
    """Mock implementation of SubtaskRepository that returns Subtask objects"""
    
    def __init__(self):
        self.subtasks = {}
    
    def save(self, subtask: Subtask) -> bool:
        self.subtasks[subtask.id.value] = subtask
        return True
    
    def find_by_parent_task_id(self, parent_task_id: TaskId) -> list[Subtask]:
        """Return all subtasks for a parent task as Subtask objects"""
        return [
            subtask for subtask in self.subtasks.values()
            if subtask.parent_task_id == parent_task_id
        ]


class TestSubtaskTypeMismatch:
    """Test the specific case where Task entity expects dict but gets Subtask objects"""
    
    def test_task_entity_subtasks_as_dict_vs_objects(self):
        """Test that Task entity now only stores subtask IDs"""
        task_id = TaskId(str(uuid4()))
        
        # Create a task with subtask IDs only (new architecture)
        subtask_id_1 = str(uuid4())
        subtask_id_2 = str(uuid4())
        
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task with subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            subtasks=[subtask_id_1, subtask_id_2],  # Just IDs
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context_id=str(uuid4())
        )
        
        # Task entity returns False when subtasks exist (conservative approach)
        assert not task.all_subtasks_completed()
        
        # Task entity no longer validates subtasks on completion
        # This should succeed even with subtasks present
        task.complete_task(completion_summary="Test completion")
        assert task.is_completed is True
    
    def test_task_completion_service_integration_mismatch(self):
        """
        Test the actual error case: TaskCompletionService returns Subtask objects
        but Task entity tries to call .get() on them
        """
        task_id = TaskId(str(uuid4()))
        subtask_repo = MockSubtaskRepository()
        
        # Create a task WITHOUT subtasks in its internal list
        # This simulates the real scenario where subtasks are stored separately
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task with external subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            subtasks=[],  # Empty - subtasks are in separate repository
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context_id=str(uuid4())
        )
        
        # Create subtasks as domain objects in the repository
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 1",
            description="First subtask",
            parent_task_id=task_id,
            status=TaskStatus.done(),
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 2", 
            description="Second subtask",
            parent_task_id=task_id,
            status=TaskStatus.todo(),
            priority=Priority.medium()
        )
        
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Create completion service
        completion_service = TaskCompletionService(subtask_repo)
        
        # The task entity has no subtasks internally, so it thinks all are complete
        assert task.all_subtasks_completed()  # Returns True because task.subtasks is empty
        
        # But the completion service checks the repository and finds incomplete subtasks
        can_complete, error_msg = completion_service.can_complete_task(task)
        assert not can_complete
        assert "1 of 2 subtasks are incomplete" in error_msg
        
        # This shows the disconnect: Task entity and TaskCompletionService
        # have different views of what subtasks exist


class TestSubtaskHandlingFix:
    """Test potential fixes for the subtask handling issue"""
    
    def test_task_entity_should_not_check_subtasks_internally(self):
        """
        The fix: Task entity should not validate subtasks internally
        since they are managed by a separate repository
        """
        task_id = TaskId(str(uuid4()))
        
        # Create a task without internal subtasks
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task managed by repository",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            subtasks=[],  # No internal subtasks
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context_id=str(uuid4())
        )
        
        # Task should be able to complete without checking internal subtasks
        # The validation should be done by TaskCompletionService instead
        task.complete_task(completion_summary="Completed successfully")
        assert task.status.is_done()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])