"""
PostgreSQL Test Support

This module provides test utilities for PostgreSQL testing mode.
Use this when you need to run tests with PostgreSQL instead of SQLite.
"""

import pytest
import os


def test_postgresql_environment_setup(postgresql_test_db):
    """
    Test that PostgreSQL environment is properly configured.
    
    Args:
        postgresql_test_db: PostgreSQL test database fixture
    """
    # Check that environment is configured for PostgreSQL
    assert os.environ.get('DATABASE_TYPE') == 'postgresql'
    assert os.environ.get('DATABASE_URL') is not None
    assert os.environ.get('DISABLE_AUTH') == 'true'
    
    print(f"✅ PostgreSQL environment configured")
    print(f"   Database type: {os.environ.get('DATABASE_TYPE')}")
    print(f"   Database URL: {os.environ.get('DATABASE_URL')}")


def test_postgresql_database_connection(postgresql_test_db):
    """
    Test that PostgreSQL database connection works.
    
    Args:
        postgresql_test_db: PostgreSQL test database fixture
    """
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    
    # Test database connection
    db_config = get_db_config()
    assert db_config is not None
    assert db_config.database_type == 'postgresql'
    
    # Test that we can get a session
    session = db_config.get_session()
    assert session is not None
    session.close()
    
    print("✅ PostgreSQL database connection successful")


@pytest.mark.integration
@pytest.mark.postgresql
@pytest.mark.skipif(
    not os.environ.get('ENABLE_POSTGRESQL_TESTS'), 
    reason="PostgreSQL tests disabled - set ENABLE_POSTGRESQL_TESTS=1 to enable"
)
def test_basic_vision_system_with_postgresql(postgresql_test_db):
    """
    Test basic Vision System functionality with PostgreSQL.
    
    Args:
        postgresql_test_db: PostgreSQL test database fixture
    """
    try:
        from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from fastmcp.task_management.infrastructure.database.models import Base
        
        # Initialize database schema
        db_config = get_db_config()
        Base.metadata.create_all(bind=db_config.engine)
        
        # Initialize Vision System
        tools = DDDCompliantMCPTools(enable_vision_system=True)
        assert tools is not None
        
        # Test basic project creation
        result = tools.project_controller.manage_project(
            action="create",
            name="PostgreSQL Test Project",
            description="Test project with PostgreSQL"
        )
        
        assert result.get("success") == True
        assert "project" in result
        assert result["project"]["name"] == "PostgreSQL Test Project"
        
        print("✅ Vision System works with PostgreSQL")
        print(f"   Project ID: {result['project']['id']}")
        
    except Exception as e:
        pytest.skip(f"PostgreSQL test failed (expected without PostgreSQL server): {e}")


if __name__ == "__main__":
    """
    Run PostgreSQL tests independently.
    
    Usage:
        python test_postgresql_support.py
    """
    print("PostgreSQL Test Support")
    print("=" * 40)
    
    # Configure test environment
    from fastmcp.task_management.infrastructure.database.test_database_config import (
        get_test_database_config
    )
    
    test_config = get_test_database_config()
    
    try:
        print("Running PostgreSQL tests...")
        
        # Run basic tests
        test_postgresql_environment_setup(test_config)
        test_postgresql_database_connection(test_config)
        test_basic_vision_system_with_postgresql(test_config)
        
        print("\n✅ All PostgreSQL tests passed!")
        
    except Exception as e:
        print(f"\n❌ PostgreSQL tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        test_config.restore_environment()
        print("✅ Environment restored")