#!/usr/bin/env python3
"""
Quick integration test to verify user context propagation fix.
"""

import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_context_propagation():
    """Test that user context propagates to MCP tool execution."""
    
    # Create a mock user context
    mock_user_context = Mock()
    mock_user_context.user_id = "test-user-123"
    mock_user_context.email = "test@example.com" 
    mock_user_context.roles = ["user"]
    
    # Create a simple test tool
    def test_tool():
        from fastmcp.auth.mcp_integration.user_context_middleware import get_current_user_id
        return get_current_user_id()
    
    # Import and create tool
    from fastmcp.tools.tool import FunctionTool
    tool = FunctionTool.from_function(test_tool)
    
    # Mock the user context to return our test context
    with patch('fastmcp.auth.mcp_integration.user_context_middleware.get_current_user_context') as mock_get_context:
        mock_get_context.return_value = mock_user_context
        
        with patch('fastmcp.auth.mcp_integration.user_context_middleware.current_user_context') as mock_context_var:
            mock_context_var.set = Mock()
            
            print("Running tool with mocked user context...")
            try:
                result = await tool.run({})
                print("✅ Tool execution completed successfully!")
                print(f"Result: {result}")
                
                # Verify context was set
                mock_context_var.set.assert_called_once_with(mock_user_context)
                print("✅ User context was properly set during tool execution!")
                
            except Exception as e:
                print(f"❌ Tool execution failed: {e}")
                return False
    
    return True

async def test_without_context():
    """Test that tools work without user context."""
    
    def simple_tool():
        return "Hello World"
    
    from fastmcp.tools.tool import FunctionTool
    tool = FunctionTool.from_function(simple_tool)
    
    with patch('fastmcp.auth.mcp_integration.user_context_middleware.get_current_user_context') as mock_get_context:
        mock_get_context.return_value = None
        
        print("Running tool without user context...")
        try:
            result = await tool.run({})
            print("✅ Tool execution without context completed successfully!")
            print(f"Result: {result}")
            return True
        except Exception as e:
            print(f"❌ Tool execution failed: {e}")
            return False

if __name__ == "__main__":
    print("🧪 Testing FastMCP User Context Propagation Fix")
    print("=" * 50)
    
    try:
        # Test with context
        success1 = asyncio.run(test_context_propagation())
        
        print()
        
        # Test without context  
        success2 = asyncio.run(test_without_context())
        
        print()
        print("=" * 50)
        if success1 and success2:
            print("🎉 ALL TESTS PASSED!")
            print("✅ User context propagation is working correctly")
        else:
            print("❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)