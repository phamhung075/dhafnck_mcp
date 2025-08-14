"""
Branch Deletion Fix Validation Tests

These tests verify that the branch deletion fix is working correctly
without requiring database access.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from typing import Dict, Any


class TestBranchDeletionFix:
    """Test suite to validate the branch deletion fix implementation"""
    
    def test_git_branch_service_has_delete_method(self):
        """Verify GitBranchService has the delete_git_branch method"""
        from fastmcp.task_management.application.services.git_branch_service import GitBranchService
        
        # Check that the service has the delete method
        assert hasattr(GitBranchService, 'delete_git_branch')
        
        # Verify it's a callable method
        service = GitBranchService()
        assert callable(getattr(service, 'delete_git_branch', None))
    
    def test_orm_repository_has_delete_branch_method(self):
        """Verify ORMGitBranchRepository has the delete_branch method"""
        from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
        
        # Check that the repository has the delete method
        assert hasattr(ORMGitBranchRepository, 'delete_branch')
        
        # Verify it's a callable method
        repo = ORMGitBranchRepository()
        assert callable(getattr(repo, 'delete_branch', None))
    
    def test_facade_has_delete_method(self):
        """Verify GitBranchApplicationFacade has the delete_git_branch method"""
        from fastmcp.task_management.application.facades.git_branch_application_facade import GitBranchApplicationFacade
        
        # Check that the facade has the delete method
        assert hasattr(GitBranchApplicationFacade, 'delete_git_branch')
        
        # Verify it's a callable method
        facade = GitBranchApplicationFacade()
        assert callable(getattr(facade, 'delete_git_branch', None))
    
    @pytest.mark.asyncio
    async def test_delete_service_method_structure(self):
        """Test the structure of the delete_git_branch service method"""
        from fastmcp.task_management.application.services.git_branch_service import GitBranchService
        
        # Create service with mocked dependencies
        mock_repo = Mock()
        mock_repo.get_git_branch_by_id = AsyncMock(return_value={
            "success": True,
            "git_branch": {"id": "test-id", "project_id": "proj-id"}
        })
        mock_repo.delete_branch = AsyncMock(return_value=True)
        
        mock_context_service = Mock()
        mock_context_service.delete_context = AsyncMock()
        
        service = GitBranchService()
        service._git_branch_repo = mock_repo
        service._hierarchical_context_service = mock_context_service
        
        # Test the delete method
        result = await service.delete_git_branch("test-branch-id")
        
        # Verify it returns expected structure
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] == True
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_delete_handles_not_found(self):
        """Test that delete handles non-existent branches gracefully"""
        from fastmcp.task_management.application.services.git_branch_service import GitBranchService
        
        # Create service with mocked dependencies
        mock_repo = Mock()
        mock_repo.get_git_branch_by_id = AsyncMock(return_value={
            "success": False,
            "error": "Not found"
        })
        
        service = GitBranchService()
        service._git_branch_repo = mock_repo
        
        # Test the delete method with non-existent branch
        result = await service.delete_git_branch("non-existent-id")
        
        # Verify it returns error
        assert isinstance(result, dict)
        assert result["success"] == False
        assert "error" in result
        assert "NOT_FOUND" in result.get("error_code", "")
    
    def test_facade_delete_method_signature(self):
        """Test that facade delete method has correct signature"""
        from fastmcp.task_management.application.facades.git_branch_application_facade import GitBranchApplicationFacade
        import inspect
        
        facade = GitBranchApplicationFacade()
        
        # Get the method signature
        sig = inspect.signature(facade.delete_git_branch)
        
        # Check parameters
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "git_branch_id" in params
        
        # Check return type hint if available
        return_annotation = sig.return_annotation
        if return_annotation != inspect.Signature.empty:
            assert return_annotation == Dict[str, Any]
    
    @patch('asyncio.run')
    @patch('asyncio.get_running_loop')
    def test_facade_handles_async_correctly(self, mock_get_loop, mock_run):
        """Test that facade properly handles async/sync context"""
        from fastmcp.task_management.application.facades.git_branch_application_facade import GitBranchApplicationFacade
        
        # Test when no event loop is running
        mock_get_loop.side_effect = RuntimeError("No event loop")
        mock_run.return_value = {"success": True, "message": "Deleted"}
        
        facade = GitBranchApplicationFacade()
        facade._git_branch_service = Mock()
        facade._git_branch_service.delete_git_branch = AsyncMock(
            return_value={"success": True, "message": "Deleted"}
        )
        
        result = facade.delete_git_branch("test-id")
        
        # Verify asyncio.run was called
        assert mock_run.called
        assert result["success"] == True
    
    def test_repository_delete_branch_cascade(self):
        """Test that repository delete_branch includes cascade logic"""
        from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
        import inspect
        
        repo = ORMGitBranchRepository()
        
        # Get the source code of the delete_branch method
        source = inspect.getsource(repo.delete_branch)
        
        # Verify it includes cascade deletion logic
        assert "Task" in source  # Should reference Task model
        assert "delete()" in source  # Should call delete
        assert "git_branch_id" in source  # Should filter by branch ID


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])