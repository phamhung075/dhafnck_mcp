#!/usr/bin/env python3
"""
Test for insights_found parameter fix
This script tests that the fix for subtask insights_found parameter accepting arrays works correctly.
"""

import sys
import os
import logging

# Add the source path to PYTHONPATH
sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

# Configure logging to reduce noise during testing
logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)

from fastmcp.task_management.interface.utils.parameter_validation_fix import ParameterTypeCoercer

def test_insights_found_coercion():
    """Test that insights_found parameter can be coerced from various formats."""
    
    print("🧪 Testing insights_found Parameter Coercion")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "JSON string array (original issue)",
            "params": {
                "insights_found": '["Using jest-mock-extended library simplifies JWT library mocking", "Test cases should cover edge cases like empty payload and expired secrets"]'
            },
            "expected": ["Using jest-mock-extended library simplifies JWT library mocking", "Test cases should cover edge cases like empty payload and expired secrets"]
        },
        {
            "name": "Comma-separated string",
            "params": {
                "insights_found": "insight1, insight2, insight3"
            },
            "expected": ["insight1", "insight2", "insight3"]
        },
        {
            "name": "Single string",
            "params": {
                "insights_found": "single insight"
            },
            "expected": ["single insight"]
        },
        {
            "name": "Empty string",
            "params": {
                "insights_found": ""
            },
            "expected": []
        },
        {
            "name": "Already a list",
            "params": {
                "insights_found": ["already", "a", "list"]
            },
            "expected": ["already", "a", "list"]
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['name']}")
        print(f"Input: {case['params']}")
        
        try:
            result = ParameterTypeCoercer.coerce_parameter_types(case['params'])
            actual = result.get('insights_found')
            expected = case['expected']
            
            if actual == expected:
                print(f"✅ PASSED - Result: {actual}")
            else:
                print(f"❌ FAILED - Expected: {expected}, Got: {actual}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print(f"\n🎯 Test Complete - {'All tests passed!' if all_passed else 'Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    success = test_insights_found_coercion()
    sys.exit(0 if success else 1)