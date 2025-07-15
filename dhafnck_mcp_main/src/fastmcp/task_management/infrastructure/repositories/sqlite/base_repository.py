"""Base SQLite Repository Implementation

This module provides a base class for all SQLite repositories to eliminate code duplication
and standardize common patterns like database connection management, initialization, and logging.
"""

import sqlite3
import logging
import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

# Removed problematic tool_path import
from ...database.database_source_manager import get_database_path, get_database_info
from ...database.database_initializer import initialize_database
from ...database.connection_pool import get_connection_pool
from ....interface.utils.error_handler import UserFriendlyErrorHandler

logger = logging.getLogger(__name__)


class SQLiteBaseRepository:
    """Base class for SQLite repositories providing common functionality"""
    
    def __init__(self, db_path: Optional[str] = None, use_pool: bool = True):
        """
        Initialize SQLite repository with standardized setup
        
        Args:
            db_path: Path to SQLite database file (optional)
            use_pool: Whether to use connection pooling (default: True)
        """
        # Resolve database path using centralized logic
        self._db_path = self._resolve_database_path(db_path)
        
        # Disable connection pooling for temporary test databases to ensure isolation
        if db_path and self._is_temporary_test_db(db_path):
            use_pool = False
            logger.info(f"{self.__class__.__name__} disabling connection pool for temporary test database")
        
        # Log repository initialization
        self._log_repository_info()
        
        # Initialize database
        self._initialize_database()
        
        # Setup connection pool if enabled
        self._use_pool = use_pool
        if self._use_pool:
            self._connection_pool = get_connection_pool(self._db_path)
            logger.info(f"{self.__class__.__name__} using connection pool")
    
    def _resolve_database_path(self, db_path: Optional[str]) -> str:
        """Resolve database path using standardized logic"""
        if db_path:
            # Handle special in-memory database
            if db_path == ":memory:":
                return db_path
            # If explicit path provided, use it (for testing/override)
            elif Path(db_path).is_absolute():
                return str(db_path)
            else:
                # Use relative to current working directory
                return str(Path(db_path).resolve())
        else:
            # Use database source manager to determine correct database
            return get_database_path()
    
    def _is_temporary_test_db(self, db_path: str) -> bool:
        """Check if the database path is a temporary test database"""
        db_path_str = str(db_path)
        # Check for common temporary file patterns used in tests
        return (
            db_path_str == ":memory:" or
            "/tmp/" in db_path_str or 
            "temp" in db_path_str.lower() or
            db_path_str.startswith(tempfile.gettempdir())
        )
    
    def _log_repository_info(self):
        """Log repository initialization info in standardized format"""
        db_info = get_database_info()
        repository_name = self.__class__.__name__
        
        logger.info(f"{repository_name} using db_path: {self._db_path}")
        logger.info(f"Database mode: {db_info['mode']}, is_test: {db_info['is_test']}")
    
    def _initialize_database(self):
        """Initialize database using the central initializer"""
        try:
            # The central initializer is idempotent and thread-safe
            initialize_database(self._db_path)
        except Exception as e:
            logger.critical(
                f"Failed to initialize database via central initializer: {e}", 
                exc_info=True
            )
            raise
    
    def _get_connection(self):
        """Get database connection with row factory for dict-like access"""
        if self._use_pool:
            # Use connection pool (returns context manager)
            return self._connection_pool.get_connection()
        else:
            # Traditional approach (for backward compatibility)
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False):
        """
        Execute query with standardized error handling
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: If True, return single row; if False, return all rows
            
        Returns:
            Query results or None
        """
        try:
            if self._use_pool:
                # Connection pool returns a context manager
                with self._get_connection() as conn:
                    cursor = conn.execute(query, params)
                    if fetch_one:
                        return cursor.fetchone()
                    else:
                        return cursor.fetchall()
            else:
                # Traditional approach
                with self._get_connection() as conn:
                    cursor = conn.execute(query, params)
                    if fetch_one:
                        return cursor.fetchone()
                    else:
                        return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database query failed: {query[:100]}... Error: {e}")
            # Convert SQLite error to user-friendly error
            error_response = UserFriendlyErrorHandler.handle_error(e, "database query", {"query_type": "SELECT"})
            raise sqlite3.Error(error_response["error"])
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise
    
    def _execute_insert(self, query: str, params: tuple = ()) -> str:
        """
        Execute INSERT query and return last row id
        
        Args:
            query: INSERT SQL query
            params: Query parameters
            
        Returns:
            Last inserted row id
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Database insert failed: {query[:100]}... Error: {e}")
            error_response = UserFriendlyErrorHandler.handle_error(e, "database insert", {"query_type": "INSERT"})
            raise sqlite3.Error(error_response["error"])
        except Exception as e:
            logger.error(f"Unexpected error executing insert: {e}")
            raise
    
    def _execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute UPDATE/DELETE query and return affected row count
        
        Args:
            query: UPDATE/DELETE SQL query
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Database update failed: {query[:100]}... Error: {e}")
            error_response = UserFriendlyErrorHandler.handle_error(e, "database update", {"query_type": "UPDATE/DELETE"})
            raise sqlite3.Error(error_response["error"])
        except Exception as e:
            logger.error(f"Unexpected error executing update: {e}")
            raise
    
    
    def _ensure_database_exists(self):
        """Ensure database file exists (utility method for subclasses)"""
        if not os.path.exists(self._db_path):
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            
            # Create empty database
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("SELECT 1")  # Create empty database
            
            logger.info(f"Created new database at {self._db_path}")