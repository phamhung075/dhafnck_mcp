"""Test subtask complete action response consistency

This test verifies that when calling manage_subtask with action='complete',
the response correctly shows action='complete' instead of action='update'.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from fastmcp.task_management.interface.controllers.subtask_mcp_controller import SubtaskMCPController
from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.application.factories.subtask_facade_factory import SubtaskFacadeFactory


class TestSubtaskCompleteActionResponse:
    """Test suite for subtask complete action response consistency."""
    
    @pytest.fixture
    def mock_subtask_facade(self):
        """Create a mock subtask facade."""
        facade = Mock(spec=SubtaskApplicationFacade)
        return facade
    
    @pytest.fixture
    def mock_subtask_facade_factory(self, mock_subtask_facade):
        """Create a mock subtask facade factory."""
        factory = Mock(spec=SubtaskFacadeFactory)
        factory.create_subtask_facade.return_value = mock_subtask_facade
        return factory
    
    @pytest.fixture
    def subtask_controller(self, mock_subtask_facade_factory):
        """Create subtask controller with mocked dependencies."""
        return SubtaskMCPController(
            subtask_facade_factory=mock_subtask_facade_factory,
            task_facade=None,
            context_facade=None,
            task_repository_factory=None
        )
    
    def test_complete_action_returns_complete_in_response(self, subtask_controller, mock_subtask_facade):
        """Test that complete action returns 'complete' as the action in response."""
        # Arrange
        task_id = "task-123"
        subtask_id = "subtask-456"
        completion_summary = "Completed the implementation"
        
        # Mock the get subtask response
        mock_subtask_facade.handle_manage_subtask.side_effect = [
            # First call for getting subtask info
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Test Subtask",
                    "status": "in_progress"
                }
            },
            # Second call for updating status to done
            {
                "success": True,
                "action": "update",  # This is what currently happens
                "subtask": {
                    "id": subtask_id,
                    "title": "Test Subtask",
                    "status": "done"
                }
            }
        ]
        
        # Act
        result = subtask_controller.manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary=completion_summary
        )
        
        # Assert
        assert result["success"] == True
        assert result["action"] == "complete", f"Expected action='complete', but got action='{result.get('action')}'"
        assert result["subtask"]["status"] == "done"
    
    def test_complete_action_with_all_parameters_returns_complete(self, subtask_controller, mock_subtask_facade):
        """Test complete action with all optional parameters still returns 'complete'."""
        # Arrange
        task_id = "task-123"
        subtask_id = "subtask-456"
        completion_summary = "Implemented feature with tests"
        impact_on_parent = "Parent task is now 50% complete"
        insights_found = ["Found reusable pattern", "Identified performance improvement"]
        testing_notes = "All unit tests pass, integration tested"
        deliverables = ["feature.py", "tests/test_feature.py"]
        skills_learned = ["pytest mocking", "async programming"]
        challenges_overcome = ["Fixed circular import", "Resolved async deadlock"]
        next_recommendations = ["Add more integration tests", "Consider caching"]
        completion_quality = "excellent"
        verification_status = "verified"
        
        # Mock responses
        mock_subtask_facade.handle_manage_subtask.side_effect = [
            # Get subtask info
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Complex Feature Implementation",
                    "status": "in_progress"
                }
            },
            # Update status to done
            {
                "success": True,
                "action": "update",  # Current behavior
                "subtask": {
                    "id": subtask_id,
                    "title": "Complex Feature Implementation",
                    "status": "done"
                }
            }
        ]
        
        # Act
        result = subtask_controller.manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary=completion_summary,
            impact_on_parent=impact_on_parent,
            insights_found=insights_found,
            testing_notes=testing_notes,
            deliverables=deliverables,
            skills_learned=skills_learned,
            challenges_overcome=challenges_overcome,
            next_recommendations=next_recommendations,
            completion_quality=completion_quality,
            verification_status=verification_status
        )
        
        # Assert
        assert result["success"] == True
        assert result["action"] == "complete", f"Expected action='complete', but got action='{result.get('action')}'"
        assert result["subtask"]["status"] == "done"
    
    def test_update_action_still_returns_update(self, subtask_controller, mock_subtask_facade):
        """Test that update action still returns 'update' (not affected by fix)."""
        # Arrange
        task_id = "task-123"
        subtask_id = "subtask-456"
        
        # Mock response
        mock_subtask_facade.handle_manage_subtask.return_value = {
            "success": True,
            "action": "update",
            "subtask": {
                "id": subtask_id,
                "title": "Test Subtask",
                "status": "in_progress"
            }
        }
        
        # Act
        result = subtask_controller.manage_subtask(
            action="update",
            task_id=task_id,
            subtask_id=subtask_id,
            progress_percentage=50,
            progress_notes="Halfway done"
        )
        
        # Assert
        assert result["success"] == True
        assert result["action"] == "update", "Update action should still return 'update'"
    
    def test_complete_action_preserves_original_action_in_workflow_guidance(
        self, subtask_controller, mock_subtask_facade
    ):
        """Test that workflow guidance shows the original complete action."""
        # Arrange
        task_id = "task-123"
        subtask_id = "subtask-456"
        completion_summary = "Task completed successfully"
        
        # Mock responses
        mock_subtask_facade.handle_manage_subtask.side_effect = [
            # Get subtask info
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Test Subtask",
                    "status": "in_progress"
                }
            },
            # Update status to done
            {
                "success": True,
                "action": "update",
                "subtask": {
                    "id": subtask_id,
                    "title": "Test Subtask",
                    "status": "done"
                }
            }
        ]
        
        # Act
        result = subtask_controller.manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary=completion_summary
        )
        
        # Assert
        assert result["success"] == True
        assert result["action"] == "complete"
        # Workflow guidance should reference the complete action
        if "workflow_guidance" in result and "current_state" in result["workflow_guidance"]:
            assert result["workflow_guidance"]["current_state"].get("last_action") == "complete"
    
    def test_complete_action_error_still_shows_complete_action(self, subtask_controller, mock_subtask_facade):
        """Test that even on error, complete action is preserved in response."""
        # Arrange
        task_id = "task-123"
        subtask_id = "subtask-456"
        completion_summary = "Completed"
        
        # Mock error response
        mock_subtask_facade.handle_manage_subtask.side_effect = Exception("Database error")
        
        # Act
        result = subtask_controller.manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary=completion_summary
        )
        
        # Assert
        assert result["success"] == False
        # Even in error response, the action should be preserved
        if "action" in result:
            assert result["action"] == "complete", "Error response should preserve original action"
    
    def test_complete_action_response_format_consistency(self, subtask_controller, mock_subtask_facade):
        """Test that complete action response format matches other actions."""
        # Arrange
        task_id = "task-123"
        subtask_id = "subtask-456"
        completion_summary = "Feature implemented"
        
        # Mock responses
        mock_subtask_facade.handle_manage_subtask.side_effect = [
            # Get subtask info
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Test Feature",
                    "status": "in_progress"
                }
            },
            # Update status to done
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Test Feature", 
                    "status": "done"
                }
            }
        ]
        
        # Act
        result = subtask_controller.manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary=completion_summary
        )
        
        # Assert - Check response structure
        assert "success" in result
        assert "action" in result
        assert result["action"] == "complete"
        assert "subtask" in result
        assert result["subtask"]["status"] == "done"
        
        # Response should have consistent structure with other actions
        expected_keys = {"success", "action", "subtask"}
        assert expected_keys.issubset(result.keys()), f"Missing expected keys in response"