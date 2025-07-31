#!/usr/bin/env python3
"""
Database Initialization Script for Docker Container
Ensures all required tables and schema are properly created.
"""

import sqlite3
import logging
import os
from pathlib import Path

def initialize_database():
    """Initialize database with complete schema"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Database path (in Docker container)
    db_path = os.getenv("MCP_DB_PATH", "/data/dhafnck_mcp.db")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Schema files path (in Docker container, or override with env var)
    schema_base_path = os.getenv("SCHEMA_BASE_PATH", "/app/database/schema")
    
    logger.info(f"Initializing database at: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # List of schema files to execute in order (flat file structure)
        schema_files = [
            "00_base_schema.sql",           # Base schema with all tables
            "01_agent_coordination_fix.sql", # Agent coordination fixes
            "01_indexes_triggers.sql",      # Indexes and triggers
            "02_views_statistics.sql",      # Views and statistics
            "03_initial_data.sql"           # Initial data
        ]
        
        # Execute schemas in order
        for schema_file in schema_files:
            schema_path = f"{schema_base_path}/{schema_file}"
            if os.path.exists(schema_path):
                logger.info(f"Applying schema: {schema_file}")
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                # Execute each statement separately to handle any errors gracefully
                try:
                    conn.executescript(schema_sql)
                    logger.info(f"✅ Successfully applied: {schema_file}")
                except Exception as e:
                    logger.error(f"❌ Error applying {schema_file}: {e}")
                    # Continue with other files even if one fails
            else:
                logger.warning(f"Schema file not found, skipping: {schema_path}")
        
        conn.commit()
    
    # Verify tables were created
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Database initialized with {len(tables)} tables:")
        for table in tables:
            logger.info(f"  ✅ {table}")
        
        # Check for required tables (updated for hierarchical context system)
        required_tables = ['tasks', 'task_assignees', 'global_contexts', 'project_contexts', 'task_contexts', 'templates']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            logger.warning(f"Missing required tables: {missing_tables}")
        else:
            logger.info("✅ All required tables present")

if __name__ == "__main__":
    initialize_database()