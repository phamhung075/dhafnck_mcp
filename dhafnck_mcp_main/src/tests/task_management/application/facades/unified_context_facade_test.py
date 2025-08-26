"""Tests for UnifiedContextFacade"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

from fastmcp.task_management.application.facades.unified_context_facade import UnifiedContextFacade
from fastmcp.task_management.domain.exceptions.base_exceptions import ValidationException


class TestUnifiedContextFacade:
    """Test suite for UnifiedContextFacade"""

    @pytest.fixture
    def mock_unified_service(self):
        """Create mock unified context service"""
        service = Mock()
        service.create_context.return_value = {"success": True, "context_id": "test-context"}
        service.get_context.return_value = {"success": True, "data": {"test": "data"}}
        service.update_context.return_value = {"success": True, "updated": True}
        service.delete_context.return_value = {"success": True, "deleted": True}
        service.resolve_context.return_value = {"success": True, "resolved": {"test": "resolved"}}
        service.delegate_context.return_value = {"success": True, "delegated": True}
        service.add_insight.return_value = {"success": True, "insight_added": True}
        service.add_progress.return_value = {"success": True, "progress_added": True}
        service.list_contexts.return_value = {"success": True, "contexts": []}
        return service

    @pytest.fixture
    def facade(self, mock_unified_service):
        """Create facade instance with mocked service"""
        return UnifiedContextFacade(
            unified_service=mock_unified_service,
            user_id="test-user",
            project_id="test-project",
            git_branch_id="test-branch"
        )

    def test_facade_initialization(self, mock_unified_service):
        """Test facade initializes correctly"""
        user_id = "user-123"
        project_id = "project-456"
        git_branch_id = "branch-789"
        
        facade = UnifiedContextFacade(
            unified_service=mock_unified_service,
            user_id=user_id,
            project_id=project_id,
            git_branch_id=git_branch_id
        )
        
        assert facade._service == mock_unified_service
        assert facade._user_id == user_id
        assert facade._project_id == project_id
        assert facade._git_branch_id == git_branch_id

    def test_facade_initialization_minimal(self, mock_unified_service):
        """Test facade initialization with minimal parameters"""
        facade = UnifiedContextFacade(unified_service=mock_unified_service)
        
        assert facade._service == mock_unified_service
        assert facade._user_id is None
        assert facade._project_id is None
        assert facade._git_branch_id is None

    def test_add_scope_to_data_all_scope(self, facade):
        """Test adding scope information to data"""
        input_data = {"existing": "data"}
        
        result = facade._add_scope_to_data(input_data)
        
        assert result["existing"] == "data"
        assert result["user_id"] == "test-user"
        assert result["project_id"] == "test-project"
        assert result["git_branch_id"] == "test-branch"

    def test_add_scope_to_data_empty_dict(self, facade):
        """Test adding scope to empty dict"""
        result = facade._add_scope_to_data({})
        
        assert result["user_id"] == "test-user"
        assert result["project_id"] == "test-project"
        assert result["git_branch_id"] == "test-branch"

    def test_add_scope_to_data_none_input(self, facade):
        """Test adding scope to None input"""
        result = facade._add_scope_to_data(None)
        
        assert result["user_id"] == "test-user"
        assert result["project_id"] == "test-project"
        assert result["git_branch_id"] == "test-branch"

    def test_add_scope_to_data_existing_scope(self, facade):
        """Test that existing scope data is not overwritten"""
        input_data = {
            "user_id": "existing-user",
            "project_id": "existing-project",
            "git_branch_id": "existing-branch"
        }
        
        result = facade._add_scope_to_data(input_data)
        
        assert result["user_id"] == "existing-user"
        assert result["project_id"] == "existing-project"
        assert result["git_branch_id"] == "existing-branch"

    def test_add_scope_to_data_no_facade_scope(self, mock_unified_service):
        """Test adding scope when facade has no scope information"""
        facade = UnifiedContextFacade(unified_service=mock_unified_service)
        input_data = {"test": "data"}
        
        result = facade._add_scope_to_data(input_data)
        
        assert result == {"test": "data"}
        assert "user_id" not in result
        assert "project_id" not in result
        assert "git_branch_id" not in result

    def test_create_context_success(self, facade, mock_unified_service):
        """Test successful context creation"""
        level = "task"
        context_id = "task-123"
        data = {"title": "Test Task"}
        
        result = facade.create_context(level, context_id, data)
        
        assert result["success"] is True
        mock_unified_service.create_context.assert_called_once()
        
        # Verify call arguments
        call_args = mock_unified_service.create_context.call_args
        assert call_args[0][0] == level  # level
        assert call_args[0][1] == context_id  # context_id
        assert call_args[0][2]["title"] == "Test Task"  # data with scope
        assert call_args[1]["user_id"] == "test-user"
        assert call_args[1]["project_id"] == "test-project"

    def test_create_context_no_data(self, facade, mock_unified_service):
        """Test context creation without data"""
        result = facade.create_context("project", "project-123")
        
        assert result["success"] is True
        mock_unified_service.create_context.assert_called_once()
        
        # Verify scope was added
        call_args = mock_unified_service.create_context.call_args
        data_param = call_args[0][2]
        assert data_param["user_id"] == "test-user"
        assert data_param["project_id"] == "test-project"

    def test_create_context_exception_handling(self, facade, mock_unified_service):
        """Test context creation exception handling"""
        mock_unified_service.create_context.side_effect = ValidationException("Invalid context")
        
        result = facade.create_context("task", "task-123", {"test": "data"})
        
        assert result["success"] is False
        assert "Invalid context" in result["error"]

    def test_run_sync_method(self, facade):
        """Test the _run_sync helper method"""
        test_value = {"test": "result"}
        
        result = facade._run_sync(test_value)
        
        assert result == test_value

    def test_facade_delegation_with_partial_scope(self, mock_unified_service):
        """Test facade with partial scope information"""
        facade = UnifiedContextFacade(
            unified_service=mock_unified_service,
            user_id="test-user",
            project_id=None,  # Missing project_id
            git_branch_id="test-branch"
        )
        
        data = {"test": "data"}
        result_data = facade._add_scope_to_data(data)
        
        assert result_data["user_id"] == "test-user"
        assert result_data["git_branch_id"] == "test-branch"
        assert "project_id" not in result_data

    def test_logging_on_initialization(self, mock_unified_service):
        """Test that initialization is logged"""
        with patch('fastmcp.task_management.application.facades.unified_context_facade.logger') as mock_logger:
            facade = UnifiedContextFacade(
                unified_service=mock_unified_service,
                user_id="test-user",
                project_id="test-project",
                git_branch_id="test-branch"
            )
            
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "UnifiedContextFacade initialized" in log_call
            assert "user=test-user" in log_call
            assert "project=test-project" in log_call
            assert "branch=test-branch" in log_call

    def test_facade_service_delegation(self, facade, mock_unified_service):
        """Test that facade properly delegates to service"""
        # Test that facade has direct access to service
        assert facade._service == mock_unified_service
        
        # Any method that would be called should delegate to the service
        facade.create_context("task", "task-123")
        mock_unified_service.create_context.assert_called_once()

    def test_create_context_data_modification(self, facade, mock_unified_service):
        """Test that create_context properly modifies data with scope"""
        original_data = {"original": "value"}
        
        facade.create_context("task", "task-123", original_data)
        
        # Verify original data is not modified
        assert original_data == {"original": "value"}
        
        # Verify service received data with scope
        call_args = mock_unified_service.create_context.call_args
        modified_data = call_args[0][2]
        assert modified_data["original"] == "value"
        assert modified_data["user_id"] == "test-user"
        assert modified_data["project_id"] == "test-project"
        assert modified_data["git_branch_id"] == "test-branch"

    def test_facade_error_handling_general_exception(self, facade, mock_unified_service):
        """Test general exception handling in facade"""
        mock_unified_service.create_context.side_effect = RuntimeError("Unexpected error")
        
        result = facade.create_context("task", "task-123")
        
        assert result["success"] is False
        assert "error" in result
        # Should handle any exception, not just ValidationException

    def test_facade_method_parameters(self, facade, mock_unified_service):
        """Test that facade methods accept expected parameters"""
        import inspect
        
        # Check create_context signature
        sig = inspect.signature(facade.create_context)
        params = list(sig.parameters.keys())
        
        assert 'level' in params
        assert 'context_id' in params
        assert 'data' in params
        
        # Verify optional parameter
        assert sig.parameters['data'].default is None

    def test_facade_with_different_service_responses(self, facade, mock_unified_service):
        """Test facade handles different service response formats"""
        # Test with different success response
        mock_unified_service.create_context.return_value = {
            "success": True,
            "context": {"id": "ctx-123", "data": {"test": "data"}},
            "metadata": {"created_at": "2025-01-01"}
        }
        
        result = facade.create_context("task", "task-123")
        
        assert result["success"] is True
        assert "context" in result
        assert "metadata" in result

    def test_scope_information_priority(self, facade):
        """Test that explicit data takes priority over facade scope"""
        data_with_explicit_user = {
            "user_id": "explicit-user",
            "other_data": "value"
        }
        
        result = facade._add_scope_to_data(data_with_explicit_user)
        
        # Explicit user_id should be preserved
        assert result["user_id"] == "explicit-user"
        # But facade scope should still be added where missing
        assert result["project_id"] == "test-project"
        assert result["git_branch_id"] == "test-branch"
        assert result["other_data"] == "value"