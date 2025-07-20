"""
TDD tests for ensuring proper differentiation between branch and task context resolution.
This test suite ensures that the context resolution system correctly handles different
context levels and prevents the issue where branch IDs are resolved as task contexts.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock

from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task, 
    GlobalContext, ProjectContext, BranchContext, TaskContext
)
from fastmcp.task_management.interface.controllers.unified_context_controller import (
    UnifiedContextMCPController
)
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel
from fastmcp.task_management.application.factories.unified_context_facade_factory import (
    UnifiedContextFacadeFactory
)
from fastmcp.task_management.infrastructure.database.database_config import get_session


class TestContextResolutionDifferentiation:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                # Clean up in dependency order to avoid foreign key errors
                session.execute(text("DELETE FROM task_contexts WHERE task_id LIKE 'test-%'"))
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("""
                    DELETE FROM branch_contexts 
                    WHERE branch_id IN (
                        SELECT id FROM project_git_branchs 
                        WHERE project_id LIKE 'test-%' OR id LIKE 'test-%'
                    )
                """))
                session.execute(text("DELETE FROM project_git_branchs WHERE project_id LIKE 'test-%' OR id LIKE 'test-%'"))
                session.execute(text("DELETE FROM project_contexts WHERE project_id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                
                # Clean up any test global contexts (but preserve global_singleton)
                session.execute(text("DELETE FROM global_contexts WHERE id LIKE 'test-%'"))
                session.commit()
            except Exception as e:
                print(f"Cleanup error: {e}")
                session.rollback()

    """Test suite for verifying correct context resolution by level."""
    
    def _get_manage_context_tool(self, controller):
        """Helper method to register tools and get manage_context function."""
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        return tools["manage_context"]
    
    @pytest.fixture
    def unified_context_controller(self):
        """Create unified context controller for testing."""
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        return UnifiedContextMCPController(factory)
    
    @pytest.fixture
    def setup_test_data(self):
        """Set up test data with project, branch, and task."""
        db_session = get_session()
        
        # Create project
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project Alpha",
            description="Test project for context resolution",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(project)
        
        # Create branch
        branch = ProjectGitBranch(
            id=str(uuid.uuid4()),  # Use dynamic UUID instead of hardcoded
            project_id=project.id,
            name=f"test-feature-{uuid.uuid4().hex[:8]}",
            description="Authentication system feature branch",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(branch)
        
        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            git_branch_id=branch.id,
            title="Implement login functionality",
            description="Create login form and validation",
            status="todo",
            priority="high",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(task)
        
        # Create contexts at different levels
        # Global context
        # Check if global_singleton exists first
        existing_global = db_session.query(GlobalContext).filter_by(id="global_singleton").first()
        if existing_global:
            global_context = existing_global
        else:
            global_context = GlobalContext(
                id="global_singleton",
                organization_id="DhafnckMCP Corp",
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
            local_standards={"project_name": project.name},
            global_overrides={},
            delegation_rules={},
            created_at=datetime.utcnow(),
            version=1,
            updated_at=datetime.utcnow()
        )
        db_session.add(project_context)
        
        # Branch context
        branch_context = BranchContext(
            branch_id=branch.id,
            parent_project_id=project.id,
            parent_project_context_id=project.id,
            branch_workflow={},
            branch_standards={"branch_name": branch.name},
            agent_assignments={},
            local_overrides={},
            delegation_rules={},
            updated_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            version=1
        )
        db_session.add(branch_context)
        
        # Task context
        task_context = TaskContext(
            task_id=task.id,
            parent_branch_id=branch.id,
            parent_branch_context_id=branch.id,
            task_data={"task_title": task.title},
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            created_at=datetime.utcnow(),
            version=1,
            updated_at=datetime.utcnow()
        )
        db_session.add(task_context)
        
        db_session.commit()
        
        data = {
            "project": project,
            "branch": branch,
            "task": task,
            "project_id": project.id,
            "branch_id": branch.id,
            "task_id": task.id
        }
        
        yield data
        
        # Cleanup
        db_session.rollback()
        db_session.close()
    
    def test_resolve_branch_context_with_branch_level(self, setup_test_data, unified_context_controller):
        """Test that branch ID is correctly resolved when level is 'branch'."""
        # Arrange
        branch_id = setup_test_data["branch_id"]
        
        # Act
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="branch",
            context_id=branch_id,
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is True
        assert "data" in result
        assert "resolved_context" in result["data"]
        resolved_context = result["data"]["resolved_context"]
        assert resolved_context["id"] == branch_id
        assert "branch_settings" in resolved_context
        assert resolved_context["branch_settings"]["branch_standards"]["branch_name"] == setup_test_data["branch"].name
    
    def test_resolve_task_context_with_task_level(self, setup_test_data, unified_context_controller):
        """Test that task ID is correctly resolved when level is 'task'."""
        # Arrange
        task_id = setup_test_data["task_id"]
        
        # Act
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="task",
            context_id=task_id,
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is True
        assert "data" in result
        assert "resolved_context" in result["data"]
        resolved_context = result["data"]["resolved_context"]
        assert resolved_context["id"] == task_id
        assert "task_data" in resolved_context or "task_settings" in resolved_context
        if "task_data" in resolved_context:
            assert resolved_context["task_data"]["task_title"] == "Implement login functionality"
        else:
            assert resolved_context["task_settings"]["task_data"]["task_title"] == "Implement login functionality"
    
    def test_branch_id_fails_with_task_level(self, setup_test_data, unified_context_controller):
        """Test that using branch ID with task level fails appropriately."""
        # Arrange
        branch_id = setup_test_data["branch_id"]
        
        # Act
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="task",
            context_id=branch_id,
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "not found" in str(result["error"]).lower()
    
    def test_task_id_fails_with_branch_level(self, setup_test_data, unified_context_controller):
        """Test that using task ID with branch level fails appropriately."""
        # Arrange
        task_id = setup_test_data["task_id"]
        
        # Act
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="branch",
            context_id=task_id,
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "not found" in str(result["error"]).lower()
    
    def test_auto_level_detection_for_branch(self, setup_test_data, unified_context_controller):
        """Test that branch ID is auto-detected as branch level when level not specified."""
        # Arrange
        branch_id = setup_test_data["branch_id"]
        
        # Act - Using get action with explicit level
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="get",
            context_id=branch_id,
            level="branch",
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is True
        assert "data" in result
        assert "context_data" in result["data"]
        context_data = result["data"]["context_data"]
        assert context_data["id"] == branch_id
    
    def test_auto_level_detection_for_task(self, setup_test_data, unified_context_controller):
        """Test that task ID is auto-detected as task level when level not specified."""
        # Arrange
        task_id = setup_test_data["task_id"]
        
        # Act - Using get action which should auto-detect level
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="get",
            context_id=task_id,
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is True
        assert "data" in result
        assert "context_data" in result["data"]
        context_data = result["data"]["context_data"]
        assert context_data["id"] == task_id
    
    def test_context_inheritance_from_branch_to_task(self, setup_test_data, unified_context_controller):
        """Test that task context properly inherits from branch context."""
        # Arrange
        task_id = setup_test_data["task_id"]
        
        # Act
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="task",
            context_id=task_id,
            include_inherited=True
        )
        
        # Assert
        assert result["success"] is True
        assert "data" in result
        assert "resolved_context" in result["data"]
        resolved_context = result["data"]["resolved_context"]
        
        # Check inheritance chain through _inheritance metadata
        assert "_inheritance" in resolved_context
        assert resolved_context["_inheritance"]["chain"] == ["global", "project", "branch", "task"]
        assert resolved_context["_inheritance"]["inheritance_depth"] == 4
        # Branch data should be inherited
        assert "branch_standards" in resolved_context
    
    def test_manage_context_backward_compatibility_branch(self, setup_test_data):
        """Test that manage_context tool properly handles branch contexts for backward compatibility."""
        from fastmcp.task_management.interface.controllers.unified_context_controller import (
            UnifiedContextMCPController
        )
        from fastmcp.task_management.application.factories.unified_context_facade_factory import (
            UnifiedContextFacadeFactory
        )
        
        # Create controller
        factory = UnifiedContextFacadeFactory()  # Use default session factory
        controller = UnifiedContextMCPController(factory)
        
        # Test branch context resolution
        branch_id = setup_test_data["branch_id"]
        manage_context = self._get_manage_context_tool(controller)
        result = manage_context(
            action="resolve",
            level="branch",
            context_id=branch_id
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "resolved_context" in result["data"]
        assert result["data"]["resolved_context"]["id"] == branch_id
    
    def test_error_message_clarity_for_wrong_level(self, setup_test_data, unified_context_controller):
        """Test that error messages clearly indicate level mismatch."""
        # Arrange
        branch_id = setup_test_data["branch_id"]
        
        # Act - Try to resolve branch ID as task
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="task",
            context_id=branch_id
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        # Error should be clear about context not found at task level
        assert "task" in str(result["error"]).lower() or "not found" in str(result["error"]).lower()
    
    def test_frontend_api_pattern_branch_context(self, setup_test_data, unified_context_controller):
        """Test the exact pattern used by frontend getBranchContext function."""
        # This simulates the exact API call from frontend
        branch_id = setup_test_data["branch_id"]
        
        # Simulate frontend API call pattern
        manage_context = self._get_manage_context_tool(unified_context_controller)
        result = manage_context(
            action="resolve",
            level="branch",
            context_id=branch_id,
            force_refresh=False,
            include_inherited=True
        )
        
        # Assert successful resolution
        assert result["success"] is True
        assert "data" in result
        assert "resolved_context" in result["data"]
        resolved_context = result["data"]["resolved_context"]
        assert resolved_context["id"] == branch_id
        
        # Verify inheritance is included through _inheritance metadata
        assert "_inheritance" in resolved_context
        assert resolved_context["_inheritance"]["chain"] == ["global", "project", "branch"]
        assert resolved_context["_inheritance"]["inheritance_depth"] == 3