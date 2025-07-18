"""Test for fixing task completion with subtasks bug"""

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
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase


class MockSubtaskRepository:
    """Mock implementation of SubtaskRepository for testing"""
    
    def __init__(self):
        self.subtasks = {}
    
    def save(self, subtask: Subtask) -> bool:
        self.subtasks[subtask.id.value] = subtask
        return True
    
    def find_by_parent_task_id(self, parent_task_id: TaskId) -> list[Subtask]:
        """Return all subtasks for a parent task"""
        return [
            subtask for subtask in self.subtasks.values()
            if subtask.parent_task_id == parent_task_id
        ]
    
    def get_next_id(self, parent_task_id: TaskId) -> SubtaskId:
        """Generate next subtask ID"""
        return SubtaskId(str(uuid4()))


class MockTaskRepository:
    """Mock implementation of TaskRepository for testing"""
    
    def __init__(self):
        self.tasks = {}
    
    def save(self, task: Task) -> bool:
        self.tasks[task.id.value] = task
        return True
    
    def find_by_id(self, task_id: TaskId) -> Task:
        return self.tasks.get(task_id.value)
    
    def find_all(self) -> list[Task]:
        return list(self.tasks.values())


class TestTaskCompletionWithSubtasks:
    """Test cases for task completion with subtasks functionality"""
    
    def test_task_completion_service_handles_subtask_objects(self):
        """Test that TaskCompletionService correctly handles Subtask objects (not dicts)"""
        # Arrange
        task_id = TaskId(str(uuid4()))
        subtask_repo = MockSubtaskRepository()
        
        # Create a task
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task with subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            subtasks=[],  # Empty subtasks list
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context_id=str(uuid4())  # Task has context
        )
        
        # Create subtasks as domain objects
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 1",
            description="First subtask",
            parent_task_id=task_id,
            status=TaskStatus.done(),  # Completed
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 2", 
            description="Second subtask",
            parent_task_id=task_id,
            status=TaskStatus.todo(),  # Not completed
            priority=Priority.medium()
        )
        
        # Save subtasks to repository
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Create service
        completion_service = TaskCompletionService(subtask_repo)
        
        # Act & Assert
        can_complete, error_msg = completion_service.can_complete_task(task)
        
        # Should not be able to complete because subtask2 is not done
        assert not can_complete
        assert "Cannot complete task" in error_msg
        assert "1 of 2 subtasks are incomplete" in error_msg
        assert "Subtask 2" in error_msg
    
    def test_task_completion_use_case_with_all_subtasks_completed(self):
        """Test completing a task when all subtasks are done"""
        # Arrange
        task_id = TaskId(str(uuid4()))
        task_repo = MockTaskRepository()
        subtask_repo = MockSubtaskRepository()
        
        # Create a task
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task with subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            subtasks=[],  # Empty subtasks list
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context_id=str(uuid4())  # Task has context
        )
        
        # Save task
        task_repo.save(task)
        
        # Create completed subtasks
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 1",
            description="First subtask",
            parent_task_id=task_id,
            status=TaskStatus.done(),  # Completed
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 2", 
            description="Second subtask",
            parent_task_id=task_id,
            status=TaskStatus.done(),  # Completed
            priority=Priority.medium()
        )
        
        # Save subtasks
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Create use case
        complete_task_use_case = CompleteTaskUseCase(task_repo, subtask_repo)
        
        # Act
        result = complete_task_use_case.execute(
            task_id=task_id.value,
            completion_summary="All subtasks completed successfully",
            testing_notes="Tested all functionality"
        )
        
        # Assert
        assert result['success'] is True
        assert result['status'] == 'done'
        assert result['message'] == f"task {task_id.value} done, can next_task"
        if 'subtask_summary' in result:
            assert result['subtask_summary']['total'] == 2
            assert result['subtask_summary']['completed'] == 2
            assert result['subtask_summary']['can_complete_parent'] is True
    
    def test_task_completion_validation_with_incomplete_subtasks(self):
        """Test that validation correctly prevents completion with incomplete subtasks"""
        # Arrange
        task_id = TaskId(str(uuid4()))
        subtask_repo = MockSubtaskRepository()
        
        # Create a task
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task with subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            subtasks=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context_id=str(uuid4())
        )
        
        # Create mixed subtasks
        for i in range(3):
            subtask = Subtask(
                id=SubtaskId(str(uuid4())),
                title=f"Subtask {i+1}",
                description=f"Subtask number {i+1}",
                parent_task_id=task_id,
                status=TaskStatus.done() if i == 0 else TaskStatus.todo(),
                priority=Priority.medium()
            )
            subtask_repo.save(subtask)
        
        # Create service
        completion_service = TaskCompletionService(subtask_repo)
        
        # Act & Assert
        with pytest.raises(TaskCompletionError) as exc_info:
            completion_service.validate_task_completion(task)
        
        error_msg = str(exc_info.value)
        assert "2 of 3 subtasks are incomplete" in error_msg
        assert "Subtask 2" in error_msg
        assert "Subtask 3" in error_msg
    
    def test_get_subtask_completion_summary(self):
        """Test getting subtask completion summary statistics"""
        # Arrange
        task_id = TaskId(str(uuid4()))
        subtask_repo = MockSubtaskRepository()
        
        # Create a task
        task = Task(
            id=task_id,
            title="Main Task",
            description="Task with subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.medium()
        )
        
        # Create subtasks with different statuses
        statuses = [TaskStatus.done(), TaskStatus.done(), TaskStatus.in_progress(), TaskStatus.todo()]
        for i, status in enumerate(statuses):
            subtask = Subtask(
                id=SubtaskId(str(uuid4())),
                title=f"Subtask {i+1}",
                description=f"Subtask number {i+1}",
                parent_task_id=task_id,
                status=status,
                priority=Priority.medium()
            )
            subtask_repo.save(subtask)
        
        # Create service
        completion_service = TaskCompletionService(subtask_repo)
        
        # Act
        summary = completion_service.get_subtask_completion_summary(task)
        
        # Assert
        assert summary['total'] == 4
        assert summary['completed'] == 2
        assert summary['incomplete'] == 2
        assert summary['completion_percentage'] == 50.0
        assert summary['can_complete_parent'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])