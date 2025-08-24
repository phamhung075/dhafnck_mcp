"""Comprehensive test suite for Subtask Domain Entity"""

import pytest
from datetime import datetime, timezone
from typing import List

from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus, TaskStatusEnum
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.enums.agent_roles import AgentRole
from fastmcp.task_management.domain.events.task_events import TaskUpdated


class TestSubtask:
    """Test suite for Subtask domain entity"""
    
    @pytest.fixture
    def parent_task_id(self):
        """Create a parent task ID"""
        return TaskId.from_string("parent-task-123")
    
    @pytest.fixture
    def subtask_id(self):
        """Create a subtask ID"""
        return SubtaskId("subtask-456")
    
    @pytest.fixture
    def basic_subtask(self, parent_task_id, subtask_id):
        """Create a basic subtask for testing"""
        return Subtask(
            id=subtask_id,
            title="Test Subtask",
            description="Test subtask description",
            parent_task_id=parent_task_id
        )
    
    def test_init_with_required_fields(self, parent_task_id):
        """Test subtask initialization with only required fields"""
        subtask = Subtask(
            title="Test Subtask",
            description="Test description",
            parent_task_id=parent_task_id
        )
        
        assert subtask.title == "Test Subtask"
        assert subtask.description == "Test description"
        assert subtask.parent_task_id == parent_task_id
        assert subtask.id is None
        assert subtask.status == TaskStatus.todo()
        assert subtask.priority == Priority.medium()
        assert subtask.assignees == []
        assert subtask.progress_percentage == 0
        assert subtask.created_at is not None
        assert subtask.updated_at is not None
        assert subtask.created_at.tzinfo is not None  # Timezone aware
        assert subtask.updated_at.tzinfo is not None
    
    def test_init_with_all_fields(self, parent_task_id, subtask_id):
        """Test subtask initialization with all fields"""
        now = datetime.now(timezone.utc)
        subtask = Subtask(
            id=subtask_id,
            title="Complete Subtask",
            description="Complete description",
            parent_task_id=parent_task_id,
            status=TaskStatus.in_progress(),
            priority=Priority.high(),
            assignees=["user1", "user2"],
            progress_percentage=50,
            created_at=now,
            updated_at=now
        )
        
        assert subtask.id == subtask_id
        assert subtask.title == "Complete Subtask"
        assert subtask.description == "Complete description"
        assert subtask.parent_task_id == parent_task_id
        assert subtask.status == TaskStatus.in_progress()
        assert subtask.priority == Priority.high()
        assert subtask.assignees == ["user1", "user2"]
        assert subtask.progress_percentage == 50
        assert subtask.created_at == now
        assert subtask.updated_at == now
    
    def test_post_init_timezone_handling(self, parent_task_id):
        """Test that timestamps are made timezone-aware in post_init"""
        # Create with naive timestamps
        naive_created = datetime(2024, 1, 1, 12, 0, 0)
        naive_updated = datetime(2024, 1, 2, 12, 0, 0)
        
        subtask = Subtask(
            title="Test",
            description="Test",
            parent_task_id=parent_task_id,
            created_at=naive_created,
            updated_at=naive_updated
        )
        
        # Verify timestamps are now timezone-aware
        assert subtask.created_at.tzinfo is not None
        assert subtask.updated_at.tzinfo is not None
        assert subtask.created_at.tzinfo == timezone.utc
        assert subtask.updated_at.tzinfo == timezone.utc
    
    def test_equality(self, parent_task_id, subtask_id):
        """Test subtask equality based on ID"""
        subtask1 = Subtask(
            id=subtask_id,
            title="Subtask 1",
            description="Description 1",
            parent_task_id=parent_task_id
        )
        
        subtask2 = Subtask(
            id=subtask_id,
            title="Subtask 2",  # Different title
            description="Description 2",  # Different description
            parent_task_id=parent_task_id
        )
        
        subtask3 = Subtask(
            id=SubtaskId("different-id"),
            title="Subtask 1",
            description="Description 1",
            parent_task_id=parent_task_id
        )
        
        # Same ID = equal
        assert subtask1 == subtask2
        
        # Different ID = not equal
        assert subtask1 != subtask3
        
        # Not a subtask = not equal
        assert subtask1 != "not a subtask"
        
        # None ID subtasks are not equal
        subtask_no_id1 = Subtask("Title", "Desc", parent_task_id)
        subtask_no_id2 = Subtask("Title", "Desc", parent_task_id)
        assert subtask_no_id1 != subtask_no_id2
    
    def test_hash(self, parent_task_id, subtask_id):
        """Test subtask hashing"""
        subtask_with_id = Subtask(
            id=subtask_id,
            title="Test",
            description="Test",
            parent_task_id=parent_task_id
        )
        
        subtask_without_id = Subtask(
            title="Test Title",
            description="Test",
            parent_task_id=parent_task_id
        )
        
        # Hash based on ID if present
        assert hash(subtask_with_id) == hash(subtask_id)
        
        # Hash based on title if no ID
        assert hash(subtask_without_id) == hash("Test Title")
    
    def test_is_completed_property(self, basic_subtask):
        """Test is_completed property"""
        # Initially not completed
        assert not basic_subtask.is_completed
        
        # Mark as done
        basic_subtask.status = TaskStatus.done()
        assert basic_subtask.is_completed
    
    def test_can_be_assigned_property(self, basic_subtask):
        """Test can_be_assigned property"""
        # Initially can be assigned
        assert basic_subtask.can_be_assigned
        
        # Cannot be assigned when done
        basic_subtask.status = TaskStatus.done()
        assert not basic_subtask.can_be_assigned
        
        # Cannot be assigned when cancelled
        basic_subtask.status = TaskStatus(TaskStatusEnum.CANCELLED.value)
        assert not basic_subtask.can_be_assigned
    
    def test_validation_empty_title(self, parent_task_id):
        """Test validation rejects empty title"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            Subtask(
                title="",
                description="Test",
                parent_task_id=parent_task_id
            )
        
        with pytest.raises(ValueError, match="title cannot be empty"):
            Subtask(
                title="   ",  # Whitespace only
                description="Test",
                parent_task_id=parent_task_id
            )
    
    def test_validation_title_too_long(self, parent_task_id):
        """Test validation rejects title over 200 characters"""
        long_title = "x" * 201
        with pytest.raises(ValueError, match="title cannot exceed 200 characters"):
            Subtask(
                title=long_title,
                description="Test",
                parent_task_id=parent_task_id
            )
    
    def test_validation_description_too_long(self, parent_task_id):
        """Test validation rejects description over 500 characters"""
        long_description = "x" * 501
        with pytest.raises(ValueError, match="description cannot exceed 500 characters"):
            Subtask(
                title="Test",
                description=long_description,
                parent_task_id=parent_task_id
            )
    
    def test_validation_missing_parent_task_id(self):
        """Test validation rejects missing parent task ID"""
        with pytest.raises(ValueError, match="must have a parent task ID"):
            Subtask(
                title="Test",
                description="Test",
                parent_task_id=None
            )
    
    def test_update_status_valid_transition(self, basic_subtask):
        """Test updating status with valid transition"""
        # Todo -> In Progress
        basic_subtask.update_status(TaskStatus.in_progress())
        assert basic_subtask.status == TaskStatus.in_progress()
        assert basic_subtask.updated_at is not None
        
        # Check event was raised
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskUpdated)
        assert events[0].field_name == "subtask_status"
    
    def test_update_status_invalid_transition(self, basic_subtask):
        """Test updating status with invalid transition"""
        # Set to done first
        basic_subtask.status = TaskStatus.done()
        basic_subtask._events.clear()
        
        # Try invalid transition: Done -> Todo
        with pytest.raises(ValueError, match="Cannot transition"):
            basic_subtask.update_status(TaskStatus.todo())
    
    def test_update_priority(self, basic_subtask):
        """Test updating priority"""
        original_priority = basic_subtask.priority
        
        basic_subtask.update_priority(Priority.high())
        
        assert basic_subtask.priority == Priority.high()
        assert basic_subtask.updated_at is not None
        
        # Check event
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert events[0].field_name == "subtask_priority"
        assert f"{original_priority}" in events[0].old_value
        assert f"{Priority.high()}" in events[0].new_value
    
    def test_update_title(self, basic_subtask):
        """Test updating title"""
        original_title = basic_subtask.title
        
        basic_subtask.update_title("Updated Title")
        
        assert basic_subtask.title == "Updated Title"
        assert basic_subtask.updated_at is not None
        
        # Check event
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert events[0].field_name == "subtask_title"
        assert original_title in events[0].old_value
        assert "Updated Title" in events[0].new_value
    
    def test_update_title_empty(self, basic_subtask):
        """Test updating title with empty value"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            basic_subtask.update_title("")
        
        with pytest.raises(ValueError, match="title cannot be empty"):
            basic_subtask.update_title("   ")
    
    def test_update_description(self, basic_subtask):
        """Test updating description"""
        original_description = basic_subtask.description
        
        basic_subtask.update_description("Updated description")
        
        assert basic_subtask.description == "Updated description"
        assert basic_subtask.updated_at is not None
        
        # Check event
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert events[0].field_name == "subtask_description"
        assert original_description in events[0].old_value
        assert "Updated description" in events[0].new_value
    
    def test_update_assignees(self, basic_subtask):
        """Test updating assignees"""
        basic_subtask.update_assignees(["user1", "user2", "user3"])
        
        assert basic_subtask.assignees == ["user1", "user2", "user3"]
        assert basic_subtask.updated_at is not None
        
        # Check event
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert events[0].field_name == "subtask_assignees"
    
    def test_update_assignees_with_agent_roles(self, basic_subtask):
        """Test updating assignees with agent role validation"""
        # Mix of valid roles and regular users
        basic_subtask.update_assignees([
            "@coding_agent",  # Valid agent role
            "user1",  # Regular user
            "test_orchestrator",  # Legacy role name (should be resolved)
            "",  # Empty string (should be filtered)
            "   ",  # Whitespace (should be filtered)
        ])
        
        # Verify resolution and filtering
        assert "@coding_agent" in basic_subtask.assignees
        assert "user1" in basic_subtask.assignees
        assert "@test_orchestrator_agent" in basic_subtask.assignees  # Resolved
        assert "" not in basic_subtask.assignees
        assert "   " not in basic_subtask.assignees
    
    def test_update_progress_percentage(self, basic_subtask):
        """Test updating progress percentage"""
        # Update to 25%
        basic_subtask.update_progress_percentage(25)
        assert basic_subtask.progress_percentage == 25
        assert basic_subtask.status == TaskStatus.in_progress()  # Auto-updated
        
        # Update to 100%
        basic_subtask.update_progress_percentage(100)
        assert basic_subtask.progress_percentage == 100
        assert basic_subtask.status == TaskStatus.done()  # Auto-updated
        
        # Update to 0%
        basic_subtask.update_progress_percentage(0)
        assert basic_subtask.progress_percentage == 0
        assert basic_subtask.status == TaskStatus.todo()  # Auto-updated
    
    def test_update_progress_percentage_invalid(self, basic_subtask):
        """Test updating progress with invalid values"""
        with pytest.raises(ValueError, match="must be integer between 0-100"):
            basic_subtask.update_progress_percentage(-1)
        
        with pytest.raises(ValueError, match="must be integer between 0-100"):
            basic_subtask.update_progress_percentage(101)
        
        with pytest.raises(ValueError, match="must be integer between 0-100"):
            basic_subtask.update_progress_percentage("50")  # String instead of int
    
    def test_add_assignee_string(self, basic_subtask):
        """Test adding assignee as string"""
        basic_subtask.add_assignee("user1")
        assert "user1" in basic_subtask.assignees
        
        # Add same assignee again - should not duplicate
        basic_subtask.add_assignee("user1")
        assert basic_subtask.assignees.count("user1") == 1
    
    def test_add_assignee_agent_role_enum(self, basic_subtask):
        """Test adding assignee as AgentRole enum"""
        basic_subtask.add_assignee(AgentRole.CODING_AGENT)
        assert "@coding_agent" in basic_subtask.assignees
    
    def test_add_assignee_with_resolution(self, basic_subtask):
        """Test adding assignee with legacy name resolution"""
        basic_subtask.add_assignee("test_orchestrator")  # Legacy name
        assert "@test_orchestrator_agent" in basic_subtask.assignees
    
    def test_add_assignee_empty(self, basic_subtask):
        """Test adding empty assignee"""
        original_assignees = basic_subtask.assignees.copy()
        
        basic_subtask.add_assignee("")
        basic_subtask.add_assignee("   ")
        basic_subtask.add_assignee(None)
        
        # Should not add empty assignees
        assert basic_subtask.assignees == original_assignees
    
    def test_remove_assignee(self, basic_subtask):
        """Test removing assignee"""
        # Add assignees first
        basic_subtask.assignees = ["user1", "user2", "@coding_agent"]
        
        # Remove string assignee
        basic_subtask.remove_assignee("user1")
        assert "user1" not in basic_subtask.assignees
        assert "user2" in basic_subtask.assignees
        
        # Remove agent role enum
        basic_subtask.remove_assignee(AgentRole.CODING_AGENT)
        assert "@coding_agent" not in basic_subtask.assignees
        
        # Remove non-existent assignee (should not error)
        basic_subtask.remove_assignee("user3")
    
    def test_complete(self, basic_subtask):
        """Test marking subtask as complete"""
        basic_subtask.complete()
        
        assert basic_subtask.is_completed
        assert basic_subtask.status == TaskStatus.done()
        
        # Check event
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert events[0].field_name == "subtask_status"
        assert "done" in events[0].new_value
        
        # Complete again should not raise event
        basic_subtask.complete()
        assert len(basic_subtask._events) == 0  # No new events
    
    def test_reopen(self, basic_subtask):
        """Test reopening a completed subtask"""
        # Complete first
        basic_subtask.status = TaskStatus.done()
        basic_subtask._events.clear()
        
        basic_subtask.reopen()
        
        assert not basic_subtask.is_completed
        assert basic_subtask.status == TaskStatus.todo()
        
        # Check event
        events = basic_subtask.get_events()
        assert len(events) == 1
        assert events[0].field_name == "subtask_status"
        assert "todo" in events[0].new_value
        
        # Reopen non-completed should not raise event
        basic_subtask.reopen()
        assert len(basic_subtask._events) == 0
    
    def test_get_events(self, basic_subtask):
        """Test getting and clearing events"""
        # Generate some events
        basic_subtask.update_title("New Title")
        basic_subtask.update_priority(Priority.high())
        
        # Get events
        events = basic_subtask.get_events()
        assert len(events) == 2
        assert all(isinstance(e, TaskUpdated) for e in events)
        
        # Events should be cleared
        assert len(basic_subtask._events) == 0
        
        # Getting again returns empty list
        assert basic_subtask.get_events() == []
    
    def test_to_dict(self, parent_task_id, subtask_id):
        """Test converting subtask to dictionary"""
        now = datetime.now(timezone.utc)
        subtask = Subtask(
            id=subtask_id,
            title="Test Subtask",
            description="Test description",
            parent_task_id=parent_task_id,
            status=TaskStatus.in_progress(),
            priority=Priority.high(),
            assignees=["user1", "@coding_agent"],
            progress_percentage=75,
            created_at=now,
            updated_at=now
        )
        
        result = subtask.to_dict()
        
        assert result["id"] == subtask_id.value
        assert result["title"] == "Test Subtask"
        assert result["description"] == "Test description"
        assert result["parent_task_id"] == str(parent_task_id)
        assert result["status"] == "in_progress"
        assert result["priority"] == "high"
        assert result["assignees"] == ["user1", "@coding_agent"]
        assert result["progress_percentage"] == 75
        assert result["created_at"] == now.isoformat()
        assert result["updated_at"] == now.isoformat()
    
    def test_to_dict_with_agent_role_enums(self, parent_task_id):
        """Test to_dict handles AgentRole enums in assignees"""
        subtask = Subtask(
            title="Test",
            description="Test",
            parent_task_id=parent_task_id,
            assignees=[AgentRole.CODING_AGENT, "user1", AgentRole.TEST_ORCHESTRATOR_AGENT]
        )
        
        result = subtask.to_dict()
        
        # AgentRole enums should be converted to strings with @ prefix
        assert result["assignees"] == ["@coding_agent", "user1", "@test_orchestrator_agent"]
    
    def test_create_factory_method(self, parent_task_id, subtask_id):
        """Test create factory method"""
        subtask = Subtask.create(
            id=subtask_id,
            title="Created Subtask",
            description="Created description",
            parent_task_id=parent_task_id,
            status=TaskStatus.in_progress(),
            priority=Priority.high(),
            assignees=["user1"],
            progress_percentage=50
        )
        
        assert subtask.id == subtask_id
        assert subtask.title == "Created Subtask"
        assert subtask.description == "Created description"
        assert subtask.parent_task_id == parent_task_id
        assert subtask.status == TaskStatus.in_progress()
        assert subtask.priority == Priority.high()
        assert subtask.assignees == ["user1"]
        assert subtask.progress_percentage == 50
    
    def test_create_factory_method_with_defaults(self, parent_task_id, subtask_id):
        """Test create factory method with default values"""
        subtask = Subtask.create(
            id=subtask_id,
            title="Created Subtask",
            description="Created description",
            parent_task_id=parent_task_id
        )
        
        assert subtask.status == TaskStatus.todo()
        assert subtask.priority == Priority.medium()
        assert subtask.assignees == []
        assert subtask.progress_percentage == 0
    
    def test_create_factory_method_filters_kwargs(self, parent_task_id, subtask_id):
        """Test create factory method filters invalid kwargs"""
        # Pass some invalid kwargs
        subtask = Subtask.create(
            id=subtask_id,
            title="Test",
            description="Test",
            parent_task_id=parent_task_id,
            invalid_field="should be ignored",
            another_invalid="also ignored",
            assignees=["user1"]  # Valid field
        )
        
        assert subtask.assignees == ["user1"]
        assert not hasattr(subtask, "invalid_field")
        assert not hasattr(subtask, "another_invalid")
    
    def test_from_dict(self, parent_task_id):
        """Test creating subtask from dictionary"""
        data = {
            "id": "subtask-999",
            "title": "From Dict Subtask",
            "description": "From dict description",
            "status": "in_progress",
            "priority": "high",
            "assignees": ["user1", "user2"],
            "progress_percentage": 60,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-02T12:00:00"
        }
        
        subtask = Subtask.from_dict(data, parent_task_id)
        
        assert subtask.id.value == "subtask-999"
        assert subtask.title == "From Dict Subtask"
        assert subtask.description == "From dict description"
        assert subtask.parent_task_id == parent_task_id
        assert subtask.status == TaskStatus.in_progress()
        assert subtask.priority == Priority.high()
        assert subtask.assignees == ["user1", "user2"]
        assert subtask.progress_percentage == 60
        assert subtask.created_at == datetime.fromisoformat("2024-01-01T12:00:00")
        assert subtask.updated_at == datetime.fromisoformat("2024-01-02T12:00:00")
    
    def test_from_dict_with_defaults(self, parent_task_id):
        """Test from_dict with minimal data uses defaults"""
        data = {
            "title": "Minimal Subtask"
        }
        
        subtask = Subtask.from_dict(data, parent_task_id)
        
        assert subtask.id is None
        assert subtask.title == "Minimal Subtask"
        assert subtask.description == ""
        assert subtask.status == TaskStatus.todo()
        assert subtask.priority == Priority.medium()
        assert subtask.assignees == []
        assert subtask.progress_percentage == 0
        assert subtask.created_at is None
        assert subtask.updated_at is None
    
    def test_domain_events_include_subtask_id(self, basic_subtask):
        """Test that domain events include subtask ID in values"""
        # Perform various updates
        basic_subtask.update_title("New Title")
        basic_subtask.update_status(TaskStatus.in_progress())
        basic_subtask.add_assignee("user1")
        
        # Get events
        events = basic_subtask.get_events()
        
        # Verify all events include subtask ID
        for event in events:
            assert isinstance(event, TaskUpdated)
            assert str(basic_subtask.id) in event.old_value or str(basic_subtask.id) in event.new_value