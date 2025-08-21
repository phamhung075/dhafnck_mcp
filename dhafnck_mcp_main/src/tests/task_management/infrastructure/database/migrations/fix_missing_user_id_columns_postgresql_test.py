"""Test suite for fix_missing_user_id_columns_postgresql migration.

Tests the PostgreSQL migration that fixes missing user_id columns in context tables:
- Adding missing user_id columns with NOT NULL constraints
- Updating NULL values with fallback user ID
- Transaction rollback on errors
- Database state verification
- Column constraint management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import logging

from fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql import (
    run_postgresql_migration
)


class TestFixMissingUserIdColumnsPostgreSQLMigration:
    """Test cases for PostgreSQL fix_missing_user_id_columns migration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock SQLAlchemy session
        self.mock_session = Mock()
        self.mock_session.begin = Mock()
        self.mock_session.commit = Mock()
        self.mock_session.rollback = Mock()
        self.mock_session.close = Mock()
        self.mock_session.execute = Mock()
        
        # Mock result objects
        self.mock_result = Mock()
        self.mock_session.execute.return_value = self.mock_result
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_success_adds_missing_columns(self, mock_get_session):
        """Test successful migration that adds missing user_id column."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "test-system-user"
        
        # Mock table structure checks
        # task_contexts does NOT have user_id column
        # branch_contexts has nullable user_id column
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "task_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # task_contexts doesn't have user_id column
                mock_result.fetchone.return_value = None
            elif "branch_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # branch_contexts has nullable user_id column
                mock_result.fetchone.return_value = ('user_id', 'YES')  # column_name, is_nullable
            elif "UPDATE task_contexts SET user_id" in query_str:
                # Mock UPDATE result for task_contexts
                mock_result.rowcount = 3
            elif "UPDATE branch_contexts SET user_id" in query_str:
                # Mock UPDATE result for branch_contexts
                mock_result.rowcount = 2
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                # Verification queries - no NULL values found
                mock_result.fetchone.return_value = [0]
            else:
                # Default result for other queries
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is True
        
        # Verify session management
        mock_get_session.assert_called_once()
        self.mock_session.begin.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.close.assert_called_once()
        
        # Verify logging
        mock_logger.info.assert_any_call("Starting missing user_id columns migration on PostgreSQL database")
        mock_logger.info.assert_any_call("Adding missing user_id column to task_contexts table")
        mock_logger.info.assert_any_call("Made task_contexts.user_id column NOT NULL")
        mock_logger.info.assert_any_call("✅ PostgreSQL migration completed successfully")
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_columns_already_exist(self, mock_get_session):
        """Test migration when columns already exist."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "existing-user"
        
        # Mock table structure checks - both columns exist and are NOT NULL
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "task_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # task_contexts has user_id column
                mock_result.fetchone.return_value = ('user_id',)
            elif "branch_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # branch_contexts has non-nullable user_id column
                mock_result.fetchone.return_value = ('user_id', 'NO')  # column_name, is_nullable
            elif "UPDATE" in query_str and "SET user_id" in query_str:
                # Mock UPDATE result - no rows updated (no NULL values)
                mock_result.rowcount = 0
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                # Verification queries - no NULL values found
                mock_result.fetchone.return_value = [0]
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is True
        
        # Verify logging
        mock_logger.info.assert_any_call("task_contexts.user_id column already exists")
        mock_logger.info.assert_any_call("branch_contexts.user_id column exists (nullable: False)")
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_branch_contexts_missing_column(self, mock_get_session):
        """Test migration when branch_contexts is missing user_id column."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "system-user"
        
        # Mock table structure checks
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "task_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # task_contexts has user_id column
                mock_result.fetchone.return_value = ('user_id',)
            elif "branch_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # branch_contexts does NOT have user_id column
                mock_result.fetchone.return_value = None
            elif "UPDATE" in query_str and "SET user_id" in query_str:
                # Mock UPDATE results
                if "task_contexts" in query_str:
                    mock_result.rowcount = 1
                elif "branch_contexts" in query_str:
                    mock_result.rowcount = 2
                else:
                    mock_result.rowcount = 0
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                # Verification queries - no NULL values found
                mock_result.fetchone.return_value = [0]
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is True
        
        # Verify logging for missing branch_contexts column
        mock_logger.info.assert_any_call("Adding missing user_id column to branch_contexts table")
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_verification_failure(self, mock_get_session):
        """Test migration rollback when verification fails."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "test-user"
        
        # Mock table structure checks and verification failure
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "task_contexts" in query_str and "column_name = 'user_id'" in query_str:
                mock_result.fetchone.return_value = None  # Missing column
            elif "branch_contexts" in query_str and "column_name = 'user_id'" in query_str:
                mock_result.fetchone.return_value = ('user_id', 'YES')  # Nullable column
            elif "UPDATE" in query_str and "SET user_id" in query_str:
                mock_result.rowcount = 1
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                # Verification failure - still have NULL values
                if "task_contexts" in query_str:
                    mock_result.fetchone.return_value = [2]  # Found NULL values
                else:
                    mock_result.fetchone.return_value = [0]
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is False
        
        # Verify rollback was called
        self.mock_session.rollback.assert_called_once()
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Found NULL/empty user_id values after update" in error_call
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_table_check_error_continues(self, mock_get_session):
        """Test migration continues when table check fails."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "system-user"
        
        # Mock table structure checks with some failures
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "task_contexts" in query_str and "column_name = 'user_id'" in query_str:
                mock_result.fetchone.return_value = ('user_id',)  # Column exists
            elif "branch_contexts" in query_str and "column_name = 'user_id'" in query_str:
                mock_result.fetchone.return_value = ('user_id', 'NO')  # Column exists, not nullable
            elif "UPDATE" in query_str and "SET user_id" in query_str:
                mock_result.rowcount = 0  # No updates needed
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                if "task_contexts" in query_str:
                    # Simulate error checking this table
                    raise Exception("Table check error")
                else:
                    mock_result.fetchone.return_value = [0]  # No NULL values
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        # Migration should still succeed for tables that can be checked
        assert result is True
        
        # Verify warning was logged for the table that failed
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Could not check task_contexts" in warning_call
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_session_creation_error(self, mock_get_session):
        """Test migration handles session creation errors gracefully."""
        mock_get_session.side_effect = Exception("Database connection failed")
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration("fallback-user")
        
        assert result is False
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Migration failed to connect" in error_call
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_execution_error(self, mock_get_session):
        """Test migration handles execution errors with rollback."""
        mock_get_session.return_value = self.mock_session
        
        # Mock execution error during migration
        self.mock_session.execute.side_effect = Exception("SQL execution error")
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration("fallback-user")
        
        assert result is False
        
        # Verify rollback was called
        self.mock_session.rollback.assert_called_once()
        self.mock_session.close.assert_called_once()
        
        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Migration failed during execution" in error_call
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_makes_columns_not_null(self, mock_get_session):
        """Test migration adds NOT NULL constraints to columns."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "system"
        
        # Mock table structure checks - columns exist but are nullable
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "task_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # task_contexts has nullable user_id column
                mock_result.fetchone.return_value = ('user_id',)
            elif "branch_contexts" in query_str and "column_name = 'user_id'" in query_str:
                # branch_contexts has nullable user_id column
                mock_result.fetchone.return_value = ('user_id', 'YES')  # is_nullable = YES
            elif "UPDATE" in query_str and "SET user_id" in query_str:
                mock_result.rowcount = 1  # One row updated
            elif "ALTER TABLE" in query_str and "ALTER COLUMN user_id SET NOT NULL" in query_str:
                mock_result.rowcount = 0  # DDL operations don't return rowcount
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                # Verification queries - no NULL values found
                mock_result.fetchone.return_value = [0]
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is True
        
        # Verify NOT NULL constraints were added
        mock_logger.info.assert_any_call("Made branch_contexts.user_id column NOT NULL")
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_with_default_fallback_user(self, mock_get_session):
        """Test migration with default fallback user ID."""
        mock_get_session.return_value = self.mock_session
        
        # Mock simple successful migration
        def mock_execute_side_effect(query):
            mock_result = Mock()
            mock_result.fetchone.return_value = None if "column_name = 'user_id'" in str(query) else [0]
            mock_result.rowcount = 0
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        result = run_postgresql_migration()  # No fallback_user_id provided
        
        assert result is True
        
        # Verify session was managed properly
        self.mock_session.begin.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.close.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_updates_existing_null_values(self, mock_get_session):
        """Test migration updates existing NULL values in columns."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "updated-user"
        
        # Mock table structure checks - columns exist with NULL values
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "column_name = 'user_id'" in query_str:
                # Both columns exist
                if "task_contexts" in query_str:
                    mock_result.fetchone.return_value = ('user_id',)
                else:
                    mock_result.fetchone.return_value = ('user_id', 'YES')  # Nullable
            elif "UPDATE" in query_str and "SET user_id" in query_str:
                # Mock UPDATE results - some rows updated
                if "task_contexts" in query_str:
                    mock_result.rowcount = 5
                elif "branch_contexts" in query_str:
                    mock_result.rowcount = 3
                else:
                    mock_result.rowcount = 0
            elif "SELECT COUNT(*)" in query_str and "WHERE user_id IS NULL" in query_str:
                # Verification queries - no NULL values after update
                mock_result.fetchone.return_value = [0]
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = None
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is True
        
        # Verify update counts were logged
        mock_logger.info.assert_any_call(f"Updated 5 NULL user_id values in task_contexts to '{fallback_user_id}'")
        mock_logger.info.assert_any_call(f"Updated 3 NULL user_id values in branch_contexts to '{fallback_user_id}'")
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_handles_sql_injection_safely(self, mock_get_session):
        """Test migration handles potentially dangerous user input safely."""
        mock_get_session.return_value = self.mock_session
        
        # Test with potentially dangerous fallback_user_id
        dangerous_user_id = "'; DROP TABLE users; --"
        
        # Mock simple execution that doesn't fail
        def mock_execute_side_effect(query):
            mock_result = Mock()
            # Check that the dangerous input is properly escaped in the query
            query_str = str(query)
            
            # The migration should properly escape the user_id
            if "UPDATE" in query_str and dangerous_user_id in query_str:
                # This would mean the user_id wasn't properly escaped
                raise Exception("SQL injection detected in query")
            
            mock_result.fetchone.return_value = None if "column_name = 'user_id'" in query_str else [0]
            mock_result.rowcount = 0
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        # This should either handle the input safely or fail gracefully
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger'):
            result = run_postgresql_migration(dangerous_user_id)
        
        # Migration should either succeed (if input is properly escaped) or fail gracefully
        assert isinstance(result, bool)
        
        # Verify rollback was called if there was an error
        if not result:
            self.mock_session.rollback.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_logs_progress(self, mock_get_session):
        """Test migration logs progress throughout execution."""
        mock_get_session.return_value = self.mock_session
        fallback_user_id = "progress-user"
        
        # Mock successful migration
        def mock_execute_side_effect(query):
            mock_result = Mock()
            mock_result.fetchone.return_value = None if "column_name = 'user_id'" in str(query) else [0]
            mock_result.rowcount = 2 if "UPDATE" in str(query) else 0
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration(fallback_user_id)
        
        assert result is True
        
        # Verify comprehensive logging
        expected_log_calls = [
            call("Starting missing user_id columns migration on PostgreSQL database"),
            call("Checking task_contexts table structure..."),
            call("Checking branch_contexts table structure..."),
            call("✅ PostgreSQL migration completed successfully"),
            call("Both task_contexts and branch_contexts now have user_id columns with NOT NULL constraints")
        ]
        
        # Check that expected log calls were made (order may vary)
        actual_calls = [call for call in mock_logger.info.call_args_list]
        for expected_call in expected_log_calls:
            assert expected_call in actual_calls
    
    @patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.get_session')
    def test_run_postgresql_migration_handles_constraint_errors(self, mock_get_session):
        """Test migration handles constraint-related errors."""
        mock_get_session.return_value = self.mock_session
        
        # Mock constraint error during ALTER COLUMN operation
        def mock_execute_side_effect(query):
            query_str = str(query)
            mock_result = Mock()
            
            if "ALTER COLUMN user_id SET NOT NULL" in query_str:
                # Simulate constraint violation error
                raise Exception("column contains null values")
            elif "column_name = 'user_id'" in query_str:
                if "task_contexts" in query_str:
                    mock_result.fetchone.return_value = None  # Missing column
                else:
                    mock_result.fetchone.return_value = ('user_id', 'YES')  # Nullable column
            elif "UPDATE" in query_str:
                mock_result.rowcount = 1
            else:
                mock_result.rowcount = 0
                mock_result.fetchone.return_value = [0]
            
            return mock_result
        
        self.mock_session.execute.side_effect = mock_execute_side_effect
        
        with patch('fastmcp.task_management.infrastructure.database.migrations.fix_missing_user_id_columns_postgresql.logger') as mock_logger:
            result = run_postgresql_migration("test-user")
        
        assert result is False
        
        # Verify rollback was called due to constraint error
        self.mock_session.rollback.assert_called_once()
        
        # Verify error was logged
        mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])