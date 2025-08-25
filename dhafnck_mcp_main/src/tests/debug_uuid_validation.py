#!/usr/bin/env python3
"""
Debug UUID validation logic in the repository.
"""

# MUST set test mode FIRST before any other imports
import os
import sys

# Set test mode environment variables FIRST
os.environ['PYTEST_CURRENT_TEST'] = 'debug_uuid_validation.py::test_debug'
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
from fastmcp.task_management.domain.entities.context import GlobalContext


def test_uuid_validation():
    """Test the UUID validation logic in the repository."""
    print("=== DEBUG: Testing UUID Validation Logic ===")
    
    try:
        factory = UnifiedContextFacadeFactory()
        user_id = str(uuid.uuid4())
        
        # Get the repository directly
        service = factory.create_unified_service()
        global_repo = service.repositories["global"]
        
        # Test the _is_valid_uuid method directly
        test_context_id = f"{GLOBAL_SINGLETON_UUID}_{user_id}"
        
        print(f"✓ User ID: {user_id}")
        print(f"✓ Test context ID: {test_context_id}")
        print(f"✓ Is valid UUID: {global_repo._is_valid_uuid(test_context_id)}")
        print(f"✓ Is valid context ID: {global_repo._is_valid_context_id(test_context_id)}")
        
        # Test individual components
        print(f"✓ GLOBAL_SINGLETON_UUID: {GLOBAL_SINGLETON_UUID}")
        print(f"✓ Is GLOBAL_SINGLETON_UUID valid: {global_repo._is_valid_uuid(GLOBAL_SINGLETON_UUID)}")
        print(f"✓ Is user_id valid: {global_repo._is_valid_uuid(user_id)}")
        
        # Test some known good and bad UUIDs
        good_uuid = str(uuid.uuid4())
        bad_uuid = "not-a-uuid"
        
        print(f"✓ Good UUID {good_uuid}: {global_repo._is_valid_uuid(good_uuid)}")
        print(f"✓ Bad UUID {bad_uuid}: {global_repo._is_valid_uuid(bad_uuid)}")
        
        # Now test what happens when we create an entity
        print(f"\n2. Creating GlobalContext entity...")
        entity = GlobalContext(
            id=test_context_id,
            organization_name="Test Organization",
            global_settings={
                "autonomous_rules": {"test": "value"},
                "security_policies": {},
                "coding_standards": {},
                "workflow_templates": {},
                "delegation_rules": {}
            },
            metadata={}
        )
        
        print(f"✓ Entity created with ID: {entity.id}")
        print(f"✓ Entity ID is valid UUID: {global_repo._is_valid_uuid(entity.id)}")
        print(f"✓ Entity ID is valid context ID: {global_repo._is_valid_context_id(entity.id)}")
        
        # Test the repository create method step by step
        print(f"\n3. Testing repository create logic...")
        
        # Simulate the UUID validation logic (updated)
        if entity.id and global_repo._is_valid_context_id(entity.id):
            context_id = entity.id
            print(f"✓ Using entity.id as context_id: {context_id}")
        else:
            context_id = str(uuid.uuid4())
            print(f"✓ Generated new context_id: {context_id}")
        
        print(f"✓ Final context_id: {context_id}")
        print(f"✓ Matches original: {context_id == test_context_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in UUID validation test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐞 Debug UUID Validation - Repository UUID validation logic")
    print("=" * 70)
    
    if test_uuid_validation():
        print("✅ UUID validation test completed")
    else:
        print("❌ UUID validation test failed")