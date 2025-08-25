#!/usr/bin/env python3
"""
Debug context retrieval issue - isolate create vs get problem.
"""

# MUST set test mode FIRST before any other imports
import os
import sys

# Set test mode environment variables FIRST
os.environ['PYTEST_CURRENT_TEST'] = 'debug_context_retrieval.py::test_debug'
os.environ['DATABASE_TYPE'] = 'sqlite'

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import uuid
from datetime import datetime, timezone

# Import pytest to simulate test environment
sys.modules['pytest'] = pytest

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.infrastructure.database.models import GLOBAL_SINGLETON_UUID
from fastmcp.task_management.infrastructure.database.database_config import get_db_config


def test_create_then_get():
    """Test create context followed by get context to isolate the issue."""
    print("=== DEBUG: Testing create then get ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        user_id = str(uuid.uuid4())
        facade = factory.create_facade(user_id=user_id)
        
        global_id = f"{GLOBAL_SINGLETON_UUID}_{user_id}"
        print(f"✓ Global ID: {global_id}")
        print(f"✓ User ID: {user_id}")
        
        # CREATE
        print("\n1. CREATING context...")
        create_result = facade.create_context(
            level="global",
            context_id=global_id,
            data={
                "global_settings": {
                    "autonomous_rules": {"test_rule": "value1"},
                    "security_policies": {"test_policy": "enabled"}
                }
            }
        )
        
        print(f"✓ Create result success: {create_result.get('success')}")
        print(f"✓ Create result keys: {list(create_result.keys())}")
        if create_result.get('context'):
            print(f"✓ Created context ID: {create_result['context'].get('id')}")
        
        # GET - immediately after create
        print("\n2. GETTING context immediately after create...")
        get_result = facade.get_context(
            level="global",
            context_id=global_id
        )
        
        print(f"✓ Get result success: {get_result.get('success')}")
        print(f"✓ Get result keys: {list(get_result.keys())}")
        print(f"✓ Get result: {get_result}")
        
        if not get_result.get('success'):
            print(f"❌ Get failed! Error: {get_result.get('error')}")
        
        # Try getting with a different facade instance for the same user
        print("\n3. TESTING with new facade instance for same user...")
        new_facade = factory.create_facade(user_id=user_id)
        get_result2 = new_facade.get_context(
            level="global",
            context_id=global_id
        )
        
        print(f"✓ Get result2 success: {get_result2.get('success')}")
        print(f"✓ Get result2: {get_result2}")
        
        # Try getting with a different user (should fail)
        print("\n4. TESTING with different user (should fail)...")
        different_user = str(uuid.uuid4())
        different_facade = factory.create_facade(user_id=different_user)
        get_result3 = different_facade.get_context(
            level="global",
            context_id=global_id
        )
        
        print(f"✓ Get result3 success (should be False): {get_result3.get('success')}")
        print(f"✓ Get result3: {get_result3}")
        
        return create_result.get('success', False) and get_result.get('success', False)
        
    except Exception as e:
        print(f"✗ Error in create_then_get: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_state():
    """Check what's actually in the database."""
    print("=== DEBUG: Testing database state ===")
    
    try:
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Check global contexts table
            from fastmcp.task_management.infrastructure.database.models import GlobalContext
            
            global_contexts = session.query(GlobalContext).all()
            print(f"✓ Total global contexts in DB: {len(global_contexts)}")
            
            for ctx in global_contexts:
                print(f"  - ID: {ctx.id}")
                print(f"    Context ID: {ctx.context_id}")
                print(f"    User ID: {ctx.user_id}")
                print(f"    Organization: {getattr(ctx, 'organization_name', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking database state: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐞 Debug Context Retrieval - Isolating create vs get issue")
    print("=" * 70)
    
    success_count = 0
    
    if test_database_state():
        success_count += 1
        print("✓ Database state check PASSED\n")
    else:
        print("✗ Database state check FAILED\n")
    
    if test_create_then_get():
        success_count += 1
        print("✓ Create-then-get test PASSED\n")
    else:
        print("✗ Create-then-get test FAILED\n")
    
    print("=" * 70)
    print(f"🏁 Results: {success_count}/2 tests passed")
    
    if success_count == 2:
        print("✅ Context retrieval working correctly")
    else:
        print("❌ Context retrieval issues detected")