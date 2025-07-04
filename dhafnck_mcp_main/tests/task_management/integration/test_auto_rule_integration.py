"""
This is the canonical and only maintained test suite for auto rule integration tests in task management.
All validation, edge-case, and integration tests should be added here.
Redundant or duplicate tests in other files have been removed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))


import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import MCP and application classes
from fastmcp.task_management.interface.consolidated_mcp_tools import ConsolidatedMCPTools
from fastmcp.task_management.application.services.task_application_service import TaskApplicationService
from fastmcp.task_management.infrastructure.repositories.json_task_repository import JsonTaskRepository
from fastmcp.task_management.infrastructure.services.file_auto_rule_generator import FileAutoRuleGenerator


class TestAutoRuleIntegration:
    """Integration test suite for auto rule generation with MCP tools"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_tasks_file = os.path.join(self.test_dir, "test_tasks.json")
        self.test_auto_rule_file = os.path.join(self.test_dir, "test_auto_rule.mdc")
        
        from datetime import datetime
        current_date = datetime.now().strftime('%Y%m%d')
        task_id_1 = f"{current_date}101"
        task_id_2 = f"{current_date}102"
        
        self.test_tasks_data = {
            "tasks": [
                {
                    "id": task_id_1,
                    "title": "Test Auto Rule Generation Trigger",
                    "description": "Test that auto_rule.mdc is generated when get_task is called",
                    "status": "todo",
                    "priority": "high",
                    "details": "Integration test for auto rule generation system",
                    "estimated_effort": "small",
                    "assignees": ["system_architect"],
                    "labels": ["auto-generation", "testing", "integration"],
                    "dependencies": [],
                    "subtasks": [],
                    "created_at": "2025-01-22T10:00:00Z",
                    "updated_at": "2025-01-22T10:00:00Z",
                    "due_date": "2025-01-23"
                },
                {
                    "id": task_id_2,
                    "title": "Test Senior Developer Rules",
                    "description": "Test auto rule generation for senior developer role",
                    "status": "in_progress",
                    "priority": "medium",
                    "details": "Test role-specific rule generation",
                    "estimated_effort": "medium",
                    "assignees": ["senior_developer"],
                    "labels": ["development", "testing"],
                    "dependencies": [],
                    "subtasks": [],
                    "created_at": "2025-01-22T11:00:00Z",
                    "updated_at": "2025-01-22T11:00:00Z",
                    "due_date": "2025-01-24"
                }
            ]
        }
        
        with open(self.test_tasks_file, 'w') as f:
            json.dump(self.test_tasks_data, f, indent=2)
        
        self.task_id_1 = self.test_tasks_data['tasks'][0]['id']
        self.task_id_2 = self.test_tasks_data['tasks'][1]['id']

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
            
    def _get_registered_tool(self, mcp_tools, tool_name):
        """Helper to get a registered tool from the MCP mock"""
        mock_mcp = MagicMock()
        registered_tools = {}

        def mock_tool_decorator(name=None):
            def decorator(func):
                actual_name = name or func.__name__
                registered_tools[actual_name] = func
                return func
            return decorator

        mock_mcp.tool = mock_tool_decorator
        mcp_tools.register_tools(mock_mcp)
        return registered_tools.get(tool_name)

    @patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator')
    def test_mcp_get_task_triggers_auto_rule_generation(self, mock_auto_rule_generator_class):
        """Test that MCP get_task tool triggers auto rule generation"""
        # Set up mock auto rule generator
        mock_generator = MagicMock()
        mock_auto_rule_generator_class.return_value = mock_generator
        
        task_repository = JsonTaskRepository(self.test_tasks_file)
        mcp_tools = ConsolidatedMCPTools(
            task_repository=task_repository
        )
        
        # Create the project first
        manage_project_func = self._get_registered_tool(mcp_tools, 'manage_project')
        assert manage_project_func is not None
        project_result = manage_project_func(action="create", project_id="test_project", name="Test Project")
        assert project_result.get("success") is True, f"create_project failed: {project_result.get('error')}"
        
        manage_task_func = self._get_registered_tool(mcp_tools, 'manage_task')
        assert manage_task_func is not None
        
        # Create the task first using the task data
        task_data = self.test_tasks_data['tasks'][0]
        create_result = manage_task_func(
            action="create",
            project_id="test_project",
            title=task_data['title'],
            description=task_data['description'],
            status=task_data['status'],
            priority=task_data['priority'],
            details=task_data['details'],
            estimated_effort=task_data['estimated_effort'],
            assignees=task_data['assignees'],
            labels=task_data['labels'],
            due_date=task_data['due_date']
        )
        assert create_result.get("success") is True, f"create_task failed: {create_result.get('error')}"
        
        # Get the actually created task ID
        created_task_id = create_result["task"]["id"]
        
        # Now get the task using the created ID
        result = manage_task_func(action="get", project_id="test_project", task_id=created_task_id)
        assert result.get("success") is True, f"manage_task failed: {result.get('error')}"
        assert result["task"]["id"] == created_task_id
        # Verify that auto rule generation was called
        mock_generator.generate_rules_for_task.assert_called()

    @patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator')
    def test_mcp_get_task_with_different_roles(self, mock_auto_rule_generator_class):
        """Test auto rule generation with different roles through MCP"""
        # Set up mock auto rule generator
        mock_generator = MagicMock()
        mock_auto_rule_generator_class.return_value = mock_generator
        
        task_repository = JsonTaskRepository(self.test_tasks_file)
        mcp_tools = ConsolidatedMCPTools(
            task_repository=task_repository
        )
        
        # Create the project first
        manage_project_func = self._get_registered_tool(mcp_tools, 'manage_project')
        assert manage_project_func is not None
        project_result = manage_project_func(action="create", project_id="test_project", name="Test Project")
        assert project_result.get("success") is True, f"create_project failed: {project_result.get('error')}"
        
        manage_task_func = self._get_registered_tool(mcp_tools, 'manage_task')
        assert manage_task_func is not None
        
        # Create the first task
        task_data1 = self.test_tasks_data['tasks'][0]
        create_result1 = manage_task_func(
            action="create",
            project_id="test_project",
            title=task_data1['title'],
            description=task_data1['description'],
            status=task_data1['status'],
            priority=task_data1['priority'],
            details=task_data1['details'],
            estimated_effort=task_data1['estimated_effort'],
            assignees=task_data1['assignees'],
            labels=task_data1['labels'],
            due_date=task_data1['due_date']
        )
        assert create_result1.get("success") is True, f"create_task1 failed: {create_result1.get('error')}"
        created_task_id1 = create_result1["task"]["id"]
        
        # Create the second task
        task_data2 = self.test_tasks_data['tasks'][1]
        create_result2 = manage_task_func(
            action="create",
            project_id="test_project",
            title=task_data2['title'],
            description=task_data2['description'],
            status=task_data2['status'],
            priority=task_data2['priority'],
            details=task_data2['details'],
            estimated_effort=task_data2['estimated_effort'],
            assignees=task_data2['assignees'],
            labels=task_data2['labels'],
            due_date=task_data2['due_date']
        )
        assert create_result2.get("success") is True, f"create_task2 failed: {create_result2.get('error')}"
        created_task_id2 = create_result2["task"]["id"]
        
        # Now get the tasks
        result1 = manage_task_func(action="get", project_id="test_project", task_id=created_task_id1)
        assert result1["success"] is True
        result2 = manage_task_func(action="get", project_id="test_project", task_id=created_task_id2)
        assert result2["success"] is True

    @patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator')
    def test_mcp_get_task_nonexistent_task(self, mock_auto_rule_generator_class):
        """Test MCP get_task with nonexistent task"""
        # Set up mock auto rule generator
        mock_generator = MagicMock()
        mock_auto_rule_generator_class.return_value = mock_generator
        
        task_repository = JsonTaskRepository(self.test_tasks_file)
        mcp_tools = ConsolidatedMCPTools(
            task_repository=task_repository
        )
        manage_task_func = self._get_registered_tool(mcp_tools, 'manage_task')
        assert manage_task_func is not None
        result = manage_task_func(action="get", project_id="test_project", task_id="20250101999")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_auto_rule_generation_content_structure(self):
        """Test the structure and quality of generated auto rule content"""
        task_repository = JsonTaskRepository(self.test_tasks_file)
        # Use a real FileAutoRuleGenerator with custom file path for this test
        with patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator') as mock_class:
            real_generator = FileAutoRuleGenerator(self.test_auto_rule_file)
            mock_class.return_value = real_generator
            
            mcp_tools = ConsolidatedMCPTools(
                task_repository=task_repository
            )
            
            # Create the project first
            manage_project_func = self._get_registered_tool(mcp_tools, 'manage_project')
            assert manage_project_func is not None
            project_result = manage_project_func(action="create", project_id="test_project", name="Test Project")
            assert project_result.get("success") is True, f"create_project failed: {project_result.get('error')}"
            
            manage_task_func = self._get_registered_tool(mcp_tools, 'manage_task')
            assert manage_task_func is not None
            
            # Create the task first using the task data
            task_data = self.test_tasks_data['tasks'][0]
            create_result = manage_task_func(
                action="create",
                project_id="test_project",
                title=task_data['title'],
                description=task_data['description'],
                status=task_data['status'],
                priority=task_data['priority'],
                details=task_data['details'],
                estimated_effort=task_data['estimated_effort'],
                assignees=task_data['assignees'],
                labels=task_data['labels'],
                due_date=task_data['due_date']
            )
            assert create_result.get("success") is True, f"create_task failed: {create_result.get('error')}"
            
            # Get the actually created task ID
            created_task_id = create_result["task"]["id"]
            
            # Now get the task using the created ID
            result = manage_task_func(action="get", project_id="test_project", task_id=created_task_id, force_full_generation=False)
            assert result.get("success") is True, f"manage_task failed: {result.get('error')}"
            assert os.path.exists(self.test_auto_rule_file)
            with open(self.test_auto_rule_file, 'r') as f:
                content = f.read()
            
            task1_assignee = self.test_tasks_data['tasks'][0]['assignees'][0]
            
            assert "### TASK CONTEXT ###" in content, "Missing '### TASK CONTEXT ###' section in simple rules."
            assert f"ROLE: {task1_assignee.upper()}" in content, f"Missing correct ROLE section for {task1_assignee.upper()} in simple rules."
            assert "### OPERATING RULES ###" in content, "Missing '### OPERATING RULES ###' section in simple rules."

    def test_auto_rule_file_overwrite_behavior(self):
        """Test that auto rule file is overwritten on subsequent calls"""
        task_repository = JsonTaskRepository(self.test_tasks_file)
        # Use a real FileAutoRuleGenerator with custom file path for this test
        with patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator') as mock_class:
            real_generator = FileAutoRuleGenerator(self.test_auto_rule_file)
            mock_class.return_value = real_generator
            
            mcp_tools = ConsolidatedMCPTools(
                task_repository=task_repository
            )
            
            # Create the project first
            manage_project_func = self._get_registered_tool(mcp_tools, 'manage_project')
            assert manage_project_func is not None
            project_result = manage_project_func(action="create", project_id="test_project", name="Test Project")
            assert project_result.get("success") is True, f"create_project failed: {project_result.get('error')}"
            
            manage_task_func = self._get_registered_tool(mcp_tools, 'manage_task')
            assert manage_task_func is not None
            
            # Create the task first using the task data
            task_data = self.test_tasks_data['tasks'][0]
            create_result = manage_task_func(
                action="create",
                project_id="test_project",
                title=task_data['title'],
                description=task_data['description'],
                status=task_data['status'],
                priority=task_data['priority'],
                details=task_data['details'],
                estimated_effort=task_data['estimated_effort'],
                assignees=task_data['assignees'],
                labels=task_data['labels'],
                due_date=task_data['due_date']
            )
            assert create_result.get("success") is True, f"create_task failed: {create_result.get('error')}"
            
            # Get the actually created task ID
            created_task_id = create_result["task"]["id"]
            
            result1 = manage_task_func(action="get", project_id="test_project", task_id=created_task_id)
            assert result1.get("success") is True, f"manage_task failed: {result1.get('error')}"
            
            with open(self.test_auto_rule_file, 'r') as f:
                content_before = f.read()
                
            update_request = {
                "action": "update",
                "project_id": "test_project",
                "task_id": created_task_id,
                "title": "Updated Test Task Title"
            }
            manage_task_func(**update_request)
            
            result2 = manage_task_func(action="get", project_id="test_project", task_id=created_task_id)
            assert result2.get("success") is True, f"manage_task failed: {result2.get('error')}"
            
            with open(self.test_auto_rule_file, 'r') as f:
                content_after = f.read()
                
            assert content_before != content_after, "File content should be different after update"
            assert "Updated Test Task Title" in content_after, "Updated title not found in content"

    @patch('fastmcp.task_management.interface.consolidated_mcp_tools.FileAutoRuleGenerator')
    def test_auto_rule_generation_error_recovery(self, mock_auto_rule_generator_class):
        """Test that the system gracefully handles errors during auto rule generation"""
        task_repository = JsonTaskRepository(self.test_tasks_file)
        mock_generator = MagicMock(spec=FileAutoRuleGenerator)
        mock_generator.generate_rules_for_task.side_effect = Exception("Simulated generation error")
        mock_auto_rule_generator_class.return_value = mock_generator
        
        mcp_tools = ConsolidatedMCPTools(
            task_repository=task_repository
        )
        
        # Create the project first
        manage_project_func = self._get_registered_tool(mcp_tools, 'manage_project')
        assert manage_project_func is not None
        project_result = manage_project_func(action="create", project_id="test_project", name="Test Project")
        assert project_result.get("success") is True, f"create_project failed: {project_result.get('error')}"
        
        manage_task_func = self._get_registered_tool(mcp_tools, 'manage_task')
        assert manage_task_func is not None
        
        # Create the task first using the task data
        task_data = self.test_tasks_data['tasks'][0]
        create_result = manage_task_func(
            action="create",
            project_id="test_project",
            title=task_data['title'],
            description=task_data['description'],
            status=task_data['status'],
            priority=task_data['priority'],
            details=task_data['details'],
            estimated_effort=task_data['estimated_effort'],
            assignees=task_data['assignees'],
            labels=task_data['labels'],
            due_date=task_data['due_date']
        )
        assert create_result.get("success") is True, f"create_task failed: {create_result.get('error')}"
        
        # Get the actually created task ID
        created_task_id = create_result["task"]["id"]
        
        result = manage_task_func(action="get", project_id="test_project", task_id=created_task_id)
        assert result.get("success") is False, "Expected manage_task to fail"
        assert "auto rule generation" in result.get("error", "").lower(), "Error message should indicate auto rule generation failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 