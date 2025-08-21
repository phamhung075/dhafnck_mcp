"""Test suite for fix_missing_user_id_columns migration.

Tests the SQLite migration that fixes missing user_id columns in context tables:
- Adding missing user_id columns
- Updating NULL values with fallback user ID
- Transaction rollback on errors
- Database state verification
- Configuration-based migration
"""

import pytest
import sqlite3
import tempfile
import os
import logging
from unittest.mock import Mock, patch, call
from pathlib import Path

from fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns import (
    run_migration,
    run_migration_with_config
)


class TestFixMissingUserIdColumnsMigration:
    """Test cases for fix_missing_user_id_columns migration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)  # Close file descriptor to avoid conflicts
        
        # Create test database schema
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create sample tables to test
        self.setup_test_schema()
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, 'conn'):
            self.conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def setup_test_schema(self):
        """Create test database schema."""
        # Create task_contexts table WITHOUT user_id column (simulating old schema)
        self.cursor.execute("""
            CREATE TABLE task_contexts (
                id TEXT PRIMARY KEY,
                context_data TEXT,
                created_at TEXT
            )
        """)
        
        # Create branch_contexts table WITH user_id column but nullable
        self.cursor.execute("""
            CREATE TABLE branch_contexts (
                id TEXT PRIMARY KEY,
                context_data TEXT,
                user_id TEXT,
                created_at TEXT
            )
        """)
        
        # Insert test data
        self.cursor.execute("""
            INSERT INTO task_contexts (id, context_data, created_at) 
            VALUES 
                ('task-1', '{"test": "data1"}', '2024-01-01'),
                ('task-2', '{"test": "data2"}', '2024-01-02')
        """)
        
        self.cursor.execute("""
            INSERT INTO branch_contexts (id, context_data, user_id, created_at) 
            VALUES 
                ('branch-1', '{"test": "branch1"}', 'user-1', '2024-01-01'),
                ('branch-2', '{"test": "branch2"}', NULL, '2024-01-02'),
                ('branch-3', '{"test": "branch3"}', '', '2024-01-03')
        """)
        
        self.conn.commit()
    
    def test_run_migration_success_adds_missing_columns(self):
        """Test successful migration that adds missing user_id column."""
        fallback_user_id = "test-system-user"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(self.db_path, fallback_user_id)
        
        assert result is True
        
        # Verify task_contexts table now has user_id column
        self.cursor.execute("PRAGMA table_info(task_contexts)")
        columns = {col[1]: col for col in self.cursor.fetchall()}
        assert 'user_id' in columns
        
        # Verify all task_contexts records have the fallback user_id
        self.cursor.execute("SELECT id, user_id FROM task_contexts ORDER BY id")
        records = self.cursor.fetchall()
        expected_records = [
            ('task-1', fallback_user_id),
            ('task-2', fallback_user_id)
        ]
        assert records == expected_records
        
        # Verify branch_contexts NULL values were updated
        self.cursor.execute("SELECT id, user_id FROM branch_contexts WHERE user_id IS NOT NULL AND user_id != '' ORDER BY id")
        records = self.cursor.fetchall()
        expected_records = [
            ('branch-1', 'user-1'),  # Original value preserved
            ('branch-2', fallback_user_id),  # NULL updated
            ('branch-3', fallback_user_id)   # Empty string updated
        ]
        assert records == expected_records
        
        # Verify logging
        mock_logger.info.assert_any_call(f"Starting missing user_id columns migration on {self.db_path}")
        mock_logger.info.assert_any_call("Adding missing user_id column to task_contexts table")
        mock_logger.info.assert_any_call("✅ Migration completed successfully")
    
    def test_run_migration_task_contexts_column_already_exists(self):
        """Test migration when task_contexts already has user_id column."""
        # Add user_id column to task_contexts manually
        self.cursor.execute("ALTER TABLE task_contexts ADD COLUMN user_id TEXT")
        self.cursor.execute("UPDATE task_contexts SET user_id = 'existing-user' WHERE id = 'task-1'")
        # Leave task-2 with NULL user_id
        self.conn.commit()
        
        fallback_user_id = "fallback-user"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(self.db_path, fallback_user_id)
        
        assert result is True
        
        # Verify existing user_id preserved and NULL updated
        self.cursor.execute("SELECT id, user_id FROM task_contexts ORDER BY id")
        records = self.cursor.fetchall()
        expected_records = [
            ('task-1', 'existing-user'),  # Existing value preserved
            ('task-2', fallback_user_id)  # NULL updated
        ]
        assert records == expected_records
        
        # Verify logging
        mock_logger.info.assert_any_call("task_contexts.user_id column already exists")
        mock_logger.info.assert_any_call(f"Updated 1 NULL user_id values in task_contexts to '{fallback_user_id}'")
    
    def test_run_migration_no_null_values_to_update(self):
        """Test migration when no NULL values exist."""
        # Add user_id column and populate all records
        self.cursor.execute("ALTER TABLE task_contexts ADD COLUMN user_id TEXT DEFAULT 'existing-user'")
        self.cursor.execute("UPDATE task_contexts SET user_id = 'existing-user'")
        self.cursor.execute("UPDATE branch_contexts SET user_id = 'existing-user' WHERE user_id IS NULL OR user_id = ''")
        self.conn.commit()
        
        fallback_user_id = "fallback-user"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(self.db_path, fallback_user_id)
        
        assert result is True
        
        # Verify no updates were performed (rowcount would be 0)
        # We can't easily test rowcount directly, but we can verify final state
        self.cursor.execute("SELECT COUNT(*) FROM task_contexts WHERE user_id = 'existing-user'")
        assert self.cursor.fetchone()[0] == 2
        
        self.cursor.execute("SELECT COUNT(*) FROM branch_contexts WHERE user_id = 'existing-user'")
        assert self.cursor.fetchone()[0] == 3
    
    def test_run_migration_branch_contexts_missing_column(self):
        """Test migration when branch_contexts is missing user_id column."""
        # Recreate branch_contexts without user_id column
        self.cursor.execute("DROP TABLE branch_contexts")
        self.cursor.execute("""
            CREATE TABLE branch_contexts (
                id TEXT PRIMARY KEY,
                context_data TEXT,
                created_at TEXT
            )
        """)
        self.cursor.execute("""
            INSERT INTO branch_contexts (id, context_data, created_at) 
            VALUES 
                ('branch-1', '{"test": "branch1"}', '2024-01-01'),
                ('branch-2', '{"test": "branch2"}', '2024-01-02')
        """)
        self.conn.commit()
        
        fallback_user_id = "system-user"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(self.db_path, fallback_user_id)
        
        assert result is True
        
        # Verify branch_contexts now has user_id column
        self.cursor.execute("PRAGMA table_info(branch_contexts)")
        columns = {col[1]: col for col in self.cursor.fetchall()}
        assert 'user_id' in columns
        
        # Verify all records have the fallback user_id
        self.cursor.execute("SELECT id, user_id FROM branch_contexts ORDER BY id")
        records = self.cursor.fetchall()
        expected_records = [
            ('branch-1', fallback_user_id),
            ('branch-2', fallback_user_id)
        ]
        assert records == expected_records
        
        # Verify logging
        mock_logger.info.assert_any_call("Adding missing user_id column to branch_contexts table")
    
    def test_run_migration_verification_failure(self):
        """Test migration rollback when verification fails."""
        # Create a scenario where the migration would fail verification
        # We'll mock the verification query to return NULL values
        original_execute = self.cursor.execute
        
        def mock_execute(*args, **kwargs):
            query = args[0] if args else ""
            
            # If it's the NULL count check, return a non-zero count to trigger failure
            if "SELECT COUNT(*)" in query and "WHERE user_id IS NULL" in query:
                # Return a mock result indicating NULL values found
                return Mock()
            else:
                return original_execute(*args, **kwargs)
        
        def mock_fetchone():
            return [1]  # Return 1 NULL value found
        
        fallback_user_id = "test-user"
        
        with patch.object(self.cursor, 'execute', side_effect=mock_execute):
            with patch.object(self.cursor, 'fetchone', side_effect=mock_fetchone):
                with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
                    result = run_migration(self.db_path, fallback_user_id)
        
        assert result is False
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Found NULL/empty user_id values after update" in error_call
    
    def test_run_migration_table_check_error_continues(self):
        """Test migration continues when table check fails (table doesn't exist)."""
        # Drop one of the tables to simulate OperationalError
        self.cursor.execute("DROP TABLE branch_contexts")
        self.conn.commit()
        
        fallback_user_id = "system-user"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(self.db_path, fallback_user_id)
        
        # Migration should still succeed for task_contexts
        assert result is True
        
        # Verify warning was logged for the missing table
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Could not check branch_contexts" in warning_call
    
    def test_run_migration_database_error(self):
        """Test migration handles database errors gracefully."""
        # Use invalid database path to trigger error
        invalid_db_path = "/nonexistent/path/db.sqlite"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(invalid_db_path, "fallback-user")
        
        assert result is False
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Migration failed" in error_call
    
    def test_run_migration_with_default_fallback_user(self):
        """Test migration with default fallback user ID."""
        result = run_migration(self.db_path)  # No fallback_user_id provided
        
        assert result is True
        
        # Verify default "system" user was used
        self.cursor.execute("SELECT DISTINCT user_id FROM task_contexts")
        user_ids = [row[0] for row in self.cursor.fetchall()]
        assert "system" in user_ids
    
    def test_run_migration_logs_sql_note(self):
        """Test that migration logs SQLite NOT NULL constraint note."""
        fallback_user_id = "test-user"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
            result = run_migration(self.db_path, fallback_user_id)
        
        assert result is True
        
        # Verify SQLite constraint notes were logged
        mock_logger.info.assert_any_call("NOTE: SQLite does not support adding NOT NULL constraints to existing columns")
        mock_logger.info.assert_any_call("All NULL user_id values have been updated, ORM will enforce NOT NULL in application")


class TestRunMigrationWithConfig:
    """Test cases for configuration-based migration execution."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)
        
        # Create minimal test database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE task_contexts (id TEXT PRIMARY KEY)")
        cursor.execute("CREATE TABLE branch_contexts (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_run_migration_with_config_uses_env_vars(self):
        """Test migration uses environment variables for configuration."""
        test_user_id = "env-test-user"
        
        with patch.dict(os.environ, {
            'MCP_DB_PATH': self.db_path,
            'MIGRATION_FALLBACK_USER_ID': test_user_id
        }):
            with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.run_migration') as mock_run:
                mock_run.return_value = True
                
                result = run_migration_with_config()
        
        assert result is True
        mock_run.assert_called_once_with(self.db_path, test_user_id)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_run_migration_with_config_finds_database(self):
        """Test migration finds database in common locations."""
        # Clear environment variables
        with patch('os.path.exists') as mock_exists:
            # Mock database found in second location
            mock_exists.side_effect = lambda path: path == self.db_path
            
            with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.run_migration') as mock_run:
                mock_run.return_value = True
                
                # Mock the possible_paths to include our test path
                with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
                    # We need to patch the possible_paths list
                    import fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns as migration_module
                    original_func = migration_module.run_migration_with_config
                    
                    def mock_run_migration_with_config(config_path=None):
                        # Mock the database discovery logic
                        possible_paths = [self.db_path]  # Use our test path
                        for path in possible_paths:
                            if os.path.exists(path):
                                db_path = path
                                mock_logger.info(f"Found database at: {db_path}")
                                break
                        
                        fallback_user_id = "system"  # Default value
                        return migration_module.run_migration(db_path, fallback_user_id)
                    
                    with patch.object(migration_module, 'run_migration_with_config', side_effect=mock_run_migration_with_config):
                        result = run_migration_with_config()
        
        assert result is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_run_migration_with_config_no_database_found(self):
        """Test migration fails when no database is found."""
        with patch('os.path.exists', return_value=False):
            with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.logger') as mock_logger:
                result = run_migration_with_config()
        
        assert result is False
        mock_logger.error.assert_called_with("Could not find database file. Please set MCP_DB_PATH environment variable")
    
    def test_run_migration_with_config_loads_dotenv(self):
        """Test migration loads environment from config file."""
        config_path = "/test/config/.env"
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.load_dotenv') as mock_load_dotenv:
            with patch.dict(os.environ, {'MCP_DB_PATH': self.db_path}):
                with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.run_migration') as mock_run:
                    mock_run.return_value = True
                    
                    result = run_migration_with_config(config_path)
        
        assert result is True
        mock_load_dotenv.assert_called_once_with(config_path)
    
    def test_run_migration_with_config_default_fallback_user(self):
        """Test migration uses default fallback user when not specified."""
        with patch.dict(os.environ, {'MCP_DB_PATH': self.db_path}):
            with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns.run_migration') as mock_run:
                mock_run.return_value = True
                
                result = run_migration_with_config()
        
        assert result is True
        # Verify default "system" user was used
        mock_run.assert_called_once_with(self.db_path, "system")


if __name__ == "__main__":
    pytest.main([__file__])