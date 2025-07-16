"""Standardized Test Fixtures for Hierarchical Context System

This module provides standardized pytest fixtures for testing the new hierarchical
context management system after repository migration.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional
import tempfile
import os

# Import the new hierarchical context system components
from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory

# Import repository interfaces for mocking
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository


@pytest.fixture
def hierarchical_context_service_mock():
    """Mock for hierarchical context service with standard method signatures"""
    # Create a mock without spec to allow arbitrary attributes
    mock = Mock()
    
    # Standard return values for common operations
    mock.create_context.return_value = {
        "success": True, 
        "context_id": "test-context-123",
        "level": "task",
        "data": {}
    }
    
    mock.get_context.return_value = {
        "level": "task", 
        "context_id": "test-context-123",
        "data": {"status": "active", "priority": "medium"},
        "parent_context": None,
        "child_contexts": []
    }
    
    mock.update_context.return_value = {
        "success": True,
        "context_id": "test-context-123", 
        "updated_fields": ["status", "data"]
    }
    
    mock.delete_context.return_value = {
        "success": True,
        "context_id": "test-context-123"
    }
    
    # Hierarchical-specific methods
    mock.resolve_context.return_value = {
        "resolved_context": {"level": "task", "data": {}},
        "inheritance_chain": ["global", "project", "branch", "task"],
        "effective_data": {}
    }
    
    mock.propagate_changes.return_value = {
        "success": True,
        "affected_contexts": ["child-1", "child-2"]
    }
    
    return mock


@pytest.fixture  
def hierarchical_context_facade_mock():
    """Mock for hierarchical context facade"""
    mock = Mock()
    
    mock.create.return_value = {
        "success": True, 
        "context_id": "test-context-123",
        "metadata": {"created_at": "2024-01-01T00:00:00Z"}
    }
    
    mock.get.return_value = {
        "context_id": "test-context-123",
        "level": "task",
        "data": {},
        "resolved_data": {}
    }
    
    mock.update.return_value = {
        "success": True,
        "context_id": "test-context-123"
    }
    
    mock.delete.return_value = {"success": True}
    
    return mock


@pytest.fixture
def orm_task_repository_mock():
    """Mock for ORM task repository with new interface"""
    mock = Mock()
    
    # Standard CRUD operations
    mock.create.return_value = "task-id-123"
    mock.get_by_id.return_value = {
        "id": "task-id-123", 
        "title": "Test Task",
        "status": "todo",
        "priority": "medium",
        "git_branch_id": "branch-123"
    }
    mock.update.return_value = True
    mock.delete.return_value = True
    
    # List operations
    mock.list_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "status": "todo"},
        {"id": "task-2", "title": "Task 2", "status": "in_progress"}
    ]
    
    mock.search.return_value = [
        {"id": "task-1", "title": "Matching Task", "status": "todo"}
    ]
    
    # Task-specific operations
    mock.get_next_task.return_value = {
        "id": "task-next-123",
        "title": "Next Priority Task", 
        "priority_score": 85,
        "autonomous_ready": True,
        "decision_confidence": 75
    }
    
    mock.add_dependency.return_value = True
    mock.remove_dependency.return_value = True
    mock.get_dependencies.return_value = ["dep-1", "dep-2"]
    
    return mock


@pytest.fixture
def orm_hierarchical_context_repository_mock():
    """Mock for ORM hierarchical context repository"""
    mock = Mock()
    
    mock.create_context.return_value = "context-id-123"
    mock.get_context.return_value = {
        "id": "context-id-123",
        "level": "task",
        "context_id": "task-123",
        "data": {},
        "parent_id": None
    }
    mock.update_context.return_value = True
    mock.delete_context.return_value = True
    
    # Hierarchical operations
    mock.get_context_hierarchy.return_value = [
        {"level": "global", "data": {}},
        {"level": "project", "data": {}},
        {"level": "task", "data": {}}
    ]
    
    mock.resolve_inheritance.return_value = {
        "resolved_data": {},
        "inheritance_chain": ["global", "project", "task"]
    }
    
    return mock


@pytest.fixture
def task_application_facade_mock():
    """Mock for task application facade with updated interface"""
    mock = Mock()
    
    # Task creation with context integration
    mock.create_task.return_value = {
        "success": True,
        "task_id": "task-123",
        "context_id": "context-123",
        "workflow_guidance": {
            "recommended_agent": "@coding_agent",
            "next_actions": [],
            "current_state": {
                "autonomous_ready": True,
                "decision_confidence": 85,
                "priority_score": 75
            }
        }
    }
    
    mock.get_task.return_value = {
        "task_id": "task-123",
        "title": "Test Task",
        "status": "todo",
        "context": {},
        "workflow_hints": []
    }
    
    mock.update_task.return_value = {
        "success": True,
        "task_id": "task-123",
        "updated_fields": ["status", "progress"]
    }
    
    mock.complete_task.return_value = {
        "success": True,
        "task_id": "task-123", 
        "completion_summary": "Task completed successfully",
        "context_updates": {}
    }
    
    mock.list_tasks.return_value = {
        "tasks": [],
        "total_count": 0,
        "filters_applied": {}
    }
    
    mock.search_tasks.return_value = {
        "tasks": [],
        "search_query": "test",
        "total_matches": 0
    }
    
    mock.get_next_task.return_value = {
        "task": None,
        "workflow_guidance": {
            "autonomous_ready": False,
            "decision_confidence": 0,
            "reason": "No pending tasks"
        }
    }
    
    return mock


@pytest.fixture
def hierarchical_context_facade_factory_mock():
    """Mock for hierarchical context facade factory"""
    mock = Mock()
    
    # Return mocked facade instance
    facade_mock = Mock()
    mock.create_facade.return_value = facade_mock
    mock.get_facade.return_value = facade_mock
    
    return mock


@pytest.fixture
def test_database_path():
    """Provide isolated test database path"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_database_config():
    """Test database configuration for isolation"""
    config = {
        "database_url": ":memory:",  # Use in-memory SQLite for tests
        "echo": False,
        "pool_pre_ping": True
    }
    return config


@pytest.fixture
def sample_task_data():
    """Standard test task data"""
    return {
        "title": "Test Task",
        "description": "A test task for unit testing",
        "status": "todo",
        "priority": "medium",
        "git_branch_id": "branch-123",
        "assignees": ["test-user"],
        "labels": ["test", "unit-test"],
        "estimated_effort": "2 hours"
    }


@pytest.fixture
def sample_context_data():
    """Standard test context data"""
    return {
        "level": "task",
        "context_id": "task-123",
        "data": {
            "task_metadata": {
                "created_by": "test-user",
                "project_id": "proj-123"
            },
            "workflow_state": {
                "current_phase": "implementation",
                "progress_percentage": 25
            },
            "ai_insights": {
                "complexity_score": 3,
                "estimated_duration": "2 hours"
            }
        },
        "parent_context": "branch-123",
        "inheritance_rules": {
            "inherit_labels": True,
            "inherit_assignees": False
        }
    }


@pytest.fixture
def sample_workflow_guidance():
    """Standard workflow guidance response"""
    return {
        "workflow_guidance": {
            "current_state": {
                "autonomous_ready": True,
                "decision_confidence": 85,
                "priority_score": 75
            },
            "recommended_agent": "@coding_agent",
            "next_actions": [
                {
                    "tool": "manage_task",
                    "action": "update",
                    "params": {
                        "task_id": "task-123",
                        "status": "in_progress"
                    }
                }
            ],
            "workflow_hints": [
                "Task is ready for implementation",
                "Consider breaking down into subtasks if complex"
            ]
        }
    }


@pytest.fixture(autouse=True)
def reset_mocks():
    """Automatically reset all mocks between tests"""
    yield
    # Any cleanup code here if needed


# Composite fixtures for common test scenarios

@pytest.fixture
def full_task_context_setup(
    hierarchical_context_service_mock,
    orm_task_repository_mock,
    task_application_facade_mock,
    sample_task_data,
    sample_context_data
):
    """Complete setup for testing task operations with context"""
    return {
        "context_service": hierarchical_context_service_mock,
        "task_repository": orm_task_repository_mock,
        "task_facade": task_application_facade_mock,
        "task_data": sample_task_data,
        "context_data": sample_context_data
    }


@pytest.fixture
def integration_test_setup(
    test_database_path,
    test_database_config,
    sample_task_data,
    sample_context_data
):
    """Setup for integration tests with real database"""
    return {
        "db_path": test_database_path,
        "db_config": test_database_config,
        "task_data": sample_task_data,
        "context_data": sample_context_data
    }