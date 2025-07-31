#!/usr/bin/env python3
"""
Quick test to verify the subtask fix works correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from uuid import uuid4

def test_subtask_response_structure():
    """Test that subtask creation returns proper single-level nesting."""
    print("🧪 Testing subtask response structure...")
    
    # Create a mock git branch ID
    git_branch_id = str(uuid4())
    
    # Create repositories
    task_repository = ORMTaskRepository(git_branch_id=git_branch_id)
    subtask_repository = ORMSubtaskRepository()
    
    # Create facades
    task_facade = TaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
    subtask_facade = SubtaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
    
    # Create a task
    task_request = CreateTaskRequest(
        title="Test Task for Subtask Structure",
        git_branch_id=git_branch_id,
        description="Testing subtask response structure",
        priority="medium"
    )
    
    try:
        task_result = task_facade.create_task(task_request)
        task_id = task_result['task']['id']
        print(f"✅ Task created: {task_id}")
        
        # Create a subtask
        subtask_result = subtask_facade.handle_manage_subtask(
            action="create",
            task_id=task_id,
            subtask_data={
                "title": "Test Subtask",
                "description": "Testing subtask response structure"
            }
        )
        
        print(f"✅ Subtask created successfully!")
        print(f"📊 Response structure: {list(subtask_result.keys())}")
        
        # Check the response structure
        assert 'success' in subtask_result
        assert 'subtask' in subtask_result
        assert 'task_id' in subtask_result
        assert 'progress' in subtask_result
        
        # Check that subtask data is accessible directly (not double nested)
        subtask_data = subtask_result['subtask']
        assert 'id' in subtask_data
        assert 'title' in subtask_data
        
        # Try to access with single nesting (should work)
        subtask_id = subtask_result['subtask']['id']
        print(f"✅ Subtask ID accessible with single nesting: {subtask_id}")
        
        # Try to access with double nesting (should fail)
        try:
            double_nested_id = subtask_result['subtask']['subtask']['id']
            print(f"❌ Double nesting still exists: {double_nested_id}")
            return False
        except KeyError:
            print("✅ Double nesting removed successfully!")
            return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing subtask response structure fix...")
    success = test_subtask_response_structure()
    if success:
        print("\n🎉 All tests passed! Subtask double nesting fix is working correctly.")
    else:
        print("\n❌ Tests failed. Double nesting issue may still exist.")
        sys.exit(1)