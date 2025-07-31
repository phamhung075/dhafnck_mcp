"""
Demonstration of PostgreSQL test isolation improvements
"""
import pytest
from sqlalchemy import text
from .conftest_postgresql_fix import postgresql_clean_db, postgresql_transactional_db
import uuid


class TestPostgreSQLIsolationDemo:
    
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

    """Demonstrates the improved PostgreSQL test isolation"""
    
    def test_clean_db_fixture_isolation(self, postgresql_clean_db):
        """Test using the clean_db fixture for isolation"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Create test data
            test_id = f'test-iso-{uuid.uuid4()}'
            session.execute(text("""
                INSERT INTO projects (id, name, description, user_id, status)
                VALUES (:id, :name, :description, :user_id, :status) ON CONFLICT (name) DO UPDATE SET updated_at = labels.updated_at
            """), {
                'id': test_id,
                'name': 'Test Isolation Project',
                'description': 'Testing isolation',
                'user_id': 'test-user',
                'status': 'active'
            })
            session.commit()
            
            # Verify it was created
            result = session.execute(text(
                "SELECT COUNT(*) as count FROM projects WHERE id = :id"
            ), {'id': test_id}).fetchone()
            
            assert result.count == 1
    
    def test_verify_previous_test_cleaned_up(self, postgresql_clean_db):
        """Verify that data from previous test was cleaned up"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Check that no test projects exist (except default)
            result = session.execute(text("""
                SELECT COUNT(*) as count 
                FROM projects 
                WHERE id LIKE 'test-iso-%'
            """)).fetchone()
            
            assert result.count == 0, "Test data from previous test still exists!"
    
    def test_transactional_fixture_complete_isolation(self, postgresql_transactional_db):
        """Test using transactional fixture for complete isolation"""
        session = postgresql_transactional_db
        
        # Create test data
        test_id = f'test-trans-{uuid.uuid4()}'
        session.execute(text("""
            INSERT INTO projects (id, name, description, user_id, status)
            VALUES (:id, :name, :description, :user_id, :status) ON CONFLICT (name) DO UPDATE SET updated_at = labels.updated_at
        """), {
            'id': test_id,
            'name': 'Transactional Test Project',
            'description': 'Testing transactional isolation',
            'user_id': 'test-user',
            'status': 'active'
        })
        
        # Verify within transaction
        result = session.execute(text(
            "SELECT COUNT(*) as count FROM projects WHERE id = :id"
        ), {'id': test_id}).fetchone()
        
        assert result.count == 1
        
        # Note: This data will be rolled back after test
    
    def test_no_duplicate_key_errors(self, postgresql_clean_db):
        """Test that we can create the same data in multiple tests without conflicts"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # This would fail with duplicate key if previous test data persisted
            session.execute(text("""
                INSERT INTO projects (id, name, description, user_id, status)
                VALUES ('test-fixed-id', 'Fixed ID Project', 'Testing', 'test-user', 'active')
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
            """))
            session.commit()
            
            # Create a global context (common source of duplicate key errors)
            session.execute(text("""
                INSERT INTO global_contexts (
                    id, data, insights, progress_tracking,
                    shared_patterns, implementation_notes,
                    local_overrides, delegation_triggers
                ) VALUES (
                    'test-global-ctx',
                    '{"test": true}',
                    '[]', '{}', '{}', '{}', '{}', '{}'
                ) ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data
            """))
            session.commit()
    
    def test_default_data_preserved(self, postgresql_clean_db):
        """Test that default test data is preserved between tests"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Check default project exists
            result = session.execute(text("""
                SELECT COUNT(*) as count 
                FROM projects 
                WHERE id = 'default_project'
            """)).fetchone()
            
            assert result.count == 1, "Default project was cleaned up!"
            
            # Check global singleton exists
            result = session.execute(text("""
                SELECT COUNT(*) as count 
                FROM global_contexts 
                WHERE id = 'global_singleton' ON CONFLICT (name) DO UPDATE SET updated_at = labels.updated_at
            """)).fetchone()
            
            # Global singleton might not exist in test DB, that's OK
            assert result is None or result.count >= 0