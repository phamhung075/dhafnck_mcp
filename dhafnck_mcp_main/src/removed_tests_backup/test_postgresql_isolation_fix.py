"""
Test to verify PostgreSQL test isolation improvements
"""
import pytest
import uuid
from sqlalchemy import text
from fastmcp.task_management.infrastructure.database.database_config import get_db_config


class TestPostgreSQLIsolation:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test that verifies PostgreSQL test isolation is working correctly"""
    
    def test_database_cleanup_between_tests(self):
        """Test that database is properly cleaned between test runs"""
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Check that test data doesn't persist
            result = session.execute(text("""
                SELECT COUNT(*) as count 
                FROM global_contexts 
                WHERE id != 'global_singleton'
            """)).fetchone()
            
            # Should be 0 or None if properly cleaned
            assert result is None or result.count == 0, "Test data persisting between runs"
    
    def test_transaction_rollback_works(self):
        """Test that transactions are properly rolled back"""
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Insert test data
            session.execute(text("""
                INSERT INTO projects (id, name, description, user_id, status)
                VALUES ('test-rollback-proj', 'Test Rollback', 'Testing', 'test-user', 'active')
                ON CONFLICT (id) DO NOTHING
            """))
            
            # Don't commit - let it rollback
            session.rollback()
            
            # Verify data was not persisted
            result = session.execute(text("""
                SELECT COUNT(*) as count FROM projects WHERE id = 'test-rollback-proj'
            """)).fetchone()
            
            assert result.count == 0, "Transaction not properly rolled back"
    
    def test_fixture_creates_clean_state(self):
        """Test that fixtures provide clean database state"""
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Verify we have the default test data
            result = session.execute(text("""
                SELECT COUNT(*) as count FROM projects WHERE id = 'default_project'
            """)).fetchone()
            
            assert result.count == 1, "Default test project not found"
            
            # Verify we don't have leftover test data
            result = session.execute(text("""
                SELECT COUNT(*) as count FROM projects WHERE id != 'default_project'
            """)).fetchone()
            
            assert result.count == 0, "Leftover test data found"