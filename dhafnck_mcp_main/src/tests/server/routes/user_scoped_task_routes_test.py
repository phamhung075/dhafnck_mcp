"""Comprehensive test suite for user-scoped task routes with authentication and data isolation"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from server.routes.user_scoped_task_routes import router, get_current_user
from domain.entities import Task, User
from datetime import datetime
import uuid
import json
from typing import Dict, List, Optional


@pytest.fixture
def test_app():
    """Create test FastAPI app with user-scoped task routes"""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "Test Task",
        "description": "Test task description",
        "project_id": str(uuid.uuid4()),
        "git_branch_id": str(uuid.uuid4()),
        "priority": "high",
        "status": "todo",
        "tags": ["test", "sample"],
        "estimated_hours": 8
    }


@pytest.fixture
def sample_task(sample_task_data, mock_user):
    """Sample task entity"""
    return Task(
        id=str(uuid.uuid4()),
        user_id=mock_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **sample_task_data
    )


@pytest.mark.unit
class TestUserScopedTaskRoutesAuthentication:
    """Test authentication handling for user-scoped task routes"""
    
    def test_all_routes_require_authentication(self, test_client):
        """Test that all task routes require authentication"""
        # Test endpoints without Authorization header
        endpoints = [
            ("GET", "/api/v1/tasks"),
            ("POST", "/api/v1/tasks"),
            ("GET", f"/api/v1/tasks/{uuid.uuid4()}"),
            ("PUT", f"/api/v1/tasks/{uuid.uuid4()}"),
            ("DELETE", f"/api/parts/{uuid.uuid4()}"),
            ("POST", f"/api/v1/tasks/{uuid.uuid4()}/complete"),
            ("GET", "/api/v1/tasks/search"),
            ("GET", "/api/v1/tasks/next"),
            ("GET", "/api/v1/tasks/stats"),
            ("POST", f"/api/v1/tasks/{uuid.uuid4()}/assign"),
            ("POST", f"/api/v1/tasks/{uuid.uuid4()}/unassign"),
            ("GET", f"/api/v1/tasks/{uuid.uuid4()}/history"),
            ("POST", f"/api/v1/tasks/{uuid.uuid4()}/comment"),
            ("POST", "/api/v1/tasks/bulk"),
            ("DELETE", "/api/v1/tasks/bulk")
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = test_client.get(endpoint)
            elif method == "POST":
                response = test_client.post(endpoint, json={})
            elif method == "PUT":
                response = test_client.put(endpoint, json={})
            elif method == "DELETE":
                response = test_client.delete(endpoint)
            
            assert response.status_code == 401, f"{method} {endpoint} should require authentication"
            assert "Unauthorized" in response.json().get("detail", "")
    
    def test_invalid_token_returns_401(self, test_client):
        """Test that invalid tokens return 401"""
        with patch('server.routes.user_scoped_task_routes.get_current_user') as mock_get_user:
            mock_get_user.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            response = test_client.get(
                "/api/v1/tasks",
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            assert response.status_code == 401
            assert "Invalid token" in response.json()["detail"]
    
    def test_expired_token_returns_401(self, test_client):
        """Test that expired tokens return 401"""
        with patch('server.routes.user_scoped_task_routes.get_current_user') as mock_get_user:
            mock_get_user.side_effect = HTTPException(status_code=401, detail="Token expired")
            
            response = test_client.get(
                "/api/v1/tasks",
                headers={"Authorization": "Bearer expired_token"}
            )
            
            assert response.status_code == 401
            assert "Token expired" in response.json()["detail"]
    
    def test_malformed_authorization_header_returns_401(self, test_client):
        """Test malformed authorization headers"""
        # Test without Bearer prefix
        response = test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": "invalid_format_token"}
        )
        assert response.status_code == 401
        
        # Test empty Bearer
        response = test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer "}
        )
        assert response.status_code == 401
        
        # Test multiple Bearer prefixes
        response = test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": "Bearer Bearer token"}
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestUserScopedTaskRoutesDataIsolation:
    """Test data isolation for user-scoped tasks"""
    
    def test_user_can_only_see_own_tasks(self, test_client, mock_user):
        """Test that users can only see their own tasks"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Mock tasks from different users
                user1_tasks = [
                    {"id": str(uuid.uuid4()), "user_id": mock_user.id, "title": "User 1 Task 1"},
                    {"id": str(uuid.uuid4()), "user_id": mock_user.id, "title": "User 1 Task 2"}
                ]
                user2_tasks = [
                    {"id": str(uuid.uuid4()), "user_id": "other_user_id", "title": "User 2 Task"}
                ]
                
                # Facade should only return current user's tasks
                mock_facade.list_tasks.return_value = user1_tasks
                
                response = test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()["data"]
                assert len(data) == 2
                assert all(task["user_id"] == mock_user.id for task in data)
                
                # Verify facade was called with correct user_id
                mock_facade.list_tasks.assert_called_once()
                call_args = mock_facade.list_tasks.call_args
                assert call_args[1]["user_id"] == mock_user.id
    
    def test_user_cannot_access_other_users_task(self, test_client, mock_user):
        """Test that users cannot access tasks from other users"""
        other_user_task_id = str(uuid.uuid4())
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Simulate task belongs to different user
                mock_facade.get_task.return_value = None  # Task not found for current user
                
                response = test_client.get(
                    f"/api/v1/tasks/{other_user_task_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 404
                assert "not found" in response.json()["message"].lower()
                
                # Verify facade was called with user_id filter
                mock_facade.get_task.assert_called_once()
                call_args = mock_facade.get_task.call_args
                assert call_args[1]["user_id"] == mock_user.id
    
    def test_user_cannot_update_other_users_task(self, test_client, mock_user):
        """Test that users cannot update tasks from other users"""
        other_user_task_id = str(uuid.uuid4())
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = None  # Task not found for current user
                
                response = test_client.put(
                    f"/api/v1/tasks/{other_user_task_id}",
                    json={"title": "Malicious update"},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 404
                assert "not found" in response.json()["message"].lower()
                mock_facade.update_task.assert_not_called()
    
    def test_user_cannot_delete_other_users_task(self, test_client, mock_user):
        """Test that users cannot delete tasks from other users"""
        other_user_task_id = str(uuid.uuid4())
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = None  # Task not found for current user
                
                response = test_client.delete(
                    f"/api/v1/tasks/{other_user_task_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 404
                assert "not found" in response.json()["message"].lower()
                mock_facade.delete_task.assert_not_called()
    
    def test_created_tasks_are_assigned_to_current_user(self, test_client, mock_user, sample_task_data):
        """Test that newly created tasks are assigned to the current user"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                created_task = {
                    "id": str(uuid.uuid4()),
                    "user_id": mock_user.id,
                    **sample_task_data
                }
                mock_facade.create_task.return_value = created_task
                
                response = test_client.post(
                    "/api/v1/tasks",
                    json=sample_task_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 201
                assert response.json()["data"]["user_id"] == mock_user.id
                
                # Verify facade was called with user_id
                mock_facade.create_task.assert_called_once()
                call_args = mock_facade.create_task.call_args
                assert call_args[0][0]["user_id"] == mock_user.id


@pytest.mark.unit
class TestUserScopedTaskRoutesCRUD:
    """Test CRUD operations for user-scoped tasks"""
    
    def test_create_task_success(self, test_client, mock_user, sample_task_data, sample_task):
        """Test successful task creation"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.create_task.return_value = sample_task.__dict__
                
                response = test_client.post(
                    "/api/v1/tasks",
                    json=sample_task_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 201
                response_data = response.json()
                assert response_data["status"] == "success"
                assert response_data["data"]["title"] == sample_task_data["title"]
                assert response_data["data"]["user_id"] == mock_user.id
    
    def test_create_task_with_minimal_data(self, test_client, mock_user):
        """Test task creation with only required fields"""
        minimal_data = {
            "title": "Minimal Task"
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                created_task = {
                    "id": str(uuid.uuid4()),
                    "user_id": mock_user.id,
                    "title": minimal_data["title"],
                    "status": "todo",
                    "priority": "medium"
                }
                mock_facade.create_task.return_value = created_task
                
                response = test_client.post(
                    "/api/v1/tasks",
                    json=minimal_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 201
                assert response.json()["data"]["title"] == minimal_data["title"]
    
    def test_create_task_validation_error(self, test_client, mock_user):
        """Test task creation with validation errors"""
        invalid_data = {
            "title": "",  # Empty title
            "priority": "invalid_priority",  # Invalid priority
            "estimated_hours": -5  # Negative hours
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.create_task.side_effect = ValueError("Validation failed: title cannot be empty")
                
                response = test_client.post(
                    "/api/v1/tasks",
                    json=invalid_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 400
                assert "Validation failed" in response.json()["message"]
    
    def test_get_task_success(self, test_client, mock_user, sample_task):
        """Test successful task retrieval"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                
                response = test_client.get(
                    f"/api/v1/tasks/{sample_task.id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["id"] == sample_task.id
                assert response.json()["data"]["title"] == sample_task.title
    
    def test_update_task_success(self, test_client, mock_user, sample_task):
        """Test successful task update"""
        update_data = {
            "title": "Updated Task Title",
            "status": "in_progress",
            "progress": 50
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # First check if task exists and belongs to user
                mock_facade.get_task.return_value = sample_task.__dict__
                
                updated_task = {**sample_task.__dict__, **update_data}
                mock_facade.update_task.return_value = updated_task
                
                response = test_client.put(
                    f"/api/v1/tasks/{sample_task.id}",
                    json=update_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["title"] == update_data["title"]
                assert response.json()["data"]["status"] == update_data["status"]
    
    def test_update_task_partial_data(self, test_client, mock_user, sample_task):
        """Test task update with partial data"""
        partial_update = {
            "status": "completed"
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                
                updated_task = {**sample_task.__dict__, **partial_update}
                mock_facade.update_task.return_value = updated_task
                
                response = test_client.put(
                    f"/api/v1/tasks/{sample_task.id}",
                    json=partial_update,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["status"] == "completed"
                assert response.json()["data"]["title"] == sample_task.title  # Unchanged
    
    def test_delete_task_success(self, test_client, mock_user, sample_task):
        """Test successful task deletion"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                mock_facade.delete_task.return_value = True
                
                response = test_client.delete(
                    f"/api/v1/tasks/{sample_task.id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["status"] == "success"
                assert "deleted successfully" in response.json()["message"]
    
    def test_delete_nonexistent_task(self, test_client, mock_user):
        """Test deleting non-existent task"""
        task_id = str(uuid.uuid4())
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = None
                
                response = test_client.delete(
                    f"/api/v1/tasks/{task_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 404
                assert "not found" in response.json()["message"].lower()


@pytest.mark.unit
class TestUserScopedTaskRoutesAdvanced:
    """Test advanced features of user-scoped task routes"""
    
    def test_list_tasks_with_filters(self, test_client, mock_user):
        """Test listing tasks with various filters"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_tasks = [
                    {"id": str(uuid.uuid4()), "title": "Task 1", "status": "todo", "priority": "high"},
                    {"id": str(uuid.uuid4()), "title": "Task 2", "status": "in_progress", "priority": "high"}
                ]
                mock_facade.list_tasks.return_value = mock_tasks
                
                response = test_client.get(
                    "/api/v1/tasks",
                    params={
                        "status": "todo,in_progress",
                        "priority": "high",
                        "project_id": str(uuid.uuid4()),
                        "limit": 20,
                        "offset": 0
                    },
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert len(response.json()["data"]) == 2
                
                # Verify filters were passed to facade
                call_args = mock_facade.list_tasks.call_args[1]
                assert call_args["user_id"] == mock_user.id
                assert "status" in call_args
                assert "priority" in call_args
    
    def test_search_tasks(self, test_client, mock_user):
        """Test task search functionality"""
        search_query = "important feature"
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                search_results = [
                    {"id": str(uuid.uuid4()), "title": "Implement important feature", "score": 0.95},
                    {"id": str(uuid.uuid4()), "title": "Important bug fix", "score": 0.85}
                ]
                mock_facade.search_tasks.return_value = search_results
                
                response = test_client.get(
                    "/api/v1/tasks/search",
                    params={"q": search_query, "limit": 10},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert len(response.json()["data"]) == 2
                assert all("important" in result["title"].lower() for result in response.json()["data"])
    
    def test_complete_task_with_summary(self, test_client, mock_user, sample_task):
        """Test task completion with summary"""
        completion_data = {
            "completion_summary": "Successfully implemented the feature with unit tests",
            "testing_notes": "All tests passing, coverage at 95%",
            "time_spent": 6.5
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                
                completed_task = {
                    **sample_task.__dict__,
                    "status": "completed",
                    "completion_summary": completion_data["completion_summary"],
                    "completed_at": datetime.utcnow().isoformat()
                }
                mock_facade.complete_task.return_value = completed_task
                
                response = test_client.post(
                    f"/api/v1/tasks/{sample_task.id}/complete",
                    json=completion_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["status"] == "completed"
                assert response.json()["data"]["completion_summary"] == completion_data["completion_summary"]
    
    def test_get_next_task_by_priority(self, test_client, mock_user):
        """Test getting next task based on priority"""
        git_branch_id = str(uuid.uuid4())
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                next_task = {
                    "id": str(uuid.uuid4()),
                    "title": "Critical Bug Fix",
                    "priority": "critical",
                    "status": "todo"
                }
                mock_facade.get_next_task.return_value = next_task
                
                response = test_client.get(
                    "/api/v1/tasks/next",
                    params={"git_branch_id": git_branch_id},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["priority"] == "critical"
    
    def test_get_task_statistics(self, test_client, mock_user):
        """Test getting task statistics"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                stats = {
                    "total_tasks": 50,
                    "completed_tasks": 30,
                    "in_progress_tasks": 10,
                    "todo_tasks": 10,
                    "completion_rate": 0.6,
                    "average_completion_time": 4.5,
                    "tasks_by_priority": {
                        "critical": 2,
                        "high": 15,
                        "medium": 20,
                        "low": 13
                    }
                }
                mock_facade.get_task_statistics.return_value = stats
                
                response = test_client.get(
                    "/api/v1/tasks/stats",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["total_tasks"] == 50
                assert response.json()["data"]["completion_rate"] == 0.6
    
    def test_assign_task_to_user(self, test_client, mock_user, sample_task):
        """Test assigning task to another user (if permitted)"""
        assignee_id = str(uuid.uuid4())
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                
                assigned_task = {
                    **sample_task.__dict__,
                    "assigned_to": assignee_id,
                    "assigned_by": mock_user.id,
                    "assigned_at": datetime.utcnow().isoformat()
                }
                mock_facade.assign_task.return_value = assigned_task
                
                response = test_client.post(
                    f"/api/v1/tasks/{sample_task.id}/assign",
                    json={"assignee_id": assignee_id},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["assigned_to"] == assignee_id
    
    def test_add_task_comment(self, test_client, mock_user, sample_task):
        """Test adding comment to task"""
        comment_data = {
            "content": "This task needs more clarification on requirements",
            "attachments": ["diagram.png"]
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                
                comment = {
                    "id": str(uuid.uuid4()),
                    "task_id": sample_task.id,
                    "user_id": mock_user.id,
                    "content": comment_data["content"],
                    "created_at": datetime.utcnow().isoformat()
                }
                mock_facade.add_task_comment.return_value = comment
                
                response = test_client.post(
                    f"/api/v1/tasks/{sample_task.id}/comment",
                    json=comment_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 201
                assert response.json()["data"]["content"] == comment_data["content"]
    
    def test_get_task_history(self, test_client, mock_user, sample_task):
        """Test getting task history/audit log"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.get_task.return_value = sample_task.__dict__
                
                history = [
                    {
                        "id": str(uuid.uuid4()),
                        "action": "created",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": mock_user.id,
                        "changes": {"status": "todo"}
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "action": "updated",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": mock_user.id,
                        "changes": {"status": {"from": "todo", "to": "in_progress"}}
                    }
                ]
                mock_facade.get_task_history.return_value = history
                
                response = test_client.get(
                    f"/api/v1/tasks/{sample_task.id}/history",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert len(response.json()["data"]) == 2
                assert response.json()["data"][0]["action"] == "created"


@pytest.mark.unit
class TestUserScopedTaskRoutesBulkOperations:
    """Test bulk operations for user-scoped tasks"""
    
    def test_bulk_create_tasks(self, test_client, mock_user):
        """Test creating multiple tasks at once"""
        bulk_data = {
            "tasks": [
                {"title": "Task 1", "priority": "high"},
                {"title": "Task 2", "priority": "medium"},
                {"title": "Task 3", "priority": "low"}
            ],
            "project_id": str(uuid.uuid4())
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                created_tasks = [
                    {"id": str(uuid.uuid4()), **task, "user_id": mock_user.id}
                    for task in bulk_data["tasks"]
                ]
                mock_facade.bulk_create_tasks.return_value = created_tasks
                
                response = test_client.post(
                    "/api/v1/tasks/bulk",
                    json=bulk_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 201
                assert len(response.json()["data"]) == 3
                assert all(task["user_id"] == mock_user.id for task in response.json()["data"])
    
    def test_bulk_update_tasks(self, test_client, mock_user):
        """Test updating multiple tasks at once"""
        task_ids = [str(uuid.uuid4()) for _ in range(3)]
        bulk_update = {
            "task_ids": task_ids,
            "updates": {
                "status": "in_progress",
                "assigned_to": str(uuid.uuid4())
            }
        }
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Mock checking ownership of all tasks
                mock_facade.verify_task_ownership.return_value = True
                
                updated_tasks = [
                    {"id": task_id, **bulk_update["updates"]}
                    for task_id in task_ids
                ]
                mock_facade.bulk_update_tasks.return_value = updated_tasks
                
                response = test_client.put(
                    "/api/v1/tasks/bulk",
                    json=bulk_update,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert len(response.json()["data"]) == 3
                assert all(task["status"] == "in_progress" for task in response.json()["data"])
    
    def test_bulk_delete_tasks(self, test_client, mock_user):
        """Test deleting multiple tasks at once"""
        task_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Mock checking ownership of all tasks
                mock_facade.verify_task_ownership.return_value = True
                mock_facade.bulk_delete_tasks.return_value = {"deleted": 3, "failed": 0}
                
                response = test_client.delete(
                    "/api/v1/tasks/bulk",
                    json={"task_ids": task_ids},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert response.json()["data"]["deleted"] == 3
                assert response.json()["data"]["failed"] == 0
    
    def test_bulk_operations_partial_failure(self, test_client, mock_user):
        """Test bulk operations with partial failures"""
        task_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Some tasks don't belong to user
                mock_facade.verify_task_ownership.side_effect = [True, True, False, True, False]
                
                response = test_client.delete(
                    "/api/v1/tasks/bulk",
                    json={"task_ids": task_ids},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 207  # Multi-status
                assert "partial success" in response.json()["message"].lower()


@pytest.mark.unit
class TestUserScopedTaskRoutesErrorHandling:
    """Test error handling for user-scoped task routes"""
    
    def test_invalid_uuid_format(self, test_client, mock_user):
        """Test handling of invalid UUID formats"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            response = test_client.get(
                "/api/v1/tasks/invalid-uuid",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 400
            assert "Invalid task ID format" in response.json()["message"]
    
    def test_malformed_json_request(self, test_client, mock_user):
        """Test handling of malformed JSON"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            response = test_client.post(
                "/api/v1/tasks",
                data="{'invalid': json}",  # Malformed JSON
                headers={
                    "Authorization": "Bearer test_token",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 400
            assert "Invalid JSON" in response.json()["detail"]
    
    def test_database_connection_error(self, test_client, mock_user):
        """Test handling of database connection errors"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.list_tasks.side_effect = ConnectionError("Database unreachable")
                
                response = test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 503  # Service Unavailable
                assert "service temporarily unavailable" in response.json()["message"].lower()
    
    def test_request_timeout_handling(self, test_client, mock_user):
        """Test handling of request timeouts"""
        import asyncio
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.list_tasks.side_effect = asyncio.TimeoutError("Request timeout")
                
                response = test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 504  # Gateway Timeout
                assert "request timeout" in response.json()["message"].lower()
    
    def test_rate_limiting_error(self, test_client, mock_user):
        """Test rate limiting error responses"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.check_rate_limit') as mock_rate_limit:
                mock_rate_limit.side_effect = HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": "60"}
                )
                
                response = test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 429
                assert "Rate limit exceeded" in response.json()["detail"]
                assert response.headers.get("Retry-After") == "60"
    
    def test_internal_server_error_fallback(self, test_client, mock_user):
        """Test generic internal server error handling"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.list_tasks.side_effect = Exception("Unexpected error")
                
                response = test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 500
                assert "internal server error" in response.json()["message"].lower()
                assert "error_id" in response.json()  # Should include error ID for tracking


@pytest.mark.unit
class TestUserScopedTaskRoutesValidation:
    """Test input validation for user-scoped task routes"""
    
    def test_task_title_validation(self, test_client, mock_user):
        """Test task title validation rules"""
        test_cases = [
            ("", 400, "Title cannot be empty"),
            ("a" * 256, 400, "Title too long"),
            ("Valid Title", 201, None),
            ("<script>alert('xss')</script>", 201, None),  # Should be escaped, not rejected
        ]
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                for title, expected_status, expected_error in test_cases:
                    if expected_status == 201:
                        mock_facade.create_task.return_value = {
                            "id": str(uuid.uuid4()),
                            "title": title,
                            "user_id": mock_user.id
                        }
                    else:
                        mock_facade.create_task.side_effect = ValueError(expected_error)
                    
                    response = test_client.post(
                        "/api/v1/tasks",
                        json={"title": title},
                        headers={"Authorization": "Bearer test_token"}
                    )
                    
                    assert response.status_code == expected_status
                    if expected_error:
                        assert expected_error in response.json()["message"]
    
    def test_task_priority_validation(self, test_client, mock_user):
        """Test task priority validation"""
        valid_priorities = ["critical", "high", "medium", "low"]
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Test valid priorities
                for priority in valid_priorities:
                    mock_facade.create_task.return_value = {
                        "id": str(uuid.uuid4()),
                        "title": "Test",
                        "priority": priority,
                        "user_id": mock_user.id
                    }
                    
                    response = test_client.post(
                        "/api/v1/tasks",
                        json={"title": "Test", "priority": priority},
                        headers={"Authorization": "Bearer test_token"}
                    )
                    assert response.status_code == 201
                
                # Test invalid priority
                mock_facade.create_task.side_effect = ValueError("Invalid priority: urgent")
                response = test_client.post(
                    "/api/v1/tasks",
                    json={"title": "Test", "priority": "urgent"},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 400
                assert "Invalid priority" in response.json()["message"]
    
    def test_task_date_validation(self, test_client, mock_user):
        """Test date field validation"""
        test_cases = [
            {"due_date": "2024-12-31", "expected": 201},
            {"due_date": "invalid-date", "expected": 400},
            {"due_date": "2020-01-01", "expected": 400},  # Past date
            {"start_date": "2024-12-31", "end_date": "2024-12-30", "expected": 400}  # End before start
        ]
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                for test_case in test_cases:
                    expected_status = test_case.pop("expected")
                    task_data = {"title": "Test Task", **test_case}
                    
                    if expected_status == 201:
                        mock_facade.create_task.return_value = {
                            "id": str(uuid.uuid4()),
                            **task_data,
                            "user_id": mock_user.id
                        }
                    else:
                        mock_facade.create_task.side_effect = ValueError("Invalid date")
                    
                    response = test_client.post(
                        "/api/v1/tasks",
                        json=task_data,
                        headers={"Authorization": "Bearer test_token"}
                    )
                    
                    assert response.status_code == expected_status
    
    def test_pagination_validation(self, test_client, mock_user):
        """Test pagination parameter validation"""
        test_cases = [
            {"limit": -1, "expected": 400},
            {"limit": 0, "expected": 400},
            {"limit": 1001, "expected": 400},  # Assuming max is 1000
            {"offset": -1, "expected": 400},
            {"limit": 50, "offset": 0, "expected": 200},
        ]
        
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                mock_facade.list_tasks.return_value = []
                
                for test_case in test_cases:
                    expected_status = test_case.pop("expected")
                    
                    response = test_client.get(
                        "/api/v1/tasks",
                        params=test_case,
                        headers={"Authorization": "Bearer test_token"}
                    )
                    
                    assert response.status_code == expected_status


@pytest.mark.integration
class TestUserScopedTaskRoutesIntegration:
    """Integration tests for user-scoped task routes"""
    
    def test_complete_task_workflow(self, test_client, mock_user):
        """Test complete task lifecycle from creation to completion"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Step 1: Create task
                task_data = {
                    "title": "Complete workflow test",
                    "description": "Testing full lifecycle",
                    "priority": "high"
                }
                
                task_id = str(uuid.uuid4())
                created_task = {
                    "id": task_id,
                    "user_id": mock_user.id,
                    "status": "todo",
                    **task_data
                }
                mock_facade.create_task.return_value = created_task
                
                create_response = test_client.post(
                    "/api/v1/tasks",
                    json=task_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                assert create_response.status_code == 201
                
                # Step 2: Update to in-progress
                mock_facade.get_task.return_value = created_task
                in_progress_task = {**created_task, "status": "in_progress"}
                mock_facade.update_task.return_value = in_progress_task
                
                update_response = test_client.put(
                    f"/api/v1/tasks/{task_id}",
                    json={"status": "in_progress"},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert update_response.status_code == 200
                assert update_response.json()["data"]["status"] == "in_progress"
                
                # Step 3: Add comment
                comment = {
                    "id": str(uuid.uuid4()),
                    "content": "Working on implementation"
                }
                mock_facade.add_task_comment.return_value = comment
                
                comment_response = test_client.post(
                    f"/api/v1/tasks/{task_id}/comment",
                    json={"content": "Working on implementation"},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert comment_response.status_code == 201
                
                # Step 4: Complete task
                mock_facade.get_task.return_value = in_progress_task
                completed_task = {
                    **in_progress_task,
                    "status": "completed",
                    "completion_summary": "All done"
                }
                mock_facade.complete_task.return_value = completed_task
                
                complete_response = test_client.post(
                    f"/api/v1/tasks/{task_id}/complete",
                    json={"completion_summary": "All done"},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert complete_response.status_code == 200
                assert complete_response.json()["data"]["status"] == "completed"
    
    def test_concurrent_user_isolation(self, test_client):
        """Test that concurrent users have properly isolated data"""
        user1 = User(id=str(uuid.uuid4()), email="user1@example.com", username="user1")
        user2 = User(id=str(uuid.uuid4()), email="user2@example.com", username="user2")
        
        with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            # User 1 creates a task
            with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=user1):
                task1_data = {"title": "User 1 Task"}
                task1 = {
                    "id": str(uuid.uuid4()),
                    "user_id": user1.id,
                    **task1_data
                }
                mock_facade.create_task.return_value = task1
                
                response1 = test_client.post(
                    "/api/v1/tasks",
                    json=task1_data,
                    headers={"Authorization": "Bearer user1_token"}
                )
                assert response1.status_code == 201
                task1_id = response1.json()["data"]["id"]
            
            # User 2 tries to access User 1's task
            with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=user2):
                mock_facade.get_task.return_value = None  # Not found for user2
                
                response2 = test_client.get(
                    f"/api/v1/tasks/{task1_id}",
                    headers={"Authorization": "Bearer user2_token"}
                )
                assert response2.status_code == 404
            
            # User 2 lists tasks and doesn't see User 1's task
            with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=user2):
                mock_facade.list_tasks.return_value = []  # Empty for user2
                
                response3 = test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": "Bearer user2_token"}
                )
                assert response3.status_code == 200
                assert len(response3.json()["data"]) == 0
    
    def test_task_search_with_permissions(self, test_client, mock_user):
        """Test that search only returns user's own tasks"""
        with patch('server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('server.routes.user_scoped_task_routes.task_facade') as mock_facade:
                # Mock search results - should be filtered by user
                user_tasks = [
                    {"id": str(uuid.uuid4()), "title": "User Task 1", "user_id": mock_user.id},
                    {"id": str(uuid.uuid4()), "title": "User Task 2", "user_id": mock_user.id}
                ]
                mock_facade.search_tasks.return_value = user_tasks
                
                response = test_client.get(
                    "/api/v1/tasks/search",
                    params={"q": "task"},
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                assert len(response.json()["data"]) == 2
                assert all(task["user_id"] == mock_user.id for task in response.json()["data"])
                
                # Verify search was called with user_id filter
                mock_facade.search_tasks.assert_called_once()
                call_args = mock_facade.search_tasks.call_args
                assert call_args[1]["user_id"] == mock_user.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])