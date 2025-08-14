"""Test that dependencies are visible immediately after adding them via MCP tool."""
import pytest
import uuid
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass

from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestDependencyVisibilityFix:
    """Test that dependencies are visible immediately after adding them."""
    
    def setup_method(self):
        """Set up test dependencies."""
        # Create mock repositories
        self.task_repository = Mock()
        self.git_branch_repository = Mock()
        self.subtask_repository = Mock()
        self.context_service = Mock()
        
        # Create facade
        self.facade = TaskApplicationFacade(
            task_repository=self.task_repository,
            subtask_repository=self.subtask_repository,
            context_service=self.context_service,
            git_branch_repository=self.git_branch_repository
        )
        
    def test_add_dependency_shows_in_response(self):
        """Test that dependencies are visible immediately after adding them."""
        # Create test tasks with proper UUID format
        task_id_str = str(uuid.uuid4())
        dependency_id_str = str(uuid.uuid4())
        task_id = TaskId(task_id_str)
        dependency_id = TaskId(dependency_id_str)
        
        task = Task(
            id=task_id,
            title="Main Task",
            description="A task that will have dependencies",
            git_branch_id="branch-123",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            dependencies=[],  # Start with no dependencies
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        dependency_task = Task(
            id=dependency_id,
            title="Dependency Task",
            description="A task that others depend on",
            git_branch_id="branch-123",
            status=TaskStatus.todo(),
            priority=Priority.high(),
            dependencies=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock repository responses
        self.task_repository.find_by_id.side_effect = lambda tid: {
            task_id: task,
            dependency_id: dependency_task
        }.get(tid)
        
        # Mock save method to capture the updated task
        saved_task = None
        def mock_save(t):
            nonlocal saved_task
            saved_task = t
        self.task_repository.save.side_effect = mock_save
        
        # Act: Add dependency
        result = self.facade.add_dependency(task_id_str, dependency_id_str)
        
        # Assert: Response should include the task with dependencies
        assert result["success"] is True
        assert "task" in result
        assert result["task"] is not None
        
        # The task's dependencies should include the newly added dependency
        task_dict = result["task"]
        assert "dependencies" in task_dict
        assert len(task_dict["dependencies"]) == 1
        assert task_dict["dependencies"][0] == dependency_id_str
        
        # Verify the task was saved with the dependency
        assert saved_task is not None
        assert len(saved_task.dependencies) == 1
        assert saved_task.dependencies[0].value == dependency_id_str
        
    def test_add_multiple_dependencies_all_visible(self):
        """Test that multiple dependencies are all visible after adding them."""
        # Create test tasks with proper UUID format
        task_id_str = str(uuid.uuid4())
        dep1_id_str = str(uuid.uuid4())
        dep2_id_str = str(uuid.uuid4())
        dep3_id_str = str(uuid.uuid4())
        
        task_id = TaskId(task_id_str)
        dep1_id = TaskId(dep1_id_str)
        dep2_id = TaskId(dep2_id_str)
        dep3_id = TaskId(dep3_id_str)
        
        task = Task(
            id=task_id,
            title="Main Task",
            description="A task with multiple dependencies",
            git_branch_id="branch-123",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            dependencies=[],  # Start with no dependencies
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create dependency tasks
        dep_tasks = {}
        for dep_id in [dep1_id, dep2_id, dep3_id]:
            dep_tasks[dep_id] = Task(
                id=dep_id,
                title=f"Dependency {dep_id.value}",
                description="A dependency task",
                git_branch_id="branch-123",
                status=TaskStatus.todo(),
                priority=Priority.medium(),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        
        # Mock repository
        def mock_find_by_id(tid):
            if tid == task_id:
                return task
            return dep_tasks.get(tid)
        
        self.task_repository.find_by_id.side_effect = mock_find_by_id
        self.task_repository.save.return_value = None
        
        # Add first dependency
        result1 = self.facade.add_dependency(task_id_str, dep1_id_str)
        assert result1["success"] is True
        assert len(result1["task"]["dependencies"]) == 1
        assert dep1_id_str in result1["task"]["dependencies"]
        
        # Add second dependency
        result2 = self.facade.add_dependency(task_id_str, dep2_id_str)
        assert result2["success"] is True
        assert len(result2["task"]["dependencies"]) == 2
        assert dep1_id_str in result2["task"]["dependencies"]
        assert dep2_id_str in result2["task"]["dependencies"]
        
        # Add third dependency
        result3 = self.facade.add_dependency(task_id_str, dep3_id_str)
        assert result3["success"] is True
        assert len(result3["task"]["dependencies"]) == 3
        assert dep1_id_str in result3["task"]["dependencies"]
        assert dep2_id_str in result3["task"]["dependencies"]
        assert dep3_id_str in result3["task"]["dependencies"]
        
    def test_remove_dependency_updates_response(self):
        """Test that removing a dependency updates the response immediately."""
        # Create test tasks with proper UUID format
        task_id_str = str(uuid.uuid4())
        dep1_id_str = str(uuid.uuid4())
        dep2_id_str = str(uuid.uuid4())
        
        task_id = TaskId(task_id_str)
        dep1_id = TaskId(dep1_id_str)
        dep2_id = TaskId(dep2_id_str)
        
        task = Task(
            id=task_id,
            title="Main Task",
            description="A task with dependencies to remove",
            git_branch_id="branch-123",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            dependencies=[dep1_id, dep2_id],  # Start with two dependencies
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock repository
        self.task_repository.find_by_id.side_effect = lambda tid: task if tid == task_id else None
        self.task_repository.save.return_value = None
        
        # Remove first dependency
        result = self.facade.remove_dependency(task_id_str, dep1_id_str)
        
        # Assert: Response should show only one dependency remaining
        assert result["success"] is True
        assert "task" in result
        task_dict = result["task"]
        assert len(task_dict["dependencies"]) == 1
        assert task_dict["dependencies"][0] == dep2_id_str
        assert dep1_id_str not in task_dict["dependencies"]
        
    def test_duplicate_dependency_not_added(self):
        """Test that adding a duplicate dependency doesn't create duplicates."""
        # Create test tasks with proper UUID format
        task_id_str = str(uuid.uuid4())
        dependency_id_str = str(uuid.uuid4())
        
        task_id = TaskId(task_id_str)
        dependency_id = TaskId(dependency_id_str)
        
        task = Task(
            id=task_id,
            title="Main Task",
            description="A task that already has a dependency",
            git_branch_id="branch-123",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            dependencies=[dependency_id],  # Already has the dependency
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        dependency_task = Task(
            id=dependency_id,
            title="Dependency Task",
            description="Already a dependency",
            git_branch_id="branch-123",
            status=TaskStatus.todo(),
            priority=Priority.high(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock repository
        self.task_repository.find_by_id.side_effect = lambda tid: {
            task_id: task,
            dependency_id: dependency_task
        }.get(tid)
        self.task_repository.save.return_value = None
        
        # Try to add the same dependency again
        result = self.facade.add_dependency(task_id_str, dependency_id_str)
        
        # Assert: Should succeed but dependencies list should still have only one
        assert result["success"] is True
        assert "already exists" in result["message"] or "added" in result["message"]
        task_dict = result["task"]
        assert len(task_dict["dependencies"]) == 1
        assert task_dict["dependencies"][0] == dependency_id_str