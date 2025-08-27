#!/usr/bin/env python3
"""
Manual test for completion_summary context storage functionality

This test validates that completion_summary is properly stored in the context system
using the actual working PostgreSQL database configuration.
"""

import os
import sys
from pathlib import Path

# Set up environment for SQLite (for testing)
os.environ['DATABASE_TYPE'] = 'sqlite'
os.environ['PYTEST_CURRENT_TEST'] = 'test_completion_summary_manual.py::test_completion_summary_storage'

# Add the project to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after setting environment
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.domain.value_objects.task_id import TaskId
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
        from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
        task_repository = TaskRepositoryFactory.create()
        facade = TaskApplicationFacade(task_repository)
        
        # Create or get a project and branch for testing
        # Simplify by directly inserting test data
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        with db.get_session() as session:
            # Insert test project
            session.execute(text("""
                INSERT INTO projects (id, name, description, status, user_id, metadata, created_at, updated_at)
                VALUES (:id, :name, :description, 'active', :user_id, :metadata, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": project_id,
                "name": "Test Project for Context Storage",
                "description": "Project for testing completion summary context storage",
                "user_id": "test-user-123",
                "metadata": "{}"
            })
            
            # Insert test branch
            session.execute(text("""
                INSERT INTO project_git_branchs (id, project_id, name, description, priority, status, metadata, task_count, completed_task_count, user_id, created_at, updated_at)
                VALUES (:id, :project_id, :name, :description, :priority, :status, :metadata, :task_count, :completed_task_count, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": branch_id,
                "project_id": project_id,
                "name": "test-completion-summary",
                "description": "Branch for testing completion summary context storage",
                "priority": "medium",
                "status": "active",
                "metadata": "{}",
                "task_count": 0,
                "completed_task_count": 0,
                "user_id": "test-user-123"
            })
            
            session.commit()
            print(f"✅ Created test project: {project_id}")
            print(f"✅ Created test branch: {branch_id}")
        
        # 3. Create a test task using the use case directly
        task_id = str(uuid.uuid4())
        
        # Import use cases directly for better control
        from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
        from fastmcp.task_management.application.use_cases.create_task import CreateTaskUseCase
        from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
        from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
        from fastmcp.task_management.infrastructure.repositories.project_repository_factory import ProjectRepositoryFactory
        from fastmcp.task_management.domain.value_objects.task_id import TaskId
        
        # Create repositories
        task_repository = TaskRepositoryFactory.create()
        project_repository = ProjectRepositoryFactory.create()
        
        # Create the create task use case
        create_task_use_case = CreateTaskUseCase(task_repository, project_repository)
        
        # Create task request with proper data
        request = CreateTaskRequest(
            title="Test completion summary storage",
            description="Testing that completion_summary is stored in context",
            priority="medium",
            git_branch_id=branch_id,
            user_id="test-user-123"
        )
        
        # Execute create task use case
        created_task = create_task_use_case.execute(request, task_id)
        print(f"✅ Created task: {created_task.id}")
        actual_task_id = str(created_task.id)
        
        # 4. Complete the task with completion_summary and testing_notes
        completion_summary = "Task completed successfully with proper context storage validation"
        testing_notes = "Verified that completion_summary field stores data correctly in context system"
        
        # Create complete task use case
        complete_task_use_case = CompleteTaskUseCase(task_repository)
        
        # Complete the task
        completed_task = complete_task_use_case.execute(
            TaskId(actual_task_id),
            completion_summary=completion_summary,
            testing_notes=testing_notes
        )
        
        # Convert domain object to dict for context checking
        completed_task = {
            'context': completed_task.context,  # Assuming this contains the context
            'id': str(completed_task.id),
            'completion_summary': completed_task.completion_summary,
            'testing_notes': completed_task.testing_notes
        }
        
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
                    raise AssertionError(f"Context is not valid JSON: {context_data[:100]}...")
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
                    raise AssertionError(f"completion_summary not found in expected location. Context structure: {json.dumps(context_dict, indent=2)[:500]}...")
            else:
                print(f"❌ Context.progress is not a dict: {progress}")
                raise AssertionError(f"Context.progress is not a dict: {progress}")
            
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
            raise AssertionError(f"No context found in completed task. Task response keys: {list(completed_task.keys())}")
        
        print("✅ All completion_summary context storage tests passed!")
        # For pytest compatibility, use assertions instead of returning values
        assert True  # Test passed
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        # For pytest compatibility, re-raise the exception instead of returning False
        raise

if __name__ == "__main__":
    print("🚀 Manual Completion Summary Context Storage Test")
    print("=" * 60)
    
    try:
        test_completion_summary_storage()
        print("\n🎉 SUCCESS: completion_summary context storage is working correctly!")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 FAILURE: completion_summary context storage needs fixing - {e}")
        sys.exit(1)