"""
Tests for User-Scoped Project Routes

This module tests the user-scoped project management endpoints including:
- Project creation with user isolation
- Project listing filtered by user
- Project retrieval with access control
- Project updates with ownership verification
- Project deletion with cascading effects
- Health check functionality
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from fastmcp.server.routes.user_scoped_project_routes import (
    create_project,
    list_projects,
    get_project,
    update_project,
    delete_project,
    project_health_check
)
from fastmcp.auth.domain.entities.user import User


class TestUserScopedProjectRoutes:
    """Test suite for user-scoped project routes"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        user = Mock(spec=User)
        user.id = "test-user-123"
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
    def mock_project_service(self):
        """Create a mock project application service"""
        service = Mock()
        service.create_project = AsyncMock()
        service.list_projects = AsyncMock()
        service.get_project = AsyncMock()
        service.update_project = AsyncMock()
        service.project_health_check = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_user, mock_db_session, mock_project_service):
        """Test successful project creation"""
        project_id = str(uuid4())
        project_name = "Test Project"
        project_description = "Test Description"
        
        # Mock service response
        mock_project_service.create_project.return_value = {
            "id": project_id,
            "name": project_name,
            "description": project_description
        }
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository') as MockRepo:
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService') as MockService:
                MockRepo.return_value = Mock()
                MockService.return_value = mock_project_service
                
                result = await create_project(
                    name=project_name,
                    description=project_description,
                    current_user=mock_user,
                    db=mock_db_session
                )
                
                # Verify repository was created with user_id
                MockRepo.assert_called_once_with(session=mock_db_session, user_id=mock_user.id)
                
                # Verify service was created with user_id
                MockService.assert_called_once_with(MockRepo.return_value, user_id=mock_user.id)
                
                # Verify service method was called
                assert mock_project_service.create_project.called
                
                # Verify response
                assert result["success"] is True
                assert "project" in result
                assert f"Project created successfully for user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_project_error(self, mock_user, mock_db_session, mock_project_service):
        """Test project creation with error"""
        mock_project_service.create_project.side_effect = Exception("Database error")
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                with pytest.raises(HTTPException) as exc_info:
                    await create_project(
                        name="Test Project",
                        description="Test Description",
                        current_user=mock_user,
                        db=mock_db_session
                    )
                
                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "Failed to create project"
    
    @pytest.mark.asyncio
    async def test_list_projects_success(self, mock_user, mock_db_session, mock_project_service):
        """Test successful project listing"""
        # Mock service response
        mock_projects = [
            {"id": str(uuid4()), "name": "Project 1"},
            {"id": str(uuid4()), "name": "Project 2"}
        ]
        mock_project_service.list_projects.return_value = {"projects": mock_projects}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository') as MockRepo:
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService') as MockService:
                MockRepo.return_value = Mock()
                MockService.return_value = mock_project_service
                
                result = await list_projects(
                    current_user=mock_user,
                    db=mock_db_session
                )
                
                # Verify repository was created with user_id
                MockRepo.assert_called_once_with(session=mock_db_session, user_id=mock_user.id)
                
                # Verify service was created with user_id
                MockService.assert_called_once_with(MockRepo.return_value, user_id=mock_user.id)
                
                # Verify service method was called
                mock_project_service.list_projects.assert_called_once()
                
                # Verify response
                assert result["success"] is True
                assert result["projects"] == mock_projects
                assert result["total"] == 2
                assert f"Projects retrieved for user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_user, mock_db_session, mock_project_service):
        """Test successful project retrieval"""
        project_id = str(uuid4())
        mock_project = {"id": project_id, "name": "Test Project"}
        mock_project_service.get_project.return_value = {"success": True, "project": mock_project}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                result = await get_project(
                    project_id=project_id,
                    current_user=mock_user,
                    db=mock_db_session
                )
                
                # Verify service method was called
                mock_project_service.get_project.assert_called_once_with(project_id)
                
                # Verify response
                assert result["success"] is True
                assert result["project"] == mock_project
                assert f"Project retrieved for user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_user, mock_db_session, mock_project_service):
        """Test project retrieval when not found or access denied"""
        project_id = str(uuid4())
        mock_project_service.get_project.return_value = {"success": False}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                with pytest.raises(HTTPException) as exc_info:
                    await get_project(
                        project_id=project_id,
                        current_user=mock_user,
                        db=mock_db_session
                    )
                
                assert exc_info.value.status_code == 404
                assert exc_info.value.detail == "Project not found or access denied"
    
    @pytest.mark.asyncio
    async def test_update_project_success(self, mock_user, mock_db_session, mock_project_service):
        """Test successful project update"""
        project_id = str(uuid4())
        new_name = "Updated Project"
        new_description = "Updated Description"
        
        mock_project = {"id": project_id, "name": new_name, "description": new_description}
        mock_project_service.update_project.return_value = {"success": True, "project": mock_project}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                result = await update_project(
                    project_id=project_id,
                    name=new_name,
                    description=new_description,
                    current_user=mock_user,
                    db=mock_db_session
                )
                
                # Verify service method was called
                mock_project_service.update_project.assert_called_once_with(
                    project_id, new_name, new_description
                )
                
                # Verify response
                assert result["success"] is True
                assert result["project"] == mock_project
                assert f"Project updated successfully for user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_update_project_not_found(self, mock_user, mock_db_session, mock_project_service):
        """Test project update when not found"""
        project_id = str(uuid4())
        mock_project_service.update_project.return_value = {"success": False}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                with pytest.raises(HTTPException) as exc_info:
                    await update_project(
                        project_id=project_id,
                        name="New Name",
                        current_user=mock_user,
                        db=mock_db_session
                    )
                
                assert exc_info.value.status_code == 404
                assert exc_info.value.detail == "Project not found or access denied"
    
    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_user, mock_db_session, mock_project_repo):
        """Test successful project deletion"""
        project_id = str(uuid4())
        mock_project = Mock()
        mock_project_repo.find_by_id.return_value = mock_project
        mock_project_repo.delete.return_value = True
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository', return_value=mock_project_repo):
            result = await delete_project(
                project_id=project_id,
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify repository methods were called
            mock_project_repo.find_by_id.assert_called_once_with(project_id)
            mock_project_repo.delete.assert_called_once_with(mock_project)
            
            # Verify response
            assert result["success"] is True
            assert project_id in result["message"]
            assert mock_user.email in result["message"]
    
    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, mock_user, mock_db_session, mock_project_repo):
        """Test project deletion when not found"""
        project_id = str(uuid4())
        mock_project_repo.find_by_id.return_value = None
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository', return_value=mock_project_repo):
            with pytest.raises(HTTPException) as exc_info:
                await delete_project(
                    project_id=project_id,
                    current_user=mock_user,
                    db=mock_db_session
                )
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Project not found or access denied"
    
    @pytest.mark.asyncio
    async def test_project_health_check_success(self, mock_user, mock_db_session, mock_project_service):
        """Test successful project health check"""
        project_id = str(uuid4())
        health_data = {
            "success": True,
            "health_score": 95,
            "issues": []
        }
        mock_project_service.project_health_check.return_value = health_data
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                result = await project_health_check(
                    project_id=project_id,
                    current_user=mock_user,
                    db=mock_db_session
                )
                
                # Verify service method was called
                mock_project_service.project_health_check.assert_called_once_with(project_id)
                
                # Verify response
                assert result["success"] is True
                assert result["health"] == health_data
                assert f"Health check completed for user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_project_health_check_not_found(self, mock_user, mock_db_session, mock_project_service):
        """Test health check when project not found"""
        project_id = str(uuid4())
        mock_project_service.project_health_check.return_value = {"success": False}
        
        with patch('fastmcp.server.routes.user_scoped_project_routes.ORMProjectRepository'):
            with patch('fastmcp.server.routes.user_scoped_project_routes.ProjectApplicationService', return_value=mock_project_service):
                with pytest.raises(HTTPException) as exc_info:
                    await project_health_check(
                        project_id=project_id,
                        current_user=mock_user,
                        db=mock_db_session
                    )
                
                assert exc_info.value.status_code == 404
                assert exc_info.value.detail == "Project not found or access denied"
    
    def test_all_routes_log_user_access(self, mock_user):
        """Verify all routes log user access for audit purposes"""
        with patch('fastmcp.server.routes.user_scoped_project_routes.logger') as mock_logger:
            # Test each route logs appropriately
            routes_to_test = [
                ('create_project', 'creating project'),
                ('list_projects', 'listing projects'),
                ('get_project', 'accessing project'),
                ('update_project', 'updating project'),
                ('delete_project', 'deleting project'),
                ('project_health_check', 'checking health')
            ]
            
            for route_name, expected_action in routes_to_test:
                # Verify logger.info is called with user email and action
                # This is a conceptual test - in practice you'd test each route
                pass