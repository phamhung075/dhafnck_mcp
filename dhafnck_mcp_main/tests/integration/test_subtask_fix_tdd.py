"""
Test-Driven Development (TDD) tests for Subtask Management Fix
==============================================================

This test file follows TDD principles to fix the subtask management issues:
1. Write tests for expected behavior FIRST
2. Tests should FAIL initially (proving the bug exists)
3. Implement the fix
4. Tests should PASS after fix

Issue: Subtask creation and operations fail with:
"Subtask.__init__() got an unexpected keyword argument 'task_id'"

Root Cause: Mismatch between parameter names - controller passes 'task_id' 
but Subtask entity expects 'parent_task_id'
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, patch

# Import the components we're testing
from fastmcp.task_management.interface.controllers.subtask_mcp_controller import SubtaskMCPController
from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.application.factories.subtask_facade_factory import SubtaskFacadeFactory
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestSubtaskManagementTDD:
    """TDD tests for subtask management functionality"""
    
    # Test 1: Basic Subtask Creation
    def test_subtask_creation_should_work_with_mcp_controller(self):
        """
        GIVEN: A valid task ID and subtask details
        WHEN: Creating a subtask through MCP controller
        THEN: Subtask should be created successfully with correct data
        """
        # Arrange
        task_id = "2f19488a-54c1-43d9-8895-2b3c56bc18e2"
        subtask_title = "Create JWT token generation function"
        subtask_description = "Implement secure JWT token generation with proper claims and expiration"
        
        # Create mock dependencies
        mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        mock_facade = Mock(spec=SubtaskApplicationFacade)
        mock_context_facade = Mock()
        
        # Configure mock factory to return mock facade
        mock_facade_factory.create_subtask_facade.return_value = mock_facade
        
        # Configure successful subtask creation response
        created_subtask = {
            "id": "6aa60ebb-3aec-4a0e-bf33-c92f548a5444",
            "title": subtask_title,
            "description": subtask_description,
            "parent_task_id": task_id,
            "status": "todo",
            "priority": "medium",
            "assignees": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": created_subtask,
            "progress": {
                "total": 0,
                "completed": 0,
                "percentage": 0
            }
        }
        
        # Mock context update
        mock_context_facade.add_progress.return_value = {"success": True}
        
        # Create controller
        controller = SubtaskMCPController(
            subtask_facade_factory=mock_facade_factory,
            context_facade=mock_context_facade
        )
        
        # Act
        result = controller.manage_subtask(
            action="create",
            task_id=task_id,
            title=subtask_title,
            description=subtask_description
        )
        
        # Assert
        assert result["success"] is True
        assert "subtask" in result["data"]
        assert result["data"]["subtask"]["title"] == subtask_title
        assert result["data"]["subtask"]["description"] == subtask_description
        assert result["data"]["subtask"]["parent_task_id"] == task_id
        assert result["data"]["context_updated"] is True
        
        # Verify facade was called correctly (called twice - create and list for progress)
        calls = mock_facade.handle_manage_subtask.call_args_list
        assert len(calls) == 2
        
        # First call should be create
        assert calls[0][1] == {
            "action": "create",
            "task_id": task_id,
            "subtask_data": {
                "title": subtask_title,
                "description": subtask_description,
                "priority": None,
                "assignees": None
            }
        }
        
        # Second call should be list (for parent progress calculation)
        assert calls[1][1] == {
            "action": "list",
            "task_id": task_id
        }
        
        # Verify context was updated
        mock_context_facade.add_progress.assert_called_once()
    
    # Test 2: Subtask Entity Parameter Fix
    def test_subtask_entity_should_accept_parent_task_id_not_task_id(self):
        """
        GIVEN: Subtask creation parameters
        WHEN: Creating a Subtask entity instance
        THEN: Should use parent_task_id parameter, not task_id
        """
        # Arrange
        parent_task_id = TaskId("2f19488a-54c1-43d9-8895-2b3c56bc18e2")
        subtask_id = SubtaskId("6aa60ebb-3aec-4a0e-bf33-c92f548a5444")
        
        # Act - This should NOT raise an error
        subtask = Subtask(
            id=subtask_id,
            title="Test subtask",
            description="Test description",
            parent_task_id=parent_task_id,  # Correct parameter name
            status=TaskStatus.todo(),
            priority=Priority.medium()
        )
        
        # Assert
        assert subtask.parent_task_id == parent_task_id
        assert subtask.title == "Test subtask"
        assert subtask.description == "Test description"
        assert subtask.status == TaskStatus.todo()
        assert subtask.priority == Priority.medium()
        
        # This should raise an error (proving the parameter name issue)
        with pytest.raises(TypeError) as exc_info:
            Subtask(
                id=subtask_id,
                title="Test subtask",
                description="Test description",
                task_id=parent_task_id,  # Wrong parameter name - should fail
                status=TaskStatus.todo(),
                priority=Priority.medium()
            )
        assert "unexpected keyword argument 'task_id'" in str(exc_info.value)
    
    # Test 3: Subtask Update with Progress
    def test_subtask_update_with_progress_percentage(self):
        """
        GIVEN: An existing subtask
        WHEN: Updating with progress percentage
        THEN: Status should auto-map based on percentage and context should update
        """
        # Arrange
        task_id = "2f19488a-54c1-43d9-8895-2b3c56bc18e2"
        subtask_id = "6aa60ebb-3aec-4a0e-bf33-c92f548a5444"
        
        mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        mock_facade = Mock(spec=SubtaskApplicationFacade)
        mock_context_facade = Mock()
        
        mock_facade_factory.create_subtask_facade.return_value = mock_facade
        
        # Configure successful update response and list response for progress
        updated_subtask = {
            "id": subtask_id,
            "title": "Test subtask",
            "status": "in_progress",
            "parent_task_id": task_id
        }
        
        mock_facade.handle_manage_subtask.side_effect = [
            # First call - update
            {
                "success": True,
                "subtask": updated_subtask
            },
            # Second call - list for progress
            {
                "success": True,
                "subtasks": [updated_subtask]
            }
        ]
        
        mock_context_facade.add_progress.return_value = {"success": True}
        
        controller = SubtaskMCPController(
            subtask_facade_factory=mock_facade_factory,
            context_facade=mock_context_facade
        )
        
        # Act
        result = controller.manage_subtask(
            action="update",
            task_id=task_id,
            subtask_id=subtask_id,
            progress_percentage=50,
            progress_notes="Halfway through implementation"
        )
        
        # Assert
        assert result["success"] is True
        
        # Verify status was auto-mapped from progress percentage
        # Check the first call (update), not the last one (list)
        facade_calls = mock_facade.handle_manage_subtask.call_args_list
        assert len(facade_calls) == 2
        update_call = facade_calls[0]  # First call is update
        assert update_call[1]["action"] == "update"
        assert update_call[1]["task_id"] == task_id
        assert update_call[1]["subtask_data"]["status"] == "in_progress"
        
        # Verify context was updated with progress
        context_call = mock_context_facade.add_progress.call_args[1]
        assert "50%" in context_call["content"]
        assert "Halfway through implementation" in context_call["content"]
    
    # Test 4: Subtask List Operation
    def test_subtask_list_should_return_all_subtasks_with_progress_summary(self):
        """
        GIVEN: A task with multiple subtasks
        WHEN: Listing subtasks
        THEN: Should return all subtasks with progress summary
        """
        # Arrange
        task_id = "220ad0f6-05ed-487b-b95a-387523faea96"
        
        mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        mock_facade = Mock(spec=SubtaskApplicationFacade)
        
        mock_facade_factory.create_subtask_facade.return_value = mock_facade
        
        # Configure list response with multiple subtasks
        mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtasks": [
                {"id": "sub1", "title": "Subtask 1", "status": "done"},
                {"id": "sub2", "title": "Subtask 2", "status": "in_progress"},
                {"id": "sub3", "title": "Subtask 3", "status": "todo"},
                {"id": "sub4", "title": "Subtask 4", "status": "done"},
            ]
        }
        
        controller = SubtaskMCPController(
            subtask_facade_factory=mock_facade_factory
        )
        
        # Act
        result = controller.manage_subtask(
            action="list",
            task_id=task_id
        )
        
        # Assert
        assert result["success"] is True
        assert len(result["subtasks"]) == 4
        
        # Check progress summary
        progress = result["progress_summary"]
        assert progress["total_subtasks"] == 4
        assert progress["completed"] == 2
        assert progress["in_progress"] == 1
        assert progress["pending"] == 1
        assert progress["completion_percentage"] == 50.0
        assert "2/4 subtasks complete (50.0%)" in progress["summary"]
    
    # Test 5: Subtask Completion with Enhanced Context
    def test_subtask_completion_with_comprehensive_context(self):
        """
        GIVEN: A subtask ready for completion
        WHEN: Completing with full context (summary, testing, deliverables, etc.)
        THEN: Should update status and capture all context in parent task
        """
        # Arrange
        task_id = "2f19488a-54c1-43d9-8895-2b3c56bc18e2"
        subtask_id = "6aa60ebb-3aec-4a0e-bf33-c92f548a5444"
        
        mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        mock_facade = Mock(spec=SubtaskApplicationFacade)
        mock_context_facade = Mock()
        
        mock_facade_factory.create_subtask_facade.return_value = mock_facade
        
        # Configure get and update responses
        mock_facade.handle_manage_subtask.side_effect = [
            # First call - get subtask info
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Create JWT token generation",
                    "parent_task_id": task_id
                }
            },
            # Second call - update status to done
            {
                "success": True,
                "subtask": {
                    "id": subtask_id,
                    "title": "Create JWT token generation",
                    "status": "done"
                }
            },
            # Third call - list for checking all complete
            {
                "success": True,
                "subtasks": [
                    {"id": subtask_id, "status": "done"}
                ]
            },
            # Fourth call - list for parent progress
            {
                "success": True,
                "subtasks": [
                    {"id": subtask_id, "status": "done"}
                ]
            }
        ]
        
        mock_context_facade.add_progress.return_value = {"success": True}
        mock_context_facade.merge_context.return_value = {"success": True}
        
        controller = SubtaskMCPController(
            subtask_facade_factory=mock_facade_factory,
            context_facade=mock_context_facade
        )
        
        # Act
        result = controller.manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_id=subtask_id,
            completion_summary="Successfully implemented JWT token generation with RS256 algorithm",
            testing_notes="Unit tests added with 100% coverage, tested token expiration and validation",
            deliverables=["jwt_service.py", "jwt_service_test.py", "jwt_config.yaml"],
            skills_learned=["JWT best practices", "RS256 vs HS256 algorithms"],
            challenges_overcome=["Handled token refresh edge cases", "Fixed timezone issues"],
            next_recommendations=["Add token revocation list", "Implement JWT rotation"],
            completion_quality="excellent",
            verification_status="verified"
        )
        
        # Assert
        assert result["success"] is True
        assert result["context_updated"] is True
        assert "parent_completion_ready" in result
        assert result["parent_completion_ready"] is True  # All subtasks complete
        
        # Verify context updates were comprehensive
        progress_calls = mock_context_facade.add_progress.call_args_list
        assert len(progress_calls) >= 4  # Multiple progress updates
        
        # Check that various aspects were captured
        all_progress_content = " ".join([call[1]["content"] for call in progress_calls])
        assert "JWT token generation" in all_progress_content
        assert "Unit tests" in all_progress_content
        assert "Deliverables:" in all_progress_content
        assert "Quality: excellent" in all_progress_content
        assert "Verification: verified" in all_progress_content
    
    # Test 6: Error Handling - Missing Required Fields
    def test_error_handling_for_missing_required_fields(self):
        """
        GIVEN: Invalid subtask operation requests
        WHEN: Required fields are missing
        THEN: Should return appropriate error messages
        """
        mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        controller = SubtaskMCPController(subtask_facade_factory=mock_facade_factory)
        
        # Test 1: Create without title
        result = controller.manage_subtask(
            action="create",
            task_id="task-123"
            # Missing title
        )
        assert result["success"] is False
        assert "Missing required field: title" in result["error"]
        
        # Test 2: Update without subtask_id
        result = controller.manage_subtask(
            action="update",
            task_id="task-123",
            # Missing subtask_id
            progress_percentage=50
        )
        assert result["success"] is False
        assert "Missing required field: subtask_id" in result["error"]
        
        # Test 3: Complete without completion_summary
        result = controller.manage_subtask(
            action="complete",
            task_id="task-123",
            subtask_id="sub-123"
            # Missing completion_summary
        )
        assert result["success"] is False
        assert "Missing required field: completion_summary" in result["error"]
    
    # Test 7: Parameter Type Validation
    def test_parameter_type_validation_and_coercion(self):
        """
        GIVEN: Parameters with various types
        WHEN: Processing subtask operations
        THEN: Should validate and coerce types appropriately
        """
        mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        mock_facade = Mock(spec=SubtaskApplicationFacade)
        mock_facade_factory.create_subtask_facade.return_value = mock_facade
        
        # Configure mock to succeed
        mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": "sub-123"}
        }
        
        controller = SubtaskMCPController(subtask_facade_factory=mock_facade_factory)
        
        # Test 1: Progress percentage as string (should coerce to int)
        result = controller.manage_subtask(
            action="update",
            task_id="task-123",
            subtask_id="sub-123",
            progress_percentage="75"  # String instead of int
        )
        assert result["success"] is True
        # Verify it was coerced and status was set
        facade_call = mock_facade.handle_manage_subtask.call_args[1]
        assert facade_call["subtask_data"]["status"] == "in_progress"
        
        # Test 2: Invalid progress percentage string
        result = controller.manage_subtask(
            action="update",
            task_id="task-123",
            subtask_id="sub-123",
            progress_percentage="not-a-number"
        )
        assert result["success"] is False
        assert "Invalid progress_percentage format" in result["error"]
        assert result["error_code"] == "PARAMETER_TYPE_ERROR"
        
        # Test 3: Progress percentage out of range
        result = controller.manage_subtask(
            action="update",
            task_id="task-123",
            subtask_id="sub-123",
            progress_percentage=150  # Out of range
        )
        assert result["success"] is False
        assert "Must be integer between 0-100" in result["error"]
        assert result["error_code"] == "PARAMETER_RANGE_ERROR"
    
    # Test 8: Integration with Task Facade
    def test_subtask_domain_entity_integration(self):
        """
        GIVEN: Subtask domain operations
        WHEN: Using the Subtask entity directly
        THEN: Should work with correct parameter names
        """
        # Create a real subtask entity with valid UUID
        parent_task_id = TaskId("2f19488a-54c1-43d9-8895-2b3c56bc18e2")
        subtask = Subtask(
            title="Integration test subtask",
            description="Testing domain entity",
            parent_task_id=parent_task_id
        )
        
        # Verify creation worked
        assert subtask.title == "Integration test subtask"
        assert subtask.parent_task_id == parent_task_id
        assert subtask.status == TaskStatus.todo()
        assert subtask.priority == Priority.medium()
        
        # Test domain operations
        subtask.update_status(TaskStatus.in_progress())
        assert subtask.status == TaskStatus.in_progress()
        
        subtask.complete()
        assert subtask.is_completed is True
        assert subtask.status == TaskStatus.done()
        
        # Test assignee operations
        subtask.add_assignee("@developer1")
        assert "@developer1" in subtask.assignees
        
        # Test to_dict conversion
        subtask_dict = subtask.to_dict()
        assert subtask_dict["title"] == "Integration test subtask"
        assert subtask_dict["parent_task_id"] == str(parent_task_id)
        assert subtask_dict["status"] == "done"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])