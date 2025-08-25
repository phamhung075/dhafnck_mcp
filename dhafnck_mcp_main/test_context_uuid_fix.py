#!/usr/bin/env python3
"""
Debug test for context UUID issue with user isolation.
"""

import uuid
import logging
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Test database imports
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.database.models import (
    GLOBAL_SINGLETON_UUID,
    GlobalContext as GlobalContextModel
)
from fastmcp.task_management.infrastructure.repositories.global_context_repository import GlobalContextRepository
from fastmcp.task_management.domain.entities.context import GlobalContext

def test_direct_db_insert():
    """Test direct database insertion to isolate the issue."""
    print("\n=== Testing Direct Database Insert ===")
    
    db_config = get_db_config()
    user_id = str(uuid.uuid4())
    
    with db_config.get_session() as session:
        try:
            # Create a global context model directly
            db_model = GlobalContextModel(
                id=GLOBAL_SINGLETON_UUID,
                organization_id="00000000-0000-0000-0000-000000000002",
                autonomous_rules={"test": "rule"},
                security_policies={"test": "policy"},
                coding_standards={},
                workflow_templates={},
                delegation_rules={},
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            print(f"Created model with ID type: {type(db_model.id)}, value: {db_model.id}")
            
            session.add(db_model)
            session.flush()
            
            print("✅ Flush successful")
            
            # This is where the error occurs
            session.refresh(db_model)
            
            print("✅ Refresh successful")
            session.commit()
            
            print(f"✅ Successfully created GlobalContext with ID: {db_model.id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()

def test_repository_create():
    """Test repository create method."""
    print("\n=== Testing Repository Create ===")
    
    db_config = get_db_config()
    user_id = str(uuid.uuid4())
    
    # Create repository with user_id
    repo = GlobalContextRepository(db_config.SessionLocal, user_id=user_id)
    
    # Create entity
    entity = GlobalContext(
        id=GLOBAL_SINGLETON_UUID,
        organization_name="Test Organization",
        global_settings={
            "autonomous_rules": {"test": "rule"},
            "security_policies": {"test": "policy"}
        },
        metadata={"version": 1}
    )
    
    try:
        result = repo.create(entity)
        print(f"✅ Successfully created GlobalContext: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_uuid_field_type():
    """Test the UUID field type handling."""
    print("\n=== Testing UUID Field Type ===")
    
    db_config = get_db_config()
    
    with db_config.get_session() as session:
        # Check if we can query by UUID string
        result = session.query(GlobalContextModel).filter(
            GlobalContextModel.id == GLOBAL_SINGLETON_UUID
        ).first()
        
        if result:
            print(f"Found existing context with ID: {result.id} (type: {type(result.id)})")
        else:
            print("No existing global context found")
        
        # Test what SQLAlchemy does with the UUID
        from sqlalchemy import inspect
        mapper = inspect(GlobalContextModel)
        id_column = mapper.columns['id']
        print(f"Column type: {id_column.type}")
        print(f"Column python type: {id_column.type.python_type if hasattr(id_column.type, 'python_type') else 'N/A'}")

if __name__ == "__main__":
    print("Starting context UUID fix tests...")
    
    # Test UUID field handling
    test_uuid_field_type()
    
    # Test direct DB insert
    test_direct_db_insert()
    
    # Test repository create
    test_repository_create()
    
    print("\n✅ All tests completed!")