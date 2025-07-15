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


class TestHintGenerationRules:
    """Test hint generation rules."""
    
    def test_stalled_progress_rule(self):
        """Test StalledProgressRule."""
        rule = StalledProgressRule(stall_hours=24)
        
        # Create stalled task using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Test Task",
            description="A task that has stalled",
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
        
        # Create blocked task using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Blocked Task",
            description="A task that is blocked",
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
        
        # Create task with high implementation progress using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Implementation Complete Task",
            description="A task ready for testing",
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
        
        # Task without context using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Task Without Context",
            description="A task missing context",
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
        
        # Task with many dependencies using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Complex Task",
            description="A task with many dependencies",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        # Set dependencies manually since Task.create doesn't accept dependencies parameter
        task.dependencies = [TaskId(str(uuid4())) for _ in range(8)]
        
        context = RuleContext(task=task, context=None)
        hint = rule.evaluate(context)
        
        assert hint is not None
        assert hint.type == HintType.OPTIMIZATION
        assert hint.priority == HintPriority.MEDIUM
        assert "8 dependencies" in hint.message
        assert "decomposition" in hint.message
    
    def test_near_completion_rule(self):
        """Test NearCompletionRule."""
        rule = NearCompletionRule(completion_threshold=0.9)
        
        # Task near completion but missing some steps using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Near Completion Task",
            description="A task that is almost done",
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
        # Create a complex task scenario using Task.create factory method
        task = Task.create(
            id=TaskId(str(uuid4())),
            title="Multiple Rules Task",
            description="A task for testing multiple rules",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        # Set up task properties in the format expected by hint rules
        task.progress = 0.45  # Overall progress
        task.dependencies = [TaskId(str(uuid4())) for _ in range(6)]
        
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
        top_hints = collection.get_top_hints(2)
        assert len(top_hints) == 2
        assert top_hints[0].priority == HintPriority.CRITICAL
        assert top_hints[1].priority == HintPriority.HIGH