#!/usr/bin/env python3
"""
Test script to verify dependency management fix
"""

import json
import sys
import os
from uuid import uuid4

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dhafnck_mcp_main', 'src'))

def test_dependency_management_fix():
    """Test that dependencies can be added even for completed tasks"""
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
    from fastmcp.task_management.application.use_cases.manage_dependencies import ManageDependenciesUseCase, AddDependencyRequest
    from fastmcp.task_management.domain.entities.task import Task
    from fastmcp.task_management.domain.value_objects.task_id import TaskId
    from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
    from fastmcp.task_management.domain.value_objects.priority import Priority
    
    # Setup database
    db_config = get_db_config()
    
    print("Testing dependency management fix...")
    
    # Create test branch ID (must exist in database for foreign key constraints)
    # Let's use an existing branch from the database
    task_repo = ORMTaskRepository()
    all_tasks = task_repo.find_all()
    
    if not all_tasks:
        print("No tasks found - cannot test without existing data")
        return
        
    # Use the git_branch_id from an existing task
    test_branch_id = all_tasks[0].git_branch_id
    print(f"Using existing branch ID: {test_branch_id}")
    
    # Create task repository with the existing branch
    task_repo = ORMTaskRepository(git_branch_id=test_branch_id)
    
    # Create dependency management use case
    dependency_use_case = ManageDependenciesUseCase(task_repo)
    
    # Create task 1 (will be marked as completed)
    task1_id = str(uuid4())
    task1 = Task.create(
        id=TaskId(task1_id),
        title="Completed Dependency Task",
        description="This task will be completed and used as dependency",
        git_branch_id=test_branch_id
    )
    
    # Create task 2 (active task that will depend on task1)
    task2_id = str(uuid4())
    task2 = Task.create(
        id=TaskId(task2_id),
        title="Active Task with Dependency",
        description="This task will depend on the completed task",
        git_branch_id=test_branch_id
    )
    
    # Save both tasks as active first
    print("Saving initial tasks...")
    task_repo.save(task1)
    task_repo.save(task2)
    
    # Complete task1 (mark as done) - need to transition through in_progress first
    task1.update_status(TaskStatus.in_progress())
    task1.update_status(TaskStatus.done())
    task_repo.save(task1)
    print(f"Task1 ({task1_id}) marked as completed")
    
    # Now try to add the completed task as a dependency to the active task
    print("Testing dependency addition...")
    try:
        request = AddDependencyRequest(
            task_id=task2_id,
            dependency_id=task1_id
        )
        
        result = dependency_use_case.add_dependency(request)
        
        print(f"Dependency addition result:")
        print(f"  Success: {result.success}")
        print(f"  Message: {result.message}")
        print(f"  Dependencies: {result.dependencies}")
        
        if result.success:
            print("✅ SUCCESS: Can now add completed tasks as dependencies!")
            
            # Test dependency retrieval
            deps = dependency_use_case.get_dependencies(task2_id)
            print(f"Dependency details:")
            for dep in deps.get('dependencies', []):
                print(f"  - {dep['id']}: {dep['title']} (status: {dep['status']})")
        else:
            print(f"❌ FAILED: {result.message}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Cleanup - delete test tasks
    print("\nCleaning up test tasks...")
    try:
        task_repo.delete(TaskId(task1_id))
        task_repo.delete(TaskId(task2_id))
        print("Test tasks cleaned up")
    except Exception as e:
        print(f"Cleanup error (ignore): {e}")

if __name__ == "__main__":
    test_dependency_management_fix()