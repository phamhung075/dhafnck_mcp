"""
Tests for Task Summary Routes for Performance Optimization
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from fastmcp.server.routes.task_summary_routes import (
    get_task_summaries,
    get_full_task,
    get_subtask_summaries,
    get_task_context_summary,
    get_performance_metrics,
    task_summary_routes
)
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.facades.unified_context_facade import UnifiedContextFacade
from fastmcp.config.auth_config import AuthConfig


class TestTaskSummaryRoutes:
    """Test suite for task summary routes performance optimization endpoints."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=b'{}')
        request.path_params = {}
        return request

    @pytest.fixture
    def mock_request_with_body(self):
        """Create a mock request with JSON body."""
        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=json.dumps({
            "git_branch_id": "branch-123",
            "page": 1,
            "limit": 20,
            "include_counts": True,
            "status_filter": "todo",
            "priority_filter": "high"
        }).encode())
        request.path_params = {}
        return request

    @pytest.fixture
    def mock_task_facade_result(self):
        """Mock task facade successful result."""
        return {
            "success": True,
            "tasks": [
                {
                    "id": "task-123",
                    "title": "Test Task 1",
                    "status": "todo",
                    "priority": "high",
                    "subtasks": ["sub-1", "sub-2"],
                    "assignees": ["user-1"],
                    "dependencies": None,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                },
                {
                    "id": "task-456",
                    "title": "Test Task 2",
                    "status": "in_progress",
                    "priority": "medium",
                    "subtasks": [],
                    "assignees": [],
                    "dependencies": ["task-789"],
                    "created_at": "2024-01-03T00:00:00Z",
                    "updated_at": "2024-01-04T00:00:00Z"
                }
            ],
            "count": 2
        }

    @pytest.mark.asyncio
    async def test_get_task_summaries_success(self, mock_request_with_body, mock_task_facade_result):
        """Test successful task summaries retrieval with full parameters."""
        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory') as MockContextFactory, \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            # Setup auth config
            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.count_tasks.return_value = {"success": True, "count": 2}
            mock_task_facade.list_tasks_summary.return_value = mock_task_facade_result
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            # Setup context facade
            mock_context_facade = Mock()
            mock_context_facade.get_context_summary.return_value = {
                "success": True, 
                "has_context": True
            }
            
            mock_context_factory_instance = Mock()
            mock_context_factory_instance.create_facade.return_value = mock_context_facade
            MockContextFactory.return_value = mock_context_factory_instance

            # Call the function
            response = await get_task_summaries(mock_request_with_body)

            # Verify response
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            
            assert len(response_data["tasks"]) == 2
            assert response_data["total"] == 2
            assert response_data["page"] == 1
            assert response_data["limit"] == 20
            assert response_data["has_more"] is False

            # Check first task summary structure
            first_task = response_data["tasks"][0]
            assert first_task["id"] == "task-123"
            assert first_task["title"] == "Test Task 1"
            assert first_task["status"] == "todo"
            assert first_task["priority"] == "high"
            assert first_task["subtask_count"] == 2
            assert first_task["assignees_count"] == 1
            assert first_task["has_dependencies"] is False
            assert first_task["has_context"] is True

    @pytest.mark.asyncio
    async def test_get_task_summaries_missing_git_branch_id(self, mock_request):
        """Test task summaries with missing git_branch_id."""
        response = await get_task_summaries(mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        response_data = json.loads(response.body.decode())
        assert response_data["error"] == "git_branch_id is required"

    @pytest.mark.asyncio
    async def test_get_task_summaries_facade_failure(self, mock_request_with_body):
        """Test task summaries when facade returns failure."""
        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup facade to return failure
            mock_task_facade = Mock()
            mock_task_facade.count_tasks.return_value = {"success": True, "count": 0}
            mock_task_facade.list_tasks_summary.return_value = {
                "success": False,
                "error": "Database connection failed"
            }
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            response = await get_task_summaries(mock_request_with_body)
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == 500
            response_data = json.loads(response.body.decode())
            assert "Database connection failed" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_task_summaries_exception_handling(self, mock_request_with_body):
        """Test exception handling in get_task_summaries."""
        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory', 
                  side_effect=Exception("Unexpected error")):
            
            response = await get_task_summaries(mock_request_with_body)
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == 500
            response_data = json.loads(response.body.decode())
            assert "Unexpected error" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_full_task_success(self, mock_request):
        """Test successful full task retrieval."""
        mock_request.path_params = {"task_id": "task-123"}
        
        mock_task_data = {
            "id": "task-123",
            "title": "Full Task",
            "description": "Complete task details",
            "status": "in_progress",
            "priority": "high",
            "assignees": ["user-1", "user-2"],
            "subtasks": [],
            "dependencies": []
        }

        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.get_task.return_value = {
                "success": True,
                "task": mock_task_data
            }
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            response = await get_full_task(mock_request)
            
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            assert response_data["id"] == "task-123"
            assert response_data["title"] == "Full Task"
            assert response_data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_get_full_task_missing_task_id(self, mock_request):
        """Test get_full_task with missing task_id."""
        response = await get_full_task(mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        response_data = json.loads(response.body.decode())
        assert response_data["error"] == "task_id is required"

    @pytest.mark.asyncio
    async def test_get_full_task_not_found(self, mock_request):
        """Test get_full_task when task is not found."""
        mock_request.path_params = {"task_id": "nonexistent"}

        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup task facade to return not found
            mock_task_facade = Mock()
            mock_task_facade.get_task.return_value = {
                "success": False,
                "error": "Task not found"
            }
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            response = await get_full_task(mock_request)
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == 404
            response_data = json.loads(response.body.decode())
            assert "Task nonexistent not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_subtask_summaries_success(self, mock_request):
        """Test successful subtask summaries retrieval."""
        mock_request.body = AsyncMock(return_value=json.dumps({
            "parent_task_id": "task-123",
            "include_counts": True
        }).encode())

        mock_subtasks_data = [
            {
                "id": "sub-1",
                "title": "Subtask 1",
                "status": "done",
                "priority": "high",
                "assignees": ["user-1"],
                "progress_percentage": 100
            },
            {
                "id": "sub-2",
                "title": "Subtask 2",
                "status": "in_progress",
                "priority": "medium",
                "assignees": [],
                "progress_percentage": 50
            }
        ]

        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": True,
                "subtasks": mock_subtasks_data
            }
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            response = await get_subtask_summaries(mock_request)
            
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            
            assert response_data["parent_task_id"] == "task-123"
            assert response_data["total_count"] == 2
            assert len(response_data["subtasks"]) == 2
            
            # Check progress summary
            progress = response_data["progress_summary"]
            assert progress["total"] == 2
            assert progress["completed"] == 1
            assert progress["in_progress"] == 1
            assert progress["completion_percentage"] == 50

    @pytest.mark.asyncio
    async def test_get_subtask_summaries_missing_parent_task_id(self, mock_request):
        """Test subtask summaries with missing parent_task_id."""
        response = await get_subtask_summaries(mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        response_data = json.loads(response.body.decode())
        assert response_data["error"] == "parent_task_id is required"

    @pytest.mark.asyncio
    async def test_get_task_context_summary_success(self, mock_request):
        """Test successful task context summary retrieval."""
        mock_request.path_params = {"task_id": "task-123"}

        with patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory') as MockContextFactory:
            # Setup context facade
            mock_context_facade = Mock()
            mock_context_facade.get_context_summary.return_value = {
                "success": True,
                "has_context": True,
                "context_size": 1024,
                "last_updated": "2024-01-01T00:00:00Z"
            }
            
            mock_context_factory_instance = Mock()
            mock_context_factory_instance.create_facade.return_value = mock_context_facade
            MockContextFactory.return_value = mock_context_factory_instance

            response = await get_task_context_summary(mock_request)
            
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            assert response_data["has_context"] is True
            assert response_data["context_size"] == 1024
            assert response_data["last_updated"] == "2024-01-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_get_task_context_summary_missing_task_id(self, mock_request):
        """Test context summary with missing task_id."""
        response = await get_task_context_summary(mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        response_data = json.loads(response.body.decode())
        assert response_data["error"] == "task_id is required"

    @pytest.mark.asyncio
    async def test_get_task_context_summary_no_context(self, mock_request):
        """Test context summary when no context exists."""
        mock_request.path_params = {"task_id": "task-123"}

        with patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory') as MockContextFactory:
            # Setup context facade to return failure
            mock_context_facade = Mock()
            mock_context_facade.get_context_summary.return_value = {
                "success": False,
                "error": "Context not found"
            }
            
            mock_context_factory_instance = Mock()
            mock_context_factory_instance.create_facade.return_value = mock_context_facade
            MockContextFactory.return_value = mock_context_factory_instance

            response = await get_task_context_summary(mock_request)
            
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            assert response_data["has_context"] is False
            assert "Context not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_performance_metrics_redis_enabled(self, mock_request):
        """Test performance metrics when Redis cache is enabled."""
        with patch('fastmcp.server.routes.task_summary_routes.REDIS_CACHE_ENABLED', True), \
             patch('fastmcp.server.routes.task_summary_routes.cache_metrics') as mock_cache_metrics:

            mock_cache_metrics.stats = {
                "hit_rate": "75.5%",
                "total_hits": 150,
                "total_misses": 50,
                "cache_size": "2.5MB"
            }

            response = await get_performance_metrics(mock_request)
            
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            
            assert response_data["cache_status"] == "enabled"
            assert response_data["cache_metrics"]["hit_rate"] == "75.5%"
            assert response_data["redis_cache"]["enabled"] is True
            assert "task_summaries" in response_data["endpoints"]
            assert len(response_data["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_get_performance_metrics_redis_disabled(self, mock_request):
        """Test performance metrics when Redis cache is disabled."""
        with patch('fastmcp.server.routes.task_summary_routes.REDIS_CACHE_ENABLED', False):
            response = await get_performance_metrics(mock_request)
            
            assert isinstance(response, JSONResponse)
            response_data = json.loads(response.body.decode())
            
            assert response_data["cache_status"] == "disabled"
            assert response_data["cache_metrics"] == {}
            assert response_data["redis_cache"]["enabled"] is False
            
            # Check that hit rate is N/A for all endpoints
            for endpoint in response_data["endpoints"].values():
                assert endpoint["cache_hit_rate"] == "N/A"

    def test_task_summary_routes_definition(self):
        """Test that all expected routes are properly defined."""
        expected_routes = [
            ("/api/tasks/summaries", "POST"),
            ("/api/tasks/{task_id:str}", "GET"),
            ("/api/subtasks/summaries", "POST"),
            ("/api/tasks/{task_id:str}/context/summary", "GET"),
            ("/api/performance/metrics", "GET")
        ]
        
        for expected_path, expected_method in expected_routes:
            found = False
            for route in task_summary_routes:
                if isinstance(route, Route):
                    if route.path == expected_path and expected_method in route.methods:
                        found = True
                        break
            assert found, f"Route {expected_method} {expected_path} not found in task_summary_routes"

    def test_route_endpoints_mapping(self):
        """Test that routes are mapped to correct endpoint functions."""
        route_mappings = {
            "/api/tasks/summaries": get_task_summaries,
            "/api/tasks/{task_id:str}": get_full_task,
            "/api/subtasks/summaries": get_subtask_summaries,
            "/api/tasks/{task_id:str}/context/summary": get_task_context_summary,
            "/api/performance/metrics": get_performance_metrics
        }
        
        for route in task_summary_routes:
            if isinstance(route, Route) and route.path in route_mappings:
                expected_endpoint = route_mappings[route.path]
                assert route.endpoint == expected_endpoint


class TestPaginationLogic:
    """Test pagination logic in task summaries."""

    @pytest.mark.asyncio
    async def test_pagination_has_more_true(self, mock_request):
        """Test pagination when there are more results available."""
        mock_request.body = AsyncMock(return_value=json.dumps({
            "git_branch_id": "branch-123",
            "page": 1,
            "limit": 10
        }).encode())

        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup task facade - total count 25, but returning only 10
            mock_task_facade = Mock()
            mock_task_facade.count_tasks.return_value = {"success": True, "count": 25}
            mock_task_facade.list_tasks_summary.return_value = {
                "success": True,
                "tasks": [{"id": f"task-{i}", "title": f"Task {i}", "status": "todo", 
                          "priority": "medium", "subtasks": [], "assignees": [], 
                          "dependencies": None} for i in range(10)]
            }
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            response = await get_task_summaries(mock_request)
            
            response_data = json.loads(response.body.decode())
            assert response_data["total"] == 25
            assert response_data["page"] == 1
            assert response_data["limit"] == 10
            assert response_data["has_more"] is True  # (0 + 10) < 25

    @pytest.mark.asyncio
    async def test_pagination_has_more_false(self, mock_request):
        """Test pagination when no more results available."""
        mock_request.body = AsyncMock(return_value=json.dumps({
            "git_branch_id": "branch-123",
            "page": 2,
            "limit": 10
        }).encode())

        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "user-123"

            # Setup task facade - total count 15, page 2 with limit 10
            mock_task_facade = Mock()
            mock_task_facade.count_tasks.return_value = {"success": True, "count": 15}
            mock_task_facade.list_tasks_summary.return_value = {
                "success": True,
                "tasks": [{"id": f"task-{i}", "title": f"Task {i}", "status": "todo", 
                          "priority": "medium", "subtasks": [], "assignees": [], 
                          "dependencies": None} for i in range(5)]  # Only 5 results on page 2
            }
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            response = await get_task_summaries(mock_request)
            
            response_data = json.loads(response.body.decode())
            assert response_data["total"] == 15
            assert response_data["page"] == 2
            assert response_data["limit"] == 10
            assert response_data["has_more"] is False  # (10 + 10) >= 15


class TestAuthConfigIntegration:
    """Test auth configuration integration."""

    @pytest.mark.asyncio
    async def test_auth_config_default_user_allowed(self, mock_request_with_body):
        """Test when default user is allowed."""
        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = True
            MockAuthConfig.get_fallback_user_id.return_value = "default-user-123"

            mock_task_facade = Mock()
            mock_task_facade.count_tasks.return_value = {"success": True, "count": 0}
            mock_task_facade.list_tasks_summary.return_value = {"success": True, "tasks": []}
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            await get_task_summaries(mock_request_with_body)
            
            # Verify auth config was called
            MockAuthConfig.is_default_user_allowed.assert_called_once()
            MockAuthConfig.get_fallback_user_id.assert_called()
            
            # Verify facade was created with fallback user
            mock_task_factory_instance.create_task_facade.assert_called_with(
                "default_project", "branch-123", "default-user-123"
            )

    @pytest.mark.asyncio
    async def test_auth_config_fallback_when_not_allowed(self, mock_request_with_body):
        """Test fallback behavior when default user is not allowed."""
        with patch('fastmcp.server.routes.task_summary_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.TaskFacadeFactory') as MockTaskFactory, \
             patch('fastmcp.server.routes.task_summary_routes.UnifiedContextFacadeFactory'), \
             patch('fastmcp.server.routes.task_summary_routes.AuthConfig') as MockAuthConfig:

            MockAuthConfig.is_default_user_allowed.return_value = False
            MockAuthConfig.get_fallback_user_id.return_value = "fallback-user-456"

            mock_task_facade = Mock()
            mock_task_facade.count_tasks.return_value = {"success": True, "count": 0}
            mock_task_facade.list_tasks_summary.return_value = {"success": True, "tasks": []}
            
            mock_task_factory_instance = Mock()
            mock_task_factory_instance.create_task_facade.return_value = mock_task_facade
            MockTaskFactory.return_value = mock_task_factory_instance

            await get_task_summaries(mock_request_with_body)
            
            # Should still use fallback user despite not being "allowed"
            mock_task_factory_instance.create_task_facade.assert_called_with(
                "default_project", "branch-123", "fallback-user-456"
            )