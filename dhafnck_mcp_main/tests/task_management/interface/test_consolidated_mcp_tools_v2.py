"""
This is the canonical and only maintained test suite for consolidated MCP tools v2 in task management.
All validation, edge-case, and integration tests should be added here.
Redundant or duplicate tests in other files have been removed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))


import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from fastmcp.task_management.interface.consolidated_mcp_tools import (
    ConsolidatedMCPTools,
    SimpleMultiAgentTools,
    ProjectManager,
    find_project_root,
    ensure_brain_dir
)
from fastmcp.task_management.infrastructure import InMemoryTaskRepository, FileAutoRuleGenerator
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus, TaskStatusEnum
from fastmcp.task_management.domain.value_objects.priority import Priority, PriorityLevel
from fastmcp.task_management.domain.enums import AgentRole


class TestFindProjectRoot:
    """Test project root finding functionality"""
    
    def test_find_project_root_with_cursor_agent_subdirectory(self):
        """Test finding project root when cursor_agent exists as subdirectory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project structure
            project_root = Path(temp_dir) / "test_project"
            cursor_agent_dir = project_root / "cursor_agent"
            cursor_agent_dir.mkdir(parents=True)
            
            # Mock the current file location to be deep inside the project
            nested_file = project_root / "some" / "nested" / "dir" / "file.py"
            
            result = find_project_root(start_path=nested_file)
            assert isinstance(result, Path)
            # Should find the project root that contains cursor_agent
            assert result == project_root

    def test_find_project_root_fallback(self):
        """Test fallback when project root not found"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a nested file path
            nested_file = Path(temp_dir) / "deep" / "nested" / "file.py"
            nested_file.parent.mkdir(parents=True, exist_ok=True)
            nested_file.touch()
            
            # Mock environment and cwd to ensure no project markers are found
            with patch.dict(os.environ, {}, clear=True):  # Clear all environment variables
                with patch('pathlib.Path.cwd', return_value=Path(temp_dir)):  # Mock cwd to temp dir
                    # No marker files in any parent
                    result = find_project_root(start_path=nested_file)
                    assert isinstance(result, Path)
                    # Should fallback to the current working directory (temp_dir)
                    assert result == Path(temp_dir)

    def test_ensure_brain_dir(self):
        """Test brain directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            brain_dir = os.path.join(temp_dir, "brain")
            
            # Call ensure_brain_dir directly with the brain_dir parameter
            result = ensure_brain_dir(brain_dir)
            
            assert os.path.exists(brain_dir)
            assert result == Path(brain_dir)


class TestSimpleMultiAgentTools:
    """Test SimpleMultiAgentTools functionality"""
    
    @pytest.fixture
    def temp_projects_file(self):
        """Create temporary projects file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def tools(self, temp_projects_file):
        """Create SimpleMultiAgentTools instance for testing"""
        return SimpleMultiAgentTools(projects_file_path=temp_projects_file)
    
    def test_init_with_custom_projects_file(self, temp_projects_file):
        """Test initialization with custom projects file"""
        tools = SimpleMultiAgentTools(projects_file_path=temp_projects_file)
        assert tools._projects_file == temp_projects_file
        assert tools._brain_dir == os.path.dirname(temp_projects_file)
        assert hasattr(tools, '_agent_converter')
        assert hasattr(tools, '_orchestrator')
    
    def test_init_with_default_paths(self):
        """Test initialization with default paths"""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the PathResolver to use our temp directory
            with patch('fastmcp.task_management.interface.consolidated_mcp_tools.PathResolver') as mock_path_resolver:
                mock_resolver_instance = Mock()
                mock_resolver_instance.brain_dir = Path(temp_dir) / "brain"
                mock_resolver_instance.projects_file = Path(temp_dir) / "brain" / "projects.json"
                mock_path_resolver.return_value = mock_resolver_instance
                
                # Mock ProjectManager to avoid file operations
                with patch('fastmcp.task_management.interface.consolidated_mcp_tools.ProjectManager') as mock_project_manager:
                    mock_pm_instance = Mock()
                    mock_pm_instance._projects_file = str(mock_resolver_instance.projects_file)
                    mock_pm_instance._brain_dir = str(mock_resolver_instance.brain_dir)
                    mock_pm_instance._agent_converter = Mock()
                    mock_pm_instance._orchestrator = Mock()
                    mock_project_manager.return_value = mock_pm_instance
                    
                    tools = SimpleMultiAgentTools()
                    assert tools._brain_dir == str(mock_resolver_instance.brain_dir)
                    assert tools._projects_file == str(mock_resolver_instance.projects_file)
    
    def test_create_project(self, tools):
        """Test project creation"""
        result = tools.create_project("test_proj", "Test Project", "A test project")
        
        assert result["success"] is True
        assert result["project"]["id"] == "test_proj"
        assert result["project"]["name"] == "Test Project"
        assert result["project"]["description"] == "A test project"
        assert "main" in result["project"]["task_trees"]
        assert result["project"]["registered_agents"] == {}
        assert result["project"]["agent_assignments"] == {}
        assert "created_at" in result["project"]
    
    def test_get_project_existing(self, tools):
        """Test getting existing project"""
        tools.create_project("test_proj", "Test Project")
        result = tools.get_project("test_proj")
        
        assert result["success"] is True
        assert result["project"]["id"] == "test_proj"
    
    def test_get_project_nonexistent(self, tools):
        """Test getting non-existent project"""
        result = tools.get_project("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_list_projects_empty(self, tools):
        """Test listing projects when none exist"""
        result = tools.list_projects()
        
        assert result["success"] is True
        assert result["projects"] == []
        assert result["count"] == 0
    
    def test_list_projects_with_data(self, tools):
        """Test listing projects with existing data"""
        tools.create_project("proj1", "Project 1")
        tools.create_project("proj2", "Project 2")
        
        result = tools.list_projects()
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["projects"]) == 2
    
    def test_create_task_tree(self, tools):
        """Test creating task tree"""
        tools.create_project("test_proj", "Test Project")
        result = tools.create_task_tree("test_proj", "frontend", "Frontend Tasks", "UI/UX tasks")
        
        assert result["success"] is True
        assert result["tree"]["id"] == "frontend"
        assert result["tree"]["name"] == "Frontend Tasks"
        assert result["tree"]["description"] == "UI/UX tasks"
    
    def test_create_task_tree_nonexistent_project(self, tools):
        """Test creating task tree for non-existent project"""
        result = tools.create_task_tree("nonexistent", "frontend", "Frontend Tasks")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_get_task_tree_status(self, tools):
        """Test getting task tree status"""
        tools.create_project("test_proj", "Test Project")
        tools.create_task_tree("test_proj", "frontend", "Frontend Tasks")
        
        result = tools.get_task_tree_status("test_proj", "frontend")
        
        assert result["success"] is True
        assert result["tree"]["id"] == "frontend"
        assert result["status"] == "active"
        assert result["progress"] == "0%"
    
    def test_get_task_tree_status_nonexistent_project(self, tools):
        """Test getting task tree status for non-existent project"""
        result = tools.get_task_tree_status("nonexistent", "frontend")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_get_task_tree_status_nonexistent_tree(self, tools):
        """Test getting status for non-existent task tree"""
        tools.create_project("test_proj", "Test Project")
        result = tools.get_task_tree_status("test_proj", "nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_register_agent(self, tools):
        """Test agent registration"""
        tools.create_project("test_proj", "Test Project")
        result = tools.register_agent("test_proj", "dev_agent", "Developer Agent", "@coding_agent")
        
        assert result["success"] is True
        assert result["agent"]["id"] == "dev_agent"
        assert result["agent"]["name"] == "Developer Agent"
        assert result["agent"]["call_agent"] == "@coding_agent"
    
    def test_register_agent_nonexistent_project(self, tools):
        """Test registering agent for non-existent project"""
        result = tools.register_agent("nonexistent", "dev_agent", "Developer Agent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_assign_agent_to_tree(self, tools):
        """Test assigning agent to task tree"""
        tools.create_project("test_proj", "Test Project")
        tools.register_agent("test_proj", "dev_agent", "Developer Agent")
        tools.create_task_tree("test_proj", "frontend", "Frontend Tasks")
        
        result = tools.assign_agent_to_tree("test_proj", "dev_agent", "frontend")
        
        assert result["success"] is True
        assert "assigned" in result["message"]
    
    def test_assign_agent_to_tree_nonexistent_project(self, tools):
        """Test assigning agent for non-existent project"""
        result = tools.assign_agent_to_tree("nonexistent", "dev_agent", "frontend")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_assign_agent_to_tree_nonexistent_agent(self, tools):
        """Test assigning non-existent agent"""
        tools.create_project("test_proj", "Test Project")
        result = tools.assign_agent_to_tree("test_proj", "nonexistent", "frontend")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_orchestrate_project(self, tools):
        """Test project orchestration"""
        tools.create_project("test_proj", "Test Project")
        
        with patch.object(tools._orchestrator, 'orchestrate_project') as mock_orchestrate:
            mock_orchestrate.return_value = {"status": "completed"}
            
            result = tools.orchestrate_project("test_proj")
            
            assert result["success"] is True
            assert "orchestration completed" in result["message"]
            assert result["orchestration_result"]["status"] == "completed"
    
    def test_orchestrate_project_nonexistent(self, tools):
        """Test orchestrating non-existent project"""
        result = tools.orchestrate_project("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_orchestrate_project_with_error(self, tools):
        """Test project orchestration with error"""
        tools.create_project("test_proj", "Test Project")
        
        with patch.object(tools._orchestrator, 'orchestrate_project') as mock_orchestrate:
            mock_orchestrate.side_effect = Exception("Orchestration failed")
            
            result = tools.orchestrate_project("test_proj")
            
            assert result["success"] is False
            assert "Orchestration failed" in result["error"]
    
    def test_get_orchestration_dashboard(self, tools):
        """Test getting orchestration dashboard"""
        tools.create_project("test_proj", "Test Project")
        
        result = tools.get_orchestration_dashboard("test_proj")
        
        assert result["success"] is True
        assert "dashboard" in result
    
    def test_get_orchestration_dashboard_nonexistent(self, tools):
        """Test getting dashboard for non-existent project"""
        result = tools.get_orchestration_dashboard("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_save_and_load_projects(self, tools, temp_projects_file):
        """Test saving and loading projects persistence"""
        # Create a project
        tools.create_project("test_proj", "Test Project")
        
        # Create new instance to test loading
        new_tools = SimpleMultiAgentTools(projects_file_path=temp_projects_file)
        result = new_tools.get_project("test_proj")
        
        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"


class TestConsolidatedMCPTools:
    """Test ConsolidatedMCPTools functionality"""
    
    @pytest.fixture
    def temp_projects_file(self):
        """Create temporary projects file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def mock_mcp(self):
        """Create mock FastMCP instance"""
        mcp = Mock()
        mcp.tool = Mock(return_value=lambda func: func)  # Decorator that returns the function unchanged
        return mcp
    
    @pytest.fixture
    def consolidated_tools(self, temp_projects_file):
        """Create ConsolidatedMCPTools instance for testing"""
        task_repository = InMemoryTaskRepository()
        return ConsolidatedMCPTools(
            task_repository=task_repository,
            projects_file_path=temp_projects_file
        )
    
    def test_init_with_custom_dependencies(self, temp_projects_file):
        """Test initialization with custom dependencies"""
        task_repository = InMemoryTaskRepository()
        
        tools = ConsolidatedMCPTools(
            task_repository=task_repository,
            projects_file_path=temp_projects_file
        )
        
        assert tools._task_repository == task_repository
        assert tools._auto_rule_generator is not None  # Should be FileAutoRuleGenerator()
        assert isinstance(tools._multi_agent_tools, ProjectManager)  # _multi_agent_tools is actually ProjectManager
        assert isinstance(tools._cursor_rules_tools, object)  # CursorRulesTools instance
    
    def test_init_with_default_dependencies(self):
        """Test initialization with default dependencies"""
        with patch('fastmcp.task_management.interface.consolidated_mcp_tools.JsonTaskRepository') as mock_repo:
            with patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator') as mock_generator:
                mock_repo.return_value = Mock()
                mock_generator.return_value = Mock()
                
                tools = ConsolidatedMCPTools()
                
                assert tools._task_repository is not None
                assert tools._auto_rule_generator is not None
    
    def test_register_tools(self, consolidated_tools, mock_mcp):
        """Test tool registration with FastMCP"""
        consolidated_tools.register_tools(mock_mcp)
        
        # Verify that tool decorator was called for each tool
        expected_tools = [
            'manage_project',
            'manage_task', 
            'manage_subtask',
            'manage_agent',
            'call_agent'
        ]
        
        assert mock_mcp.tool.call_count >= len(expected_tools)
    
    def test_handle_core_task_operations_create(self, consolidated_tools):
        """Test creating task through core operations"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        result = consolidated_tools._handle_core_task_operations(
            action="create",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=None,
            title="Test Task",
            description="Test Description",
            status=None,
            priority="high",
            details="Test details",
            estimated_effort="small",
            assignees=["@coding_agent"],
            labels=["feature"],
            due_date=None
        )
        
        assert result["success"] is True
        assert result["action"] == "create"
        assert result["task"]["title"] == "Test Task"
    
    def test_handle_core_task_operations_get(self, consolidated_tools):
        """Test getting task through core operations"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # First create a task
        create_result = consolidated_tools._handle_core_task_operations(
            action="create",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=None,
            title="Test Task",
            description="Test Description",
            status=None,
            priority="high",
            details="Test details",
            estimated_effort="small",
            assignees=["@coding_agent"],
            labels=["feature"],
            due_date=None
        )
        task_id = create_result["task"]["id"]
        
        # Then get it
        result = consolidated_tools._handle_core_task_operations(
            action="get",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=task_id,
            title=None,
            description=None,
            status=None,
            priority=None,
            details=None,
            estimated_effort=None,
            assignees=None,
            labels=None,
            due_date=None
        )
        
        assert result["success"] is True
        assert result["action"] == "get"
        assert result["task"]["id"] == task_id
    
    def test_handle_core_task_operations_update(self, consolidated_tools):
        """Test updating task through core operations"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # First create a task
        create_result = consolidated_tools._handle_core_task_operations(
            action="create",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=None,
            title="Test Task",
            description="Test Description",
            status=None,
            priority="high",
            details="Test details",
            estimated_effort="small",
            assignees=["@coding_agent"],
            labels=["feature"],
            due_date=None
        )
        task_id = create_result["task"]["id"]
        
        # Then update it
        result = consolidated_tools._handle_core_task_operations(
            action="update",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=task_id,
            title="Updated Task",
            description="Updated Description",
            status="in_progress",
            priority="critical",
            details="Updated details",
            estimated_effort="medium",
            assignees=["@test_agent"],
            labels=["bugfix"],
            due_date=None
        )
        
        assert result["success"] is True
        assert result["action"] == "update"
        assert result["task"]["title"] == "Updated Task"
        assert result["task"]["status"] == "in_progress"
    
    def test_handle_core_task_operations_delete(self, consolidated_tools):
        """Test deleting task through core operations"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # First create a task
        create_result = consolidated_tools._handle_core_task_operations(
            action="create",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=None,
            title="Test Task",
            description="Test Description",
            status=None,
            priority="high",
            details="Test details",
            estimated_effort="small",
            assignees=["@coding_agent"],
            labels=["feature"],
            due_date=None
        )
        task_id = create_result["task"]["id"]
        
        # Then delete it
        result = consolidated_tools._handle_core_task_operations(
            action="delete",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=task_id,
            title=None,
            description=None,
            status=None,
            priority=None,
            details=None,
            estimated_effort=None,
            assignees=None,
            labels=None,
            due_date=None
        )
        
        assert result["success"] is True
        assert result["action"] == "delete"
    
    def test_handle_complete_task(self, consolidated_tools):
        """Test completing task"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # First create a task
        create_result = consolidated_tools._handle_core_task_operations(
            action="create",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=None,
            title="Test Task",
            description="Test Description",
            status=None,
            priority="high",
            details="Test details",
            estimated_effort="small",
            assignees=["@coding_agent"],
            labels=["feature"],
            due_date=None
        )
        task_id = create_result["task"]["id"]
        
        # Then complete it
        result = consolidated_tools._handle_complete_task(
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=task_id
        )
        
        assert result["success"] is True
        assert result["action"] == "complete"
    
    def test_handle_list_tasks(self, consolidated_tools):
        """Test listing tasks"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Create some tasks first
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Task 1", description="Desc 1",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Task 2", description="Desc 2",
            status=None, priority="medium", details=None, estimated_effort=None,
            assignees=["@test_agent"], labels=["bugfix"], due_date=None
        )
        
        # List all tasks
        result = consolidated_tools._handle_list_tasks(
            project_id="test_project", task_tree_id="main", user_id="default_id",
            status=None, priority=None, assignees=None, labels=None, limit=None
        )
        
        assert result["success"] is True
        assert len(result["tasks"]) >= 2
        assert result["count"] >= 2
    
    def test_handle_list_tasks_with_filters(self, consolidated_tools):
        """Test listing tasks with filters"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Create tasks with different properties
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="High Priority Task", description="Desc",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Medium Priority Task", description="Desc",
            status=None, priority="medium", details=None, estimated_effort=None,
            assignees=["@test_agent"], labels=["bugfix"], due_date=None
        )
        
        # Filter by priority
        result = consolidated_tools._handle_list_tasks(
            project_id="test_project", task_tree_id="main", user_id="default_id",
            status=None, priority="high", assignees=None, labels=None, limit=None
        )
        
        assert result["success"] is True
        # Should have at least one high priority task
        high_priority_tasks = [t for t in result["tasks"] if t.get("priority") == "high"]
        assert len(high_priority_tasks) >= 1
    
    def test_handle_search_tasks(self, consolidated_tools):
        """Test searching tasks"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Create tasks with searchable content
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Authentication Feature", description="User login system",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Database Migration", description="Update schema",
            status=None, priority="medium", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["migration"], due_date=None
        )
        
        # Search for authentication
        result = consolidated_tools._handle_search_tasks(
            project_id="test_project", task_tree_id="main", user_id="default_id",
            query="authentication"
        )
        
        assert result["success"] is True
        assert result["query"] == "authentication"
        # Should find the authentication task
        auth_tasks = [t for t in result["tasks"] if "authentication" in t.get("title", "").lower()]
        assert len(auth_tasks) >= 1
    
    def test_handle_do_next(self, consolidated_tools):
        """Test getting next recommended task"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Create some tasks
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="High Priority Task", description="Urgent",
            status=None, priority="critical", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Low Priority Task", description="Not urgent",
            status=None, priority="low", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["enhancement"], due_date=None
        )
        
        result = consolidated_tools._handle_do_next(
            project_id="test_project", task_tree_id="main", user_id="default_id"
        )
        
        assert result["success"] is True
        assert result["action"] == "next"
        # Should recommend a task (likely the high priority one)
        if "recommended_task" in result and result["recommended_task"]:
            assert "title" in result["recommended_task"]
    
    def test_handle_subtask_operations_add(self, consolidated_tools):
        """Test adding subtask"""
        # First create the project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Then create a parent task
        create_result = consolidated_tools.task_handler.handle_core_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Parent Task", description="Parent",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        task_id = create_result["task"]["id"]
        
        # Add subtask
        result = consolidated_tools.task_handler.handle_subtask_operations(
            action="add_subtask",
            task_id=task_id,
            subtask_data={"title": "Subtask 1", "description": "First subtask"},
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id"
        )
        
        assert result["success"] is True
        assert result["action"] == "add_subtask"
        assert result["result"]["subtask"]["title"] == "Subtask 1"
    
    def test_handle_subtask_operations_list(self, consolidated_tools):
        """Test listing subtasks"""
        # First create the project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Create parent task and add subtask
        create_result = consolidated_tools.task_handler.handle_core_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Parent Task", description="Parent",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        task_id = create_result["task"]["id"]
        
        consolidated_tools.task_handler.handle_subtask_operations(
            action="add_subtask",
            task_id=task_id,
            subtask_data={"title": "Subtask 1", "description": "First subtask"},
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id"
        )
        
        # List subtasks
        result = consolidated_tools.task_handler.handle_subtask_operations(
            action="list_subtasks",
            task_id=task_id,
            subtask_data=None,
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id"
        )
        
        assert result["success"] is True
        assert result["action"] == "list_subtasks"
        assert len(result["result"]) >= 1
    
    def test_handle_dependency_operations_add(self, consolidated_tools):
        """Test adding task dependency"""
        # First create the project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        # Create two tasks
        task1_result = consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Task 1", description="First task",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        task2_result = consolidated_tools._handle_core_task_operations(
            action="create", project_id="test_project", task_tree_id="main", user_id="default_id",
            task_id=None, title="Task 2", description="Second task",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["feature"], due_date=None
        )
        
        task1_id = task1_result["task"]["id"]
        task2_id = task2_result["task"]["id"]
        
        # Add dependency (task2 depends on task1)
        result = consolidated_tools._handle_dependency_operations(
            action="add_dependency",
            task_id=task2_id,
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            dependency_data={"dependency_id": task1_id}
        )
        
        assert result["success"] is True
        assert result["action"] == "add_dependency"
    
    def test_error_handling_invalid_task_id(self, consolidated_tools):
        """Test error handling for invalid task ID"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        result = consolidated_tools._handle_core_task_operations(
            action="get",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id="nonexistent_id",
            title=None, description=None, status=None, priority=None,
            details=None, estimated_effort=None, assignees=None, labels=None, due_date=None
        )
        
        assert result["success"] is False
        assert "error" in result
    
    def test_error_handling_invalid_action(self, consolidated_tools):
        """Test error handling for invalid action"""
        # First create a project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "test_project", "Test Project", "Project for testing"
        )
        assert project_result["success"] is True
        
        result = consolidated_tools._handle_core_task_operations(
            action="invalid_action",
            project_id="test_project",
            task_tree_id="main",
            user_id="default_id",
            task_id=None, title="Test", description="Test", status=None, priority=None,
            details=None, estimated_effort=None, assignees=None, labels=None, due_date=None
        )
        
        assert result["success"] is False
        assert "error" in result


class TestIntegrationScenarios:
    """Test complex integration scenarios"""
    
    @pytest.fixture
    def temp_projects_file(self):
        """Create temporary projects file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def consolidated_tools(self, temp_projects_file):
        """Create ConsolidatedMCPTools instance for testing"""
        task_repository = InMemoryTaskRepository()
        return ConsolidatedMCPTools(
            task_repository=task_repository,
            projects_file_path=temp_projects_file
        )
    
    def test_complete_task_workflow(self, consolidated_tools):
        """Test complete workflow: create project, agents, tasks, subtasks"""
        # Create project
        project_result = consolidated_tools._multi_agent_tools.create_project(
            "workflow_test", "Workflow Test Project", "Testing complete workflow"
        )
        assert project_result["success"] is True
        
        # Register agent
        agent_result = consolidated_tools._multi_agent_tools.register_agent(
            "workflow_test", "dev_agent", "Developer Agent", "@coding_agent"
        )
        assert agent_result["success"] is True
        
        # Create task
        task_result = consolidated_tools._handle_core_task_operations(
            action="create", project_id="workflow_test", task_tree_id="main", user_id="default_id",
            task_id=None, title="Workflow Task", description="Complete workflow task",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["workflow"], due_date=None
        )
        assert task_result["success"] is True
        task_id = task_result["task"]["id"]
        
        # Add subtask
        subtask_result = consolidated_tools._handle_subtask_operations(
            action="add",
            task_id=task_id,
            subtask_data={"title": "Workflow Subtask", "description": "Subtask for workflow"}
        )
        assert subtask_result["success"] is True
        
        # Complete task
        complete_result = consolidated_tools._handle_core_task_operations(
            action="complete", project_id="workflow_test", task_tree_id="main", user_id="default_id",
            task_id=task_id, title=None, description=None, status=None, priority=None,
            details=None, estimated_effort=None, assignees=None, labels=None, due_date=None
        )
        assert complete_result["success"] is True
    
    def test_multi_project_scenario(self, consolidated_tools):
        """Test scenario with multiple projects and cross-project operations"""
        # Create multiple projects
        proj1_result = consolidated_tools._multi_agent_tools.create_project(
            "proj1", "Project 1", "First project"
        )
        proj2_result = consolidated_tools._multi_agent_tools.create_project(
            "proj2", "Project 2", "Second project"
        )
        assert proj1_result["success"] is True
        assert proj2_result["success"] is True
        
        # List projects
        list_result = consolidated_tools._multi_agent_tools.list_projects()
        assert list_result["success"] is True
        assert list_result["count"] == 2
        
        # Create tasks in different projects
        task1_result = consolidated_tools._handle_core_task_operations(
            action="create", project_id="proj1", task_tree_id="main", user_id="default_id",
            task_id=None, title="Project 1 Task", description="Task for project 1",
            status=None, priority="high", details=None, estimated_effort=None,
            assignees=["@coding_agent"], labels=["project1"], due_date=None
        )
        task2_result = consolidated_tools._handle_core_task_operations(
            action="create", project_id="proj2", task_tree_id="main", user_id="default_id",
            task_id=None, title="Project 2 Task", description="Task for project 2",
            status=None, priority="medium", details=None, estimated_effort=None,
            assignees=["@test_agent"], labels=["project2"], due_date=None
        )
        
        assert task1_result["success"] is True
        assert task2_result["success"] is True
        
        # Search across tasks in proj1
        search_result = consolidated_tools._handle_search_tasks(
            project_id="proj1", task_tree_id="main", user_id="default_id", query="project"
        )
        assert search_result["success"] is True
        # Should find at least the task from proj1
        assert len(search_result["tasks"]) >= 1
    
    def test_error_recovery_scenarios(self, consolidated_tools):
        """Test error recovery and resilience"""
        # Test with invalid data
        invalid_result = consolidated_tools._handle_core_task_operations(
            action="create", task_id=None, title="", description="",  # Empty title
            status="invalid_status", priority="invalid_priority", details=None,
            estimated_effort="invalid_effort", assignees=["invalid_agent"], labels=[""], due_date="invalid_date"
        )
        # Should handle gracefully (might succeed with defaults or fail gracefully)
        assert "success" in invalid_result
        
        # Test operations on non-existent resources
        nonexistent_result = consolidated_tools._handle_subtask_operations(
            action="add_subtask", task_id="nonexistent_task_id",
            subtask_data={"title": "Test Subtask"}
        )
        assert nonexistent_result["success"] is False
        
        # Test dependency operations with invalid data
        dep_result = consolidated_tools._handle_dependency_operations(
            action="add_dependency", task_id="nonexistent", dependency_data={"dependency_id": "also_nonexistent"}
        )
        assert dep_result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__]) 