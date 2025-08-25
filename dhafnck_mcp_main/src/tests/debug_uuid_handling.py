#!/usr/bin/env python3
"""
Debug UUID handling issue with SQLite.
"""

# MUST set test mode FIRST before any other imports
import os
import sys

# Set test mode environment variables FIRST
os.environ['PYTEST_CURRENT_TEST'] = 'debug_uuid_handling.py::test_debug'
os.environ['DATABASE_TYPE'] = 'sqlite'

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import uuid

# Import pytest to simulate test environment
sys.modules['pytest'] = pytest

from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.database.models import GlobalContext
from sqlalchemy import text


def test_direct_database_operations():
    """Test direct database operations to isolate UUID issues."""
    print("=== DEBUG: Testing direct database operations ===")
    
    try:
        db_config = get_db_config()
        test_user_id = str(uuid.uuid4())
        test_context_id = str(uuid.uuid4())
        
        print(f"✓ User ID: {test_user_id}")
        print(f"✓ Context ID: {test_context_id}")
        
        # Test direct insertion
        print("\n1. Testing direct insertion...")
        with db_config.get_session() as session:
            global_context = GlobalContext(
                id=test_context_id,
                user_id=test_user_id,
                autonomous_rules={"test": "value"},
                security_policies={},
                coding_standards={},
                workflow_templates={},
                delegation_rules={}
            )
            
            session.add(global_context)
            session.commit()
            print("✓ Context inserted successfully")
            
            # Get the ID back to see what was actually stored
            stored_id = global_context.id
            print(f"✓ Stored ID: {stored_id} (type: {type(stored_id)})")
        
        # Test retrieval without any UUID processing
        print("\n2. Testing direct retrieval...")
        with db_config.get_session() as session:
            # Use raw SQL to see what's actually in the database
            result = session.execute(text("SELECT id, user_id FROM global_contexts WHERE user_id = :user_id"), 
                                    {"user_id": test_user_id})
            row = result.fetchone()
            if row:
                print(f"✓ Raw SQL result: id={row[0]} (type: {type(row[0])}), user_id={row[1]}")
            else:
                print("❌ No rows found with raw SQL")
        
        # Test ORM retrieval 
        print("\n3. Testing ORM retrieval...")
        with db_config.get_session() as session:
            try:
                # Try to get without triggering UUID processing
                context = session.query(GlobalContext).filter_by(user_id=test_user_id).first()
                if context:
                    print(f"✓ ORM retrieval successful: id={context.id}")
                    return True
                else:
                    print("❌ ORM retrieval found no results")
                    return False
            except Exception as e:
                print(f"❌ ORM retrieval failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"✗ Error in direct database operations: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sqlite_uuid_storage():
    """Check how SQLite actually stores UUID values."""
    print("=== DEBUG: Testing SQLite UUID storage ===")
    
    try:
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Check the schema
            result = session.execute(text("PRAGMA table_info(global_contexts)"))
            columns = result.fetchall()
            print("✓ Global contexts table schema:")
            for col in columns:
                print(f"    {col[1]} {col[2]} {'(PK)' if col[5] else ''}")
            
            # Check existing data
            result = session.execute(text("SELECT COUNT(*) FROM global_contexts"))
            count = result.scalar()
            print(f"✓ Total records in global_contexts: {count}")
            
            if count > 0:
                result = session.execute(text("SELECT id, user_id, typeof(id), typeof(user_id) FROM global_contexts LIMIT 5"))
                rows = result.fetchall()
                print("✓ Sample data with types:")
                for row in rows:
                    print(f"    id={row[0]} ({row[2]}), user_id={row[1]} ({row[3]})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking SQLite UUID storage: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐞 Debug UUID Handling - SQLite UUID storage and processing")
    print("=" * 70)
    
    success_count = 0
    
    if test_sqlite_uuid_storage():
        success_count += 1
        print("✓ SQLite UUID storage check PASSED\n")
    else:
        print("✗ SQLite UUID storage check FAILED\n")
    
    if test_direct_database_operations():
        success_count += 1
        print("✓ Direct database operations PASSED\n")
    else:
        print("✗ Direct database operations FAILED\n")
    
    print("=" * 70)
    print(f"🏁 Results: {success_count}/2 tests passed")
    
    if success_count == 2:
        print("✅ UUID handling working correctly")
    else:
        print("❌ UUID handling issues detected")