"""Test suite for ComplianceMCPController.

Tests the compliance MCP controller including:
- Tool registration and MCP integration
- Compliance validation operations
- Compliance dashboard generation
- Compliant command execution
- Audit trail retrieval
- Authentication and user context handling
- Error handling and validation
- Edge cases and boundary conditions
"""

import pytest
import logging
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from pathlib import Path

from fastmcp.task_management.interface.controllers.compliance_mcp_controller import ComplianceMCPController
from fastmcp.task_management.application.orchestrators.compliance_orchestrator import ComplianceOrchestrator
from fastmcp.config.auth_config import AuthConfig


class TestComplianceMCPController:
    """Test cases for ComplianceMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock(spec=ComplianceOrchestrator)
        self.project_root = Path("/test/project")
        
        # Mock description loader
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader') as mock_desc_loader:
            mock_desc_loader.get_all_descriptions.return_value = {
                'compliance': {
                    'manage_compliance': {
                        'description': 'Test compliance management tool'
                    }
                }
            }
            self.controller = ComplianceMCPController(self.mock_orchestrator, self.project_root)
    
    def test_init_with_orchestrator(self):
        """Test controller initialization with provided orchestrator."""
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader'):
            controller = ComplianceMCPController(self.mock_orchestrator, self.project_root)
            
            assert controller._compliance_orchestrator == self.mock_orchestrator
            assert controller._project_root == self.project_root
    
    def test_init_without_orchestrator(self):
        """Test controller initialization with default orchestrator."""
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader'):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.ComplianceOrchestrator') as mock_orchestrator_class:
                mock_orchestrator_instance = Mock()
                mock_orchestrator_class.return_value = mock_orchestrator_instance
                
                controller = ComplianceMCPController(project_root=self.project_root)
                
                assert controller._compliance_orchestrator == mock_orchestrator_instance
                assert controller._project_root == self.project_root
                mock_orchestrator_class.assert_called_once_with(self.project_root)
    
    def test_init_without_project_root(self):
        """Test controller initialization with default project root."""
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader'):
            with patch('pathlib.Path.cwd') as mock_cwd:
                mock_cwd.return_value = Path("/default/project")
                
                controller = ComplianceMCPController(self.mock_orchestrator)
                
                assert controller._project_root == Path("/default/project")
                assert controller._compliance_orchestrator == self.mock_orchestrator
    
    def test_register_tools(self):
        """Test MCP tool registration."""
        mock_mcp = Mock()
        mock_tool_decorator = Mock()
        mock_mcp.tool.return_value = mock_tool_decorator
        
        self.controller.register_tools(mock_mcp)
        
        # Verify tool registration was called
        mock_mcp.tool.assert_called_once()
        call_kwargs = mock_mcp.tool.call_args.kwargs
        assert call_kwargs['name'] == 'manage_compliance'
        assert 'Test compliance management tool' in call_kwargs['description']
    
    def test_get_compliance_management_descriptions(self):
        """Test description loading from external files."""
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader') as mock_desc_loader:
            mock_desc_loader.get_all_descriptions.return_value = {
                'compliance': {
                    'manage_compliance': {
                        'description': 'Compliance tool description'
                    }
                },
                'other': {
                    'other_tool': {
                        'description': 'Other tool'
                    }
                }
            }
            
            descriptions = self.controller._get_compliance_management_descriptions()
            
            assert 'manage_compliance' in descriptions
            assert descriptions['manage_compliance']['description'] == 'Compliance tool description'
            assert 'other_tool' not in descriptions
    
    def test_get_compliance_management_descriptions_not_found(self):
        """Test description loading when manage_compliance not found."""
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader') as mock_desc_loader:
            mock_desc_loader.get_all_descriptions.return_value = {
                'other': {
                    'other_tool': {
                        'description': 'Other tool'
                    }
                }
            }
            
            descriptions = self.controller._get_compliance_management_descriptions()
            
            assert descriptions == {}
    
    @patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed')
    @patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id')
    def test_validate_compliance_action(self, mock_get_fallback_user_id, mock_is_default_user_allowed):
        """Test validate_compliance action."""
        # Setup mocks
        mock_is_default_user_allowed.return_value = True
        mock_get_fallback_user_id.return_value = "compatibility-default-user"
        
        expected_result = {
            "success": True,
            "compliance_score": 0.95,
            "violations": []
        }
        self.mock_orchestrator.validate_operation.return_value = expected_result
        
        # Test successful validation
        result = self.controller.manage_compliance(
            action="validate_compliance",
            operation="create_file",
            file_path="/test/file.txt",
            content="test content",
            security_level="public",
            audit_required=True
        )
        
        assert result == expected_result
        self.mock_orchestrator.validate_operation.assert_called_once_with(
            operation="create_file",
            file_path="/test/file.txt",
            content="test content",
            user_id="compatibility-default-user",
            security_level="public",
            audit_required=True
        )
    
    def test_validate_compliance_missing_operation(self):
        """Test validate_compliance action with missing operation parameter."""
        result = self.controller.manage_compliance(action="validate_compliance")
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: operation"
        assert result["error_code"] == "MISSING_FIELD"
        assert result["field"] == "operation"
        assert "create_file" in result["expected"]
        assert "Include 'operation'" in result["hint"]
        
        # Ensure orchestrator was not called
        self.mock_orchestrator.validate_operation.assert_not_called()
    
    def test_get_compliance_dashboard_action(self):
        """Test get_compliance_dashboard action."""
        expected_result = {
            "success": True,
            "dashboard_id": "test-dashboard-id",
            "compliance_rate": 0.95,
            "total_operations": 100
        }
        self.mock_orchestrator.get_compliance_dashboard.return_value = expected_result
        
        result = self.controller.manage_compliance(action="get_compliance_dashboard")
        
        assert result == expected_result
        self.mock_orchestrator.get_compliance_dashboard.assert_called_once()
    
    @patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed')
    @patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id')
    def test_execute_with_compliance_action(self, mock_get_fallback_user_id, mock_is_default_user_allowed):
        """Test execute_with_compliance action."""
        # Setup mocks
        mock_is_default_user_allowed.return_value = True
        mock_get_fallback_user_id.return_value = "compatibility-default-user"
        
        expected_result = {
            "success": True,
            "output": "Command executed successfully",
            "return_code": 0
        }
        self.mock_orchestrator.execute_with_compliance.return_value = expected_result
        
        # Test with timeout as string (should convert to int)
        result = self.controller.manage_compliance(
            action="execute_with_compliance",
            command="ls -la",
            timeout="30",
            audit_required=True
        )
        
        # Verify metadata was added
        assert "metadata" in result
        metadata = result["metadata"]
        assert metadata["action"] == "execute_with_compliance"
        assert metadata["command"] == "ls -la"
        assert metadata["timeout"] == 30
        assert "timestamp" in metadata
        
        self.mock_orchestrator.execute_with_compliance.assert_called_once_with(
            command="ls -la",
            timeout=30,
            user_id="compatibility-default-user",
            audit_required=True
        )
    
    def test_execute_with_compliance_missing_command(self):
        """Test execute_with_compliance action with missing command parameter."""
        result = self.controller.manage_compliance(action="execute_with_compliance")
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: command"
        assert result["error_code"] == "MISSING_FIELD"
        assert result["field"] == "command"
        assert "shell command" in result["expected"]
        assert "Include 'command'" in result["hint"]
        
        # Ensure orchestrator was not called
        self.mock_orchestrator.execute_with_compliance.assert_not_called()
    
    def test_execute_with_compliance_long_command_truncation(self):
        """Test command truncation in metadata for long commands."""
        long_command = "echo " + "a" * 100  # 105 characters total
        
        expected_result = {"success": True}
        self.mock_orchestrator.execute_with_compliance.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                result = self.controller.manage_compliance(
                    action="execute_with_compliance",
                    command=long_command
                )
        
        # Verify command was truncated in metadata
        assert "metadata" in result
        truncated_command = result["metadata"]["command"]
        assert len(truncated_command) == 53  # 50 characters + "..."
        assert truncated_command.endswith("...")
    
    def test_execute_with_compliance_invalid_timeout(self):
        """Test execute_with_compliance with invalid timeout value."""
        result = self.controller.manage_compliance(
            action="execute_with_compliance",
            command="ls -la",
            timeout="invalid"
        )
        
        assert result["success"] is False
        assert "Invalid timeout value" in result["error"]
        assert "metadata" in result
        metadata = result["metadata"]
        assert metadata["action"] == "execute_with_compliance"
        assert metadata["command"] == "ls -la"
        assert "timestamp" in metadata
        
        # Ensure orchestrator was not called due to timeout validation error
        self.mock_orchestrator.execute_with_compliance.assert_not_called()
    
    def test_get_audit_trail_action(self):
        """Test get_audit_trail action."""
        expected_result = {
            "success": True,
            "audit_entries": [
                {"timestamp": "2023-01-01T00:00:00", "operation": "create_file"}
            ],
            "total_entries": 1
        }
        self.mock_orchestrator.get_audit_trail.return_value = expected_result
        
        result = self.controller.manage_compliance(
            action="get_audit_trail",
            limit=50
        )
        
        assert result == expected_result
        self.mock_orchestrator.get_audit_trail.assert_called_once_with(50)
    
    def test_get_audit_trail_default_limit(self):
        """Test get_audit_trail action with default limit."""
        expected_result = {"success": True, "audit_entries": []}
        self.mock_orchestrator.get_audit_trail.return_value = expected_result
        
        result = self.controller.manage_compliance(action="get_audit_trail")
        
        assert result == expected_result
        self.mock_orchestrator.get_audit_trail.assert_called_once_with(100)
    
    def test_invalid_action(self):
        """Test handling of invalid action."""
        result = self.controller.manage_compliance(action="invalid_action")
        
        assert result["success"] is False
        assert "Invalid action: invalid_action" in result["error"]
        assert result["error_code"] == "UNKNOWN_ACTION"
        assert result["field"] == "action"
        assert "validate_compliance" in result["expected"]
        assert "get_compliance_dashboard" in result["expected"]
        assert "execute_with_compliance" in result["expected"]
        assert "get_audit_trail" in result["expected"]
        assert "Check the 'action' parameter" in result["hint"]
        
        # Ensure orchestrator was not called
        self.mock_orchestrator.validate_operation.assert_not_called()
        self.mock_orchestrator.get_compliance_dashboard.assert_not_called()
        self.mock_orchestrator.execute_with_compliance.assert_not_called()
        self.mock_orchestrator.get_audit_trail.assert_not_called()
    
    @patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed')
    @patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id')
    def test_user_id_handling_no_auth_config(self, mock_get_fallback_user_id, mock_is_default_user_allowed):
        """Test user_id handling when no user_id provided and auth config disabled."""
        mock_is_default_user_allowed.return_value = False
        
        expected_result = {"success": True, "compliance_score": 0.8}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        
        # Should still work with fallback even when auth is disabled (controller forces compatibility)
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', 
                   return_value="forced-fallback-user"):
            result = self.controller.manage_compliance(
                action="validate_compliance",
                operation="create_file"
            )
        
        assert result == expected_result
        # Verify fallback was used despite auth config being disabled
        self.mock_orchestrator.validate_operation.assert_called_once_with(
            operation="create_file",
            file_path=None,
            content=None,
            user_id="forced-fallback-user",
            security_level="public",
            audit_required=True
        )
    
    def test_user_id_handling_provided_user_id(self):
        """Test user_id handling when user_id is explicitly provided."""
        expected_result = {"success": True, "compliance_score": 0.9}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        
        result = self.controller.manage_compliance(
            action="validate_compliance",
            operation="edit_file",
            user_id="explicit-user-123"
        )
        
        assert result == expected_result
        self.mock_orchestrator.validate_operation.assert_called_once_with(
            operation="edit_file",
            file_path=None,
            content=None,
            user_id="explicit-user-123",
            security_level="public",
            audit_required=True
        )
    
    def test_exception_handling_in_manage_compliance(self):
        """Test exception handling in main manage_compliance method."""
        # Mock an exception in orchestrator
        self.mock_orchestrator.validate_operation.side_effect = RuntimeError("Orchestrator failed")
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                result = self.controller.manage_compliance(
                    action="validate_compliance",
                    operation="create_file"
                )
        
        assert result["success"] is False
        assert "Compliance operation failed" in result["error"]
        assert result["error_code"] == "INTERNAL_ERROR"
        assert "Orchestrator failed" in result["details"]
    
    def test_handle_validate_compliance_missing_operation(self):
        """Test _handle_validate_compliance with missing operation."""
        result = self.controller._handle_validate_compliance(operation=None)
        
        assert result["success"] is False
        assert "operation is required" in result["error"]
        
        # Ensure orchestrator was not called
        self.mock_orchestrator.validate_operation.assert_not_called()
    
    def test_handle_validate_compliance_exception(self):
        """Test _handle_validate_compliance with orchestrator exception."""
        self.mock_orchestrator.validate_operation.side_effect = ValueError("Invalid operation type")
        
        result = self.controller._handle_validate_compliance(
            operation="invalid_op",
            user_id="test-user"
        )
        
        assert result["success"] is False
        assert "Invalid operation type" in result["error"]
        assert result["compliance_score"] == 0.0
    
    def test_handle_get_compliance_dashboard_exception(self):
        """Test _handle_get_compliance_dashboard with orchestrator exception."""
        self.mock_orchestrator.get_compliance_dashboard.side_effect = RuntimeError("Dashboard error")
        
        result = self.controller._handle_get_compliance_dashboard()
        
        assert result["success"] is False
        assert "Dashboard error" in result["error"]
    
    def test_handle_execute_with_compliance_missing_command(self):
        """Test _handle_execute_with_compliance with missing command."""
        result = self.controller._handle_execute_with_compliance(command=None)
        
        assert result["success"] is False
        assert "command is required" in result["error"]
        assert "metadata" in result
        assert "timestamp" in result["metadata"]
        
        # Ensure orchestrator was not called
        self.mock_orchestrator.execute_with_compliance.assert_not_called()
    
    def test_handle_execute_with_compliance_exception(self):
        """Test _handle_execute_with_compliance with orchestrator exception."""
        self.mock_orchestrator.execute_with_compliance.side_effect = RuntimeError("Execution failed")
        
        result = self.controller._handle_execute_with_compliance(
            command="test command",
            user_id="test-user"
        )
        
        assert result["success"] is False
        assert "Execution failed" in result["error"]
        assert "metadata" in result
        metadata = result["metadata"]
        assert metadata["action"] == "execute_with_compliance"
        assert metadata["command"] == "test command"
        assert metadata["error_type"] == "RuntimeError"
        assert "timestamp" in metadata
    
    def test_handle_execute_with_compliance_failed_result(self):
        """Test _handle_execute_with_compliance with failed execution result."""
        failed_result = {
            "success": False,
            "error": "Command execution failed",
            "return_code": 1
        }
        self.mock_orchestrator.execute_with_compliance.return_value = failed_result
        
        result = self.controller._handle_execute_with_compliance(
            command="failing command",
            timeout=60,
            user_id="test-user"
        )
        
        # Should still add metadata even for failed results
        assert "metadata" in result
        metadata = result["metadata"]
        assert metadata["action"] == "execute_with_compliance"
        assert metadata["command"] == "failing command"
        assert metadata["timeout"] == 60
        assert "timestamp" in metadata
        assert result["success"] is False
        assert result["error"] == "Command execution failed"
    
    def test_handle_get_audit_trail_exception(self):
        """Test _handle_get_audit_trail with orchestrator exception."""
        self.mock_orchestrator.get_audit_trail.side_effect = ConnectionError("Database connection failed")
        
        result = self.controller._handle_get_audit_trail(limit=50)
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]
    
    @pytest.mark.parametrize("timeout_value,expected_timeout", [
        (None, None),
        (30, 30),
        ("60", 60),
        (0, 0),
        (-1, -1)  # Negative timeouts should be passed through to orchestrator
    ])
    def test_timeout_conversion_valid_values(self, timeout_value, expected_timeout):
        """Test timeout conversion for various valid values."""
        expected_result = {"success": True}
        self.mock_orchestrator.execute_with_compliance.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                result = self.controller.manage_compliance(
                    action="execute_with_compliance",
                    command="test command",
                    timeout=timeout_value
                )
        
        assert result["success"] is True
        self.mock_orchestrator.execute_with_compliance.assert_called_once_with(
            command="test command",
            timeout=expected_timeout,
            user_id="test-user",
            audit_required=True
        )
    
    @pytest.mark.parametrize("invalid_timeout", [
        "not_a_number",
        "30.5",  # Float string
        "abc123",
        "",
        "   ",
        "null"
    ])
    def test_timeout_conversion_invalid_values(self, invalid_timeout):
        """Test timeout conversion for various invalid values."""
        result = self.controller.manage_compliance(
            action="execute_with_compliance",
            command="test command",
            timeout=invalid_timeout
        )
        
        assert result["success"] is False
        assert "Invalid timeout value" in result["error"]
        assert "metadata" in result
        
        # Ensure orchestrator was not called due to validation error
        self.mock_orchestrator.execute_with_compliance.assert_not_called()
    
    def test_logging_integration(self):
        """Test that appropriate logging occurs."""
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.logger') as mock_logger:
            # Test initialization logging
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader'):
                controller = ComplianceMCPController(self.mock_orchestrator)
                mock_logger.info.assert_called_with("ComplianceMCPController initialized")
            
            # Test error logging
            self.mock_orchestrator.validate_operation.side_effect = RuntimeError("Test error")
            
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
                with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                    controller.manage_compliance(
                        action="validate_compliance",
                        operation="test_op"
                    )
                    
                    # Should log the error
                    mock_logger.error.assert_called()
                    error_call_args = mock_logger.error.call_args[0][0]
                    assert "validate_compliance" in error_call_args
                    assert "Test error" in error_call_args
    
    def test_all_required_parameters_coverage(self):
        """Test that all action types handle their required parameters correctly."""
        test_cases = [
            {
                'action': 'validate_compliance',
                'valid_params': {'operation': 'create_file'},
                'missing_param_error': 'operation'
            },
            {
                'action': 'execute_with_compliance',
                'valid_params': {'command': 'ls -la'},
                'missing_param_error': 'command'
            },
            {
                'action': 'get_compliance_dashboard',
                'valid_params': {},
                'missing_param_error': None
            },
            {
                'action': 'get_audit_trail',
                'valid_params': {},
                'missing_param_error': None
            }
        ]
        
        for case in test_cases:
            # Test missing required parameter
            if case['missing_param_error']:
                result = self.controller.manage_compliance(action=case['action'])
                assert result['success'] is False
                assert case['missing_param_error'] in result['error']
            
            # Test with valid parameters
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
                with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                    # Mock all orchestrator methods to return success
                    self.mock_orchestrator.validate_operation.return_value = {"success": True}
                    self.mock_orchestrator.get_compliance_dashboard.return_value = {"success": True}
                    self.mock_orchestrator.execute_with_compliance.return_value = {"success": True}
                    self.mock_orchestrator.get_audit_trail.return_value = {"success": True}
                    
                    params = {'action': case['action']}
                    params.update(case['valid_params'])
                    
                    result = self.controller.manage_compliance(**params)
                    
                    # Should not raise an error for valid parameters
                    assert 'error' not in result or result.get('success') is True


class TestComplianceMCPControllerEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_orchestrator = Mock(spec=ComplianceOrchestrator)
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.description_loader'):
            self.controller = ComplianceMCPController(self.mock_orchestrator)
    
    def test_empty_string_parameters(self):
        """Test handling of empty string parameters."""
        result = self.controller.manage_compliance(
            action="validate_compliance",
            operation="",  # Empty string
            file_path="",
            content=""
        )
        
        # Empty operation should be treated as missing
        assert result["success"] is False
        assert "operation is required" in result["error"] or "Missing required field: operation" in result["error"]
    
    def test_none_vs_empty_string_handling(self):
        """Test distinction between None and empty string parameters."""
        expected_result = {"success": True, "compliance_score": 0.8}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                # Test with None values (should be passed as None)
                result = self.controller.manage_compliance(
                    action="validate_compliance",
                    operation="create_file",
                    file_path=None,
                    content=None
                )
                
                self.mock_orchestrator.validate_operation.assert_called_once_with(
                    operation="create_file",
                    file_path=None,
                    content=None,
                    user_id="test-user",
                    security_level="public",
                    audit_required=True
                )
                
                # Reset mock for next test
                self.mock_orchestrator.reset_mock()
                
                # Test with empty strings (should be passed as empty strings)
                result = self.controller.manage_compliance(
                    action="validate_compliance",
                    operation="create_file",
                    file_path="",
                    content=""
                )
                
                self.mock_orchestrator.validate_operation.assert_called_once_with(
                    operation="create_file",
                    file_path="",
                    content="",
                    user_id="test-user",
                    security_level="public",
                    audit_required=True
                )
    
    def test_boolean_parameter_variations(self):
        """Test various boolean parameter formats."""
        expected_result = {"success": True}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                # Test with explicit boolean values
                for audit_value in [True, False]:
                    self.mock_orchestrator.reset_mock()
                    
                    result = self.controller.manage_compliance(
                        action="validate_compliance",
                        operation="create_file",
                        audit_required=audit_value
                    )
                    
                    self.mock_orchestrator.validate_operation.assert_called_once_with(
                        operation="create_file",
                        file_path=None,
                        content=None,
                        user_id="test-user",
                        security_level="public",
                        audit_required=audit_value
                    )
    
    def test_large_parameter_values(self):
        """Test handling of very large parameter values."""
        large_content = "x" * 10000  # 10KB of content
        large_command = "echo " + "y" * 1000  # Long command
        
        expected_result = {"success": True}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        self.mock_orchestrator.execute_with_compliance.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                # Test large content
                result = self.controller.manage_compliance(
                    action="validate_compliance",
                    operation="create_file",
                    content=large_content
                )
                
                assert result["success"] is True
                
                # Test long command (should be truncated in metadata)
                result = self.controller.manage_compliance(
                    action="execute_with_compliance",
                    command=large_command
                )
                
                assert result["success"] is True
                # Verify command truncation in metadata
                if "metadata" in result:
                    truncated_command = result["metadata"]["command"]
                    assert len(truncated_command) <= 53  # 50 chars + "..."
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in parameters."""
        unicode_content = "Hello 世界! 🌍 Special chars: àáâãäå"
        special_command = "echo 'Special chars: !@#$%^&*()[]{}|\\;:\",.<>?'"
        
        expected_result = {"success": True}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        self.mock_orchestrator.execute_with_compliance.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                # Test unicode content
                result = self.controller.manage_compliance(
                    action="validate_compliance",
                    operation="create_file",
                    content=unicode_content
                )
                
                assert result["success"] is True
                
                # Test special characters in command
                result = self.controller.manage_compliance(
                    action="execute_with_compliance",
                    command=special_command
                )
                
                assert result["success"] is True
    
    def test_concurrent_access_simulation(self):
        """Test behavior under simulated concurrent access."""
        # This tests that the controller handles multiple rapid calls gracefully
        expected_result = {"success": True, "compliance_score": 0.9}
        self.mock_orchestrator.validate_operation.return_value = expected_result
        
        with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.is_default_user_allowed', return_value=True):
            with patch('fastmcp.task_management.interface.controllers.compliance_mcp_controller.AuthConfig.get_fallback_user_id', return_value="test-user"):
                # Simulate multiple rapid calls
                results = []
                for i in range(10):
                    result = self.controller.manage_compliance(
                        action="validate_compliance",
                        operation=f"create_file_{i}",
                        user_id=f"user_{i}"
                    )
                    results.append(result)
                
                # All calls should succeed
                for result in results:
                    assert result["success"] is True
                    assert result["compliance_score"] == 0.9
                
                # All calls should have been made to the orchestrator
                assert self.mock_orchestrator.validate_operation.call_count == 10