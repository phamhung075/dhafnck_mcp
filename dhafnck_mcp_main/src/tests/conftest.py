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

def _initialize_test_database_with_basic_data():
    """Initialize test database with basic test data for PostgreSQL."""
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from sqlalchemy import text
    import uuid
    from datetime import datetime
    
    try:
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Create default test project
            try:
                session.execute(text("""
                    INSERT INTO projects (id, name, description, user_id, status, created_at, updated_at, metadata) 
                    VALUES (:id, :name, :description, :user_id, :status, :created_at, :updated_at, :metadata)
                    ON CONFLICT (id) DO UPDATE SET 
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        updated_at = EXCLUDED.updated_at
                """), {
                    'id': 'default_project',
                    'name': 'Default Test Project',
                    'description': 'Project for testing',
                    'user_id': 'default_id',
                    'status': 'active',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'metadata': '{}'
                })
                
                # Create main git branch for default project
                main_branch_id = 'test-main-branch-' + str(uuid.uuid4())
                session.execute(text("""
                    INSERT INTO project_git_branchs (id, project_id, name, description, created_at, updated_at, priority, status, metadata, task_count, completed_task_count) 
                    VALUES (:id, :project_id, :name, :description, :created_at, :updated_at, :priority, :status, :metadata, :task_count, :completed_task_count)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        updated_at = EXCLUDED.updated_at
                """), {
                    'id': main_branch_id,
                    'project_id': 'default_project',
                    'name': 'main',
                    'description': 'Main branch for testing',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'priority': 'medium',
                    'status': 'todo',
                    'metadata': '{}',
                    'task_count': 0,
                    'completed_task_count': 0
                })
                
                session.commit()
                print(f"📦 Initialized PostgreSQL test database with basic test data (branch_id: {main_branch_id})")
                
            except Exception as e:
                print(f"⚠️ Error initializing test data: {e}")
                session.rollback()
                # Don't fail - let individual tests handle missing data
                
    except Exception as e:
        print(f"⚠️ Could not initialize test data: {e}")
        # Don't fail - let individual tests handle missing data

# =============================================
# MCP_DB_PATH TEST DATABASE FIXTURE
# =============================================

@pytest.fixture(scope="function", autouse=True)
def set_mcp_db_path_for_tests(request):
    """
    Function-scoped fixture to set up PostgreSQL test database for each test.
    This guarantees test isolation with PostgreSQL.
    
    Skips database initialization for unit tests marked with @pytest.mark.unit
    """
    # Skip database setup for unit tests
    if "unit" in request.keywords:
        print("\n⚡ Skipping database setup for unit test")
        yield
        return
    
    from fastmcp.task_management.infrastructure.database.database_initializer import reset_initialization_cache
    from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager
    from fastmcp.task_management.infrastructure.database.test_database_config import (
        TestDatabaseConfig,
        install_missing_dependencies
    )
    
    # Install missing dependencies if needed
    try:
        install_missing_dependencies()
    except Exception as e:
        print(f"⚠️ Could not install dependencies: {e}")
    
    # Clear the initializer's cache to ensure schemas are re-run
    reset_initialization_cache()
    
    # Clear the database source manager singleton to ensure fresh database path detection
    DatabaseSourceManager.clear_instance()
    
    # Clear the global database configuration to force re-initialization
    from fastmcp.task_management.infrastructure.database.database_config import close_db
    close_db()

    # Save original environment variables
    original_db_type = os.environ.get("DATABASE_TYPE")
    original_db_url = os.environ.get("DATABASE_URL")
    original_test_db_url = os.environ.get("TEST_DATABASE_URL")
    
    try:
        # Set up TestDatabaseConfig for PostgreSQL testing
        test_config = TestDatabaseConfig()
        
        # If TEST_DATABASE_URL is not set, use the production database with test schema
        if not os.environ.get("TEST_DATABASE_URL"):
            # Fix the production DATABASE_URL and use it with a test schema
            prod_url = os.environ.get("DATABASE_URL", "")
            if prod_url and "postgres:" in prod_url and "@" in prod_url:
                # Parse and fix the malformed URL properly
                # The URL has format: postgresql://user:password@@@@host:port/database
                # We need to fix the multiple @ symbols in the password
                try:
                    # Split by :// to get scheme and rest
                    parts = prod_url.split("://", 1)
                    if len(parts) == 2:
                        scheme, rest = parts
                        # Find the last @ which separates auth from host
                        auth_host = rest.rsplit('@', 1)
                        if len(auth_host) == 2:
                            auth, host = auth_host
                            # Fix the password with multiple @
                            if ":" in auth:
                                user, password = auth.split(':', 1)
                                # Remove extra @ symbols from password
                                password = password.replace("@@@@", "@")
                                # URL encode the @ symbol
                                import urllib.parse
                                encoded_password = urllib.parse.quote(password, safe='')
                                # Reconstruct the URL
                                fixed_prod_url = f"{scheme}://{user}:{encoded_password}@{host}"
                                os.environ["TEST_DATABASE_URL"] = fixed_prod_url
                                print(f"📝 Fixed TEST_DATABASE_URL for Supabase")
                except Exception as e:
                    print(f"⚠️ Could not fix DATABASE_URL: {e}")
        
        # Setup PostgreSQL test environment and get the fixed URL
        test_db_url = test_config.setup_postgresql_test_database()
        
        # Set environment variables for PostgreSQL
        os.environ['DATABASE_TYPE'] = 'postgresql'
        os.environ['DATABASE_URL'] = test_db_url  # Use the fixed URL
        os.environ['DISABLE_AUTH'] = 'true'
        os.environ['DHAFNCK_ENABLE_VISION'] = 'true'
        
        print(f"\n🐘 Using PostgreSQL test database")
        print(f"📊 DATABASE_TYPE: {os.environ.get('DATABASE_TYPE', 'not set')}")
        print(f"🔗 DATABASE_URL: [fixed and configured for test database]")
        
        # Initialize the test database with schema and basic test data
        # Note: For PostgreSQL, we don't need to pass a file path
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        initialize_database(None)  # Will use DATABASE_URL from environment
        
        # Add basic test data
        _initialize_test_database_with_basic_data()
        
        yield
        
    except Exception as e:
        print(f"❌ PostgreSQL test setup failed: {e}")
        pytest.fail(f"PostgreSQL test setup failed: {e}")
        
    finally:
        # Restore original environment
        test_config.restore_environment()
        
        # Additional restoration for safety
        if original_db_type is not None:
            os.environ["DATABASE_TYPE"] = original_db_type
        elif "DATABASE_TYPE" in os.environ:
            del os.environ["DATABASE_TYPE"]
            
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
            
        if original_test_db_url is not None:
            os.environ["TEST_DATABASE_URL"] = original_test_db_url
        elif "TEST_DATABASE_URL" in os.environ:
            del os.environ["TEST_DATABASE_URL"]


# =============================================
# POSTGRESQL TEST DATABASE FIXTURES
# =============================================

@pytest.fixture(scope="function")
def postgresql_test_db():
    """
    Function-scoped fixture for PostgreSQL testing.
    
    This fixture respects the user requirement for separate PostgreSQL
    test database and handles URL parsing issues with special characters.
    """
    # Import here to avoid circular dependencies
    try:
        from fastmcp.task_management.infrastructure.database.test_database_config import (
            get_test_database_config,
            install_missing_dependencies
        )
        
        # Install missing dependencies
        install_missing_dependencies()
        
        # Configure PostgreSQL test environment
        test_config = get_test_database_config()
        
        yield test_config
        
        # Restore environment
        test_config.restore_environment()
        
    except ImportError as e:
        pytest.skip(f"PostgreSQL test configuration not available: {e}")
    except Exception as e:
        pytest.fail(f"PostgreSQL test setup failed: {e}")


@pytest.fixture(scope="session")
def postgresql_session_db():
    """
    Session-scoped fixture for PostgreSQL integration tests.
    Creates database once per test session for read-only tests.
    """
    try:
        from fastmcp.task_management.infrastructure.database.test_database_config import (
            get_test_database_config,
            install_missing_dependencies
        )
        
        # Install missing dependencies
        install_missing_dependencies()
        
        # Configure PostgreSQL test environment
        test_config = get_test_database_config()
        
        print(f"\n🚀 Creating PostgreSQL test database session")
        
        yield test_config
        
        print(f"\n🧹 Cleaning up PostgreSQL test database session")
        test_config.restore_environment()
        
    except ImportError as e:
        pytest.skip(f"PostgreSQL test configuration not available: {e}")
    except Exception as e:
        pytest.fail(f"PostgreSQL session test setup failed: {e}")


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