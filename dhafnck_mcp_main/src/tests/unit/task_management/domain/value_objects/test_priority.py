"""Test suite for Priority value object

This module tests the Priority value object following DDD principles.
Tests verify immutability, validation, ordering, and comparison operations.
"""

import pytest

from fastmcp.task_management.domain.value_objects.priority import Priority, PriorityLevel



pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests

class TestPriorityValueObject:
    
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

    """Test suite for Priority value object"""
    
    # ========== Valid Creation Tests ==========
    
    def test_priority_creation_with_valid_value(self):
        """Priority can be created with valid priority value"""
        # Act
        priority = Priority("high")
        
        # Assert
        assert priority.value == "high"
        assert str(priority) == "high"
    
    def test_priority_creation_with_all_valid_levels(self):
        """Priority can be created with any valid priority level"""
        # Arrange
        valid_priorities = ["low", "medium", "high", "urgent", "critical"]
        
        # Act & Assert
        for priority_value in valid_priorities:
            priority = Priority(priority_value)
            assert priority.value == priority_value
    
    def test_priority_factory_methods(self):
        """Priority factory methods create correct instances"""
        # Act & Assert
        assert Priority.low().value == "low"
        assert Priority.medium().value == "medium"
        assert Priority.high().value == "high"
        assert Priority.urgent().value == "urgent"
        assert Priority.critical().value == "critical"
    
    def test_priority_from_string_with_whitespace(self):
        """from_string trims whitespace from input"""
        # Arrange
        priority_with_spaces = "  high  "
        
        # Act
        priority = Priority.from_string(priority_with_spaces)
        
        # Assert
        assert priority.value == "high"
    
    def test_priority_from_string_with_empty_defaults_to_medium(self):
        """from_string with empty/None defaults to medium"""
        # Act
        priority_empty = Priority.from_string("")
        priority_none = Priority.from_string(None)
        
        # Assert
        assert priority_empty.value == "medium"
        assert priority_none.value == "medium"
    
    # ========== Validation Tests ==========
    
    def test_priority_creation_with_empty_string_raises_error(self):
        """Priority cannot be created with empty string"""
        with pytest.raises(ValueError, match="Priority cannot be empty"):
            Priority("")
    
    def test_priority_creation_with_none_raises_error(self):
        """Priority cannot be created with None"""
        with pytest.raises(ValueError, match="Priority cannot be empty"):
            Priority(None)
    
    def test_priority_creation_with_invalid_value_raises_error(self):
        """Priority validates against enum values"""
        invalid_values = [
            "LOW",  # Wrong case
            "MEDIUM",  # Wrong case
            "very_high",
            "super_urgent",
            "normal",
            "1",
            "high!",
            "med"
        ]
        
        for invalid in invalid_values:
            with pytest.raises(ValueError) as exc_info:
                Priority(invalid)
            assert "Invalid priority" in str(exc_info.value)
            assert invalid in str(exc_info.value)
            assert "Valid priorities:" in str(exc_info.value)
    
    # ========== Immutability Tests ==========
    
    def test_priority_is_immutable(self):
        """Priority value cannot be modified after creation (frozen dataclass)"""
        # Arrange
        priority = Priority.high()
        
        # Act & Assert
        with pytest.raises(AttributeError):
            priority.value = "low"
    
    def test_priority_dataclass_is_frozen(self):
        """Priority dataclass is properly frozen"""
        # Arrange
        priority = Priority.medium()
        
        # Verify the dataclass is frozen
        assert hasattr(priority, "__frozen__") or priority.__class__.__dataclass_params__.frozen
    
    # ========== Equality and Hashing Tests ==========
    
    def test_priority_equality(self):
        """Priority instances with same value are equal"""
        # Arrange
        priority1 = Priority("high")
        priority2 = Priority("high")
        priority3 = Priority.high()
        priority4 = Priority("low")
        
        # Assert
        assert priority1 == priority2
        assert priority1 == priority3
        assert priority2 == priority3
        assert priority1 != priority4
    
    def test_priority_not_equal_to_other_types(self):
        """Priority is not equal to other types"""
        # Arrange
        priority = Priority.high()
        
        # Assert
        assert priority != "high"
        assert priority != PriorityLevel.HIGH
        assert priority != 3
        assert priority != None
        assert priority != object()
    
    def test_priority_hashable(self):
        """Priority can be used in sets and as dict keys"""
        # Arrange
        priority1 = Priority("high")
        priority2 = Priority("high")  # Same value
        priority3 = Priority("low")  # Different value
        
        # Act - Use in set
        priority_set = {priority1, priority2, priority3}
        
        # Assert
        assert len(priority_set) == 2  # priority1 and priority2 are same
        
        # Act - Use as dict key
        priority_dict = {priority1: "value1", priority3: "value3"}
        priority_dict[priority2] = "value2"  # Should overwrite priority1's value
        
        # Assert
        assert len(priority_dict) == 2
        assert priority_dict[priority1] == "value2"  # Overwritten by priority2
    
    def test_priority_hash_consistency(self):
        """Priority hash is consistent with equality"""
        # Arrange
        priority1 = Priority("urgent")
        priority2 = Priority("urgent")
        
        # Assert
        assert hash(priority1) == hash(priority2)  # Equal objects have equal hashes
    
    # ========== String Representation Tests ==========
    
    def test_priority_string_representation(self):
        """Priority string representation returns the value"""
        # Arrange
        priority = Priority("critical")
        
        # Assert
        assert str(priority) == "critical"
        assert repr(priority) == "Priority(value='critical')"
    
    # ========== Ordering and Comparison Tests ==========
    
    def test_priority_ordering_levels(self):
        """Priority levels are correctly ordered (low < medium < high < urgent < critical)"""
        # Arrange
        low = Priority.low()
        medium = Priority.medium()
        high = Priority.high()
        urgent = Priority.urgent()
        critical = Priority.critical()
        
        # Assert ordering
        assert low < medium < high < urgent < critical
        assert critical > urgent > high > medium > low
    
    def test_priority_less_than_comparison(self):
        """Priority less than comparison works correctly"""
        # Arrange
        low = Priority.low()
        medium = Priority.medium()
        high = Priority.high()
        
        # Assert
        assert low < medium
        assert low < high
        assert medium < high
        assert not (high < medium)
        assert not (medium < medium)  # Not less than itself
    
    def test_priority_less_than_or_equal_comparison(self):
        """Priority less than or equal comparison works correctly"""
        # Arrange
        low = Priority.low()
        medium = Priority.medium()
        high = Priority.high()
        
        # Assert
        assert low <= medium
        assert low <= high
        assert medium <= medium  # Equal to itself
        assert medium <= high
        assert not (high <= medium)
    
    def test_priority_greater_than_comparison(self):
        """Priority greater than comparison works correctly"""
        # Arrange
        low = Priority.low()
        medium = Priority.medium()
        high = Priority.high()
        
        # Assert
        assert high > medium
        assert high > low
        assert medium > low
        assert not (medium > high)
        assert not (medium > medium)  # Not greater than itself
    
    def test_priority_greater_than_or_equal_comparison(self):
        """Priority greater than or equal comparison works correctly"""
        # Arrange
        low = Priority.low()
        medium = Priority.medium()
        high = Priority.high()
        
        # Assert
        assert high >= medium
        assert high >= low
        assert medium >= medium  # Equal to itself
        assert medium >= low
        assert not (low >= medium)
    
    def test_priority_comparison_with_all_levels(self):
        """All priority levels compare correctly"""
        # Arrange
        priorities = [
            Priority.low(),
            Priority.medium(),
            Priority.high(),
            Priority.urgent(),
            Priority.critical()
        ]
        
        # Assert each priority is less than all higher priorities
        for i in range(len(priorities)):
            for j in range(i + 1, len(priorities)):
                assert priorities[i] < priorities[j]
                assert priorities[j] > priorities[i]
                assert priorities[i] <= priorities[j]
                assert priorities[j] >= priorities[i]
    
    def test_priority_sorting(self):
        """Priorities can be sorted correctly"""
        # Arrange - Create in random order
        priorities = [
            Priority.high(),
            Priority.low(),
            Priority.critical(),
            Priority.medium(),
            Priority.urgent()
        ]
        
        # Act
        sorted_priorities = sorted(priorities)
        
        # Assert
        assert sorted_priorities[0].value == "low"
        assert sorted_priorities[1].value == "medium"
        assert sorted_priorities[2].value == "high"
        assert sorted_priorities[3].value == "urgent"
        assert sorted_priorities[4].value == "critical"
    
    # ========== Property Tests ==========
    
    def test_priority_order_property(self):
        """Priority order property returns correct numeric level"""
        # Assert
        assert Priority.low().order == 1
        assert Priority.medium().order == 2
        assert Priority.high().order == 3
        assert Priority.urgent().order == 4
        assert Priority.critical().order == 5
    
    def test_priority_get_level_internal_method(self):
        """_get_level returns correct numeric values"""
        # Arrange
        priorities = {
            Priority.low(): 1,
            Priority.medium(): 2,
            Priority.high(): 3,
            Priority.urgent(): 4,
            Priority.critical(): 5
        }
        
        # Assert
        for priority, expected_level in priorities.items():
            assert priority._get_level() == expected_level
    
    # ========== Helper Method Tests ==========
    
    def test_is_critical_method(self):
        """is_critical correctly identifies critical priority"""
        # Arrange
        critical = Priority.critical()
        urgent = Priority.urgent()
        high = Priority.high()
        
        # Assert
        assert critical.is_critical() is True
        assert urgent.is_critical() is False
        assert high.is_critical() is False
    
    def test_is_high_or_critical_method(self):
        """is_high_or_critical correctly identifies high/critical priorities"""
        # Arrange
        critical = Priority.critical()
        high = Priority.high()
        urgent = Priority.urgent()
        medium = Priority.medium()
        low = Priority.low()
        
        # Assert
        assert critical.is_high_or_critical() is True
        assert high.is_high_or_critical() is True
        assert urgent.is_high_or_critical() is False  # Urgent is not high/critical
        assert medium.is_high_or_critical() is False
        assert low.is_high_or_critical() is False
    
    # ========== Enum Integration Tests ==========
    
    def test_priority_enum_values_match(self):
        """Priority values match PriorityLevel enum labels"""
        # Assert all enum labels work with Priority
        assert Priority(PriorityLevel.LOW.label).value == "low"
        assert Priority(PriorityLevel.MEDIUM.label).value == "medium"
        assert Priority(PriorityLevel.HIGH.label).value == "high"
        assert Priority(PriorityLevel.URGENT.label).value == "urgent"
        assert Priority(PriorityLevel.CRITICAL.label).value == "critical"
    
    def test_all_enum_values_have_factory_methods(self):
        """Every PriorityLevel has a corresponding factory method"""
        # Get all enum labels
        enum_labels = {priority.label for priority in PriorityLevel}
        
        # Get all factory method values
        factory_values = {
            Priority.low().value,
            Priority.medium().value,
            Priority.high().value,
            Priority.urgent().value,
            Priority.critical().value
        }
        
        # Assert they match
        assert enum_labels == factory_values
    
    def test_priority_level_enum_ordering(self):
        """PriorityLevel enum has correct numeric ordering"""
        # Assert
        assert PriorityLevel.LOW.level == 1
        assert PriorityLevel.MEDIUM.level == 2
        assert PriorityLevel.HIGH.level == 3
        assert PriorityLevel.URGENT.level == 4
        assert PriorityLevel.CRITICAL.level == 5
        
        # Verify ordering
        assert PriorityLevel.LOW.level < PriorityLevel.MEDIUM.level
        assert PriorityLevel.MEDIUM.level < PriorityLevel.HIGH.level
        assert PriorityLevel.HIGH.level < PriorityLevel.URGENT.level
        assert PriorityLevel.URGENT.level < PriorityLevel.CRITICAL.level
    
    # ========== Business Logic Tests ==========
    
    def test_priority_escalation_path(self):
        """Test typical priority escalation scenarios"""
        # Start with low priority
        task_priority = Priority.low()
        
        # Can escalate to medium
        assert task_priority < Priority.medium()
        
        # Further escalation to high
        task_priority = Priority.medium()
        assert task_priority < Priority.high()
        
        # Critical escalation
        task_priority = Priority.high()
        assert task_priority < Priority.critical()
    
    def test_priority_filtering_use_case(self):
        """Test filtering tasks by priority threshold"""
        # Arrange - Tasks with various priorities
        task_priorities = [
            Priority.low(),
            Priority.medium(),
            Priority.high(),
            Priority.urgent(),
            Priority.critical()
        ]
        
        # Filter for high priority and above
        threshold = Priority.high()
        high_priority_tasks = [p for p in task_priorities if p >= threshold]
        
        # Assert
        assert len(high_priority_tasks) == 3
        assert all(p >= threshold for p in high_priority_tasks)
        assert Priority.low() not in high_priority_tasks
        assert Priority.medium() not in high_priority_tasks