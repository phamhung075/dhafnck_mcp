#!/usr/bin/env python3
"""
Simple test for context CRUD with user isolation.
"""

import os
import sys
import uuid
from pathlib import Path

# Set up environment for test mode
os.environ['MCP_DB_PATH'] = './test_simple.db'
os.environ['PYTHONPATH'] = 'src'
os.environ['PYTEST_CURRENT_TEST'] = 'test_simple_context.py::test'  # Force test mode
sys.path.insert(0, 'src')

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.infrastructure.database.models import GLOBAL_SINGLETON_UUID

def test_simple_global_context():
    """Test basic global context creation with user isolation."""
    print("\n=== Testing Simple Global Context ===")
    
    # Create factory
    factory = UnifiedContextFacadeFactory()
    
    # Create user 1
    user_id_1 = str(uuid.uuid4())
    print(f"User 1 ID: {user_id_1}")
    
    # Create facade for user 1
    facade_user1 = factory.create_facade(user_id=user_id_1)
    
    # Create global context for user 1
    context_id_1 = str(uuid.uuid4())  # Use a fresh UUID
    print(f"Creating global context with ID: {context_id_1}")
    
    result1 = facade_user1.create_context(
        level="global",
        context_id=context_id_1,
        data={
            "global_settings": {
                "autonomous_rules": {"user1_rule": "value1"},
                "security_policies": {"user1_policy": "policy1"}
            }
        }
    )
    
    print(f"Create result success: {result1.get('success')}")
    if not result1.get('success'):
        print(f"Error: {result1.get('error')}")
        return False
    
    print(f"Created context ID: {result1.get('context', {}).get('id')}")
    
    # Check the structure
    if result1.get('context'):
        global_settings = result1['context'].get('global_settings', {})
        print(f"Global settings keys: {global_settings.keys()}")
        print(f"Autonomous rules: {global_settings.get('autonomous_rules')}")
        
        # Verify data
        if global_settings.get('autonomous_rules', {}).get('user1_rule') == 'value1':
            print("✅ Data correctly stored and retrieved!")
            return True
        else:
            print("❌ Data not correctly stored")
            return False
    
    return False

def test_user_isolation():
    """Test that different users have isolated contexts."""
    print("\n=== Testing User Isolation ===")
    
    # Create factory
    factory = UnifiedContextFacadeFactory()
    
    # Create two users
    user_id_1 = str(uuid.uuid4())
    user_id_2 = str(uuid.uuid4())
    print(f"User 1 ID: {user_id_1}")
    print(f"User 2 ID: {user_id_2}")
    
    # Create facades
    facade_user1 = factory.create_facade(user_id=user_id_1)
    facade_user2 = factory.create_facade(user_id=user_id_2)
    
    # Create contexts with different IDs for each user
    context_id_1 = str(uuid.uuid4())
    context_id_2 = str(uuid.uuid4())
    
    # Create global context for user 1
    result1 = facade_user1.create_context(
        level="global",
        context_id=context_id_1,
        data={
            "global_settings": {
                "autonomous_rules": {"user1_rule": "value1"}
            }
        }
    )
    
    if not result1.get('success'):
        print(f"Failed to create context for user 1: {result1.get('error')}")
        return False
    
    # Create global context for user 2
    result2 = facade_user2.create_context(
        level="global",
        context_id=context_id_2,
        data={
            "global_settings": {
                "autonomous_rules": {"user2_rule": "value2"}
            }
        }
    )
    
    if not result2.get('success'):
        print(f"Failed to create context for user 2: {result2.get('error')}")
        return False
    
    print("✅ Both users successfully created their own contexts")
    
    # Try to access each other's contexts
    # User 1 tries to get user 2's context
    cross_result1 = facade_user1.get_context(
        level="global",
        context_id=context_id_2
    )
    
    # User 2 tries to get user 1's context
    cross_result2 = facade_user2.get_context(
        level="global",
        context_id=context_id_1
    )
    
    # Check isolation
    if cross_result1.get('success') and cross_result1.get('context'):
        print("❌ User 1 can see User 2's context - isolation failed!")
        return False
    
    if cross_result2.get('success') and cross_result2.get('context'):
        print("❌ User 2 can see User 1's context - isolation failed!")
        return False
    
    print("✅ Users cannot access each other's contexts - isolation working!")
    return True

if __name__ == "__main__":
    print("Starting simple context tests...")
    
    # Test basic creation
    success1 = test_simple_global_context()
    
    # Test user isolation
    success2 = test_user_isolation()
    
    if success1 and success2:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")