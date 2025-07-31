#!/usr/bin/env python3
"""
Manual test for completion_summary context storage functionality

This test validates that completion_summary is properly stored in the context system
using the actual working PostgreSQL database configuration.
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

# Import after setting environment
from dhafnck_mcp_main.src.fastmcp.task_management.infrastructure.database.database_config import get_db_config
from dhafnck_mcp_main.src.fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from dhafnck_mcp_main.src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from sqlalchemy import text
import uuid
import json

def test_completion_summary_storage():
    """Test that completion_summary is stored properly in context"""
    print("🧪 Testing completion_summary context storage...")
    
    try:
        # 1. Verify database connection
        db = get_db_config()
        print("✅ Database connected successfully")
        
        # 2. Create a test task facade
        from dhafnck_mcp_main.src.fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
        task_repository = TaskRepositoryFactory.create()
        facade = TaskApplicationFacade(task_repository)
        
        # Create or get a project and branch for testing
        # Simplify by directly inserting test data
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        with db.get_session() as session:
            # Insert test project
            session.execute(text("""
                INSERT INTO projects (id, name, description, status, created_at, updated_at)
                VALUES (:id, :name, :description, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": project_id,
                "name": "Test Project for Context Storage",
                "description": "Project for testing completion summary context storage"
            })
            
            # Insert test branch
            session.execute(text("""
                INSERT INTO project_git_branchs (id, project_id, name, description, created_at, updated_at)
                VALUES (:id, :project_id, :name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": branch_id,
                "project_id": project_id,
                "name": "test-completion-summary",
                "description": "Branch for testing completion summary context storage"
            })
            
            session.commit()
            print(f"✅ Created test project: {project_id}")
            print(f"✅ Created test branch: {branch_id}")
        
        # 3. Create a test task
        task_id = str(uuid.uuid4())
        
        # Create task using the facade with proper request object
        from dhafnck_mcp_main.src.fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
        
        request = CreateTaskRequest(
            title="Test completion summary storage",
            description="Testing that completion_summary is stored in context",
            priority="medium",
            git_branch_id=branch_id
        )
        
        created_task = facade.create_task(request)
        print(f"📋 Task creation response: {created_task}")
        
        # Check different possible key names
        actual_task_id = None
        if 'task_id' in created_task:
            actual_task_id = created_task['task_id']
        elif 'id' in created_task:
            actual_task_id = created_task['id']
        elif 'task' in created_task and 'id' in created_task['task']:
            actual_task_id = created_task['task']['id']
        else:
            print(f"❌ Could not find task ID in response keys: {list(created_task.keys())}")
            return False
            
        print(f"✅ Created task: {actual_task_id}")
        
        # 4. Complete the task with completion_summary and testing_notes
        completion_summary = "Task completed successfully with proper context storage validation"
        testing_notes = "Verified that completion_summary field stores data correctly in context system"
        
        completed_task = facade.complete_task(
            task_id=actual_task_id,
            completion_summary=completion_summary,
            testing_notes=testing_notes
        )
        
        print(f"✅ Completed task with summary: {completion_summary[:50]}...")
        
        # 5. Verify context was created and contains the completion_summary
        if 'context' in completed_task and completed_task['context']:
            context_data = completed_task['context']
            print(f"✅ Context found: {type(context_data)}")
            
            # Check if context is a string (JSON) or dict
            if isinstance(context_data, str):
                try:
                    context_dict = json.loads(context_data)
                except json.JSONDecodeError:
                    print(f"❌ Context is not valid JSON: {context_data[:100]}...")
                    return False
            else:
                context_dict = context_data
            
            # Check for completion_summary in context
            progress = context_dict.get('progress', {})
            if isinstance(progress, dict):
                current_session = progress.get('current_session_summary')
                if current_session == completion_summary:
                    print(f"✅ completion_summary found in context.progress.current_session_summary")
                    print(f"   Stored value: {current_session}")
                else:
                    print(f"❌ completion_summary not found in expected location")
                    print(f"   Context structure: {json.dumps(context_dict, indent=2)[:500]}...")
                    return False
            else:
                print(f"❌ Context.progress is not a dict: {progress}")
                return False
            
            # Check for testing_notes in context  
            next_steps = progress.get('next_steps', [])
            if isinstance(next_steps, list) and testing_notes in next_steps:
                print(f"✅ testing_notes found in context.progress.next_steps")
                print(f"   Stored value: {testing_notes}")
            else:
                print(f"⚠️  testing_notes not found in expected location")
                print(f"   next_steps: {next_steps}")
        else:
            print(f"❌ No context found in completed task")
            print(f"   Task response keys: {list(completed_task.keys())}")
            return False
        
        print("✅ All completion_summary context storage tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Manual Completion Summary Context Storage Test")
    print("=" * 60)
    
    success = test_completion_summary_storage()
    
    if success:
        print("\n🎉 SUCCESS: completion_summary context storage is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: completion_summary context storage needs fixing")
        sys.exit(1)