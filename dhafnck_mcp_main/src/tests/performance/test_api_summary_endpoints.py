"""
Test API Summary Endpoints for Performance Optimization

This test verifies that the lightweight summary endpoints are working correctly
and provide the expected performance improvements.
"""

import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, patch

from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.facades.unified_context_facade import UnifiedContextFacade


class TestAPISummaryEndpoints:
    """Test suite for API summary endpoints"""
    
    def test_count_tasks_method(self):
        """Test count_tasks method returns correct count"""
        # Create mock repository
        mock_repo = Mock()
        
        # Create facade with mock
        facade = TaskApplicationFacade(task_repository=mock_repo)
        
        # Test count_tasks method
        filters = {
            "git_branch_id": "test-branch-123",
            "status": "todo"
        }
        
        # Mock the list_tasks_use_case
        mock_response = Mock()
        mock_response.count = 42
        facade._list_tasks_use_case.execute = Mock(return_value=mock_response)
        
        result = facade.count_tasks(filters)
        
        assert result["success"] is True
        assert result["count"] == 42
    
    def test_list_tasks_summary_method(self):
        """Test list_tasks_summary returns lightweight summaries"""
        # Create mock repository
        mock_repo = Mock()
        
        # Create facade with mock
        facade = TaskApplicationFacade(task_repository=mock_repo)
        
        # Create mock task
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.title = "Test Task"
        mock_task.status = "todo"
        mock_task.priority = "high"
        mock_task.created_at = "2024-01-01T00:00:00Z"
        mock_task.updated_at = "2024-01-01T00:00:00Z"
        mock_task.subtasks = []
        mock_task.assignees = ["user1"]
        mock_task.dependencies = []
        
        # Mock the list_tasks_use_case
        mock_response = Mock()
        mock_response.tasks = [mock_task]
        mock_response.count = 1
        facade._list_tasks_use_case.execute = Mock(return_value=mock_response)
        
        # Test list_tasks_summary
        filters = {"git_branch_id": "test-branch-123"}
        result = facade.list_tasks_summary(filters, offset=0, limit=20)
        
        assert result["success"] is True
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["id"] == "task-123"
        assert result["tasks"][0]["title"] == "Test Task"
        assert "subtasks" in result["tasks"][0]
        assert "assignees" in result["tasks"][0]
    
    def test_list_subtasks_summary_method(self):
        """Test list_subtasks_summary returns lightweight subtask summaries"""
        # Create mock repositories
        mock_task_repo = Mock()
        mock_subtask_repo = Mock()
        
        # Create facade with mocks
        facade = TaskApplicationFacade(
            task_repository=mock_task_repo,
            subtask_repository=mock_subtask_repo
        )
        
        # Create mock subtask
        mock_subtask = Mock()
        mock_subtask.id = "subtask-123"
        mock_subtask.title = "Test Subtask"
        mock_subtask.status = "in_progress"
        mock_subtask.priority = "medium"
        mock_subtask.progress_percentage = 50
        mock_subtask.assignees = []
        
        # Mock the find_by_parent_task_id method
        mock_subtask_repo.find_by_parent_task_id = Mock(return_value=[mock_subtask])
        
        # Test list_subtasks_summary
        result = facade.list_subtasks_summary("parent-task-123")
        
        assert result["success"] is True
        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["id"] == "subtask-123"
        assert result["subtasks"][0]["title"] == "Test Subtask"
        assert result["subtasks"][0]["progress_percentage"] == 50
    
    def test_get_context_summary_method(self):
        """Test get_context_summary returns lightweight context info"""
        # Create mock service
        mock_service = Mock()
        
        # Create facade with mock
        facade = UnifiedContextFacade(unified_service=mock_service)
        
        # Mock successful context retrieval
        mock_service.get_context = Mock(return_value={
            "success": True,
            "context": {
                "id": "context-123",
                "data": {"some": "data"},
                "created_at": "2024-01-01T00:00:00Z"
            }
        })
        
        # Test get_context_summary
        result = facade.get_context_summary("task-123")
        
        assert result["success"] is True
        assert result["has_context"] is True
        assert result["context_size"] > 0
        assert result["last_updated"] == "2024-01-01T00:00:00Z"
    
    def test_performance_comparison(self):
        """Compare performance between full load and summary load"""
        # Create mock repository
        mock_repo = Mock()
        
        # Create facade with mock
        facade = TaskApplicationFacade(task_repository=mock_repo)
        
        # Create 100 mock tasks
        mock_tasks = []
        for i in range(100):
            mock_task = Mock()
            mock_task.id = f"task-{i}"
            mock_task.title = f"Task {i}"
            mock_task.status = "todo"
            mock_task.priority = "medium"
            mock_task.created_at = "2024-01-01T00:00:00Z"
            mock_task.updated_at = "2024-01-01T00:00:00Z"
            mock_task.subtasks = [f"sub-{i}-{j}" for j in range(5)]  # 5 subtasks each
            mock_task.assignees = [f"user-{j}" for j in range(3)]  # 3 assignees each
            mock_task.dependencies = [f"dep-{i}-{j}" for j in range(2)]  # 2 dependencies each
            mock_task.description = "A" * 500  # Large description
            mock_task.details = "B" * 1000  # Large details
            mock_tasks.append(mock_task)
        
        # Mock the list_tasks_use_case
        mock_response = Mock()
        mock_response.tasks = mock_tasks
        mock_response.count = 100
        facade._list_tasks_use_case.execute = Mock(return_value=mock_response)
        
        # Measure summary load time
        start_time = time.time()
        summary_result = facade.list_tasks_summary(
            {"git_branch_id": "test-branch"},
            offset=0,
            limit=20,
            include_counts=True
        )
        summary_time = time.time() - start_time
        
        # Measure full load time (simulated by accessing all attributes)
        start_time = time.time()
        full_result = facade.list_tasks(
            status=None,
            priority=None,
            assignees=[],
            labels=[],
            limit=20,
            offset=0,
            git_branch_id="test-branch",
            minimal=False
        )
        full_time = time.time() - start_time
        
        # Verify summary is more efficient
        assert summary_result["success"] is True
        assert len(summary_result["tasks"]) == 20  # Only requested 20
        
        # Calculate data size difference
        import json
        summary_size = len(json.dumps(summary_result["tasks"]))
        full_size = len(json.dumps(full_result["tasks"]))
        
        print(f"\nPerformance Comparison:")
        print(f"Summary endpoint size: {summary_size} bytes")
        print(f"Full endpoint size: {full_size} bytes")
        print(f"Size reduction: {round((1 - summary_size/full_size) * 100, 1)}%")
        print(f"Summary time: {round(summary_time * 1000, 2)}ms")
        print(f"Full time: {round(full_time * 1000, 2)}ms")
        
        # Summary should be significantly smaller
        assert summary_size < full_size * 0.5  # At least 50% smaller


if __name__ == "__main__":
    test = TestAPISummaryEndpoints()
    test.test_count_tasks_method()
    test.test_list_tasks_summary_method()
    test.test_list_subtasks_summary_method()
    test.test_get_context_summary_method()
    test.test_performance_comparison()