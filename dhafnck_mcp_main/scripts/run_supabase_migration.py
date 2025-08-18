#!/usr/bin/env python3
"""
Supabase Database Migration Runner

This script connects to Supabase and runs the authentication migration
to create the users table and related schema.
"""

import os
import sys
import logging
import psycopg2
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables."""
    # Try direct DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # If not found, construct from individual components
    host = os.getenv("DATABASE_HOST")
    port = os.getenv("DATABASE_PORT", "5432")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    dbname = os.getenv("DATABASE_NAME", "postgres")
    
    if host and user and password:
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
    
    return None

def load_migration_sql():
    """Load the authentication migration SQL."""
    script_dir = Path(__file__).parent
    migration_file = script_dir.parent / "database" / "migrations" / "002_add_authentication_tables.sql"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return None
    
    with open(migration_file, 'r') as f:
        return f.read()

def run_migration():
    """Connect to Supabase and run the authentication migration."""
    database_url = get_database_url()
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    logger.info(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Load migration SQL
        migration_sql = load_migration_sql()
        if not migration_sql:
            return False
        
        logger.info("Running authentication migration...")
        
        # Execute migration
        cursor.execute(migration_sql)
        
        logger.info("✅ Migration completed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'user_sessions', 'auth_audit_log')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        logger.info(f"✅ Created tables: {[table[0] for table in tables]}")
        
        # Check users table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        logger.info(f"✅ Users table has {len(columns)} columns")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Supabase Authentication Migration")
    
    success = run_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        logger.info("🔧 User registration should now work properly")
        sys.exit(0)
    else:
        logger.error("💥 Migration failed!")
        sys.exit(1)