"""
Test to verify the fix for context hierarchy validation issue with dual authentication.

This test ensures that project context creation works correctly when:
1. Global context exists for a specific user
2. Project context creation is attempted by the same user
3. The hierarchy validator uses the correct user-scoped repositories
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastmcp.task_management.infrastructure.database.models import Base, GlobalContext as GlobalContextModel
from fastmcp.task_management.infrastructure.repositories.global_context_repository_user_scoped import GlobalContextRepository
from fastmcp.task_management.infrastructure.repositories.project_context_repository_user_scoped import ProjectContextRepository
from fastmcp.task_management.infrastructure.repositories.branch_context_repository import BranchContextRepository
from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository
from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.domain.entities.context import GlobalContext


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory


@pytest.fixture
def user_id():
    """Test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def global_context_data():
    """Test global context data."""
    return {
        "organization_name": "Test Organization",
        "global_settings": {
            "autonomous_rules": {"test": "rule"},
            "security_policies": {"test": "policy"}
        }
    }


@pytest.fixture
def project_context_data():
    """Test project context data."""
    return {
        "project_name": "Test Project",
        "project_settings": {
            "test": "setting"
        }
    }


def test_context_hierarchy_validation_with_dual_auth(test_db, user_id, global_context_data, project_context_data):
    """
    Test that demonstrates the fix for context hierarchy validation with dual authentication.
    
    Steps:
    1. Create user-scoped global context
    2. Create user-scoped unified context service
    3. Verify that project context creation works (this was failing before the fix)
    """
    # Step 1: Create global context for the user
    global_repo = GlobalContextRepository(test_db, user_id)
    global_entity = GlobalContext(
        id="global_singleton",
        organization_name=global_context_data["organization_name"],
        global_settings=global_context_data["global_settings"]
    )
    created_global = global_repo.create(global_entity)
    
    assert created_global is not None
    assert created_global.organization_name == global_context_data["organization_name"]
    
    # Step 2: Verify global context can be retrieved
    retrieved_global = global_repo.get("global_singleton")
    assert retrieved_global is not None
    assert retrieved_global.id == created_global.id
    
    # Step 3: Create unified context service with user scope
    project_repo = ProjectContextRepository(test_db, user_id)
    branch_repo = BranchContextRepository(test_db, user_id)  
    task_repo = TaskContextRepository(test_db, user_id)
    
    unified_service = UnifiedContextService(
        global_context_repository=global_repo,
        project_context_repository=project_repo,
        branch_context_repository=branch_repo,
        task_context_repository=task_repo,
        user_id=user_id
    )
    
    # Step 4: Create project context (this should work with the fix)
    project_id = str(uuid.uuid4())
    project_result = unified_service.create_context(
        level="project",
        context_id=project_id,
        data=project_context_data,
        user_id=user_id
    )
    
    # This was failing before the fix with "Global context is required before creating project contexts"
    assert project_result["success"] is True, f"Project context creation failed: {project_result.get('error')}"
    assert project_result["context"]["id"] == project_id
    assert project_result["context"]["project_name"] == project_context_data["project_name"]
    
    # Step 5: Verify the project context can be retrieved
    project_get_result = unified_service.get_context(
        level="project", 
        context_id=project_id
    )
    assert project_get_result["success"] is True
    assert project_get_result["context"]["id"] == project_id


def test_context_hierarchy_validation_error_case(test_db, user_id, project_context_data):
    """
    Test that hierarchy validation still works when global context doesn't exist.
    """
    # Create unified context service without creating global context first
    global_repo = GlobalContextRepository(test_db, user_id)
    project_repo = ProjectContextRepository(test_db, user_id)
    branch_repo = BranchContextRepository(test_db, user_id)
    task_repo = TaskContextRepository(test_db, user_id)
    
    unified_service = UnifiedContextService(
        global_context_repository=global_repo,
        project_context_repository=project_repo,
        branch_context_repository=branch_repo,
        task_context_repository=task_repo,
        user_id=user_id
    )
    
    # Try to create project context without global context
    project_id = str(uuid.uuid4())
    project_result = unified_service.create_context(
        level="project",
        context_id=project_id,
        data=project_context_data,
        user_id=user_id
    )
    
    # This should fail with helpful error message
    assert project_result["success"] is False
    assert "Global context is required" in project_result["error"]


def test_user_isolation_in_hierarchy_validation(test_db, global_context_data, project_context_data):
    """
    Test that hierarchy validation respects user isolation.
    """
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    
    # Create global context for user1 only
    global_repo_user1 = GlobalContextRepository(test_db, user1_id)
    global_entity = GlobalContext(
        id="global_singleton",
        organization_name=global_context_data["organization_name"],
        global_settings=global_context_data["global_settings"]
    )
    global_repo_user1.create(global_entity)
    
    # Create unified service for user2 (who has no global context)
    global_repo_user2 = GlobalContextRepository(test_db, user2_id)
    project_repo_user2 = ProjectContextRepository(test_db, user2_id)
    branch_repo_user2 = BranchContextRepository(test_db, user2_id)
    task_repo_user2 = TaskContextRepository(test_db, user2_id)
    
    unified_service_user2 = UnifiedContextService(
        global_context_repository=global_repo_user2,
        project_context_repository=project_repo_user2,
        branch_context_repository=branch_repo_user2,
        task_context_repository=task_repo_user2,
        user_id=user2_id
    )
    
    # Try to create project context for user2
    project_id = str(uuid.uuid4())
    project_result = unified_service_user2.create_context(
        level="project",
        context_id=project_id,
        data=project_context_data,
        user_id=user2_id
    )
    
    # This should fail because user2 has no global context
    # (user1's global context should not be visible to user2)
    assert project_result["success"] is False
    assert "Global context is required" in project_result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])