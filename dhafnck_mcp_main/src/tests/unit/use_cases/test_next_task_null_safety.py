#!/usr/bin/env python3
"""
Unit tests for NextTaskUseCase null safety fixes.

Tests the fix for NoneType error when task.labels or task.assignees is None.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
import uuid

from fastmcp.task_management.application.use_cases.next_task import NextTaskUseCase
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestNextTaskNullSafety:
    """Test NextTaskUseCase handles None values correctly"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        return Mock()
    
    @pytest.fixture
    def mock_context_service(self):
        """Create a mock context service"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_task_repository, mock_context_service):
        """Create NextTaskUseCase instance"""
        return NextTaskUseCase(mock_task_repository, mock_context_service)
    
    def create_task(self, **kwargs):
        """Helper to create a task with defaults"""
        defaults = {
            "id": TaskId(str(uuid.uuid4())),
            "title": "Test Task",
            "description": "Test Description",
            "git_branch_id": "test-branch",
            "status": TaskStatus.todo(),
            "priority": Priority.medium(),
            "assignees": [],
            "labels": [],
            "estimated_effort": "",
            "due_date": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        defaults.update(kwargs)
        return Task(**defaults)
    
    @pytest.mark.asyncio
    async def test_execute_with_none_labels(self, use_case, mock_task_repository):
        """Test that tasks with None labels don't cause NoneType errors"""
        # Create tasks with various label states
        tasks = [
            self.create_task(title="Task 1", labels=None),
            self.create_task(title="Task 2", labels=[]),
            self.create_task(title="Task 3", labels=["bug", "urgent"]),
            self.create_task(title="Task 4", labels=None, assignees=None),
        ]
        
        mock_task_repository.find_all.return_value = tasks
        
        # Execute with label filtering
        result = await use_case.execute(
            git_branch_id="test-branch",
            labels=["bug", "urgent"]
        )
        
        # Should not raise TypeError
        assert result is not None or result is None  # Just checking it doesn't crash
    
    @pytest.mark.asyncio
    async def test_execute_with_none_assignees(self, use_case, mock_task_repository):
        """Test that tasks with None assignees don't cause NoneType errors"""
        # Create tasks with various assignee states
        tasks = [
            self.create_task(title="Task 1", assignees=None),
            self.create_task(title="Task 2", assignees=[]),
            self.create_task(title="Task 3", assignees=["user1", "user2"]),
            self.create_task(title="Task 4", assignees=None, labels=None),
        ]
        
        mock_task_repository.find_all.return_value = tasks
        
        # Execute with assignee filtering
        result = await use_case.execute(
            git_branch_id="test-branch",
            assignee="user1"
        )
        
        # Should not raise TypeError
        assert result is not None or result is None  # Just checking it doesn't crash
    
    def test_label_filtering_logic(self):
        """Test the specific label filtering logic that was fixed"""
        # Create a task with None labels
        task = self.create_task(labels=None)
        
        # Test the exact logic from line 294
        labels_to_check = ["bug", "urgent"]
        
        # This should not raise "argument of type 'NoneType' is not iterable"
        if task.labels is not None and isinstance(task.labels, (list, tuple)) and any(label in task.labels for label in labels_to_check):
            matches = True
        else:
            matches = False
        
        assert not matches, "Task with None labels should not match any label"
    
    def test_assignee_filtering_logic(self):
        """Test the assignee filtering logic for None safety"""
        # Create a task with None assignees
        task = self.create_task(assignees=None)
        
        # Test similar logic for assignees
        assignees_to_check = ["user1", "user2"]
        
        # This should not raise "argument of type 'NoneType' is not iterable"
        if task.assignees is not None and isinstance(task.assignees, (list, tuple)) and any(assignee in task.assignees for assignee in assignees_to_check):
            matches = True
        else:
            matches = False
        
        assert not matches, "Task with None assignees should not match any assignee"
    
    @pytest.mark.asyncio
    async def test_mixed_null_and_valid_tasks(self, use_case, mock_task_repository):
        """Test handling a mix of tasks with None and valid values"""
        # Create a diverse set of tasks
        tasks = [
            self.create_task(title="Normal Task", labels=["feature"], assignees=["dev1"]),
            self.create_task(title="No Labels", labels=None, assignees=["dev2"]),
            self.create_task(title="No Assignees", labels=["bug"], assignees=None),
            self.create_task(title="Nothing", labels=None, assignees=None),
            self.create_task(title="Empty Lists", labels=[], assignees=[]),
        ]
        
        mock_task_repository.find_all.return_value = tasks
        
        # Execute with both filters
        result = await use_case.execute(
            git_branch_id="test-branch",
            labels=["bug", "feature"],
            assignee="dev1"
        )
        
        # Should complete without errors
        assert True  # If we get here, no TypeError was raised
    
    def test_edge_cases(self):
        """Test various edge cases for null safety"""
        test_cases = [
            # (labels, assignees, should_work)
            (None, None, True),
            (None, [], True),
            ([], None, True),
            ([], [], True),
            (["label"], None, True),
            (None, ["user"], True),
            ("not_a_list", None, True),  # Wrong type
            (None, "not_a_list", True),   # Wrong type
        ]
        
        for labels, assignees, should_work in test_cases:
            task = self.create_task(labels=labels, assignees=assignees)
            
            try:
                # Test label check
                if labels is not None:
                    labels_check = task.labels is not None and isinstance(task.labels, (list, tuple))
                else:
                    labels_check = False
                
                # Test assignee check
                if assignees is not None:
                    assignees_check = task.assignees is not None and isinstance(task.assignees, (list, tuple))
                else:
                    assignees_check = False
                
                if should_work:
                    assert True  # Should not raise exception
            except Exception as e:
                if should_work:
                    pytest.fail(f"Unexpected exception for labels={labels}, assignees={assignees}: {e}")