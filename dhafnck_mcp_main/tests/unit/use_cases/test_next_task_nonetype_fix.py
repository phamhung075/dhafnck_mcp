"""Test cases for NextTaskUseCase NoneType error fix

This test suite validates that the NextTaskUseCase properly handles None values
in task attributes (assignees, labels) without throwing 'NoneType is not iterable' errors.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import List, Optional
import asyncio

from fastmcp.task_management.application.use_cases.next_task import NextTaskUseCase, NextTaskResponse
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestNextTaskNoneTypeFix:
    """Test cases for fixing NoneType errors in NextTaskUseCase"""

    def create_mock_task(
        self,
        task_id: str = "12345678-1234-5678-1234-567812345678",
        title: str = "Test Task",
        status: str = "todo",
        priority: str = "medium",
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        subtasks: Optional[List[dict]] = None
    ) -> MagicMock:
        """Create a mock task with configurable attributes"""
        task = MagicMock(spec=Task)
        task.id = MagicMock()
        task.id.value = task_id
        task.title = title
        task.description = "Test description"
        task.status = TaskStatus.from_string(status)
        task.priority = Priority.from_string(priority)
        task.assignees = assignees  # Can be None
        task.labels = labels  # Can be None
        task.dependencies = [MagicMock(value=dep) for dep in (dependencies or [])]
        task.subtasks = subtasks or []
        task.context_id = f"context-{task_id}"
        
        # Mock methods
        task.get_subtask_progress = MagicMock(return_value={"completed": 0, "total": 0, "percentage": 0})
        task.to_dict = MagicMock(return_value={
            "id": task_id,
            "title": title,
            "status": status,
            "priority": priority,
            "assignees": assignees,
            "labels": labels
        })
        
        return task

    @pytest.mark.asyncio
    async def test_apply_filters_with_none_assignees(self):
        """Test that filtering by assignee works when task.assignees is None"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Create tasks with various assignee configurations
        tasks = [
            self.create_mock_task("11111111-1111-1111-1111-111111111111", "Task with assignees", assignees=["user1", "user2"]),
            self.create_mock_task("22222222-2222-2222-2222-222222222222", "Task with None assignees", assignees=None),
            self.create_mock_task("33333333-3333-3333-3333-333333333333", "Task with empty assignees", assignees=[]),
            self.create_mock_task("44444444-4444-4444-4444-444444444444", "Task with different assignees", assignees=["user3"])
        ]
        
        # Act - filter by assignee "user1"
        filtered = use_case._apply_filters(tasks, assignee="user1", project_id=None, labels=None)
        
        # Assert - should only return first task with user1
        assert len(filtered) == 1
        assert filtered[0].id.value == "11111111-1111-1111-1111-111111111111"

    @pytest.mark.asyncio
    async def test_apply_filters_with_none_labels(self):
        """Test that filtering by labels works when task.labels is None"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Create tasks with various label configurations
        tasks = [
            self.create_mock_task("11111111-1111-1111-1111-111111111111", "Task with labels", labels=["bug", "urgent"]),
            self.create_mock_task("22222222-2222-2222-2222-222222222222", "Task with None labels", labels=None),
            self.create_mock_task("33333333-3333-3333-3333-333333333333", "Task with empty labels", labels=[]),
            self.create_mock_task("44444444-4444-4444-4444-444444444444", "Task with different labels", labels=["feature"])
        ]
        
        # Act - filter by label "bug"
        filtered = use_case._apply_filters(tasks, assignee=None, project_id=None, labels=["bug"])
        
        # Assert - should only return first task with bug label
        assert len(filtered) == 1
        assert filtered[0].id.value == "11111111-1111-1111-1111-111111111111"

    @pytest.mark.asyncio
    async def test_apply_filters_with_none_tasks_list(self):
        """Test that filtering handles None or empty task list gracefully"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Act & Assert - None tasks
        filtered = use_case._apply_filters(None, assignee="user1", project_id=None, labels=None)
        assert filtered == []
        
        # Act & Assert - Empty list
        filtered = use_case._apply_filters([], assignee="user1", project_id=None, labels=None)
        assert filtered == []

    @pytest.mark.asyncio
    async def test_sort_tasks_with_none_priority(self):
        """Test that sorting handles tasks with None priority"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Create tasks with various priority configurations
        task1 = self.create_mock_task("11111111-1111-1111-1111-111111111111", "High priority task", priority="high")
        task2 = self.create_mock_task("22222222-2222-2222-2222-222222222222", "None priority task")
        task2.priority = None  # Explicitly set to None
        task3 = self.create_mock_task("33333333-3333-3333-3333-333333333333", "Low priority task", priority="low")
        
        tasks = [task2, task1, task3]
        
        # Act
        sorted_tasks = use_case._sort_tasks_by_priority(tasks)
        
        # Assert - high priority should be first, None should be treated as medium
        assert len(sorted_tasks) == 3
        assert sorted_tasks[0].id.value == "11111111-1111-1111-1111-111111111111"  # high priority
        assert sorted_tasks[2].id.value == "33333333-3333-3333-3333-333333333333"  # low priority

    @pytest.mark.asyncio
    async def test_sort_tasks_with_none_status(self):
        """Test that sorting handles tasks with None status"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Create tasks with various status configurations
        task1 = self.create_mock_task("11111111-1111-1111-1111-111111111111", "In progress task", status="in_progress")
        task2 = self.create_mock_task("22222222-2222-2222-2222-222222222222", "None status task")
        task2.status = None  # Explicitly set to None
        task3 = self.create_mock_task("33333333-3333-3333-3333-333333333333", "Todo task", status="todo")
        
        tasks = [task2, task1, task3]
        
        # Act
        sorted_tasks = use_case._sort_tasks_by_priority(tasks)
        
        # Assert - should not crash with None status
        assert len(sorted_tasks) == 3

    @pytest.mark.asyncio
    async def test_execute_with_all_none_attributes(self):
        """Test the full execute flow with tasks having None attributes"""
        # Arrange
        repository = MagicMock()
        context_service = MagicMock()
        use_case = NextTaskUseCase(repository, context_service)
        
        # Create tasks with None attributes
        tasks = [
            self.create_mock_task("11111111-1111-1111-1111-111111111111", "Task with all None", 
                                assignees=None, labels=None, status="todo"),
            self.create_mock_task("22222222-2222-2222-2222-222222222222", "Task with some None", 
                                assignees=["user1"], labels=None, status="in_progress"),
            self.create_mock_task("33333333-3333-3333-3333-333333333333", "Complete task", 
                                assignees=None, labels=["bug"], status="done")
        ]
        
        repository.find_all.return_value = tasks
        
        # Act - execute with filters that would trigger None checks
        result = await use_case.execute(
            assignee="user1",
            labels=["bug"],
            project_id="proj-123",
            git_branch_id="main",
            include_context=False
        )
        
        # Assert - no tasks match both filters (user1 AND bug)
        assert isinstance(result, NextTaskResponse)
        assert result.has_next is False
        assert "No tasks match" in result.message
        
        # Now test with just assignee filter
        result2 = await use_case.execute(
            assignee="user1",
            project_id="proj-123",
            git_branch_id="main",
            include_context=False
        )
        
        # Should return task-2 which has user1 assignee
        assert result2.has_next is True
        assert result2.next_item["task"]["id"] == "22222222-2222-2222-2222-222222222222"

    @pytest.mark.asyncio
    async def test_complex_filtering_scenario(self):
        """Test complex filtering with multiple None values and edge cases"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Create a complex task set
        tasks = [
            # Task with everything None
            self.create_mock_task("11111111-1111-1111-1111-111111111111", "All None task", 
                                assignees=None, labels=None),
            # Task with non-list assignees (edge case)
            self.create_mock_task("22222222-2222-2222-2222-222222222222", "String assignee task"),
            # Task with non-list labels (edge case)  
            self.create_mock_task("33333333-3333-3333-3333-333333333333", "String label task"),
            # Normal task
            self.create_mock_task("44444444-4444-4444-4444-444444444444", "Normal task",
                                assignees=["user1", "user2"], 
                                labels=["feature", "high-priority"])
        ]
        
        # Simulate non-list attributes (edge cases)
        tasks[1].assignees = "user1"  # String instead of list
        tasks[2].labels = "bug"  # String instead of list
        
        repository.find_all.return_value = tasks
        
        # Act - multiple filter combinations
        # Filter by assignee
        result1 = await use_case.execute(assignee="user1", include_context=False)
        # Filter by labels
        result2 = await use_case.execute(labels=["feature"], include_context=False)
        # Filter by both
        result3 = await use_case.execute(assignee="user2", labels=["high-priority"], include_context=False)
        
        # Assert
        # Only task-4 has proper list attributes and matches filters
        assert result1.has_next is True
        assert result1.next_item["task"]["id"] == "44444444-4444-4444-4444-444444444444"
        
        assert result2.has_next is True
        assert result2.next_item["task"]["id"] == "44444444-4444-4444-4444-444444444444"
        
        assert result3.has_next is True
        assert result3.next_item["task"]["id"] == "44444444-4444-4444-4444-444444444444"

    @pytest.mark.asyncio
    async def test_should_generate_context_info_with_none_values(self):
        """Test _should_generate_context_info handles None values properly"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Test various None scenarios
        # Task with None status
        task1 = self.create_mock_task("11111111-1111-1111-1111-111111111111")
        task1.status = None
        assert use_case._should_generate_context_info(task1) is False
        
        # Task with None subtasks
        task2 = self.create_mock_task("22222222-2222-2222-2222-222222222222", status="todo")
        task2.subtasks = None
        assert use_case._should_generate_context_info(task2) is True
        
        # None task
        assert use_case._should_generate_context_info(None) is False
        
        # Task without status attribute
        task3 = MagicMock()
        delattr(task3, 'status')
        assert use_case._should_generate_context_info(task3) is False

    @pytest.mark.asyncio
    async def test_empty_repository_response(self):
        """Test handling when repository returns None or empty list"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Test 1: Repository returns None
        repository.find_all.return_value = None
        result = await use_case.execute()
        assert result.has_next is False
        assert "No tasks found" in result.message
        
        # Test 2: Repository returns empty list
        repository.find_all.return_value = []
        result = await use_case.execute()
        assert result.has_next is False
        assert "No tasks found" in result.message

    @pytest.mark.asyncio  
    async def test_malformed_task_attributes(self):
        """Test handling of tasks with malformed attributes"""
        # Arrange
        repository = MagicMock()
        use_case = NextTaskUseCase(repository)
        
        # Create task with dictionary assignees (malformed)
        task = self.create_mock_task("11111111-1111-1111-1111-111111111111", status="todo")
        task.assignees = {"user": "user1"}  # Dict instead of list
        task.labels = 123  # Number instead of list
        
        repository.find_all.return_value = [task]
        
        # Act - should not crash
        result = await use_case.execute(assignee="user1", labels=["bug"])
        
        # Assert - task is filtered out due to malformed attributes
        assert result.has_next is False
        assert "No tasks match" in result.message or "No actionable tasks" in result.message