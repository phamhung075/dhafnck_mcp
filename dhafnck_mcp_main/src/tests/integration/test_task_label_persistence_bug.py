"""Test case to reproduce the task label persistence bug"""

import pytest

from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import (
    ORMTaskRepository,
)


class TestTaskLabelPersistenceBug:
    """Test cases to reproduce and verify the task label persistence bug"""
    
    def test_labels_not_persisted_in_save_method(self):
        """Test that demonstrates labels are not being saved in the repository save() method"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id="test-branch-123")
        
        # Create a task entity with labels
        task = TaskEntity(
            id=TaskId("test-task-123"),
            title="Test Task",
            description="Task with labels",
            git_branch_id="test-branch-123",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            labels=["bug", "urgent", "backend"]  # These labels should be persisted
        )
        
        # Act
        # Save the task
        save_result = repository.save(task)
        
        # Retrieve the task
        retrieved_task = repository.get_task("test-task-123")
        
        # Assert
        assert save_result is True, "Task save should succeed"
        assert retrieved_task is not None, "Task should be retrievable"
        
        # This assertion will fail because labels are not saved
        assert retrieved_task.labels == ["bug", "urgent", "backend"], \
            f"Expected labels ['bug', 'urgent', 'backend'], but got {retrieved_task.labels}"
    
    def test_labels_not_handled_in_create_task_method(self):
        """Test that demonstrates labels are not handled in create_task() method"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id="test-branch-456")
        
        # Act
        # Create a task with labels using create_task method
        task = repository.create_task(
            title="Task with Labels",
            description="Testing label creation",
            priority="high",
            label_names=["feature", "frontend", "v2.0"]  # These should be saved
        )
        
        # Retrieve the task to verify
        retrieved_task = repository.get_task(str(task.id))
        
        # Assert
        assert task is not None, "Task creation should succeed"
        assert retrieved_task is not None, "Task should be retrievable"
        
        # This assertion will fail because label handling is not implemented
        assert retrieved_task.labels == ["feature", "frontend", "v2.0"], \
            f"Expected labels ['feature', 'frontend', 'v2.0'], but got {retrieved_task.labels}"
    
    def test_labels_not_updated_in_update_task_method(self):
        """Test that demonstrates labels are not updated in update_task() method"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id="test-branch-789")
        
        # Create a task first
        task = repository.create_task(
            title="Task to Update",
            description="Testing label updates",
            priority="medium"
        )
        task_id = str(task.id)
        
        # Act
        # Update the task with labels
        updated_task = repository.update_task(
            task_id,
            label_names=["updated", "tested", "fixed"]  # These should be saved
        )
        
        # Retrieve the task to verify
        retrieved_task = repository.get_task(task_id)
        
        # Assert
        assert updated_task is not None, "Task update should succeed"
        assert retrieved_task is not None, "Task should be retrievable"
        
        # This assertion will fail because label updating is not implemented
        assert retrieved_task.labels == ["updated", "tested", "fixed"], \
            f"Expected labels ['updated', 'tested', 'fixed'], but got {retrieved_task.labels}"


@pytest.mark.integration
def test_label_persistence_bug():
    """Integration test to demonstrate the label persistence bug"""
    test_suite = TestTaskLabelPersistenceBug()
    
    # Run all tests - they should fail, demonstrating the bug
    try:
        test_suite.test_labels_not_persisted_in_save_method()
        print("✗ Test 1 passed unexpectedly - labels ARE being saved in save()")
    except AssertionError as e:
        print(f"✓ Test 1 failed as expected - {e}")
    
    try:
        test_suite.test_labels_not_handled_in_create_task_method()
        print("✗ Test 2 passed unexpectedly - labels ARE being handled in create_task()")
    except AssertionError as e:
        print(f"✓ Test 2 failed as expected - {e}")
    
    try:
        test_suite.test_labels_not_updated_in_update_task_method()
        print("✗ Test 3 passed unexpectedly - labels ARE being updated in update_task()")
    except AssertionError as e:
        print(f"✓ Test 3 failed as expected - {e}")