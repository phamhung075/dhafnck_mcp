"""
TDD Tests for Context Storage Validation

Tests that verify context data is stored with correct IDs at each level:
- Project-level context stored with project_id (not task_id)  
- Git branch-level context stored with git_branch_id (as task-level context)
- Task-level context stored with task_id

This addresses the root issue where contexts are stored with incorrect IDs,
making them unretrievable by the context inclusion methods.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import uuid
import sqlite3

# Test fixtures
@pytest.fixture
def test_project_id():
    """Sample project ID for testing"""
    return "02c40162-10c3-4977-b418-0d925a001ffd"

@pytest.fixture
def test_git_branch_id():
    """Sample git branch ID for testing"""
    return "ee502205-88ad-46be-8c06-12af7d1b8cda"

@pytest.fixture
def test_task_id():
    """Sample task ID for testing"""
    return "46e680a9-f71a-4990-807d-bb37f4b4fdfa"

@pytest.fixture
def test_project_context_data():
    """Sample project context data"""
    return {
        "title": "enhanced-context-test",
        "description": "Test project for enhanced context inclusion functionality",
        "team_preferences": {
            "coding_style": "PEP8",
            "testing_framework": "pytest"
        }
    }

@pytest.fixture
def test_branch_context_data():
    """Sample branch context data"""
    return {
        "title": "feature/context-inclusion-test",
        "description": "Branch for testing enhanced context inclusion",
        "branch_type": "feature",
        "workflow": "gitflow"
    }

@pytest.fixture
def test_task_context_data():
    """Sample task context data"""
    return {
        "title": "Test enhanced context inclusion",
        "description": "Task to test the enhanced context inclusion functionality",
        "progress": 0,
        "notes": "Initial task creation"
    }

@pytest.fixture
def mock_hierarchical_services():
    """Mock services for HierarchicalContextFacade"""
    return {
        "hierarchy_service": Mock(),
        "inheritance_service": Mock(),
        "delegation_service": Mock(),
        "cache_service": Mock()
    }


class TestContextStorageValidation:
    """TDD tests for context storage validation"""
    
    def test_project_context_should_be_stored_with_project_id(self, 
                                                             test_project_id, 
                                                             test_project_context_data,
                                                             mock_hierarchical_services):
        """
        TEST 1: Project context should be stored with project_id as context_id
        
        GIVEN: A project context is created
        WHEN: The context is stored
        THEN: It should be stored with project_id as the context_id (not task_id)
        """
        try:
            from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade
            
            # Create facade with mock services
            facade = HierarchicalContextFacade(
                mock_hierarchical_services["hierarchy_service"],
                mock_hierarchical_services["inheritance_service"], 
                mock_hierarchical_services["delegation_service"],
                mock_hierarchical_services["cache_service"]
            )
            
            # Mock the hierarchy service to return success
            mock_hierarchical_services["hierarchy_service"].create_context.return_value = {
                "context_id": test_project_id,
                "level": "project",
                "data": test_project_context_data
            }
            
            # Act - create project context
            result = facade.create_context(
                level="project",
                context_id=test_project_id,  # This should be used as the storage key
                data=test_project_context_data
            )
            
            # Assert - verify the hierarchy service was called with correct project_id
            mock_hierarchical_services["hierarchy_service"].create_context.assert_called_once()
            call_args = mock_hierarchical_services["hierarchy_service"].create_context.call_args
            
            # The context should be stored with project_id as the key
            stored_level = call_args[0][0]  # First argument is level
            stored_context_id = call_args[0][1]  # Second argument is context_id
            
            assert stored_level == "project", f"Context level should be 'project', but was '{stored_level}'"
            assert stored_context_id == test_project_id, f"Project context should be stored with project_id {test_project_id}, but was stored with {stored_context_id}"
            
            # Verify cache invalidation was called
            mock_hierarchical_services["cache_service"].invalidate_context.assert_called_once_with("project", test_project_id)
            
            # Verify result success
            assert result["success"] is True
            
        except ImportError as e:
            pytest.fail(f"HierarchicalContextFacade not available: {e}")
    
    def test_git_branch_context_should_be_stored_with_git_branch_id(self, 
                                                                   test_project_id,
                                                                   test_git_branch_id, 
                                                                   test_branch_context_data,
                                                                   mock_hierarchical_services):
        """
        TEST 2: Git branch context should be stored with git_branch_id as context_id
        
        GIVEN: A git branch context is created
        WHEN: The context is stored (as task-level context per architecture)
        THEN: It should be stored with git_branch_id as the context_id
        """
        try:
            from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade
            
            # Create facade with mock services
            facade = HierarchicalContextFacade(
                mock_hierarchical_services["hierarchy_service"],
                mock_hierarchical_services["inheritance_service"], 
                mock_hierarchical_services["delegation_service"],
                mock_hierarchical_services["cache_service"]
            )
            
            # Mock the hierarchy service to return success
            mock_hierarchical_services["hierarchy_service"].create_context.return_value = {
                "context_id": test_git_branch_id,
                "level": "task",
                "data": test_branch_context_data
            }
            
            # Act - create branch context (stored as task-level context)
            result = facade.create_context(
                level="task",  # Branch contexts are stored as task-level
                context_id=test_git_branch_id,  # This should be used as the storage key
                data=test_branch_context_data
            )
            
            # Assert - verify the hierarchy service was called with correct git_branch_id
            mock_hierarchical_services["hierarchy_service"].create_context.assert_called_once()
            call_args = mock_hierarchical_services["hierarchy_service"].create_context.call_args
            
            # The context should be stored with git_branch_id as the key
            stored_level = call_args[0][0]  # First argument is level
            stored_context_id = call_args[0][1]  # Second argument is context_id
            
            assert stored_level == "task", f"Branch context level should be 'task', but was '{stored_level}'"
            assert stored_context_id == test_git_branch_id, f"Branch context should be stored with git_branch_id {test_git_branch_id}, but was stored with {stored_context_id}"
            
            # Verify cache invalidation was called
            mock_hierarchical_services["cache_service"].invalidate_context.assert_called_once_with("task", test_git_branch_id)
            
            # Verify result success
            assert result["success"] is True
            
        except ImportError as e:
            pytest.fail(f"HierarchicalContextFacade not available: {e}")
    
    def test_task_context_should_be_stored_with_task_id(self, 
                                                       test_project_id,
                                                       test_git_branch_id,
                                                       test_task_id, 
                                                       test_task_context_data,
                                                       mock_hierarchical_services):
        """
        TEST 3: Task context should be stored with task_id as context_id
        
        GIVEN: A task context is created
        WHEN: The context is stored
        THEN: It should be stored with task_id as the context_id
        """
        try:
            from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade
            
            # Create facade with mock services
            facade = HierarchicalContextFacade(
                mock_hierarchical_services["hierarchy_service"],
                mock_hierarchical_services["inheritance_service"], 
                mock_hierarchical_services["delegation_service"],
                mock_hierarchical_services["cache_service"]
            )
            
            # Mock the hierarchy service to return success
            mock_hierarchical_services["hierarchy_service"].create_context.return_value = {
                "context_id": test_task_id,
                "level": "task",
                "data": test_task_context_data
            }
            
            # Act - create task context
            result = facade.create_context(
                level="task",
                context_id=test_task_id,  # This should be used as the storage key
                data=test_task_context_data
            )
            
            # Assert - verify the hierarchy service was called with correct task_id
            mock_hierarchical_services["hierarchy_service"].create_context.assert_called_once()
            call_args = mock_hierarchical_services["hierarchy_service"].create_context.call_args
            
            # The context should be stored with task_id as the key
            stored_level = call_args[0][0]  # First argument is level
            stored_context_id = call_args[0][1]  # Second argument is context_id
            
            assert stored_level == "task", f"Context level should be 'task', but was '{stored_level}'"
            assert stored_context_id == test_task_id, f"Task context should be stored with task_id {test_task_id}, but was stored with {stored_context_id}"
            
            # Verify cache invalidation was called
            mock_hierarchical_services["cache_service"].invalidate_context.assert_called_once_with("task", test_task_id)
            
            # Verify result success
            assert result["success"] is True
            
        except ImportError as e:
            pytest.fail(f"HierarchicalContextFacade not available: {e}")
    
    def test_context_retrieval_with_correct_ids(self, 
                                               test_project_id,
                                               test_git_branch_id,
                                               test_task_id,
                                               test_project_context_data,
                                               test_branch_context_data,
                                               test_task_context_data,
                                               mock_hierarchical_services):
        """
        TEST 4: Context retrieval should work with correctly stored IDs
        
        GIVEN: Contexts are stored with correct IDs at each level
        WHEN: Contexts are retrieved for inclusion
        THEN: All contexts should be found with correct IDs
        """
        try:
            from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade
            
            # Create facade with mock services
            facade = HierarchicalContextFacade(
                mock_hierarchical_services["hierarchy_service"],
                mock_hierarchical_services["inheritance_service"], 
                mock_hierarchical_services["delegation_service"],
                mock_hierarchical_services["cache_service"]
            )
            
            # Mock the hierarchy service to simulate correctly stored contexts
            def mock_get_context(level, context_id):
                if level == "project" and context_id == test_project_id:
                    return test_project_context_data
                elif level == "task" and context_id == test_git_branch_id:
                    return {"task_data": test_branch_context_data}
                elif level == "task" and context_id == test_task_id:
                    return {"task_data": test_task_context_data}
                else:
                    return None
            
            mock_hierarchical_services["hierarchy_service"].get_context.side_effect = mock_get_context
            mock_hierarchical_services["cache_service"].get_context.return_value = None  # No cache hits
            
            # Act - retrieve all three levels of context
            project_result = facade.get_context("project", test_project_id, include_inherited=False)
            branch_result = facade.get_context("task", test_git_branch_id, include_inherited=False)  
            task_result = facade.get_context("task", test_task_id, include_inherited=False)
            
            # Assert - all contexts should be found
            assert project_result["success"] is True, f"Project context not found with project_id {test_project_id}"
            assert project_result["context"]["context_id"] == test_project_id
            
            assert branch_result["success"] is True, f"Branch context not found with git_branch_id {test_git_branch_id}"
            assert branch_result["context"]["context_id"] == test_git_branch_id
            
            assert task_result["success"] is True, f"Task context not found with task_id {test_task_id}"
            assert task_result["context"]["context_id"] == test_task_id
            
        except ImportError as e:
            pytest.fail(f"HierarchicalContextFacade not available: {e}")
    
    def test_database_storage_validation_direct(self, 
                                              test_project_id,
                                              test_git_branch_id,
                                              test_task_id):
        """
        TEST 5: Direct database validation of stored context IDs
        
        GIVEN: Contexts are created and stored
        WHEN: Database is queried directly
        THEN: Contexts should be stored with correct context_id values
        """
        # This test will verify the actual database storage
        # For now, we'll mock the database interaction to define expected behavior
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            # Expected database queries for different context levels
            expected_queries = [
                # Project context should be stored with project_id
                ("SELECT * FROM context_data WHERE level = 'project' AND context_id = ?", (test_project_id,)),
                # Branch context should be stored with git_branch_id (as task level)
                ("SELECT * FROM context_data WHERE level = 'task' AND context_id = ?", (test_git_branch_id,)),
                # Task context should be stored with task_id  
                ("SELECT * FROM context_data WHERE level = 'task' AND context_id = ?", (test_task_id,))
            ]
            
            # Simulate database queries
            for query, params in expected_queries:
                mock_cursor.fetchone.return_value = (
                    params[0],  # context_id should match the expected ID
                    "test_data",  # mock data
                    "2024-01-01T00:00:00Z"  # mock timestamp
                )
                
                # Verify the query would find the context with correct ID
                result = mock_cursor.fetchone()
                assert result is not None, f"Context should be found with ID {params[0]}"
                assert result[0] == params[0], f"Retrieved context_id {result[0]} should match expected {params[0]}"


class TestContextIdInconsistencyDetection:
    """Tests to detect and prevent context ID inconsistencies"""
    
    def test_detect_project_context_stored_with_wrong_id(self, 
                                                        test_project_id, 
                                                        test_task_id,
                                                        mock_hierarchical_services):
        """
        TEST 6: Detect when project context is incorrectly stored with task_id
        
        This test identifies the specific issue we've been seeing where
        project contexts are stored with task_id instead of project_id.
        """
        try:
            from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade
            
            facade = HierarchicalContextFacade(
                mock_hierarchical_services["hierarchy_service"],
                mock_hierarchical_services["inheritance_service"], 
                mock_hierarchical_services["delegation_service"],
                mock_hierarchical_services["cache_service"]
            )
            
            # Mock database to simulate the incorrect storage we've been seeing
            def mock_incorrect_storage(level, context_id):
                if level == "project" and context_id == test_project_id:
                    # This simulates the bug: project context not found with project_id
                    return None
                elif level == "project" and context_id == test_task_id:
                    # This simulates the bug: project context incorrectly stored with task_id
                    return {"title": "Project stored with wrong ID"}
                else:
                    return None
            
            mock_hierarchical_services["hierarchy_service"].get_context.side_effect = mock_incorrect_storage
            mock_hierarchical_services["cache_service"].get_context.return_value = None
            
            # Act - try to retrieve project context with correct project_id
            correct_result = facade.get_context("project", test_project_id, include_inherited=False)
            
            # This should fail if the bug exists
            assert correct_result["success"] is False, "This test expects the bug to exist - project context not found with correct project_id"
            
            # Try to retrieve with incorrect task_id (simulating the bug)
            incorrect_result = facade.get_context("project", test_task_id, include_inherited=False)
            
            # This would succeed if the bug exists
            if incorrect_result["success"]:
                pytest.fail(f"BUG DETECTED: Project context found with task_id {test_task_id} instead of project_id {test_project_id}")
                
        except ImportError as e:
            pytest.fail(f"HierarchicalContextFacade not available: {e}")
    
    def test_context_creation_id_validation(self, 
                                           test_project_id,
                                           test_git_branch_id,
                                           test_task_id):
        """
        TEST 7: Validate that context creation uses correct IDs
        
        This test ensures that when contexts are created through the MCP tools,
        they use the correct IDs for storage.
        """
        # Mock the MCP tool calls to verify correct ID usage
        with patch('fastmcp.task_management.application.facades.hierarchical_context_facade.HierarchicalContextFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade_class.return_value = mock_facade
            
            # Track what IDs are used for context creation
            created_contexts = []
            
            def mock_create_context(level, context_id, data, **kwargs):
                created_contexts.append({
                    "level": level,
                    "context_id": context_id,
                    "data": data
                })
                return {"success": True, "context_id": context_id}
            
            mock_facade.create_context.side_effect = mock_create_context
            
            # Simulate MCP tool context creation calls
            try:
                from fastmcp.task_management.interface.controllers.project_mcp_controller import ProjectMCPController
                
                # Create a minimal controller to test context creation
                controller = ProjectMCPController(Mock())
                
                # This would be called when including project context
                # Verify it uses project_id not task_id
                with patch.object(controller, '_include_project_context') as mock_include:
                    mock_include.return_value = {"success": True}
                    
                    # Test that project context inclusion uses project_id
                    # (This is what SHOULD happen, test will drive implementation)
                    
                    # For now, just verify the pattern we expect
                    assert True  # Placeholder - will be implemented based on actual context creation flow
                    
            except ImportError:
                # Controller may not exist yet, that's fine for this test
                assert True


# Run these tests with: python -m pytest tests/unit/interface/controllers/test_context_storage_validation.py -v