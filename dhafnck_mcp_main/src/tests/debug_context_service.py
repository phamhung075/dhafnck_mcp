#!/usr/bin/env python3
"""
Debug UnifiedContextService to understand why get_context fails after create_context.
"""

# MUST set test mode FIRST before any other imports
import os
import sys

# Set test mode environment variables FIRST
os.environ['PYTEST_CURRENT_TEST'] = 'debug_context_service.py::test_debug'
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
from sqlalchemy import text


def test_service_layer():
    """Test the unified context service directly."""
    print("=== DEBUG: Testing UnifiedContextService directly ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        user_id = str(uuid.uuid4())
        
        # Get the service directly
        service = factory.create_unified_service()
        scoped_service = service.with_user(user_id)
        
        global_id = f"{GLOBAL_SINGLETON_UUID}_{user_id}"
        print(f"✓ User ID: {user_id}")
        print(f"✓ Global ID: {global_id}")
        
        # Test create in service
        print("\n1. CREATING context in service...")
        create_result = scoped_service.create_context(
            level="global",
            context_id=global_id,
            data={
                "global_settings": {
                    "autonomous_rules": {"test_rule": "value1"},
                    "security_policies": {"test_policy": "enabled"}
                }
            },
            user_id=user_id
        )
        
        print(f"✓ Service create result: {create_result}")
        
        if not create_result.get('success'):
            print(f"❌ Service create failed: {create_result.get('error')}")
            return False
        
        # Test get in service
        print("\n2. GETTING context from service...")
        get_result = scoped_service.get_context(
            level="global",
            context_id=global_id
        )
        
        print(f"✓ Service get result: {get_result}")
        
        if not get_result.get('success'):
            print(f"❌ Service get failed: {get_result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error in service layer test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_repository_layer():
    """Test the repository layer directly."""
    print("=== DEBUG: Testing repository layer directly ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        user_id = str(uuid.uuid4())
        
        # Get the global context repository directly
        service = factory.create_unified_service()
        global_repo = service.repositories[ContextLevel.GLOBAL]
        
        print(f"✓ User ID: {user_id}")
        print(f"✓ Global repo: {type(global_repo)}")
        
        # Create a context directly in the repository
        print("\n1. CREATING context in repository...")
        
        # Import the model
        from fastmcp.task_management.infrastructure.database.models import GlobalContext
        
        global_context = GlobalContext(
            id=str(uuid.uuid4()),
            user_id=user_id,
            autonomous_rules={"test": "value"},
            security_policies={},
            coding_standards={},
            workflow_templates={},
            delegation_rules={}
        )
        
        # Use repository to save
        global_repo_scoped = global_repo.with_user(user_id)
        saved_context = global_repo_scoped.create(global_context)
        print(f"✓ Repository save result: {saved_context}")
        print(f"✓ Saved context ID: {saved_context.id}")
        
        # Try to get it back
        print("\n2. GETTING context from repository...")
        retrieved_context = global_repo_scoped.get(saved_context.id)
        
        if retrieved_context:
            print(f"✓ Repository get result: {retrieved_context}")
            print(f"✓ Retrieved context ID: {retrieved_context.id}")
            return True
        else:
            print("❌ Repository get returned None")
            return False
        
    except Exception as e:
        print(f"✗ Error in repository layer test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_after_operations():
    """Check what's actually in the database after operations."""
    print("=== DEBUG: Testing database state after operations ===")
    
    try:
        db_config = get_db_config()
        
        with db_config.get_session() as session:
            # Check all global contexts
            result = session.execute(text("SELECT id, user_id, autonomous_rules FROM global_contexts ORDER BY created_at DESC LIMIT 10"))
            rows = result.fetchall()
            print(f"✓ Recent global contexts ({len(rows)} found):")
            for row in rows:
                print(f"    id={row[0]}, user_id={row[1]}, rules={row[2]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐞 Debug UnifiedContextService - Service vs Repository layer investigation")
    print("=" * 80)
    
    success_count = 0
    
    if test_repository_layer():
        success_count += 1
        print("✓ Repository layer test PASSED\n")
    else:
        print("✗ Repository layer test FAILED\n")
    
    if test_service_layer():
        success_count += 1
        print("✓ Service layer test PASSED\n")
    else:
        print("✗ Service layer test FAILED\n")
    
    if test_database_after_operations():
        success_count += 1
        print("✓ Database check PASSED\n")
    else:
        print("✗ Database check FAILED\n")
    
    print("=" * 80)
    print(f"🏁 Results: {success_count}/3 tests passed")
    
    if success_count == 3:
        print("✅ Context service working correctly")
    else:
        print("❌ Context service issues detected")