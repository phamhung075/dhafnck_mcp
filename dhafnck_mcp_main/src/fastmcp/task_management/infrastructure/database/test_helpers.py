"""Test helpers for database operations

This module provides utilities for setting up and tearing down test databases.
"""

import os
import tempfile
from typing import Optional
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from fastmcp.task_management.infrastructure.database.database_adapter import DatabaseAdapter


class TestDatabaseAdapter:
    """Adapter for test database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()


def setup_test_database(db_name: Optional[str] = None) -> TestDatabaseAdapter:
    """Setup a test database for integration tests
    
    Args:
        db_name: Optional database name. If not provided, a temporary one is created.
        
    Returns:
        TestDatabaseAdapter: Adapter for interacting with the test database
    """
    # Set test environment variables
    os.environ["USE_TEST_DB"] = "true"
    os.environ["DATABASE_PROVIDER"] = "sqlite"
    
    # Create temporary database if no name provided
    if db_name is None:
        temp_dir = tempfile.mkdtemp(prefix="dhafnck_test_")
        db_path = os.path.join(temp_dir, "test.db")
    else:
        db_path = db_name
    
    # Set the test database path
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    # Create the database adapter
    adapter = DatabaseAdapter()
    
    # Initialize the database schema
    from fastmcp.task_management.infrastructure.database.models import Base
    Base.metadata.create_all(bind=adapter.engine)
    
    # Return a test adapter
    return TestDatabaseAdapter(db_path)


def cleanup_test_database(adapter: TestDatabaseAdapter):
    """Cleanup test database after tests
    
    Args:
        adapter: The test database adapter to cleanup
    """
    # Close any open sessions
    adapter.engine.dispose()
    
    # Remove the database file if it exists
    if os.path.exists(adapter.db_path):
        os.remove(adapter.db_path)
    
    # Remove temp directory if it was created
    parent_dir = os.path.dirname(adapter.db_path)
    if parent_dir.startswith(tempfile.gettempdir()) and "dhafnck_test_" in parent_dir:
        try:
            os.rmdir(parent_dir)
        except OSError:
            pass  # Directory not empty or other error
    
    # Clear test environment variables
    if "USE_TEST_DB" in os.environ:
        del os.environ["USE_TEST_DB"]
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]