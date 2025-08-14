#!/usr/bin/env python3
"""
Debug script to test task dependency retrieval issue
"""

import json
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dhafnck_mcp_main', 'src'))

def test_task_dependencies():
    """Test task dependency retrieval with existing tasks"""
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
    from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
    
    # Setup database
    db_config = get_db_config()
    
    # First, let's list existing tasks to see what we have
    print("Listing existing tasks...")
    task_repo = ORMTaskRepository()  # No git_branch_id filter
    all_tasks = task_repo.find_all()
    
    if not all_tasks:
        print("No tasks found in database")
        return
    
    print(f"Found {len(all_tasks)} task(s):")
    for task in all_tasks[:5]:  # Show first 5 tasks
        print(f"  - ID: {task.id}, Title: {task.title}")
        print(f"    Dependencies: {task.get_dependency_ids()}")
    
    # Get the first task for testing
    test_task = all_tasks[0]
    print(f"\nTesting with task: {test_task.id}")
    
    # Create facade and test retrieval
    facade = TaskApplicationFacade(task_repo)
    result = facade.get_task(str(test_task.id), include_context=False, include_dependencies=True)
    
    print("\nResult structure:")
    print(json.dumps(result, indent=2, default=str))
    
    # Check if dependencies are in the response
    if result.get("success"):
        if "task" in result:
            task_data = result["task"]
            print(f"\nTask dependencies found: {task_data.get('dependencies', [])}")
            print(f"Dependency relationships: {bool(task_data.get('dependency_relationships'))}")
        else:
            print("No task data in response")
    else:
        print(f"Task retrieval failed: {result.get('error')}")

if __name__ == "__main__":
    test_task_dependencies()