"""Test suite for user-scoped task routes"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastmcp.server.routes.user_scoped_task_routes import router
import uuid
import json


@pytest.fixture
def test_app():
    """Create test FastAPI app"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.mark.unit
class TestUserScopedTaskRoutes:
    """Test user-scoped task routes"""
    
    def test_create_task_endpoint(self, test_client):
        """Test task creation endpoint"""
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "project_id": "proj123",
            "git_branch_id": "branch456",
            "priority": "high",
            "status": "todo"
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            expected_task = {
                "id": str(uuid.uuid4()),
                **task_data,
                "created_at": "2024-01-01T00:00:00Z"
            }
            mock_facade.create_task.return_value = expected_task
            
            response = test_client.post(
                "/tasks",
                json=task_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["title"] == task_data["title"]
        assert response_data["status"] == "success"
    
    def test_get_task_endpoint(self, test_client):
        """Test get task by ID endpoint"""
        task_id = str(uuid.uuid4())
        expected_task = {
            "id": task_id,
            "title": "Test Task",
            "description": "Test Description",
            "status": "todo"
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.get_task.return_value = expected_task
            
            response = test_client.get(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["id"] == task_id
        assert response_data["status"] == "success"
    
    def test_get_nonexistent_task_returns_404(self, test_client):
        """Test getting non-existent task returns 404"""
        task_id = str(uuid.uuid4())
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.get_task.return_value = None
            
            response = test_client.get(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "not found" in response_data["message"].lower()
    
    def test_update_task_endpoint(self, test_client):
        """Test task update endpoint"""
        task_id = str(uuid.uuid4())
        update_data = {
            "title": "Updated Task",
            "description": "Updated Description",
            "status": "in_progress"
        }
        
        expected_task = {
            "id": task_id,
            **update_data,
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.update_task.return_value = expected_task
            
            response = test_client.put(
                f"/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["title"] == update_data["title"]
        assert response_data["status"] == "success"
    
    def test_delete_task_endpoint(self, test_client):
        """Test task deletion endpoint"""
        task_id = str(uuid.uuid4())
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.delete_task.return_value = True
            
            response = test_client.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "deleted successfully" in response_data["message"]
    
    def test_list_tasks_endpoint(self, test_client):
        """Test list tasks endpoint with filters"""
        expected_tasks = [
            {
                "id": str(uuid.uuid4()),
                "title": "Task 1",
                "status": "todo",
                "priority": "high"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Task 2",
                "status": "todo",
                "priority": "medium"
            }
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.list_tasks.return_value = expected_tasks
            
            response = test_client.get(
                "/tasks",
                params={"status": "todo", "priority": "high"},
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert len(response_data["data"]) == 2
    
    def test_complete_task_endpoint(self, test_client):
        """Test task completion endpoint"""
        task_id = str(uuid.uuid4())
        completion_data = {
            "completion_summary": "Task completed successfully",
            "testing_notes": "All tests passed"
        }
        
        expected_task = {
            "id": task_id,
            "status": "completed",
            "completion_summary": completion_data["completion_summary"]
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.complete_task.return_value = expected_task
            
            response = test_client.post(
                f"/tasks/{task_id}/complete",
                json=completion_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["status"] == "completed"
        assert response_data["status"] == "success"
    
    def test_search_tasks_endpoint(self, test_client):
        """Test task search endpoint"""
        search_query = "test search"
        expected_results = [
            {"id": str(uuid.uuid4()), "title": "Test Task 1"},
            {"id": str(uuid.uuid4()), "title": "Another Test Task"}
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.search_tasks.return_value = expected_results
            
            response = test_client.get(
                "/tasks/search",
                params={"q": search_query},
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert len(response_data["data"]) == 2
    
    def test_get_next_task_endpoint(self, test_client):
        """Test get next task endpoint"""
        git_branch_id = str(uuid.uuid4())
        expected_task = {
            "id": str(uuid.uuid4()),
            "title": "Next Task",
            "priority": "high",
            "status": "todo"
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.get_next_task.return_value = expected_task
            
            response = test_client.get(
                "/tasks/next",
                params={"git_branch_id": git_branch_id},
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["title"] == "Next Task"
        assert response_data["status"] == "success"
    
    def test_endpoint_requires_authentication(self, test_client):
        """Test endpoints require authentication"""
        # Test without Authorization header
        response = test_client.get("/tasks")
        assert response.status_code == 401
        
        response = test_client.post("/tasks", json={"title": "Test"})
        assert response.status_code == 401
    
    def test_invalid_json_returns_400(self, test_client):
        """Test invalid JSON returns 400 error"""
        response = test_client.post(
            "/tasks",
            data="invalid json",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
    
    def test_validation_error_handling(self, test_client):
        """Test validation error handling"""
        invalid_task_data = {
            "title": "",  # Invalid empty title
            "description": "Test"
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.create_task.side_effect = ValueError("Title cannot be empty")
            
            response = test_client.post(
                "/tasks",
                json=invalid_task_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "Title cannot be empty" in response_data["message"]
    
    def test_internal_server_error_handling(self, test_client):
        """Test internal server error handling"""
        task_data = {
            "title": "Test Task",
            "description": "Test Description"
        }
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.create_task.side_effect = Exception("Database connection failed")
            
            response = test_client.post(
                "/tasks",
                json=task_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 500
        response_data = response.json()
        assert response_data["status"] == "error"


@pytest.mark.integration
class TestUserScopedTaskRoutesIntegration:
    """Integration tests for user-scoped task routes"""
    
    def test_full_task_crud_flow(self, test_client):
        """Test complete CRUD flow for tasks"""
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            # Create task
            create_data = {
                "title": "Integration Test Task",
                "description": "Test CRUD flow",
                "project_id": "proj123"
            }
            
            created_task = {
                "id": str(uuid.uuid4()),
                **create_data,
                "status": "todo"
            }
            mock_facade.create_task.return_value = created_task
            
            create_response = test_client.post(
                "/tasks",
                json=create_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert create_response.status_code == 201
            
            task_id = created_task["id"]
            
            # Read task
            mock_facade.get_task.return_value = created_task
            get_response = test_client.get(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer test_token"}
            )
            assert get_response.status_code == 200
            
            # Update task
            update_data = {"title": "Updated Task", "status": "in_progress"}
            updated_task = {**created_task, **update_data}
            mock_facade.update_task.return_value = updated_task
            
            update_response = test_client.put(
                f"/tasks/{task_id}",
                json=update_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert update_response.status_code == 200
            
            # Delete task
            mock_facade.delete_task.return_value = True
            delete_response = test_client.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer test_token"}
            )
            assert delete_response.status_code == 200
    
    def test_route_error_consistency(self, test_client):
        """Test consistent error response format across routes"""
        with patch('fastmcp.server.routes.user_scoped_task_routes.task_facade') as mock_facade:
            mock_facade.get_task.side_effect = Exception("Test error")
            
            response = test_client.get(
                f"/tasks/{uuid.uuid4()}",
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 500
        response_data = response.json()
        
        # Check error response structure
        assert "status" in response_data
        assert "message" in response_data
        assert response_data["status"] == "error"