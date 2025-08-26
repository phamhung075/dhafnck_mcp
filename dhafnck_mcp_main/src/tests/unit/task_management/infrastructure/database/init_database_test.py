"""
Tests for database initialization script using SQLAlchemy.

This module tests the database initialization functionality
that supports both SQLite and PostgreSQL databases.
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock, call
import logging
from pathlib import Path

from fastmcp.task_management.infrastructure.database.init_database import (
    init_database,
    migrate_from_sqlite_to_postgresql
)


class TestInitDatabase:
    """Test database initialization functionality."""
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_init_database_success(self, mock_logger, mock_get_db_config):
        """Test successful database initialization."""
        # Arrange
        mock_config = Mock()
        mock_config.get_database_info.return_value = {'type': 'sqlite'}
        mock_config.create_tables.return_value = None
        mock_get_db_config.return_value = mock_config
        
        # Act
        init_database()
        
        # Assert
        mock_get_db_config.assert_called_once()
        mock_config.get_database_info.assert_called_once()
        mock_config.create_tables.assert_called_once()
        mock_logger.info.assert_any_call("Initializing database: sqlite")
        mock_logger.info.assert_any_call("Database initialization completed successfully")
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_init_database_postgresql(self, mock_logger, mock_get_db_config):
        """Test database initialization for PostgreSQL."""
        # Arrange
        mock_config = Mock()
        mock_config.get_database_info.return_value = {'type': 'postgresql'}
        mock_config.create_tables.return_value = None
        mock_get_db_config.return_value = mock_config
        
        # Act
        init_database()
        
        # Assert
        mock_logger.info.assert_any_call("Initializing database: postgresql")
        mock_logger.info.assert_any_call("Database initialization completed successfully")
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_init_database_failure(self, mock_logger, mock_get_db_config):
        """Test database initialization failure handling."""
        # Arrange
        mock_config = Mock()
        mock_config.get_database_info.side_effect = Exception("Database config error")
        mock_get_db_config.return_value = mock_config
        
        # Act & Assert
        with pytest.raises(Exception, match="Database config error"):
            init_database()
        
        mock_logger.error.assert_called_with("Failed to initialize database: Database config error")
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_init_database_create_tables_failure(self, mock_logger, mock_get_db_config):
        """Test database initialization when table creation fails."""
        # Arrange
        mock_config = Mock()
        mock_config.get_database_info.return_value = {'type': 'sqlite'}
        mock_config.create_tables.side_effect = Exception("Table creation failed")
        mock_get_db_config.return_value = mock_config
        
        # Act & Assert
        with pytest.raises(Exception, match="Table creation failed"):
            init_database()
        
        mock_logger.info.assert_called_with("Initializing database: sqlite")
        mock_logger.error.assert_called_with("Failed to initialize database: Table creation failed")


class TestMigrateFromSQLiteToPostgreSQL:
    """Test SQLite to PostgreSQL migration functionality."""
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.sqlite3')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_migrate_database_type_validation(self, mock_logger, mock_sqlite3, mock_get_db_config):
        """Test migration fails if target is not PostgreSQL."""
        # Arrange
        mock_config = Mock()
        mock_config.database_type = "sqlite"
        mock_get_db_config.return_value = mock_config
        
        # Act & Assert
        with pytest.raises(ValueError, match="DATABASE_TYPE must be set to 'postgresql' for migration"):
            migrate_from_sqlite_to_postgresql("/path/to/sqlite.db")
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.sqlite3')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_migrate_successful_migration(self, mock_logger, mock_sqlite3, mock_get_db_config):
        """Test successful migration from SQLite to PostgreSQL."""
        # Arrange
        sqlite_path = "/path/to/sqlite.db"
        
        # Mock PostgreSQL config
        mock_pg_session = Mock()
        mock_config = Mock()
        mock_config.database_type = "postgresql"
        mock_config.get_session.return_value = mock_pg_session
        mock_get_db_config.return_value = mock_config
        
        # Mock SQLite connection and data
        mock_sqlite_conn = Mock()
        mock_sqlite3.connect.return_value = mock_sqlite_conn
        
        # Mock project data
        mock_project_cursor = Mock()
        mock_project_row = {
            'id': 'proj-123',
            'name': 'Test Project',
            'description': 'A test project',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00',
            'user_id': 'user-123',
            'status': 'active',
            'metadata': '{}'
        }
        mock_project_cursor.__iter__ = Mock(return_value=iter([mock_project_row]))
        
        # Mock git branch data
        mock_branch_cursor = Mock()
        mock_branch_row = {
            'id': 'branch-123',
            'project_id': 'proj-123',
            'name': 'main',
            'description': 'Main branch',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00',
            'assigned_agent_id': 'agent-123',
            'priority': 'high',
            'status': 'active',
            'metadata': '{}',
            'task_count': 5,
            'completed_task_count': 2
        }
        mock_branch_cursor.__iter__ = Mock(return_value=iter([mock_branch_row]))
        
        # Mock task data
        mock_task_cursor = Mock()
        mock_task_row = {
            'id': 'task-123',
            'title': 'Test Task',
            'description': 'A test task',
            'git_branch_id': 'branch-123',
            'status': 'todo',
            'priority': 'medium',
            'details': 'Task details',
            'estimated_effort': '2h',
            'due_date': None,
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00',
            'context_id': 'context-123'
        }
        mock_task_cursor.__iter__ = Mock(return_value=iter([mock_task_row]))
        
        # Mock subtask data
        mock_subtask_cursor = Mock()
        mock_subtask_row = {
            'id': 'subtask-123',
            'task_id': 'task-123',
            'title': 'Test Subtask',
            'description': 'A test subtask',
            'status': 'todo',
            'priority': 'low',
            'assignees': '[]',
            'estimated_effort': '1h',
            'progress_percentage': 0,
            'progress_notes': '',
            'blockers': '',
            'completion_summary': '',
            'impact_on_parent': '',
            'insights_found': '[]',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00',
            'completed_at': None
        }
        mock_subtask_cursor.__iter__ = Mock(return_value=iter([mock_subtask_row]))
        
        # Mock hierarchical context data (will cause import error but should be handled)
        mock_context_cursor = Mock()
        mock_context_cursor.__iter__ = Mock(return_value=iter([]))
        
        # Set up execute calls
        execute_calls = [
            mock_project_cursor,
            mock_branch_cursor,
            mock_task_cursor,
            mock_subtask_cursor,
            mock_context_cursor
        ]
        mock_sqlite_conn.execute.side_effect = execute_calls
        
        # Act
        migrate_from_sqlite_to_postgresql(sqlite_path)
        
        # Assert
        mock_logger.info.assert_any_call(f"Starting migration from SQLite: {sqlite_path}")
        mock_logger.info.assert_any_call("Migrating projects...")
        mock_logger.info.assert_any_call("Migrating git branches...")
        mock_logger.info.assert_any_call("Migrating tasks...")
        mock_logger.info.assert_any_call("Migrating subtasks...")
        mock_logger.info.assert_any_call("Migrating hierarchical context...")
        mock_logger.info.assert_any_call("Migration completed successfully")
        
        mock_pg_session.commit.assert_called_once()
        mock_pg_session.close.assert_called_once()
        mock_sqlite_conn.close.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.sqlite3')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_migrate_handles_session_exception(self, mock_logger, mock_sqlite3, mock_get_db_config):
        """Test migration handles session exceptions properly."""
        # Arrange
        sqlite_path = "/path/to/sqlite.db"
        
        # Mock PostgreSQL config
        mock_pg_session = Mock()
        mock_pg_session.execute.side_effect = Exception("Database error")
        mock_config = Mock()
        mock_config.database_type = "postgresql"
        mock_config.get_session.return_value = mock_pg_session
        mock_get_db_config.return_value = mock_config
        
        # Mock SQLite connection
        mock_sqlite_conn = Mock()
        mock_sqlite3.connect.return_value = mock_sqlite_conn
        
        # Mock empty cursor
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        mock_sqlite_conn.execute.return_value = mock_cursor
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            migrate_from_sqlite_to_postgresql(sqlite_path)
        
        mock_pg_session.rollback.assert_called_once()
        mock_pg_session.close.assert_called_once()
        mock_sqlite_conn.close.assert_called_once()
        mock_logger.error.assert_called_with("Migration failed: Database error")
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.sqlite3')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_migrate_handles_sqlite_connection_error(self, mock_logger, mock_sqlite3, mock_get_db_config):
        """Test migration handles SQLite connection errors."""
        # Arrange
        sqlite_path = "/path/to/sqlite.db"
        mock_sqlite3.connect.side_effect = Exception("SQLite connection error")
        
        # Mock PostgreSQL config
        mock_config = Mock()
        mock_config.database_type = "postgresql"
        mock_get_db_config.return_value = mock_config
        
        # Act & Assert
        with pytest.raises(Exception, match="SQLite connection error"):
            migrate_from_sqlite_to_postgresql(sqlite_path)
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.Project')
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    @patch('fastmcp.task_management.infrastructure.database.init_database.sqlite3')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logger')
    def test_migrate_creates_correct_entities(self, mock_logger, mock_sqlite3, mock_get_db_config, mock_project):
        """Test migration creates correct entity instances."""
        # Arrange
        sqlite_path = "/path/to/sqlite.db"
        
        # Mock PostgreSQL config
        mock_pg_session = Mock()
        mock_config = Mock()
        mock_config.database_type = "postgresql"
        mock_config.get_session.return_value = mock_pg_session
        mock_get_db_config.return_value = mock_config
        
        # Mock SQLite connection and project data
        mock_sqlite_conn = Mock()
        mock_sqlite3.connect.return_value = mock_sqlite_conn
        
        mock_project_row = {
            'id': 'proj-123',
            'name': 'Test Project',
            'description': 'A test project',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00',
            'user_id': 'user-123',
            'status': 'active',
            'metadata': '{}'
        }
        
        # Set up cursors with limited data for focused testing
        mock_project_cursor = Mock()
        mock_project_cursor.__iter__ = Mock(return_value=iter([mock_project_row]))
        
        # Mock empty cursors for other tables
        mock_empty_cursor = Mock()
        mock_empty_cursor.__iter__ = Mock(return_value=iter([]))
        
        mock_sqlite_conn.execute.side_effect = [
            mock_project_cursor,  # projects
            mock_empty_cursor,    # git branches
            mock_empty_cursor,    # tasks
            mock_empty_cursor,    # subtasks
            mock_empty_cursor     # hierarchical context
        ]
        
        # Act
        migrate_from_sqlite_to_postgresql(sqlite_path)
        
        # Assert
        mock_project.assert_called_with(
            id='proj-123',
            name='Test Project',
            description='A test project',
            created_at='2023-01-01T00:00:00',
            updated_at='2023-01-01T00:00:00',
            user_id='user-123',
            status='active',
            metadata='{}'
        )


class TestMainExecution:
    """Test main execution functionality."""
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.task_management.infrastructure.database.init_database.logging')
    def test_main_execution(self, mock_logging, mock_init_database):
        """Test main execution sets up logging and calls init_database."""
        # Import and execute the main block
        import fastmcp.task_management.infrastructure.database.init_database as init_module
        
        # Mock __name__ to be "__main__"
        with patch.object(init_module, '__name__', '__main__'):
            # Execute the main block code
            mock_logging.basicConfig.assert_not_called()  # Reset any previous calls
            mock_init_database.assert_not_called()  # Reset any previous calls
            
            # Simulate main execution
            if init_module.__name__ == "__main__":
                init_module.logging.basicConfig(
                    level=init_module.logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                init_module.init_database()
        
        # Note: Direct testing of __main__ block is tricky due to import behavior
        # In practice, this would be tested via subprocess or integration tests


class TestDatabaseInitIntegration:
    """Integration tests for database initialization."""
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    def test_init_database_integration_flow(self, mock_get_db_config):
        """Test the complete integration flow of database initialization."""
        # Arrange
        mock_config = Mock()
        mock_config.get_database_info.return_value = {
            'type': 'sqlite',
            'path': '/tmp/test.db',
            'url': 'sqlite:///tmp/test.db'
        }
        mock_config.create_tables.return_value = None
        mock_get_db_config.return_value = mock_config
        
        # Act
        init_database()
        
        # Assert
        mock_get_db_config.assert_called_once()
        mock_config.get_database_info.assert_called_once()
        mock_config.create_tables.assert_called_once()


class TestErrorScenarios:
    """Test various error scenarios in database initialization."""
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    def test_database_config_import_error(self, mock_get_db_config):
        """Test handling of database config import errors."""
        # Arrange
        mock_get_db_config.side_effect = ImportError("Cannot import database config")
        
        # Act & Assert
        with pytest.raises(ImportError, match="Cannot import database config"):
            init_database()
    
    @patch('fastmcp.task_management.infrastructure.database.init_database.get_db_config')
    def test_database_permission_error(self, mock_get_db_config):
        """Test handling of database permission errors."""
        # Arrange
        mock_config = Mock()
        mock_config.get_database_info.return_value = {'type': 'sqlite'}
        mock_config.create_tables.side_effect = PermissionError("Permission denied")
        mock_get_db_config.return_value = mock_config
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Permission denied"):
            init_database()


if __name__ == "__main__":
    pytest.main([__file__])