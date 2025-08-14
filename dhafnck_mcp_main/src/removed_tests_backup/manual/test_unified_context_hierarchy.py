#!/usr/bin/env python3
"""
Test unified context system with complete hierarchy.
"""

import os
import sqlite3
from pathlib import Path
import sys

# Set test environment to avoid database conflicts
os.environ["PYTEST_CURRENT_TEST"] = "test_unified_context_hierarchy.py::test_hierarchy"

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


def setup_test_data():
    """Create the required parent records for task context."""
    print("📋 Setting up test data hierarchy...")
    
    # Connect directly to test database
    db_path = Path(__file__).parent.parent.parent.parent / "database" / "data" / "dhafnck_mcp_test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key enforcement
    cursor = conn.cursor()
    
    try:
        # 1. Create global context (if not exists)
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO global_contexts (
                    id, organization_id, autonomous_rules, security_policies, 
                    coding_standards, workflow_templates, delegation_rules, 
                    created_at, updated_at, version
                ) VALUES (
                    'global_singleton', 'test_org', '{}', '{}', 
                    '{}', '{}', '{}', 
                    datetime('now'), datetime('now'), 1
                )
            """)
            print("   ✅ Global context created")
        except Exception as e:
            print(f"   ❌ Global context failed: {e}")
        
        # 2. Create project
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO projects (
                    id, name, description, created_at, updated_at, user_id, status, metadata
                ) VALUES (
                    'test-project-123', 'Test Project', 'Test project for unified context', 
                    datetime('now'), datetime('now'), 'test_user', 'active', '{}'
                )
            """)
            print("   ✅ Project created")
        except Exception as e:
            print(f"   ❌ Project failed: {e}")
        
        # 3. Create project context
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO project_contexts (
                    project_id, parent_global_id, team_preferences, technology_stack,
                    project_workflow, local_standards, global_overrides, delegation_rules,
                    created_at, updated_at, version, inheritance_disabled
                ) VALUES (
                    'test-project-123', 'global_singleton', '{}', '{}',
                    '{}', '{}', '{}', '{}',
                    datetime('now'), datetime('now'), 1, 0
                )
            """)
            print("   ✅ Project context created")
        except Exception as e:
            print(f"   ❌ Project context failed: {e}")
        
        # 4. Create git branch
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO project_git_branchs (
                    id, project_id, name, description, created_at, updated_at
                ) VALUES (
                    'test-branch-456', 'test-project-123', 'feature/test-branch', 
                    'Test branch for unified context', datetime('now'), datetime('now')
                )
            """)
            print("   ✅ Git branch created")
        except Exception as e:
            print(f"   ❌ Git branch failed: {e}")
        
        # 5. Create branch context
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO branch_contexts (
                    branch_id, parent_project_id, parent_project_context_id,
                    branch_workflow, branch_standards, agent_assignments, local_overrides,
                    delegation_rules, inheritance_disabled, force_local_only,
                    created_at, updated_at, version
                ) VALUES (
                    'test-branch-456', 'test-project-123', 'test-project-123',
                    '{}', '{}', '{}', '{}',
                    '{}', 0, 0,
                    datetime('now'), datetime('now'), 1
                )
            """)
            print("   ✅ Branch context created")
        except Exception as e:
            print(f"   ❌ Branch context failed: {e}")
        
        # 6. Create a task (for task context)
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO tasks (
                    id, git_branch_id, title, description, status, priority,
                    estimated_effort, due_date, created_at, updated_at, context_id
                ) VALUES (
                    'test-task-123', 'test-branch-456', 'Test Task', 'Test task for unified context',
                    'todo', 'medium', '2 hours', NULL, 
                    datetime('now'), datetime('now'), NULL
                )
            """)
            print("   ✅ Task created")
        except Exception as e:
            print(f"   ❌ Task failed: {e}")
        
        conn.commit()
        print("✅ Test data hierarchy created successfully!")
        
        # Verify the hierarchy
        cursor.execute("SELECT COUNT(*) FROM global_contexts WHERE id = 'global_singleton'")
        global_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE id = 'test-project-123'")
        project_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM project_contexts WHERE project_id = 'test-project-123'")
        project_context_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM project_git_branchs WHERE id = 'test-branch-456'")
        branch_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM branch_contexts WHERE branch_id = 'test-branch-456'")
        branch_context_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE id = 'test-task-123'")
        task_count = cursor.fetchone()[0]
        
        print(f"📊 Hierarchy verification:")
        print(f"   Global contexts: {global_count}")
        print(f"   Projects: {project_count}")
        print(f"   Project contexts: {project_context_count}")
        print(f"   Git branches: {branch_count}")
        print(f"   Branch contexts: {branch_context_count}")
        print(f"   Tasks: {task_count}")
        
    finally:
        conn.close()


def test_unified_context():
    """Test unified context system with proper hierarchy."""
    print("\n🚀 Testing Unified Context System with Full Hierarchy...")
    
    # Setup test data first
    setup_test_data()
    
    # Create facade
    facade_factory = UnifiedContextFacadeFactory()
    facade = facade_factory.create_facade()
    
    # Test creating a task context (should work now)
    print("\n1. Creating task context...")
    result = facade.create_context(
        level="task",
        context_id="test-task-123",
        data={
            "title": "Test Task",
            "description": "Testing unified context",
            "branch_id": "test-branch-456"
        }
    )
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        print(f"   Created context: {result.get('context', {}).get('id')}")
        print(f"   Task data: {result.get('context', {}).get('task_data')}")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test getting the context
    print("\n2. Getting task context...")
    result = facade.get_context(
        level="task", 
        context_id="test-task-123"
    )
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        print(f"   Context data: {result.get('context', {}).get('task_data')}")
    
    # Test resolving with inheritance
    print("\n3. Resolving context with inheritance...")
    result = facade.resolve_context(
        level="task",
        context_id="test-task-123"
    )
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        resolved = result.get('resolved_context', {})
        print(f"   Resolved context has {len(resolved)} keys")
        print(f"   Keys: {list(resolved.keys())}")
    
    # Test updating context
    print("\n4. Updating context...")
    result = facade.update_context(
        level="task",
        context_id="test-task-123",
        data={"progress": 50, "status": "in_progress"}
    )
    print(f"   Success: {result.get('success')}")
    
    # Test adding an insight
    print("\n5. Adding insight...")
    result = facade.add_insight(
        level="task",
        context_id="test-task-123",
        content="Found optimization opportunity",
        category="performance",
        importance="high"
    )
    print(f"   Success: {result.get('success')}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_unified_context()