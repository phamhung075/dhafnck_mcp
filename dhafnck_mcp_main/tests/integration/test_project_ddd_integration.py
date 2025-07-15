#!/usr/bin/env python3
"""
Integration Test for Project DDD Architecture

This test verifies that the project repositories are properly connected to the DDD architecture
and all layers work together correctly.
"""

import os
import sys
import tempfile
import logging
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.infrastructure.repositories.project_repository_factory import (
    ProjectRepositoryFactory,
    RepositoryType,
    RepositoryConfig,
    get_default_repository,
    get_sqlite_repository,
    create_project_repository
)
from fastmcp.task_management.application.factories.project_service_factory import (
    ProjectServiceFactory,
    create_project_service_factory,
    create_default_project_service,
    create_project_service_for_user,
    create_sqlite_project_service
)
from fastmcp.task_management.domain.repositories.project_repository import ProjectRepository
from fastmcp.task_management.infrastructure.utilities.path_resolver import PathResolver
from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_repository_factory():
    """Test the project repository factory"""
    print("🏗️  Testing Project Repository Factory...")
    
    # Test default creation
    repo1 = ProjectRepositoryFactory.create()
    assert repo1 is not None
    assert isinstance(repo1, ProjectRepository)
    print("✅ Default repository creation works")
    
    # Test SQLite repository creation
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        repo2 = ProjectRepositoryFactory.create(
            repository_type=RepositoryType.SQLITE,
            user_id="test_user",
            db_path=str(db_path)
        )
        assert repo2 is not None
        assert isinstance(repo2, ProjectRepository)
        print("✅ SQLite repository creation works")
    
    # Test configuration-based creation
    config = RepositoryConfig(
        repository_type="sqlite",
        user_id="config_user",
        db_path=":memory:"
    )
    repo3 = config.create_repository()
    assert repo3 is not None
    print("✅ Configuration-based creation works")
    
    # Test convenience functions
    repo4 = get_default_repository()
    assert repo4 is not None
    print("✅ Default repository getter works")
    
    repo5 = get_sqlite_repository(user_id="convenience_user", db_path=":memory:")
    assert repo5 is not None
    print("✅ SQLite repository getter works")
    
    print("🎉 Repository Factory tests passed!")


def test_service_factory():
    """Test the project service factory"""
    print("🏭  Testing Project Service Factory...")
    
    # Test factory creation
    path_resolver = PathResolver()
    factory = ProjectServiceFactory(path_resolver)
    assert factory is not None
    print("✅ Service factory creation works")
    
    # Test application service creation
    app_service = factory.create_project_application_service()
    assert app_service is not None
    print("✅ Application service creation works")
    
    # Test legacy service creation
    legacy_service = factory.create_project_service()
    assert legacy_service is not None
    print("✅ Legacy service creation works")
    
    # Test SQLite service creation
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        sqlite_service = factory.create_sqlite_service(
            user_id="test_user",
            db_path=str(db_path)
        )
        assert sqlite_service is not None
        print("✅ SQLite service creation works")
    
    # Test convenience functions
    default_service = create_default_project_service()
    assert default_service is not None
    print("✅ Default service creation works")
    
    user_service = create_project_service_for_user("test_user")
    assert user_service is not None
    print("✅ User-specific service creation works")
    
    print("🎉 Service Factory tests passed!")


@pytest.mark.asyncio
async def test_ddd_integration():
    """Test the full DDD integration"""
    print("🏛️  Testing DDD Integration...")
    
    # Create a temporary database for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "integration_test.db"
        
        # Ensure the temporary database is initialized with the schema
        initialize_database(str(db_path))
        
        # Create service through factory
        factory = create_project_service_factory()
        service = factory.create_sqlite_service(
            user_id="integration_user",
            db_path=str(db_path)
        )
        
        # Test project creation
        create_result = await service.create_project(
            project_id="test_project",
            name="Test Project",
            description="A test project for DDD integration"
        )
        assert create_result.get("success", False)
        print("✅ Project creation through service works")
        
        # Test project retrieval
        get_result = await service.get_project("test_project")
        assert get_result.get("success", False)
        project = get_result.get("project")
        assert project is not None
        assert project.get("name") == "Test Project"
        print("✅ Project retrieval through service works")
        
        # Test project listing
        list_result = await service.list_projects()
        assert list_result.get("success", False)
        projects = list_result.get("projects", [])
        assert len(projects) > 0
        print("✅ Project listing through service works")
        
        # Test project update
        update_result = await service.update_project(
            project_id="test_project",
            name="Updated Test Project",
            description="Updated description"
        )
        assert update_result.get("success", False)
        print("✅ Project update through service works")
        
        # Test task tree creation
        tree_result = await service.create_task_tree(
            project_id="test_project",
            git_branch_name="feature_branch",
            tree_name="Feature Development",
            tree_description="Tasks for feature development"
        )
        assert tree_result.get("success", False)
        print("✅ Task tree creation through service works")
        
        print("🎉 DDD Integration tests passed!")


@pytest.mark.asyncio
async def test_multi_user_support():
    """Test multi-user support in the architecture"""
    print("👥  Testing Multi-User Support...")
    
    # Create services for different users with unique databases
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create separate database files for each user
        user1_db = Path(temp_dir) / "user1.db"
        user2_db = Path(temp_dir) / "user2.db"
        
        # Initialize both databases
        initialize_database(str(user1_db))
        initialize_database(str(user2_db))
        
        factory = create_project_service_factory()
        user1_service = factory.create_sqlite_service(
            user_id="user1",
            db_path=str(user1_db)
        )
        user2_service = factory.create_sqlite_service(
            user_id="user2", 
            db_path=str(user2_db)
        )
        
        # Create projects for each user
        user1_result = await user1_service.create_project(
            project_id="user1_project",
            name="User 1 Project",
            description="Project for user 1"
        )
        assert user1_result.get("success", False)
        
        user2_result = await user2_service.create_project(
            project_id="user2_project", 
            name="User 2 Project",
            description="Project for user 2"
        )
        assert user2_result.get("success", False)
        
        # Verify isolation - user1 shouldn't see user2's projects
        user1_projects = await user1_service.list_projects()
        user2_projects = await user2_service.list_projects()
        
        user1_project_ids = [p.get("id") for p in user1_projects.get("projects", [])]
        user2_project_ids = [p.get("id") for p in user2_projects.get("projects", [])]
        
        assert "user1_project" in user1_project_ids
        assert "user2_project" not in user1_project_ids
        assert "user2_project" in user2_project_ids
        assert "user1_project" not in user2_project_ids
        
        print("✅ User isolation works correctly")
    
    print("🎉 Multi-User Support tests passed!")


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the architecture"""
    print("🚨  Testing Error Handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "error_test.db"
        initialize_database(str(db_path))
        
        factory = create_project_service_factory()
        service = factory.create_sqlite_service(
            user_id="error_user",
            db_path=str(db_path)
        )
        
        # Test getting a non-existent project
        get_result = await service.get_project("non_existent_project")
        assert not get_result.get("success", True)
        assert "not found" in get_result.get("error", "").lower()
        print("✅ Graceful failure for non-existent project works")
    
    print("🎉 Error Handling tests passed!")


# Tests are now run via pytest - see individual test functions above 