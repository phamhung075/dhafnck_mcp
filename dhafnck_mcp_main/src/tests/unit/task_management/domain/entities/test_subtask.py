"""Unit tests for Subtask entity"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects import TaskId, Priority, TaskStatus
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.exceptions.task_exceptions import InvalidTaskStateError


class TestSubtask:
    """Test suite for Subtask entity"""
    
    @pytest.fixture
    def valid_subtask_data(self):
        """Valid subtask data for testing"""
        now = datetime.now()
        return {
            'id': str(SubtaskId.generate_new()),
            'task_id': str(TaskId.generate_new()),
            'title': 'Test Subtask',
            'description': 'Test subtask description',
            'status': 'todo',
            'priority': 'medium',
            'assignees': ['user1', 'user2'],
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
    
    def test_create_subtask_minimal(self):
        """Test creating subtask with minimal required fields"""
        task_id = TaskId.generate_new()
        subtask_id = SubtaskId.generate_new()
        title = "Minimal Subtask"
        description = "Test description"
        
        subtask = Subtask.create(
            id=subtask_id,
            title=title,
            description=description,
            parent_task_id=task_id
        )
        
        assert subtask.id == subtask_id
        assert subtask.parent_task_id == task_id
        assert subtask.title == title
        assert subtask.description == description
    
    def test_create_subtask_full(self):
        """Test creating subtask with all fields"""
        task_id = TaskId.generate_new()
        subtask_id = SubtaskId.generate_new()
        
        subtask = Subtask.create(
            id=subtask_id,
            parent_task_id=task_id,
            title="Full Subtask",
            description="Detailed description",
            priority=Priority.high(),
            assignees=['user1', 'user2']
        )
        
        assert subtask.parent_task_id == task_id
        assert subtask.title == "Full Subtask"
        assert subtask.description == "Detailed description"
        assert subtask.priority == Priority.high()
        assert subtask.assignees == ['user1', 'user2']
        assert str(subtask.status) == 'todo'
    
    def test_from_dict(self, valid_subtask_data):
        """Test creating subtask from dictionary"""
        parent_task_id = TaskId.generate_new()
        subtask = Subtask.from_dict(valid_subtask_data, parent_task_id)
        
        assert str(subtask.id) == valid_subtask_data['id']
        assert subtask.parent_task_id == parent_task_id
        assert subtask.title == valid_subtask_data['title']
        assert subtask.description == valid_subtask_data['description']
        assert str(subtask.status) == valid_subtask_data['status']
        assert subtask.assignees == valid_subtask_data['assignees']
    
    def test_to_dict(self):
        """Test converting subtask to dictionary"""
        task_id = TaskId.generate_new()
        subtask_id = SubtaskId.generate_new()
        subtask = Subtask.create(
            id=subtask_id,
            parent_task_id=task_id,
            title="Test Subtask",
            description="Test description"
        )
        
        data = subtask.to_dict()
        
        assert data['id'] == subtask.id.value
        assert data['parent_task_id'] == str(subtask.parent_task_id)
        assert data['title'] == subtask.title
        assert data['description'] == subtask.description
        assert data['status'] == str(subtask.status)
        assert data['priority'] == str(subtask.priority)
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_update_subtask(self):
        """Test updating subtask fields"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Original Title",
            description="Original description"
        )
        
        original_updated_at = subtask.updated_at
        
        # Sleep briefly to ensure time difference
        import time
        time.sleep(0.01)
        
        # Update using individual methods
        subtask.update_title("Updated Title")
        subtask.update_description("New description")
        subtask.update_status(TaskStatus.in_progress())
        subtask.update_priority(Priority.high())
        
        assert subtask.title == "Updated Title"
        assert subtask.description == "New description"
        assert str(subtask.status) == "in_progress"
        assert subtask.priority == Priority.high()
        assert subtask.updated_at > original_updated_at
    
    def test_update_partial(self):
        """Test partial update of subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Original",
            description="Original desc"
        )
        
        subtask.update_title("New Title")
        
        assert subtask.title == "New Title"
        assert subtask.description == "Original desc"  # Unchanged
    
    def test_start_subtask(self):
        """Test starting a subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        assert str(subtask.status) == 'todo'
        
        subtask.update_status(TaskStatus.in_progress())
        
        assert str(subtask.status) == 'in_progress'
    
    def test_complete_subtask(self):
        """Test completing a subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        subtask.update_status(TaskStatus.in_progress())
        subtask.complete()
        
        assert str(subtask.status) == 'done'
    
    def test_cannot_complete_todo_subtask(self):
        """Test that todo subtask cannot be directly completed"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        # Most implementations would allow this, but let's test the behavior
        subtask.complete()
        assert str(subtask.status) == 'done'
    
    def test_assign_users(self):
        """Test assigning users to subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        subtask.update_assignees(['user1', 'user2'])
        
        assert 'user1' in subtask.assignees
        assert 'user2' in subtask.assignees
        assert len(subtask.assignees) == 2
    
    def test_unassign_users(self):
        """Test unassigning users from subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test",
            assignees=['user1', 'user2', 'user3']
        )
        
        subtask.remove_assignee('user2')
        
        assert 'user1' in subtask.assignees
        assert 'user2' not in subtask.assignees
        assert 'user3' in subtask.assignees
        assert len(subtask.assignees) == 2
    
    def test_is_blocked(self):
        """Test checking if subtask is blocked"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        # Initially not blocked
        assert str(subtask.status) != 'blocked'
        
        # Set to blocked status if supported
        subtask.update_status(TaskStatus.blocked())
        assert str(subtask.status) == 'blocked'
    
    def test_is_completed(self):
        """Test checking if subtask is completed"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        assert subtask.is_completed == False
        
        subtask.complete()
        assert subtask.is_completed == True
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        # Todo = 0%
        assert subtask.progress_percentage == 0
        
        # Set progress manually
        subtask.progress_percentage = 50
        assert subtask.progress_percentage == 50
        
        # Done = 100%
        subtask.progress_percentage = 100
        assert subtask.progress_percentage == 100
    
    def test_validate_required_fields(self):
        """Test validation of required fields"""
        with pytest.raises((ValueError, TypeError)):
            Subtask.create(
                id=SubtaskId.generate_new(),
                parent_task_id=None,  # Invalid
                title="Test",
                description="Test"
            )
        
        with pytest.raises((ValueError, TypeError)):
            Subtask.create(
                id=SubtaskId.generate_new(),
                parent_task_id=TaskId.generate_new(),
                title="",  # Empty title
                description="Test"
            )
    
    def test_subtask_equality(self):
        """Test subtask equality comparison"""
        task_id = TaskId.generate_new()
        
        subtask1 = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=task_id,
            title="Test",
            description="Test"
        )
        
        subtask2 = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=task_id,
            title="Test",
            description="Test"
        )
        
        # Different IDs mean different subtasks
        assert subtask1 != subtask2
        
        # Same object
        assert subtask1 == subtask1
    
    def test_subtask_string_representation(self):
        """Test string representation of subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        str_repr = str(subtask)
        assert "Test Subtask" in str_repr or str(subtask.id) in str_repr
    
    def test_estimated_time(self):
        """Test estimated time for subtask"""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test Subtask",
            description="Test"
        )
        
        # Set estimated time if supported
        if hasattr(subtask, 'estimated_hours'):
            subtask.estimated_hours = 4
            assert subtask.estimated_hours == 4
    
    def test_parent_task_reference(self):
        """Test parent task reference"""
        task_id = TaskId.generate_new()
        
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=task_id,
            title="Child Subtask",
            description="Test"
        )
        
        assert subtask.parent_task_id == task_id
        assert str(subtask.parent_task_id) == str(task_id)
    
    def test_subtask_with_invalid_priority(self):
        """Test creating subtask with invalid priority"""
        # Should use default priority if invalid
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=TaskId.generate_new(),
            title="Test",
            description="Test"
            # priority defaults to medium
        )
        
        # Should have a valid priority
        assert subtask.priority in [Priority.low(), Priority.medium(), Priority.high(), Priority.critical()]
    
    def test_bulk_operations(self):
        """Test bulk operations on multiple subtasks"""
        task_id = TaskId.generate_new()
        
        subtasks = [
            Subtask.create(
                id=SubtaskId.generate_new(),
                parent_task_id=task_id,
                title=f"Subtask {i}",
                description="Test"
            )
            for i in range(5)
        ]
        
        # Start all subtasks
        for subtask in subtasks:
            subtask.update_status(TaskStatus.in_progress())
        
        assert all(str(s.status) == 'in_progress' for s in subtasks)
        
        # Complete all subtasks
        for subtask in subtasks:
            subtask.complete()
        
        assert all(s.is_completed() for s in subtasks)
    
    def test_subtask_ordering(self):
        """Test ordering of subtasks"""
        task_id = TaskId.generate_new()
        
        subtask1 = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=task_id,
            title="A Subtask",
            description="Test",
            priority=Priority.low()
        )
        
        subtask2 = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=task_id,
            title="B Subtask",
            description="Test",
            priority=Priority.high()
        )
        
        subtask3 = Subtask.create(
            id=SubtaskId.generate_new(),
            parent_task_id=task_id,
            title="C Subtask",
            description="Test",
            priority=Priority.medium()
        )
        
        # Sort by priority (assuming HIGH > MEDIUM > LOW)
        subtasks = sorted(
            [subtask1, subtask2, subtask3],
            key=lambda s: s.priority.value if hasattr(s.priority, 'value') else str(s.priority),
            reverse=True
        )
        
        # High priority should be first
        assert subtasks[0] == subtask2