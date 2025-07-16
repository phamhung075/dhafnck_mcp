#!/usr/bin/env python3
"""
Test script to reproduce the subtask assignment issue
"""

import sys
import os
import requests
import json
sys.path.insert(0, 'src')

from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects import TaskId, TaskStatus, Priority

def test_mcp_server_subtask_assignment():
    """Test subtask assignment via MCP server"""
    print("🔍 Testing MCP server subtask assignment...")
    
    # MCP server endpoint
    url = "http://localhost:8000/mcp/"
    
    # First, let's list tasks to find one with subtasks
    payload = {
        "method": "call_tool",
        "params": {
            "name": "mcp__dhafnck_mcp_http__manage_task",
            "arguments": {
                "action": "list",
                "limit": 10
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Task list request successful")
            
            # Find a task with subtasks
            tasks = result.get('content', [])
            task_with_subtasks = None
            
            for task in tasks:
                if task.get('subtasks') and len(task['subtasks']) > 0:
                    task_with_subtasks = task
                    break
            
            if task_with_subtasks:
                print(f"✅ Found task with subtasks: {task_with_subtasks['id']}")
                
                # Test subtask assignment
                subtask = task_with_subtasks['subtasks'][0]
                print(f"Testing subtask assignment for: {subtask['id']}")
                
                # Try to assign an agent to the subtask
                payload = {
                    "method": "call_tool",
                    "params": {
                        "name": "mcp__dhafnck_mcp_http__manage_subtask",
                        "arguments": {
                            "action": "update",
                            "task_id": task_with_subtasks['id'],
                            "subtask_id": subtask['id'],
                            "assignees": ["@test_agent"]
                        }
                    }
                }
                
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Subtask assignment successful")
                    print(f"Result: {json.dumps(result, indent=2)}")
                else:
                    print(f"❌ Subtask assignment failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    
            else:
                print("❌ No tasks with subtasks found")
                
        else:
            print(f"❌ Task list request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ MCP server test error: {e}")
        return False
    
    return True

def test_direct_repository_access():
    """Test direct repository access for subtask assignment"""
    print("\n🔍 Testing direct repository access...")
    
    try:
        # Create repository instance
        repo = SQLiteTaskRepository(git_branch_id="test-branch")
        
        # Try to find a task with subtasks
        print("Getting tasks from repository...")
        # This would need to be implemented based on the actual repository interface
        
        return True
        
    except Exception as e:
        print(f"❌ Direct repository test error: {e}")
        return False

def test_concurrent_database_access():
    """Test concurrent database access that might cause locks"""
    print("\n🔍 Testing concurrent database access...")
    
    import threading
    import time
    import sqlite3
    
    db_path = "/home/daihungpham/agentic-project/dhafnck_mcp_main/database/data/dhafnck_mcp.db"
    errors = []
    
    def worker(worker_id):
        """Worker function to simulate concurrent access"""
        try:
            conn = sqlite3.connect(db_path, timeout=1.0)
            cursor = conn.cursor()
            
            # Simulate some work
            cursor.execute("SELECT COUNT(*) FROM task_subtasks;")
            count = cursor.fetchone()[0]
            
            # Simulate update
            cursor.execute("UPDATE task_subtasks SET assignees = assignees WHERE id IN (SELECT id FROM task_subtasks LIMIT 1);")
            conn.commit()
            
            conn.close()
            print(f"   Worker {worker_id}: ✅ Success")
            
        except Exception as e:
            error_msg = f"Worker {worker_id}: ❌ Error: {e}"
            errors.append(error_msg)
            print(f"   {error_msg}")
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    if errors:
        print(f"❌ {len(errors)} concurrent access errors detected")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("✅ All concurrent access tests passed")
        return True

def main():
    """Main test function"""
    print("🔧 Subtask Assignment Debug Test")
    print("=" * 50)
    
    # Test 1: MCP server subtask assignment
    mcp_result = test_mcp_server_subtask_assignment()
    
    # Test 2: Direct repository access
    repo_result = test_direct_repository_access()
    
    # Test 3: Concurrent database access
    concurrent_result = test_concurrent_database_access()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    print(f"MCP Server Test: {'✅ PASS' if mcp_result else '❌ FAIL'}")
    print(f"Repository Test: {'✅ PASS' if repo_result else '❌ FAIL'}")
    print(f"Concurrent Test: {'✅ PASS' if concurrent_result else '❌ FAIL'}")
    
    if all([mcp_result, repo_result, concurrent_result]):
        print("\n🎉 All tests passed - no lock issues detected")
    else:
        print("\n⚠️  Some tests failed - investigate specific failures")

if __name__ == "__main__":
    main()