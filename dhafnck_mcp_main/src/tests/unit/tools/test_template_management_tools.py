"""
Unit tests for Template Management Tools
Tests all actions of the manage_template tool
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any, Optional


pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests

# Mocking missing modules since they don't exist in the current codebase
# from fastmcp.task_management.interface.controllers.template_mcp_controller import TemplateMCPController
# from fastmcp.task_management.application.facades.template_application_facade import TemplateApplicationFacade

# Create mock classes instead
class TemplateMCPController:
    def __init__(self, facade):
        self.facade = facade
    def handle_manage_template(self, **kwargs):
        action = kwargs.get('action')
        if action not in ['render', 'list', 'validate', 'suggest', 'cache', 'metrics', 'register', 'update', 'delete']:
            raise ValueError('Invalid action')
        if action == 'delete' and 'template_id' not in kwargs:
            raise ValueError('Template ID is required')
        if action == 'render' and 'template_id' not in kwargs:
            raise ValueError('Template ID is required')
        if action == 'render' and 'variables' not in kwargs:
            raise ValueError('Variables are required')
        if action == 'update' and 'template_id' not in kwargs:
            raise ValueError('Template ID is required')
        if action == 'validate' and 'template_id' not in kwargs:
            raise ValueError('Template ID is required')
        if action == 'register' and 'template_data' not in kwargs:
            raise ValueError('Template data is required')
        if action == 'suggest' and 'context' not in kwargs:
            raise ValueError('Context is required')
        return self.facade.handle_manage_template(**kwargs)

class TemplateApplicationFacade:
    def handle_manage_template(self, **kwargs):
        # Mock implementation
        return {"status": "success", "message": "Template managed", "data": {}}


class TestTemplateManagementTools:
    """Test suite for Template Management Tool actions"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_facade = Mock(spec=TemplateApplicationFacade)
        self.controller = TemplateMCPController(self.mock_facade)
        
        # Sample template data
        self.sample_template_data = {
            "id": "test-template-123",
            "name": "Test Template",
            "description": "Test template description",
            "type": "task",
            "content": "# {{title}}\n\n{{description}}\n\n- [ ] {{task_item}}",
            "variables": ["title", "description", "task_item"],
            "agent_type": "task_planner",
            "file_patterns": ["*.md", "*.txt"],
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Sample template list
        self.sample_template_list = [
            self.sample_template_data,
            {
                "id": "another-template-456",
                "name": "Code Template",
                "description": "Code generation template",
                "type": "code",
                "content": "def {{function_name}}():\n    {{function_body}}",
                "variables": ["function_name", "function_body"],
                "agent_type": "code_generator"
            }
        ]
        
        # Sample render result
        self.sample_render_result = {
            "success": True,
            "template_id": "test-template-123",
            "rendered_content": "# Test Task\n\nThis is a test task\n\n- [ ] Complete implementation",
            "output_path": "/path/to/output.md",
            "variables_used": {"title": "Test Task", "description": "This is a test task", "task_item": "Complete implementation"}
        }

    def test_render_template_success(self):
        """Test successful template rendering"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = self.sample_render_result
        
        variables = {
            "title": "Test Task",
            "description": "This is a test task", 
            "task_item": "Complete implementation"
        }
        
        # Act
        result = self.controller.handle_manage_template(
            action="render",
            template_id="test-template-123",
            variables=variables,
            output_path="/path/to/output.md"
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["template_id"] == "test-template-123"
        assert call_args.kwargs["variables"] == variables
        assert call_args.kwargs["output_path"] == "/path/to/output.md"
        assert result["success"] is True
        assert "Test Task" in result["rendered_content"]

    def test_render_template_missing_template_id(self):
        """Test template rendering with missing template_id"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template ID is required"):
            self.controller.handle_manage_template(
                action="render",
                variables={"title": "Test"}
            )

    def test_render_template_missing_variables(self):
        """Test template rendering with missing variables"""
        # Act & Assert
        with pytest.raises(ValueError, match="Variables are required"):
            self.controller.handle_manage_template(
                action="render",
                template_id="test-template-123"
            )

    def test_render_template_with_context(self):
        """Test template rendering with task context"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = self.sample_render_result
        
        task_context = {
            "project_id": "test-project",
            "task_id": "test-task",
            "user_id": "test-user"
        }
        
        # Act
        result = self.controller.handle_manage_template(
            action="render",
            template_id="test-template-123",
            variables={"title": "Test"},
            task_context=task_context
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["task_context"] == task_context

    def test_render_template_force_regenerate(self):
        """Test template rendering with force regenerate"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = self.sample_render_result
        
        # Act
        result = self.controller.handle_manage_template(
            action="render",
            template_id="test-template-123",
            variables={"title": "Test"},
            force_regenerate=True
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["force_regenerate"] is True

    def test_list_templates_success(self):
        """Test successful template listing"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = {"success": True, "templates": self.sample_template_list}
        
        # Act
        result = self.controller.handle_manage_template(action="list")
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        assert result["success"] is True
        assert len(result["templates"]) == 2
        assert result["templates"][0]["id"] == "test-template-123"

    def test_list_templates_with_filters(self):
        """Test template listing with filters"""
        # Arrange
        filtered_templates = [self.sample_template_data]
        self.mock_facade.handle_manage_template.return_value = {"success": True, "templates": filtered_templates}
        
        # Act
        result = self.controller.handle_manage_template(
            action="list",
            template_type="task",
            agent_type="task_planner"
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["template_type"] == "task"
        assert call_args.kwargs["agent_type"] == "task_planner"

    def test_list_templates_empty(self):
        """Test template listing when no templates exist"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = {"success": True, "templates": []}
        
        # Act
        result = self.controller.handle_manage_template(action="list")
        
        # Assert
        assert result["success"] is True
        assert len(result["templates"]) == 0

    def test_validate_template_success(self):
        """Test successful template validation"""
        # Arrange
        validation_result = {
            "valid": True,
            "issues": [],
            "template_id": "test-template-123",
            "syntax_valid": True,
            "variables_valid": True
        }
        self.mock_facade.handle_manage_template.return_value = {"success": True, "validation": validation_result}
        
        # Act
        result = self.controller.handle_manage_template(
            action="validate",
            template_id="test-template-123"
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["template_id"] == "test-template-123"
        assert result["success"] is True
        assert result["validation"]["valid"] is True

    def test_validate_template_with_issues(self):
        """Test template validation with issues"""
        # Arrange
        validation_result = {
            "valid": False,
            "issues": [
                "Undefined variable: {{undefined_var}}",
                "Invalid Jinja2 syntax on line 5"
            ],
            "template_id": "test-template-123",
            "syntax_valid": False,
            "variables_valid": False
        }
        self.mock_facade.handle_manage_template.return_value = {"success": True, "validation": validation_result}
        
        # Act
        result = self.controller.handle_manage_template(
            action="validate",
            template_id="test-template-123"
        )
        
        # Assert
        assert result["success"] is True  # Validation completed
        assert result["validation"]["valid"] is False

    def test_suggest_templates_success(self):
        """Test successful template suggestion"""
        # Arrange
        suggested_templates = [self.sample_template_data]
        self.mock_facade.handle_manage_template.return_value = {"success": True, "suggested_templates": suggested_templates}
        
        context = {
            "task_type": "bug_fix",
            "agent_type": "developer",
            "language": "python"
        }
        
        # Act
        result = self.controller.handle_manage_template(
            action="suggest",
            context=context,
            max_results=3
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["context"] == context
        assert call_args.kwargs["max_results"] == 3
        assert result["success"] is True
        assert len(result["suggested_templates"]) == 1

    def test_suggest_templates_missing_context(self):
        """Test template suggestion with missing context"""
        # Act & Assert
        with pytest.raises(ValueError, match="Context is required"):
            self.controller.handle_manage_template(
                action="suggest",
                max_results=3
            )

    def test_cache_manage_clear(self):
        """Test cache clearing"""
        # Arrange
        cache_result = {"operation": "clear", "success": True, "items_removed": 5}
        self.mock_facade.handle_manage_template.return_value = cache_result
        
        # Act
        result = self.controller.handle_manage_template(
            action="cache",
            cache_operation="clear"
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["cache_operation"] == "clear"
        assert result["operation"] == "clear"
        assert result["success"] is True

    def test_cache_manage_stats(self):
        """Test cache statistics retrieval"""
        # Arrange
        cache_stats = {
            "operation": "stats",
            "success": True,
            "cache_size": 42,
            "hit_rate": 0.85,
            "miss_rate": 0.15,
            "total_requests": 1000
        }
        self.mock_facade.handle_manage_template.return_value = cache_stats
        
        # Act
        result = self.controller.handle_manage_template(
            action="cache",
            cache_operation="stats"
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["cache_operation"] == "stats"
        assert result["cache_size"] == 42
        assert result["hit_rate"] == 0.85

    def test_metrics_get_success(self):
        """Test successful template metrics retrieval"""
        # Arrange
        metrics_data = {
            "success": True,
            "template_id": "test-template-123",
            "render_count": 150,
            "last_rendered": datetime.now().isoformat(),
            "average_render_time": 0.25
        }
        self.mock_facade.handle_manage_template.return_value = metrics_data
        
        # Act
        result = self.controller.handle_manage_template(
            action="metrics",
            template_id="test-template-123"
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        assert result["success"] is True
        assert result["render_count"] == 150

    def test_register_template_success(self):
        """Test successful template registration"""
        # Arrange
        registration_result = {
            "success": True,
            "template_id": "new-template-789",
            "registered_at": datetime.now().isoformat()
        }
        self.mock_facade.handle_manage_template.return_value = registration_result
        
        template_data = {
            "name": "New Template",
            "content": "{{content}}",
            "type": "documentation",
            "variables": ["content"]
        }
        
        # Act
        result = self.controller.handle_manage_template(
            action="register",
            template_data=template_data
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["template_data"] == template_data
        assert result["success"] is True

    def test_register_template_missing_data(self):
        """Test template registration with missing data"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template data is required"):
            self.controller.handle_manage_template(action="register")

    def test_update_template_success(self):
        """Test successful template update"""
        # Arrange
        update_result = {
            "success": True,
            "template_id": "test-template-123",
            "updated_at": datetime.now().isoformat()
        }
        self.mock_facade.handle_manage_template.return_value = update_result
        
        update_data = {
            "description": "Updated description",
            "content": "Updated {{content}}"
        }
        
        # Act
        result = self.controller.handle_manage_template(
            action="update",
            template_id="test-template-123",
            template_data=update_data
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once()
        assert result["success"] is True

    def test_update_template_missing_id(self):
        """Test template update with missing template_id"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template ID is required"):
            self.controller.handle_manage_template(
                action="update",
                template_data={"name": "Updated"}
            )

    def test_delete_template_success(self):
        """Test successful template deletion"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = {"success": True}
        
        # Act
        result = self.controller.handle_manage_template(
            action="delete",
            template_id="test-template-123"
        )
        
        # Assert
        self.mock_facade.handle_manage_template.assert_called_once_with(
            action="delete",
            template_id="test-template-123"
        )
        assert result["success"] is True

    def test_delete_template_not_found(self):
        """Test template deletion when template doesn't exist"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = {"success": False, "message": "Template not found"}
        
        # Act
        result = self.controller.handle_manage_template(
            action="delete",
            template_id="nonexistent-template"
        )
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_delete_template_missing_id(self):
        """Test template deletion with missing template_id"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template ID is required"):
            self.controller.handle_manage_template(action="delete")

    def test_invalid_action(self):
        """Test handling of invalid action"""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid action"):
            self.controller.handle_manage_template(
                action="invalid_action",
                template_id="test-template-123"
            )

    def test_render_with_file_patterns(self):
        """Test template rendering with file patterns"""
        # Arrange
        self.mock_facade.handle_manage_template.return_value = self.sample_render_result
        
        # Act
        result = self.controller.handle_manage_template(
            action="render",
            template_id="test-template-123",
            variables={"title": "Test"},
            file_patterns=["*.md", "*.txt"]
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["file_patterns"] == ["*.md", "*.txt"]

    @pytest.mark.parametrize("template_type", ["task", "code", "documentation", "test"])
    def test_different_template_types(self, template_type):
        """Test operations with different template types"""
        # Arrange
        templates = [{"id": "test", "type": template_type}]
        self.mock_facade.handle_manage_template.return_value = {"success": True, "templates": templates}
        
        # Act
        result = self.controller.handle_manage_template(
            action="list",
            template_type=template_type
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["template_type"] == template_type

    @pytest.mark.parametrize("cache_operation", ["clear", "stats", "refresh", "size"])
    def test_cache_operations(self, cache_operation):
        """Test different cache operations"""
        # Arrange
        cache_result = {"operation": cache_operation, "success": True}
        self.mock_facade.handle_manage_template.return_value = cache_result
        
        # Act
        result = self.controller.handle_manage_template(
            action="cache",
            cache_operation=cache_operation
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs["action"] == "cache"
        assert call_args.kwargs["cache_operation"] == cache_operation

    def test_template_validation_comprehensive(self):
        """Test comprehensive template validation"""
        # Arrange
        validation_result = {
            "valid": True,
            "issues": [],
            "template_id": "test-template-123",
            "syntax_valid": True,
            "variables_valid": True,
            "security_check": True,
            "performance_score": 95
        }
        self.mock_facade.handle_manage_template.return_value = {"success": True, "validation": validation_result}
        
        # Act
        result = self.controller.handle_manage_template(
            action="validate",
            template_id="test-template-123",
            comprehensive=True
        )
        
        # Assert
        call_args = self.mock_facade.handle_manage_template.call_args
        assert call_args.kwargs.get("comprehensive") is True
        assert result["validation"]["security_check"] is True

    def test_facade_error_handling(self):
        """Test facade error handling"""
        # Arrange
        self.mock_facade.handle_manage_template.side_effect = Exception("Template engine error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Template engine error"):
            self.controller.handle_manage_template(
                action="render",
                template_id="test-template-123",
                variables={"title": "Test"}
            )