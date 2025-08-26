"""
Unit tests for User-Scoped Project Routes

Tests the FastAPI endpoints for user-isolated project management.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from fastmcp.server.routes.user_scoped_project_routes import (
    create_project, list_projects, get_project, update_project,
    delete_project, project_health_check
)
from fastmcp.auth.domain.entities.user import User


class TestUserScopedProjectRoutes:
    """Test cases for user-scoped project routes"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        user = Mock(spec=User)
        user.id = "user123"
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_project_repo(self):
        """Create a mock project repository"""
        repo = Mock()
        repo.find_by_id = AsyncMock()
        repo.delete = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock project application service"""
        service = Mock()
        service.create_project = AsyncMock()
        service.list_projects = AsyncMock()
        service.get_project = AsyncMock()
        service.update_project = AsyncMock()
        service.project_health_check = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_user, mock_db_session, mock_service):
        """Test successful project creation"""
        # Setup
        project_name = "Test Project"
        project_description = "Test Description"
        project_id = str(uuid4())
        
        mock_service.create_project.return_value = {
            "id": project_id,
            "name": project_name,
            "description": project_description
        }
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository') as mock_repo_class:
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService') as mock_service_class:
                with patch('uuid.uuid4', return_value=project_id):
                    mock_service_class.return_value = mock_service
                    
                    # Execute
                    result = await create_project(
                        name=project_name,
                        description=project_description,
                        current_user=mock_user,
                        db=mock_db_session
                    )
        
        # Assert
        assert result["success"] is True
        assert result["project"]["id"] == project_id
        assert result["project"]["name"] == project_name
        assert f"Project created successfully for user {mock_user.email}" in result["message"]
        
        # Verify repository was created with user_id
        mock_repo_class.assert_called_once_with(session=mock_db_session, user_id=mock_user.id)
        
        # Verify service was created with user_id
        mock_service_class.assert_called_once_with(mock_repo_class.return_value, user_id=mock_user.id)
        
        # Verify service method was called
        mock_service.create_project.assert_called_once_with(project_id, project_name, project_description)
    
    @pytest.mark.asyncio
    async def test_create_project_error(self, mock_user, mock_db_session, mock_service):
        """Test project creation with error"""
        # Setup
        mock_service.create_project.side_effect = Exception("Database error")
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                with patch('uuid.uuid4'):
                    # Execute and assert
                    with pytest.raises(HTTPException) as exc_info:
                        await create_project(
                            name="Test",
                            description="",
                            current_user=mock_user,
                            db=mock_db_session
                        )
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to create project"
    
    @pytest.mark.asyncio
    async def test_list_projects_success(self, mock_user, mock_db_session, mock_service):
        """Test successful project listing"""
        # Setup
        projects = [
            {"id": "proj1", "name": "Project 1"},
            {"id": "proj2", "name": "Project 2"}
        ]
        mock_service.list_projects.return_value = {"projects": projects}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository') as mock_repo_class:
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService') as mock_service_class:
                mock_service_class.return_value = mock_service
                
                # Execute
                result = await list_projects(
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        # Assert
        assert result["success"] is True
        assert result["projects"] == projects
        assert result["total"] == 2
        assert f"Projects retrieved for user {mock_user.email}" in result["message"]
        
        # Verify user scoping
        mock_repo_class.assert_called_once_with(session=mock_db_session, user_id=mock_user.id)
        mock_service_class.assert_called_once_with(mock_repo_class.return_value, user_id=mock_user.id)
    
    @pytest.mark.asyncio
    async def test_list_projects_empty(self, mock_user, mock_db_session, mock_service):
        """Test listing projects when none exist"""
        # Setup
        mock_service.list_projects.return_value = {}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                # Execute
                result = await list_projects(
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        # Assert
        assert result["success"] is True
        assert result["projects"] == []
        assert result["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_user, mock_db_session, mock_service):
        """Test successfully getting a project"""
        # Setup
        project_id = "proj123"
        project_data = {
            "id": project_id,
            "name": "Test Project",
            "description": "Test Description"
        }
        mock_service.get_project.return_value = {"success": True, "project": project_data}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                # Execute
                result = await get_project(
                    project_id=project_id,
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        # Assert
        assert result["success"] is True
        assert result["project"] == project_data
        assert f"Project retrieved for user {mock_user.email}" in result["message"]
        
        # Verify service method was called
        mock_service.get_project.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_user, mock_db_session, mock_service):
        """Test getting a non-existent project"""
        # Setup
        project_id = "nonexistent"
        mock_service.get_project.return_value = {"success": False}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                # Execute and assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_project(
                        project_id=project_id,
                        current_user=mock_user,
                        db=mock_db_session
                    )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Project not found or access denied"
    
    @pytest.mark.asyncio
    async def test_update_project_success(self, mock_user, mock_db_session, mock_service):
        """Test successfully updating a project"""
        # Setup
        project_id = "proj123"
        new_name = "Updated Name"
        new_description = "Updated Description"
        updated_project = {
            "id": project_id,
            "name": new_name,
            "description": new_description
        }
        mock_service.update_project.return_value = {"success": True, "project": updated_project}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                # Execute
                result = await update_project(
                    project_id=project_id,
                    name=new_name,
                    description=new_description,
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        # Assert
        assert result["success"] is True
        assert result["project"] == updated_project
        assert f"Project updated successfully for user {mock_user.email}" in result["message"]
        
        # Verify service method was called
        mock_service.update_project.assert_called_once_with(project_id, new_name, new_description)
    
    @pytest.mark.asyncio
    async def test_update_project_partial(self, mock_user, mock_db_session, mock_service):
        """Test partially updating a project (only name)"""
        # Setup
        project_id = "proj123"
        new_name = "Updated Name"
        mock_service.update_project.return_value = {"success": True, "project": {}}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                # Execute
                await update_project(
                    project_id=project_id,
                    name=new_name,
                    description=None,
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        # Verify service was called with partial update
        mock_service.update_project.assert_called_once_with(project_id, new_name, None)
    
    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_user, mock_db_session, mock_project_repo):
        """Test successfully deleting a project"""
        # Setup
        project_id = "proj123"
        project = Mock()
        mock_project_repo.find_by_id.return_value = project
        mock_project_repo.delete.return_value = True
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository', return_value=mock_project_repo):
            # Execute
            result = await delete_project(
                project_id=project_id,
                current_user=mock_user,
                db=mock_db_session
            )
        
        # Assert
        assert result["success"] is True
        assert f"Project {project_id} deleted successfully for user {mock_user.email}" in result["message"]
        
        # Verify repository methods were called
        mock_project_repo.find_by_id.assert_called_once_with(project_id)
        mock_project_repo.delete.assert_called_once_with(project)
    
    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, mock_user, mock_db_session, mock_project_repo):
        """Test deleting a non-existent project"""
        # Setup
        project_id = "nonexistent"
        mock_project_repo.find_by_id.return_value = None
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository', return_value=mock_project_repo):
            # Execute and assert
            with pytest.raises(HTTPException) as exc_info:
                await delete_project(
                    project_id=project_id,
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Project not found or access denied"
    
    @pytest.mark.asyncio
    async def test_project_health_check_success(self, mock_user, mock_db_session, mock_service):
        """Test successful project health check"""
        # Setup
        project_id = "proj123"
        health_data = {
            "success": True,
            "health_score": 85,
            "issues": [],
            "recommendations": ["Run cleanup"]
        }
        mock_service.project_health_check.return_value = health_data
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_service):
                # Execute
                result = await project_health_check(
                    project_id=project_id,
                    current_user=mock_user,
                    db=mock_db_session
                )
        
        # Assert
        assert result["success"] is True
        assert result["health"] == health_data
        assert f"Health check completed for user {mock_user.email}" in result["message"]
        
        # Verify service method was called
        mock_service.project_health_check.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_routes_handle_exceptions(self, mock_user, mock_db_session):
        """Test that routes properly handle and log exceptions"""
        # Test each route with an exception
        routes_to_test = [
            (create_project, {"name": "Test", "description": ""}),
            (list_projects, {}),
            (get_project, {"project_id": "test"}),
            (update_project, {"project_id": "test"}),
            (project_health_check, {"project_id": "test"})
        ]
        
        for route_func, extra_args in routes_to_test:
            with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository', side_effect=Exception("DB Error")):
                with pytest.raises(HTTPException) as exc_info:
                    await route_func(
                        current_user=mock_user,
                        db=mock_db_session,
                        **extra_args
                    )
                
                assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR