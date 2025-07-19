"""Test auto-context creation when creating git branches"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastmcp.task_management.application.use_cases.create_git_branch import CreateGitBranchUseCase
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch


class TestBranchAutoContext:
    """Test auto-context creation for git branches"""
    
    @pytest.mark.asyncio
    async def test_create_branch_auto_creates_context(self):
        """Test that creating a branch automatically creates branch context"""
        # Arrange
        project_id = "proj-123"
        branch_id = "branch-456"
        
        # Create mock project
        project = Project(
            id=project_id,
            name="Test Project",
            description="Test Description",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create mock repository
        mock_project_repo = AsyncMock()
        mock_project_repo.find_by_id.return_value = project
        mock_project_repo.update = AsyncMock()
        
        # Mock the branch creation
        mock_branch = GitBranch(
            id=branch_id,
            name="Feature Branch",
            description="Test branch",
            project_id=project_id,
            created_at=datetime.now(timezone.utc)
        )
        
        # Override the create_git_branch method to return our mock branch
        original_create = project.create_git_branch
        def mock_create_git_branch(git_branch_name, name, description):
            mock_branch.git_branch_name = git_branch_name
            project.git_branchs[branch_id] = mock_branch
            return mock_branch
        project.create_git_branch = mock_create_git_branch
        
        # Create use case
        use_case = CreateGitBranchUseCase(mock_project_repo)
        
        # Mock context facade
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory_class:
            mock_facade = MagicMock()
            mock_facade.create_context.return_value = {"success": True}
            
            mock_factory = MagicMock()
            mock_factory.create_facade.return_value = mock_facade
            mock_factory_class.return_value = mock_factory
            
            # Act
            result = await use_case.execute(
                project_id=project_id,
                git_branch_name="feature-branch",
                branch_name="Feature Branch",
                branch_description="Test branch"
            )
        
        # Assert
        assert result["success"] is True
        assert result["git_branch"]["id"] == branch_id
        
        # Verify context creation was attempted
        mock_factory.create_facade.assert_called_once_with(
            user_id="default_id",
            project_id=project_id,
            git_branch_id=branch_id
        )
        
        # Verify context was created with correct data
        mock_facade.create_context.assert_called_once()
        context_call = mock_facade.create_context.call_args
        assert context_call[1]["level"] == "branch"
        assert context_call[1]["context_id"] == branch_id
        assert context_call[1]["data"]["branch_id"] == branch_id
        assert context_call[1]["data"]["project_id"] == project_id
    
    @pytest.mark.asyncio
    async def test_create_branch_continues_on_context_failure(self):
        """Test that branch creation continues even if context creation fails"""
        # Arrange
        project_id = "proj-123"
        branch_id = "branch-456"
        
        # Create mock project
        project = Project(
            id=project_id,
            name="Test Project",
            description="Test Description",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create mock repository
        mock_project_repo = AsyncMock()
        mock_project_repo.find_by_id.return_value = project
        mock_project_repo.update = AsyncMock()
        
        # Mock the branch creation
        mock_branch = GitBranch(
            id=branch_id,
            name="Feature Branch",
            description="Test branch",
            project_id=project_id,
            created_at=datetime.now(timezone.utc)
        )
        
        # Override the create_git_branch method
        original_create = project.create_git_branch
        def mock_create_git_branch(git_branch_name, name, description):
            mock_branch.git_branch_name = git_branch_name
            project.git_branchs[branch_id] = mock_branch
            return mock_branch
        project.create_git_branch = mock_create_git_branch
        
        # Create use case
        use_case = CreateGitBranchUseCase(mock_project_repo)
        
        # Mock context facade to fail
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory_class:
            mock_facade = MagicMock()
            mock_facade.create_context.return_value = {"success": False, "error": "Context creation failed"}
            
            mock_factory = MagicMock()
            mock_factory.create_facade.return_value = mock_facade
            mock_factory_class.return_value = mock_factory
            
            # Act
            result = await use_case.execute(
                project_id=project_id,
                git_branch_name="feature-branch",
                branch_name="Feature Branch",
                branch_description="Test branch"
            )
        
        # Assert - Branch creation should still succeed
        assert result["success"] is True
        assert result["git_branch"]["id"] == branch_id
        assert "message" in result
        
        # Verify context creation was attempted
        mock_factory.create_facade.assert_called_once()
        mock_facade.create_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_branch_handles_context_exception(self):
        """Test that branch creation handles exceptions during context creation"""
        # Arrange
        project_id = "proj-123"
        branch_id = "branch-456"
        
        # Create mock project
        project = Project(
            id=project_id,
            name="Test Project",
            description="Test Description",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create mock repository
        mock_project_repo = AsyncMock()
        mock_project_repo.find_by_id.return_value = project
        mock_project_repo.update = AsyncMock()
        
        # Mock the branch creation
        mock_branch = GitBranch(
            id=branch_id,
            name="Feature Branch",
            description="Test branch",
            project_id=project_id,
            created_at=datetime.now(timezone.utc)
        )
        
        # Override the create_git_branch method
        original_create = project.create_git_branch
        def mock_create_git_branch(git_branch_name, name, description):
            mock_branch.git_branch_name = git_branch_name
            project.git_branchs[branch_id] = mock_branch
            return mock_branch
        project.create_git_branch = mock_create_git_branch
        
        # Create use case
        use_case = CreateGitBranchUseCase(mock_project_repo)
        
        # Mock context facade to raise exception
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory_class:
            mock_factory_class.side_effect = Exception("Context system unavailable")
            
            # Act
            result = await use_case.execute(
                project_id=project_id,
                git_branch_name="feature-branch",
                branch_name="Feature Branch",
                branch_description="Test branch"
            )
        
        # Assert - Branch creation should still succeed
        assert result["success"] is True
        assert result["git_branch"]["id"] == branch_id
        assert "message" in result