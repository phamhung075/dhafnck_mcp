"""
Centralized Database Initializer for DhafnckMCP

This module provides a single point of truth for initializing the SQLite database,
ensuring that all required schemas (project, task, context, etc.) are created
consistently.
"""

import sqlite3
import os
import logging

# Removed problematic tool_path import

logger = logging.getLogger(__name__)

# Use a lock to prevent race conditions during initialization
# Although tests run sequentially, this is good practice for future concurrency
import threading
db_init_lock = threading.Lock()

# Keep track of initialized databases to avoid redundant IO
_initialized_dbs = set()


def _find_project_root() -> str:
    """Find project root by looking for dhafnck_mcp_main directory"""
    import os
    
    # Primary approach - use the directory containing dhafnck_mcp_main
    # This is the most reliable when we're inside the dhafnck_mcp_main directory
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
    return "/home/daihungpham/agentic-project"

def initialize_database(db_path: str):
    """
    Initializes the database at the given path with all required schemas.
    This function is idempotent and thread-safe.

    Args:
        db_path: The absolute path to the SQLite database file.
    """
    global _initialized_dbs
    
    # If this specific DB path has been initialized in this session, skip
    if db_path in _initialized_dbs:
        return

    with db_init_lock:
        # Double-check after acquiring the lock
        if db_path in _initialized_dbs:
            return
            
        logger.info(f"Initializing database at {db_path}...")
        try:
            # Ensure the directory for the database file exists (skip for in-memory databases)
            if db_path != ":memory:" and os.path.dirname(db_path):
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Connect to the database (this will create the file if it doesn't exist)
            with sqlite3.connect(db_path) as conn:
                # Start with foreign keys disabled to avoid issues during initialization
                conn.execute("PRAGMA foreign_keys = OFF")
                project_root = _find_project_root()
                
                # Modernized schema structure v6.0 - Single execution order
                # All tables, relationships, and dependencies are properly defined in order
                schema_files = [
                    "00_base_schema.sql",           # All core tables and relationships
                    "01_agent_coordination_fix.sql", # Fix agent coordination tables
                    "01_indexes_triggers.sql",      # Performance indexes and triggers
                    "02_views_statistics.sql",      # Views and analytics
                    "03_initial_data.sql"           # Default data and configuration
                ]
                
                # Execute schema files in order
                for schema_file in schema_files:
                    schema_path = os.path.join(project_root, "dhafnck_mcp_main", "database", "schema", schema_file)
                    if os.path.exists(schema_path):
                        try:
                            with open(schema_path, 'r', encoding='utf-8') as f:
                                schema_sql = f.read()
                            logger.info(f"Executing modernized schema: {schema_file}")
                            
                            # Execute the schema
                            conn.executescript(schema_sql)
                            
                            # Verify critical tables after base schema
                            if schema_file == "00_base_schema.sql":
                                cursor = conn.cursor()
                                
                                # Verify core tables exist
                                critical_tables = [
                                    'projects', 'project_task_trees', 'tasks', 'task_subtasks', 'task_assignees',
                                    'project_agents', 'labels', 'task_labels', 
                                    'global_contexts', 'project_contexts', 'task_contexts',
                                    'templates', 'checklists'
                                ]
                                
                                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({','.join(['?' for _ in critical_tables])})", critical_tables)
                                tables_created = [row[0] for row in cursor.fetchall()]
                                
                                missing_tables = set(critical_tables) - set(tables_created)
                                if missing_tables:
                                    raise Exception(f"Critical tables not created! Missing: {missing_tables}")
                                logger.info(f"Verified {len(tables_created)} critical tables created successfully")
                            
                            logger.info(f"Successfully executed modernized schema: {schema_file}")
                        except Exception as e:
                            logger.error(f"Error executing modernized schema {schema_file}: {e}")
                            raise
                    else:
                        logger.warning(f"Modernized schema file not found, skipping: {schema_path}")
                        
                # Note: Initial data is now included in 03_initial_data.sql
                
                # Final verification - ensure all critical systems are operational
                cursor = conn.cursor()
                
                # Verify comprehensive table structure
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                all_tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Database initialized with {len(all_tables)} tables: {', '.join(all_tables)}")
                
                
                # Verify default data
                cursor.execute("SELECT COUNT(*) FROM global_contexts")
                global_context_count = cursor.fetchone()[0]
                if global_context_count == 0:
                    logger.warning("No global context found - initial data may not have loaded properly")
                else:
                    logger.info(f"Global context initialized successfully ({global_context_count} record(s))")
                
                cursor.execute("SELECT COUNT(*) FROM projects WHERE id = 'default_project'")
                default_project_count = cursor.fetchone()[0]
                if default_project_count == 0:
                    logger.warning("Default project not found - initial data may not have loaded properly")
                else:
                    logger.info("Default project initialized successfully")
                
                conn.commit()
                
                # Re-enable foreign keys after all initialization is complete
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
            
            # Mark this database as initialized for this session
            _initialized_dbs.add(db_path)
            logger.info(f"Database {db_path} initialized successfully.")

        except sqlite3.Error as e:
            logger.critical(f"A critical SQLite error occurred during database initialization: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.critical(f"An unexpected critical error occurred during database initialization: {e}", exc_info=True)
            raise

def clear_initialized_cache():
    """Clears the cache of initialized databases. Mainly for testing purposes."""
    global _initialized_dbs
    with db_init_lock:
        _initialized_dbs.clear()
    logger.info("Initialized database cache cleared.")

def force_reinitialize_database(db_path: str):
    """Force reinitialize database even if already marked as initialized."""
    global _initialized_dbs
    with db_init_lock:
        _initialized_dbs.discard(db_path)
    initialize_database(db_path) 