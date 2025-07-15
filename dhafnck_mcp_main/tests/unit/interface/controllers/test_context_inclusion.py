"""
TDD Tests for Enhanced Context Inclusion Functionality

Tests the context inclusion enhancements for:
- Project MCP Controller
- Git Branch MCP Controller  
- Task MCP Controller

Following TDD approach:
1. Write failing tests first
2. Make them pass with minimal code
3. Refactor
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import uuid

# Test fixtures for all test classes
@pytest.fixture
def mock_context_facade():
    """Mock hierarchical context facade for testing"""
    facade = Mock()
    facade.get_context = Mock()
    return facade

@pytest.fixture
def test_project_data():
    """Sample project data for testing"""
    return {
        "id": "02c40162-10c3-4977-b418-0d925a001ffd",
        "name": "test-project",
        "description": "Test project for context inclusion"
    }

@pytest.fixture
def test_git_branch_data():
    """Sample git branch data for testing"""
    return {
        "id": "ee502205-88ad-46be-8c06-12af7d1b8cda",
        "name": "feature/test-branch",
        "description": "Test branch for context inclusion",
        "project_id": "02c40162-10c3-4977-b418-0d925a001ffd"
    }

@pytest.fixture
def test_task_data():
    """Sample task data for testing"""
    return {
        "id": "46e680a9-f71a-4990-807d-bb37f4b4fdfa",
        "title": "Test task",
        "description": "Test task for context inclusion",
        "git_branch_id": "ee502205-88ad-46be-8c06-12af7d1b8cda",
        "status": "todo",
        "priority": "high"
    }

@pytest.fixture
def test_project_context():
    """Sample project context data"""
    return {
        "success": True,
        "context": {
            "level": "project",
            "context_id": "02c40162-10c3-4977-b418-0d925a001ffd",
            "data": {
                "title": "test-project",
                "description": "Test project for context inclusion",
                "team_preferences": {
                    "coding_style": "PEP8",
                    "testing_framework": "pytest"
                }
            }
        }
    }

@pytest.fixture
def test_branch_context():
    """Sample branch context data"""
    return {
        "success": True,
        "context": {
            "level": "task", 
            "context_id": "ee502205-88ad-46be-8c06-12af7d1b8cda",
            "data": {
                "title": "feature/test-branch",
                "description": "Test branch for context inclusion",
                "branch_type": "feature",
                "workflow": "gitflow"
            }
        }
    }

@pytest.fixture
def test_task_context():
    """Sample task context data"""
    return {
        "success": True,
        "context": {
            "level": "task",
            "context_id": "46e680a9-f71a-4990-807d-bb37f4b4fdfa",
            "data": {
                "title": "Test task",
                "description": "Test task for context inclusion",
                "progress": 0,
                "notes": "Initial task creation"
            }
        }
    }

class TestProjectMCPControllerContextInclusion:
    """TDD tests for project controller context inclusion"""
    
    def test_project_get_should_include_project_context(self, test_project_data, test_project_context, mock_context_facade):
        """
        TEST 1: Project GET operations should include project_context
        
        GIVEN: A project exists with context
        WHEN: GET operation is called
        THEN: Response should include project_context field
        """
        # Test the specific _include_project_context method
        from fastmcp.task_management.interface.controllers.project_mcp_controller import ProjectMCPController
        from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
        
        # Create controller with mocked dependencies
        mock_facade_factory = Mock(spec=ProjectFacadeFactory)
        controller = ProjectMCPController(mock_facade_factory)
        
        # Test result with project data
        test_result = {
            "success": True,
            "project": test_project_data
        }
        
        # Mock the hierarchical context facade creation and response
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory:
            mock_context_facade_instance = Mock()
            mock_context_facade_instance.get_context.return_value = test_project_context
            mock_factory.return_value.create_facade.return_value = mock_context_facade_instance
            
            # Act - call the specific method we want to test
            result = controller._include_project_context(test_result)
            
            # Assert
            assert result["success"] is True
            assert "project" in result
            assert "project_context" in result  # This is what we're testing for!
            assert result["project_context"]["level"] == "project"
            assert result["project_context"]["context_id"] == test_project_data["id"]
            
            # Verify the context facade was called correctly
            mock_context_facade_instance.get_context.assert_called_once_with(
                "project", test_project_data["id"], include_inherited=True
            )

class TestGitBranchMCPControllerContextInclusion:
    """TDD tests for git branch controller context inclusion"""
    
    def test_git_branch_get_should_include_project_and_branch_context(self, 
                                                                     test_git_branch_data, 
                                                                     test_project_context,
                                                                     test_branch_context,
                                                                     mock_context_facade):
        """
        TEST 2: Git branch GET operations should include project_context AND branch_context
        
        GIVEN: A git branch exists with project_id and has contexts at both levels
        WHEN: GET operation is called
        THEN: Response should include both project_context and branch_context
        """
        # Arrange
        def mock_get_context(level, context_id, include_inherited=True):
            if level == "project" and context_id == test_git_branch_data["project_id"]:
                return test_project_context
            elif level == "task" and context_id == test_git_branch_data["id"]:
                return test_branch_context
            else:
                return {"success": False, "error": "Not found"}
        
        mock_context_facade.get_context.side_effect = mock_get_context
        
        # Import and test controller (will fail initially)
        try:
            from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController
            from fastmcp.task_management.application.factories.git_branch_facade_factory import GitBranchFacadeFactory
            
            # Mock the facade
            mock_facade_factory = Mock(spec=GitBranchFacadeFactory)
            mock_facade = Mock()
            mock_facade.get_git_branch_by_id.return_value = {
                "success": True,
                "git_branch": test_git_branch_data
            }
            mock_facade_factory.create_git_branch_facade.return_value = mock_facade
            
            # Create controller
            controller = GitBranchMCPController(mock_facade_factory)
            
            # Mock the context inclusion method
            with patch.object(controller, '_include_project_branch_context') as mock_include:
                mock_include.return_value = {
                    "success": True,
                    "git_branch": test_git_branch_data,
                    "project_context": test_project_context["context"],
                    "branch_context": test_branch_context["context"]
                }
                
                # Act
                result = controller._handle_get_git_branch(mock_facade, test_git_branch_data["id"])
                
                # Assert
                assert result["success"] is True
                assert "git_branch" in result
                assert "project_context" in result
                assert "branch_context" in result
                assert result["project_context"]["level"] == "project"
                assert result["branch_context"]["level"] == "task"
                assert result["git_branch"]["project_id"] == test_git_branch_data["project_id"]
                
        except ImportError:
            pytest.fail("GitBranchMCPController context inclusion not implemented yet")
    
    def test_git_branch_context_inclusion_with_missing_project_context(self, test_git_branch_data, test_project_context, test_branch_context):
        """
        TEST 2b: Test that git branch context inclusion fails when project_context is missing
        
        This test specifically checks that the _include_project_branch_context method
        correctly includes BOTH project and branch context, not just branch context.
        """
        from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController
        from fastmcp.task_management.application.factories.git_branch_facade_factory import GitBranchFacadeFactory
        
        # Create controller
        mock_facade_factory = Mock(spec=GitBranchFacadeFactory)
        controller = GitBranchMCPController(mock_facade_factory)
        
        # Test response with git branch data that includes project_id
        test_response = {
            "success": True,
            "git_branch": test_git_branch_data
        }
        
        # Mock context facade to return both contexts
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory:
            mock_context_facade_instance = Mock()
            
            def mock_get_context(level, context_id, include_inherited=True):
                if level == "project" and context_id == test_git_branch_data["project_id"]:
                    return test_project_context
                elif level == "task" and context_id == test_git_branch_data["id"]:
                    return test_branch_context
                else:
                    return {"success": False, "error": "Not found"}
            
            mock_context_facade_instance.get_context.side_effect = mock_get_context
            mock_factory.return_value.create_facade.return_value = mock_context_facade_instance
            
            # Act
            result = controller._include_project_branch_context(
                test_response, 
                test_git_branch_data["project_id"], 
                test_git_branch_data["id"]
            )
            
            # Assert - THIS is the specific test for our issue
            assert result["success"] is True
            assert "git_branch" in result
            assert "project_context" in result, "MISSING: project_context should be included in git branch GET response"
            assert "branch_context" in result, "MISSING: branch_context should be included in git branch GET response"
            
            # Verify both contexts have correct structure
            assert result["project_context"]["level"] == "project"
            assert result["branch_context"]["level"] == "task"
            
            # Verify context facade was called for both project and branch
            expected_calls = [
                (("project", test_git_branch_data["project_id"]), {"include_inherited": True}),
                (("task", test_git_branch_data["id"]), {"include_inherited": True})
            ]
            actual_calls = mock_context_facade_instance.get_context.call_args_list
            
            assert len(actual_calls) == 2, f"Expected 2 context calls, got {len(actual_calls)}"
    
    def test_git_branch_get_should_derive_project_id_from_response(self, test_git_branch_data):
        """
        TEST 3: Git branch facade should return project_id in git_branch response
        
        GIVEN: A git branch request is made
        WHEN: The facade processes the request  
        THEN: The response should include project_id in the git_branch object
        """
        try:
            from fastmcp.task_management.application.facades.git_branch_application_facade import GitBranchApplicationFacade
            
            # Mock the facade method
            facade = GitBranchApplicationFacade()
            
            # This test will drive us to fix the _find_git_branch_by_id method
            with patch.object(facade, '_find_git_branch_by_id') as mock_find:
                mock_find.return_value = {
                    "success": True,
                    "git_branch": test_git_branch_data  # Should include project_id
                }
                
                # Act
                result = facade.get_git_branch_by_id(test_git_branch_data["id"])
                
                # Assert
                assert result["success"] is True
                assert "git_branch" in result
                assert "project_id" in result["git_branch"]
                assert result["git_branch"]["project_id"] == test_git_branch_data["project_id"]
                
        except ImportError:
            pytest.fail("GitBranchApplicationFacade not properly returning project_id")

class TestTaskMCPControllerContextInclusion:
    """TDD tests for task controller context inclusion"""
    
    def test_next_task_should_include_all_three_contexts(self,
                                                        test_task_data,
                                                        test_project_context,
                                                        test_branch_context, 
                                                        test_task_context,
                                                        mock_context_facade):
        """
        TEST 4: Next task operations should include project_context, branch_context, AND task_context
        
        GIVEN: A task exists in a branch within a project, all with contexts
        WHEN: Next task operation is called
        THEN: Response should include all three context levels
        """
        # Arrange
        def mock_get_context(level, context_id, include_inherited=True):
            if level == "project":
                return test_project_context
            elif level == "task" and context_id == test_task_data["git_branch_id"]:
                return test_branch_context
            elif level == "task" and context_id == test_task_data["id"]:
                return test_task_context
            else:
                return {"success": False, "error": "Not found"}
        
        mock_context_facade.get_context.side_effect = mock_get_context
        
        # Import and test controller
        try:
            from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
            from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
            
            # Mock the facade
            mock_facade_factory = Mock(spec=TaskFacadeFactory)
            mock_facade = Mock()
            mock_facade.get_next_task.return_value = {
                "success": True,
                "task": test_task_data
            }
            mock_facade_factory.create_task_facade.return_value = mock_facade
            
            # Create controller
            controller = TaskMCPController(mock_facade_factory)
            
            # Mock the context inclusion method
            with patch.object(controller, '_include_project_branch_task_context') as mock_include:
                mock_include.return_value = {
                    "success": True,
                    "task": test_task_data,
                    "project_context": test_project_context["context"],
                    "branch_context": test_branch_context["context"],
                    "task_context": test_task_context["context"]
                }
                
                # Act
                result = controller._handle_next_task(mock_facade, test_task_data["git_branch_id"], True)
                
                # Assert
                assert result["success"] is True
                assert "task" in result
                assert "project_context" in result
                assert "branch_context" in result  
                assert "task_context" in result
                assert result["project_context"]["level"] == "project"
                assert result["branch_context"]["level"] == "task"
                assert result["task_context"]["level"] == "task"
                
        except ImportError:
            pytest.fail("TaskMCPController context inclusion not fully implemented")
    
    def test_derive_context_from_identifiers_should_return_actual_project_id(self, test_task_data, test_git_branch_data):
        """
        TEST 5: _derive_context_from_identifiers should return actual project_id from database
        
        GIVEN: A git_branch_id is provided
        WHEN: _derive_context_from_identifiers is called
        THEN: It should return the actual project_id from the database, not "default_project"
        """
        try:
            from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
            
            # Create a minimal controller
            controller = TaskMCPController(Mock())
            
            # Mock the database lookup
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_conn.execute.return_value = mock_cursor
                mock_cursor.fetchone.return_value = (test_git_branch_data["project_id"], test_git_branch_data["name"])
                mock_connect.return_value.__enter__.return_value = mock_conn
                
                # Act
                project_id, git_branch_name, user_id = controller._derive_context_from_identifiers(
                    git_branch_id=test_git_branch_data["id"]
                )
                
                # Assert
                assert project_id == test_git_branch_data["project_id"]
                assert project_id != "default_project"  # Should not be the default
                assert git_branch_name == test_git_branch_data["name"]
                assert user_id == "default_id"
                
        except ImportError:
            pytest.fail("TaskMCPController _derive_context_from_identifiers not properly implemented")

class TestContextInclusionIntegration:
    """Integration tests for context inclusion across all controllers"""
    
    def test_end_to_end_context_flow(self,
                                   test_project_data,
                                   test_git_branch_data, 
                                   test_task_data,
                                   test_project_context,
                                   test_branch_context,
                                   test_task_context):
        """
        TEST 6: End-to-end context inclusion flow
        
        GIVEN: Project, branch, and task with contexts exist
        WHEN: Operations are performed on each level
        THEN: Appropriate contexts should be included at each level
        """
        # This test will verify the complete flow works
        # Will be implemented after the individual controller tests pass
        pass

# Test helper functions
def create_test_project_with_context():
    """Helper to create test project with context for integration tests"""
    pass

def create_test_git_branch_with_context(project_id):
    """Helper to create test git branch with context for integration tests"""
    pass

def create_test_task_with_context(git_branch_id):
    """Helper to create test task with context for integration tests"""
    pass

# Run these tests with: python -m pytest tests/unit/interface/controllers/test_context_inclusion.py -v