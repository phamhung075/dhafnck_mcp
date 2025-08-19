"""
Simple Integration Test for User Data Isolation

This test demonstrates the core user isolation functionality
without complex fixture dependencies.
"""

import pytest
import uuid
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import the components we're testing
from fastmcp.task_management.infrastructure.repositories.base_user_scoped_repository import (
    BaseUserScopedRepository
)


class TestSimpleUserIsolation:
    """Simple test to verify user isolation works"""
    
    def test_base_repository_user_filtering(self):
        """Test that BaseUserScopedRepository correctly filters by user"""
        
        # Create a mock session (not actually used in this simple test)
        session = None  # Would be a real SQLAlchemy session in production
        
        # Test 1: Repository with user ID filters correctly
        user1_id = str(uuid.uuid4())
        repo1 = BaseUserScopedRepository(session, user_id=user1_id)
        
        assert repo1.get_current_user_id() == user1_id
        assert not repo1.is_system_mode()
        
        filter_dict = repo1.get_user_filter()
        assert filter_dict == {"user_id": user1_id}
        
        # Test 2: Different user gets different filter
        user2_id = str(uuid.uuid4())
        repo2 = BaseUserScopedRepository(session, user_id=user2_id)
        
        assert repo2.get_current_user_id() == user2_id
        filter_dict2 = repo2.get_user_filter()
        assert filter_dict2 == {"user_id": user2_id}
        assert filter_dict != filter_dict2
        
        # Test 3: System mode has no filtering
        system_repo = BaseUserScopedRepository(session, user_id=None)
        
        assert system_repo.is_system_mode()
        assert system_repo.get_current_user_id() is None
        assert system_repo.get_user_filter() == {}
        
        # Test 4: with_user creates new scoped instance
        user3_id = str(uuid.uuid4())
        repo3 = repo1.with_user(user3_id)
        
        assert repo3.get_current_user_id() == user3_id
        assert repo1.get_current_user_id() == user1_id  # Original unchanged
        
        print("✅ All user isolation tests passed!")
    
    def test_data_preparation_with_user_id(self):
        """Test that user_id is correctly added to data"""
        
        session = None
        user_id = str(uuid.uuid4())
        repo = BaseUserScopedRepository(session, user_id=user_id)
        
        # Test data without user_id
        data = {
            "title": "Test Task",
            "description": "Test Description"
        }
        
        # Add user_id to data
        updated_data = repo.set_user_id(data.copy())
        
        assert updated_data["user_id"] == user_id
        assert updated_data["title"] == "Test Task"
        assert updated_data["description"] == "Test Description"
        
        # Test system mode doesn't add user_id
        system_repo = BaseUserScopedRepository(session, user_id=None)
        system_data = system_repo.set_user_id(data.copy())
        
        assert "user_id" not in system_data
        
        print("✅ Data preparation tests passed!")
    
    def test_ownership_validation(self):
        """Test that ownership validation works correctly"""
        
        session = None
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        repo = BaseUserScopedRepository(session, user_id=user_id)
        
        # Create mock entity with correct user_id
        class MockEntity:
            def __init__(self, uid):
                self.user_id = uid
        
        # Test 1: Entity with correct user_id passes
        correct_entity = MockEntity(user_id)
        try:
            repo.ensure_user_ownership(correct_entity)
            print("✅ Correct ownership validation passed")
        except PermissionError:
            pytest.fail("Should not raise error for correct user")
        
        # Test 2: Entity with wrong user_id fails
        wrong_entity = MockEntity(other_user_id)
        with pytest.raises(PermissionError) as exc_info:
            repo.ensure_user_ownership(wrong_entity)
        assert f"does not belong to user {user_id}" in str(exc_info.value)
        print("✅ Wrong ownership validation correctly failed")
        
        # Test 3: System mode allows any entity
        system_repo = BaseUserScopedRepository(session, user_id=None)
        try:
            system_repo.ensure_user_ownership(wrong_entity)
            system_repo.ensure_user_ownership(correct_entity)
            print("✅ System mode allows all entities")
        except PermissionError:
            pytest.fail("System mode should not raise permission errors")
    
    def test_audit_logging(self, caplog):
        """Test that audit logging works correctly"""
        import logging
        
        # Set log level to INFO to capture audit logs
        caplog.set_level(logging.INFO)
        
        session = None
        user_id = str(uuid.uuid4())
        repo = BaseUserScopedRepository(session, user_id=user_id)
        
        # Test user access logging
        repo.log_access("create", "task", "task-123")
        repo.log_access("read", "project", "proj-456")
        repo.log_access("delete", "agent")
        
        # Test system access logging
        system_repo = BaseUserScopedRepository(session, user_id=None)
        system_repo.log_access("update", "context", "ctx-789")
        
        # Verify logs contain expected information
        assert f"User {user_id} performed create on task task-123" in caplog.text
        assert f"User {user_id} performed read on project proj-456" in caplog.text
        assert f"User {user_id} performed delete on agent" in caplog.text
        assert "System performed update on context ctx-789" in caplog.text
        
        print("✅ Audit logging tests passed!")


if __name__ == "__main__":
    # Run the tests
    test = TestSimpleUserIsolation()
    test.test_base_repository_user_filtering()
    test.test_data_preparation_with_user_id()
    test.test_ownership_validation()
    print("\n🎉 All simple integration tests passed successfully!")