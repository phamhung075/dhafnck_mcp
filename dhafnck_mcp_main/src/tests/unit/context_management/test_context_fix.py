#!/usr/bin/env python3
"""Test script to verify context synchronization fix"""

import sqlite3
import uuid
from datetime import datetime

# Database path
DB_PATH = "/data/dhafnck_mcp.db"

def create_test_data():
    """Create test project and git branch directly in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create a test project if not exists
    test_project_id = "test-project-" + str(uuid.uuid4())
    test_branch_id = "test-branch-" + str(uuid.uuid4())
    
    try:
        # Insert project
        cursor.execute("""
            INSERT INTO projects (id, name, description, created_at, updated_at, user_id, status, model_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_project_id,
            "Test Project for Context Fix",
            "Testing context synchronization fix",
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            "default_id",
            "active",
            "{}"
        ))
        
        # Insert project context
        cursor.execute("""
            INSERT INTO project_contexts (
                project_id, parent_global_id, team_preferences, technology_stack,
                project_workflow, local_standards, global_overrides, delegation_rules,
                inheritance_disabled, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_project_id,
            "global_singleton",
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            1
        ))
        
        # Insert git branch
        cursor.execute("""
            INSERT INTO project_git_branchs (
                id, project_id, name, description, created_at, updated_at,
                assigned_agent_id, priority, status, model_metadata,
                task_count, completed_task_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_branch_id,
            test_project_id,
            "test/context-fix",
            "Branch for testing context fix",
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            None,
            "medium",
            "todo",
            "{}",
            0,
            0
        ))
        
        conn.commit()
        print(f"✅ Created test data:")
        print(f"   Project ID: {test_project_id}")
        print(f"   Branch ID: {test_branch_id}")
        print()
        print("Now you can test task creation with:")
        print(f'mcp__dhafnck_mcp_http__manage_task(action="create", git_branch_id="{test_branch_id}", title="Test Task", description="Test")')
        
        return test_project_id, test_branch_id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        conn.rollback()
        return None, None
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_data()