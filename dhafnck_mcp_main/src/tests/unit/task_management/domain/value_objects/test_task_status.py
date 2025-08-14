"""Test suite for TaskStatus value object

This module tests the TaskStatus value object following DDD principles.
Tests verify immutability, validation, state transitions, and enum handling.
"""

import pytest

from fastmcp.task_management.domain.value_objects.task_status import TaskStatus, TaskStatusEnum



pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests

class TestTaskStatusValueObject:
    
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

    """Test suite for TaskStatus value object"""
    
    # ========== Valid Creation Tests ==========
    
    def test_task_status_creation_with_valid_enum_value(self):
        """TaskStatus can be created with valid enum value"""
        # Act
        status = TaskStatus("todo")
        
        # Assert
        assert status.value == "todo"
        assert str(status) == "todo"
    
    def test_task_status_creation_with_all_valid_statuses(self):
        """TaskStatus can be created with any valid status value"""
        # Arrange
        valid_statuses = [
            "todo",
            "in_progress",
            "blocked",
            "review",
            "testing",
            "done",
            "cancelled",
            "archived"
        ]
        
        # Act & Assert
        for status_value in valid_statuses:
            status = TaskStatus(status_value)
            assert status.value == status_value
    
    def test_task_status_factory_methods(self):
        """TaskStatus factory methods create correct instances"""
        # Act & Assert
        assert TaskStatus.todo().value == "todo"
        assert TaskStatus.in_progress().value == "in_progress"
        assert TaskStatus.blocked().value == "blocked"
        assert TaskStatus.review().value == "review"
        assert TaskStatus.testing().value == "testing"
        assert TaskStatus.done().value == "done"
        assert TaskStatus.cancelled().value == "cancelled"
        assert TaskStatus.archived().value == "archived"
    
    def test_task_status_from_string_with_whitespace(self):
        """from_string trims whitespace from input"""
        # Arrange
        status_with_spaces = "  todo  "
        
        # Act
        status = TaskStatus.from_string(status_with_spaces)
        
        # Assert
        assert status.value == "todo"
    
    def test_task_status_from_string_with_empty_defaults_to_todo(self):
        """from_string with empty/None defaults to todo"""
        # Act
        status_empty = TaskStatus.from_string("")
        status_none = TaskStatus.from_string(None)
        
        # Assert
        assert status_empty.value == "todo"
        assert status_none.value == "todo"
    
    # ========== Validation Tests ==========
    
    def test_task_status_creation_with_empty_string_raises_error(self):
        """TaskStatus cannot be created with empty string"""
        with pytest.raises(ValueError, match="Task status cannot be empty"):
            TaskStatus("")
    
    def test_task_status_creation_with_none_raises_error(self):
        """TaskStatus cannot be created with None"""
        with pytest.raises(ValueError, match="Task status cannot be empty"):
            TaskStatus(None)
    
    def test_task_status_creation_with_invalid_value_raises_error(self):
        """TaskStatus validates against enum values"""
        invalid_values = [
            "pending",
            "completed",
            "TODO",  # Wrong case
            "IN_PROGRESS",  # Wrong case
            "in progress",  # Space instead of underscore
            "random_status",
            "123",
            "done!"
        ]
        
        for invalid in invalid_values:
            with pytest.raises(ValueError) as exc_info:
                TaskStatus(invalid)
            assert "Invalid task status" in str(exc_info.value)
            assert invalid in str(exc_info.value)
            assert "Valid statuses:" in str(exc_info.value)
    
    # ========== Immutability Tests ==========
    
    def test_task_status_is_immutable(self):
        """TaskStatus value cannot be modified after creation (frozen dataclass)"""
        # Arrange
        status = TaskStatus.todo()
        
        # Act & Assert
        with pytest.raises(AttributeError):
            status.value = "done"
    
    def test_task_status_dataclass_is_frozen(self):
        """TaskStatus dataclass is properly frozen"""
        # Arrange
        status = TaskStatus.in_progress()
        
        # Verify the dataclass is frozen
        assert hasattr(status, "__frozen__") or status.__class__.__dataclass_params__.frozen
    
    # ========== Equality and Hashing Tests ==========
    
    def test_task_status_equality(self):
        """TaskStatus instances with same value are equal"""
        # Arrange
        status1 = TaskStatus("todo")
        status2 = TaskStatus("todo")
        status3 = TaskStatus.todo()
        status4 = TaskStatus("done")
        
        # Assert
        assert status1 == status2
        assert status1 == status3
        assert status2 == status3
        assert status1 != status4
    
    def test_task_status_not_equal_to_other_types(self):
        """TaskStatus is not equal to other types"""
        # Arrange
        status = TaskStatus.todo()
        
        # Assert
        assert status != "todo"
        assert status != TaskStatusEnum.TODO
        assert status != 123
        assert status != None
        assert status != object()
    
    def test_task_status_hashable(self):
        """TaskStatus can be used in sets and as dict keys"""
        # Arrange
        status1 = TaskStatus("todo")
        status2 = TaskStatus("todo")  # Same value
        status3 = TaskStatus("done")  # Different value
        
        # Act - Use in set
        status_set = {status1, status2, status3}
        
        # Assert
        assert len(status_set) == 2  # status1 and status2 are same
        
        # Act - Use as dict key
        status_dict = {status1: "value1", status3: "value3"}
        status_dict[status2] = "value2"  # Should overwrite status1's value
        
        # Assert
        assert len(status_dict) == 2
        assert status_dict[status1] == "value2"  # Overwritten by status2
    
    def test_task_status_hash_consistency(self):
        """TaskStatus hash is consistent with equality"""
        # Arrange
        status1 = TaskStatus("in_progress")
        status2 = TaskStatus("in_progress")
        
        # Assert
        assert hash(status1) == hash(status2)  # Equal objects have equal hashes
    
    # ========== String Representation Tests ==========
    
    def test_task_status_string_representation(self):
        """TaskStatus string representation returns the value"""
        # Arrange
        status = TaskStatus("review")
        
        # Assert
        assert str(status) == "review"
        assert repr(status) == "TaskStatus(value='review')"
    
    # ========== Helper Method Tests ==========
    
    def test_is_todo_method(self):
        """is_todo correctly identifies todo status"""
        # Arrange
        todo_status = TaskStatus.todo()
        other_status = TaskStatus.in_progress()
        
        # Assert
        assert todo_status.is_todo() is True
        assert other_status.is_todo() is False
    
    def test_is_in_progress_method(self):
        """is_in_progress correctly identifies in_progress status"""
        # Arrange
        in_progress_status = TaskStatus.in_progress()
        other_status = TaskStatus.todo()
        
        # Assert
        assert in_progress_status.is_in_progress() is True
        assert other_status.is_in_progress() is False
    
    def test_is_done_method(self):
        """is_done correctly identifies done status"""
        # Arrange
        done_status = TaskStatus.done()
        other_status = TaskStatus.review()
        
        # Assert
        assert done_status.is_done() is True
        assert other_status.is_done() is False
    
    def test_is_completed_alias_method(self):
        """is_completed is an alias for is_done"""
        # Arrange
        done_status = TaskStatus.done()
        other_status = TaskStatus.testing()
        
        # Assert
        assert done_status.is_completed() is True
        assert done_status.is_completed() == done_status.is_done()
        assert other_status.is_completed() is False
    
    # ========== State Transition Tests ==========
    
    def test_can_transition_to_valid_transitions(self):
        """can_transition_to allows valid state transitions"""
        # Test valid transitions from TODO
        todo = TaskStatus.todo()
        assert todo.can_transition_to("in_progress") is True
        assert todo.can_transition_to("cancelled") is True
        assert todo.can_transition_to("done") is False  # Invalid
        
        # Test valid transitions from IN_PROGRESS
        in_progress = TaskStatus.in_progress()
        assert in_progress.can_transition_to("blocked") is True
        assert in_progress.can_transition_to("review") is True
        assert in_progress.can_transition_to("testing") is True
        assert in_progress.can_transition_to("cancelled") is True
        assert in_progress.can_transition_to("done") is True
        assert in_progress.can_transition_to("todo") is False  # Invalid
        
        # Test valid transitions from BLOCKED
        blocked = TaskStatus.blocked()
        assert blocked.can_transition_to("in_progress") is True
        assert blocked.can_transition_to("cancelled") is True
        assert blocked.can_transition_to("done") is False  # Invalid
        
        # Test valid transitions from REVIEW
        review = TaskStatus.review()
        assert review.can_transition_to("in_progress") is True
        assert review.can_transition_to("testing") is True
        assert review.can_transition_to("done") is True
        assert review.can_transition_to("cancelled") is True
        assert review.can_transition_to("todo") is False  # Invalid
        
        # Test valid transitions from TESTING
        testing = TaskStatus.testing()
        assert testing.can_transition_to("in_progress") is True
        assert testing.can_transition_to("review") is True
        assert testing.can_transition_to("done") is True
        assert testing.can_transition_to("cancelled") is True
        assert testing.can_transition_to("todo") is False  # Invalid
    
    def test_can_transition_to_terminal_states(self):
        """Terminal states (done, archived) don't allow transitions"""
        # DONE state allows no transitions
        done = TaskStatus.done()
        assert done.can_transition_to("todo") is False
        assert done.can_transition_to("in_progress") is False
        assert done.can_transition_to("review") is False
        assert done.can_transition_to("cancelled") is False
        
        # ARCHIVED state allows no transitions
        archived = TaskStatus.archived()
        assert archived.can_transition_to("todo") is False
        assert archived.can_transition_to("in_progress") is False
        assert archived.can_transition_to("done") is False
    
    def test_can_transition_to_cancelled_can_reopen(self):
        """Cancelled tasks can be reopened to todo"""
        # CANCELLED can transition back to TODO
        cancelled = TaskStatus.cancelled()
        assert cancelled.can_transition_to("todo") is True
        assert cancelled.can_transition_to("in_progress") is False
        assert cancelled.can_transition_to("done") is False
    
    def test_can_transition_to_invalid_status(self):
        """can_transition_to handles invalid status gracefully"""
        # Arrange
        status = TaskStatus.todo()
        
        # Act & Assert - Invalid status returns False (doesn't raise)
        assert status.can_transition_to("invalid_status") is False
        assert status.can_transition_to("") is False
        assert status.can_transition_to(None) is False
    
    def test_can_transition_to_self(self):
        """Status cannot transition to itself (not in allowed transitions)"""
        # Arrange
        statuses = [
            TaskStatus.todo(),
            TaskStatus.in_progress(),
            TaskStatus.blocked(),
            TaskStatus.review(),
            TaskStatus.testing(),
            TaskStatus.done(),
            TaskStatus.cancelled(),
            TaskStatus.archived()
        ]
        
        # Act & Assert
        for status in statuses:
            assert status.can_transition_to(status.value) is False
    
    # ========== Enum Integration Tests ==========
    
    def test_task_status_enum_values_match(self):
        """TaskStatus values match TaskStatusEnum values"""
        # Assert all enum values work with TaskStatus
        assert TaskStatus(TaskStatusEnum.TODO.value).value == "todo"
        assert TaskStatus(TaskStatusEnum.IN_PROGRESS.value).value == "in_progress"
        assert TaskStatus(TaskStatusEnum.BLOCKED.value).value == "blocked"
        assert TaskStatus(TaskStatusEnum.REVIEW.value).value == "review"
        assert TaskStatus(TaskStatusEnum.TESTING.value).value == "testing"
        assert TaskStatus(TaskStatusEnum.DONE.value).value == "done"
        assert TaskStatus(TaskStatusEnum.CANCELLED.value).value == "cancelled"
        assert TaskStatus(TaskStatusEnum.ARCHIVED.value).value == "archived"
    
    def test_all_enum_values_have_factory_methods(self):
        """Every TaskStatusEnum value has a corresponding factory method"""
        # Get all enum values
        enum_values = {status.value for status in TaskStatusEnum}
        
        # Get all factory method values
        factory_methods = {
            TaskStatus.todo().value,
            TaskStatus.in_progress().value,
            TaskStatus.blocked().value,
            TaskStatus.review().value,
            TaskStatus.testing().value,
            TaskStatus.done().value,
            TaskStatus.cancelled().value,
            TaskStatus.archived().value
        }
        
        # Assert they match
        assert enum_values == factory_methods
    
    # ========== Business Logic Tests ==========
    
    def test_workflow_progression_path(self):
        """Test typical workflow progression through statuses"""
        # Typical happy path: todo → in_progress → review → testing → done
        todo = TaskStatus.todo()
        assert todo.can_transition_to("in_progress") is True
        
        in_progress = TaskStatus.in_progress()
        assert in_progress.can_transition_to("review") is True
        
        review = TaskStatus.review()
        assert review.can_transition_to("testing") is True
        
        testing = TaskStatus.testing()
        assert testing.can_transition_to("done") is True
        
        done = TaskStatus.done()
        # No transitions from done
        assert done.can_transition_to("archived") is False
    
    def test_blocked_workflow_path(self):
        """Test workflow when task gets blocked"""
        # Task gets blocked and then unblocked
        in_progress = TaskStatus.in_progress()
        assert in_progress.can_transition_to("blocked") is True
        
        blocked = TaskStatus.blocked()
        assert blocked.can_transition_to("in_progress") is True
        
        # Blocked task can be cancelled
        assert blocked.can_transition_to("cancelled") is True
    
    def test_review_rejection_workflow(self):
        """Test workflow when review finds issues"""
        # Review can go back to in_progress if issues found
        review = TaskStatus.review()
        assert review.can_transition_to("in_progress") is True
        
        # Testing can also go back to in_progress or review
        testing = TaskStatus.testing()
        assert testing.can_transition_to("in_progress") is True
        assert testing.can_transition_to("review") is True