#!/usr/bin/env python3
"""
Debug script to inspect project contexts in the test database.
"""

import sys
import os
sys.path.append('src')

# Set test mode environment
os.environ['PYTEST_RUNNING'] = '1'

from fastmcp.task_management.infrastructure.database.test_database_config import get_test_database_config
from fastmcp.task_management.infrastructure.database.models import ProjectContext
from sqlalchemy import text

def inspect_project_contexts():
    """Inspect project contexts in the database."""
    db_config = get_test_database_config()
    
    with db_config.get_session() as session:
        # Get all project contexts
        contexts = session.query(ProjectContext).all()
        print(f"Total project contexts: {len(contexts)}")
        
        # Group by user_id
        user_counts = {}
        for context in contexts:
            user_id = context.user_id or "NULL"
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        print("Project contexts by user_id:")
        for user_id, count in user_counts.items():
            print(f"  {user_id}: {count} contexts")
        
        # Show last 5 contexts with details
        print("\nLast 5 project contexts:")
        recent_contexts = session.query(ProjectContext).order_by(ProjectContext.created_at.desc()).limit(5).all()
        for i, context in enumerate(recent_contexts):
            print(f"  {i+1}. ID: {context.id}")
            print(f"     project_id: {context.project_id}")
            print(f"     user_id: {context.user_id}")
            print(f"     created_at: {context.created_at}")
            print(f"     context_data keys: {list(context.context_data.keys()) if context.context_data else 'None'}")

if __name__ == "__main__":
    inspect_project_contexts()