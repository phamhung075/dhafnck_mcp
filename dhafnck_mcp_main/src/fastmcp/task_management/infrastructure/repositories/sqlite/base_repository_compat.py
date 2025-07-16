"""
SQLite Base Repository Compatibility Layer

This module provides a compatibility layer that bridges SQLite repositories
with SQLAlchemy ORM, allowing gradual migration while maintaining backward compatibility.
"""

import sqlite3
import logging
import os
import tempfile
from typing import Optional, Dict, Any, Union
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import text

# Import existing functionality
from ...database.database_source_manager import get_database_path, get_database_info
from ...database.database_initializer import initialize_database
from ...database.session_manager import get_session_manager
from ....interface.utils.error_handler import UserFriendlyErrorHandler
from ....domain.exceptions.base_exceptions import DatabaseException

logger = logging.getLogger(__name__)


class SQLiteBaseRepositoryCompat:
    """
    Compatibility layer for SQLite repositories.
    
    This class provides the same interface as SQLiteBaseRepository but uses
    SQLAlchemy sessions under the hood. It supports both new ORM operations
    and legacy raw SQL queries.
    """
    
    def __init__(self, db_path: Optional[str] = None, use_pool: bool = True):
        """
        Initialize SQLite repository with SQLAlchemy backend
        
        Args:
            db_path: Path to SQLite database file (for compatibility)
            use_pool: Whether to use connection pooling (now uses SQLAlchemy sessions)
        """
        # Resolve database path using centralized logic
        self._db_path = self._resolve_database_path(db_path)
        
        # Log repository initialization
        self._log_repository_info()
        
        # Initialize database
        self._initialize_database()
        
        # Get session manager
        self._session_manager = get_session_manager()
        
        # Legacy compatibility flag
        self._use_pool = use_pool
        if self._use_pool:
            logger.info(f"{self.__class__.__name__} using SQLAlchemy session manager")
    
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
    
    @contextmanager
    def _get_connection(self):
        """
        Get database connection - now returns SQLAlchemy session
        
        This method maintains compatibility with the old interface
        while using SQLAlchemy sessions underneath.
        """
        with self._session_manager.get_session() as session:
            yield SQLAlchemyConnectionWrapper(session)
    
    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False):
        """
        Execute query with standardized error handling using SQLAlchemy
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: If True, return single row; if False, return all rows
            
        Returns:
            Query results or None
        """
        try:
            with self._session_manager.get_session() as session:
                # Convert tuple params to dict for SQLAlchemy
                if params:
                    # Handle both positional and named parameters
                    if isinstance(params, (list, tuple)):
                        # Convert positional parameters to named
                        param_dict = {f"param_{i}": val for i, val in enumerate(params)}
                        # Replace ? with :param_n for SQLAlchemy
                        sql_query = query
                        for i in range(len(params)):
                            sql_query = sql_query.replace("?", f":param_{i}", 1)
                    else:
                        param_dict = params
                        sql_query = query
                else:
                    param_dict = {}
                    sql_query = query
                
                result = session.execute(text(sql_query), param_dict)
                
                if fetch_one:
                    row = result.fetchone()
                    return SQLiteRowCompat(row) if row else None
                else:
                    rows = result.fetchall()
                    return [SQLiteRowCompat(row) for row in rows]
                    
        except SQLAlchemyError as e:
            logger.error(f"Database query failed: {query[:100]}... Error: {e}")
            # Convert SQLAlchemy error to user-friendly error
            error_response = UserFriendlyErrorHandler.handle_error(
                e, "database query", {"query_type": "SELECT"}
            )
            raise DatabaseException(
                message=error_response["error"],
                operation="query",
                table="unknown"
            )
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise
    
    def _execute_insert(self, query: str, params: tuple = ()) -> str:
        """
        Execute INSERT query and return last row id using SQLAlchemy
        
        Args:
            query: INSERT SQL query
            params: Query parameters
            
        Returns:
            Last inserted row id
        """
        try:
            with self._session_manager.get_session() as session:
                # Convert parameters for SQLAlchemy
                if params:
                    param_dict = {f"param_{i}": val for i, val in enumerate(params)}
                    sql_query = query
                    for i in range(len(params)):
                        sql_query = sql_query.replace("?", f":param_{i}", 1)
                else:
                    param_dict = {}
                    sql_query = query
                
                result = session.execute(text(sql_query), param_dict)
                session.commit()
                
                # Return last inserted ID
                return result.lastrowid or result.inserted_primary_key[0]
                
        except SQLAlchemyError as e:
            logger.error(f"Database insert failed: {query[:100]}... Error: {e}")
            error_response = UserFriendlyErrorHandler.handle_error(
                e, "database insert", {"query_type": "INSERT"}
            )
            raise DatabaseException(
                message=error_response["error"],
                operation="insert",
                table="unknown"
            )
        except Exception as e:
            logger.error(f"Unexpected error executing insert: {e}")
            raise
    
    def _execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute UPDATE/DELETE query and return affected row count using SQLAlchemy
        
        Args:
            query: UPDATE/DELETE SQL query
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self._session_manager.get_session() as session:
                # Convert parameters for SQLAlchemy
                if params:
                    param_dict = {f"param_{i}": val for i, val in enumerate(params)}
                    sql_query = query
                    for i in range(len(params)):
                        sql_query = sql_query.replace("?", f":param_{i}", 1)
                else:
                    param_dict = {}
                    sql_query = query
                
                result = session.execute(text(sql_query), param_dict)
                session.commit()
                return result.rowcount
                
        except SQLAlchemyError as e:
            logger.error(f"Database update failed: {query[:100]}... Error: {e}")
            error_response = UserFriendlyErrorHandler.handle_error(
                e, "database update", {"query_type": "UPDATE/DELETE"}
            )
            raise DatabaseException(
                message=error_response["error"],
                operation="update",
                table="unknown"
            )
        except Exception as e:
            logger.error(f"Unexpected error executing update: {e}")
            raise
    
    def _ensure_database_exists(self):
        """Ensure database file exists (utility method for subclasses)"""
        if self._db_path != ":memory:" and not os.path.exists(self._db_path):
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            logger.info(f"Created database directory for {self._db_path}")


class SQLiteRowCompat:
    """
    Compatibility wrapper for SQLite Row objects.
    
    Provides both dict-like and list-like access to row data from SQLAlchemy result rows.
    Supports both column name access (row['column_name']) and numeric indexing (row[0]).
    """
    
    def __init__(self, row):
        """Initialize with SQLAlchemy result row"""
        self._row = row
        self._data = dict(row._mapping) if row else {}
        # Store values as list for numeric indexing
        self._values = list(row) if row else []
    
    def __getitem__(self, key):
        """Get item by key (dict-like access) or index (list-like access)"""
        if isinstance(key, int):
            # Numeric indexing - return value by position
            return self._values[key] if key < len(self._values) else None
        else:
            # String key - return value by column name
            return self._data[key]
    
    def __contains__(self, key):
        """Check if key exists"""
        return key in self._data
    
    def get(self, key, default=None):
        """Get item with default"""
        return self._data.get(key, default)
    
    def keys(self):
        """Get keys"""
        return self._data.keys()
    
    def values(self):
        """Get values"""
        return self._data.values()
    
    def items(self):
        """Get items"""
        return self._data.items()
    
    def __iter__(self):
        """Iterate over keys"""
        return iter(self._data)
    
    def __len__(self):
        """Get number of columns"""
        return len(self._data)


class SQLAlchemyConnectionWrapper:
    """
    Wrapper to make SQLAlchemy session look like sqlite3 connection.
    
    This provides compatibility for code that expects sqlite3.Connection interface.
    """
    
    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session"""
        self.session = session
        self.row_factory = SQLiteRowCompat  # Default row factory
    
    def execute(self, query: str, params=()):
        """Execute query and return cursor-like object"""
        try:
            # Convert parameters for SQLAlchemy
            if params:
                if isinstance(params, (list, tuple)):
                    param_dict = {f"param_{i}": val for i, val in enumerate(params)}
                    sql_query = query
                    for i in range(len(params)):
                        sql_query = sql_query.replace("?", f":param_{i}", 1)
                else:
                    param_dict = params
                    sql_query = query
            else:
                param_dict = {}
                sql_query = query
            
            result = self.session.execute(text(sql_query), param_dict)
            return SQLAlchemyCursorWrapper(result, self.row_factory)
            
        except SQLAlchemyError as e:
            # Convert to sqlite3-like error for compatibility
            raise sqlite3.Error(str(e))
    
    def commit(self):
        """Commit transaction"""
        self.session.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.session.rollback()
    
    def close(self):
        """Close session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()


class SQLAlchemyCursorWrapper:
    """
    Wrapper to make SQLAlchemy result look like sqlite3 cursor.
    """
    
    def __init__(self, result, row_factory=None):
        """Initialize with SQLAlchemy result"""
        self._result = result
        self._row_factory = row_factory or SQLiteRowCompat
        self._lastrowid = getattr(result, 'lastrowid', None)
        self._rowcount = getattr(result, 'rowcount', -1)
    
    @property
    def lastrowid(self):
        """Get last row ID"""
        return self._lastrowid
    
    @property
    def rowcount(self):
        """Get row count"""
        return self._rowcount
    
    def fetchone(self):
        """Fetch one row"""
        try:
            row = self._result.fetchone()
            return self._row_factory(row) if row else None
        except Exception:
            return None
    
    def fetchall(self):
        """Fetch all rows"""
        try:
            rows = self._result.fetchall()
            return [self._row_factory(row) for row in rows]
        except Exception:
            return []
    
    def fetchmany(self, size=None):
        """Fetch many rows"""
        try:
            rows = self._result.fetchmany(size) if size else self._result.fetchmany()
            return [self._row_factory(row) for row in rows]
        except Exception:
            return []