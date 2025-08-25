#!/usr/bin/env python3
"""
Debug test runner to isolate and understand the test failure.
"""

# MUST set test mode FIRST before any other imports
import os
import sys

# Set test mode environment variables FIRST
os.environ['PYTEST_CURRENT_TEST'] = 'debug_test_runner.py::test_debug'
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


def test_simple_facade_creation():
    """Simple test to verify facade creation works."""
    print("=== DEBUG: Testing facade creation ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        print(f"✓ Factory created: {type(factory)}")
        
        user_id = str(uuid.uuid4())
        print(f"✓ User ID generated: {user_id}")
        
        facade = factory.create_facade(user_id=user_id)
        print(f"✓ Facade created: {type(facade)}")
        
        return True
    except Exception as e:
        print(f"✗ Error creating facade: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_context_creation():
    """Simple test to verify context creation works."""
    print("=== DEBUG: Testing context creation ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        user_id = str(uuid.uuid4())
        facade = factory.create_facade(user_id=user_id)
        
        global_id = f"{GLOBAL_SINGLETON_UUID}_{user_id}"
        print(f"✓ Global ID: {global_id}")
        
        result = facade.create_context(
            level="global",
            context_id=global_id,
            data={
                "global_settings": {
                    "autonomous_rules": {"test_rule": "value1"},
                    "security_policies": {"test_policy": "enabled"}
                }
            }
        )
        
        print(f"✓ Create result: {result}")
        print(f"✓ Success: {result.get('success')}")
        
        if result.get('context'):
            print(f"✓ Context keys: {list(result['context'].keys())}")
            print(f"✓ Context data: {result['context']}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"✗ Error creating context: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """Test database connection directly."""
    print("=== DEBUG: Testing database connection ===")
    
    try:
        db_config = get_db_config()
        print(f"✓ DB config created: {type(db_config)}")
        print(f"✓ DB type: {db_config.database_type}")
        
        with db_config.get_session() as session:
            print(f"✓ Session created: {type(session)}")
            
        return True
        
    except Exception as e:
        print(f"✗ Error with database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐞 Debug Test Runner - Investigating test failures")
    print("=" * 60)
    
    success_count = 0
    
    if test_database_connection():
        success_count += 1
        print("✓ Database connection test PASSED\n")
    else:
        print("✗ Database connection test FAILED\n")
    
    if test_simple_facade_creation():
        success_count += 1
        print("✓ Facade creation test PASSED\n")
    else:
        print("✗ Facade creation test FAILED\n")
        
    if test_simple_context_creation():
        success_count += 1
        print("✓ Context creation test PASSED\n")
    else:
        print("✗ Context creation test FAILED\n")
    
    print("=" * 60)
    print(f"🏁 Results: {success_count}/3 tests passed")
    
    if success_count == 3:
        print("✅ All basic functionality working - issue might be in test logic")
    else:
        print("❌ Basic functionality issues detected")