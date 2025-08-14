#!/usr/bin/env python3
"""
Initialize test database with unified context schema.
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

# Set test environment
os.environ["PYTEST_CURRENT_TEST"] = "init_test_db.py::init_test_database"

from fastmcp.task_management.infrastructure.database.database_config import get_db_config, Base
# Import all models to register them with Base
from fastmcp.task_management.infrastructure.database import models

def init_test_database():
    print("🚀 Initializing test database with unified context schema...")
    
    # Get database configuration
    db_config = get_db_config()
    
    print(f"📍 Database engine: {db_config.engine}")
    
    # Create all tables
    Base.metadata.create_all(bind=db_config.engine)
    
    print("✅ Database schema created successfully!")
    
    # Verify tables exist using inspector
    from sqlalchemy import inspect
    inspector = inspect(db_config.engine)
    table_names = inspector.get_table_names()
    print(f"📋 Created tables: {table_names}")

if __name__ == "__main__":
    init_test_database()