"""
Simple test to isolate the limit parameter validation issue.
This bypasses complex infrastructure to focus on the core MCP validation issue.
"""

import pytest
from typing import Dict, Any, Union
from pydantic import ValidationError


def test_limit_parameter_direct_validation():
    """Test limit parameter validation directly using Pydantic."""
    
    # Let's test the actual Pydantic type annotation used in the controller
    from typing import Optional, Annotated
    from pydantic import Field, TypeAdapter
    
    # This is the exact type annotation from the controller
    LimitType = Annotated[Optional[int], Field(description="Result limit")]
    
    type_adapter = TypeAdapter(LimitType)
    
    # Test cases
    test_cases = [
        {"value": 3, "expected": "success", "description": "integer value"},
        {"value": "3", "expected": "success", "description": "string value (should work with Pydantic)"},
        {"value": None, "expected": "success", "description": "None value"},
    ]
    
    for case in test_cases:
        try:
            result = type_adapter.validate_python(case["value"])
            
            if case["expected"] == "success":
                print(f"✅ PASSED: {case['description']} -> {result}")
                assert result == (3 if case["value"] == "3" else case["value"])
            else:
                pytest.fail(f"Expected error but got success for {case['description']}: {result}")
                
        except ValidationError as e:
            if case["expected"] == "error":
                print(f"✅ EXPECTED ERROR: {case['description']} -> {e}")
                assert "is not valid under any of the given schemas" in str(e) or "Input should be" in str(e)
            else:
                pytest.fail(f"Unexpected validation error for {case['description']}: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error for {case['description']}: {e}")


def test_fastmcp_type_coercion():
    """Test how FastMCP handles type coercion in the tool.py file."""
    
    # Let's test the type coercion logic that exists in FastMCP
    from typing import Optional
    
    # Simulate what FastMCP does in tool.py lines 172-189
    def simulate_fastmcp_coercion(param_name: str, value: Any, target_type: type) -> Any:
        """Simulate FastMCP's type coercion logic."""
        
        if not isinstance(value, str):
            return value
            
        # This is the logic from tool.py
        if target_type in (int, float, bool):
            try:
                if target_type == int:
                    return int(value)
                elif target_type == float:
                    return float(value)
                elif target_type == bool:
                    return value.lower() in ('true', '1', 'yes', 'on')
            except ValueError:
                pass
        
        return value
    
    # Test cases
    test_cases = [
        {"value": "3", "target_type": int, "expected": 3},
        {"value": "3", "target_type": Optional[int], "expected": "3"},  # This is the problem!
        {"value": 3, "target_type": int, "expected": 3},
        {"value": 3, "target_type": Optional[int], "expected": 3},
    ]
    
    for case in test_cases:
        result = simulate_fastmcp_coercion("limit", case["value"], case["target_type"])
        print(f"Input: {case['value']} ({type(case['value'])}), Target: {case['target_type']}, Result: {result} ({type(result)})")
        
        if case["target_type"] == Optional[int] and isinstance(case["value"], str):
            # This is the failing case - FastMCP doesn't handle Optional[int]
            assert result == case["value"]  # String stays as string
            print(f"❌ PROBLEM: String '{case['value']}' not coerced for Optional[int]")
        else:
            assert result == case["expected"]


def test_enhanced_type_coercion():
    """Test our enhanced type coercion solution."""
    
    from typing import Optional
    
    def enhanced_fastmcp_coercion(param_name: str, value: Any, target_type: type) -> Any:
        """Enhanced FastMCP coercion that handles Optional types."""
        
        if not isinstance(value, str):
            return value
        
        # Handle Optional types by extracting the inner type
        import typing
        origin = getattr(target_type, '__origin__', None)
        args = getattr(target_type, '__args__', ())
        
        if origin is typing.Union and len(args) == 2 and type(None) in args:
            # This is Optional[T] which is Union[T, None]
            inner_type = args[0] if args[1] is type(None) else args[1]
            target_type = inner_type
        
        # Now apply the original FastMCP logic
        if target_type in (int, float, bool):
            try:
                if target_type == int:
                    return int(value)
                elif target_type == float:
                    return float(value)
                elif target_type == bool:
                    return value.lower() in ('true', '1', 'yes', 'on')
            except ValueError:
                pass
        
        return value
    
    # Test cases
    test_cases = [
        {"value": "3", "target_type": int, "expected": 3},
        {"value": "3", "target_type": Optional[int], "expected": 3},  # Should work now!
        {"value": 3, "target_type": int, "expected": 3},
        {"value": 3, "target_type": Optional[int], "expected": 3},
        {"value": None, "target_type": Optional[int], "expected": None},
    ]
    
    for case in test_cases:
        result = enhanced_fastmcp_coercion("limit", case["value"], case["target_type"])
        print(f"Enhanced: Input: {case['value']} ({type(case['value'])}), Target: {case['target_type']}, Result: {result} ({type(result)})")
        assert result == case["expected"]
        
    print("✅ Enhanced type coercion works for Optional[int]!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])