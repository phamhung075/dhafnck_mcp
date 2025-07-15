"""
Unit tests for SQLite hint repository implementation.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pathlib import Path

from fastmcp.task_management.infrastructure.repositories.sqlite.hint_repository import SQLiteHintRepository
from fastmcp.task_management.domain.value_objects.hints import (
    WorkflowHint, HintType, HintPriority, HintMetadata
)
from fastmcp.task_management.domain.events.hint_events import (
    HintGenerated, HintAccepted, HintDismissed,
    HintFeedbackProvided, HintEffectivenessCalculated
)

pytestmark = pytest.mark.unit


@pytest.fixture
async def temp_db_repository():
    """Create a temporary SQLite hint repository for testing."""
    # Create temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
        temp_db_path = temp_file.name
    
    try:
        # Create repository with temporary database
        repository = SQLiteHintRepository(db_path=temp_db_path)
        yield repository
    finally:
        # Clean up temporary file
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@pytest.fixture
def sample_hint():
    """Create a sample WorkflowHint for testing."""
    metadata = HintMetadata(
        source="test_rule",
        confidence=0.85,
        reasoning="Test reasoning"
    )
    
    return WorkflowHint(
        id=uuid4(),
        task_id=uuid4(),
        type=HintType.NEXT_ACTION,
        priority=HintPriority.HIGH,
        message="Test hint message",
        suggested_action="Take this action",
        metadata=metadata,
        context_data={"key": "value"},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc)
    )


class TestSQLiteHintRepository:
    """Test SQLite hint repository functionality."""
    
    async def test_save_and_get_hint(self, temp_db_repository, sample_hint):
        """Test saving and retrieving a hint."""
        # Save hint
        await temp_db_repository.save(sample_hint)
        
        # Retrieve hint
        retrieved_hint = await temp_db_repository.get(sample_hint.id)
        
        assert retrieved_hint is not None
        assert retrieved_hint.id == sample_hint.id
        assert retrieved_hint.task_id == sample_hint.task_id
        assert retrieved_hint.type == sample_hint.type
        assert retrieved_hint.priority == sample_hint.priority
        assert retrieved_hint.message == sample_hint.message
        assert retrieved_hint.suggested_action == sample_hint.suggested_action
        assert retrieved_hint.metadata.source == sample_hint.metadata.source
        assert retrieved_hint.metadata.confidence == sample_hint.metadata.confidence
        assert retrieved_hint.context_data == sample_hint.context_data
    
    async def test_get_nonexistent_hint(self, temp_db_repository):
        """Test retrieving a non-existent hint."""
        result = await temp_db_repository.get(uuid4())
        assert result is None
    
    async def test_get_by_task(self, temp_db_repository):
        """Test retrieving hints by task ID."""
        task_id = uuid4()
        
        # Create multiple hints for the same task
        metadata1 = HintMetadata(source="rule1", confidence=0.9, reasoning="High priority test")
        hint1 = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="High priority hint",
            suggested_action="Do high priority action",
            metadata=metadata1,
            created_at=datetime.now(timezone.utc)
        )
        
        metadata2 = HintMetadata(source="rule2", confidence=0.95, reasoning="Critical test")
        hint2 = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.BLOCKER_RESOLUTION,
            priority=HintPriority.CRITICAL,
            message="Critical blocker",
            suggested_action="Resolve this blocker",
            metadata=metadata2,
            created_at=datetime.now(timezone.utc)
        )
        
        metadata3 = HintMetadata(source="rule3", confidence=0.7, reasoning="Different task test")
        hint3 = WorkflowHint(
            id=uuid4(),
            task_id=uuid4(),  # Different task
            type=HintType.NEXT_ACTION,
            priority=HintPriority.LOW,
            message="Different task hint",
            suggested_action="Do different action", 
            metadata=metadata3,
            created_at=datetime.now(timezone.utc)
        )
        
        # Save all hints
        await temp_db_repository.save(hint1)
        await temp_db_repository.save(hint2)
        await temp_db_repository.save(hint3)
        
        # Get hints for specific task
        task_hints = await temp_db_repository.get_by_task(task_id)
        
        assert len(task_hints) == 2
        # Should be sorted by priority (critical first, then high)
        assert task_hints[0].priority == HintPriority.CRITICAL
        assert task_hints[1].priority == HintPriority.HIGH
    
    async def test_get_by_task_with_type_filter(self, temp_db_repository):
        """Test retrieving hints by task ID with type filtering."""
        task_id = uuid4()
        
        metadata1 = HintMetadata(source="rule1", confidence=0.9, reasoning="Next action test")
        hint1 = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Next action hint",
            suggested_action="Do next action",
            metadata=metadata1,
            created_at=datetime.now(timezone.utc)
        )
        
        metadata2 = HintMetadata(source="rule2", confidence=0.95, reasoning="Blocker test")
        hint2 = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.BLOCKER_RESOLUTION,
            priority=HintPriority.CRITICAL,
            message="Blocker alert",
            suggested_action="Resolve blocker",
            metadata=metadata2,
            created_at=datetime.now(timezone.utc)
        )
        
        await temp_db_repository.save(hint1)
        await temp_db_repository.save(hint2)
        
        # Filter by type
        next_action_hints = await temp_db_repository.get_by_task(
            task_id, 
            hint_types=[HintType.NEXT_ACTION]
        )
        
        assert len(next_action_hints) == 1
        assert next_action_hints[0].type == HintType.NEXT_ACTION
    
    async def test_expired_hint_filtering(self, temp_db_repository):
        """Test filtering of expired hints."""
        task_id = uuid4()
        
        # Create expired hint
        metadata1 = HintMetadata(source="rule1", confidence=0.9, reasoning="Expired test")
        expired_hint = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Expired hint",
            suggested_action="Do expired action",
            metadata=metadata1,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        
        # Create active hint
        metadata2 = HintMetadata(source="rule2", confidence=0.9, reasoning="Active test")
        active_hint = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Active hint",
            suggested_action="Do active action",
            metadata=metadata2,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc)
        )
        
        await temp_db_repository.save(expired_hint)
        await temp_db_repository.save(active_hint)
        
        # Get active hints only (default behavior)
        active_hints = await temp_db_repository.get_by_task(task_id)
        assert len(active_hints) == 1
        assert active_hints[0].id == active_hint.id
        
        # Get all hints including expired
        all_hints = await temp_db_repository.get_by_task(task_id, include_expired=True)
        assert len(all_hints) == 2
    
    async def test_store_generated_hint_event(self, temp_db_repository):
        """Test storing hint generated events."""
        hint_id = uuid4()
        task_id = uuid4()
        
        event = HintGenerated(
            hint_id=hint_id,
            task_id=task_id,
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Test hint message",
            suggested_action="Take action",
            source_rule="test_rule",
            confidence=0.85
        )
        
        await temp_db_repository.store_generated_hint(event)
        # No exception means success
    
    async def test_store_hint_acceptance_event(self, temp_db_repository):
        """Test storing hint acceptance events."""
        hint_id = uuid4()
        task_id = uuid4()
        
        event = HintAccepted(
            hint_id=hint_id,
            task_id=task_id,
            user_id="test_user",
            action_taken="Applied suggestion"
        )
        
        await temp_db_repository.store_hint_acceptance(event)
        # Event storage doesn't throw exceptions on success
    
    async def test_store_hint_dismissal_event(self, temp_db_repository):
        """Test storing hint dismissal events."""
        hint_id = uuid4()
        task_id = uuid4()
        
        event = HintDismissed(
            hint_id=hint_id,
            task_id=task_id,
            user_id="test_user",
            reason="Not relevant"
        )
        
        await temp_db_repository.store_hint_dismissal(event)
        # Event storage doesn't throw exceptions on success
    
    async def test_store_hint_feedback_event(self, temp_db_repository):
        """Test storing hint feedback events."""
        hint_id = uuid4()
        task_id = uuid4()
        
        event = HintFeedbackProvided(
            hint_id=hint_id,
            task_id=task_id,
            user_id="test_user",
            was_helpful=True,
            feedback_text="Very useful suggestion",
            effectiveness_score=0.9
        )
        
        await temp_db_repository.store_hint_feedback(event)
        # Event storage doesn't throw exceptions on success
    
    async def test_effectiveness_score_storage_and_retrieval(self, temp_db_repository):
        """Test storing and retrieving effectiveness scores."""
        now = datetime.now(timezone.utc)
        event = HintEffectivenessCalculated(
            hint_type=HintType.NEXT_ACTION,
            source_rule="test_rule",
            total_hints=10,
            accepted_count=7,
            dismissed_count=2,
            effectiveness_score=0.75,
            period_start=now - timedelta(days=7),
            period_end=now
        )
        
        await temp_db_repository.store_effectiveness_score(event)
        
        # Retrieve the score
        score = await temp_db_repository.get_effectiveness_score(
            "test_rule", 
            HintType.NEXT_ACTION
        )
        
        assert score == 0.75
    
    async def test_get_effectiveness_score_nonexistent(self, temp_db_repository):
        """Test retrieving non-existent effectiveness score."""
        score = await temp_db_repository.get_effectiveness_score(
            "nonexistent_rule",
            HintType.NEXT_ACTION
        )
        
        assert score is None
    
    async def test_store_improvement_suggestion(self, temp_db_repository):
        """Test storing improvement suggestions."""
        hint_id = uuid4()
        suggestion = "Could be more specific about the action required"
        
        await temp_db_repository.store_improvement_suggestion(hint_id, suggestion)
        # No exception means success
    
    async def test_store_detected_pattern(self, temp_db_repository):
        """Test storing detected patterns."""
        pattern_event = {
            "pattern_id": "pattern_123",
            "pattern_name": "Frequent Context Switch",
            "pattern_description": "User switches between tasks frequently",
            "confidence": 0.8,
            "occurred_at": datetime.now(timezone.utc),
            "affected_tasks": [str(uuid4()), str(uuid4())],
            "suggested_rule": "suggest_focus_time"
        }
        
        await temp_db_repository.store_detected_pattern(pattern_event)
        # No exception means success
    
    async def test_get_patterns(self, temp_db_repository):
        """Test retrieving detected patterns."""
        # Store patterns with different confidence levels
        pattern1 = {
            "pattern_id": "pattern_1",
            "pattern_name": "High Confidence Pattern",
            "pattern_description": "Pattern with high confidence",
            "confidence": 0.9,
            "occurred_at": datetime.now(timezone.utc),
            "affected_tasks": [],
            "suggested_rule": "rule1"
        }
        
        pattern2 = {
            "pattern_id": "pattern_2", 
            "pattern_name": "Low Confidence Pattern",
            "pattern_description": "Pattern with low confidence",
            "confidence": 0.5,
            "occurred_at": datetime.now(timezone.utc),
            "affected_tasks": [],
            "suggested_rule": "rule2"
        }
        
        await temp_db_repository.store_detected_pattern(pattern1)
        await temp_db_repository.store_detected_pattern(pattern2)
        
        # Get patterns with default confidence threshold (0.7)
        patterns = await temp_db_repository.get_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_name"] == "High Confidence Pattern"
        
        # Get patterns with lower confidence threshold
        all_patterns = await temp_db_repository.get_patterns(min_confidence=0.4)
        assert len(all_patterns) == 2
    
    async def test_hint_statistics(self, temp_db_repository):
        """Test getting hint statistics."""
        task_id = uuid4()
        
        # Create some hints
        metadata1 = HintMetadata(source="rule1", confidence=0.9, reasoning="Test 1")
        hint1 = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Test hint 1",
            suggested_action="Action 1",
            metadata=metadata1,
            created_at=datetime.now(timezone.utc)
        )
        
        metadata2 = HintMetadata(source="rule2", confidence=0.8, reasoning="Test 2")
        hint2 = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.BLOCKER_RESOLUTION,
            priority=HintPriority.CRITICAL,
            message="Test hint 2",
            suggested_action="Action 2",
            metadata=metadata2,
            created_at=datetime.now(timezone.utc)
        )
        
        await temp_db_repository.save(hint1)
        await temp_db_repository.save(hint2)
        
        # Store effectiveness score
        now = datetime.now(timezone.utc)
        await temp_db_repository.store_effectiveness_score(
            HintEffectivenessCalculated(
                hint_type=HintType.NEXT_ACTION,
                source_rule="rule1",
                total_hints=5,
                accepted_count=4,
                dismissed_count=1,
                effectiveness_score=0.85,
                period_start=now - timedelta(days=1),
                period_end=now
            )
        )
        
        stats = await temp_db_repository.get_hint_statistics()
        
        assert stats["total_hints"] == 2
        assert stats["hints_by_type"]["next_action"] == 1
        assert stats["hints_by_type"]["blocker_resolution"] == 1
        assert stats["hints_by_priority"]["high"] == 1
        assert stats["hints_by_priority"]["critical"] == 1
        assert stats["average_effectiveness"] == 0.85
    
    async def test_cleanup_expired_hints(self, temp_db_repository):
        """Test cleaning up expired hints."""
        task_id = uuid4()
        
        # Create expired hint
        metadata1 = HintMetadata(source="rule1", confidence=0.9, reasoning="Expired test")
        expired_hint = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Expired hint",
            suggested_action="Expired action",
            metadata=metadata1,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        
        # Create active hint
        metadata2 = HintMetadata(source="rule2", confidence=0.9, reasoning="Active test")
        active_hint = WorkflowHint(
            id=uuid4(),
            task_id=task_id,
            type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Active hint",
            suggested_action="Active action",
            metadata=metadata2,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc)
        )
        
        await temp_db_repository.save(expired_hint)
        await temp_db_repository.save(active_hint)
        
        # Clean up expired hints
        removed_count = await temp_db_repository.cleanup_expired_hints()
        
        assert removed_count == 1
        
        # Verify expired hint is gone
        retrieved_expired = await temp_db_repository.get(expired_hint.id)
        assert retrieved_expired is None
        
        # Verify active hint remains
        retrieved_active = await temp_db_repository.get(active_hint.id)
        assert retrieved_active is not None
    
    async def test_update_hint_overwrites_existing(self, temp_db_repository, sample_hint):
        """Test that saving a hint with the same ID overwrites the existing one."""
        # Save original hint
        await temp_db_repository.save(sample_hint)
        
        # Create updated version
        updated_metadata = HintMetadata(
            source="updated_rule",
            confidence=0.95,
            reasoning="Updated reasoning"
        )
        
        updated_hint = WorkflowHint(
            id=sample_hint.id,  # Same ID
            task_id=sample_hint.task_id,
            type=HintType.BLOCKER_RESOLUTION,  # Different type
            priority=HintPriority.CRITICAL,  # Different priority
            message="Updated message",  # Different message
            suggested_action="Updated action",  # Different action
            metadata=updated_metadata,  # Different metadata
            created_at=sample_hint.created_at
        )
        
        # Save updated hint
        await temp_db_repository.save(updated_hint)
        
        # Retrieve and verify it was updated
        retrieved = await temp_db_repository.get(sample_hint.id)
        assert retrieved.type == HintType.BLOCKER_RESOLUTION
        assert retrieved.priority == HintPriority.CRITICAL
        assert retrieved.message == "Updated message"
        assert retrieved.suggested_action == "Updated action"
        assert retrieved.metadata.source == "updated_rule"
        assert retrieved.metadata.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__])