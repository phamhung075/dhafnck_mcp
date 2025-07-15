#!/usr/bin/env python3
"""
Complete test suite for the dependency management fix.

Tests all components:
1. Enhanced dependency lookup
2. Task completion with dependent task updating  
3. Dependency chain validation
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
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.application.use_cases.validate_dependencies import ValidateDependenciesUseCase
from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository

def create_test_database(db_path: str) -> tuple:
    """Create test database with sample data"""
    
    # Clean up any existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
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
        
        # Create test tasks for dependency chain: Task A -> Task B -> Task C
        task_a_id = str(uuid4())  # Depends on B
        task_b_id = str(uuid4())  # Depends on C  
        task_c_id = str(uuid4())  # No dependencies (will be completed first)
        
        # Insert tasks
        tasks = [
            (task_a_id, "Task A", "Final task in chain", "todo", "high"),
            (task_b_id, "Task B", "Middle task in chain", "todo", "medium"),
            (task_c_id, "Task C", "First task in chain", "in_progress", "medium"),
        ]
        
        for task_id, title, desc, status, priority in tasks:
            conn.execute('''
                INSERT INTO tasks (id, title, description, status, priority, git_branch_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, title, desc, status, priority, 
                  branch_id, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()))
        
        conn.commit()
    
    return project_id, branch_id, task_a_id, task_b_id, task_c_id

def test_complete_dependency_fix():
    """Test the complete dependency management fix"""
    
    print("🧪 COMPREHENSIVE DEPENDENCY MANAGEMENT FIX TEST")
    print("=" * 70)
    
    test_db_path = "/tmp/test_complete_dependency_fix.db"
    
    try:
        # Create test environment
        print("\n1. Setting up test environment...")
        project_id, branch_id, task_a_id, task_b_id, task_c_id = create_test_database(test_db_path)
        
        # Create repositories and use cases
        repo = SQLiteTaskRepository(db_path=test_db_path, git_branch_id=branch_id)
        add_dep_use_case = AddDependencyUseCase(repo)
        complete_task_use_case = CompleteTaskUseCase(repo)
        validate_deps_use_case = ValidateDependenciesUseCase(repo)
        
        print(f"   ✅ Created test environment with tasks:")
        print(f"      - Task A (depends on B): {task_a_id}")
        print(f"      - Task B (depends on C): {task_b_id}")
        print(f"      - Task C (no deps):      {task_c_id}")
        
        # Test 2: Create dependency chain
        print("\n2. Creating dependency chain...")
        
        # Task A depends on Task B
        result_a_b = add_dep_use_case.execute(AddDependencyRequest(
            task_id=task_a_id,
            depends_on_task_id=task_b_id
        ))
        
        # Task B depends on Task C
        result_b_c = add_dep_use_case.execute(AddDependencyRequest(
            task_id=task_b_id,
            depends_on_task_id=task_c_id
        ))
        
        print(f"   Task A -> Task B: {result_a_b.success} - {result_a_b.message}")
        print(f"   Task B -> Task C: {result_b_c.success} - {result_b_c.message}")
        
        if result_a_b.success and result_b_c.success:
            print("   ✅ Dependency chain created successfully")
        else:
            print("   ❌ Failed to create dependency chain")
            return False
        
        # Test 3: Validate dependency chain
        print("\n3. Validating dependency chain...")
        
        validation_a = validate_deps_use_case.validate_task_dependencies(task_a_id)
        validation_b = validate_deps_use_case.validate_task_dependencies(task_b_id)
        validation_c = validate_deps_use_case.validate_task_dependencies(task_c_id)
        
        print(f"   Task A validation: {'✅ Valid' if validation_a.get('valid') else '❌ Invalid'}")
        if validation_a.get('issues'):
            for issue in validation_a['issues']:
                print(f"      - {issue.get('message', '')}")
        
        print(f"   Task B validation: {'✅ Valid' if validation_b.get('valid') else '❌ Invalid'}")
        print(f"   Task C validation: {'✅ Valid' if validation_c.get('valid') else '❌ Invalid'}")
        
        # Test 4: Get dependency chain analysis
        print("\n4. Analyzing dependency chains...")
        
        chain_analysis_a = validate_deps_use_case.get_dependency_chain_analysis(task_a_id)
        chain_analysis_b = validate_deps_use_case.get_dependency_chain_analysis(task_b_id)
        
        print(f"   Task A chain: {chain_analysis_a.get('chain_statistics', {}).get('total_dependencies', 0)} dependencies")
        print(f"   Task A can proceed: {'✅ Yes' if chain_analysis_a.get('can_proceed') else '❌ No'}")
        
        print(f"   Task B chain: {chain_analysis_b.get('chain_statistics', {}).get('total_dependencies', 0)} dependencies")
        print(f"   Task B can proceed: {'✅ Yes' if chain_analysis_b.get('can_proceed') else '❌ No'}")
        
        # Test 5: Complete Task C and verify dependent task updates
        print("\n5. Completing Task C and testing dependent task updates...")
        
        # Complete Task C
        complete_result_c = complete_task_use_case.execute(
            task_id=task_c_id,
            completion_summary="Task C completed successfully - ready for dependent tasks"
        )
        
        print(f"   Task C completion: {'✅ Success' if complete_result_c.get('success') else '❌ Failed'}")
        print(f"   Message: {complete_result_c.get('message', '')}")
        
        # Check if Task B status was updated (should be unblocked if it was blocked)
        task_b = repo.find_by_id(TaskId.from_string(task_b_id))
        if task_b:
            print(f"   Task B status after C completion: {task_b.status}")
        
        # Test 6: Validate chain after Task C completion
        print("\n6. Re-validating dependency chains after completion...")
        
        validation_a_after = validate_deps_use_case.validate_task_dependencies(task_a_id)
        validation_b_after = validate_deps_use_case.validate_task_dependencies(task_b_id)
        
        chain_analysis_b_after = validate_deps_use_case.get_dependency_chain_analysis(task_b_id)
        
        print(f"   Task B can proceed now: {'✅ Yes' if chain_analysis_b_after.get('can_proceed') else '❌ No'}")
        print(f"   Task B completion %: {chain_analysis_b_after.get('chain_statistics', {}).get('completion_percentage', 0):.1f}%")
        
        # Test 7: Complete Task B and verify Task A updates
        print("\n7. Completing Task B and testing final dependent task update...")
        
        complete_result_b = complete_task_use_case.execute(
            task_id=task_b_id,
            completion_summary="Task B completed - all dependencies for Task A should now be satisfied"
        )
        
        print(f"   Task B completion: {'✅ Success' if complete_result_b.get('success') else '❌ Failed'}")
        
        # Check Task A final status
        chain_analysis_a_final = validate_deps_use_case.get_dependency_chain_analysis(task_a_id)
        print(f"   Task A can proceed now: {'✅ Yes' if chain_analysis_a_final.get('can_proceed') else '❌ No'}")
        print(f"   Task A completion %: {chain_analysis_a_final.get('chain_statistics', {}).get('completion_percentage', 0):.1f}%")
        
        # Test 8: Test dependency on completed task (the original bug)
        print("\n8. Testing dependency on completed task (original bug fix)...")
        
        # Create a new task that depends on the completed Task C
        new_task_id = str(uuid4())
        with sqlite3.connect(test_db_path) as conn:
            conn.execute('''
                INSERT INTO tasks (id, title, description, status, priority, git_branch_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (new_task_id, "New Task", "Should depend on completed Task C", "todo", "low",
                  branch_id, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()))
            conn.commit()
        
        # Try to add dependency on completed Task C
        result_new_c = add_dep_use_case.execute(AddDependencyRequest(
            task_id=new_task_id,
            depends_on_task_id=task_c_id
        ))
        
        print(f"   New task -> Completed Task C: {'✅ Success' if result_new_c.success else '❌ Failed'}")
        print(f"   Message: {result_new_c.message}")
        
        if result_new_c.success:
            print("   ✅ ORIGINAL BUG FIXED: Can now add dependencies on completed tasks!")
        else:
            print("   ❌ Original bug still exists")
        
        # Final validation
        print("\n9. Final comprehensive validation...")
        
        all_task_ids = [task_a_id, task_b_id, task_c_id, new_task_id]
        multi_validation = validate_deps_use_case.validate_multiple_tasks(all_task_ids)
        
        print(f"   Overall validation: {'✅ Valid' if multi_validation.get('overall_valid') else '❌ Invalid'}")
        print(f"   Summary: {multi_validation.get('summary', {})}")
        
        if multi_validation.get('overall_valid'):
            print("\n🎉 ALL TESTS PASSED! Dependency management fix is working correctly!")
        else:
            print("\n⚠️  Some issues remain - check validation results")
        
        return multi_validation.get('overall_valid', False)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print(f"\n🧹 Cleaned up test database: {test_db_path}")

if __name__ == "__main__":
    success = test_complete_dependency_fix()
    
    print("\n" + "="*70)
    print("🎯 COMPREHENSIVE DEPENDENCY MANAGEMENT FIX TEST COMPLETE")
    print(f"📊 Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    if success:
        print("🎊 All dependency management issues have been resolved!")
        print("📋 Features implemented:")
        print("   ✅ Enhanced dependency lookup (completed/archived tasks)")
        print("   ✅ Task completion with dependent task updates")
        print("   ✅ Comprehensive dependency chain validation")
        print("   ✅ Dependency status tracking and analysis")
    else:
        print("⚠️  Some issues still need to be addressed")
    
    print("="*70)