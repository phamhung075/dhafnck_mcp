"""
Unit tests for workflow hints functionality in the Vision System.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastmcp.task_management.domain.value_objects.hints import (
    HintType, HintPriority, HintMetadata, WorkflowHint, HintCollection
)
from fastmcp.task_management.domain.services.hint_rules import (
    RuleContext, StalledProgressRule, ImplementationReadyForTestingRule,
    MissingContextRule, ComplexDependencyRule, NearCompletionRule
)
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.context import TaskContext
from fastmcp.task_management.domain.value_objects.progress import ProgressType
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus, TaskStatusEnum
from fastmcp.task_management.domain.value_objects.priority import Priority



pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests

class TestWorkflowHintValueObjects:
    """Test hint value objects."""
    
    def test_hint_metadata_creation(self):
        """Test HintMetadata creation and validation."""
        metadata = HintMetadata(
            source="test_rule",
            confidence=0.85,
            reasoning="Test reasoning",
            related_tasks=[uuid4()],
            patterns_detected=["pattern1"],
            effectiveness_score=0.9
        )
        
        assert metadata.source == "test_rule"
        assert metadata.confidence == 0.85
        assert metadata.effectiveness_score == 0.9
    
    def test_hint_metadata_invalid_confidence(self):
        """Test HintMetadata with invalid confidence."""
        with pytest.raises(ValueError):
            HintMetadata(
                source="test",
                confidence=1.5,  # Invalid
                reasoning="Test"
            )
    
    def test_workflow_hint_creation(self):
        """Test WorkflowHint creation."""
        task_id = uuid4()
        metadata = HintMetadata(
            source="test_rule",
            confidence=0.8,
            reasoning="Test reasoning"
        )
        
        hint = WorkflowHint.create(
            task_id=task_id,
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="Test message",
            suggested_action="Test action",
            metadata=metadata
        )
        
        assert hint.task_id == task_id
        assert hint.type == HintType.NEXT_ACTION
        assert hint.priority == HintPriority.HIGH
        assert hint.message == "Test message"
        assert not hint.is_expired()
    
    def test_hint_expiration(self):
        """Test hint expiration logic."""
        metadata = HintMetadata(
            source="test",
            confidence=0.8,
            reasoning="Test"
        )
        
        # Create expired hint
        hint = WorkflowHint.create(
            task_id=uuid4(),
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.LOW,
            message="Test",
            suggested_action="Test",
            metadata=metadata,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        assert hint.is_expired()
    
    def test_hint_collection(self):
        """Test HintCollection functionality."""
        task_id = uuid4()
        collection = HintCollection(task_id=task_id)
        
        # Create hints
        metadata = HintMetadata(
            source="test",
            confidence=0.8,
            reasoning="Test"
        )
        
        hint1 = WorkflowHint.create(
            task_id=task_id,
            hint_type=HintType.NEXT_ACTION,
            priority=HintPriority.HIGH,
            message="High priority hint",
            suggested_action="Do this first",
            metadata=metadata
        )
        
        hint2 = WorkflowHint.create(
            task_id=task_id,
            hint_type=HintType.OPTIMIZATION,
            priority=HintPriority.LOW,
            message="Low priority hint",
            suggested_action="Consider this",
            metadata=metadata
        )
        
        collection.add_hint(hint1)
        collection.add_hint(hint2)
        
        # Test retrieval
        assert len(collection.get_active_hints()) == 2
        assert len(collection.get_hints_by_type(HintType.NEXT_ACTION)) == 1
        assert len(collection.get_hints_by_priority(HintPriority.HIGH)) == 1
        
        # Test top hints (should prioritize high priority)
        top_hints = collection.get_top_hints(limit=1)
        assert len(top_hints) == 1
        assert top_hints[0].priority == HintPriority.HIGH


class TestHintGenerationRules:
    """Test hint generation rules."""
    
    def test_stalled_progress_rule(self):
        """Test StalledProgressRule."""
        rule = StalledProgressRule(stall_hours=24)
        
        # Create stalled task
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="Test task for stalled progress rule",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        # Set up progress timeline in the format expected by hint rules (list of dicts)
        task.progress_timeline = [{
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(),
            "type": ProgressType.IMPLEMENTATION.value,
            "status": "advancing",
            "percentage": 50.0,
            "description": "Advancing"
        }]
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.NEXT_ACTION
        assert hint.priority == HintPriority.HIGH
        assert "48 hours" in hint.message
    
    def test_stalled_blocked_task_rule(self):
        """Test StalledProgressRule for blocked tasks."""
        rule = StalledProgressRule(stall_hours=24)
        
        # Create blocked task
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="Test task for blocked stalled rule",
            status=TaskStatus(TaskStatusEnum.BLOCKED.value)
        )
        # Set up progress timeline in the format expected by hint rules (list of dicts)
        task.progress_timeline = [{
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat(),
            "type": ProgressType.IMPLEMENTATION.value,
            "status": "blocked",
            "percentage": 30.0,
            "description": "Blocked"
        }]
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.BLOCKER_RESOLUTION
        assert hint.priority == HintPriority.CRITICAL  # >48 hours
        assert "blocked for 72 hours" in hint.message
    
    def test_implementation_ready_for_testing_rule(self):
        """Test ImplementationReadyForTestingRule."""
        rule = ImplementationReadyForTestingRule(implementation_threshold=0.75)
        
        # Create task with high implementation progress
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="Test task for implementation ready rule",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        # Set up progress breakdown in the format expected by hint rules
        task.progress_breakdown = {
            ProgressType.IMPLEMENTATION.value: 0.8,
            ProgressType.TESTING.value: 0.0
        }
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.NEXT_ACTION
        assert hint.priority == HintPriority.HIGH
        assert "ready for testing" in hint.message
        assert "80%" in hint.message
    
    def test_missing_context_rule(self):
        """Test MissingContextRule."""
        rule = MissingContextRule()
        
        # Task without context
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="Test task for missing context rule",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.NEXT_ACTION
        assert hint.priority == HintPriority.HIGH
        assert "missing context" in hint.message
    
    def test_complex_dependency_rule(self):
        """Test ComplexDependencyRule."""
        rule = ComplexDependencyRule(complexity_threshold=3)
        
        # Task with many dependencies
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="Test task for complex dependency rule"
        )
        # Set dependencies manually since Task.create doesn't accept dependencies parameter
        task.dependencies = [TaskId(str(uuid4())) for _ in range(5)]
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.OPTIMIZATION
        assert hint.priority == HintPriority.MEDIUM
        assert "5 dependencies" in hint.message
        assert "decomposition" in hint.message
    
    def test_near_completion_rule(self):
        """Test NearCompletionRule."""
        rule = NearCompletionRule(completion_threshold=0.9)
        
        # Task near completion but missing some steps
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="Test task for near completion rule",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        # Set up progress in the format expected by hint rules
        task.progress = 0.92  # Overall progress
        task.progress_breakdown = {
            ProgressType.IMPLEMENTATION.value: 1.0,
            ProgressType.TESTING.value: 0.7,
            ProgressType.DOCUMENTATION.value: 0.5,
            ProgressType.REVIEW.value: 0.0
        }
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.COMPLETION
        assert hint.priority == HintPriority.HIGH
        assert "92% complete" in hint.message
        assert "complete review" in hint.suggested_action


class TestHintIntegration:
    """Test hint integration scenarios."""
    
    def test_multiple_rules_evaluation(self):
        """Test evaluating multiple rules on same task."""
        # Create a complex task scenario
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Complex Task",
            description="Complex task for multiple rules evaluation",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        # Set up task properties in the format expected by hint rules
        task.progress = 0.45  # Overall progress
        task.dependencies = [TaskId(str(uuid4())) for _ in range(4)]
        
        # Set up progress timeline for stalled rule (list of dicts)
        task.progress_timeline = [{
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(),
            "type": ProgressType.IMPLEMENTATION.value,
            "status": "advancing",
            "percentage": 40.0,
            "description": "Advancing"
        }]
        
        # Set up progress breakdown for implementation ready rule
        task.progress_breakdown = {
            ProgressType.IMPLEMENTATION.value: 0.8,
            ProgressType.TESTING.value: 0.1
        }
        
        rules = [
            StalledProgressRule(stall_hours=24),
            ImplementationReadyForTestingRule(implementation_threshold=0.75),
            ComplexDependencyRule(complexity_threshold=3)
        ]
        
        context = RuleContext(task=task, context=None)
        hints = []
        
        for rule in rules:
            hint = rule.evaluate(context)
            if hint:
                hints.append(hint)
        
        # Should get hints from multiple rules
        assert len(hints) >= 2
        
        # Check hint types
        hint_types = {hint.type for hint in hints}
        assert HintType.NEXT_ACTION in hint_types
        assert HintType.OPTIMIZATION in hint_types
    
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
        top_hints = collection.get_top_hints(limit=4)
        
        # Check ordering
        assert top_hints[0].priority == HintPriority.CRITICAL
        assert top_hints[1].priority == HintPriority.HIGH
        assert top_hints[2].priority == HintPriority.MEDIUM
        assert top_hints[3].priority == HintPriority.LOW


if __name__ == "__main__":
    pytest.main([__file__, "-v"])