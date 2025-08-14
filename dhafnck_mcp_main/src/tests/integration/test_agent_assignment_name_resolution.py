"""
Integration tests for agent assignment with name resolution support.

This test file validates that agent assignment works with:
1. UUID format (existing functionality)
2. @prefixed agent names (new functionality)  
3. Agent names without @ prefix (new functionality)
"""

import pytest
import uuid
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController
from fastmcp.task_management.application.factories.git_branch_facade_factory import GitBranchFacadeFactory
from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
from fastmcp.task_management.application.factories.agent_facade_factory import AgentFacadeFactory


class TestAgentAssignmentNameResolution:
    """Test agent assignment with user-friendly name resolution"""
    
    @pytest.fixture
    def project_id(self) -> str:
        """Create a test project and return its ID"""
        import asyncio
        import threading
        
        project_facade = ProjectFacadeFactory().create_project_facade()
        
        # Handle async project creation in a sync test
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(
                    project_facade.create_project("test-agent-assignment", "Test project for agent assignment")
                )
                new_loop.close()
            except Exception as e:
                exception = e
                if new_loop:
                    new_loop.close()
        
        thread = threading.Thread(target=run_in_new_loop)
        thread.start()
        thread.join()
        
        if exception:
            raise exception
            
        assert result["success"], f"Failed to create project: {result.get('error')}"
        return result["project"]["id"]
    
    @pytest.fixture  
    def git_branch_id(self, project_id: str) -> str:
        """Create a test git branch and return its ID"""
        git_branch_facade = GitBranchFacadeFactory().create_git_branch_facade(project_id=project_id)
        result = git_branch_facade.create_git_branch(project_id, "feature/test-branch", "Test branch for agent assignment")
        assert result["success"], f"Failed to create branch: {result.get('error')}"
        return result["git_branch"]["id"]
    
    @pytest.fixture
    def controller(self) -> GitBranchMCPController:
        """Create a GitBranchMCPController instance"""
        factory = GitBranchFacadeFactory()
        return GitBranchMCPController(factory)
    
    def test_resolve_agent_identifier_uuid_format(self, controller: GitBranchMCPController, project_id: str):
        """Test that UUID format is preserved as-is"""
        test_uuid = str(uuid.uuid4())
        resolved_id = controller._resolve_agent_identifier(project_id, test_uuid)
        
        assert resolved_id == test_uuid, f"UUID should be preserved as-is, got: {resolved_id}"
    
    def test_resolve_agent_identifier_prefixed_name(self, controller: GitBranchMCPController, project_id: str):
        """Test that @prefixed agent names are preserved as-is"""
        agent_name = "@coding_agent"
        resolved_id = controller._resolve_agent_identifier(project_id, agent_name)
        
        assert resolved_id == agent_name, f"@prefixed name should be preserved, got: {resolved_id}"
    
    def test_resolve_agent_identifier_unprefixed_name(self, controller: GitBranchMCPController, project_id: str):
        """Test that unprefixed agent names get @ prefix added"""
        agent_name = "coding_agent"
        expected_resolved = "@coding_agent"
        resolved_id = controller._resolve_agent_identifier(project_id, agent_name)
        
        assert resolved_id == expected_resolved, f"Unprefixed name should get @ prefix, got: {resolved_id}"
    
    def test_assign_agent_with_uuid(self, controller: GitBranchMCPController, project_id: str, git_branch_id: str):
        """Test agent assignment using UUID format (existing functionality)"""
        # Register agent first to get UUID
        agent_facade = AgentFacadeFactory().create_agent_facade(project_id=project_id)
        agent_uuid = str(uuid.uuid4())
        register_result = agent_facade.register_agent(project_id, agent_uuid, "Test UUID Agent")
        assert register_result["success"], f"Failed to register agent: {register_result.get('error')}"
        
        # Assign agent using UUID
        result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_id=git_branch_id,
            agent_id=agent_uuid
        )
        
        assert result["success"], f"Agent assignment with UUID failed: {result.get('error')}"
        assert result["agent_id"] == agent_uuid, f"Expected agent_id to be {agent_uuid}, got: {result.get('agent_id')}"
        assert result["original_agent_id"] == agent_uuid, "original_agent_id should match input"
    
    def test_assign_agent_with_prefixed_name(self, controller: GitBranchMCPController, project_id: str, git_branch_id: str):
        """Test agent assignment using @prefixed agent name (new functionality)"""
        agent_name = "@test_coding_agent"
        
        result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_id=git_branch_id,
            agent_id=agent_name
        )
        
        assert result["success"], f"Agent assignment with @prefixed name failed: {result.get('error')}"
        assert result["agent_id"] == agent_name, f"Expected agent_id to be {agent_name}, got: {result.get('agent_id')}"
        assert result["original_agent_id"] == agent_name, "original_agent_id should match input"
    
    def test_assign_agent_with_unprefixed_name(self, controller: GitBranchMCPController, project_id: str, git_branch_id: str):
        """Test agent assignment using unprefixed agent name (new functionality)"""
        agent_name = "test_ui_agent"
        expected_resolved = "@test_ui_agent"
        
        result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_id=git_branch_id,
            agent_id=agent_name
        )
        
        assert result["success"], f"Agent assignment with unprefixed name failed: {result.get('error')}"
        assert result["agent_id"] == expected_resolved, f"Expected agent_id to be {expected_resolved}, got: {result.get('agent_id')}"
        assert result["original_agent_id"] == agent_name, "original_agent_id should match input"
    
    def test_unassign_agent_with_prefixed_name(self, controller: GitBranchMCPController, project_id: str, git_branch_id: str):
        """Test agent unassignment using @prefixed agent name"""
        agent_name = "@test_debugger_agent"
        
        # First assign the agent
        assign_result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_id=git_branch_id,
            agent_id=agent_name
        )
        assert assign_result["success"], f"Failed to assign agent: {assign_result.get('error')}"
        
        # Then unassign using the same name format
        result = controller.manage_git_branch(
            action="unassign_agent",
            project_id=project_id,
            git_branch_id=git_branch_id,
            agent_id=agent_name
        )
        
        assert result["success"], f"Agent unassignment with @prefixed name failed: {result.get('error')}"
        assert result["agent_id"] == agent_name, f"Expected agent_id to be {agent_name}, got: {result.get('agent_id')}"
        assert result["original_agent_id"] == agent_name, "original_agent_id should match input"
    
    def test_assign_agent_with_branch_name(self, controller: GitBranchMCPController, project_id: str):
        """Test agent assignment using branch name instead of branch ID"""
        # Create a test branch with a specific name
        git_branch_facade = GitBranchFacadeFactory().create_git_branch_facade(project_id=project_id)
        branch_result = git_branch_facade.create_git_branch(project_id, "feature/agent-test", "Branch for agent assignment test")
        assert branch_result["success"], f"Failed to create branch: {branch_result.get('error')}"
        
        agent_name = "@branch_test_agent"
        branch_name = "feature/agent-test"
        
        result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_name=branch_name,
            agent_id=agent_name
        )
        
        assert result["success"], f"Agent assignment with branch name failed: {result.get('error')}"
        assert result["agent_id"] == agent_name, f"Expected agent_id to be {agent_name}, got: {result.get('agent_id')}"
        assert result["git_branch_name"] == branch_name, f"Expected branch_name to be {branch_name}, got: {result.get('git_branch_name')}"
        assert result["original_agent_id"] == agent_name, "original_agent_id should match input"
    
    def test_error_handling_invalid_branch(self, controller: GitBranchMCPController, project_id: str):
        """Test error handling when branch doesn't exist"""
        result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_name="non-existent-branch",
            agent_id="@test_agent"
        )
        
        assert not result["success"], "Assignment to non-existent branch should fail"
        assert result["error_code"] == "BRANCH_NOT_FOUND", f"Expected BRANCH_NOT_FOUND error code, got: {result.get('error_code')}"
        assert "non-existent-branch" in result["error"], "Error message should mention the branch name"
    
    def test_response_includes_tracking_fields(self, controller: GitBranchMCPController, project_id: str, git_branch_id: str):
        """Test that response includes both resolved and original agent identifiers"""
        original_agent_id = "tracking_test_agent"
        expected_resolved = "@tracking_test_agent"
        
        result = controller.manage_git_branch(
            action="assign_agent",
            project_id=project_id,
            git_branch_id=git_branch_id,
            agent_id=original_agent_id
        )
        
        assert result["success"], f"Agent assignment failed: {result.get('error')}"
        
        # Verify tracking fields are present
        assert "agent_id" in result, "Response should include resolved agent_id"
        assert "original_agent_id" in result, "Response should include original_agent_id"
        assert "action" in result, "Response should include action"
        
        # Verify values are correct
        assert result["agent_id"] == expected_resolved, f"Expected resolved agent_id to be {expected_resolved}"
        assert result["original_agent_id"] == original_agent_id, f"Expected original_agent_id to be {original_agent_id}"
        assert result["action"] == "assign_agent", "Action should be assign_agent"
    
    def test_edge_cases_empty_and_special_characters(self, controller: GitBranchMCPController, project_id: str):
        """Test edge cases with empty strings and special characters"""
        # Test with edge case agent names (these should work since they'll be auto-registered)
        edge_cases = [
            "@agent-with-dashes",
            "@agent_with_underscores", 
            "agent123",
            "@agent.with.dots"
        ]
        
        git_branch_facade = GitBranchFacadeFactory().create_git_branch_facade(project_id=project_id)
        
        for i, agent_name in enumerate(edge_cases):
            # Create a unique branch for each test
            branch_name = f"test-edge-case-{i}"
            branch_result = git_branch_facade.create_git_branch(project_id, branch_name, f"Branch for edge case test {i}")
            assert branch_result["success"], f"Failed to create branch {branch_name}"
            
            branch_id = branch_result["git_branch"]["id"]
            
            result = controller.manage_git_branch(
                action="assign_agent",
                project_id=project_id,
                git_branch_id=branch_id,
                agent_id=agent_name
            )
            
            # These should succeed due to auto-registration in the agent repository
            assert result["success"], f"Assignment with edge case agent name '{agent_name}' failed: {result.get('error')}"
            
            # Verify the resolution logic worked correctly
            if agent_name.startswith('@'):
                assert result["agent_id"] == agent_name, f"@prefixed name should be preserved"
            else:
                assert result["agent_id"] == f"@{agent_name}", f"Unprefixed name should get @ prefix"