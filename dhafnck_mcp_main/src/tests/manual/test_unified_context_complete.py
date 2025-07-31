#!/usr/bin/env python3
"""
Complete test for unified context system with proper hierarchy.
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import os
os.chdir("/home/daihungpham/agentic-project/dhafnck_mcp_main/src")
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory

def main():
    """Test the unified context system with proper hierarchy setup."""
    print("Testing Unified Context System with Proper Hierarchy...")
    
    try:
        # Initialize factory and facade
        factory = UnifiedContextFacadeFactory()
        facade = factory.create_facade()
        
        print("✅ Factory and facade initialized successfully")
        
        # 1. Create project context first
        print("\n1. Creating project context...")
        project_result = facade.create_context(
            level="project",
            context_id="test-project-789",
            data={
                "project_name": "Test Project",
                "project_settings": {"environment": "test"},
                "metadata": {"created_by": "unified_test"}
            }
        )
        print(f"   Success: {project_result.get('success')}")
        if not project_result.get('success'):
            print(f"   Error: {project_result.get('error')}")
            return
        
        # 2. Create branch context
        print("\n2. Creating branch context...")
        branch_result = facade.create_context(
            level="branch",
            context_id="test-branch-456",
            data={
                "project_id": "test-project-789",
                "git_branch_name": "feature/test",
                "branch_settings": {"auto_deploy": False},
                "metadata": {"created_by": "unified_test"}
            }
        )
        print(f"   Success: {branch_result.get('success')}")
        if not branch_result.get('success'):
            print(f"   Error: {branch_result.get('error')}")
            return
        
        # 3. Create task context
        print("\n3. Creating task context...")
        task_result = facade.create_context(
            level="task",
            context_id="test-task-123",
            data={
                "branch_id": "test-branch-456",
                "task_data": {
                    "title": "Test Task",
                    "description": "Testing unified context system",
                    "status": "in_progress"
                },
                "metadata": {"created_by": "unified_test"}
            }
        )
        print(f"   Success: {task_result.get('success')}")
        if not task_result.get('success'):
            print(f"   Error: {task_result.get('error')}")
            return
        
        # 4. Get task context
        print("\n4. Getting task context...")
        get_result = facade.get_context(
            level="task",
            context_id="test-task-123"
        )
        print(f"   Success: {get_result.get('success')}")
        if get_result.get('success'):
            context = get_result.get('context', {})
            print(f"   Found context with {len(context)} fields")
        else:
            print(f"   Error: {get_result.get('error')}")
        
        # 5. Add insight
        print("\n5. Adding insight...")
        insight_result = facade.add_insight(
            level="task",
            context_id="test-task-123",
            content="Found reusable authentication pattern",
            category="discovery",
            importance="high"
        )
        print(f"   Success: {insight_result.get('success')}")
        if not insight_result.get('success'):
            print(f"   Error: {insight_result.get('error')}")
        
        # 6. Update context
        print("\n6. Updating context...")
        update_result = facade.update_context(
            level="task",
            context_id="test-task-123",
            data={
                "progress": 75,
                "additional_notes": "Making good progress"
            }
        )
        print(f"   Success: {update_result.get('success')}")
        if not update_result.get('success'):
            print(f"   Error: {update_result.get('error')}")
        
        # 7. Resolve with inheritance
        print("\n7. Resolving context with inheritance...")
        resolve_result = facade.resolve_context(
            level="task",
            context_id="test-task-123"
        )
        print(f"   Success: {resolve_result.get('success')}")
        if resolve_result.get('success'):
            context = resolve_result.get('context', {})
            print(f"   Resolved context has {len(context)} keys")
        else:
            print(f"   Error: {resolve_result.get('error')}")
        
        # 8. List contexts
        print("\n8. Listing task contexts...")
        list_result = facade.list_contexts(level="task")
        print(f"   Success: {list_result.get('success')}")
        if list_result.get('success'):
            contexts = list_result.get('contexts', [])
            print(f"   Found {len(contexts)} task contexts")
        else:
            print(f"   Error: {list_result.get('error')}")
        
        # 9. Clean up - delete contexts in reverse order
        print("\n9. Cleaning up...")
        
        # Delete task context
        delete_task = facade.delete_context(level="task", context_id="test-task-123")
        print(f"   Delete task: {delete_task.get('success')}")
        
        # Delete branch context
        delete_branch = facade.delete_context(level="branch", context_id="test-branch-456")
        print(f"   Delete branch: {delete_branch.get('success')}")
        
        # Delete project context
        delete_project = facade.delete_context(level="project", context_id="test-project-789")
        print(f"   Delete project: {delete_project.get('success')}")
        
        print("\n✅ Unified Context System test complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()