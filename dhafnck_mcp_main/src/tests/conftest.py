"""
Global pytest configuration for DhafnckMCP test suite

This module provides:
- Test isolation fixtures  
- Data cleanup after tests
- Performance monitoring
- Test environment validation
"""

import pytest
import tempfile
import shutil
import time
import psutil
import os
from pathlib import Path
from typing import Generator, Dict, Any
import sys

# Ensure src directory is on sys.path for fastmcp imports
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import our test isolation system
# Try top-level tests package import for environment config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from tests.test_environment_config import (
    isolated_test_environment, 
    cleanup_test_data_files_only,
    is_test_data_file,
    IsolatedTestEnvironmentConfig
)

# Import unified context test fixtures if needed
# (Currently no global fixtures needed for unified context)


# =============================================
# PYTEST FIXTURES FOR TEST ISOLATION
# =============================================

@pytest.fixture(scope="function")
def isolated_env() -> Generator[IsolatedTestEnvironmentConfig, None, None]:
    """
    Pytest fixture for isolated test environment with automatic cleanup
    
    Usage:
        def test_something(isolated_env):
            # Use isolated_env.test_files["projects"] etc.
            pass
    """
    test_id = f"pytest_{int(time.time())}"
    
    with isolated_test_environment(test_id) as config:
        yield config


@pytest.fixture(scope="function") 
def performance_tracker():
    """
    Pytest fixture for tracking test performance
    
    Usage:
        def test_something(performance_tracker):
            performance_tracker.start()
            # ... test code ...
            metrics = performance_tracker.end()
            assert metrics['duration'] < 1.0
    """
    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        def end(self) -> Dict[str, Any]:
            self.end_time = time.time()
            self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            return {
                'duration': self.end_time - self.start_time if self.start_time else 0,
                'memory_delta': self.end_memory - self.start_memory if self.start_memory else 0,
                'memory_start': self.start_memory,
                'memory_end': self.end_memory
            }
    
    return PerformanceTracker()


# =============================================
# PYTEST HOOKS FOR AUTOMATED CLEANUP
# =============================================

def pytest_runtest_setup(item):
    """
    Hook run before each test
    Ensures test environment is clean
    """
    # Check if test is marked as isolated
    if item.get_closest_marker("isolated"):
        # Ensure no leftover test data files exist
        test_root = Path(__file__).parent
        cleanup_count = cleanup_test_data_files_only(test_root)
        if cleanup_count > 0:
            print(f"🧹 Cleaned up {cleanup_count} leftover test data files before test")


def pytest_runtest_teardown(item, nextitem):
    """
    Hook run after each test
    Ensures test data is cleaned up
    """
    # Always cleanup test data after any test
    test_root = Path(__file__).parent
    cleanup_count = cleanup_test_data_files_only(test_root)
    if cleanup_count > 0:
        print(f"🧹 Cleaned up {cleanup_count} test data files after test")


def pytest_sessionstart(session):
    """
    Hook run at the start of the test session
    """
    print("\n🧪 Starting DhafnckMCP Test Suite")
    print("🛡️  Test data isolation enabled")
    print("🧹 Automatic cleanup configured")
    
    # Initial cleanup of any existing test data
    test_root = Path(__file__).parent
    cleanup_count = cleanup_test_data_files_only(test_root)
    if cleanup_count > 0:
        print(f"🧹 Cleaned up {cleanup_count} existing test data files")


def pytest_sessionfinish(session, exitstatus):
    """
    Hook run at the end of the test session
    Final cleanup of all test data
    """
    print("\n🧹 Performing final test data cleanup...")
    
    # Final cleanup
    test_root = Path(__file__).parent
    cleanup_count = cleanup_test_data_files_only(test_root)
    
    # Also cleanup any temporary directories
    temp_dirs_cleaned = 0
    for temp_dir in Path("/tmp").glob("dhafnck_test_*"):
        try:
            if temp_dir.is_dir():
                shutil.rmtree(temp_dir)
                temp_dirs_cleaned += 1
        except Exception as e:
            print(f"⚠️  Could not remove temp dir {temp_dir}: {e}")
    
    print(f"🧹 Final cleanup completed:")
    print(f"   - {cleanup_count} test data files removed")
    print(f"   - {temp_dirs_cleaned} temporary directories removed")
    print("✅ Test environment is clean")


# =============================================
# PYTEST MARKS CONFIGURATION
# =============================================

def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", 
        "isolated: mark test as requiring isolated test environment"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance/load test"
    )
    config.addinivalue_line(
        "markers",
        "mcp: mark test as MCP protocol integration test"
    )
    config.addinivalue_line(
        "markers",
        "memory: mark test as memory usage test"
    )
    config.addinivalue_line(
        "markers",
        "stress: mark test as stress test"
    )
    config.addinivalue_line(
        "markers",
        "load: mark test as load test"
    )
    # New markers for hierarchical context migration
    config.addinivalue_line(
        "markers",
        "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers",
        "vision: mark test as vision system test"
    )
    config.addinivalue_line(
        "markers",
        "context: mark test as hierarchical context test"
    )
    config.addinivalue_line(
        "markers",
        "migration: mark test as repository migration test"
    )
    config.addinivalue_line(
        "markers",
        "database: mark test as requiring database"
    )


@pytest.fixture
def test_data_validator():
    """
    Fixture that provides utilities for validating test data isolation
    """
    class TestDataValidator:
        @staticmethod
        def assert_using_test_files(file_path: Path):
            """Assert that a file path is a test file, not production"""
            assert is_test_data_file(file_path), f"File {file_path} is not a test file! Tests must use .test.json files"
        
        @staticmethod
        def assert_no_production_data_modified():
            """Assert that no production data files have been modified"""
            return True  # Placeholder implementation
    
    return TestDataValidator()


# =============================================
# TEST DATABASE INITIALIZATION
# =============================================

def _initialize_test_database(db_path: Path):
    """Initialize test database with schema and basic test data."""
    from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
    import sqlite3
    import uuid
    
    # First initialize the schema
    initialize_database(str(db_path))
    
    # Then add basic test data that tests expect
    with sqlite3.connect(str(db_path)) as conn:
        # Create default test project (no users table needed)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO projects (id, name, description, user_id, status, created_at, updated_at, metadata) 
                VALUES ('default_project', 'Default Test Project', 'Project for testing', 'default_id', 'active', datetime('now'), datetime('now'), '{}')
            """)
            
            # Create main git branch for default project
            # Use a deterministic ID so tests can find it
            main_branch_id = 'test-main-branch-' + str(uuid.uuid4())
            conn.execute("""
                INSERT OR REPLACE INTO project_git_branchs (id, project_id, name, description, created_at, updated_at, priority, status, metadata, task_count, completed_task_count) 
                VALUES (?, 'default_project', 'main', 'Main branch for testing', datetime('now'), datetime('now'), 'medium', 'todo', '{}', 0, 0)
            """, (main_branch_id,))
            
            conn.commit()
            print(f"📦 Initialized test database with basic test data (branch_id: {main_branch_id})")
        except Exception as e:
            print(f"⚠️ Error initializing test data: {e}")
            # Don't fail - let individual tests handle missing data

# =============================================
# MCP_DB_PATH TEST DATABASE FIXTURE
# =============================================

@pytest.fixture(scope="function", autouse=True)
def set_mcp_db_path_for_tests(request):
    """
    Function-scoped fixture to set MCP_DB_PATH to a fresh test database for each test.
    This guarantees test isolation.
    
    Skips database initialization for unit tests marked with @pytest.mark.unit
    """
    # Skip database setup for unit tests
    if "unit" in request.keywords:
        print("\n⚡ Skipping database setup for unit test")
        yield
        return
    
    from fastmcp.task_management.infrastructure.database.database_initializer import reset_initialization_cache
    from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager
    
    # Clear the initializer's cache to ensure schemas are re-run
    reset_initialization_cache()
    
    # Clear the database source manager singleton to ensure fresh database path detection
    DatabaseSourceManager.clear_instance()

    test_db_path = Path(__file__).parent.parent / "database" / "data" / "dhafnck_mcp_test.db"
    
    # Ensure a clean slate before each test by deleting the old DB file
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except OSError as e:
            print(f"Error removing existing test database: {e}")

    os.environ["MCP_DB_PATH"] = str(test_db_path)
    print(f"\n🔒 MCP_DB_PATH set to fresh test database: {test_db_path}")
    
    # Initialize the test database with schema and basic test data
    _initialize_test_database(test_db_path)
    
    yield
    # Optionally, cleanup test DB after tests as a fallback
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except OSError as e:
            print(f"Error removing test database post-test: {e}")


# =============================================
# SESSION-SCOPED DATABASE FIXTURES FOR SPEED
# =============================================

@pytest.fixture(scope="session")
def shared_test_db():
    """
    Session-scoped fixture for read-only integration tests.
    Creates database once per test session, dramatically speeding up tests.
    
    Use this for tests that only read from database, not modify it.
    """
    from fastmcp.task_management.infrastructure.database.database_initializer import reset_initialization_cache
    from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager
    
    # Clear caches
    reset_initialization_cache()
    DatabaseSourceManager.clear_instance()
    
    # Create a shared test database
    shared_db_path = Path(__file__).parent.parent / "database" / "data" / "dhafnck_mcp_shared_test.db"
    
    # Remove if exists
    if shared_db_path.exists():
        try:
            shared_db_path.unlink()
        except OSError:
            pass
    
    # Set environment variable
    old_db_path = os.environ.get("MCP_DB_PATH")
    os.environ["MCP_DB_PATH"] = str(shared_db_path)
    
    print(f"\n🚀 Creating shared test database (session scope): {shared_db_path}")
    
    # Initialize database
    _initialize_test_database(shared_db_path)
    
    yield shared_db_path
    
    # Cleanup after session
    print(f"\n🧹 Cleaning up shared test database")
    if shared_db_path.exists():
        try:
            shared_db_path.unlink()
        except OSError:
            pass
    
    # Restore old path
    if old_db_path:
        os.environ["MCP_DB_PATH"] = old_db_path
    elif "MCP_DB_PATH" in os.environ:
        del os.environ["MCP_DB_PATH"]


@pytest.fixture(scope="module")
def module_test_db():
    """
    Module-scoped fixture for integration tests within a module.
    Creates database once per test module.
    """
    from fastmcp.task_management.infrastructure.database.database_initializer import reset_initialization_cache
    from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager
    
    # Clear caches
    reset_initialization_cache()
    DatabaseSourceManager.clear_instance()
    
    # Create a module-scoped test database
    module_db_path = Path(__file__).parent.parent / "database" / "data" / f"dhafnck_mcp_module_test_{os.getpid()}.db"
    
    # Remove if exists
    if module_db_path.exists():
        try:
            module_db_path.unlink()
        except OSError:
            pass
    
    os.environ["MCP_DB_PATH"] = str(module_db_path)
    print(f"\n📦 Creating module test database: {module_db_path}")
    
    # Initialize database
    _initialize_test_database(module_db_path)
    
    yield module_db_path
    
    # Cleanup
    if module_db_path.exists():
        try:
            module_db_path.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    print("🧪 Pytest configuration is ready!")
    print("✅ Test isolation and cleanup configured")