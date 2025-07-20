#!/usr/bin/env python3
"""
Parameter Validation Fix Implementation

This module implements the type coercion functionality to fix the parameter validation issue:
"Input validation error: '5' is not valid under any of the given schemas"

Key Features:
- Type coercion for string integers to integers
- Type coercion for string booleans to booleans  
- Flexible schema validation supporting multiple types
- Comprehensive error handling with helpful messages
"""

import json
import logging
import re
from typing import Dict, Any, Union, List, Optional, Pattern

logger = logging.getLogger(__name__)


class ParameterTypeCoercionError(Exception):
    """Custom exception for parameter type coercion errors"""
    def __init__(self, parameter: str, value: Any, expected_type: str, message: str = None):
        self.parameter = parameter
        self.value = value
        self.expected_type = expected_type
        self.message = message or f"Parameter '{parameter}' must be a valid {expected_type}"
        super().__init__(self.message)


class ParameterTypeCoercer:
    """
    Handles type coercion for MCP parameters to fix validation issues.
    """
    
    # Define which parameters should be coerced to integers
    INTEGER_PARAMETERS = {
        'limit', 'progress_percentage', 'timeout', 'port', 'offset',
        'head_limit', 'thought_number', 'total_thoughts', 'revises_thought',
        'branch_from_thought'
    }
    
    # Define which parameters should be coerced to booleans
    BOOLEAN_PARAMETERS = {
        'include_context', 'force', 'audit_required', 'include_details',
        'propagate_changes', 'force_refresh', 'include_inherited',
        'next_thought_needed', 'is_revision', 'needs_more_thoughts', 
        'replace_all', 'multiline'
    }
    
    # Define which parameters should be coerced to lists/arrays
    LIST_PARAMETERS = {
        'insights_found', 'assignees', 'labels', 'tags', 'dependencies',
        'challenges_overcome', 'deliverables', 'next_recommendations',
        'skills_learned'
    }
    
    # Boolean string values that should be considered True
    TRUE_VALUES = {'true', '1', 'yes', 'on', 'enabled', 'enable'}
    
    # Boolean string values that should be considered False  
    FALSE_VALUES = {'false', '0', 'no', 'off', 'disabled', 'disable'}
    
    @classmethod
    def coerce_parameter_types(cls, params: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert parameter types to match expected types.
        
        Args:
            params: Dictionary of parameters to coerce
            schema: Optional schema for validation (future use)
            
        Returns:
            Dictionary with coerced parameter types
            
        Raises:
            ParameterTypeCoercionError: If coercion fails
        """
        if not params:
            return params
            
        coerced = params.copy()
        
        # Coerce integer parameters
        for param_name in cls.INTEGER_PARAMETERS:
            if param_name in coerced:
                coerced[param_name] = cls._coerce_to_integer(param_name, coerced[param_name])
        
        # Coerce boolean parameters
        for param_name in cls.BOOLEAN_PARAMETERS:
            if param_name in coerced:
                coerced[param_name] = cls._coerce_to_boolean(param_name, coerced[param_name])
        
        # Coerce list parameters
        for param_name in cls.LIST_PARAMETERS:
            if param_name in coerced:
                coerced[param_name] = cls._coerce_to_list(param_name, coerced[param_name])
        
        return coerced
    
    @classmethod
    def _coerce_to_integer(cls, param_name: str, value: Any) -> int:
        """
        Coerce a value to integer with helpful error messages.
        
        Args:
            param_name: Name of the parameter being coerced
            value: Value to coerce
            
        Returns:
            Integer value
            
        Raises:
            ParameterTypeCoercionError: If coercion fails
        """
        # If already an integer, return as-is
        if isinstance(value, int):
            return value
            
        # If it's a string, try to convert
        if isinstance(value, str):
            # Handle empty strings
            if not value.strip():
                raise ParameterTypeCoercionError(
                    param_name, value, "integer",
                    f"Parameter '{param_name}' cannot be empty when expecting an integer"
                )
            
            # Try to convert to integer
            try:
                return int(value)
            except ValueError:
                raise ParameterTypeCoercionError(
                    param_name, value, "integer",
                    f"Parameter '{param_name}' value '{value}' cannot be converted to integer"
                )
        
        # If it's a float, check if it's a whole number
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            else:
                raise ParameterTypeCoercionError(
                    param_name, value, "integer",
                    f"Parameter '{param_name}' value {value} is not a whole number"
                )
        
        # For any other type, raise an error
        raise ParameterTypeCoercionError(
            param_name, value, "integer",
            f"Parameter '{param_name}' value {value} (type: {type(value).__name__}) cannot be converted to integer"
        )
    
    @classmethod
    def _coerce_to_boolean(cls, param_name: str, value: Any) -> bool:
        """
        Coerce a value to boolean with helpful error messages.
        
        Args:
            param_name: Name of the parameter being coerced
            value: Value to coerce
            
        Returns:
            Boolean value
            
        Raises:
            ParameterTypeCoercionError: If coercion fails
        """
        # If already a boolean, return as-is
        if isinstance(value, bool):
            return value
            
        # If it's a string, try to convert
        if isinstance(value, str):
            value_lower = value.lower().strip()
            
            if value_lower in cls.TRUE_VALUES:
                return True
            elif value_lower in cls.FALSE_VALUES:
                return False
            else:
                raise ParameterTypeCoercionError(
                    param_name, value, "boolean",
                    f"Parameter '{param_name}' value '{value}' is not a valid boolean. "
                    f"Valid true values: {cls.TRUE_VALUES}. "
                    f"Valid false values: {cls.FALSE_VALUES}"
                )
        
        # For integers, use Python's truthiness but be explicit
        if isinstance(value, int):
            return bool(value)
        
        # For any other type, use Python's truthiness but warn
        logger.warning(f"Parameter '{param_name}' received unexpected type {type(value).__name__}, "
                      f"using Python truthiness evaluation")
        return bool(value)
    
    @classmethod
    def _coerce_to_list(cls, param_name: str, value: Any) -> List[str]:
        """
        Coerce a value to list with helpful error messages.
        
        Args:
            param_name: Name of the parameter being coerced
            value: Value to coerce
            
        Returns:
            List value
            
        Raises:
            ParameterTypeCoercionError: If coercion fails
        """
        # If already a list, return as-is
        if isinstance(value, list):
            return value
            
        # If it's a string, try to parse as JSON array
        if isinstance(value, str):
            # Handle empty strings
            if not value.strip():
                return []
            
            # Try to parse as JSON array
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    # Convert all items to strings for consistency
                    return [str(item) for item in parsed]
                else:
                    # If JSON parsed but not a list, wrap in list
                    return [str(parsed)]
            except json.JSONDecodeError:
                # If not valid JSON, treat as comma-separated string
                if ',' in value:
                    # Split by comma and clean up
                    items = [item.strip() for item in value.split(',')]
                    return [item for item in items if item]  # Remove empty strings
                else:
                    # Single string value, wrap in list
                    return [value.strip()]
        
        # If it's any other iterable (tuple, set, etc.), convert to list
        try:
            return list(value)
        except TypeError:
            # If not iterable, wrap single value in list
            return [str(value)]


class FlexibleSchemaValidator:
    """
    Validates parameters using flexible schemas that support multiple types.
    """
    
    @classmethod
    def create_flexible_schema(cls, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a restrictive schema to a flexible one that accepts both integers and strings.
        
        Args:
            original_schema: The original restrictive schema
            
        Returns:
            Flexible schema that accepts multiple types
        """
        if "properties" not in original_schema:
            return original_schema
            
        flexible_schema = original_schema.copy()
        flexible_properties = {}
        
        for prop_name, prop_schema in original_schema["properties"].items():
            flexible_properties[prop_name] = cls._make_property_flexible(prop_name, prop_schema)
        
        flexible_schema["properties"] = flexible_properties
        return flexible_schema
    
    @classmethod
    def _make_property_flexible(cls, prop_name: str, prop_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a single property schema flexible.
        
        Args:
            prop_name: Name of the property
            prop_schema: Original property schema
            
        Returns:
            Flexible property schema
        """
        if not isinstance(prop_schema, dict):
            return prop_schema
            
        prop_type = prop_schema.get("type")
        
        # Handle integer properties
        if prop_type == "integer":
            return cls._create_flexible_integer_schema(prop_name, prop_schema)
        
        # Handle boolean properties  
        elif prop_type == "boolean":
            return cls._create_flexible_boolean_schema(prop_name, prop_schema)
        
        # Handle array/list properties
        elif prop_type == "array":
            return cls._create_flexible_array_schema(prop_name, prop_schema)
        
        # For other types, return as-is
        return prop_schema
    
    @classmethod
    def _create_flexible_integer_schema(cls, prop_name: str, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a flexible schema for integer properties that accepts both integers and string integers.
        """
        minimum = original_schema.get("minimum")
        maximum = original_schema.get("maximum")
        
        # Create the integer schema
        integer_schema = {"type": "integer"}
        if minimum is not None:
            integer_schema["minimum"] = minimum
        if maximum is not None:
            integer_schema["maximum"] = maximum
        
        # Create the string schema with pattern for numeric strings
        string_schema = {"type": "string"}
        
        # Build regex pattern based on constraints
        if minimum is not None and maximum is not None:
            # For specific ranges like 0-100, create a specific pattern
            if minimum == 0 and maximum == 100:
                string_schema["pattern"] = "^(100|[1-9]?[0-9])$"
            elif minimum == 1 and maximum == 100:
                string_schema["pattern"] = "^[1-9][0-9]?$|^100$"
            elif minimum == 1 and maximum == 65535:  # Port range
                string_schema["pattern"] = "^([1-9][0-9]{0,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
            else:
                # Generic pattern for positive integers
                string_schema["pattern"] = "^[0-9]+$"
        elif minimum is not None and minimum >= 0:
            # Non-negative integers
            string_schema["pattern"] = "^[0-9]+$"
        else:
            # Any integer (including negative)
            string_schema["pattern"] = "^-?[0-9]+$"
        
        # Return anyOf schema
        return {
            "anyOf": [integer_schema, string_schema],
            "description": f"Accepts integer or string representation for {prop_name}"
        }
    
    @classmethod
    def _create_flexible_boolean_schema(cls, prop_name: str, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a flexible schema for boolean properties that accepts booleans and string booleans.
        """
        return {
            "anyOf": [
                {"type": "boolean"},
                {
                    "type": "string",
                    "pattern": "^(true|false|True|False|TRUE|FALSE|1|0|yes|no|Yes|No|YES|NO|on|off|On|Off|ON|OFF)$"
                }
            ],
            "description": f"Accepts boolean or string representation for {prop_name}"
        }
    
    @classmethod
    def _create_flexible_array_schema(cls, prop_name: str, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a flexible schema for array properties that accepts arrays, strings, and JSON string arrays.
        """
        # Get the items schema from the original array schema
        items_schema = original_schema.get("items", {"type": "string"})
        
        return {
            "anyOf": [
                # Original array schema
                {
                    "type": "array",
                    "items": items_schema
                },
                # JSON string representation of array
                {
                    "type": "string",
                    "description": "JSON string representation of array (e.g., '[\"item1\", \"item2\"]')"
                },
                # Comma-separated string
                {
                    "type": "string", 
                    "pattern": "^[^\\[\\]]*$",  # No square brackets (to distinguish from JSON)
                    "description": "Comma-separated string (e.g., 'item1, item2, item3')"
                }
            ],
            "description": f"Accepts array, JSON string array, or comma-separated string for {prop_name}"
        }


class EnhancedParameterValidator:
    """
    Enhanced parameter validator that combines type coercion with validation.
    """
    
    def __init__(self, enable_coercion: bool = True, enable_flexible_schemas: bool = True):
        """
        Initialize the enhanced validator.
        
        Args:
            enable_coercion: Whether to enable automatic type coercion
            enable_flexible_schemas: Whether to use flexible schemas
        """
        self.enable_coercion = enable_coercion
        self.enable_flexible_schemas = enable_flexible_schemas
        self.coercer = ParameterTypeCoercer()
        self.schema_validator = FlexibleSchemaValidator()
    
    def validate_parameters(self, action: str, params: Dict[str, Any], 
                          schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate parameters with optional type coercion.
        
        Args:
            action: The action being performed
            params: Parameters to validate
            schema: Optional schema for validation
            
        Returns:
            Dictionary with validation result and coerced parameters
        """
        try:
            # Step 1: Type coercion (if enabled)
            if self.enable_coercion:
                coerced_params = self.coercer.coerce_parameter_types(params, schema)
            else:
                coerced_params = params.copy()
            
            # Step 2: Schema validation (if schema provided)
            if schema:
                if self.enable_flexible_schemas:
                    flexible_schema = self.schema_validator.create_flexible_schema(schema)
                    validation_result = self._validate_against_schema(coerced_params, flexible_schema)
                else:
                    validation_result = self._validate_against_schema(coerced_params, schema)
                
                if not validation_result["success"]:
                    return validation_result
            
            # Step 3: Action-specific validation
            action_validation = self._validate_action_specific(action, coerced_params)
            if not action_validation["success"]:
                return action_validation
            
            # Success
            return {
                "success": True,
                "coerced_params": coerced_params,
                "action": action,
                "validation_notes": "Parameter validation and coercion completed successfully"
            }
            
        except ParameterTypeCoercionError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "PARAMETER_COERCION_ERROR",
                "parameter": e.parameter,
                "provided_value": str(e.value),
                "expected_type": e.expected_type,
                "hint": "Check parameter format and try again"
            }
        except Exception as e:
            logger.error(f"Unexpected error in parameter validation: {e}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "error_code": "VALIDATION_ERROR",
                "hint": "Please check parameter format and try again"
            }
    
    def _validate_against_schema(self, params: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against a schema.
        
        Args:
            params: Parameters to validate
            schema: Schema to validate against
            
        Returns:
            Validation result
        """
        # This is a placeholder - in a real implementation, you would use jsonschema
        # For now, we'll do basic validation
        
        if "properties" not in schema:
            return {"success": True}
            
        for param_name, param_schema in schema["properties"].items():
            if param_name in params:
                param_value = params[param_name]
                validation_result = self._validate_single_parameter(param_name, param_value, param_schema)
                if not validation_result["success"]:
                    return validation_result
        
        return {"success": True}
    
    def _validate_single_parameter(self, param_name: str, value: Any, param_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single parameter against its schema.
        """
        # Handle anyOf schemas (flexible schemas)
        if "anyOf" in param_schema:
            for sub_schema in param_schema["anyOf"]:
                result = self._validate_single_parameter(param_name, value, sub_schema)
                if result["success"]:
                    return result
            # If none of the anyOf schemas matched
            return {
                "success": False,
                "error": f"Parameter '{param_name}' with value '{value}' does not match any of the allowed schemas",
                "error_code": "SCHEMA_VALIDATION_ERROR"
            }
        
        # Handle specific type validation
        expected_type = param_schema.get("type")
        if expected_type:
            if expected_type == "integer" and not isinstance(value, int):
                return {
                    "success": False,
                    "error": f"Parameter '{param_name}' expected integer, got {type(value).__name__}",
                    "error_code": "TYPE_MISMATCH"
                }
            elif expected_type == "boolean" and not isinstance(value, bool):
                return {
                    "success": False,
                    "error": f"Parameter '{param_name}' expected boolean, got {type(value).__name__}",
                    "error_code": "TYPE_MISMATCH"
                }
            elif expected_type == "string" and not isinstance(value, str):
                return {
                    "success": False,
                    "error": f"Parameter '{param_name}' expected string, got {type(value).__name__}",
                    "error_code": "TYPE_MISMATCH"
                }
        
        # Handle range validation for integers
        if isinstance(value, int):
            minimum = param_schema.get("minimum")
            maximum = param_schema.get("maximum")
            
            if minimum is not None and value < minimum:
                return {
                    "success": False,
                    "error": f"Parameter '{param_name}' value {value} is below minimum {minimum}",
                    "error_code": "VALUE_TOO_LOW"
                }
            
            if maximum is not None and value > maximum:
                return {
                    "success": False,
                    "error": f"Parameter '{param_name}' value {value} is above maximum {maximum}",
                    "error_code": "VALUE_TOO_HIGH"
                }
        
        # Handle pattern validation for strings
        if isinstance(value, str) and "pattern" in param_schema:
            pattern = param_schema["pattern"]
            if not re.match(pattern, value):
                return {
                    "success": False,
                    "error": f"Parameter '{param_name}' value '{value}' does not match required pattern",
                    "error_code": "PATTERN_MISMATCH"
                }
        
        return {"success": True}
    
    def _validate_action_specific(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform action-specific validation.
        """
        # Add action-specific validation logic here
        # For now, just return success
        return {"success": True}


# Main functions to be used by the application

def coerce_parameter_types(params: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Public function to coerce parameter types.
    
    Args:
        params: Parameters to coerce
        schema: Optional schema (for future use)
        
    Returns:
        Dictionary with coerced parameters
        
    Raises:
        ValueError: If coercion fails
    """
    try:
        return ParameterTypeCoercer.coerce_parameter_types(params, schema)
    except ParameterTypeCoercionError as e:
        raise ValueError(str(e))


def validate_parameters(action: str, params: Dict[str, Any], 
                       schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Public function to validate parameters with coercion.
    
    Args:
        action: Action being performed
        params: Parameters to validate
        schema: Optional schema for validation
        
    Returns:
        Validation result dictionary
    """
    validator = EnhancedParameterValidator()
    return validator.validate_parameters(action, params, schema)


def create_flexible_schema(original_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public function to create flexible schemas.
    
    Args:
        original_schema: Original restrictive schema
        
    Returns:
        Flexible schema that accepts multiple types
    """
    return FlexibleSchemaValidator.create_flexible_schema(original_schema)


# Test function to demonstrate the fix
def test_parameter_validation_fix():
    """
    Test function to demonstrate that the parameter validation fix works.
    """
    print("🧪 Testing Parameter Validation Fix")
    print("=" * 40)
    
    test_cases = [
        # Integer as string
        {"action": "search", "params": {"query": "test", "limit": "5"}},
        # Integer as actual int  
        {"action": "search", "params": {"query": "test", "limit": 5}},
        # Progress as string
        {"action": "update", "params": {"task_id": "test", "progress_percentage": "50"}},
        # Progress as int
        {"action": "update", "params": {"task_id": "test", "progress_percentage": 50}},
        # Boolean as string
        {"action": "get", "params": {"task_id": "test", "include_context": "true"}},
        # Boolean as actual bool
        {"action": "get", "params": {"task_id": "test", "include_context": True}},
        # List as JSON string (the original issue)
        {"action": "complete", "params": {"task_id": "test", "insights_found": '["Using jest-mock-extended library", "Test cases should cover edge cases"]'}},
        # List as comma-separated string
        {"action": "complete", "params": {"task_id": "test", "insights_found": "insight1, insight2, insight3"}},
        # List as actual list
        {"action": "complete", "params": {"task_id": "test", "insights_found": ["insight1", "insight2"]}},
        # Empty list as empty string
        {"action": "complete", "params": {"task_id": "test", "insights_found": ""}},
        # Single item as string (should become list)
        {"action": "complete", "params": {"task_id": "test", "insights_found": "single insight"}},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['action']} with {case['params']}")
        try:
            result = validate_parameters(case["action"], case["params"])
            if result["success"]:
                print(f"✅ PASSED: {result['coerced_params']}")
            else:
                print(f"❌ FAILED: {result['error']}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n🎯 Parameter Validation Fix Test Complete!")


if __name__ == "__main__":
    test_parameter_validation_fix()