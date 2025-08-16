"""
PostgreSQL Test Configuration Improvements

This module provides enhanced test isolation for PostgreSQL tests.
Import this in conftest.py to enable better test isolation.
"""
import pytest
from sqlalchemy import text
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)


def cleanup_postgresql_test_data(session, preserve_defaults=True):
    """
    Clean up test data from PostgreSQL database.
    
    Args:
        session: SQLAlchemy session
        preserve_defaults: If True, preserves default test fixtures
    """
    try:
        # Start with dependent tables and work backwards
        
        # 1. Clean up subtasks
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM subtasks WHERE task_id NOT IN (
                    SELECT id FROM tasks WHERE git_branch_id IN (
                        SELECT id FROM project_git_branchs WHERE project_id = 'default_project'
                    )
                )
            """))
        else:
            session.execute(text("TRUNCATE TABLE subtasks CASCADE"))
        
        # 2. Clean up task contexts
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM task_contexts WHERE task_id NOT IN (
                    SELECT id FROM tasks WHERE git_branch_id IN (
                        SELECT id FROM project_git_branchs WHERE project_id = 'default_project'
                    )
                )
            """))
        else:
            session.execute(text("TRUNCATE TABLE task_contexts CASCADE"))
        
        # 3. Clean up tasks
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM tasks WHERE git_branch_id NOT IN (
                    SELECT id FROM project_git_branchs WHERE project_id = 'default_project'
                )
            """))
        else:
            session.execute(text("TRUNCATE TABLE tasks CASCADE"))
        
        # 4. Clean up branch contexts
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM branch_contexts WHERE branch_id NOT IN (
                    SELECT id FROM project_git_branchs WHERE project_id = 'default_project'
                )
            """))
        else:
            session.execute(text("TRUNCATE TABLE branch_contexts CASCADE"))
        
        # 5. Clean up git branches
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM project_git_branchs 
                WHERE project_id != 'default_project'
            """))
        else:
            session.execute(text("TRUNCATE TABLE project_git_branchs CASCADE"))
        
        # 6. Clean up project contexts  
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM project_contexts WHERE project_id != 'default_project'
            """))
        else:
            session.execute(text("TRUNCATE TABLE project_contexts CASCADE"))
        
        # 7. Clean up projects
        if preserve_defaults:
            session.execute(text("""
                DELETE FROM projects WHERE id != 'default_project'
            """))
        else:
            session.execute(text("TRUNCATE TABLE projects CASCADE"))
        
        # 8. Clean up global contexts (always preserve singleton)
        session.execute(text("""
            DELETE FROM global_contexts WHERE id != 'global_singleton'
        """))
        
        # 9. Clean up other tables
        session.execute(text("DELETE FROM agents WHERE project_id != 'default_project'"))
        session.execute(text("DELETE FROM rules WHERE id != 'default_rule'"))
        
        session.commit()
        logger.debug("PostgreSQL test data cleanup completed")
        
    except Exception as e:
        logger.warning(f"Test cleanup warning: {e}")
        session.rollback()


def ensure_postgresql_defaults(session):
    """Ensure default test data exists in PostgreSQL"""
    try:
        # Ensure global singleton
        session.execute(text("""
            INSERT INTO global_contexts (
                id, data, insights, progress_tracking,
                shared_patterns, implementation_notes,
                local_overrides, delegation_triggers,
                created_at, updated_at
            ) VALUES (
                'global_singleton',
                '{"organization": "test"}',
                '[]', '{}', '{}', '{}', '{}', '{}',
                :created_at, :updated_at
            ) ON CONFLICT (id) DO NOTHING
        """), {
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        })
        
        # Ensure default project
        session.execute(text("""
            INSERT INTO projects (
                id, name, description, user_id, status,
                created_at, updated_at, metadata
            ) VALUES (
                'default_project',
                'Default Test Project', 
                'Project for testing',
                'default_id',
                'active',
                :created_at, :updated_at,
                '{}'
            ) ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at
        """), {
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        })
        
        # Ensure at least one branch exists
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM project_git_branchs 
            WHERE project_id = 'default_project' AND name = 'main'
        """)).fetchone()
        
        if result.count == 0:
            branch_id = f'test-main-branch-{uuid.uuid4()}'
            session.execute(text("""
                INSERT INTO project_git_branchs (
                    id, project_id, name, description,
                    created_at, updated_at, priority, status,
                    metadata, task_count, completed_task_count
                ) VALUES (
                    :id, 'default_project', 'main',
                    'Main test branch',
                    :created_at, :updated_at,
                    'medium', 'todo', '{}', 0, 0
                )
            """), {
                'id': branch_id,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            })
        
        session.commit()
        
    except Exception as e:
        logger.warning(f"Could not ensure defaults: {e}")
        session.rollback()


@pytest.fixture(scope="function")
def postgresql_clean_db():
    """
    Fixture that ensures clean PostgreSQL state for each test.
    
    This fixture:
    1. Cleans up before test (except defaults)
    2. Ensures default data exists
    3. Cleans up after test
    """
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    
    db_config = get_db_config()
    
    # Pre-test cleanup
    with db_config.get_session() as session:
        cleanup_postgresql_test_data(session, preserve_defaults=True)
        ensure_postgresql_defaults(session)
    
    yield
    
    # Post-test cleanup
    with db_config.get_session() as session:
        cleanup_postgresql_test_data(session, preserve_defaults=True)


@pytest.fixture(scope="function")
def postgresql_transactional_db():
    """
    Fixture that runs test in a transaction that's rolled back.
    
    This provides the strongest isolation - nothing persists.
    """
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from sqlalchemy.orm import Session
    
    db_config = get_db_config()
    connection = db_config.engine.connect()
    transaction = connection.begin()
    
    # Create session bound to this connection
    session = Session(bind=connection)
    
    # Ensure defaults exist
    ensure_postgresql_defaults(session)
    
    # Create a savepoint for the actual test
    savepoint = connection.begin_nested()
    
    yield session
    
    # Rollback to savepoint (undoes test changes)
    savepoint.rollback()
    
    # Close everything
    session.close()
    transaction.rollback()
    connection.close()


def pytest_runtest_setup(item):
    """
    Hook that runs before each test to ensure clean state.
    """
    if "postgresql" in item.keywords or "database" in item.keywords:
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        
        try:
            db_config = get_db_config()
            with db_config.get_session() as session:
                # Quick cleanup of obviously test-related data
                session.execute(text("""
                    DELETE FROM tasks 
                    WHERE title LIKE 'Test%' 
                    OR title LIKE 'test%'
                    OR id LIKE 'test-%'
                """))
                session.execute(text("""
                    DELETE FROM projects 
                    WHERE id LIKE 'test-%' 
                    AND id != 'default_project'
                """))
                session.commit()
        except Exception as e:
            logger.debug(f"Pre-test cleanup: {e}")


# Export fixtures
__all__ = [
    'postgresql_clean_db',
    'postgresql_transactional_db',
    'cleanup_postgresql_test_data',
    'ensure_postgresql_defaults'
]