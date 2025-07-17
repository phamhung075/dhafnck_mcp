#!/usr/bin/env python3
"""
Test PostgreSQL Connection and ORM Setup

This script tests the PostgreSQL connection and verifies that the ORM is working correctly.
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.database.init_database import init_database
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Test database connection and basic operations"""
    try:
        # Get database configuration
        db_config = get_db_config()
        db_info = db_config.get_database_info()
        
        print("\n=== Database Configuration ===")
        print(f"Type: {db_info['type']}")
        print(f"URL: {db_info['url'] if db_info['type'] == 'postgresql' else 'SQLite'}")
        print(f"Engine: {db_info['engine']}")
        
        # Initialize database (create tables)
        print("\n=== Initializing Database ===")
        init_database()
        print("✓ Database tables created successfully")
        
        # Test ORM repository
        print("\n=== Testing ORM Repository ===")
        repo = ORMTaskRepository(
            git_branch_id="test-branch",
            project_id="test-project",
            git_branch_name="main",
            user_id="test-user"
        )
        
        # Create a test task
        task = repo.create_task(
            title="Test Task",
            description="This is a test task to verify PostgreSQL connection",
            priority="high",
            assignee_ids=["user1", "user2"]
        )
        print(f"✓ Created task: {task.id} - {task.title}")
        
        # List tasks
        tasks = repo.list_tasks()
        print(f"✓ Found {len(tasks)} tasks in the database")
        
        # Clean up - delete the test task
        repo.delete_task(task.id)
        print("✓ Cleaned up test task")
        
        print("\n=== Test Completed Successfully ===")
        print(f"Database is working correctly with {db_info['type'].upper()}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()