"""
Basic unit tests for workflow hints functionality - focusing on value objects.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastmcp.task_management.domain.value_objects.hints import (
    HintType, HintPriority, HintMetadata, WorkflowHint, HintCollection
)

pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests


class TestWorkflowHintValueObjects:
    
    def setup_method(self, method):
        """Clean up before each test"""
        # Skip database operations for unit tests
        # Unit tests should not access the database
        pass

    """Test hint value objects."""
    
    def test_hint_metadata_creation(self):
        """Test HintMetadata creation and validation."""
        metadata = HintMetadata(
            source="test_rule",
            confidence=0.85,
            reasoning="Test reasoning",
            related_tasks=[uuid4()],
            patterns_detected=["pattern1", "pattern2"],
            effectiveness_score=0.75
        )
        
        assert metadata.source == "test_rule"
        assert metadata.confidence == 0.85
        assert metadata.reasoning == "Test reasoning"
        assert len(metadata.related_tasks) == 1
        assert len(metadata.patterns_detected) == 2
        assert metadata.effectiveness_score == 0.75
    
    def test_hint_metadata_invalid_confidence(self):
        """Test HintMetadata validation."""
        with pytest.raises(ValueError):
            HintMetadata(
                source="test",
                confidence=1.5,  # Invalid: > 1.0
                reasoning="Test"
            )
        
        with pytest.raises(ValueError):
            HintMetadata(
                source="test",
                confidence=-0.1,  # Invalid: < 0
                reasoning="Test"
            )
    
    def test_workflow_hint_creation(self):
        """Test WorkflowHint creation."""
        metadata = HintMetadata(
            source="test_rule",
            confidence=0.8,
            reasoning="Test reasoning"
        )
        
        hint = WorkflowHint.create(
            task_id=uuid4(),
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Test hint message",
            suggested_action="Do something",
            metadata=metadata
        )
        
        assert hint.id is not None
        assert hint.type == HintType.NEXT_ACTION
        assert hint.priority == HintPriority.HIGH
        assert hint.message == "Test hint message"
        assert hint.suggested_action == "Do something"
        assert hint.metadata == metadata
        assert hint.created_at is not None
        assert not hint.is_expired()
    
    def test_hint_expiration(self):
        """Test hint expiration logic."""
        # Create expired hint
        hint = WorkflowHint.create(
            task_id=uuid4(),
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Expired hint",
            suggested_action="Do something",
            metadata=HintMetadata("test", 0.8, "Test"),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        assert hint.is_expired()
        
        # Create non-expired hint
        future_hint = WorkflowHint.create(
            task_id=uuid4(),
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Future hint",
            suggested_action="Do something",
            metadata=HintMetadata("test", 0.8, "Test"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        assert not future_hint.is_expired()
    
    def test_hint_collection(self):
        """Test HintCollection functionality."""
        task_id = uuid4()
        collection = HintCollection(task_id=task_id)
        
        metadata = HintMetadata(
            source="test",
            confidence=0.8,
            reasoning="Test"
        )
        
        # Add hints
        hint1 = WorkflowHint.create(
            task_id=task_id,
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Hint 1",
            suggested_action="Action 1",
            metadata=metadata
        )
        
        hint2 = WorkflowHint.create(
            task_id=task_id,
            hint_type=HintType.OPTIMIZATION,
            priority=HintPriority.LOW,
            message="Hint 2",
            suggested_action="Action 2",
            metadata=metadata
        )
        
        collection.add_hint(hint1)
        collection.add_hint(hint2)
        
        assert len(collection.hints) == 2
        
        # Test filtering
        high_priority = collection.get_hints_by_priority(HintPriority.HIGH)
        assert len(high_priority) == 1
        assert high_priority[0] == hint1
        
        optimization_hints = collection.get_hints_by_type(HintType.OPTIMIZATION)
        assert len(optimization_hints) == 1
        assert optimization_hints[0] == hint2
    
    def test_hint_priority_ordering(self):
        """Test hint priority ordering in collection."""
        task_id = uuid4()
        collection = HintCollection(task_id=task_id)
        
        metadata = HintMetadata(
            source="test",
            confidence=0.8,
            reasoning="Test"
        )
        
        # Add hints with different priorities
        priorities = [
            HintPriority.LOW,
            HintPriority.CRITICAL,
            HintPriority.MEDIUM,
            HintPriority.HIGH
        ]
        
        for i, priority in enumerate(priorities):
            hint = WorkflowHint.create(
                task_id=task_id,
                hint_type=HintType.NEXT_ACTION,
                priority=priority,
                message=f"Hint {i}",
                suggested_action=f"Action {i}",
                metadata=metadata
            )
            collection.add_hint(hint)
        
        # Get top hints
        top_hints = collection.get_top_hints(2)
        assert len(top_hints) == 2
        assert top_hints[0].priority == HintPriority.CRITICAL
        assert top_hints[1].priority == HintPriority.HIGH