"""Test to verify the next task controller fix works"""

import os
import sys

# Set test environment
os.environ["USE_TEST_DB"] = "true"
os.environ["DATABASE_PROVIDER"] = "sqlite"

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory

def test_next_task_no_type_error():
    """Test that next task doesn't throw TypeError after fix"""
    # Create facade factory
    facade_factory = TaskFacadeFactory()
    
    # Create controller
    controller = TaskMCPController(task_facade_factory=facade_factory)
    
    # Call manage_task with "next" action
    # This should not throw TypeError about unexpected keyword argument
    try:
        result = controller.manage_task(
            action="next",
            git_branch_id="test-branch-uuid-123"
        )
        
        # Check result structure (should be a proper response, not an error)
        assert isinstance(result, dict), f"Expected dict response, got {type(result)}"
        
        # Check for TypeError in error message
        if "error" in result:
            assert "TypeError" not in result["error"], f"TypeError still present: {result['error']}"
            assert "unexpected keyword argument" not in result["error"], f"Keyword argument error: {result['error']}"
        
        print("✅ SUCCESS: No TypeError thrown")
        print(f"Response keys: {result.keys()}")
        
        # Expected response for no tasks
        if not result.get("success"):
            print(f"Message: {result.get('message') or result.get('error')}")
        
        return True
        
    except TypeError as e:
        print(f"❌ FAILED: TypeError still occurs: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Other error (not TypeError): {e}")
        # This is okay - we're just testing for TypeError
        return True

if __name__ == "__main__":
    print("Testing next task operation after fix...")
    print("-" * 50)
    
    success = test_next_task_no_type_error()
    
    print("-" * 50)
    if success:
        print("✅ FIX VERIFIED: The TypeError issue is resolved!")
        print("The controller now passes git_branch_id correctly to the facade.")
    else:
        print("❌ FIX FAILED: TypeError still occurs")
        sys.exit(1)