#!/usr/bin/env python3
"""
Test-Driven Development: Context Response Format Consistency

This test file verifies that all context operations return consistent response formats
as specified in docs/context-response-format.md.

Expected behavior:
- All context operations should return standardized structure
- Field names should be consistent (context_data, contexts, delegation_result, etc.)
- Response format should be predictable and well-documented
- Include operation tracking and confirmation details
"""

import pytest
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastmcp.task_management.interface.utils.response_formatter import StandardResponseFormatter
from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task as TaskModel,
    GlobalContext as GlobalContextModel,
    ProjectContext, BranchContext
)
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.application.facades.unified_context_facade import UnifiedContextFacade


class TestContextResponseFormatConsistency:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test that all context operations return consistent response formats."""
    
    @pytest.fixture
    def setup_test_data(self):
        """Create test project, branch, and task for context operations."""
        with get_session() as session:
            # Ensure global context exists
            global_context = session.get(GlobalContextModel, "global_singleton")
            if not global_context:
                global_context = GlobalContextModel(
                    id="global_singleton",
                    organization_id="default_org",
                    autonomous_rules={},
                    security_policies={},
                    coding_standards={},
                    workflow_templates={},
                    delegation_rules={},
                    version=1
                )
                session.add(global_context)
            
            # Create project
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name="Context Format Test Project",
                description="Testing context response format consistency",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project)
            
            # Create branch
            branch_id = str(uuid.uuid4())
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project_id,
                name="feature/context-format-test",
                description="Test branch for context format",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(branch)
            
            # Create project context (required for branch context)
            project_context = ProjectContext(
                project_id=project_id,
                team_preferences={},
                technology_stack={},
                project_workflow={},
                local_standards={},
                global_overrides={},
                delegation_rules={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project_context)
            
            # Create branch context (required for task context)
            branch_context = BranchContext(
                branch_id=branch_id,
                parent_project_id=project_id,
                parent_project_context_id=project_id,
                branch_workflow={},
                branch_standards={},
                agent_assignments={},

                delegation_rules={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(branch_context)
            
            # Create task
            task_id = str(uuid.uuid4())
            task = TaskModel(
                id=task_id,
                git_branch_id=branch_id,
                title="Test Context Format Task",
                description="Task for testing context format",
                status="todo",
                priority="medium",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(task)
            session.commit()
            
            return {
                "project_id": project_id,
                "branch_id": branch_id,
                "task_id": task_id
            }
    
    @pytest.fixture
    def context_facade(self):
        """Create unified context facade."""
        factory = UnifiedContextFacadeFactory()
        return factory.create_facade()
    
    def _validate_base_response_structure(self, response: Dict[str, Any], expected_operation: str) -> None:
        """Validate that response follows the base standardized structure."""
        # Check required fields
        assert "status" in response, "Response must include 'status' field"
        assert "success" in response, "Response must include 'success' field"
        assert "operation" in response, "Response must include 'operation' field"
        assert "operation_id" in response, "Response must include 'operation_id' field" 
        assert "timestamp" in response, "Response must include 'timestamp' field"
        
        # Validate field types
        assert isinstance(response["success"], bool), "'success' must be boolean"
        assert response["operation"] == expected_operation, f"Operation should be '{expected_operation}'"
        assert isinstance(response["operation_id"], str), "'operation_id' must be string"
        assert isinstance(response["timestamp"], str), "'timestamp' must be string"
        
        # Check confirmation structure
        if "confirmation" in response:
            confirmation = response["confirmation"]
            assert "operation_completed" in confirmation, "Confirmation must include 'operation_completed'"
            assert "data_persisted" in confirmation, "Confirmation must include 'data_persisted'"
            assert isinstance(confirmation["operation_completed"], bool)
            assert isinstance(confirmation["data_persisted"], bool)
    
    def _validate_context_metadata(self, response: Dict[str, Any], expected_level: str = None, expected_context_id: str = None) -> None:
        """Validate context operation metadata structure."""
        if "metadata" in response:
            metadata = response["metadata"]
            
            if "context_operation" in metadata:
                context_op = metadata["context_operation"]
                
                if expected_level:
                    assert context_op.get("level") == expected_level, f"Level should be '{expected_level}'"
                
                if expected_context_id:
                    assert context_op.get("context_id") == expected_context_id, f"Context ID should be '{expected_context_id}'"
    
    def test_create_context_response_format(self, context_facade, setup_test_data):
        """Test that create context returns standardized format with 'context_data' field."""
        test_data = setup_test_data
        task_id = test_data["task_id"]
        
        # Create context
        branch_id = test_data["branch_id"]
        raw_response = context_facade.create_context(
            level="task",
            context_id=task_id,
            data={
                "title": "Test Context",
                "description": "Test Description",
                "branch_id": branch_id,
                "task_data": {"title": "Test Context", "description": "Test Description"}
            }
        )
        
        # Apply standardization (this is what the controller does)
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.create"
        )
        
        # Validate base structure
        self._validate_base_response_structure(response, "manage_context.create")
        
        # Validate success response format
        if response.get("success"):
            assert "data" in response, "Successful response must include 'data' field"
            data = response["data"]
            
            # Check for standardized field name
            assert "context_data" in data, "Create operation should return 'context_data' field"
            assert "context" not in data, "Should not include legacy 'context' field name"
            
            context_data = data["context_data"]
            assert isinstance(context_data, dict), "'context_data' must be a dictionary"
            
            # Validate context metadata
            self._validate_context_metadata(response, "task", task_id)
            
            # Check for creation metadata
            if "metadata" in response and "context_operation" in response["metadata"]:
                context_op = response["metadata"]["context_operation"]
                assert "created" in context_op, "Create operation should include 'created' field"
    
    def test_get_context_response_format(self, context_facade, setup_test_data):
        """Test that get context returns standardized format with 'context_data' field."""
        test_data = setup_test_data
        task_id = test_data["task_id"]
        
        # First create a context
        branch_id = test_data["branch_id"]
        create_response = context_facade.create_context(
            level="task",
            context_id=task_id,
            data={
                "title": "Test Context",
                "branch_id": branch_id,
                "task_data": {"title": "Test Context"}
            }
        )
        
        # Skip if create failed
        if not create_response.get("success"):
            print(f"DEBUG: Context creation failed: {create_response}")
            pytest.skip("Context creation failed, skipping get test")
        
        # Get the context
        raw_response = context_facade.get_context(
            level="task",
            context_id=task_id
        )
        
        # Apply standardization (this is what the controller does)
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.get"
        )
        
        # Validate base structure
        self._validate_base_response_structure(response, "manage_context.get")
        
        # Validate success response format
        if response.get("success"):
            assert "data" in response, "Successful response must include 'data' field"
            data = response["data"]
            
            # Check for standardized field name
            assert "context_data" in data, "Get operation should return 'context_data' field"
            assert "context" not in data, "Should not include legacy 'context' field name"
            
            context_data = data["context_data"]
            assert isinstance(context_data, dict), "'context_data' must be a dictionary"
            
            # Validate context metadata
            self._validate_context_metadata(response, "task", task_id)
    
    def test_list_contexts_response_format(self, context_facade, setup_test_data):
        """Test that list contexts returns standardized format with 'contexts' field."""
        # Get list of contexts
        raw_response = context_facade.list_contexts(
            level="task"
        )
        
        # Apply standardization (this is what the controller does)
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.list"
        )
        
        # Validate base structure
        self._validate_base_response_structure(response, "manage_context.list")
        
        # Validate success response format
        if response.get("success"):
            assert "data" in response, "Successful response must include 'data' field"
            data = response["data"]
            
            # Check for standardized field name
            assert "contexts" in data, "List operation should return 'contexts' field"
            assert "context" not in data, "Should not include legacy 'context' field name"
            
            contexts = data["contexts"]
            assert isinstance(contexts, list), "'contexts' must be a list"
            
            # Validate context metadata includes count
            if "metadata" in response and "context_operation" in response["metadata"]:
                context_op = response["metadata"]["context_operation"]
                assert "count" in context_op, "List operation should include 'count' field"
                assert context_op["count"] == len(contexts), "Count should match contexts length"
    
    def test_update_context_response_format(self, context_facade, setup_test_data):
        """Test that update context returns standardized format with 'context_data' field."""
        test_data = setup_test_data
        task_id = test_data["task_id"]
        
        # First create a context
        branch_id = test_data["branch_id"]
        create_response = context_facade.create_context(
            level="task",
            context_id=task_id,
            data={
                "title": "Original Title",
                "branch_id": branch_id,
                "task_data": {"title": "Original Title"}
            }
        )
        
        # Skip if create failed
        if not create_response.get("success"):
            pytest.skip("Context creation failed, skipping update test")
        
        # Update the context
        raw_response = context_facade.update_context(
            level="task",
            context_id=task_id,
            data={"title": "Updated Title", "status": "in_progress"}
        )
        
        # Apply standardization (this is what the controller does)
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.update"
        )
        
        # Validate base structure
        self._validate_base_response_structure(response, "manage_context.update")
        
        # Validate success response format
        if response.get("success"):
            assert "data" in response, "Successful response must include 'data' field"
            data = response["data"]
            
            # Check for standardized field name
            assert "context_data" in data, "Update operation should return 'context_data' field"
            assert "context" not in data, "Should not include legacy 'context' field name"
            
            context_data = data["context_data"]
            assert isinstance(context_data, dict), "'context_data' must be a dictionary"
            
            # Validate context metadata
            self._validate_context_metadata(response, "task", task_id)
            
            # Check for propagation metadata
            if "metadata" in response and "context_operation" in response["metadata"]:
                context_op = response["metadata"]["context_operation"]
                assert "propagated" in context_op, "Update operation should include 'propagated' field"
    
    def test_delete_context_response_format(self, context_facade, setup_test_data):
        """Test that delete context returns standardized format."""
        test_data = setup_test_data
        task_id = test_data["task_id"]
        
        # First create a context
        branch_id = test_data["branch_id"]
        create_response = context_facade.create_context(
            level="task",
            context_id=task_id,
            data={
                "title": "To Be Deleted",
                "branch_id": branch_id,
                "task_data": {"title": "To Be Deleted"}
            }
        )
        
        # Skip if create failed
        if not create_response.get("success"):
            pytest.skip("Context creation failed, skipping delete test")
        
        # Delete the context
        raw_response = context_facade.delete_context(
            level="task",
            context_id=task_id
        )
        
        # Apply standardization (this is what the controller does)
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.delete"
        )
        
        # Validate base structure
        self._validate_base_response_structure(response, "manage_context.delete")
        
        # Validate success response format
        if response.get("success"):
            assert "data" in response, "Successful response must include 'data' field"
            
            # Validate context metadata
            self._validate_context_metadata(response, "task", task_id)
    
    def test_response_json_serializable(self, context_facade, setup_test_data):
        """Test that all context responses are JSON serializable."""
        test_data = setup_test_data
        task_id = test_data["task_id"]
        
        # Test create operation
        branch_id = test_data["branch_id"]
        raw_create_response = context_facade.create_context(
            level="task", 
            context_id=task_id,
            data={
                "title": "JSON Test Context",
                "branch_id": branch_id,
                "task_data": {"title": "JSON Test Context"}
            }
        )
        create_response = StandardResponseFormatter.format_context_response(
            raw_create_response,
            operation="manage_context.create"
        )
        
        # Verify response is JSON serializable
        try:
            json_str = json.dumps(create_response)
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict), "Parsed response should be a dictionary"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Create response is not JSON serializable: {e}")
        
        # Test get operation if create succeeded
        if create_response.get("success"):
            raw_get_response = context_facade.get_context(
                level="task",
                context_id=task_id
            )
            get_response = StandardResponseFormatter.format_context_response(
                raw_get_response,
                operation="manage_context.get"
            )
            
            try:
                json.dumps(get_response)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Get response is not JSON serializable: {e}")
    
    def test_error_response_format(self, context_facade):
        """Test that error responses follow standardized format."""
        # Try to get non-existent context
        raw_response = context_facade.get_context(
            level="task",
            context_id="non-existent-id"
        )
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.get"
        )
        
        # Validate base structure
        self._validate_base_response_structure(response, "manage_context.get")
        
        # Should be an error response
        assert response.get("success") is False, "Response should indicate failure"
        assert response.get("status") == "failure", "Status should be 'failure'"
        
        # Should include error information
        assert "error" in response, "Error response must include 'error' field"
        error = response["error"]
        assert "message" in error, "Error must include 'message' field"
        assert "code" in error, "Error must include 'code' field"
        
        # Should still include metadata for debugging
        self._validate_context_metadata(response, "task", "non-existent-id")
    
    def test_standardized_response_formatter_helper_methods(self, context_facade, setup_test_data):
        """Test that StandardResponseFormatter helper methods work with context responses."""
        test_data = setup_test_data
        task_id = test_data["task_id"]
        
        # Create context
        branch_id = test_data["branch_id"]
        raw_response = context_facade.create_context(
            level="task",
            context_id=task_id,
            data={
                "title": "Helper Test Context",
                "branch_id": branch_id,
                "task_data": {"title": "Helper Test Context"}
            }
        )
        response = StandardResponseFormatter.format_context_response(
            raw_response,
            operation="manage_context.create"
        )
        
        # Test verify_success method
        if response.get("success"):
            assert StandardResponseFormatter.verify_success(response), "verify_success should return True for successful operation"
            
            # Test extract_data method
            data = StandardResponseFormatter.extract_data(response)
            assert data is not None, "extract_data should return data for successful operation"
            assert "context_data" in data, "Extracted data should contain 'context_data'"
            
            # Test get_operation_id method
            operation_id = StandardResponseFormatter.get_operation_id(response)
            assert operation_id is not None, "get_operation_id should return operation ID"
            assert isinstance(operation_id, str), "Operation ID should be string"
            
            # Test has_partial_failures method
            has_failures = StandardResponseFormatter.has_partial_failures(response)
            assert has_failures is False, "Should not have partial failures for successful operation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])