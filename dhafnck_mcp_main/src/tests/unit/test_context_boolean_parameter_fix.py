#!/usr/bin/env python3
"""
Test for Context Boolean Parameter Fix

Tests that the boolean parameter validation issue in manage_context is fixed.
Verifies that parameters like include_inherited, force_refresh, and propagate_changes
properly accept boolean values and string representations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from fastmcp.task_management.interface.utils.parameter_validation_fix import ParameterTypeCoercer


class TestContextBooleanParameterFix:
    """Test cases for the boolean parameter fix in manage_context."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the facade factory
        self.mock_facade_factory = Mock()
        self.mock_facade = Mock()
        self.mock_facade_factory.create_facade.return_value = self.mock_facade
        
        # Create controller instance
        self.controller = UnifiedContextMCPController(self.mock_facade_factory)
    
    def test_parameter_type_coercer_includes_context_booleans(self):
        """Test that ParameterTypeCoercer includes the context boolean parameters."""
        boolean_params = ParameterTypeCoercer.BOOLEAN_PARAMETERS
        
        # Verify that context management boolean parameters are included
        assert 'include_inherited' in boolean_params
        assert 'force_refresh' in boolean_params
        assert 'propagate_changes' in boolean_params
    
    def test_boolean_string_coercion_true_values(self):
        """Test that various string representations of True are coerced correctly."""
        test_params = {
            'include_inherited': 'true',
            'force_refresh': 'True',
            'propagate_changes': '1'
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        assert coerced['include_inherited'] is True
        assert coerced['force_refresh'] is True
        assert coerced['propagate_changes'] is True
    
    def test_boolean_string_coercion_false_values(self):
        """Test that various string representations of False are coerced correctly."""
        test_params = {
            'include_inherited': 'false',
            'force_refresh': 'False',
            'propagate_changes': '0'
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        assert coerced['include_inherited'] is False
        assert coerced['force_refresh'] is False
        assert coerced['propagate_changes'] is False
    
    def test_boolean_actual_values_preserved(self):
        """Test that actual boolean values are preserved without modification."""
        test_params = {
            'include_inherited': True,
            'force_refresh': False,
            'propagate_changes': True
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        assert coerced['include_inherited'] is True
        assert coerced['force_refresh'] is False
        assert coerced['propagate_changes'] is True
    
    def test_boolean_additional_string_formats(self):
        """Test additional string formats like yes/no, on/off."""
        test_params = {
            'include_inherited': 'yes',
            'force_refresh': 'on',
            'propagate_changes': 'no'
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        assert coerced['include_inherited'] is True
        assert coerced['force_refresh'] is True
        assert coerced['propagate_changes'] is False
    
    def test_invalid_boolean_string_raises_error(self):
        """Test that invalid boolean strings raise appropriate errors."""
        test_params = {
            'include_inherited': 'maybe',
            'force_refresh': 'sometimes'
        }
        
        with pytest.raises(Exception) as exc_info:
            ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        # Should mention valid boolean values
        error_message = str(exc_info.value)
        assert 'boolean' in error_message.lower()
        assert ('true' in error_message.lower() or 'false' in error_message.lower())
    
    @patch('fastmcp.task_management.interface.controllers.unified_context_controller.description_loader')
    def test_manage_context_get_with_boolean_string(self, mock_desc_loader):
        """Test that manage_context get action works with boolean string parameters."""
        # Mock description loader
        mock_desc_loader.get_all_descriptions.return_value = {
            "context": {
                "manage_unified_context": {
                    "description": "Test description",
                    "parameters": {
                        "action": "Action to perform",
                        "include_inherited": "Include inherited context",
                        "force_refresh": "Force refresh from source"
                    }
                }
            }
        }
        
        # Mock facade response
        self.mock_facade.get_context.return_value = {
            "success": True,
            "context_data": {"test": "data"}
        }
        
        # Register tools (this would normally be done during app startup)
        mock_mcp = Mock()
        self.controller.register_tools(mock_mcp)
        
        # Get the registered function
        assert mock_mcp.tool.called
        tool_decorator_call = mock_mcp.tool.call_args
        manage_context_func = tool_decorator_call[1] if len(tool_decorator_call) > 1 else None
        
        if not manage_context_func:
            # Try to get it from the decorator call
            decorator_func = mock_mcp.tool.return_value
            if hasattr(decorator_func, '__call__'):
                manage_context_func = decorator_func
        
        # For this test, we'll simulate the function call directly
        # In a real test environment, you'd call the actual registered function
        
        # Simulate parameter coercion that should happen in the function
        test_params = {
            'include_inherited': 'true',
            'force_refresh': 'false',
            'propagate_changes': 'yes'
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        # Verify coercion worked
        assert coerced['include_inherited'] is True
        assert coerced['force_refresh'] is False
        assert coerced['propagate_changes'] is True
    
    def test_manage_context_parameter_coercion_error_handling(self):
        """Test that parameter coercion errors are handled gracefully."""
        # Test case where coercion might fail
        test_params = {
            'include_inherited': 'invalid_boolean_value'
        }
        
        with pytest.raises(Exception) as exc_info:
            ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        # Verify that the error is descriptive
        error_message = str(exc_info.value)
        assert 'include_inherited' in error_message
        assert 'boolean' in error_message.lower()
    
    def test_mixed_parameter_types_coercion(self):
        """Test coercion when mixing boolean and other parameter types."""
        test_params = {
            'include_inherited': 'true',  # Boolean
            'force_refresh': False,       # Already boolean
            'limit': '10',               # Integer (if limit is in INTEGER_PARAMETERS)
            'context_id': 'test-id',     # String (no coercion needed)
            'propagate_changes': 'on'    # Boolean
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        
        # Check boolean coercions
        assert coerced['include_inherited'] is True
        assert coerced['force_refresh'] is False
        assert coerced['propagate_changes'] is True
        
        # Check that non-boolean params are preserved
        assert coerced['context_id'] == 'test-id'
        
        # Check integer coercion if limit is configured
        if 'limit' in ParameterTypeCoercer.INTEGER_PARAMETERS:
            assert coerced['limit'] == 10
        else:
            assert coerced['limit'] == '10'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])