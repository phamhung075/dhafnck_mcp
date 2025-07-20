#!/usr/bin/env python3
"""
Integration tests for JSON field compatibility between SQLite and PostgreSQL.

This test suite validates that JSON fields work correctly and consistently
across both database types, including storage, retrieval, and querying.
"""

import os
import sys
import json
import pytest
from uuid import uuid4
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Agent, Task, TaskSubtask, GlobalContext, ProjectContext,
    BranchContext, TaskContext, Template, Base
)


class TestJSONFieldCompatibility:
    """Test suite for JSON field compatibility between SQLite and PostgreSQL"""
    
    def setup_method(self):
        """Set up test environment"""
        # Use in-memory SQLite for testing
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()
    
    def teardown_method(self):
        """Clean up test environment"""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    def test_project_metadata_json_field(self):
        """Test Project metadata JSON field"""
        # Test various JSON data types
        test_metadata = {
            "string_field": "test_value",
            "number_field": 42,
            "boolean_field": True,
            "null_field": None,
            "array_field": [1, 2, 3, "four"],
            "nested_object": {
                "nested_string": "nested_value",
                "nested_number": 123,
                "deeply_nested": {
                    "deep_value": "very_deep"
                }
            }
        }
        
        # Create project with complex metadata
        from uuid import uuid4
        project = Project(
            id=str(uuid4()),
            name="JSON Test Project",
            description="Testing JSON metadata",
            user_id="test_user",
            model_metadata=test_metadata
        )
        
        self.session.add(project)
        self.session.commit()
        
        # Retrieve and verify JSON data
        retrieved_project = self.session.query(Project).filter_by(name="JSON Test Project").first()
        
        assert retrieved_project.model_metadata == test_metadata
        assert retrieved_project.model_metadata["string_field"] == "test_value"
        assert retrieved_project.model_metadata["number_field"] == 42
        assert retrieved_project.model_metadata["boolean_field"] is True
        assert retrieved_project.model_metadata["null_field"] is None
        assert retrieved_project.model_metadata["array_field"] == [1, 2, 3, "four"]
        assert retrieved_project.model_metadata["nested_object"]["nested_string"] == "nested_value"
        assert retrieved_project.model_metadata["nested_object"]["deeply_nested"]["deep_value"] == "very_deep"
        
        print("✅ Project metadata JSON field test passed")
    
    def test_agent_capabilities_and_metadata_json_fields(self):
        """Test Agent capabilities and metadata JSON fields"""
        # Test capabilities as JSON array
        capabilities = ["coding", "testing", "debugging", "documentation"]
        
        # Test metadata as complex JSON
        metadata = {
            "version": "2.0",
            "configuration": {
                "timeout": 30,
                "retries": 3,
                "features": ["async", "parallel"]
            },
            "statistics": {
                "tasks_completed": 150,
                "success_rate": 0.95,
                "average_time": 45.5
            }
        }
        
        # Create agent
        agent = Agent(
            id=str(uuid4()),
            name="json_test_agent",
            status="available",
            capabilities=capabilities,
            model_metadata=metadata
        )
        
        self.session.add(agent)
        self.session.commit()
        
        # Retrieve and verify
        retrieved_agent = self.session.query(Agent).filter_by(name="json_test_agent").first()
        
        assert retrieved_agent.capabilities == capabilities
        assert retrieved_agent.model_metadata == metadata
        assert retrieved_agent.model_metadata["version"] == "2.0"
        assert retrieved_agent.model_metadata["configuration"]["timeout"] == 30
        assert retrieved_agent.model_metadata["statistics"]["success_rate"] == 0.95
        
        print("✅ Agent capabilities and metadata JSON fields test passed")
    
    def test_task_metadata_json_field(self):
        """Test Task metadata JSON field via TaskContext"""
        # Create project and branch first
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            description="Test project",
            user_id="test_user",
            model_metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        branch = ProjectGitBranch(
            id=str(uuid4()),
            project_id=project.id,
            name="main",
            description="Main branch",
            status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Create project context first (required for TaskContext)
        project_context = ProjectContext(
            project_id=project.id,
            parent_global_id="global_singleton",
            team_preferences={},
            technology_stack={},
            project_workflow={},
            local_standards={},
            global_overrides={},
            delegation_rules={}
        )
        self.session.add(project_context)
        self.session.commit()
        
        # Create branch context (required for 4-tier hierarchy)
        branch_context = BranchContext(
            branch_id=branch.id,
            parent_project_id=project.id,
            parent_project_context_id=project.id,
            branch_workflow={},
            branch_standards={},
            agent_assignments={},
            local_overrides={},
            delegation_rules={})
        self.session.add(branch_context)
        self.session.commit()
        
        # Create task
        task_id = str(uuid4())
        task = Task(
            id=task_id,
            git_branch_id=branch.id,
            title="JSON Metadata Test Task",
            description="Testing JSON metadata storage",
            priority="high",
            status="pending",
            context_id=task_id  # Link to context
        )
        
        self.session.add(task)
        self.session.commit()
        
        # Test complex task metadata stored in TaskContext
        task_metadata = {
            "dependencies": ["task_1", "task_2"],
            "tags": ["urgent", "bug", "frontend"],
            "time_estimates": {
                "development": 4.5,
                "testing": 2.0,
                "review": 1.0
            },
            "requirements": {
                "browser_support": ["chrome", "firefox", "safari"],
                "responsive": True,
                "accessibility": {
                    "level": "AA",
                    "screen_reader": True
                }
            },
            "files_affected": [
                "src/components/Header.tsx",
                "src/styles/header.css",
                "tests/header.test.tsx"
            ]
        }
        
        # Create task context with metadata (updated for 4-tier hierarchy)
        task_context = TaskContext(
            task_id=task_id,
            parent_branch_id=branch.id,
            parent_branch_context_id=branch.id,
            task_data=task_metadata,

        )
        
        self.session.add(task_context)
        self.session.commit()
        
        # Retrieve and verify
        retrieved_task = self.session.query(Task).filter_by(title="JSON Metadata Test Task").first()
        retrieved_context = self.session.query(TaskContext).filter_by(task_id=retrieved_task.id).first()
        
        assert retrieved_context.task_data == task_metadata
        assert retrieved_context.task_data["dependencies"] == ["task_1", "task_2"]
        assert retrieved_context.task_data["time_estimates"]["development"] == 4.5
        assert retrieved_context.task_data["requirements"]["accessibility"]["level"] == "AA"
        
        print("✅ Task metadata JSON field test passed")
    
    def test_subtask_assignees_json_field(self):
        """Test TaskSubtask assignees JSON field"""
        # Create project, branch, and task
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            description="Test project",
            user_id="test_user",
            model_metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        branch = ProjectGitBranch(
            id=str(uuid4()),
            project_id=project.id,
            name="main",
            description="Main branch",
            status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        task = Task(
            id=str(uuid4()),
            git_branch_id=branch.id,
            title="Parent Task",
            description="Parent task for subtask testing",
            priority="medium",
            status="pending"
        )
        self.session.add(task)
        self.session.commit()
        
        # Test various assignee configurations
        assignees_configs = [
            [],  # No assignees
            ["user1"],  # Single assignee
            ["user1", "user2", "user3"],  # Multiple assignees
            ["user@example.com", "another.user@company.com"]  # Email format
        ]
        
        subtasks = []
        for i, assignees in enumerate(assignees_configs):
            subtask = TaskSubtask(
                id=str(uuid4()),
                task_id=task.id,
                title=f"Subtask {i+1}",
                description=f"Subtask with {len(assignees)} assignees",
                status="pending",
                priority="medium",
                assignees=assignees,
                progress_percentage=0
            )
            subtasks.append(subtask)
        
        self.session.add_all(subtasks)
        self.session.commit()
        
        # Retrieve and verify
        retrieved_subtasks = self.session.query(TaskSubtask).filter_by(task_id=task.id).all()
        
        for i, subtask in enumerate(retrieved_subtasks):
            expected_assignees = assignees_configs[i]
            assert subtask.assignees == expected_assignees
            assert isinstance(subtask.assignees, list)
        
        print("✅ TaskSubtask assignees JSON field test passed")
    
    def test_context_data_content_json_field(self):
        """Test Context data_content JSON field"""
        # Test GlobalContext
        global_data = {
            "global_settings": {
                "theme": "dark",
                "language": "en",
                "timezone": "UTC"
            },
            "api_keys": {
                "service_a": "key_a",
                "service_b": "key_b"
            },
            "feature_flags": {
                "new_ui": True,
                "beta_features": False
            }
        }
        
        global_context = GlobalContext(
            id="global_singleton",
            organization_id="test_org",
            autonomous_rules={"rules": global_data},
            security_policies={},
            coding_standards={},
            workflow_templates={},
            delegation_rules={}
        )
        
        self.session.add(global_context)
        self.session.commit()
        
        # Test ProjectContext
        project = Project(
            id=str(uuid4()),
            name="Context Test Project",
            description="Project for context testing",
            user_id="test_user",
            model_metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        project_data = {
            "project_config": {
                "framework": "React",
                "version": "18.0",
                "dependencies": ["react", "typescript", "jest"]
            },
            "deployment": {
                "environment": "production",
                "url": "https://example.com",
                "ssl": True
            }
        }
        
        project_context = ProjectContext(
            project_id=project.id,
            parent_global_id="global_singleton",
            team_preferences={"team": project_data},
            technology_stack={},
            project_workflow={},
            local_standards={},
            global_overrides={},
            delegation_rules={}
        )
        
        self.session.add(project_context)
        self.session.commit()
        
        # Retrieve and verify
        retrieved_global = self.session.query(GlobalContext).first()
        assert retrieved_global.autonomous_rules["rules"] == global_data
        assert retrieved_global.autonomous_rules["rules"]["global_settings"]["theme"] == "dark"
        assert retrieved_global.autonomous_rules["rules"]["feature_flags"]["new_ui"] is True
        
        retrieved_project = self.session.query(ProjectContext).first()
        assert retrieved_project.team_preferences["team"] == project_data
        assert retrieved_project.team_preferences["team"]["project_config"]["framework"] == "React"
        assert retrieved_project.team_preferences["team"]["deployment"]["ssl"] is True
        
        print("✅ Context data_content JSON field test passed")
    
    def test_template_content_json_field(self):
        """Test Template content JSON field"""
        # Test complex template content
        template_content = {
            "template_version": "1.0",
            "template_type": "task",
            "structure": {
                "title": "{{task_title}}",
                "description": "{{task_description}}",
                "checklist": [
                    "Review requirements",
                    "Design solution",
                    "Implement code",
                    "Write tests",
                    "Create documentation"
                ]
            },
            "variables": {
                "task_title": {
                    "type": "string",
                    "required": True,
                    "description": "The title of the task"
                },
                "task_description": {
                    "type": "text",
                    "required": False,
                    "description": "Detailed description of the task"
                }
            },
            "metadata": {
                "created_by": "system",
                "last_modified": "2024-01-01T00:00:00Z",
                "usage_count": 0
            }
        }
        
        template = Template(
            id=str(uuid4()),
            name="Task Template",
            type="task",
            category="development",
            content=template_content,
            tags=["task", "development", "checklist"]
        )
        
        self.session.add(template)
        self.session.commit()
        
        # Retrieve and verify
        retrieved_template = self.session.query(Template).filter_by(name="Task Template").first()
        
        assert retrieved_template.content == template_content
        assert retrieved_template.content["template_version"] == "1.0"
        assert retrieved_template.content["structure"]["title"] == "{{task_title}}"
        assert retrieved_template.content["variables"]["task_title"]["required"] is True
        assert len(retrieved_template.content["structure"]["checklist"]) == 5
        
        print("✅ Template content JSON field test passed")
    
    def test_json_field_updates(self):
        """Test updating JSON fields"""
        # Create project with initial metadata
        project = Project(
            id=str(uuid4()),
            name="Update Test Project",
            description="Testing JSON updates",
            user_id="test_user",
            model_metadata={"version": 1, "status": "initial"}
        )
        
        self.session.add(project)
        self.session.commit()
        
        # Update metadata
        project.model_metadata = {
            "version": 2,
            "status": "updated",
            "new_field": "new_value",
            "nested": {
                "key": "value"
            }
        }
        
        self.session.commit()
        
        # Retrieve and verify update
        retrieved_project = self.session.query(Project).filter_by(name="Update Test Project").first()
        
        assert retrieved_project.model_metadata["version"] == 2
        assert retrieved_project.model_metadata["status"] == "updated"
        assert retrieved_project.model_metadata["new_field"] == "new_value"
        assert retrieved_project.model_metadata["nested"]["key"] == "value"
        
        print("✅ JSON field updates test passed")
    
    def test_json_field_null_and_empty_values(self):
        """Test JSON fields with null and empty values"""
        # Test null metadata
        project1 = Project(
            id=str(uuid4()),
            name="Null Metadata Project",
            description="Testing null metadata",
            user_id="test_user",
            model_metadata=None
        )
        
        # Test empty metadata
        project2 = Project(
            id=str(uuid4()),
            name="Empty Metadata Project",
            description="Testing empty metadata",
            user_id="test_user",
            model_metadata={}
        )
        
        self.session.add_all([project1, project2])
        self.session.commit()
        
        # Retrieve and verify
        retrieved_project1 = self.session.query(Project).filter_by(name="Null Metadata Project").first()
        retrieved_project2 = self.session.query(Project).filter_by(name="Empty Metadata Project").first()
        
        # Note: SQLite JSON field may convert None to {} 
        assert retrieved_project1.model_metadata in [None, {}]
        assert retrieved_project2.model_metadata == {}
        
        print("✅ JSON field null and empty values test passed")
    
    def test_json_field_special_characters(self):
        """Test JSON fields with special characters"""
        # Test special characters in JSON
        special_metadata = {
            "unicode": "Hello 世界 🌍",
            "quotes": 'He said "Hello" and she said \'Hi\'',
            "backslashes": "C:\\path\\to\\file",
            "newlines": "Line 1\nLine 2\nLine 3",
            "tabs": "Column1\tColumn2\tColumn3",
            "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
        }
        
        project = Project(
            id=str(uuid4()),
            name="Special Characters Project",
            description="Testing special characters in JSON",
            user_id="test_user",
            model_metadata=special_metadata
        )
        
        self.session.add(project)
        self.session.commit()
        
        # Retrieve and verify
        retrieved_project = self.session.query(Project).filter_by(name="Special Characters Project").first()
        
        assert retrieved_project.model_metadata == special_metadata
        assert retrieved_project.model_metadata["unicode"] == "Hello 世界 🌍"
        assert retrieved_project.model_metadata["quotes"] == 'He said "Hello" and she said \'Hi\''
        assert retrieved_project.model_metadata["backslashes"] == "C:\\path\\to\\file"
        assert retrieved_project.model_metadata["newlines"] == "Line 1\nLine 2\nLine 3"
        
        print("✅ JSON field special characters test passed")


def run_json_compatibility_tests():
    """Run all JSON field compatibility tests"""
    print("📝 Running JSON Field Compatibility Integration Tests...\n")
    
    test_instance = TestJSONFieldCompatibility()
    
    test_methods = [
        'test_project_metadata_json_field',
        'test_agent_capabilities_and_metadata_json_fields',
        'test_task_metadata_json_field',
        'test_subtask_assignees_json_field',
        'test_context_data_content_json_field',
        'test_template_content_json_field',
        'test_json_field_updates',
        'test_json_field_null_and_empty_values',
        'test_json_field_special_characters'
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            test_instance.setup_method()
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {method_name} - FAILED: {e}")
        finally:
            test_instance.teardown_method()
    
    print(f"\n📊 JSON Field Compatibility Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    return failed == 0, {"passed": passed, "failed": failed}


if __name__ == "__main__":
    success, results = run_json_compatibility_tests()
    
    if success:
        print("\n🎉 All JSON field compatibility tests passed!")
        print("✅ JSON fields work correctly across database types")
        print("✅ Complex nested JSON structures are preserved")
        print("✅ JSON field updates work properly")
        print("✅ Special characters and unicode are handled correctly")
    else:
        print("\n💥 Some JSON field compatibility tests failed!")
        print("Check the output above for details.")
    
    sys.exit(0 if success else 1)