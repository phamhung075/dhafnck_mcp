"""Base SQLite Repository Implementation

This module provides a base class for all SQLite repositories to eliminate code duplication
and standardize common patterns like database connection management, initialization, and logging.

MIGRATION NOTE: This class now uses SQLAlchemy compatibility layer.
Direct SQLite3 usage is being phased out in favor of SQLAlchemy ORM.
"""

import sqlite3
import logging
import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

# New SQLAlchemy compatibility imports
from .base_repository_compat import SQLiteBaseRepositoryCompat
from ...database.database_source_manager import get_database_path, get_database_info
from ...database.database_initializer import initialize_database
from ....interface.utils.error_handler import UserFriendlyErrorHandler

# Legacy imports for backward compatibility
try:
    from ...database.connection_pool import get_connection_pool
    LEGACY_POOL_AVAILABLE = True
except ImportError:
    LEGACY_POOL_AVAILABLE = False

logger = logging.getLogger(__name__)


class SQLiteBaseRepository(SQLiteBaseRepositoryCompat):
    """
    Base class for SQLite repositories providing common functionality.
    
    MIGRATION NOTE: Now inherits from SQLiteBaseRepositoryCompat which uses
    SQLAlchemy sessions instead of direct SQLite connections.
    """
    
    def __init__(self, db_path: Optional[str] = None, use_pool: bool = True):
        """
        Initialize SQLite repository with standardized setup
        
        Args:
            db_path: Path to SQLite database file (optional)
            use_pool: Whether to use connection pooling (now uses SQLAlchemy sessions)
        """
        # Use SQLAlchemy compatibility layer
        super().__init__(db_path=db_path, use_pool=use_pool)
        
        # Legacy support for connection pool
        if use_pool and LEGACY_POOL_AVAILABLE:
            try:
                self._legacy_connection_pool = get_connection_pool(self._db_path)
                logger.info(f"{self.__class__.__name__} legacy connection pool available as fallback")
            except Exception as e:
                logger.warning(f"Failed to create legacy connection pool: {e}")
                self._legacy_connection_pool = None
        else:
            self._legacy_connection_pool = None
    
    # Legacy method compatibility - these methods are now handled by the parent class
    # SQLiteBaseRepositoryCompat, but we keep them here for any direct calls
    
    def _get_connection(self):
        """Get database connection - now delegated to parent class"""
        return super()._get_connection()
    
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
    
    def get_legacy_connection_pool(self):
        """Get legacy connection pool if available (for backward compatibility)"""
        return getattr(self, '_legacy_connection_pool', None)