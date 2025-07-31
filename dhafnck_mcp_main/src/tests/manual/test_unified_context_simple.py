#!/usr/bin/env python3
"""
Simple test to verify unified context system is working.
"""

import os
from pathlib import Path
import sys

# Set test environment to avoid database conflicts
os.environ["PYTEST_CURRENT_TEST"] = "test_unified_context_simple.py::test_simple"

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController


def main():
    print("Testing Unified Context System...")
    
    # Create factory and controller
    facade_factory = UnifiedContextFacadeFactory()
    controller = UnifiedContextMCPController(facade_factory)
    
    # Create a facade
    facade = facade_factory.create_facade()
    
    # Test creating a task context
    print("\n1. Creating task context...")
    result = facade.create_context(
        level="task",
        context_id="test-task-123",
        data={
            "title": "Test Task",
            "description": "Testing unified context",
            "branch_id": "test-branch-456"
        }
    )
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        print(f"   Created context: {result.get('context', {}).get('id')}")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test getting the context
    print("\n2. Getting task context...")
    result = facade.get_context(
        level="task", 
        context_id="test-task-123"
    )
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        print(f"   Context data: {result.get('context', {}).get('task_data')}")
    
    # Test adding an insight
    print("\n3. Adding insight...")
    result = facade.add_insight(
        level="task",
        context_id="test-task-123",
        content="Found optimization opportunity",
        category="performance",
        importance="high"
    )
    print(f"   Success: {result.get('success')}")
    
    # Test updating context
    print("\n4. Updating context...")
    result = facade.update_context(
        level="task",
        context_id="test-task-123",
        data={"progress": 75}
    )
    print(f"   Success: {result.get('success')}")
    
    # Test resolve (with inheritance)
    print("\n5. Resolving context with inheritance...")
    result = facade.resolve_context(
        level="task",
        context_id="test-task-123"
    )
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        print(f"   Resolved context has {len(result.get('resolved_context', {}))} keys")
    
    # Test delete
    print("\n6. Deleting context...")
    result = facade.delete_context(
        level="task",
        context_id="test-task-123"
    )
    print(f"   Success: {result.get('success')}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()