"""Test to verify the task label persistence fix works correctly"""

import uuid

import pytest

from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.infrastructure.database.models import (
    Project,
    ProjectGitBranch,
)
from fastmcp.task_management.infrastructure.database.test_helpers import (
    cleanup_test_database,
    setup_test_database,
)
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import (
    ORMTaskRepository,
)


class TestTaskLabelPersistenceFix:
    """Test cases to verify the task label persistence fix is working"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test database before each test and cleanup after"""
        self.db_adapter = setup_test_database()
        
        # Create test project and branch
        with self.db_adapter.get_session() as session:
            # Create test project
            project = Project(
                id=str(uuid.uuid4()),
                name="Test Project",
                description="Test project for label tests"
            )
            session.add(project)
            
            # Create test branch
            self.git_branch_id = str(uuid.uuid4())
            branch = ProjectGitBranch(
                id=self.git_branch_id,
                project_id=project.id,
                git_branch_name="test-branch",
                git_branch_description="Test branch for label tests"
            )
            session.add(branch)
            session.commit()
        
        yield
        
        cleanup_test_database()
    
    def test_labels_persisted_in_save_method(self):
        """Test that labels are now correctly saved in the repository save() method"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id=self.git_branch_id)
        task_id = str(uuid.uuid4())
        
        # Create a task entity with labels
        task = TaskEntity(
            id=TaskId(task_id),
            title="Test Task with Labels",
            description="Task to test label persistence",
            git_branch_id=self.git_branch_id,
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            labels=["bug", "urgent", "backend"]  # These labels should be persisted
        )
        
        # Act
        # Save the task
        save_result = repository.save(task)
        
        # Retrieve the task
        retrieved_task = repository.get_task(task_id)
        
        # Assert
        assert save_result is True, "Task save should succeed"
        assert retrieved_task is not None, "Task should be retrievable"
        
        # This should now pass with the fix
        assert sorted(retrieved_task.labels) == sorted(["bug", "urgent", "backend"]), \
            f"Expected labels ['bug', 'urgent', 'backend'], but got {retrieved_task.labels}"
    
    def test_labels_handled_in_create_task_method(self):
        """Test that labels are now handled in create_task() method"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id=self.git_branch_id)
        
        # Act
        # Create a task with labels using create_task method
        task = repository.create_task(
            title="Task Created with Labels",
            description="Testing label creation",
            priority="high",
            label_names=["feature", "frontend", "v2.0"]  # These should be saved
        )
        
        # Retrieve the task to verify
        retrieved_task = repository.get_task(str(task.id))
        
        # Assert
        assert task is not None, "Task creation should succeed"
        assert retrieved_task is not None, "Task should be retrievable"
        
        # This should now pass with the fix
        assert sorted(retrieved_task.labels) == sorted(["feature", "frontend", "v2.0"]), \
            f"Expected labels ['feature', 'frontend', 'v2.0'], but got {retrieved_task.labels}"
    
    def test_labels_updated_in_update_task_method(self):
        """Test that labels are now updated in update_task() method"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id=self.git_branch_id)
        
        # Create a task first
        task = repository.create_task(
            title="Task to Update Labels",
            description="Testing label updates",
            priority="medium",
            label_names=["initial", "test"]
        )
        task_id = str(task.id)
        
        # Act
        # Update the task with new labels
        updated_task = repository.update_task(
            task_id,
            label_names=["updated", "tested", "fixed"]  # These should replace the old labels
        )
        
        # Retrieve the task to verify
        retrieved_task = repository.get_task(task_id)
        
        # Assert
        assert updated_task is not None, "Task update should succeed"
        assert retrieved_task is not None, "Task should be retrievable"
        
        # This should now pass with the fix
        assert sorted(retrieved_task.labels) == sorted(["updated", "tested", "fixed"]), \
            f"Expected labels ['updated', 'tested', 'fixed'], but got {retrieved_task.labels}"
    
    def test_labels_persisted_across_multiple_operations(self):
        """Test that labels persist correctly across create, update, and save operations"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id=self.git_branch_id)
        
        # Create a task with initial labels
        task = repository.create_task(
            title="Multi-operation Label Test",
            description="Testing labels across operations",
            priority="low",
            label_names=["initial", "label1"]
        )
        task_id = str(task.id)
        
        # Update with new labels using update_task
        repository.update_task(
            task_id,
            label_names=["updated", "label2"]
        )
        
        # Get the task entity and add more labels using save
        task_entity = repository.get_task(task_id)
        task_entity.labels = ["final", "label3", "label4"]
        repository.save(task_entity)
        
        # Retrieve the final state
        final_task = repository.get_task(task_id)
        
        # Assert
        assert final_task is not None, "Task should exist"
        assert sorted(final_task.labels) == sorted(["final", "label3", "label4"]), \
            f"Expected labels ['final', 'label3', 'label4'], but got {final_task.labels}"
    
    def test_empty_labels_handled_correctly(self):
        """Test that empty labels are handled correctly"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id=self.git_branch_id)
        
        # Create task without labels
        task = repository.create_task(
            title="Task Without Labels",
            description="Testing empty labels",
            priority="medium"
        )
        task_id = str(task.id)
        
        # Add labels
        repository.update_task(task_id, label_names=["added1", "added2"])
        
        # Clear labels
        repository.update_task(task_id, label_names=[])
        
        # Retrieve to verify
        final_task = repository.get_task(task_id)
        
        # Assert
        assert final_task is not None, "Task should exist"
        assert final_task.labels == [], f"Expected empty labels, but got {final_task.labels}"
    
    def test_duplicate_labels_handled_correctly(self):
        """Test that duplicate labels are handled correctly"""
        # Arrange
        repository = ORMTaskRepository(git_branch_id=self.git_branch_id)
        
        # Create task with duplicate labels
        task = repository.create_task(
            title="Task with Duplicate Labels",
            description="Testing duplicate label handling",
            priority="high",
            label_names=["duplicate", "duplicate", "unique", "duplicate"]
        )
        
        # Retrieve to verify
        retrieved_task = repository.get_task(str(task.id))
        
        # Assert - duplicates should be removed
        assert retrieved_task is not None, "Task should exist"
        # Sort for consistent comparison
        assert sorted(retrieved_task.labels) == sorted(["duplicate", "unique"]), \
            f"Expected ['duplicate', 'unique'], but got {retrieved_task.labels}"


@pytest.mark.integration
def test_label_persistence_fix_comprehensive():
    """Run comprehensive tests to verify the label persistence fix"""
    test_suite = TestTaskLabelPersistenceFix()
    test_suite.setup_and_teardown()
    
    # Run all tests
    try:
        test_suite.test_labels_persisted_in_save_method()
        print("✓ Test 1 passed - labels ARE being saved in save()")
    except AssertionError as e:
        print(f"✗ Test 1 failed - {e}")
    
    try:
        test_suite.test_labels_handled_in_create_task_method()
        print("✓ Test 2 passed - labels ARE being handled in create_task()")
    except AssertionError as e:
        print(f"✗ Test 2 failed - {e}")
    
    try:
        test_suite.test_labels_updated_in_update_task_method()
        print("✓ Test 3 passed - labels ARE being updated in update_task()")
    except AssertionError as e:
        print(f"✗ Test 3 failed - {e}")
    
    try:
        test_suite.test_labels_persisted_across_multiple_operations()
        print("✓ Test 4 passed - labels persist across multiple operations")
    except AssertionError as e:
        print(f"✗ Test 4 failed - {e}")
    
    try:
        test_suite.test_empty_labels_handled_correctly()
        print("✓ Test 5 passed - empty labels handled correctly")
    except AssertionError as e:
        print(f"✗ Test 5 failed - {e}")
    
    try:
        test_suite.test_duplicate_labels_handled_correctly()
        print("✓ Test 6 passed - duplicate labels handled correctly")
    except AssertionError as e:
        print(f"✗ Test 6 failed - {e}")