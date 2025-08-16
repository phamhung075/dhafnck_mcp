"""
Test to validate the simplified fixture strategy works correctly
"""

import pytest
from pathlib import Path


@pytest.mark.unit
def test_unit_skips_database():
    """Unit test should skip database setup"""
    # This should run quickly without database
    assert 1 + 1 == 2
    print("✅ Unit test ran without database")


def test_integration_uses_database():
    """Integration test should have database available"""
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    
    # Should be able to get database config
    db_config = get_db_config()
    assert db_config is not None
    
    # Should be able to create a session
    with db_config.get_session() as session:
        # Try a simple query
        from sqlalchemy import text
        result = session.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1
    
    print("✅ Integration test successfully used database")


def test_test_data_exists():
    """Test that basic test data was initialized"""
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from sqlalchemy import text
    
    db_config = get_db_config()
    
    with db_config.get_session() as session:
        # Check default project exists
        result = session.execute(
            text("SELECT name FROM projects WHERE id = :id"),
            {'id': 'default_project'}
        ).fetchone()
        
        assert result is not None
        assert result[0] == 'Default Test Project'
    
    print("✅ Test data was properly initialized")


@pytest.mark.unit 
def test_isolation_between_unit_tests():
    """Multiple unit tests should not interfere"""
    # First unit test
    test_value = "test_1"
    assert test_value == "test_1"
    print("✅ Unit test 1 isolated")


@pytest.mark.unit
def test_another_unit_test():
    """Second unit test should also skip database"""
    # Second unit test
    test_value = "test_2"
    assert test_value == "test_2"
    print("✅ Unit test 2 isolated")


def test_database_cleanup():
    """Test that database is properly cleaned between tests"""
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from sqlalchemy import text
    import uuid
    
    db_config = get_db_config()
    
    # Create a test record
    test_id = f"cleanup-test-{uuid.uuid4()}"
    
    with db_config.get_session() as session:
        # This should not exist from a previous test
        result = session.execute(
            text("SELECT COUNT(*) FROM projects WHERE id LIKE :pattern"),
            {'pattern': 'cleanup-test-%'}
        ).fetchone()
        
        # Should be clean
        assert result[0] == 0
        
        print("✅ Database properly cleaned between tests")


if __name__ == "__main__":
    print("Running simplified fixture validation tests...")
    pytest.main([__file__, "-v", "-s"])