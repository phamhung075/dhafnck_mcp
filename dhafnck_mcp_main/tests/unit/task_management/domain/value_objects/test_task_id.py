"""Test suite for TaskId value object

This module tests the TaskId value object following DDD principles.
Tests verify immutability, validation, equality, and proper UUID handling.
"""

import pytest
import uuid

from fastmcp.task_management.domain.value_objects.task_id import TaskId

pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests

class TestTaskIdValueObject:
    """Test suite for TaskId value object"""
    
    # ========== Valid Creation Tests ==========
    
    def test_task_id_creation_with_valid_uuid_hex(self):
        """TaskId can be created with valid 32-char UUID hex string"""
        # Arrange
        valid_hex = "550e8400e29b41d4a716446655440000"
        expected_canonical = "550e8400-e29b-41d4-a716-446655440000"
        
        # Act
        task_id = TaskId(valid_hex)
        
        # Assert
        assert task_id.value == expected_canonical  # Stored in canonical format
        assert str(task_id) == expected_canonical
    
    def test_task_id_creation_with_canonical_uuid(self):
        """TaskId can be created with canonical UUID format (with dashes)"""
        # Arrange
        canonical_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        # Act
        task_id = TaskId(canonical_uuid)
        
        # Assert
        assert task_id.value == canonical_uuid  # Stored in canonical format
        assert str(task_id) == canonical_uuid
    
    def test_task_id_creation_normalizes_to_lowercase(self):
        """TaskId normalizes UUID to lowercase and canonical format"""
        # Arrange
        uppercase_uuid = "550E8400E29B41D4A716446655440000"
        expected_canonical = "550e8400-e29b-41d4-a716-446655440000"
        
        # Act
        task_id = TaskId(uppercase_uuid)
        
        # Assert
        assert task_id.value == expected_canonical
    
    def test_task_id_from_string_factory_method(self):
        """TaskId can be created using from_string factory method"""
        # Arrange
        uuid_string = "550e8400-e29b-41d4-a716-446655440000"
        
        # Act
        task_id = TaskId.from_string(uuid_string)
        
        # Assert
        assert isinstance(task_id, TaskId)
        assert task_id.value == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_task_id_generate_new_creates_unique_ids(self):
        """generate_new creates unique TaskIds"""
        # Act
        id1 = TaskId.generate_new()
        id2 = TaskId.generate_new()
        id3 = TaskId.generate_new()
        
        # Assert
        assert isinstance(id1, TaskId)
        assert isinstance(id2, TaskId)
        assert isinstance(id3, TaskId)
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3
        assert len(id1.value) == 36  # UUID canonical is 36 chars
    
    def test_task_id_to_hex_format(self):
        """TaskId can convert to hex UUID format without dashes"""
        # Arrange
        canonical_value = "550e8400-e29b-41d4-a716-446655440000"
        task_id = TaskId(canonical_value)
        
        # Act
        hex_format = task_id.to_hex_format()
        
        # Assert
        assert hex_format == "550e8400e29b41d4a716446655440000"
    
    # ========== Validation Tests ==========
    
    def test_task_id_creation_with_none_raises_error(self):
        """TaskId cannot be created with None value"""
        with pytest.raises(ValueError, match="Task ID cannot be None"):
            TaskId(None)
    
    def test_task_id_creation_with_empty_string_raises_error(self):
        """TaskId cannot be created with empty string"""
        with pytest.raises(ValueError, match="Task ID cannot be empty or whitespace"):
            TaskId("")
    
    def test_task_id_creation_with_whitespace_raises_error(self):
        """TaskId cannot be created with whitespace only"""
        with pytest.raises(ValueError, match="Task ID cannot be empty or whitespace"):
            TaskId("   ")
    
    def test_task_id_creation_with_invalid_type_raises_error(self):
        """TaskId must be created with string value"""
        with pytest.raises(TypeError, match="Task ID value must be a string"):
            TaskId(12345)
    
    def test_task_id_creation_with_invalid_uuid_format_raises_error(self):
        """TaskId validates UUID format"""
        invalid_values = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "GGGG8400-e29b-41d4-a716-446655440000",  # Invalid hex chars
            "550e8400e29b41d4a716446655440000z",  # Invalid char at end
            "123.abc",  # Invalid hierarchical ID
        ]
        
        for invalid in invalid_values:
            with pytest.raises(ValueError, match="Invalid Task ID format"):
                TaskId(invalid)
    
    # ========== Immutability Tests ==========
    
    def test_task_id_is_immutable(self):
        """TaskId value cannot be modified after creation (frozen dataclass)"""
        # Arrange
        task_id = TaskId.generate_new()
        
        # Act & Assert
        with pytest.raises(AttributeError):
            task_id.value = "new-value"
    
    def test_task_id_dataclass_is_frozen(self):
        """TaskId dataclass is properly frozen"""
        # Arrange
        task_id = TaskId.generate_new()
        
        # Verify the dataclass is frozen
        assert hasattr(task_id, "__frozen__") or task_id.__class__.__dataclass_params__.frozen
    
    # ========== Equality and Hashing Tests ==========
    
    def test_task_id_equality(self):
        """TaskIds with same value are equal"""
        # Arrange
        uuid_value = "550e8400e29b41d4a716446655440000"
        id1 = TaskId(uuid_value)
        id2 = TaskId(uuid_value)
        id3 = TaskId.generate_new()
        
        # Assert
        assert id1 == id2
        assert id1 != id3
        assert id2 != id3
    
    def test_task_id_equality_with_different_input_formats(self):
        """TaskIds are equal regardless of input format (with/without dashes)"""
        # Arrange
        id1 = TaskId("550e8400e29b41d4a716446655440000")
        id2 = TaskId("550e8400-e29b-41d4-a716-446655440000")
        
        # Assert - Both normalize to same canonical value
        assert id1 == id2
        assert id1.value == id2.value == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_task_id_not_equal_to_other_types(self):
        """TaskId is not equal to other types"""
        # Arrange
        task_id = TaskId.generate_new()
        
        # Assert
        assert task_id != "some-string"
        assert task_id != 123
        assert task_id != None
        assert task_id != object()
    
    def test_task_id_hashable(self):
        """TaskId can be used in sets and as dict keys"""
        # Arrange
        id1 = TaskId("550e8400e29b41d4a716446655440000")
        id2 = TaskId("550e8400-e29b-41d4-a716-446655440000")  # Same value, different format
        id3 = TaskId.generate_new()  # Different value
        
        # Act - Use in set
        id_set = {id1, id2, id3}
        
        # Assert
        assert len(id_set) == 2  # id1 and id2 are same, so only 2 unique
        
        # Act - Use as dict key
        id_dict = {id1: "value1", id3: "value3"}
        id_dict[id2] = "value2"  # Should overwrite id1's value
        
        # Assert
        assert len(id_dict) == 2
        assert id_dict[id1] == "value2"  # Overwritten by id2
    
    def test_task_id_hash_consistency(self):
        """TaskId hash is consistent with equality"""
        # Arrange
        uuid_hex = "550e8400e29b41d4a716446655440000"
        uuid_canonical = "550e8400-e29b-41d4-a716-446655440000"
        id1 = TaskId(uuid_hex)
        id2 = TaskId(uuid_canonical)
        
        # Assert
        assert hash(id1) == hash(id2)  # Equal objects have equal hashes
    
    # ========== String Representation Tests ==========
    
    def test_task_id_string_representation(self):
        """TaskId string representation returns the canonical value"""
        # Arrange
        hex_value = "550e8400e29b41d4a716446655440000"
        expected_canonical = "550e8400-e29b-41d4-a716-446655440000"
        task_id = TaskId(hex_value)
        
        # Assert
        assert str(task_id) == expected_canonical
        assert repr(task_id) == f"TaskId(value='{expected_canonical}')"
    
    # ========== Factory Method Tests ==========
    
    def test_from_int_factory_method(self):
        """TaskId from_int factory method creates valid integer-based TaskIds"""
        # The from_int method creates integer TaskIds for backward compatibility
        
        # Act - Create TaskIds from integers
        task_id_123 = TaskId.from_int(123)
        task_id_456 = TaskId.from_int(456)
        
        # Assert - Values should be stored as strings but valid
        assert str(task_id_123) == "123"
        assert str(task_id_456) == "456"
        assert task_id_123 != task_id_456
    
    def test_generate_subtask_method(self):
        """TaskId generate_subtask method creates hierarchical subtask IDs"""
        # Arrange
        parent_id = TaskId.generate_new()
        
        # Act - Generate first subtask
        existing_ids = []
        subtask1 = TaskId.generate_subtask(parent_id, existing_ids)
        
        # Assert - First subtask should be parent.001
        expected_first = f"{parent_id}.001"
        assert str(subtask1) == expected_first
        
        # Act - Generate second subtask
        existing_ids.append(str(subtask1))
        subtask2 = TaskId.generate_subtask(parent_id, existing_ids)
        
        # Assert - Second subtask should be parent.002
        expected_second = f"{parent_id}.002"
        assert str(subtask2) == expected_second
        
        # Act - Generate third subtask with existing subtasks and non-subtask ID
        existing_ids.append(str(subtask2))  # Add the second subtask
        existing_ids.append("some-other-id")  # Non-subtask ID should be ignored
        subtask3 = TaskId.generate_subtask(parent_id, existing_ids)
        
        # Assert - Third subtask should be parent.003
        expected_third = f"{parent_id}.003"
        assert str(subtask3) == expected_third
        
        # Verify all subtasks are unique
        assert subtask1 != subtask2
        assert subtask2 != subtask3
        assert subtask1 != subtask3
    
    # ========== Integration Tests ==========
    
    def test_task_id_works_with_python_uuid(self):
        """TaskId integrates properly with Python's uuid module"""
        # Arrange
        python_uuid = uuid.uuid4()
        
        # Act - Create from hex
        task_id_hex = TaskId(python_uuid.hex)
        
        # Act - Create from string representation
        task_id_str = TaskId(str(python_uuid))
        
        # Assert
        assert task_id_hex == task_id_str
        assert task_id_hex.value == str(python_uuid)  # Both stored in canonical format
    
    def test_task_id_preserves_uuid_value(self):
        """TaskId preserves the actual UUID value through conversions"""
        # Arrange
        original_uuid = uuid.uuid4()
        
        # Act
        task_id = TaskId(str(original_uuid))
        back_to_canonical = task_id.value  # Already in canonical format
        
        # Assert
        assert back_to_canonical == str(original_uuid)
        assert uuid.UUID(back_to_canonical) == original_uuid