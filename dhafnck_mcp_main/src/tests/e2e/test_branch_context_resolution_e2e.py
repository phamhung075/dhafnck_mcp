"""
End-to-end test for branch context resolution issue.
This test simulates the exact scenario that caused the error:
- Frontend calling context resolution with a branch ID
- Backend attempting to resolve it as the wrong context level
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock

from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task,
    GlobalContext, ProjectContext, BranchContext, TaskContext
)
from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel
from fastmcp.task_management.infrastructure.database.database_config import get_session


class TestBranchContextResolutionE2E:
    """End-to-end test for the branch context resolution issue."""
    
    @pytest.fixture
    def setup_production_like_data(self):
        """Set up data that mimics production scenario."""
        db_session = get_session()
        # Create project - mimicking "test-project-alpha"
        project = Project(
            id=str(uuid.uuid4()),
            name="test-project-alpha",
            description="Production-like test project",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(project)
        
        # Create branch with the exact problematic ID
        branch = ProjectGitBranch(
            id="d4f91ee3-1f97-4768-b4ff-1e734180f874",
            project_id=project.id,
            name="feature/auth-system",
            description="Authentication system implementation",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(branch)
        
        # Create some tasks in the branch
        task1 = Task(
            id=str(uuid.uuid4()),
            git_branch_id=branch.id,
            title="Create login form",
            description="Design and implement login UI",
            status="in_progress",
            priority="high",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(task1)
        
        task2 = Task(
            id=str(uuid.uuid4()),
            git_branch_id=branch.id,
            title="Implement JWT tokens",
            description="Add JWT token generation and validation",
            status="todo",
            priority="high",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(task2)
        
        # Create the full context hierarchy
        # Global context
        global_context = GlobalContext(
            id="global_singleton",
            organization_id="DhafnckMCP Corporation",
            autonomous_rules={},
            security_policies={},
            coding_standards={"code_style": "PEP8", "testing": "TDD"},
            workflow_templates={},
            delegation_rules={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(global_context)
        
        # Project context
        project_context = ProjectContext(
            project_id=project.id,
            team_preferences={},
            technology_stack={"stack": ["Python", "FastAPI", "React", "TypeScript"]},
            project_workflow={},
            local_standards={"_custom": {"project_name": project.name, "team_size": 5}},
            global_overrides={},
            delegation_rules={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(project_context)
        
        # Branch context - this is what was failing to resolve
        branch_context = BranchContext(
            branch_id=branch.id,
            parent_project_id=project.id,
            parent_project_context_id=project.id,
            branch_workflow={},
            branch_standards={"_custom": {
                "branch_name": branch.name,
                "feature_scope": "Authentication and authorization",
                "estimated_completion": "2 weeks"
            }},
            agent_assignments={},
            local_overrides={},
            delegation_rules={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(branch_context)
        
        # Task contexts
        task1_context = TaskContext(
            task_id=task1.id,
            parent_branch_id=branch.id,
            parent_branch_context_id=branch.id,
            task_data={
                "task_title": task1.title,
                "assigned_to": "frontend_team",
                "progress": 60
            },
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(task1_context)
        
        db_session.commit()
        
        data = {
            "project": project,
            "branch": branch,
            "tasks": [task1, task2],
            "branch_id": branch.id,
            "project_id": project.id
        }
        
        yield data
        
        # Cleanup
        db_session.rollback()
        db_session.close()
    
    def test_frontend_branch_context_resolution_pattern(self, setup_production_like_data):
        """Test the exact frontend pattern that was failing."""
        # Create controller
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        controller = UnifiedContextMCPController(factory)
        
        # Register tools to get the manage_context function
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        manage_context = tools["manage_context"]
        
        # Simulate the exact frontend API call pattern
        # This is what getBranchContext() sends
        result = manage_context(
            action="resolve",
            level="branch",
            context_id="d4f91ee3-1f97-4768-b4ff-1e734180f874",
            force_refresh=False,
            include_inherited=True
        )
        
        # Assert - This should now succeed
        assert result["success"] is True
        assert "data" in result
        assert "resolved_context" in result["data"]
        
        resolved_context = result["data"]["resolved_context"]
        assert resolved_context["id"] == "d4f91ee3-1f97-4768-b4ff-1e734180f874"
        
        # Verify inheritance through _inheritance metadata
        assert "_inheritance" in resolved_context
        assert resolved_context["_inheritance"]["chain"] == ["global", "project", "branch"]
        
        # Verify branch data is available
        assert "branch_settings" in resolved_context
        assert "branch_standards" in resolved_context["branch_settings"]
        
        # Project name should be inherited
        assert "project_name" in resolved_context or "local_standards" in resolved_context
    
    def test_old_pattern_that_was_failing(self, setup_production_like_data):
        """Test the old pattern that was incorrectly trying to resolve branch as task."""
        # Create controller
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        controller = UnifiedContextMCPController(factory)
        
        # Register tools to get the manage_context function
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        manage_context = tools["manage_context"]
        
        # This is what the frontend was incorrectly doing before the fix
        # Using getTaskContext for a branch ID
        result = manage_context(
            action="get",
            context_id="d4f91ee3-1f97-4768-b4ff-1e734180f874",  # Branch ID!
            level="task"  # Wrong level!
        )
        
        # This should fail because it's looking for a task context with a branch ID
        assert result["success"] is False
        assert "error" in result
        assert "not found" in str(result["error"]).lower()
    
    def test_correct_task_context_resolution(self, setup_production_like_data):
        """Test that task context resolution still works correctly."""
        # Create controller
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        controller = UnifiedContextMCPController(factory)
        
        # Register tools to get the manage_context function
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        manage_context = tools["manage_context"]
        
        # Get a real task ID
        task_id = setup_production_like_data["tasks"][0].id
        
        # Resolve task context
        result = manage_context(
            action="get",
            context_id=task_id,
            level="task"
        )
        
        # Assert success
        assert result["success"] is True
        assert "data" in result
        assert "context_data" in result["data"]
        
        context_data = result["data"]["context_data"]
        assert context_data["id"] == task_id
        assert "task_data" in context_data or "task_settings" in context_data
        
        # Task title could be in task_data or task_settings
        if "task_data" in context_data:
            assert context_data["task_data"]["task_title"] == "Create login form"
        elif "task_settings" in context_data:
            assert context_data["task_settings"]["task_data"]["task_title"] == "Create login form"
    
    def test_list_contexts_at_different_levels(self, setup_production_like_data):
        """Test listing contexts at different hierarchy levels."""
        # Create controller
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        controller = UnifiedContextMCPController(factory)
        
        # Register tools to get the manage_context function
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        manage_context = tools["manage_context"]
        
        # List branch contexts
        branch_result = manage_context(
            action="list",
            level="branch"
        )
        
        assert branch_result["success"] is True
        assert "data" in branch_result
        assert "contexts" in branch_result["data"]
        assert len(branch_result["data"]["contexts"]) >= 1
        assert any(ctx["id"] == "d4f91ee3-1f97-4768-b4ff-1e734180f874" 
                  for ctx in branch_result["data"]["contexts"])
        
        # List task contexts
        task_result = manage_context(
            action="list",
            level="task"
        )
        
        assert task_result["success"] is True
        assert "data" in task_result
        assert "contexts" in task_result["data"]
        # Should have at least one task context
        assert len(task_result["data"]["contexts"]) >= 1
        # But should NOT include the branch ID
        assert not any(ctx["id"] == "d4f91ee3-1f97-4768-b4ff-1e734180f874" 
                      for ctx in task_result["data"]["contexts"])
    
    def test_error_message_improvement(self, setup_production_like_data):
        """Test that error messages are clear when using wrong context level."""
        # Create controller
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        controller = UnifiedContextMCPController(factory)
        
        # Register tools to get the manage_context function
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        manage_context = tools["manage_context"]
        
        # Try to resolve branch ID as task level
        result = manage_context(
            action="resolve",
            level="task",
            context_id="d4f91ee3-1f97-4768-b4ff-1e734180f874",
            include_inherited=True
        )
        
        # Should fail with clear error
        assert result["success"] is False
        assert "error" in result
        # Error should mention that context was not found
        assert "not found" in str(result["error"]).lower()
        
        # Ideally, error could be more specific like:
        # "Context d4f91ee3-1f97-4768-b4ff-1e734180f874 not found at task level. 
        #  This ID exists as a branch context."
        # But current error is sufficient for debugging