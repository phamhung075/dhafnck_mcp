"""
Integration Tests for Enhanced Context Inclusion

These tests verify the actual context inclusion functionality works end-to-end
using real data and minimal mocking to identify the root cause of missing contexts.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock
from typing import Dict, Any


@pytest.mark.integration
class TestContextInclusionIntegration:
    """Integration tests for context inclusion functionality"""
    
    @pytest.fixture
    def real_project_data(self):
        """Real project data from our test setup"""
        return {
            "id": "02c40162-10c3-4977-b418-0d925a001ffd",
            "name": "enhanced-context-test",
            "description": "Test project for enhanced context inclusion functionality"
        }
    
    @pytest.fixture
    def real_git_branch_data(self):
        """Real git branch data from our test setup"""
        return {
            "id": "ee502205-88ad-46be-8c06-12af7d1b8cda",
            "name": "feature/context-inclusion-test",
            "description": "Branch for testing enhanced context inclusion",
            "project_id": "02c40162-10c3-4977-b418-0d925a001ffd"
        }
    
    @pytest.fixture
    def real_task_data(self):
        """Real task data from our test setup"""
        return {
            "id": "46e680a9-f71a-4990-807d-bb37f4b4fdfa",
            "title": "Test enhanced context inclusion",
            "description": "Task to test the enhanced context inclusion functionality",
            "git_branch_id": "ee502205-88ad-46be-8c06-12af7d1b8cda",
            "status": "todo",
            "priority": "high"
        }

    def test_project_get_context_inclusion_with_real_facade(self, real_project_data):
        """
        TEST: Project controller context inclusion with real facade call
        
        This test uses minimal mocking to test the actual _include_project_context method
        """
        from fastmcp.task_management.interface.controllers.project_mcp_controller import ProjectMCPController
        from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
        
        # Create controller with real factory
        facade_factory = ProjectFacadeFactory()
        controller = ProjectMCPController(facade_factory)
        
        # Simulate a successful project response (what would come from the facade)
        test_result = {
            "success": True,
            "project": real_project_data
        }
        
        # Mock only the context creation to see if the issue is in context retrieval
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory:
            mock_context_facade = Mock()
            
            # Simulate successful context retrieval
            mock_context_facade.get_context.return_value = {
                "success": True,
                "context": {
                    "level": "project",
                    "context_id": real_project_data["id"],
                    "data": {
                        "title": real_project_data["name"],
                        "description": real_project_data["description"],
                        "team_preferences": {
                            "coding_style": "PEP8"
                        }
                    }
                }
            }
            
            mock_factory.return_value.create_facade.return_value = mock_context_facade
            
            # Act - call the actual method
            result = controller._include_project_context(test_result)
            
            # Debug output
            print(f"DEBUG: Result keys: {list(result.keys())}")
            print(f"DEBUG: Has project_context: {'project_context' in result}")
            if 'project_context' in result:
                print(f"DEBUG: project_context type: {type(result['project_context'])}")
                print(f"DEBUG: project_context: {result['project_context']}")
            
            # Assert
            assert result["success"] is True
            assert "project" in result
            assert "project_context" in result, f"project_context missing from result: {list(result.keys())}"
            
            # Verify the context facade was called
            mock_context_facade.get_context.assert_called_once_with(
                "project", real_project_data["id"], include_inherited=True
            )

    def test_git_branch_get_context_inclusion_debug(self, real_git_branch_data):
        """
        TEST: Debug git branch context inclusion to find the root cause
        """
        from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController
        from fastmcp.task_management.application.factories.git_branch_facade_factory import GitBranchFacadeFactory
        
        # Create controller
        facade_factory = GitBranchFacadeFactory()
        controller = GitBranchMCPController(facade_factory)
        
        # Test response that would come from the facade (with project_id)
        test_response = {
            "success": True,
            "git_branch": real_git_branch_data
        }
        
        # Mock context facade responses
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory:
            mock_context_facade = Mock()
            
            def mock_get_context(level, context_id, include_inherited=True):
                if level == "project":
                    return {
                        "success": True,
                        "context": {
                            "level": "project",
                            "context_id": context_id,
                            "data": {"title": "Test Project"}
                        }
                    }
                elif level == "task":
                    return {
                        "success": True,
                        "context": {
                            "level": "task", 
                            "context_id": context_id,
                            "data": {"title": "Test Branch"}
                        }
                    }
                else:
                    return {"success": False, "error": "Unknown level"}
            
            mock_context_facade.get_context.side_effect = mock_get_context
            mock_factory.return_value.create_facade.return_value = mock_context_facade
            
            # Act
            result = controller._include_project_branch_context(
                test_response, 
                real_git_branch_data["project_id"], 
                real_git_branch_data["id"]
            )
            
            # Debug output
            print(f"DEBUG: Git branch result keys: {list(result.keys())}")
            print(f"DEBUG: Has project_context: {'project_context' in result}")
            print(f"DEBUG: Has branch_context: {'branch_context' in result}")
            print(f"DEBUG: Full result: {result}")
            
            # Check what calls were made to context facade
            calls = mock_context_facade.get_context.call_args_list
            print(f"DEBUG: Context facade calls: {calls}")
            
            # Assert
            assert result["success"] is True
            assert "git_branch" in result
            assert "project_context" in result, f"project_context missing from git branch result"
            assert "branch_context" in result, f"branch_context missing from git branch result"

    def test_task_next_context_inclusion_debug(self, real_task_data, real_git_branch_data):
        """
        TEST: Debug task next context inclusion to find why contexts are missing
        """
        from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
        from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
        from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
        
        # Create controller with minimal mocking
        repository_factory = TaskRepositoryFactory()
        facade_factory = TaskFacadeFactory(repository_factory)
        controller = TaskMCPController(facade_factory)
        
        # Test response that would come from next task
        test_response = {
            "success": True,
            "task": real_task_data
        }
        
        # Mock context facade responses
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory:
            mock_context_facade = Mock()
            
            def mock_get_context(level, context_id, include_inherited=True):
                print(f"DEBUG: get_context called with level={level}, context_id={context_id}")
                if level == "project":
                    return {
                        "success": True,
                        "context": {
                            "level": "project",
                            "context_id": context_id,
                            "data": {"title": "Test Project"}
                        }
                    }
                elif level == "task" and context_id == real_git_branch_data["id"]:
                    return {
                        "success": True,
                        "context": {
                            "level": "task",
                            "context_id": context_id,
                            "data": {"title": "Test Branch"}
                        }
                    }
                elif level == "task" and context_id == real_task_data["id"]:
                    return {
                        "success": True,
                        "context": {
                            "level": "task",
                            "context_id": context_id,
                            "data": {"title": "Test Task"}
                        }
                    }
                else:
                    print(f"DEBUG: get_context returning failure for level={level}, context_id={context_id}")
                    return {"success": False, "error": f"Not found: {level}/{context_id}"}
            
            mock_context_facade.get_context.side_effect = mock_get_context
            mock_factory.return_value.create_facade.return_value = mock_context_facade
            
            # Act
            result = controller._include_project_branch_task_context(
                test_response, 
                real_git_branch_data["project_id"],  # project_id
                real_git_branch_data["id"],          # git_branch_id
                real_task_data["id"]                 # task_id
            )
            
            # Debug output
            print(f"DEBUG: Task result keys: {list(result.keys())}")
            print(f"DEBUG: Has project_context: {'project_context' in result}")
            print(f"DEBUG: Has branch_context: {'branch_context' in result}")
            print(f"DEBUG: Has task_context: {'task_context' in result}")
            
            # Check what calls were made
            calls = mock_context_facade.get_context.call_args_list
            print(f"DEBUG: All context facade calls:")
            for i, call in enumerate(calls):
                print(f"  {i+1}. {call}")
            
            # Assert
            assert result["success"] is True
            assert "task" in result
            assert "project_context" in result, f"project_context missing from task result"
            assert "branch_context" in result, f"branch_context missing from task result"
            assert "task_context" in result, f"task_context missing from task result"

    def test_real_world_context_issue_reproduction(self):
        """
        TEST: Try to reproduce the actual issue we're seeing in production
        
        This test will help us understand why contexts are missing in real scenarios
        """
        # This will use the actual MCP tool calls to reproduce the issue
        # For now, just a placeholder to be implemented once we identify the root cause
        pass