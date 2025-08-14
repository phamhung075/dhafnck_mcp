"""Test for fixing the parameter mismatch in next task operation"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade

class TestNextTaskParameterFix:
    """Test that the next task operation passes correct parameters"""
    
    def test_controller_passes_correct_parameter_to_facade(self):
        """Test that controller passes git_branch_id (not git_branch_name) to facade"""
        # Create mock facade factory
        mock_facade_factory = MagicMock()
        
        # Create controller with mock factory
        controller = TaskMCPController(task_facade_factory=mock_facade_factory)
        
        # Create mock facade
        mock_facade = MagicMock(spec=TaskApplicationFacade)
        
        # Setup async mock for get_next_task
        async def mock_get_next_task(**kwargs):
            # Verify we receive git_branch_id, not git_branch_name
            assert 'git_branch_id' in kwargs, "Facade should receive git_branch_id parameter"
            assert 'git_branch_name' not in kwargs, "Facade should NOT receive git_branch_name parameter"
            
            return {
                "success": True,
                "action": "next",
                "task": {
                    "has_next": True,
                    "next_item": {
                        "type": "task",
                        "task": {"id": "test-task-123", "title": "Test Task"}
                    },
                    "message": "Next task found"
                }
            }
        
        mock_facade.get_next_task = AsyncMock(side_effect=mock_get_next_task)
        
        # Call _handle_next_task
        with patch.object(controller, '_create_facade', return_value=mock_facade):
            result = controller._handle_next_task(
                facade=mock_facade,
                git_branch_id="test-branch-uuid-123",
                include_context=True
            )
        
        # Verify the facade method was called
        mock_facade.get_next_task.assert_called_once()
        
        # Get the call arguments
        call_kwargs = mock_facade.get_next_task.call_args[1]
        
        # Verify git_branch_id was passed (not git_branch_name)
        assert 'git_branch_id' in call_kwargs, "git_branch_id should be passed to facade"
        assert call_kwargs['git_branch_id'] == "test-branch-uuid-123"
        
        # Verify git_branch_name was NOT passed
        assert 'git_branch_name' not in call_kwargs, "git_branch_name should NOT be passed to facade"
    
    def test_facade_signature_expects_git_branch_id(self):
        """Test that the facade's get_next_task method signature expects git_branch_id"""
        import inspect
        
        # Get the signature of the facade's get_next_task method
        sig = inspect.signature(TaskApplicationFacade.get_next_task)
        
        # Check that git_branch_id is in the parameters
        assert 'git_branch_id' in sig.parameters, "Facade method should have git_branch_id parameter"
        
        # Check that git_branch_name is NOT in the parameters
        assert 'git_branch_name' not in sig.parameters, "Facade method should NOT have git_branch_name parameter"
    
    @pytest.mark.asyncio
    async def test_end_to_end_next_task_with_correct_parameters(self):
        """Test end-to-end next task operation with correct parameter passing"""
        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = []
        
        # Create real facade with mock repository
        from fastmcp.task_management.application.use_cases.next_task import NextTaskUseCase
        
        next_use_case = NextTaskUseCase(task_repository=mock_repo)
        
        # Call execute with git_branch_id parameter
        response = await next_use_case.execute(
            git_branch_id="test-branch-uuid",
            include_context=True
        )
        
        # Verify response structure
        assert response is not None
        assert hasattr(response, 'has_next')
        assert response.has_next == False  # No tasks found
        assert response.message == "No tasks found. Create a task to get started!"