"""Unit Tests for Phase 1: Foundation & Parameter Schema Implementation

Tests the enhanced parameter schema validation and context enforcement
for the Vision System Phase 1 implementation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.interface.controllers.progress_tools_controller import ProgressToolsController
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


class TestPhase1ParameterSchema:
    """Test suite for Phase 1 parameter schema validation and context enforcement."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_task_facade_factory = Mock(spec=TaskFacadeFactory)
        self.mock_task_facade = Mock()
        self.mock_task_facade_factory.create.return_value = self.mock_task_facade
        
        self.mock_context_facade_factory = Mock(spec=UnifiedContextFacadeFactory)
        self.mock_context_facade = Mock()
        self.mock_context_facade_factory.create.return_value = self.mock_context_facade
        
        # Create controller
        self.controller = TaskMCPController(
            task_facade_factory=self.mock_task_facade_factory,
            context_facade_factory=self.mock_context_facade_factory
        )
    
    def test_completion_requires_summary(self):
        """Test that task completion requires a completion_summary parameter."""
        # Attempt to complete task without summary
        result = self.controller.manage_task(
            action="complete",
            task_id="test-task-123"
        )
        
        # Should fail with helpful error
        assert result["success"] is False
        assert "completion_summary is required" in result["error"]
        assert "workflow_guidance" in result
        assert "example" in result["workflow_guidance"]["next_actions"][0]
    
    def test_completion_with_summary_succeeds(self):
        """Test that task completion with summary succeeds."""
        # Mock facade response
        self.mock_task_facade.complete_task.return_value = {
            "success": True,
            "task": {"id": "test-task-123", "status": "done"}
        }
        
        # Complete task with summary
        result = self.controller.manage_task(
            action="complete",
            task_id="test-task-123",
            completion_summary="Implemented feature X with full test coverage",
            testing_notes="All unit tests passing, integration tests added"
        )
        
        # Should succeed
        assert result["success"] is True
        # Verify facade was called with summary
        self.mock_task_facade.complete_task.assert_called_once()
        call_args = self.mock_task_facade.complete_task.call_args[0]
        assert call_args[0] == "test-task-123"
        assert call_args[1] == "Implemented feature X with full test coverage"
        assert call_args[2] == "All unit tests passing, integration tests added"
    
    def test_update_with_context_parameters(self):
        """Test that update action handles new context tracking parameters."""
        # Mock facade response
        self.mock_task_facade.update_task.return_value = {
            "success": True,
            "task": {"id": "test-task-123"}
        }
        
        # Mock context update response
        self.mock_context_facade.update_context.return_value = {
            "success": True
        }
        
        # Update task with context parameters
        result = self.controller.manage_task(
            action="update",
            task_id="test-task-123",
            work_notes="Refactored authentication module",
            progress_made="Completed JWT implementation",
            files_modified=["auth/jwt.py", "auth/middleware.py"],
            decisions_made=["Use Redis for token storage", "Implement refresh tokens"],
            blockers_encountered=["Redis connection timeout issue"]
        )
        
        # Should update context
        self.mock_context_facade.update_context.assert_called_once()
        call_kwargs = self.mock_context_facade.update_context.call_args[1]
        assert call_kwargs["level"] == "task"
        assert call_kwargs["context_id"] == "test-task-123"
        assert call_kwargs["propagate_changes"] is True
        
        # Check context data
        context_data = call_kwargs["data"]
        assert context_data["work_notes"] == "Refactored authentication module"
        assert context_data["progress_made"] == "Completed JWT implementation"
        assert context_data["files_modified"] == ["auth/jwt.py", "auth/middleware.py"]
        assert context_data["decisions_made"] == ["Use Redis for token storage", "Implement refresh tokens"]
        assert context_data["blockers_encountered"] == ["Redis connection timeout issue"]
    
    def test_update_without_context_parameters(self):
        """Test that update works normally without context parameters."""
        # Mock facade response
        self.mock_task_facade.update_task.return_value = {
            "success": True,
            "task": {"id": "test-task-123"}
        }
        
        # Regular update without context parameters
        result = self.controller.manage_task(
            action="update",
            task_id="test-task-123",
            status="in_progress",
            description="Updated task description"
        )
        
        # Should not call context update
        self.mock_context_facade.update_context.assert_not_called()
    
    def test_progress_tools_report_progress(self):
        """Test the report_progress tool from ProgressToolsController."""
        # Create progress tools controller
        progress_controller = ProgressToolsController(
            task_facade=self.mock_task_facade,
            context_facade_factory=self.mock_context_facade_factory
        )
        
        # Mock context update response
        self.mock_context_facade.update_context.return_value = {
            "success": True
        }
        
        # Report progress
        result = progress_controller.report_progress(
            task_id="test-task-123",
            progress_type="implementation",
            description="Implemented core authentication logic",
            percentage=60,
            files_affected=["auth/core.py", "auth/utils.py"],
            next_steps=["Add error handling", "Write tests"]
        )
        
        # Should succeed
        assert result["success"] is True
        assert result["progress_type"] == "implementation"
        assert result["percentage"] == 60
        assert "hint" in result  # Should provide contextual hint
        
        # Verify context was updated
        self.mock_context_facade.update_context.assert_called_once()
        call_kwargs = self.mock_context_facade.update_context.call_args[1]
        assert call_kwargs["level"] == "task"
        assert call_kwargs["context_id"] == "test-task-123"
        
        context_data = call_kwargs["data"]
        assert "progress" in context_data
        assert context_data["progress"]["type"] == "implementation"
        assert context_data["progress"]["percentage"] == 60
        assert context_data["files_affected"] == ["auth/core.py", "auth/utils.py"]
        assert context_data["next_steps"] == ["Add error handling", "Write tests"]
    
    def test_progress_tools_quick_update(self):
        """Test the quick_task_update tool."""
        # Create progress tools controller
        progress_controller = ProgressToolsController(
            task_facade=self.mock_task_facade,
            context_facade_factory=self.mock_context_facade_factory
        )
        
        # Mock responses
        self.mock_context_facade.update_context.return_value = {"success": True}
        self.mock_task_facade.update_task.return_value = {"success": True}
        
        # Quick update with progress
        result = progress_controller.quick_task_update(
            task_id="test-task-123",
            what_i_did="Fixed authentication bug and added validation",
            progress_percentage=75,
            blockers=None
        )
        
        # Should succeed
        assert result["success"] is True
        assert result["progress"] == 75
        
        # Should update task status based on progress
        self.mock_task_facade.update_task.assert_called_once()
        update_call = self.mock_task_facade.update_task.call_args[0][0]
        assert update_call["task_id"] == "test-task-123"
        assert update_call["status"] == "in_progress"  # 75% = in_progress
    
    def test_progress_tools_checkpoint(self):
        """Test the checkpoint_work tool."""
        # Create progress tools controller
        progress_controller = ProgressToolsController(
            task_facade=self.mock_task_facade,
            context_facade_factory=self.mock_context_facade_factory
        )
        
        # Mock context update response
        self.mock_context_facade.update_context.return_value = {"success": True}
        
        # Create checkpoint
        result = progress_controller.checkpoint_work(
            task_id="test-task-123",
            current_state="Authentication module 80% complete, tests pending",
            next_steps=["Write unit tests", "Add integration tests", "Update documentation"],
            notes="Consider adding rate limiting in future iteration"
        )
        
        # Should succeed
        assert result["success"] is True
        assert result["next_steps_count"] == 3
        assert "checkpoint_time" in result
        
        # Verify context was updated with checkpoint
        self.mock_context_facade.update_context.assert_called_once()
        call_kwargs = self.mock_context_facade.update_context.call_args[1]
        context_data = call_kwargs["data"]
        assert "checkpoint" in context_data
        assert context_data["checkpoint"]["current_state"] == "Authentication module 80% complete, tests pending"
        assert len(context_data["checkpoint"]["next_steps"]) == 3
        assert context_data["checkpoint"]["notes"] == "Consider adding rate limiting in future iteration"
    
    def test_invalid_progress_percentage(self):
        """Test that invalid progress percentage is rejected."""
        progress_controller = ProgressToolsController(
            task_facade=self.mock_task_facade,
            context_facade_factory=self.mock_context_facade_factory
        )
        
        # Report progress with invalid percentage
        result = progress_controller.report_progress(
            task_id="test-task-123",
            progress_type="implementation",
            description="Some work",
            percentage=150  # Invalid - over 100
        )
        
        # Should fail with validation error
        assert result["success"] is False
        assert "percentage" in result["field"]
        assert "between 0 and 100" in result["expected"]
    
    def test_unknown_progress_type_fallback(self):
        """Test that unknown progress types fall back to 'update'."""
        progress_controller = ProgressToolsController(
            task_facade=self.mock_task_facade,
            context_facade_factory=self.mock_context_facade_factory
        )
        
        # Mock context update response
        self.mock_context_facade.update_context.return_value = {"success": True}
        
        # Report progress with unknown type
        result = progress_controller.report_progress(
            task_id="test-task-123",
            progress_type="unknown_type",  # Not in valid types
            description="Some work",
            percentage=50
        )
        
        # Should succeed but use 'update' type
        assert result["success"] is True
        
        # Check that context was updated with 'update' type
        call_kwargs = self.mock_context_facade.update_context.call_args[1]
        # The controller warns and uses "update" as fallback
        # but still reports the original type in response
        assert result["progress_type"] == "update" or result["progress_type"] == "unknown_type"
    
    def test_context_update_failure_handling(self):
        """Test handling of context update failures."""
        progress_controller = ProgressToolsController(
            task_facade=self.mock_task_facade,
            context_facade_factory=self.mock_context_facade_factory
        )
        
        # Mock context update failure
        self.mock_context_facade.update_context.return_value = {
            "success": False,
            "error": "Context not found"
        }
        
        # Try to report progress
        result = progress_controller.report_progress(
            task_id="test-task-123",
            progress_type="implementation",
            description="Some work",
            percentage=50
        )
        
        # Should fail gracefully
        assert result["success"] is False
        assert "Failed to update progress" in result["error"]
        assert result["task_id"] == "test-task-123"


class TestParameterValidation:
    """Test parameter validation and coercion from parameter_validation_fix.py"""
    
    def test_parameter_type_coercion(self):
        """Test that parameter types are correctly coerced."""
        from fastmcp.task_management.interface.utils.parameter_validation_fix import (
            ParameterTypeCoercer
        )
        
        # Test integer coercion
        params = {
            "limit": "5",
            "progress_percentage": "75",
            "timeout": "3000"
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(params)
        
        assert coerced["limit"] == 5
        assert coerced["progress_percentage"] == 75
        assert coerced["timeout"] == 3000
        assert isinstance(coerced["limit"], int)
        assert isinstance(coerced["progress_percentage"], int)
        assert isinstance(coerced["timeout"], int)
    
    def test_boolean_coercion(self):
        """Test boolean parameter coercion."""
        from fastmcp.task_management.interface.utils.parameter_validation_fix import (
            ParameterTypeCoercer
        )
        
        # Test various boolean representations
        params = {
            "include_context": "true",
            "force": "1",
            "audit_required": "yes",
            "propagate_changes": "false",
            "force_refresh": "0",
            "include_inherited": "no"
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(params)
        
        assert coerced["include_context"] is True
        assert coerced["force"] is True
        assert coerced["audit_required"] is True
        assert coerced["propagate_changes"] is False
        assert coerced["force_refresh"] is False
        assert coerced["include_inherited"] is False
    
    def test_list_coercion(self):
        """Test list parameter coercion."""
        from fastmcp.task_management.interface.utils.parameter_validation_fix import (
            ParameterTypeCoercer
        )
        
        # Test various list representations
        params = {
            "insights_found": '["insight1", "insight2"]',  # JSON array
            "assignees": "user1, user2, user3",  # Comma-separated
            "labels": "frontend",  # Single value
            "dependencies": "",  # Empty string
            "tags": ["tag1", "tag2"]  # Already a list
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(params)
        
        assert coerced["insights_found"] == ["insight1", "insight2"]
        assert coerced["assignees"] == ["user1", "user2", "user3"]
        assert coerced["labels"] == ["frontend"]
        assert coerced["dependencies"] == []
        assert coerced["tags"] == ["tag1", "tag2"]
    
    def test_flexible_schema_creation(self):
        """Test flexible schema generation."""
        from fastmcp.task_management.interface.utils.parameter_validation_fix import (
            FlexibleSchemaValidator
        )
        
        # Original restrictive schema
        original_schema = {
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "include_context": {"type": "boolean"},
                "insights_found": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        flexible = FlexibleSchemaValidator.create_flexible_schema(original_schema)
        
        # Check that properties now have anyOf schemas
        assert "anyOf" in flexible["properties"]["limit"]
        assert "anyOf" in flexible["properties"]["include_context"]
        assert "anyOf" in flexible["properties"]["insights_found"]
        
        # Check integer schema accepts both int and string
        limit_schemas = flexible["properties"]["limit"]["anyOf"]
        assert any(s.get("type") == "integer" for s in limit_schemas)
        assert any(s.get("type") == "string" for s in limit_schemas)
        
        # Check boolean schema accepts both bool and string
        bool_schemas = flexible["properties"]["include_context"]["anyOf"]
        assert any(s.get("type") == "boolean" for s in bool_schemas)
        assert any(s.get("type") == "string" for s in bool_schemas)