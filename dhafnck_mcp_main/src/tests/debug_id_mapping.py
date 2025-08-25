#!/usr/bin/env python3
"""
Debug ID mapping issue - track IDs through the entire create/get process.
"""

# MUST set test mode FIRST before any other imports
import os
import sys

# Set test mode environment variables FIRST
os.environ['PYTEST_CURRENT_TEST'] = 'debug_id_mapping.py::test_debug'
os.environ['DATABASE_TYPE'] = 'sqlite'

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import uuid

# Import pytest to simulate test environment
sys.modules['pytest'] = pytest

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.infrastructure.database.models import GLOBAL_SINGLETON_UUID
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel
from fastmcp.task_management.domain.entities.context import GlobalContext
from sqlalchemy import text


def test_id_tracking():
    """Track IDs through the entire create/get process."""
    print("=== DEBUG: ID Tracking Through Create/Get Process ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        user_id = str(uuid.uuid4())
        
        # Generate IDs we'll track
        original_context_id = f"{GLOBAL_SINGLETON_UUID}_{user_id}"
        
        print(f"✓ User ID: {user_id}")
        print(f"✓ Original Context ID: {original_context_id}")
        
        # Step 1: Create through facade
        facade = factory.create_facade(user_id=user_id)
        
        print(f"\n1. FACADE CREATE - Input context_id: {original_context_id}")
        create_result = facade.create_context(
            level="global",
            context_id=original_context_id,
            data={
                "global_settings": {
                    "autonomous_rules": {"test_rule": "value1"},
                    "security_policies": {"test_policy": "enabled"}
                }
            }
        )
        
        if create_result.get('success'):
            returned_context = create_result.get('context', {})
            returned_id = returned_context.get('id')
            returned_context_id = create_result.get('context_id')
            
            print(f"✓ Facade create SUCCESS")
            print(f"✓ Returned context.id: {returned_id}")
            print(f"✓ Returned context_id: {returned_context_id}")
            print(f"✓ ID Match: {returned_context_id == original_context_id}")
        else:
            print(f"❌ Facade create FAILED: {create_result.get('error')}")
            return False
        
        # Step 2: Check database directly
        print(f"\n2. DATABASE CHECK - Looking for context_id: {original_context_id}")
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Check what's actually in the database - search more broadly
            result = session.execute(text("""
                SELECT id, user_id, autonomous_rules, 
                       typeof(id) as id_type, length(id) as id_length
                FROM global_contexts 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            
            all_rows = result.fetchall()
            print(f"✓ All recent records ({len(all_rows)} found):")
            matching_row = None
            for i, row in enumerate(all_rows):
                db_id = row[0]
                db_user_id = row[1]
                db_rules = row[2]
                db_id_type = row[3]
                db_id_length = row[4]
                
                print(f"  {i+1}. ID: {db_id} (type: {db_id_type}, length: {db_id_length})")
                print(f"      User ID: {db_user_id}")
                print(f"      Rules: {db_rules}")
                
                if str(db_user_id) == str(user_id):
                    matching_row = row
                    print(f"      *** MATCH for user {user_id} ***")
            
            # Now check specifically for our user
            result2 = session.execute(text("""
                SELECT id, user_id, autonomous_rules, 
                       typeof(id) as id_type, length(id) as id_length
                FROM global_contexts 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT 1
            """), {"user_id": user_id})
            
            row = result2.fetchone()
            
            if row:
                db_id = row[0]
                db_user_id = row[1]
                db_rules = row[2]
                db_id_type = row[3]
                db_id_length = row[4]
                
                print(f"✓ Database record found:")
                print(f"  - ID: {db_id} (type: {db_id_type}, length: {db_id_length})")
                print(f"  - User ID: {db_user_id}")
                print(f"  - Rules: {db_rules}")
                
                # Compare IDs
                print(f"✓ ID Comparison:")
                print(f"  - Original: {original_context_id}")
                print(f"  - Database: {db_id}")
                print(f"  - Match: {str(db_id) == original_context_id}")
                
                # Check if it's a UUID formatting issue
                import re
                def normalize_uuid(uuid_str):
                    """Remove hyphens from UUID string."""
                    return re.sub(r'-', '', str(uuid_str))
                
                normalized_original = normalize_uuid(original_context_id)
                normalized_db = normalize_uuid(db_id)
                
                print(f"  - Normalized Original: {normalized_original}")
                print(f"  - Normalized Database: {normalized_db}")
                print(f"  - Normalized Match: {normalized_original == normalized_db}")
                
            else:
                print("❌ No database record found")
                return False
        
        # Step 3: Try facade get
        print(f"\n3. FACADE GET - Looking for context_id: {original_context_id}")
        get_result = facade.get_context(
            level="global",
            context_id=original_context_id
        )
        
        if get_result.get('success'):
            get_context = get_result.get('context', {})
            get_id = get_context.get('id')
            print(f"✓ Facade get SUCCESS")
            print(f"✓ Retrieved context.id: {get_id}")
        else:
            print(f"❌ Facade get FAILED: {get_result.get('error')}")
            
            # Try with the database ID instead
            print(f"\n3b. FACADE GET RETRY - Using database ID: {db_id}")
            get_result2 = facade.get_context(
                level="global", 
                context_id=str(db_id)
            )
            
            if get_result2.get('success'):
                print(f"✓ Facade get with DB ID SUCCESS")
                return True
            else:
                print(f"❌ Facade get with DB ID FAILED: {get_result2.get('error')}")
                return False
        
        return get_result.get('success', False)
        
    except Exception as e:
        print(f"✗ Error in ID tracking test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐞 Debug ID Mapping - Track IDs through create/get process")
    print("=" * 80)
    
    if test_id_tracking():
        print("✅ ID tracking test completed successfully")
    else:
        print("❌ ID tracking test failed")