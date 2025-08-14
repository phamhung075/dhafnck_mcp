#!/usr/bin/env python3
"""
Test to verify that the Subtask.create() factory method properly filters out invalid parameters.

This test was created to address the issue where subtask delete operations failed with:
"Subtask.__init__() got an unexpected keyword argument 'estimated_effort'"

The root cause was that Subtask.create() was using **kwargs and passing through
invalid parameters like 'estimated_effort' to the Subtask constructor.
"""

import pytest
from datetime import datetime, timezone

from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestSubtaskCreateFix:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test suite for Subtask.create() factory method parameter filtering."""

    def test_create_with_valid_parameters_only(self):
        """Test that Subtask.create() works with only valid parameters."""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId.generate_new(),
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=["user1", "user2"]
        )
        
        assert subtask.title == "Test Subtask"
        assert subtask.description == "Test description"
        assert subtask.status.value == "todo"
        assert subtask.priority.value == "medium"
        assert subtask.assignees == ["user1", "user2"]

    def test_create_filters_out_invalid_parameters(self):
        """Test that Subtask.create() filters out invalid parameters like 'estimated_effort'."""
        # This should not raise an exception even with invalid parameters
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId.generate_new(),
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=["user1"],
            # Invalid parameters that should be filtered out
            estimated_effort="2 hours",
            some_random_field="value",
            another_invalid_param=123,
            invalid_boolean=True
        )
        
        assert subtask.title == "Test Subtask"
        assert subtask.description == "Test description"
        assert subtask.assignees == ["user1"]
        
        # Ensure the invalid parameters are not present in the object
        assert not hasattr(subtask, 'estimated_effort')
        assert not hasattr(subtask, 'some_random_field')
        assert not hasattr(subtask, 'another_invalid_param')
        assert not hasattr(subtask, 'invalid_boolean')

    def test_create_allows_valid_optional_parameters(self):
        """Test that Subtask.create() allows valid optional parameters like created_at and updated_at."""
        now = datetime.now(timezone.utc)
        
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId.generate_new(),
            assignees=["user1"],
            created_at=now,
            updated_at=now
        )
        
        assert subtask.title == "Test Subtask"
        assert subtask.assignees == ["user1"]
        assert subtask.created_at == now
        assert subtask.updated_at == now

    def test_create_with_mixed_valid_and_invalid_parameters(self):
        """Test that Subtask.create() accepts valid parameters while filtering out invalid ones."""
        now = datetime.now(timezone.utc)
        
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            title="Mixed Parameters Test",
            description="Test with mixed parameters",
            parent_task_id=TaskId.generate_new(),
            # Valid optional parameters
            assignees=["user1", "user2"],
            created_at=now,
            updated_at=now,
            # Invalid parameters that should be filtered out
            estimated_effort="5 hours",
            completion_percentage=50,
            some_metadata={"key": "value"},
            random_string="should_be_filtered",
            random_number=42
        )
        
        # Verify valid parameters are set
        assert subtask.title == "Mixed Parameters Test"
        assert subtask.description == "Test with mixed parameters"
        assert subtask.assignees == ["user1", "user2"]
        assert subtask.created_at == now
        assert subtask.updated_at == now
        
        # Verify invalid parameters are not present
        assert not hasattr(subtask, 'estimated_effort')
        assert not hasattr(subtask, 'completion_percentage')
        assert not hasattr(subtask, 'some_metadata')
        assert not hasattr(subtask, 'random_string')
        assert not hasattr(subtask, 'random_number')

    def test_create_with_defaults(self):
        """Test that Subtask.create() sets proper defaults for status and priority."""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId.generate_new()
        )
        
        # Check that defaults are set correctly
        assert subtask.status.value == "todo"
        assert subtask.priority.value == "medium"
        assert subtask.assignees == []  # Default from __post_init__

    def test_create_overrides_defaults(self):
        """Test that Subtask.create() allows overriding defaults for status and priority."""
        subtask = Subtask.create(
            id=SubtaskId.generate_new(),
            title="Test Subtask",
            description="Test description",
            parent_task_id=TaskId.generate_new(),
            status=TaskStatus.in_progress(),
            priority=Priority.high()
        )
        
        assert subtask.status.value == "in_progress"
        assert subtask.priority.value == "high"

    def test_create_backward_compatibility(self):
        """Test that the fix doesn't break existing code that uses Subtask.create()."""
        # This simulates how the factory method might be called in existing code
        task_id = TaskId.generate_new()
        subtask_id = SubtaskId.generate_new()
        
        subtask = Subtask.create(
            id=subtask_id,
            title="Backward Compatibility Test",
            description="Testing existing usage patterns",
            parent_task_id=task_id,
            assignees=["existing_user"]
        )
        
        assert subtask.id == subtask_id
        assert subtask.title == "Backward Compatibility Test"
        assert subtask.description == "Testing existing usage patterns"
        assert subtask.parent_task_id == task_id
        assert subtask.assignees == ["existing_user"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])