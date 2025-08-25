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
from fastmcp.config.auth_config import AuthConfig
from fastmcp.task_management.domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError


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
        assert len(saved_project.git_branchs) == 1
        # Get the first (and only) branch
        branch_id = list(saved_project.git_branchs.keys())[0]
        main_branch = saved_project.git_branchs[branch_id]
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
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
    @patch('fastmcp.config.auth_config.AuthConfig')
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
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
    @patch('fastmcp.config.auth_config.AuthConfig')
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
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
    @patch('fastmcp.config.auth_config.AuthConfig')
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
    @patch('builtins.request')
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
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

    @pytest.mark.asyncio
    async def test_create_project_with_user_scoped_repository(self):
        """Test project creation with user-scoped repository."""
        # Add user_id attribute to mock repository
        self.mock_repository.user_id = "user-123"
        
        use_case = CreateProjectUseCase(self.mock_repository)
        
        with patch("fastmcp.task_management.domain.constants.validate_user_id") as mock_validate:
            mock_validate.return_value = None  # Valid user_id
            
            with patch("fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory") as mock_factory:
                mock_facade = AsyncMock()
                mock_facade.create_context = AsyncMock(return_value={"success": True})
                mock_factory.return_value.create_facade = MagicMock(return_value=mock_facade)
                
                result = await use_case.execute(
                    name="Test Project",
                    description="Test Description"
                )
                
                assert result["success"] is True
                
                # Verify validate_user_id was called with repository user_id
                mock_validate.assert_called_once_with("user-123")
                
                # Verify context was created with correct user_id
                mock_facade.create_context.assert_called_once()
                context_call = mock_facade.create_context.call_args[1]
                assert context_call["data"]["user_id"] == "user-123"

    @pytest.mark.asyncio
    async def test_create_project_repository_without_user_id(self):
        """Test fallback behavior when repository lacks user_id."""
        # Ensure repository doesn't have user_id attribute
        if hasattr(self.mock_repository, 'user_id'):
            delattr(self.mock_repository, 'user_id')
        
        use_case = CreateProjectUseCase(self.mock_repository)
        
        with patch("fastmcp.config.auth_config.AuthConfig.is_default_user_allowed") as mock_auth:
            mock_auth.return_value = True  # Compatibility mode
            
            with patch("fastmcp.config.auth_config.AuthConfig.log_authentication_bypass") as mock_log:
                result = await use_case.execute(
                    name="Test Project",
                    description="Test Description"
                )
                
                assert result["success"] is True
                
                # Verify compatibility mode was used
                mock_auth.assert_called_once()
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_strict_authentication_mode(self):
        """Test project creation fails when authentication is required."""
        # Ensure repository doesn't have user_id
        if hasattr(self.mock_repository, 'user_id'):
            delattr(self.mock_repository, 'user_id')
        
        use_case = CreateProjectUseCase(self.mock_repository)
        
        with patch("fastmcp.config.auth_config.AuthConfig.is_default_user_allowed") as mock_auth:
            mock_auth.return_value = False  # Strict mode
            
            # Should still succeed but without context creation
            result = await use_case.execute(
                name="Test Project",
                description="Test Description"
            )
            
            assert result["success"] is True
            assert "Project created successfully" in result["message"]

    @pytest.mark.asyncio 
    async def test_create_project_validate_user_id_failure(self):
        """Test handling when user_id validation fails."""
        self.mock_repository.user_id = "invalid-user"
        
        use_case = CreateProjectUseCase(self.mock_repository)
        
        with patch("fastmcp.task_management.domain.constants.validate_user_id") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid user ID format")
            
            # Should still create project but without context
            result = await use_case.execute(
                name="Test Project", 
                description="Test Description"
            )
            
            assert result["success"] is True
            assert "Project created successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_create_project_context_factory_creation_failure(self):
        """Test handling when context factory creation fails."""
        self.mock_repository.user_id = "user-123"
        
        use_case = CreateProjectUseCase(self.mock_repository)
        
        with patch("fastmcp.task_management.domain.constants.validate_user_id") as mock_validate:
            mock_validate.return_value = None
            
            with patch("fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory") as mock_factory:
                mock_factory.side_effect = Exception("Factory creation failed")
                
                # Should still create project
                result = await use_case.execute(
                    name="Test Project",
                    description="Test Description"
                )
                
                assert result["success"] is True
                assert "Project created successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_create_project_logs_authentication_bypass(self):
        """Test that authentication bypass is logged in compatibility mode."""
        if hasattr(self.mock_repository, 'user_id'):
            delattr(self.mock_repository, 'user_id')
        
        use_case = CreateProjectUseCase(self.mock_repository)
        
        with patch("fastmcp.config.auth_config.AuthConfig.is_default_user_allowed") as mock_auth:
            mock_auth.return_value = True
            
            with patch("fastmcp.config.auth_config.AuthConfig.log_authentication_bypass") as mock_log:
                with patch("fastmcp.config.auth_config.AuthConfig.get_default_user_id") as mock_default:
                    mock_default.return_value = "default_user"
                    
                    result = await use_case.execute(
                        name="Test Project",
                        description="Test Description"
                    )
                    
                    assert result["success"] is True
                    
                    # Verify bypass was logged
                    mock_log.assert_called_once_with(
                        operation="create_project",
                        reason="No authenticated user in repository context"
                    )