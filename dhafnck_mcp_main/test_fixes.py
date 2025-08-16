#!/usr/bin/env python3
"""
Test that the fixes work
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository

def main():
    print("Testing fixes for found problems...")
    print("-" * 50)
    
    repo = SupabaseOptimizedRepository()
    
    # Test 1: Integer as status (should now be handled)
    print("\nTest 1: Integer as status")
    try:
        result = repo.list_tasks_minimal(status=123)
        print(f"✅ Handled gracefully, returned {len(result)} results")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    # Test 2: List as status (should now be handled)
    print("\nTest 2: List as status")
    try:
        result = repo.list_tasks_minimal(status=["todo", "done"])
        print(f"✅ Handled gracefully, returned {len(result)} results")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    # Test 3: Dict as priority (additional test)
    print("\nTest 3: Dict as priority")
    try:
        result = repo.list_tasks_minimal(priority={"level": "high"})
        print(f"✅ Handled gracefully, returned {len(result)} results")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    # Test 4: Normal query (should still work)
    print("\nTest 4: Normal query")
    try:
        result = repo.list_tasks_minimal(status="todo", limit=10)
        print(f"✅ Normal query works, returned {len(result)} results")
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
    
    print("\n" + "-" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()