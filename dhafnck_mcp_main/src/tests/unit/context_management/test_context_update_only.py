#!/usr/bin/env python3
"""
Test only the context update functionality for completion_summary
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
from dhafnck_mcp_main.src.fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from sqlalchemy import text
import uuid
import json

def test_context_update_only():
    """Test context update functionality only"""
    print("🧪 Testing context update for completion_summary...")
    
    try:
        # 1. Get existing task context from previous test
        db = get_db_config()
        print("✅ Database connected successfully")
        
        # Find the latest task context
        with db.get_session() as session:
            result = session.execute(text("""
                SELECT tc.task_id, tc.parent_branch_id, t.git_branch_id
                FROM task_contexts tc
                JOIN tasks t ON t.id = tc.task_id
                ORDER BY tc.created_at DESC 
                LIMIT 1
            """))
            
            row = result.fetchone()
            if not row:
                print("❌ No task context found to test")
                return False
                
            task_id = str(row[0])
            parent_branch_id = str(row[1])
            git_branch_id = str(row[2])
            
            print(f"✅ Found task context: task_id={task_id}, git_branch_id={git_branch_id}")
        
        # 2. Create unified facade
        unified_facade = UnifiedContextFacadeFactory().create_facade(
            git_branch_id=git_branch_id
        )
        print("✅ Created unified facade")
        
        # 3. Get current context
        context_result = unified_facade.get_context("task", task_id)
        print(f"📋 Current context result: {context_result}")
        
        if not context_result.get("success"):
            print(f"❌ Failed to get context: {context_result}")
            return False
        
        # 4. Update context with completion summary
        completion_summary = "Test completion summary stored through direct context update"
        testing_notes = "Verified completion summary context update works"
        
        context_update = {
            "progress": {
                "current_session_summary": completion_summary,
                "completion_percentage": 100.0,
                "next_steps": [f"Testing completed: {testing_notes}"],
                "completed_actions": ["Context update test"]
            },
            "metadata": {
                "status": "done"
            }
        }
        
        print(f"📤 Updating context with: {json.dumps(context_update, indent=2)}")
        
        # Update task context with completion summary
        update_result = unified_facade.update_context(
            level="task",
            context_id=task_id,
            data=context_update,
            propagate_changes=True
        )
        
        print(f"📋 Update result: {update_result}")
        
        if not update_result.get("success"):
            print(f"❌ Failed to update context: {update_result}")
            return False
        
        # 5. Verify the update worked
        context_result_after = unified_facade.get_context("task", task_id)
        print(f"📋 Context after update: {context_result_after}")
        
        if context_result_after.get("success") and "context" in context_result_after:
            context = context_result_after["context"]
            
            # Check for completion_summary in progress section
            progress = context.get('progress', {})
            if isinstance(progress, dict):
                current_session = progress.get('current_session_summary')
                if current_session == completion_summary:
                    print(f"✅ completion_summary correctly stored: {current_session}")
                    
                    # Check testing notes
                    next_steps = progress.get('next_steps', [])
                    expected_testing_note = f"Testing completed: {testing_notes}"
                    if isinstance(next_steps, list) and expected_testing_note in next_steps:
                        print(f"✅ testing_notes correctly stored: {expected_testing_note}")
                        
                        # Double-check in database
                        with db.get_session() as session:
                            result = session.execute(text("""
                                SELECT task_data, local_overrides FROM task_contexts 
                                WHERE task_id = :task_id
                            """), {"task_id": task_id})
                            
                            row = result.fetchone()
                            if row:
                                print(f"📋 Database task_data: {json.dumps(row[0], indent=2)}")
                                print(f"📋 Database local_overrides: {json.dumps(row[1], indent=2)}")
                        
                        return True
                    else:
                        print(f"❌ testing_notes not found in next_steps: {next_steps}")
                else:
                    print(f"❌ completion_summary not found. Expected: {completion_summary}, Found: {current_session}")
            else:
                print(f"❌ Progress is not a dict: {progress}")
        else:
            print(f"❌ Failed to get updated context: {context_result_after}")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Context Update Test for Completion Summary")
    print("=" * 60)
    
    success = test_context_update_only()
    
    if success:
        print("\n🎉 SUCCESS: Context update for completion_summary is working!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Context update needs investigation")
        sys.exit(1)