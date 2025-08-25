#!/usr/bin/env python3
"""
Debug script for project context creation issue.
"""

import os
import sys
import uuid
from pathlib import Path

# Set up environment for test mode
os.environ['MCP_DB_PATH'] = './test_debug.db'
os.environ['PYTHONPATH'] = 'src'
os.environ['PYTEST_CURRENT_TEST'] = 'test_debug.py::test'  # Force test mode
os.environ['DATABASE_TYPE'] = 'sqlite'  # Force SQLite for testing
sys.path.insert(0, 'src')

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.infrastructure.database.models import Project

def test_project_context_creation():
    """Test project context creation with user isolation."""
    print("\n=== Testing Project Context Creation ===")
    
    # Create factory
    factory = UnifiedContextFacadeFactory()
    
    # Create user and project IDs
    user_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    print(f"User ID: {user_id}")
    print(f"Project ID: {project_id}")
    
    # First initialize and create a project in the database
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from fastmcp.task_management.infrastructure.database.init_database import init_database
    
    # Initialize database first
    init_database()
    
    db_config = get_db_config()
    with db_config.get_session() as session:
        project = Project(
            id=project_id,
            name="Test Project",
            description="Test project for context",
            user_id=user_id
        )
        session.add(project)
        session.commit()
        print(f"Created project in database: {project_id}")
    
    # Create facade for user
    facade = factory.create_facade(
        user_id=user_id,
        project_id=project_id
    )
    
    # Create project context
    context_id = str(uuid.uuid4())
    print(f"Creating project context with ID: {context_id}")
    
    result = facade.create_context(
        level="project",
        context_id=context_id,
        data={
            "project_name": "Test Project",
            "project_settings": {"theme": "dark"},
            "technology_stack": {"framework": "FastAPI"}
        }
    )
    
    print(f"\n=== RESULT ===")
    print(f"Success: {result.get('success')}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
        print(f"Guidance: {result.get('guidance')}")
    else:
        print(f"Context created successfully!")
        print(f"Context data: {result.get('context')}")
    
    return result.get('success')

if __name__ == "__main__":
    success = test_project_context_creation()
    if success:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)