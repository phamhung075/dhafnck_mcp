#!/usr/bin/env python3
"""
Test script to verify the dependency management fix works correctly.
"""

import sys
import os
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

# Add the source path to sys.path for imports
sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.application.dtos.dependency.add_dependency_request import AddDependencyRequest
from fastmcp.task_management.application.use_cases.add_dependency import AddDependencyUseCase
from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository

def test_dependency_fix():
    """Test the dependency management fix with real repository"""
    
    print("🧪 Testing Dependency Management Fix")
    print("=" * 60)
    
    # Use test database
    test_db_path = "/tmp/test_dependency_fix.db"
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # Create test repository
        repo = SQLiteTaskRepository(db_path=test_db_path, git_branch_id=None)
        use_case = AddDependencyUseCase(repo)
        
        print("\n1. Creating test project and branch...")
        
        # We need to create the database schema and test data manually
        with sqlite3.connect(test_db_path) as conn:
            # Create basic schema
            conn.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    user_id TEXT,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_task_trees (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    name TEXT,
                    description TEXT,
                    created_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    status TEXT,
                    priority TEXT,
                    git_branch_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (git_branch_id) REFERENCES project_task_trees (id)
                )
            ''')
            
            # Create test project and branch
            project_id = str(uuid4())
            branch_id = str(uuid4())
            
            conn.execute('INSERT INTO projects (id, name, user_id, created_at) VALUES (?, ?, ?, ?)',
                        (project_id, "Test Project", "test_user", datetime.now(timezone.utc).isoformat()))
            
            conn.execute('INSERT INTO project_task_trees (id, project_id, name, description, created_at) VALUES (?, ?, ?, ?, ?)',
                        (branch_id, project_id, "main", "Main branch", datetime.now(timezone.utc).isoformat()))
            
            # Create test tasks
            active_task_id = str(uuid4())
            completed_task_id = str(uuid4())
            
            # Insert active task
            conn.execute('''
                INSERT INTO tasks (id, title, description, status, priority, git_branch_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (active_task_id, "Active Task", "This is an active task", "todo", "medium", 
                  branch_id, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()))
            
            # Insert completed task
            conn.execute('''
                INSERT INTO tasks (id, title, description, status, priority, git_branch_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (completed_task_id, "Completed Task", "This is a completed task", "done", "medium", 
                  branch_id, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()))
            
            conn.commit()
            
            print(f"   ✅ Created project: {project_id}")
            print(f"   ✅ Created branch: {branch_id}")
            print(f"   ✅ Created active task: {active_task_id}")
            print(f"   ✅ Created completed task: {completed_task_id}")
        
        print("\n2. Testing dependency on active task (baseline)...")
        
        # Create repository with proper context
        repo_with_context = SQLiteTaskRepository(db_path=test_db_path, git_branch_id=branch_id)
        use_case_with_context = AddDependencyUseCase(repo_with_context)
        
        # Test adding dependency on active task
        request_active = AddDependencyRequest(
            task_id=active_task_id,
            depends_on_task_id=active_task_id  # Self-dependency for test
        )
        
        try:
            result = use_case_with_context.execute(request_active)
            print(f"   Result: {result.success}")
            print(f"   Message: {result.message}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n3. Testing dependency on completed task (fixed!)...")
        
        # Test adding dependency on completed task
        request_completed = AddDependencyRequest(
            task_id=active_task_id,
            depends_on_task_id=completed_task_id
        )
        
        try:
            result = use_case_with_context.execute(request_completed)
            print(f"   Result: {result.success}")
            print(f"   Message: {result.message}")
            if hasattr(result, 'metadata') and result.metadata:
                print(f"   Metadata: {result.metadata}")
            
            if result.success:
                print("   ✅ DEPENDENCY FIX SUCCESSFUL!")
                print("   ✅ Can now add dependencies on completed tasks!")
            else:
                print(f"   ❌ Fix failed: {result.message}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n4. Verification: Checking task has the dependency...")
        
        # Verify the dependency was added
        task = repo_with_context.find_by_id(TaskId.from_string(active_task_id))
        if task:
            dependencies = task.get_dependency_ids()
            print(f"   Task dependencies: {dependencies}")
            if completed_task_id in dependencies:
                print("   ✅ Dependency correctly added to task!")
            else:
                print("   ❌ Dependency not found in task")
        else:
            print("   ❌ Could not retrieve task")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print(f"\n🧹 Cleaned up test database: {test_db_path}")

if __name__ == "__main__":
    test_dependency_fix()
    
    print("\n" + "="*60)
    print("🎯 Dependency Management Fix Test Complete")
    print("📋 If this test passes, the fix is working correctly!")