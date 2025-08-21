"""Test suite for GitBranchService.

Tests the git branch service including:
- Branch creation with validation
- Branch retrieval
- Branch listing
- Branch deletion
- Branch context creation
- User context handling
- Error scenarios
"""

import pytest
import logging
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
import uuid

from fastmcp.task_management.application.services.git_branch_service import GitBranchService
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch
from fastmcp.task_management.domain.repositories.project_repository import ProjectRepository
from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService


class TestGitBranchService:
    """Test cases for GitBranchService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock repositories
        self.mock_project_repo = Mock(spec=ProjectRepository)
        self.mock_context_service = Mock(spec=UnifiedContextService)
        
        # Create test data
        self.test_user_id = "test-user-123"
        self.test_project_id = str(uuid.uuid4())
        self.test_project = Project(
            id=self.test_project_id,
            name="Test Project",
            description="Test project description",
            user_id=self.test_user_id
        )
        
        # Setup async methods
        self.mock_project_repo.find_by_id = AsyncMock(return_value=self.test_project)
        self.mock_project_repo.update = AsyncMock(return_value=self.test_project)
        
        # Mock context service methods
        self.mock_context_service.create_context = AsyncMock(return_value={
            "success": True,
            "context": {"id": str(uuid.uuid4())}
        })
        self.mock_context_service.delete_context = AsyncMock(return_value={
            "success": True
        })
        
        # Create service instance
        self.service = GitBranchService(
            project_repo=self.mock_project_repo,
            hierarchical_context_service=self.mock_context_service,
            user_id=self.test_user_id
        )
    
    def test_init_with_user_id(self):
        """Test service initialization with user ID."""
        service = GitBranchService(user_id=self.test_user_id)
        assert service._user_id == self.test_user_id
    
    def test_init_with_project_repo(self):
        """Test service initialization with project repository."""
        service = GitBranchService(
            project_repo=self.mock_project_repo,
            user_id=self.test_user_id
        )
        assert service._project_repo == self.mock_project_repo
    
    @patch('fastmcp.task_management.application.services.git_branch_service.GlobalRepositoryManager')
    def test_init_with_user_id_creates_user_repo(self, mock_repo_manager):
        """Test that initializing with user_id creates user-specific repository."""
        mock_user_repo = Mock()
        mock_repo_manager.get_for_user.return_value = mock_user_repo
        
        service = GitBranchService(user_id=self.test_user_id)
        
        mock_repo_manager.get_for_user.assert_called_once_with(self.test_user_id)
        assert service._project_repo == mock_user_repo
    
    @patch('fastmcp.task_management.application.services.git_branch_service.GlobalRepositoryManager')
    def test_init_without_user_id_uses_default_repo(self, mock_repo_manager):
        """Test that initializing without user_id uses default repository."""
        mock_default_repo = Mock()
        mock_repo_manager.get_default.return_value = mock_default_repo
        
        service = GitBranchService()
        
        mock_repo_manager.get_default.assert_called_once()
        assert service._project_repo == mock_default_repo
    
    def test_with_user_creates_new_instance(self):
        """Test that with_user creates a new service instance."""
        new_user_id = "new-user-456"
        new_service = self.service.with_user(new_user_id)
        
        assert new_service is not self.service
        assert new_service._user_id == new_user_id
        assert new_service._project_repo == self.service._project_repo
        assert new_service._hierarchical_context_service == self.service._hierarchical_context_service
    
    def test_get_user_scoped_repository_with_user(self):
        """Test getting user-scoped repository when user_id is set."""
        mock_repo = Mock()
        mock_repo.with_user = Mock(return_value="scoped_repo")
        
        result = self.service._get_user_scoped_repository(mock_repo)
        
        mock_repo.with_user.assert_called_once_with(self.test_user_id)
        assert result == "scoped_repo"
    
    def test_get_user_scoped_repository_without_user(self):
        """Test getting repository when user_id is not set."""
        service = GitBranchService(
            project_repo=self.mock_project_repo,
            hierarchical_context_service=self.mock_context_service,
            user_id=None
        )
        mock_repo = Mock()
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_repo
    
    @pytest.mark.asyncio
    async def test_create_git_branch_success(self):
        """Test successful git branch creation."""
        branch_name = "feature/test-branch"
        description = "Test branch description"
        
        # Mock git branch repository
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_name = AsyncMock(return_value=None)
        
        test_branch = GitBranch(
            id=str(uuid.uuid4()),
            name=branch_name,
            description=description,
            project_id=self.test_project_id
        )
        mock_git_branch_repo.create_branch = AsyncMock(return_value=test_branch)
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.create_git_branch(
                self.test_project_id,
                branch_name,
                description
            )
        
        assert result["success"] is True
        assert result["git_branch"]["name"] == branch_name
        assert result["git_branch"]["description"] == description
        assert result["git_branch"]["project_id"] == self.test_project_id
        assert "message" in result
        
        # Verify repository calls
        mock_git_branch_repo.find_by_name.assert_called_once_with(
            self.test_project_id, branch_name
        )
        mock_git_branch_repo.create_branch.assert_called_once_with(
            self.test_project_id, branch_name, description
        )
        
        # Verify context creation
        self.mock_context_service.create_context.assert_called_once()
        context_call_args = self.mock_context_service.create_context.call_args
        assert context_call_args[1]["level"] == "branch"
        assert context_call_args[1]["context_id"] == test_branch.id
        
        # Verify project update
        self.mock_project_repo.update.assert_called_once_with(self.test_project)
    
    @pytest.mark.asyncio
    async def test_create_git_branch_project_not_found(self):
        """Test git branch creation when project doesn't exist."""
        self.mock_project_repo.find_by_id.return_value = None
        
        result = await self.service.create_git_branch(
            self.test_project_id,
            "feature/test",
            "Description"
        )
        
        assert result["success"] is False
        assert f"Project {self.test_project_id} not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_git_branch_already_exists(self):
        """Test git branch creation when branch already exists."""
        branch_name = "feature/existing"
        
        # Mock existing branch
        existing_branch = GitBranch(
            id=str(uuid.uuid4()),
            name=branch_name,
            description="Existing branch",
            project_id=self.test_project_id
        )
        
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_name = AsyncMock(return_value=existing_branch)
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.create_git_branch(
                self.test_project_id,
                branch_name,
                "New description"
            )
        
        assert result["success"] is False
        assert f"Git branch '{branch_name}' already exists" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_git_branch_context_creation_fails(self):
        """Test git branch creation continues even if context creation fails."""
        branch_name = "feature/test-branch"
        
        # Mock git branch repository
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_name = AsyncMock(return_value=None)
        
        test_branch = GitBranch(
            id=str(uuid.uuid4()),
            name=branch_name,
            description="Description",
            project_id=self.test_project_id
        )
        mock_git_branch_repo.create_branch = AsyncMock(return_value=test_branch)
        
        # Make context creation fail
        self.mock_context_service.create_context.side_effect = Exception("Context error")
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            with patch('fastmcp.task_management.application.services.git_branch_service.logger') as mock_logger:
                result = await self.service.create_git_branch(
                    self.test_project_id,
                    branch_name,
                    "Description"
                )
        
        # Branch creation should still succeed
        assert result["success"] is True
        assert result["git_branch"]["name"] == branch_name
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Failed to create branch context" in mock_logger.error.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_get_git_branch_success(self):
        """Test successful git branch retrieval."""
        branch_name = "feature/test"
        test_branch = GitBranch(
            id=str(uuid.uuid4()),
            name=branch_name,
            description="Test branch",
            project_id=self.test_project_id
        )
        
        # Add branch to project
        self.test_project.add_git_branch(test_branch)
        
        result = await self.service.get_git_branch(self.test_project_id, branch_name)
        
        assert result["success"] is True
        assert result["git_branch"]["name"] == branch_name
        assert result["git_branch"]["id"] == test_branch.id
    
    @pytest.mark.asyncio
    async def test_get_git_branch_not_found(self):
        """Test git branch retrieval when branch doesn't exist."""
        branch_name = "feature/nonexistent"
        
        result = await self.service.get_git_branch(self.test_project_id, branch_name)
        
        assert result["success"] is False
        assert f"Git branch '{branch_name}' not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_git_branchs_success(self):
        """Test listing all git branches in a project."""
        # Add test branches
        branches = []
        for i in range(3):
            branch = GitBranch(
                id=str(uuid.uuid4()),
                name=f"feature/branch-{i}",
                description=f"Branch {i}",
                project_id=self.test_project_id
            )
            self.test_project.add_git_branch(branch)
            branches.append(branch)
        
        result = await self.service.list_git_branchs(self.test_project_id)
        
        assert result["success"] is True
        assert len(result["git_branchs"]) == 3
        
        # Verify branch data
        branch_names = [b["name"] for b in result["git_branchs"]]
        assert "feature/branch-0" in branch_names
        assert "feature/branch-1" in branch_names
        assert "feature/branch-2" in branch_names
    
    @pytest.mark.asyncio
    async def test_list_git_branchs_project_not_found(self):
        """Test listing branches when project doesn't exist."""
        self.mock_project_repo.find_by_id.return_value = None
        
        result = await self.service.list_git_branchs(self.test_project_id)
        
        assert result["success"] is False
        assert f"Project {self.test_project_id} not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_git_branch_success(self):
        """Test successful git branch deletion."""
        branch_id = str(uuid.uuid4())
        
        # Mock git branch repository
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.get_git_branch_by_id = AsyncMock(return_value={
            "success": True,
            "git_branch": {
                "id": branch_id,
                "project_id": self.test_project_id,
                "name": "feature/to-delete"
            }
        })
        mock_git_branch_repo.delete_branch = AsyncMock()
        
        # Add branch to project
        test_branch = GitBranch(
            id=branch_id,
            name="feature/to-delete",
            description="Branch to delete",
            project_id=self.test_project_id
        )
        self.test_project.add_git_branch(test_branch)
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.delete_git_branch(branch_id)
        
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        
        # Verify repository calls
        mock_git_branch_repo.get_git_branch_by_id.assert_called_once_with(branch_id)
        mock_git_branch_repo.delete_branch.assert_called_once_with(branch_id)
        
        # Verify context deletion
        self.mock_context_service.delete_context.assert_called_once_with(
            level="branch",
            context_id=branch_id
        )
        
        # Verify project update
        self.mock_project_repo.update.assert_called_once()
        assert branch_id not in self.test_project.git_branchs
    
    @pytest.mark.asyncio
    async def test_delete_git_branch_not_found(self):
        """Test git branch deletion when branch doesn't exist."""
        branch_id = str(uuid.uuid4())
        
        # Mock git branch repository
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.get_git_branch_by_id = AsyncMock(return_value={
            "success": False
        })
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.delete_git_branch(branch_id)
        
        assert result["success"] is False
        assert result["error_code"] == "NOT_FOUND"
        assert f"Git branch {branch_id} not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_git_branch_context_deletion_fails(self):
        """Test git branch deletion continues even if context deletion fails."""
        branch_id = str(uuid.uuid4())
        
        # Mock git branch repository
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.get_git_branch_by_id = AsyncMock(return_value={
            "success": True,
            "git_branch": {
                "id": branch_id,
                "project_id": self.test_project_id,
                "name": "feature/to-delete"
            }
        })
        mock_git_branch_repo.delete_branch = AsyncMock()
        
        # Make context deletion fail
        self.mock_context_service.delete_context.side_effect = Exception("Context error")
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            with patch('fastmcp.task_management.application.services.git_branch_service.logger') as mock_logger:
                result = await self.service.delete_git_branch(branch_id)
        
        # Deletion should still succeed
        assert result["success"] is True
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        assert "Failed to delete branch context" in mock_logger.warning.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_delete_git_branch_exception(self):
        """Test git branch deletion with general exception."""
        branch_id = str(uuid.uuid4())
        
        # Mock git branch repository to raise exception
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.get_git_branch_by_id.side_effect = Exception("Database error")
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.delete_git_branch(branch_id)
        
        assert result["success"] is False
        assert result["error_code"] == "DELETE_FAILED"
        assert "Failed to delete git branch" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_missing_branch_context_success(self):
        """Test creating branch context for existing branch."""
        branch_id = str(uuid.uuid4())
        branch_name = "feature/existing"
        
        # Mock existing branch
        test_branch = GitBranch(
            id=branch_id,
            name=branch_name,
            description="Existing branch",
            project_id=self.test_project_id
        )
        
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_id = AsyncMock(return_value=test_branch)
        
        # Mock synchronous context creation (not async in the actual code)
        self.mock_context_service.create_context = Mock(return_value={
            "success": True,
            "context": {"id": str(uuid.uuid4())}
        })
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.create_missing_branch_context(
                branch_id,
                project_id=self.test_project_id,
                branch_name=branch_name,
                description="Updated description"
            )
        
        assert result["success"] is True
        assert "Branch context created" in result["message"]
        assert "branch_context" in result
        
        # Verify context creation
        self.mock_context_service.create_context.assert_called_once()
        context_call_args = self.mock_context_service.create_context.call_args
        assert context_call_args[1]["level"] == "branch"
        assert context_call_args[1]["context_id"] == branch_id
        assert context_call_args[1]["data"]["parent_project_id"] == self.test_project_id
    
    @pytest.mark.asyncio
    async def test_create_missing_branch_context_branch_not_found(self):
        """Test creating branch context when branch doesn't exist."""
        branch_id = str(uuid.uuid4())
        
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_id = AsyncMock(return_value=None)
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.create_missing_branch_context(branch_id)
        
        assert result["success"] is False
        assert f"Git branch {branch_id} not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_missing_branch_context_uses_branch_data(self):
        """Test that missing parameters are filled from branch data."""
        branch_id = str(uuid.uuid4())
        
        # Mock existing branch
        test_branch = GitBranch(
            id=branch_id,
            name="feature/from-db",
            description="DB description",
            project_id=self.test_project_id
        )
        
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_id = AsyncMock(return_value=test_branch)
        
        # Mock synchronous context creation
        self.mock_context_service.create_context = Mock(return_value={
            "success": True,
            "context": {"id": str(uuid.uuid4())}
        })
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            # Call without optional parameters
            result = await self.service.create_missing_branch_context(branch_id)
        
        assert result["success"] is True
        
        # Verify context was created with branch data
        context_call_args = self.mock_context_service.create_context.call_args
        context_data = context_call_args[1]["data"]
        assert context_data["parent_project_id"] == self.test_project_id
        assert context_data["branch_name"] == "feature/from-db"
        assert context_data["branch_description"] == "DB description"
    
    @pytest.mark.asyncio
    async def test_create_missing_branch_context_exception(self):
        """Test handling exception during context creation."""
        branch_id = str(uuid.uuid4())
        
        # Mock existing branch
        test_branch = GitBranch(
            id=branch_id,
            name="feature/test",
            description="Test branch",
            project_id=self.test_project_id
        )
        
        mock_git_branch_repo = Mock()
        mock_git_branch_repo.find_by_id = AsyncMock(return_value=test_branch)
        
        # Make context creation fail
        self.mock_context_service.create_context = Mock(
            side_effect=Exception("Context creation failed")
        )
        
        with patch.object(self.service, '_git_branch_repo', mock_git_branch_repo):
            result = await self.service.create_missing_branch_context(branch_id)
        
        assert result["success"] is False
        assert "Failed to create branch context" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])