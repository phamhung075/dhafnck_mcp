"""Test suite for CreateProjectUseCase.

Tests the project creation use case including:
- Project entity creation
- Repository persistence
- Default branch creation
- Context initialization
- Error handling
- Backward compatibility
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4

from fastmcp.task_management.application.use_cases.create_project import CreateProjectUseCase
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.repositories.project_repository import ProjectRepository


class TestCreateProjectUseCase:
    """Test cases for CreateProjectUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock(spec=ProjectRepository)
        self.mock_repository.save = AsyncMock()
        self.use_case = CreateProjectUseCase(self.mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Test successful project creation with all parameters."""
        project_id = str(uuid4())
        name = "Test Project"
        description = "Test project description"
        
        result = await self.use_case.execute(project_id, name, description)
        
        assert result["success"] is True
        assert result["project"]["id"] == project_id
        assert result["project"]["name"] == name
        assert result["project"]["description"] == description
        assert "created_at" in result["project"]
        assert "updated_at" in result["project"]
        assert "git_branchs" in result["project"]
        assert "main" in result["project"]["git_branchs"]
        
        # Verify repository save was called
        self.mock_repository.save.assert_called_once()
        saved_project = self.mock_repository.save.call_args[0][0]
        assert isinstance(saved_project, Project)
        assert saved_project.id == project_id
        assert saved_project.name == name
        assert saved_project.description == description
    
    @pytest.mark.asyncio
    async def test_create_project_auto_generate_id(self):
        """Test project creation with auto-generated ID."""
        name = "Test Project"
        description = "Test description"
        
        result = await self.use_case.execute(None, name, description)
        
        assert result["success"] is True
        assert result["project"]["id"] is not None
        assert len(result["project"]["id"]) == 36  # UUID format
        assert result["project"]["name"] == name
        assert result["project"]["description"] == description
    
    @pytest.mark.asyncio
    async def test_create_project_backward_compatibility_old_signature(self):
        """Test backward compatibility with old (name, description) signature."""
        name = "Test Project"
        description = "Test description"
        
        # Call with old signature style (project_id is actually name)
        result = await self.use_case.execute(name, description)
        
        assert result["success"] is True
        assert result["project"]["name"] == name
        assert result["project"]["description"] == description
        assert result["project"]["id"] is not None  # Auto-generated
    
    @pytest.mark.asyncio
    async def test_create_project_missing_name(self):
        """Test project creation fails without name."""
        result = await self.use_case.execute(None, None, "description")
        
        assert result["success"] is False
        assert result["error"] == "Project name is required"
    
    @pytest.mark.asyncio
    async def test_create_project_empty_description(self):
        """Test project creation with empty description."""
        name = "Test Project"
        
        result = await self.use_case.execute(None, name, "")
        
        assert result["success"] is True
        assert result["project"]["name"] == name
        assert result["project"]["description"] == ""
    
    @pytest.mark.asyncio
    async def test_create_project_default_main_branch(self):
        """Test that default main branch is created."""
        name = "Test Project"
        
        result = await self.use_case.execute(None, name)
        
        assert result["success"] is True
        assert "main" in result["project"]["git_branchs"]
        
        # Verify project entity has main branch
        saved_project = self.mock_repository.save.call_args[0][0]
        assert "main" in saved_project.git_branchs
        main_branch = saved_project.git_branchs["main"]
        assert main_branch.name == "main"
        assert main_branch.description == "Main task tree for the project"
    
    @pytest.mark.asyncio
    async def test_create_project_repository_save_error(self):
        """Test handling of repository save errors."""
        self.mock_repository.save.side_effect = ValueError("Duplicate project name")
        
        result = await self.use_case.execute(None, "Test Project")
        
        assert result["success"] is False
        assert "Duplicate project name" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_project_unexpected_error(self):
        """Test handling of unexpected errors."""
        self.mock_repository.save.side_effect = Exception("Unexpected error")
        
        result = await self.use_case.execute(None, "Test Project")
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
    
    @pytest.mark.asyncio
    @patch('fastmcp.task_management.application.use_cases.create_project.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_project.AuthConfig')
    async def test_create_project_context_creation_success(self, mock_auth_config, mock_context_factory):
        """Test successful project context creation."""
        # Setup authentication
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "test-user"
        
        # Setup context facade
        mock_context_facade = Mock()
        mock_context_facade.create_context.return_value = {"success": True}
        mock_context_factory_instance = Mock()
        mock_context_factory_instance.create_facade.return_value = mock_context_facade
        mock_context_factory.return_value = mock_context_factory_instance
        
        # Create project
        result = await self.use_case.execute(None, "Test Project", "Description")
        
        assert result["success"] is True
        
        # Verify context creation was attempted
        mock_context_factory.assert_called_once()
        mock_context_factory_instance.create_facade.assert_called_once_with(
            user_id="test-user",
            project_id=result["project"]["id"]
        )
        mock_context_facade.create_context.assert_called_once()
        
        # Verify context data
        context_call = mock_context_facade.create_context.call_args
        assert context_call[1]["level"] == "project"
        assert context_call[1]["context_id"] == result["project"]["id"]
        assert context_call[1]["data"]["name"] == "Test Project"
    
    @pytest.mark.asyncio
    @patch('fastmcp.task_management.application.use_cases.create_project.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_project.AuthConfig')
    async def test_create_project_context_creation_failure(self, mock_auth_config, mock_context_factory):
        """Test project creation continues even if context creation fails."""
        # Setup authentication
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "test-user"
        
        # Setup context facade to fail
        mock_context_facade = Mock()
        mock_context_facade.create_context.return_value = {"success": False, "error": "Context error"}
        mock_context_factory_instance = Mock()
        mock_context_factory_instance.create_facade.return_value = mock_context_facade
        mock_context_factory.return_value = mock_context_factory_instance
        
        # Create project
        result = await self.use_case.execute(None, "Test Project", "Description")
        
        # Project creation should still succeed
        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"
    
    @pytest.mark.asyncio
    @patch('fastmcp.task_management.application.use_cases.create_project.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_project.AuthConfig')
    async def test_create_project_context_creation_exception(self, mock_auth_config, mock_context_factory):
        """Test project creation continues even if context creation throws exception."""
        # Setup authentication
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "test-user"
        
        # Setup context factory to throw exception
        mock_context_factory.side_effect = Exception("Context factory error")
        
        # Create project
        result = await self.use_case.execute(None, "Test Project", "Description")
        
        # Project creation should still succeed
        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"
    
    @pytest.mark.asyncio
    @patch('fastmcp.task_management.application.use_cases.create_project.request')
    @patch('fastmcp.task_management.application.use_cases.create_project.UnifiedContextFacadeFactory')
    async def test_create_project_context_with_request_user(self, mock_context_factory, mock_request):
        """Test context creation uses user ID from request."""
        # Setup request with user_id
        mock_request.user_id = "request-user-123"
        
        # Setup context facade
        mock_context_facade = Mock()
        mock_context_facade.create_context.return_value = {"success": True}
        mock_context_factory_instance = Mock()
        mock_context_factory_instance.create_facade.return_value = mock_context_facade
        mock_context_factory.return_value = mock_context_factory_instance
        
        # Create project
        result = await self.use_case.execute(None, "Test Project", "Description")
        
        assert result["success"] is True
        
        # Verify request user ID was used
        mock_context_factory_instance.create_facade.assert_called_once_with(
            user_id="request-user-123",
            project_id=result["project"]["id"]
        )
    
    @pytest.mark.asyncio
    async def test_create_project_timestamps(self):
        """Test that timestamps are properly set."""
        before_create = datetime.now(timezone.utc)
        
        result = await self.use_case.execute(None, "Test Project")
        
        after_create = datetime.now(timezone.utc)
        
        assert result["success"] is True
        
        # Parse timestamps
        created_at = datetime.fromisoformat(result["project"]["created_at"])
        updated_at = datetime.fromisoformat(result["project"]["updated_at"])
        
        # Verify timestamps are in expected range
        assert before_create <= created_at <= after_create
        assert before_create <= updated_at <= after_create
        assert created_at == updated_at  # Should be equal on creation
    
    @pytest.mark.asyncio
    async def test_create_project_with_special_characters(self):
        """Test project creation with special characters in name."""
        special_names = [
            "Project with spaces",
            "Project-with-dashes",
            "Project_with_underscores",
            "Project.with.dots",
            "Project@special#chars",
            "プロジェクト",  # Japanese
            "项目",  # Chinese
            "🚀 Rocket Project"  # Emoji
        ]
        
        for name in special_names:
            result = await self.use_case.execute(None, name, "Test")
            assert result["success"] is True
            assert result["project"]["name"] == name
    
    @pytest.mark.asyncio
    async def test_create_project_entity_properties(self):
        """Test that created project entity has all expected properties."""
        result = await self.use_case.execute(None, "Test Project", "Description")
        
        assert result["success"] is True
        
        # Get the saved entity
        saved_project = self.mock_repository.save.call_args[0][0]
        
        # Verify entity properties
        assert isinstance(saved_project, Project)
        assert saved_project.id is not None
        assert saved_project.name == "Test Project"
        assert saved_project.description == "Description"
        assert isinstance(saved_project.created_at, datetime)
        assert isinstance(saved_project.updated_at, datetime)
        assert len(saved_project.git_branchs) == 1
        assert "main" in saved_project.git_branchs