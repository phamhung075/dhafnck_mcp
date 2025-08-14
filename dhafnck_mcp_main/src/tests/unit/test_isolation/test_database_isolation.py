"""Test Database Isolation - TDD Phase 1
Tests for ensuring proper database isolation between test runs.
Written BEFORE implementation following TDD methodology.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from typing import Any, Generator

# These imports will fail initially - that's expected in TDD
# We're testing what SHOULD exist, not what does exist
from fastmcp.task_management.infrastructure.database.test_helpers import (
    DatabaseIsolation,
    TestDatabaseAdapter,
    setup_test_database,
    cleanup_test_database,
    create_isolated_session
)


class TestDatabaseIsolation:
    """Test suite for database isolation functionality"""
    
    def test_database_isolation_creates_separate_test_database(self):
        """Test that DatabaseIsolation creates a separate test database"""
        # Arrange
        isolation = DatabaseIsolation()
        
        # Act
        test_db = isolation.create_test_database("test_isolation_db")
        
        # Assert
        assert test_db is not None
        assert test_db.database_name == "test_isolation_db"
        assert test_db.is_isolated is True
        assert test_db.connection_string != isolation.get_production_connection_string()
    
    def test_database_isolation_cleanup_removes_test_data(self):
        """Test that cleanup properly removes all test data"""
        # Arrange
        isolation = DatabaseIsolation()
        test_db = isolation.create_test_database("test_cleanup_db")
        
        # Insert test data
        test_db.insert_test_data({"tasks": [{"id": "test-1", "title": "Test Task"}]})
        
        # Act
        isolation.cleanup_database(test_db)
        
        # Assert
        data = test_db.query_all("tasks")
        assert len(data) == 0
        assert test_db.is_clean is True
    
    def test_database_isolation_prevents_cross_test_contamination(self):
        """Test that data from one test doesn't affect another"""
        # Arrange
        isolation = DatabaseIsolation()
        
        # Test 1
        db1 = isolation.create_test_database("test_db_1")
        db1.insert_test_data({"tasks": [{"id": "task-1", "title": "Task 1"}]})
        
        # Test 2
        db2 = isolation.create_test_database("test_db_2")
        
        # Assert
        data_db1 = db1.query_all("tasks")
        data_db2 = db2.query_all("tasks")
        
        assert len(data_db1) == 1
        assert len(data_db2) == 0
        assert data_db1[0]["id"] == "task-1"
    
    def test_setup_test_database_helper_function(self):
        """Test the setup_test_database helper function"""
        # Act
        test_adapter = setup_test_database("helper_test_db")
        
        # Assert
        assert test_adapter is not None
        assert isinstance(test_adapter, TestDatabaseAdapter)
        assert test_adapter.is_ready is True
        assert test_adapter.database_name == "helper_test_db"
    
    def test_cleanup_test_database_helper_function(self):
        """Test the cleanup_test_database helper function"""
        # Arrange
        test_adapter = setup_test_database("cleanup_helper_db")
        test_adapter.insert_test_data({"tasks": [{"id": "test-cleanup"}]})
        
        # Act
        cleanup_result = cleanup_test_database(test_adapter)
        
        # Assert
        assert cleanup_result is True
        assert test_adapter.is_clean is True
        data = test_adapter.query_all("tasks")
        assert len(data) == 0
    
    def test_create_isolated_session_returns_valid_session(self):
        """Test that create_isolated_session returns a valid SQLAlchemy session"""
        # Act
        session = create_isolated_session("session_test_db")
        
        # Assert
        assert session is not None
        assert isinstance(session, Session)
        assert session.is_active is True
        assert hasattr(session, 'commit')
        assert hasattr(session, 'rollback')
        assert hasattr(session, 'close')
    
    def test_isolated_session_rollback_preserves_isolation(self):
        """Test that rollback in isolated session preserves isolation"""
        # Arrange
        session = create_isolated_session("rollback_test_db")
        
        # Act - Try to insert and rollback
        from fastmcp.task_management.infrastructure.database.models import Task
        task = Task(id="rollback-test", title="Should be rolled back")
        session.add(task)
        session.rollback()
        
        # Assert
        result = session.query(Task).filter_by(id="rollback-test").first()
        assert result is None
    
    def test_multiple_isolated_sessions_are_independent(self):
        """Test that multiple isolated sessions don't interfere"""
        # Arrange
        session1 = create_isolated_session("session_1_db")
        session2 = create_isolated_session("session_2_db")
        
        # Act
        from fastmcp.task_management.infrastructure.database.models import Task
        task1 = Task(id="session-1-task", title="Session 1 Task")
        task2 = Task(id="session-2-task", title="Session 2 Task")
        
        session1.add(task1)
        session1.commit()
        
        session2.add(task2)
        session2.commit()
        
        # Assert
        result1 = session1.query(Task).all()
        result2 = session2.query(Task).all()
        
        assert len(result1) == 1
        assert len(result2) == 1
        assert result1[0].id == "session-1-task"
        assert result2[0].id == "session-2-task"
    
    def test_test_database_adapter_provides_utility_methods(self):
        """Test that TestDatabaseAdapter provides necessary utility methods"""
        # Arrange
        adapter = TestDatabaseAdapter("utility_test_db")
        
        # Assert - Check required methods exist
        assert hasattr(adapter, 'insert_test_data')
        assert hasattr(adapter, 'query_all')
        assert hasattr(adapter, 'query_by_id')
        assert hasattr(adapter, 'delete_all')
        assert hasattr(adapter, 'get_session')
        assert hasattr(adapter, 'reset')
        assert hasattr(adapter, 'get_connection_string')
    
    def test_database_isolation_with_transactions(self):
        """Test that database isolation works with transactions"""
        # Arrange
        adapter = setup_test_database("transaction_test_db")
        session = adapter.get_session()
        
        # Act
        with adapter.transaction() as tx_session:
            from fastmcp.task_management.infrastructure.database.models import Task
            task = Task(id="tx-test", title="Transaction Test")
            tx_session.add(task)
            # Transaction should auto-commit on context exit
        
        # Assert
        result = session.query(Task).filter_by(id="tx-test").first()
        assert result is not None
        assert result.title == "Transaction Test"
    
    def test_database_isolation_thread_safety(self):
        """Test that database isolation is thread-safe"""
        import threading
        results = []
        
        def create_isolated_db(name: str):
            adapter = setup_test_database(name)
            adapter.insert_test_data({"tasks": [{"id": f"{name}-task"}]})
            data = adapter.query_all("tasks")
            results.append((name, len(data)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=create_isolated_db, args=(f"thread_{i}_db",))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Assert each thread had isolated database
        assert len(results) == 5
        for name, count in results:
            assert count == 1  # Each thread should only see its own data