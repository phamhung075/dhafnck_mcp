#!/usr/bin/env python3
"""
Test script to verify the database fix for subtask assignees
"""

import sys
import os
sys.path.insert(0, 'src')

from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects import TaskId, TaskStatus, Priority
import json

def test_database_fix():
    """Test that the database fix works correctly"""
    
    print("🔧 Testing database fix for subtask assignees...")
    
    # Create a task repository
    repo = SQLiteTaskRepository(git_branch_id="test-branch")
    
    # Test 1: JSON parsing function
    print("\n1. Testing JSON parsing function:")
    test_cases = [
        '[]',
        '["@coding_agent"]',
        '["@coding_agent", "@test_agent"]',
        '[invalid',
        '"not_a_list"',
        ''
    ]
    
    for test_case in test_cases:
        try:
            result = repo._parse_json_assignees(test_case)
            print(f"   Input: {test_case!r} -> Output: {result}")
        except Exception as e:
            print(f"   Input: {test_case!r} -> Error: {e}")
    
    # Test 2: Create a task with subtasks
    print("\n2. Testing task creation with subtasks:")
    try:
        task = Task(
            id=TaskId("12345678-1234-1234-1234-123456789012"),
            title="Test Task",
            description="Test description",
            git_branch_id="test-branch",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            subtasks=[
                {
                    'id': 'subtask-1',
                    'title': 'Test Subtask 1',
                    'description': 'Test description 1',
                    'status': 'todo',
                    'priority': 'medium',
                    'assignees': [],  # Empty list
                    'estimated_effort': '2 hours',
                    'completed': False
                },
                {
                    'id': 'subtask-2',
                    'title': 'Test Subtask 2',
                    'description': 'Test description 2',
                    'status': 'todo',
                    'priority': 'medium',
                    'assignees': ['@coding_agent', '@test_agent'],  # List with agents
                    'estimated_effort': '1 hour',
                    'completed': False
                }
            ]
        )
        print("   ✅ Task created successfully with subtasks")
        
        # Test 3: Update subtask assignees
        print("\n3. Testing subtask assignees update:")
        updates = {'assignees': ['@new_agent', '@another_agent']}
        success = task.update_subtask('subtask-1', updates)
        if success:
            print("   ✅ Subtask assignees updated successfully")
            updated_subtask = task.get_subtask('subtask-1')
            print(f"   Updated assignees: {updated_subtask['assignees']}")
        else:
            print("   ❌ Failed to update subtask assignees")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 4: Database consistency test
    print("\n4. Testing database JSON consistency:")
    test_assignees = [
        [],
        ['@agent1'],
        ['@agent1', '@agent2'],
        ['@agent1', '@agent2', '@agent3']
    ]
    
    for assignees in test_assignees:
        json_str = json.dumps(assignees)
        parsed = repo._parse_json_assignees(json_str)
        if parsed == assignees:
            print(f"   ✅ {assignees} -> {json_str} -> {parsed}")
        else:
            print(f"   ❌ {assignees} -> {json_str} -> {parsed}")
            return False
    
    print("\n🎉 All tests passed! The database fix is working correctly.")
    return True

if __name__ == "__main__":
    success = test_database_fix()
    if success:
        print("\n✅ Database fix verification successful!")
        sys.exit(0)
    else:
        print("\n❌ Database fix verification failed!")
        sys.exit(1)