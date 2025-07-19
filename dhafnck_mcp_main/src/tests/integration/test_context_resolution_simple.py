"""
Simple integration test for context resolution differentiation.
This test verifies that branch and task contexts are properly differentiated.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock

from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task, 
    GlobalContext, ProjectContext, BranchContext, TaskContext
)
from fastmcp.task_management.interface.controllers.unified_context_controller import (
    UnifiedContextMCPController
)
from fastmcp.task_management.application.factories.unified_context_facade_factory import (
    UnifiedContextFacadeFactory
)


class TestContextResolutionSimple:
    """Simple test for context resolution."""
    
    def test_branch_context_resolution(self):
        """Test that branch contexts are resolved correctly with level='branch'."""
        # Get a database session
        db_session = get_session()
        
        try:
            # Create test data
            project = Project(
                id=str(uuid.uuid4()),
                name="Test Project",
                description="Test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(project)
            
            # The problematic branch ID from the issue
            branch_id = "d4f91ee3-1f97-4768-b4ff-1e734180f874"
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project.id,
                name="feature/auth-system",
                description="Auth feature",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(branch)
            
            # Create global context first (required for hierarchy)
            global_context = GlobalContext(
                id="global_singleton",
                organization_id="TestOrg",
                autonomous_rules={},
                security_policies={},
                coding_standards={},
                workflow_templates={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(global_context)
            
            # Create project context (required for branch context)
            project_context = ProjectContext(
                project_id=project.id,
                team_preferences={},
                technology_stack={},
                project_workflow={},
                local_standards={},
                global_overrides={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(project_context)
            
            # Create branch context
            branch_context = BranchContext(
                branch_id=branch_id,
                parent_project_id=project.id,
                parent_project_context_id=project.id,
                branch_workflow={},
                branch_standards={"branch_name": branch.name},
                agent_assignments={},
                local_overrides={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(branch_context)
            
            db_session.commit()
            
            # Create controller
            factory = UnifiedContextFacadeFactory()  # Use default session factory
            controller = UnifiedContextMCPController(factory)
            
            # Test: Resolve branch context with correct level
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
            
            result = manage_context(
                action="resolve",
                level="branch",
                context_id=branch_id,
                include_inherited=True
            )
            
            # Assertions
            assert result["success"] is True
            assert "data" in result
            assert "resolved_context" in result["data"]
            resolved_context = result["data"]["resolved_context"]
            
            assert resolved_context["id"] == branch_id
            
            # Debug: Print entire resolved context to understand structure
            print(f"\nDEBUG: Full resolved context keys: {list(resolved_context.keys())}")
            print(f"DEBUG: Full resolved context: {resolved_context}")
            
            # When include_inherited=True, data is flattened but some fields are nested
            # Check branch-specific fields - they are under branch_settings
            assert "branch_settings" in resolved_context
            assert "branch_standards" in resolved_context["branch_settings"]
            assert resolved_context["branch_settings"]["branch_standards"]["branch_name"] == "feature/auth-system"
            
            # Check that inherited data is included
            # From global context  
            assert "organization_name" in resolved_context
            assert resolved_context["organization_name"] == "TestOrg"
            assert "global_settings" in resolved_context
            
            # From project context - these are flattened at the top level
            assert "team_preferences" in resolved_context
            assert "technology_stack" in resolved_context
            assert "project_workflow" in resolved_context
            assert "local_standards" in resolved_context
            
            # From branch context - these are flattened at the top level
            assert "branch_workflow" in resolved_context
            assert "branch_standards" in resolved_context  # Empty at top level
            assert "agent_assignments" in resolved_context
            
            # Check inheritance metadata
            assert "_inheritance" in resolved_context
            assert resolved_context["_inheritance"]["chain"] == ["global", "project", "branch"]
            assert resolved_context["_inheritance"]["inheritance_depth"] == 3
            
            # Test: Wrong level should fail
            result_wrong = manage_context(
                action="resolve",
                level="task",  # Wrong level!
                context_id=branch_id,
                include_inherited=True
            )
            
            assert result_wrong["success"] is False
            assert "error" in result_wrong
            
        finally:
            db_session.rollback()
            db_session.close()
    
    def test_task_context_resolution(self):
        """Test that task contexts are resolved correctly with level='task'."""
        # Get a database session
        db_session = get_session()
        
        try:
            # Create test data
            project = Project(
                id=str(uuid.uuid4()),
                name="Test Project",
                description="Test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(project)
            
            branch = ProjectGitBranch(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name="main",
                description="Main branch",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(branch)
            
            task = Task(
                id=str(uuid.uuid4()),
                git_branch_id=branch.id,
                title="Test Task",
                description="Test",
                status="todo",
                priority="medium",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(task)
            
            # Create necessary parent contexts for hierarchy
            # Global context
            global_context = GlobalContext(
                id="global_singleton",
                organization_id="TestOrg",
                autonomous_rules={},
                security_policies={},
                coding_standards={},
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
                technology_stack={},
                project_workflow={},
                local_standards={},
                global_overrides={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(project_context)
            
            # Branch context (required for task context FK)
            branch_context = BranchContext(
                branch_id=branch.id,
                parent_project_id=project.id,
                parent_project_context_id=project.id,
                branch_workflow={},
                branch_standards={},
                agent_assignments={},
                local_overrides={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(branch_context)
            
            # Create task context
            task_context = TaskContext(
                task_id=task.id,
                parent_branch_id=branch.id,
                parent_branch_context_id=branch.id,
                task_data={"task_title": task.title},
                local_overrides={},
                implementation_notes={},
                delegation_triggers={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(task_context)
            
            db_session.commit()
            
            # Create controller
            factory = UnifiedContextFacadeFactory()  # Use default session factory
            controller = UnifiedContextMCPController(factory)
            
            # Test: Resolve task context with correct level
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
            
            result = manage_context(
                action="resolve",
                level="task",
                context_id=task.id,
                include_inherited=True
            )
            
            # Assertions
            assert result["success"] is True
            assert "data" in result
            assert "resolved_context" in result["data"]
            resolved_context = result["data"]["resolved_context"]
            
            assert resolved_context["id"] == task.id
            # Task data should be available in the resolved context
            assert "task_data" in resolved_context or "task_settings" in resolved_context
            # The task title could be in task_data or task_settings
            if "task_data" in resolved_context and "task_title" in resolved_context["task_data"]:
                assert resolved_context["task_data"]["task_title"] == "Test Task"
            elif "task_settings" in resolved_context:
                assert resolved_context["task_settings"]["task_data"]["task_title"] == "Test Task"
            
        finally:
            db_session.rollback()
            db_session.close()
    
    def test_frontend_api_pattern_for_branches(self):
        """Test the exact API pattern used by frontend for branches."""
        # Get a database session  
        db_session = get_session()
        
        try:
            # Create test data
            project = Project(
                id=str(uuid.uuid4()),
                name="test-project-alpha",  # Same as frontend
                description="Test",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(project)
            
            # The exact branch ID from the issue
            branch_id = "d4f91ee3-1f97-4768-b4ff-1e734180f874"
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project.id,
                name="feature/auth-system",
                description="Authentication system",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(branch)
            
            # Create all contexts for proper hierarchy
            # Global
            global_ctx = GlobalContext(
                id="global_singleton",
                organization_id="DhafnckMCP",
                autonomous_rules={},
                security_policies={},
                coding_standards={},
                workflow_templates={"_custom": {"org": "DhafnckMCP"}},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(global_ctx)
            
            # Project
            project_ctx = ProjectContext(
                project_id=project.id,
                team_preferences={},
                technology_stack={},
                project_workflow={},
                local_standards={"_custom": {"project_name": project.name}},
                global_overrides={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(project_ctx)
            
            # Branch
            branch_ctx = BranchContext(
                branch_id=branch_id,
                parent_project_id=project.id,
                parent_project_context_id=project.id,
                branch_workflow={},
                branch_standards={"branch_name": branch.name},
                agent_assignments={},
                local_overrides={},
                delegation_rules={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(branch_ctx)
            
            db_session.commit()
            
            # Create controller
            factory = UnifiedContextFacadeFactory()  # Use default session factory
            controller = UnifiedContextMCPController(factory)
            
            # Test: Exact frontend API call
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
            
            result = manage_context(
                action="resolve",
                level="branch",
                context_id=branch_id,
                force_refresh=False,
                include_inherited=True
            )
            
            # Assertions - This should succeed now
            assert result["success"] is True, f"Failed: {result.get('error', 'Unknown error')}"
            assert "data" in result
            assert "resolved_context" in result["data"]
            resolved_context = result["data"]["resolved_context"]
            
            assert resolved_context["id"] == branch_id
            
            # Verify inheritance through _inheritance metadata
            assert "_inheritance" in resolved_context
            assert resolved_context["_inheritance"]["chain"] == ["global", "project", "branch"]
            
            # Verify branch data is available
            assert "branch_settings" in resolved_context
            assert resolved_context["branch_settings"]["branch_standards"]["branch_name"] == branch.name
            
        finally:
            db_session.rollback()
            db_session.close()