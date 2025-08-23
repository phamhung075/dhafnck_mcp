"""
Integration test to verify that branch contexts are automatically created.

This test verifies the fix for the issue where branch contexts were not
automatically created when branches were created, causing "Context not found" errors.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock

from fastmcp.task_management.application.services.git_branch_service import GitBranchService
from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService


class TestBranchContextCreationFix:
    """Test the fix for automatic branch context creation."""

    @pytest.fixture
    def mock_project_repo(self):
        """Mock project repository."""
        import asyncio
        
        mock_repo = MagicMock()
        mock_project = MagicMock()
        mock_project.id = "test-project-id"
        mock_project.add_git_branch = MagicMock()
        
        # Make async methods return coroutines
        async def mock_find_by_id(project_id):
            return mock_project
            
        async def mock_update(project):
            return project
            
        mock_repo.find_by_id = mock_find_by_id
        mock_repo.update = mock_update
        return mock_repo

    @pytest.fixture
    def mock_git_branch_repo(self):
        """Mock git branch repository."""
        mock_repo = MagicMock()
        mock_git_branch = MagicMock()
        mock_git_branch.id = f"branch-{uuid.uuid4().hex[:8]}"
        mock_git_branch.name = "test-branch"
        mock_git_branch.description = "Test branch"
        mock_git_branch.project_id = "test-project-id"
        
        # Make async methods return coroutines
        async def mock_find_by_name(project_id, branch_name):
            return None  # No existing branch
            
        async def mock_create_branch(project_id, branch_name, description):
            return mock_git_branch
        
        mock_repo.find_by_name = mock_find_by_name
        mock_repo.create_branch = mock_create_branch
        return mock_repo

    @pytest.fixture
    def mock_context_service(self):
        """Mock unified context service."""
        mock_service = MagicMock()
        # Mock successful context creation
        mock_service.create_context.return_value = {
            "success": True,
            "context": {
                "id": "branch-context-id",
                "project_id": "test-project-id",
                "git_branch_name": "test-branch",
                "branch_settings": {},
                "metadata": {"auto_created": True}
            }
        }
        return mock_service

    def test_branch_context_created_during_branch_creation(
        self, mock_project_repo, mock_git_branch_repo, mock_context_service
    ):
        """Test that branch context is created automatically when branch is created."""
        # Create GitBranchService with mocked dependencies
        git_branch_service = GitBranchService(
            project_repo=mock_project_repo,
            hierarchical_context_service=mock_context_service,
            user_id="test-user"
        )
        
        # Replace the git branch repository with our mock
        git_branch_service._git_branch_repo = mock_git_branch_repo
        
        # Create a branch (this should trigger context creation)
        project_id = "test-project-id"
        branch_name = "test-branch"
        description = "Test branch description"
        
        # Run the async method
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                git_branch_service.create_git_branch(
                    project_id=project_id,
                    branch_name=branch_name,
                    description=description
                )
            )
        finally:
            loop.close()
        
        # Verify branch creation succeeded
        assert result["success"] is True
        assert "git_branch" in result
        assert result["git_branch"]["name"] == branch_name
        
        # Verify that context creation was called with correct parameters
        mock_context_service.create_context.assert_called_once()
        call_args = mock_context_service.create_context.call_args
        
        # Check the call arguments
        assert call_args[1]["level"] == "branch"  # level parameter
        assert call_args[1]["project_id"] == project_id  # project_id parameter
        
        # Check the context data structure
        context_data = call_args[1]["data"]
        assert context_data["project_id"] == project_id
        assert context_data["git_branch_name"] == branch_name
        assert "branch_settings" in context_data
        assert "metadata" in context_data
        assert context_data["metadata"]["auto_created"] is True
        assert context_data["metadata"]["created_by"] == "git_branch_service"

    def test_branch_creation_continues_if_context_creation_fails(
        self, mock_project_repo, mock_git_branch_repo, mock_context_service
    ):
        """Test that branch creation succeeds even if context creation fails."""
        # Make context creation fail
        mock_context_service.create_context.return_value = {
            "success": False,
            "error": "Context creation failed"
        }
        
        # Create GitBranchService with mocked dependencies
        git_branch_service = GitBranchService(
            project_repo=mock_project_repo,
            hierarchical_context_service=mock_context_service,
            user_id="test-user"
        )
        
        # Replace the git branch repository with our mock
        git_branch_service._git_branch_repo = mock_git_branch_repo
        
        # Create a branch
        project_id = "test-project-id"
        branch_name = "test-branch"
        description = "Test branch description"
        
        # Run the async method
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                git_branch_service.create_git_branch(
                    project_id=project_id,
                    branch_name=branch_name,
                    description=description
                )
            )
        finally:
            loop.close()
        
        # Verify branch creation still succeeded despite context creation failure
        assert result["success"] is True
        assert "git_branch" in result
        assert result["git_branch"]["name"] == branch_name
        
        # Verify that context creation was attempted
        mock_context_service.create_context.assert_called_once()

    def test_branch_context_data_structure_is_correct(
        self, mock_project_repo, mock_git_branch_repo, mock_context_service
    ):
        """Test that the branch context data structure matches UnifiedContextService expectations."""
        git_branch_service = GitBranchService(
            project_repo=mock_project_repo,
            hierarchical_context_service=mock_context_service,
            user_id="test-user"
        )
        
        git_branch_service._git_branch_repo = mock_git_branch_repo
        
        project_id = "test-project-id"
        branch_name = "feature/new-feature"
        description = "Feature branch for new functionality"
        
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                git_branch_service.create_git_branch(
                    project_id=project_id,
                    branch_name=branch_name,
                    description=description
                )
            )
        finally:
            loop.close()
        
        # Verify branch creation succeeded
        assert result["success"] is True
        
        # Check the context creation call
        mock_context_service.create_context.assert_called_once()
        call_args = mock_context_service.create_context.call_args
        
        # Verify the data structure matches BranchContext requirements
        context_data = call_args[1]["data"]
        
        # Required fields for BranchContext
        assert "project_id" in context_data
        assert "git_branch_name" in context_data
        assert "branch_settings" in context_data
        assert "metadata" in context_data
        
        # Check specific values
        assert context_data["project_id"] == project_id
        assert context_data["git_branch_name"] == branch_name
        assert context_data["metadata"]["branch_description"] == description
        assert context_data["metadata"]["auto_created"] is True
        
        # Check branch_settings structure
        branch_settings = context_data["branch_settings"]
        expected_settings = [
            "feature_flags", "branch_workflow", "testing_strategy",
            "deployment_config", "collaboration_settings", "agent_assignments"
        ]
        for setting in expected_settings:
            assert setting in branch_settings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])