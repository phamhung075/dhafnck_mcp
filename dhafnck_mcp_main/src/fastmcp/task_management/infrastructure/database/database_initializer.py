"""
Centralized Database Initializer for DhafnckMCP

This module provides a single point of truth for initializing the database,
ensuring that all required schemas are created consistently.
Now uses SQLAlchemy ORM to support both SQLite and PostgreSQL.
"""

import os
import logging
import threading
from pathlib import Path
from typing import Optional

from .database_config import get_db_config
from .init_database import init_database as sqlalchemy_init_database

logger = logging.getLogger(__name__)

# Use a lock to prevent race conditions during initialization
db_init_lock = threading.Lock()

# Keep track of initialized databases to avoid redundant IO
_initialized_dbs = set()


def _find_project_root() -> str:
    """Find project root by looking for dhafnck_mcp_main directory"""
    # Primary approach - use the directory containing dhafnck_mcp_main
    current_path = os.path.abspath(__file__)
    while os.path.dirname(current_path) != current_path:
        if os.path.basename(current_path) == "dhafnck_mcp_main":
            return os.path.dirname(current_path)
        current_path = os.path.dirname(current_path)
    
    # Fallback 1: Walk up the directory tree looking for dhafnck_mcp_main as a subdirectory
    current_path = os.path.abspath(__file__)
    while os.path.dirname(current_path) != current_path:
        if os.path.exists(os.path.join(current_path, "dhafnck_mcp_main")):
            return current_path
        current_path = os.path.dirname(current_path)
    
    # Fallback 2: use current working directory if it contains dhafnck_mcp_main
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "dhafnck_mcp_main")):
        return cwd
    
    # Absolute fallback
    # Use environment variable or default data path
    data_path = os.environ.get('DHAFNCK_DATA_PATH', '/data')
    # If running in development, try to find project root
    if not os.path.exists(data_path):
        # Try current working directory
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "dhafnck_mcp_main")):
            return cwd
        # Fall back to temp directory for safety
        return "/tmp/dhafnck_project"
    return data_path


def initialize_database(db_path: Optional[str] = None):
    """
    Initialize the database with all required schemas.
    
    This function now uses SQLAlchemy ORM to create tables,
    supporting both SQLite and PostgreSQL based on DATABASE_TYPE.
    
    Args:
        db_path: Optional database path (for backward compatibility with SQLite)
                 Ignored when using PostgreSQL.
    """
    database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    # For PostgreSQL, we don't need db_path as it uses DATABASE_URL
    if database_type == "postgresql":
        db_identifier = "postgresql"
    else:
        # For SQLite, use provided path or default
        if not db_path:
            from .database_source_manager import DatabaseSourceManager
            manager = DatabaseSourceManager()
            db_path = manager.get_database_path()
        db_identifier = os.path.abspath(db_path)
    
    # Skip if already initialized (thread-safe check)
    with db_init_lock:
        if db_identifier in _initialized_dbs:
            logger.debug(f"Database already initialized: {db_identifier}")
            return
        
        logger.info(f"Initializing database: {db_identifier}")
        
        try:
            # Use SQLAlchemy to initialize database
            sqlalchemy_init_database()
            
            # Mark as initialized
            _initialized_dbs.add(db_identifier)
            logger.info(f"Database initialized successfully: {db_identifier}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise


def reset_initialization_cache():
    """Reset the initialization cache - useful for testing"""
    global _initialized_dbs
    _initialized_dbs = set()


# Backward compatibility function
def get_schema_path() -> str:
    """
    Get the path to the schema file.
    
    This function is kept for backward compatibility but is no longer used
    when using SQLAlchemy ORM.
    """
    project_root = _find_project_root()
    schema_path = os.path.join(project_root, "dhafnck_mcp_main", "database", "schema", "00_base_schema.sql")
    
    if not os.path.exists(schema_path):
        # Try alternative path
        alt_path = os.path.join(project_root, "database", "schema", "00_base_schema.sql")
        if os.path.exists(alt_path):
            schema_path = alt_path
        else:
            raise FileNotFoundError(f"Schema file not found at {schema_path} or {alt_path}")
    
    return schema_path