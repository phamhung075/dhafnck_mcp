#!/usr/bin/env python3
"""Manual test to verify context auto-loading fix works"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dhafnck_mcp_main/src'))

# Use production database
os.environ['MCP_DB_PATH'] = os.path.join(os.path.dirname(__file__), 'dhafnck_mcp_main/database/data/dhafnck_mcp.db')

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory as ContextFacadeFactory
from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory

def main():
    print("=== Testing Context Auto-Loading Fix ===")
    
    # Initialize controllers
    task_repo_factory = TaskRepositoryFactory()
    subtask_repo_factory = SubtaskRepositoryFactory()
    
    task_facade_factory = TaskFacadeFactory(
        repository_factory=task_repo_factory,
        subtask_repository_factory=subtask_repo_factory
    )
    context_facade_factory = ContextFacadeFactory()
    
    task_controller = TaskMCPController(
        task_facade_factory=task_facade_factory,
        context_facade_factory=context_facade_factory
    )
    
    # List existing tasks
    print("\n1. Listing existing tasks...")
    list_result = task_controller.manage_task(
        action="list",
        limit=5
    )
    
    if list_result["success"] and list_result.get("tasks"):
        print(f"Found {len(list_result['tasks'])} tasks")
        
        # Get the first task with context auto-loading
        task_id = list_result["tasks"][0]["id"]
        print(f"\n2. Getting task {task_id} (should auto-load context)...")
        
        get_result = task_controller.manage_task(
            action="get",
            task_id=task_id
        )
        
        if get_result["success"]:
            task = get_result["task"]
            print(f"✅ Task retrieved successfully")
            print(f"   Title: {task.get('title')}")
            print(f"   Context available: {task.get('context_available')}")
            print(f"   Context data present: {task.get('context_data') is not None}")
            
            if task.get('context_data'):
                print(f"   Context sections: {list(task['context_data'].keys())}")
                print("\n✅ Context auto-loading is working!")
            else:
                print("\n❌ Context data is not loaded")
        else:
            print(f"❌ Failed to get task: {get_result.get('error')}")
    else:
        print("No tasks found in database")
        
        # Try the next action
        print("\n3. Trying next action...")
        next_result = task_controller.manage_task(
            action="next",
            git_branch_id=None  # Get from any branch
        )
        
        if next_result["success"] and next_result.get("task"):
            task = next_result["task"]
            print(f"✅ Next task found")
            print(f"   Title: {task.get('title')}")
            print(f"   Context available: {task.get('context_available')}")
            print(f"   Context data present: {task.get('context_data') is not None}")
            
            if task.get('context_data'):
                print(f"   Context sections: {list(task['context_data'].keys())}")
                print("\n✅ Context auto-loading is working for next action!")
            else:
                print("\n❌ Context data is not loaded for next action")
        else:
            print("No next task found")

if __name__ == "__main__":
    main()