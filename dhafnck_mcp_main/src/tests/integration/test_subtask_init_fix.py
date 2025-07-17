"""
Test-Driven Development for Subtask initialization fix

This test file covers the Subtask.__init__() error where 'task_id' is incorrectly
passed instead of 'parent_task_id'.
"""

import pytest
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository


class TestSubtaskInitialization:
    """Test cases for Subtask initialization with correct parameters"""
    
    def test_subtask_creation_with_parent_task_id(self):
        """Test that Subtask can be created with parent_task_id parameter"""
        # Given
        parent_task_id = TaskId(str(uuid.uuid4()))
        subtask_id = SubtaskId(str(uuid.uuid4()))
        
        # When - This should NOT raise an error
        subtask = Subtask(
            id=subtask_id,
            title="Test Subtask",
            description="Test Description",
            parent_task_id=parent_task_id,
            status=TaskStatus.todo(),
            priority=Priority.medium()
        )
        
        # Then
        assert subtask.parent_task_id == parent_task_id
        assert subtask.title == "Test Subtask"
        assert subtask.description == "Test Description"
        assert subtask.status.value == "todo"
        assert subtask.priority.value == "medium"
    
    def test_subtask_creation_without_task_id_parameter(self):
        """Test that Subtask cannot be created with task_id parameter"""
        # Given
        parent_task_id = TaskId(str(uuid.uuid4()))
        subtask_id = SubtaskId(str(uuid.uuid4()))
        
        # When/Then - This should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            subtask = Subtask(
                id=subtask_id,
                title="Test Subtask",
                description="Test Description",
                task_id=parent_task_id,  # WRONG parameter name
                status=TaskStatus.todo(),
                priority=Priority.medium()
            )
        
        assert "got an unexpected keyword argument 'task_id'" in str(exc_info.value)
    
    def test_subtask_from_dict_creation(self):
        """Test that Subtask.from_dict creates subtask with parent_task_id"""
        # Given
        parent_task_id = TaskId(str(uuid.uuid4()))
        data = {
            "id": str(uuid.uuid4()),
            "title": "Test Subtask from Dict",
            "description": "Description from dict",
            "status": "in_progress",
            "priority": "high",
            "assignees": ["@developer", "@reviewer"]
        }
        
        # When
        subtask = Subtask.from_dict(data, parent_task_id)
        
        # Then
        assert subtask.parent_task_id == parent_task_id
        assert subtask.title == "Test Subtask from Dict"
        assert subtask.status.value == "in_progress"
        assert subtask.priority.value == "high"
        assert subtask.assignees == ["@developer", "@reviewer"]
    
    def test_subtask_create_factory_method(self):
        """Test that Subtask.create factory method works correctly"""
        # Given
        parent_task_id = TaskId(str(uuid.uuid4()))
        subtask_id = SubtaskId(str(uuid.uuid4()))
        
        # When
        subtask = Subtask.create(
            id=subtask_id,
            title="Factory Created Subtask",
            description="Created via factory method",
            parent_task_id=parent_task_id,
            status=TaskStatus.blocked(),
            priority=Priority.urgent()
        )
        
        # Then
        assert subtask.parent_task_id == parent_task_id
        assert subtask.title == "Factory Created Subtask"
        assert subtask.status.value == "blocked"
        assert subtask.priority.value == "urgent"


class TestORMSubtaskRepository:
    """Test cases for ORM Subtask Repository to ensure correct entity creation"""
    
    @pytest.fixture
    def repository(self):
        """Create a test repository instance"""
        return ORMSubtaskRepository()
    
    def test_repository_to_model_data_conversion(self, repository):
        """Test that _to_model_data converts Subtask with parent_task_id to task_id"""
        # Given
        parent_task_id = TaskId(str(uuid.uuid4()))
        subtask = Subtask(
            title="Model Data Test",
            description="Testing model data conversion",
            parent_task_id=parent_task_id,
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=["@developer"]
        )
        
        # When - Convert to model data
        model_data = repository._to_model_data(subtask)
        
        # Then - Should have task_id (not parent_task_id) for ORM
        assert "task_id" in model_data
        assert model_data["task_id"] == parent_task_id.value
        assert "parent_task_id" not in model_data
        assert model_data["title"] == "Model Data Test"
        assert model_data["assignees"] == ["@developer"]
    
    def test_repository_to_domain_entity_mock(self, repository):
        """Test that _to_domain_entity creates Subtask with correct parameters"""
        # Given - Create a mock TaskSubtask model
        from fastmcp.task_management.infrastructure.database.models import TaskSubtask
        
        # We'll create a simple class to simulate the ORM model
        class MockTaskSubtask:
            def __init__(self):
                self.id = str(uuid.uuid4())
                self.title = "ORM Test Subtask" 
                self.description = "ORM Description"
                self.task_id = str(uuid.uuid4())  # ORM uses task_id
                self.status = "todo"
                self.priority = "low"
                self.assignees = ["@tester"]
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
        
        mock_model = MockTaskSubtask()
        
        # When - Convert to domain entity
        # This will fail because _to_domain_entity is incorrectly passing task_id
        # instead of parent_task_id to Subtask constructor
        with pytest.raises(TypeError) as exc_info:
            subtask = repository._to_domain_entity(mock_model)
        
        assert "got an unexpected keyword argument" in str(exc_info.value)


class TestSubtaskIntegrationWithTasks:
    """Integration tests to ensure Subtask works correctly with Task operations"""
    
    def test_task_can_add_subtask_with_correct_parameters(self):
        """Test that a Task can add a Subtask without initialization errors"""
        # This test would require the Task entity, but we're focusing on Subtask for now
        # The key is ensuring Subtask initialization works with parent_task_id
        parent_task_id = TaskId(str(uuid.uuid4()))
        
        # When - Creating multiple subtasks
        subtask1 = Subtask(
            title="Integration Subtask 1",
            description="First subtask",
            parent_task_id=parent_task_id
        )
        
        subtask2 = Subtask(
            title="Integration Subtask 2", 
            description="Second subtask",
            parent_task_id=parent_task_id,
            priority=Priority.high()
        )
        
        # Then - Both should be created successfully
        assert subtask1.parent_task_id == parent_task_id
        assert subtask2.parent_task_id == parent_task_id
        assert subtask1.status.value == "todo"  # Default
        assert subtask2.priority.value == "high"


class TestSubtaskErrorScenarios:
    """Test error scenarios that users are experiencing"""
    
    def test_mcp_tool_subtask_creation_scenario(self):
        """Simulate the error occurring in MCP tool usage"""
        # Given - Parameters that would come from MCP tool
        task_id = "34034853-c856-4d85-a362-a1eceb0bf6a4"
        subtask_data = {
            "title": "Create JWT token generation function",
            "description": "Implement function to generate JWT tokens with user claims and expiration",
            "priority": "high"
        }
        
        # When - Attempting to create subtask the wrong way (simulating the error)
        with pytest.raises(TypeError) as exc_info:
            # This simulates what might be happening in the code
            subtask = Subtask(
                task_id=TaskId(task_id),  # WRONG - should be parent_task_id
                **subtask_data
            )
        
        assert "got an unexpected keyword argument 'task_id'" in str(exc_info.value)
        
        # Then - The correct way should work
        subtask = Subtask(
            parent_task_id=TaskId(task_id),  # CORRECT
            title=subtask_data["title"],
            description=subtask_data["description"],
            priority=Priority.from_string(subtask_data["priority"])
        )
        
        assert subtask.parent_task_id.value == task_id
        assert subtask.title == subtask_data["title"]