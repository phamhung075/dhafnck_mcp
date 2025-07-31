#!/usr/bin/env python3
"""
Simple test for completion_summary context storage functionality
Bypasses complex relationships to focus on core functionality
"""

import os
import sys
from pathlib import Path

# Set up environment for PostgreSQL
os.environ['DATABASE_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = 'postgresql://dhafnck_user:dhafnck_password@localhost:5432/dhafnck_mcp'

# Add the project to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dhafnck_mcp_main.src.fastmcp.task_management.infrastructure.database.database_config import get_db_config
from dhafnck_mcp_main.src.fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from dhafnck_mcp_main.src.fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from sqlalchemy import text
import uuid
import json

def test_completion_summary_simple():
    """Test completion_summary storage using direct database approach"""
    print("🧪 Testing completion_summary with simple approach...")
    
    try:
        # 1. Verify database connection
        db = get_db_config()
        print("✅ Database connected successfully")
        
        # 2. Create test data directly in database
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        with db.get_session() as session:
            # Insert test project
            session.execute(text("""
                INSERT INTO projects (id, name, description, status, created_at, updated_at, user_id)
                VALUES (:id, :name, :description, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'test_user')
            """), {
                "id": project_id,
                "name": "Test Project Simple",
                "description": "Simple test project"
            })
            
            # Insert test branch
            session.execute(text("""
                INSERT INTO project_git_branchs (id, project_id, name, description, created_at, updated_at)
                VALUES (:id, :project_id, :name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                "id": branch_id,
                "project_id": project_id,
                "name": "test-simple",
                "description": "Simple test branch"
            })
            
            # Insert test task directly (avoiding ORM relationships)
            session.execute(text("""
                INSERT INTO tasks (id, title, description, git_branch_id, status, priority, created_at, updated_at)
                VALUES (:id, :title, :description, :git_branch_id, 'todo', 'medium', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                "id": task_id,
                "title": "Simple Test Task",
                "description": "Testing completion summary storage",
                "git_branch_id": branch_id
            })
            
            session.commit()
            print(f"✅ Created test data: project={project_id}, branch={branch_id}, task={task_id}")
        
        # 3. Test completion using the use case directly
        task_repository = TaskRepositoryFactory.create()
        complete_use_case = CompleteTaskUseCase(task_repository)
        
        completion_summary = "Task completed successfully with simple direct testing approach"
        testing_notes = "Verified completion_summary storage works through direct database operations"
        
        # Complete the task
        result = complete_use_case.execute(
            task_id=task_id,
            completion_summary=completion_summary,
            testing_notes=testing_notes
        )
        
        print(f"✅ Task completion result: {result}")
        
        # 4. Verify the task status and context were updated
        with db.get_session() as session:
            # Check task status
            task_result = session.execute(text("""
                SELECT id, status, context_id 
                FROM tasks 
                WHERE id = :task_id
            """), {"task_id": task_id})
            
            task_row = task_result.fetchone()
            if task_row:
                print(f"✅ Task status: {task_row[1]}")
                print(f"✅ Task context_id: {task_row[2]}")
                
                # Check if context was created (task_contexts table)
                if task_row[2]:  # If context_id is set
                    context_result = session.execute(text("""
                        SELECT task_id, task_data
                        FROM task_contexts
                        WHERE task_id = :task_id
                    """), {"task_id": task_id})
                    
                    context_row = context_result.fetchone()
                    if context_row:
                        print(f"✅ Context found in task_contexts table")
                        context_data = context_row[1]  # task_data JSON field
                        
                        if isinstance(context_data, dict):
                            progress = context_data.get('progress', {})
                            if isinstance(progress, dict):
                                current_session = progress.get('current_session_summary')
                                if current_session == completion_summary:
                                    print(f"✅ completion_summary correctly stored: {current_session}")
                                    
                                    # Check testing notes
                                    next_steps = progress.get('next_steps', [])
                                    if isinstance(next_steps, list) and testing_notes in next_steps:
                                        print(f"✅ testing_notes correctly stored: {testing_notes}")
                                        return True
                                    else:
                                        print(f"⚠️  testing_notes not found: {next_steps}")
                                else:
                                    print(f"❌ completion_summary not found. Expected: {completion_summary}, Found: {current_session}")
                            else:
                                print(f"❌ Progress is not a dict: {progress}")
                        else:
                            print(f"❌ Context data is not a dict: {type(context_data)}")
                    else:
                        print("❌ No context found in task_contexts table")
                else:
                    print("❌ No context_id set on task")
            else:
                print("❌ Task not found after completion")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple Completion Summary Test")
    print("=" * 50)
    
    success = test_completion_summary_simple()
    
    if success:
        print("\n🎉 SUCCESS: completion_summary storage is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: completion_summary storage needs investigation")
        sys.exit(1)