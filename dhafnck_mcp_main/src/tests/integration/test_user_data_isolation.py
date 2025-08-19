"""
Integration Tests for User Data Isolation

This module tests that user-based data isolation is working correctly,
ensuring users can only access their own data.
"""

import pytest
import uuid
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastmcp.auth.application.services.auth_service import AuthService
from fastmcp.auth.infrastructure.repositories.user_repository import UserRepository
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import TaskRepository
from fastmcp.task_management.infrastructure.repositories.base_user_scoped_repository import (
    BaseUserScopedRepository,
    CrossUserAccessError
)


class TestUserDataIsolation:
    """Test suite for user data isolation functionality"""
    
    @pytest.fixture
    def test_users(self, db_session: Session) -> Dict[str, Dict[str, Any]]:
        """Create test users for isolation testing"""
        auth_service = AuthService(UserRepository(db_session))
        
        # Create two test users
        user1_data = {
            "email": f"user1_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "username": f"user1_{uuid.uuid4().hex[:8]}"
        }
        
        user2_data = {
            "email": f"user2_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass456!",
            "username": f"user2_{uuid.uuid4().hex[:8]}"
        }
        
        # Register users
        user1_result = auth_service.register(
            email=user1_data["email"],
            password=user1_data["password"],
            username=user1_data["username"]
        )
        
        user2_result = auth_service.register(
            email=user2_data["email"],
            password=user2_data["password"],
            username=user2_data["username"]
        )
        
        # Login to get tokens
        user1_login = auth_service.login(
            email=user1_data["email"],
            password=user1_data["password"]
        )
        
        user2_login = auth_service.login(
            email=user2_data["email"],
            password=user2_data["password"]
        )
        
        return {
            "user1": {
                "id": user1_result.user.id,
                "email": user1_data["email"],
                "token": user1_login.access_token,
                "user": user1_result.user
            },
            "user2": {
                "id": user2_result.user.id,
                "email": user2_data["email"],
                "token": user2_login.access_token,
                "user": user2_result.user
            }
        }
    
    def test_repository_user_isolation(self, db_session: Session, test_users: Dict):
        """Test that repositories properly isolate data by user"""
        
        # Create user-scoped repositories
        user1_repo = TaskRepository(db_session).with_user(test_users["user1"]["id"])
        user2_repo = TaskRepository(db_session).with_user(test_users["user2"]["id"])
        
        # Create tasks for each user
        task1_data = {
            "title": "User 1 Task",
            "description": "This belongs to user 1",
            "git_branch_id": str(uuid.uuid4()),
            "status": "todo"
        }
        
        task2_data = {
            "title": "User 2 Task",
            "description": "This belongs to user 2",
            "git_branch_id": str(uuid.uuid4()),
            "status": "todo"
        }
        
        # Create tasks
        task1 = user1_repo.create(task1_data)
        task2 = user2_repo.create(task2_data)
        
        # Verify each user can only see their own tasks
        user1_tasks = user1_repo.find_all()
        assert len(user1_tasks) == 1
        assert user1_tasks[0].id == task1.id
        assert user1_tasks[0].user_id == test_users["user1"]["id"]
        
        user2_tasks = user2_repo.find_all()
        assert len(user2_tasks) == 1
        assert user2_tasks[0].id == task2.id
        assert user2_tasks[0].user_id == test_users["user2"]["id"]
        
        # Verify user1 cannot access user2's task
        user1_task2 = user1_repo.find_by_id(task2.id)
        assert user1_task2 is None
        
        # Verify user2 cannot access user1's task
        user2_task1 = user2_repo.find_by_id(task1.id)
        assert user2_task1 is None
    
    def test_api_endpoint_isolation(self, test_client: TestClient, test_users: Dict):
        """Test that API endpoints properly isolate data by user"""
        
        # Create tasks as user1
        user1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
        user1_task_data = {
            "title": "User 1 API Task",
            "description": "Created via API by user 1",
            "git_branch_id": str(uuid.uuid4())
        }
        
        response1 = test_client.post(
            "/api/v2/tasks/",
            json=user1_task_data,
            headers=user1_headers
        )
        assert response1.status_code == 200
        user1_task = response1.json()["task"]
        
        # Create tasks as user2
        user2_headers = {"Authorization": f"Bearer {test_users['user2']['token']}"}
        user2_task_data = {
            "title": "User 2 API Task",
            "description": "Created via API by user 2",
            "git_branch_id": str(uuid.uuid4())
        }
        
        response2 = test_client.post(
            "/api/v2/tasks/",
            json=user2_task_data,
            headers=user2_headers
        )
        assert response2.status_code == 200
        user2_task = response2.json()["task"]
        
        # Verify user1 can only see their own tasks
        list_response1 = test_client.get("/api/v2/tasks/", headers=user1_headers)
        assert list_response1.status_code == 200
        user1_task_list = list_response1.json()["tasks"]
        assert len(user1_task_list) == 1
        assert user1_task_list[0]["id"] == user1_task["id"]
        
        # Verify user2 can only see their own tasks
        list_response2 = test_client.get("/api/v2/tasks/", headers=user2_headers)
        assert list_response2.status_code == 200
        user2_task_list = list_response2.json()["tasks"]
        assert len(user2_task_list) == 1
        assert user2_task_list[0]["id"] == user2_task["id"]
        
        # Verify user1 cannot access user2's task
        get_response1 = test_client.get(
            f"/api/v2/tasks/{user2_task['id']}",
            headers=user1_headers
        )
        assert get_response1.status_code == 404
        
        # Verify user2 cannot access user1's task
        get_response2 = test_client.get(
            f"/api/v2/tasks/{user1_task['id']}",
            headers=user2_headers
        )
        assert get_response2.status_code == 404
    
    def test_cross_user_update_prevention(self, test_client: TestClient, test_users: Dict):
        """Test that users cannot update each other's data"""
        
        # Create task as user1
        user1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
        task_data = {
            "title": "User 1 Task to Update",
            "description": "Original description",
            "git_branch_id": str(uuid.uuid4())
        }
        
        create_response = test_client.post(
            "/api/v2/tasks/",
            json=task_data,
            headers=user1_headers
        )
        assert create_response.status_code == 200
        task = create_response.json()["task"]
        
        # Try to update user1's task as user2 (should fail)
        user2_headers = {"Authorization": f"Bearer {test_users['user2']['token']}"}
        update_data = {
            "title": "Hacked by User 2",
            "description": "User 2 shouldn't be able to do this"
        }
        
        update_response = test_client.put(
            f"/api/v2/tasks/{task['id']}",
            json=update_data,
            headers=user2_headers
        )
        assert update_response.status_code == 404  # Task not found for user2
        
        # Verify task remains unchanged
        get_response = test_client.get(
            f"/api/v2/tasks/{task['id']}",
            headers=user1_headers
        )
        assert get_response.status_code == 200
        unchanged_task = get_response.json()["task"]
        assert unchanged_task["title"] == task_data["title"]
        assert unchanged_task["description"] == task_data["description"]
    
    def test_cross_user_delete_prevention(self, test_client: TestClient, test_users: Dict):
        """Test that users cannot delete each other's data"""
        
        # Create task as user1
        user1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
        task_data = {
            "title": "User 1 Task to Delete",
            "description": "This should only be deletable by user 1",
            "git_branch_id": str(uuid.uuid4())
        }
        
        create_response = test_client.post(
            "/api/v2/tasks/",
            json=task_data,
            headers=user1_headers
        )
        assert create_response.status_code == 200
        task = create_response.json()["task"]
        
        # Try to delete user1's task as user2 (should fail)
        user2_headers = {"Authorization": f"Bearer {test_users['user2']['token']}"}
        delete_response = test_client.delete(
            f"/api/v2/tasks/{task['id']}",
            headers=user2_headers
        )
        assert delete_response.status_code == 404  # Task not found for user2
        
        # Verify task still exists for user1
        get_response = test_client.get(
            f"/api/v2/tasks/{task['id']}",
            headers=user1_headers
        )
        assert get_response.status_code == 200
        existing_task = get_response.json()["task"]
        assert existing_task["id"] == task["id"]
    
    def test_system_mode_access(self, db_session: Session, test_users: Dict):
        """Test that system mode can access all user data (for admin operations)"""
        
        # Create tasks for both users
        user1_repo = TaskRepository(db_session).with_user(test_users["user1"]["id"])
        user2_repo = TaskRepository(db_session).with_user(test_users["user2"]["id"])
        
        task1 = user1_repo.create({
            "title": "User 1 System Test Task",
            "git_branch_id": str(uuid.uuid4())
        })
        
        task2 = user2_repo.create({
            "title": "User 2 System Test Task",
            "git_branch_id": str(uuid.uuid4())
        })
        
        # Create system-mode repository (no user_id)
        system_repo = TaskRepository(db_session).create_system_context()
        
        # System mode should see all tasks
        all_tasks = system_repo.find_all()
        task_ids = [t.id for t in all_tasks]
        
        assert task1.id in task_ids
        assert task2.id in task_ids
        
        # System mode can access any specific task
        system_task1 = system_repo.find_by_id(task1.id)
        assert system_task1 is not None
        assert system_task1.user_id == test_users["user1"]["id"]
        
        system_task2 = system_repo.find_by_id(task2.id)
        assert system_task2 is not None
        assert system_task2.user_id == test_users["user2"]["id"]
    
    def test_bulk_operation_isolation(self, db_session: Session, test_users: Dict):
        """Test that bulk operations respect user isolation"""
        
        # Create multiple tasks for each user
        user1_repo = TaskRepository(db_session).with_user(test_users["user1"]["id"])
        user2_repo = TaskRepository(db_session).with_user(test_users["user2"]["id"])
        
        # Create 3 tasks for user1
        for i in range(3):
            user1_repo.create({
                "title": f"User 1 Bulk Task {i}",
                "git_branch_id": str(uuid.uuid4())
            })
        
        # Create 2 tasks for user2
        for i in range(2):
            user2_repo.create({
                "title": f"User 2 Bulk Task {i}",
                "git_branch_id": str(uuid.uuid4())
            })
        
        # Bulk delete for user1 should only affect user1's tasks
        user1_tasks = user1_repo.find_all()
        assert len(user1_tasks) == 3
        
        # Simulate bulk update (mark all as completed)
        for task in user1_tasks:
            task.status = "done"
        user1_repo.session.commit()
        
        # Verify user2's tasks are unaffected
        user2_tasks = user2_repo.find_all()
        assert len(user2_tasks) == 2
        assert all(task.status != "done" for task in user2_tasks)
    
    def test_statistics_isolation(self, test_client: TestClient, test_users: Dict):
        """Test that statistics are properly isolated by user"""
        
        # Create different numbers of tasks for each user
        user1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
        user2_headers = {"Authorization": f"Bearer {test_users['user2']['token']}"}
        
        # Create 5 tasks for user1 with different statuses
        for i in range(3):
            test_client.post(
                "/api/v2/tasks/",
                json={
                    "title": f"User 1 Task {i}",
                    "git_branch_id": str(uuid.uuid4()),
                    "status": "todo"
                },
                headers=user1_headers
            )
        
        for i in range(2):
            test_client.post(
                "/api/v2/tasks/",
                json={
                    "title": f"User 1 Completed Task {i}",
                    "git_branch_id": str(uuid.uuid4()),
                    "status": "done"
                },
                headers=user1_headers
            )
        
        # Create 2 tasks for user2
        for i in range(2):
            test_client.post(
                "/api/v2/tasks/",
                json={
                    "title": f"User 2 Task {i}",
                    "git_branch_id": str(uuid.uuid4()),
                    "status": "in_progress"
                },
                headers=user2_headers
            )
        
        # Get statistics for user1
        stats1_response = test_client.get(
            "/api/v2/tasks/stats/summary",
            headers=user1_headers
        )
        assert stats1_response.status_code == 200
        stats1 = stats1_response.json()["stats"]
        assert stats1["total_tasks"] == 5
        assert stats1["completed_tasks"] == 2
        assert stats1["pending_tasks"] == 3
        
        # Get statistics for user2
        stats2_response = test_client.get(
            "/api/v2/tasks/stats/summary",
            headers=user2_headers
        )
        assert stats2_response.status_code == 200
        stats2 = stats2_response.json()["stats"]
        assert stats2["total_tasks"] == 2
        assert stats2["in_progress_tasks"] == 2
        assert stats2["completed_tasks"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])