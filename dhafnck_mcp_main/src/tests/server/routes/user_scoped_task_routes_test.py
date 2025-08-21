"""
Tests for User-Scoped Task Routes with Authentication
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastmcp.server.routes.user_scoped_task_routes import (
    router,
    UserScopedRepositoryFactory,
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    complete_task,
    get_user_task_stats
)
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from fastmcp.task_management.application.dtos.task.update_task_request import UpdateTaskRequest
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest


class TestUserScopedRepositoryFactory:
    """Test the UserScopedRepositoryFactory"""
    
    def test_create_task_repository(self):
        """Test creating a user-scoped task repository"""
        mock_session = Mock(spec=Session)
        user_id = "user-123"
        
        # Mock the repository and its with_user method
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepository') as MockTaskRepo:
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockTaskRepo.return_value = mock_repo_instance
            
            repo = UserScopedRepositoryFactory.create_task_repository(mock_session, user_id)
            
            MockTaskRepo.assert_called_once_with(mock_session)
            mock_repo_instance.with_user.assert_called_once_with(user_id)
            assert repo == mock_repo_instance
    
    def test_create_project_repository(self):
        """Test creating a user-scoped project repository"""
        mock_session = Mock(spec=Session)
        user_id = "user-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.ProjectRepository') as MockProjectRepo:
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockProjectRepo.return_value = mock_repo_instance
            
            repo = UserScopedRepositoryFactory.create_project_repository(mock_session, user_id)
            
            MockProjectRepo.assert_called_once_with(mock_session)
            mock_repo_instance.with_user.assert_called_once_with(user_id)
            assert repo == mock_repo_instance
    
    def test_create_agent_repository(self):
        """Test creating a user-scoped agent repository"""
        mock_session = Mock(spec=Session)
        user_id = "user-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.AgentRepository') as MockAgentRepo:
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockAgentRepo.return_value = mock_repo_instance
            
            repo = UserScopedRepositoryFactory.create_agent_repository(mock_session, user_id)
            
            MockAgentRepo.assert_called_once_with(mock_session)
            mock_repo_instance.with_user.assert_called_once_with(user_id)
            assert repo == mock_repo_instance


class TestTaskRoutes:
    """Test the user-scoped task route endpoints"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task"""
        task = Mock()
        task.id = "task-123"
        task.title = "Test Task"
        task.status = "todo"
        task.priority = "high"
        task.user_id = "user-123"
        return task
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_user, mock_db_session):
        """Test successful task creation"""
        request = CreateTaskRequest(
            title="New Task",
            description="Task description",
            status="todo",
            priority="high"
        )
        
        mock_task = Mock()
        mock_task.id = "task-456"
        mock_task.title = request.title
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.create_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await create_task(request, mock_user, mock_db_session)
            
            # Verify
            MockFactory.create_task_repository.assert_called_once_with(mock_db_session, mock_user.id)
            MockFacade.assert_called_once()
            mock_facade.create_task.assert_called_once_with(request)
            
            assert result["success"] is True
            assert result["task"] == mock_task
            assert f"user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_task_failure(self, mock_user, mock_db_session):
        """Test task creation failure"""
        request = CreateTaskRequest(title="New Task")
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            MockFactory.create_task_repository.side_effect = Exception("Database error")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_task(request, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create task" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mock_user, mock_db_session):
        """Test successful task listing"""
        mock_tasks = [
            Mock(id="1", title="Task 1", status="todo"),
            Mock(id="2", title="Task 2", status="done")
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.list_tasks.return_value = mock_tasks
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await list_tasks(
                status="todo",
                priority="high",
                limit=10,
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify
            assert result["success"] is True
            assert result["tasks"] == mock_tasks
            assert result["count"] == 2
            assert result["user"] == mock_user.email
    
    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task retrieval"""
        task_id = "task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await get_task(task_id, mock_user, mock_db_session)
            
            # Verify
            mock_facade.get_task.assert_called_once_with(task_id)
            assert result["success"] is True
            assert result["task"] == mock_task
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_user, mock_db_session):
        """Test task not found scenario"""
        task_id = "nonexistent-task"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = None
            MockFacade.return_value = mock_facade
            
            # Call the function
            with pytest.raises(HTTPException) as exc_info:
                await get_task(task_id, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Task not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task update"""
        task_id = "task-123"
        request = UpdateTaskRequest(
            title="Updated Task",
            status="in_progress"
        )
        
        updated_task = Mock()
        updated_task.id = task_id
        updated_task.title = request.title
        updated_task.status = request.status
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            mock_facade.update_task.return_value = updated_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await update_task(task_id, request, mock_user, mock_db_session)
            
            # Verify
            mock_facade.get_task.assert_called_once_with(task_id)
            mock_facade.update_task.assert_called_once_with(task_id, request)
            assert result["success"] is True
            assert result["task"] == updated_task
            assert "Task updated successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, mock_user, mock_db_session):
        """Test updating non-existent task"""
        task_id = "nonexistent-task"
        request = UpdateTaskRequest(title="Updated")
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = None
            MockFacade.return_value = mock_facade
            
            # Call the function
            with pytest.raises(HTTPException) as exc_info:
                await update_task(task_id, request, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Task not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task deletion"""
        task_id = "task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await delete_task(task_id, mock_user, mock_db_session)
            
            # Verify
            mock_facade.get_task.assert_called_once_with(task_id)
            mock_facade.delete_task.assert_called_once_with(task_id)
            assert result["success"] is True
            assert "Task deleted successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task completion"""
        task_id = "task-123"
        completion_summary = "Task completed successfully"
        testing_notes = "All tests passed"
        
        completed_task = Mock()
        completed_task.id = task_id
        completed_task.status = "done"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            mock_facade.complete_task.return_value = completed_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await complete_task(
                task_id,
                completion_summary,
                testing_notes,
                mock_user,
                mock_db_session
            )
            
            # Verify
            mock_facade.complete_task.assert_called_once_with(
                task_id=task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            assert result["success"] is True
            assert result["task"] == completed_task
            assert "Task completed successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_user_task_stats(self, mock_user, mock_db_session):
        """Test getting user task statistics"""
        mock_tasks = [
            Mock(status="done", priority="high"),
            Mock(status="done", priority="low"),
            Mock(status="in_progress", priority="high"),
            Mock(status="todo", priority="medium"),
            Mock(status="todo", priority="high")
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            # Setup mocks
            mock_task_repo = Mock()
            mock_task_repo.find_all.return_value = mock_tasks
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            # Call the function
            result = await get_user_task_stats(mock_user, mock_db_session)
            
            # Verify
            assert result["success"] is True
            stats = result["stats"]
            assert stats["total_tasks"] == 5
            assert stats["completed_tasks"] == 2
            assert stats["in_progress_tasks"] == 1
            assert stats["pending_tasks"] == 2
            assert stats["high_priority_tasks"] == 3
            assert stats["user"] == mock_user.email


class TestRouterIntegration:
    """Test router integration with FastAPI"""
    
    def test_router_prefix(self):
        """Test that router has correct prefix"""
        assert router.prefix == "/api/v2/tasks"
    
    def test_router_tags(self):
        """Test that router has correct tags"""
        assert "User-Scoped Tasks" in router.tags
    
    def test_router_endpoints(self):
        """Test that all expected endpoints are registered"""
        route_paths = [route.path for route in router.routes]
        
        # Check main CRUD endpoints
        assert "/" in route_paths  # POST and GET
        assert "/{task_id}" in route_paths  # GET, PUT, DELETE
        assert "/{task_id}/complete" in route_paths  # POST
        assert "/stats/summary" in route_paths  # GET
    
    def test_endpoint_methods(self):
        """Test that endpoints have correct HTTP methods"""
        method_paths = {}
        for route in router.routes:
            if hasattr(route, 'methods'):
                for method in route.methods:
                    if route.path not in method_paths:
                        method_paths[route.path] = []
                    method_paths[route.path].append(method)
        
        # Verify methods for each path
        assert "POST" in method_paths.get("/", [])
        assert "GET" in method_paths.get("/", [])
        assert "GET" in method_paths.get("/{task_id}", [])
        assert "PUT" in method_paths.get("/{task_id}", [])
        assert "DELETE" in method_paths.get("/{task_id}", [])
        assert "POST" in method_paths.get("/{task_id}/complete", [])
        assert "GET" in method_paths.get("/stats/summary", [])


class TestErrorHandling:
    """Test error handling in routes"""
    
    @pytest.mark.asyncio
    async def test_http_exception_passthrough(self, mock_user, mock_db_session):
        """Test that HTTPExceptions are passed through correctly"""
        task_id = "task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            mock_facade = Mock()
            # Simulate an HTTPException being raised
            mock_facade.get_task.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            MockFacade.return_value = mock_facade
            
            with pytest.raises(HTTPException) as exc_info:
                await get_task(task_id, mock_user, mock_db_session)
            
            # Verify the original exception is preserved
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == "Access denied"
    
    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, mock_user, mock_db_session):
        """Test handling of unexpected errors"""
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            # Simulate unexpected error
            MockFactory.create_task_repository.side_effect = RuntimeError("Unexpected error")
            
            with pytest.raises(HTTPException) as exc_info:
                await list_tasks(current_user=mock_user, db=mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to list tasks" in str(exc_info.value.detail)


class TestAuthenticationIntegration:
    """Test authentication integration in routes."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="auth-user-456", 
            email="auth@example.com",
            username="authuser",
            full_name="Auth User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )

    @pytest.mark.asyncio
    async def test_supabase_auth_fallback_handling(self, mock_user):
        """Test that routes handle Supabase auth fallback correctly."""
        mock_db_session = Mock(spec=Session)
        
        # Mock the try/except import logic from the routes module
        with patch('fastmcp.server.routes.user_scoped_task_routes.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = mock_user
            
            with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
                 patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
                
                MockFactory.create_task_repository.return_value = Mock()
                mock_facade = Mock()
                mock_facade.list_tasks.return_value = []
                MockFacade.return_value = mock_facade
                
                # Call the list_tasks function
                result = await list_tasks(current_user=mock_user, db=mock_db_session)
                
                # Verify user was used correctly
                MockFactory.create_task_repository.assert_called_once_with(mock_db_session, mock_user.id)
                assert result["user"] == mock_user.email

    @pytest.mark.asyncio
    async def test_user_id_passed_correctly_to_repositories(self, mock_user):
        """Test that user ID is correctly passed to all repository factories."""
        mock_db_session = Mock(spec=Session)
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            mock_task_repo = Mock()
            mock_project_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            MockFactory.create_project_repository.return_value = mock_project_repo
            
            with patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
                mock_facade = Mock()
                mock_task = Mock(id="task-456", title="Test Task")
                mock_facade.create_task.return_value = mock_task
                MockFacade.return_value = mock_facade
                
                request = CreateTaskRequest(
                    title="New Task",
                    description="Task description"
                )
                
                result = await create_task(request, mock_user, mock_db_session)
                
                # Verify user ID passed correctly
                MockFactory.create_task_repository.assert_called_with(mock_db_session, "auth-user-456")
                MockFactory.create_project_repository.assert_called_with(mock_db_session, "auth-user-456")
                
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_user_scoped_access_control(self, mock_user):
        """Test that user scoped access control works correctly."""
        mock_db_session = Mock(spec=Session)
        task_id = "restricted-task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup user-scoped repository
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            # Setup facade to return None (task not found for this user)
            mock_facade = Mock()
            mock_facade.get_task.return_value = None
            MockFacade.return_value = mock_facade
            
            # Attempt to access task should fail with 404
            with pytest.raises(HTTPException) as exc_info:
                await get_task(task_id, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Task not found" in str(exc_info.value.detail)
            
            # Verify user-scoped repository was used
            MockFactory.create_task_repository.assert_called_with(mock_db_session, mock_user.id)

    @pytest.mark.asyncio 
    async def test_audit_logging_with_user_context(self, mock_user):
        """Test that audit logging includes proper user context."""
        mock_db_session = Mock(spec=Session)
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_task = Mock(id="logged-task-789", title="Logged Task")
            mock_facade.create_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            request = CreateTaskRequest(title="Logged Task", description="For audit testing")
            
            await create_task(request, mock_user, mock_db_session)
            
            # Verify audit log contains user information
            mock_logger.info.assert_called_with(f"User {mock_user.email} creating task: {request.title}")

    @pytest.mark.asyncio
    async def test_user_stats_calculation_scoped_correctly(self, mock_user):
        """Test that user statistics are calculated only for the user's tasks."""
        mock_db_session = Mock(spec=Session)
        
        # Create mock tasks with different statuses for the user
        mock_user_tasks = [
            Mock(status="done", priority="high"),       # completed, high priority
            Mock(status="done", priority="medium"),     # completed, medium priority  
            Mock(status="in_progress", priority="high"), # in progress, high priority
            Mock(status="todo", priority="low"),        # pending, low priority
            Mock(status="todo", priority="high"),       # pending, high priority
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            mock_task_repo = Mock()
            mock_task_repo.find_all.return_value = mock_user_tasks
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            result = await get_user_task_stats(mock_user, mock_db_session)
            
            # Verify user-scoped repository was used
            MockFactory.create_task_repository.assert_called_with(mock_db_session, mock_user.id)
            
            # Verify statistics are calculated correctly
            stats = result["stats"]
            assert stats["total_tasks"] == 5
            assert stats["completed_tasks"] == 2       # 2 "done" tasks
            assert stats["in_progress_tasks"] == 1     # 1 "in_progress" task
            assert stats["pending_tasks"] == 2        # 2 "todo" tasks  
            assert stats["high_priority_tasks"] == 3  # 3 "high" priority tasks
            assert stats["user"] == mock_user.email

    @pytest.mark.asyncio
    async def test_task_completion_with_user_context(self, mock_user):
        """Test task completion includes proper user context and validation."""
        mock_db_session = Mock(spec=Session)
        task_id = "completion-task-123"
        completion_summary = "Task completed with full context"
        testing_notes = "All tests passed for user scope"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            # Mock existing task for user
            existing_task = Mock(id=task_id, user_id=mock_user.id)
            completed_task = Mock(id=task_id, status="done", user_id=mock_user.id)
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = existing_task
            mock_facade.complete_task.return_value = completed_task
            MockFacade.return_value = mock_facade
            
            result = await complete_task(
                task_id, completion_summary, testing_notes, mock_user, mock_db_session
            )
            
            # Verify user-scoped validation occurred
            mock_facade.get_task.assert_called_once_with(task_id)
            
            # Verify completion with proper parameters
            mock_facade.complete_task.assert_called_once_with(
                task_id=task_id,
                completion_summary=completion_summary, 
                testing_notes=testing_notes
            )
            
            # Verify audit logging
            mock_logger.info.assert_called_with(f"User {mock_user.email} completed task {task_id}")
            
            assert result["success"] is True
            assert result["task"] == completed_task