"""Unit tests for Vision System Phase 2: Progress Tracking.

These tests verify the functionality of:
- Progress domain models and value objects
- Task entity progress methods
- Progress tracking service
- Progress event handling with SQLite event store
- Progress calculations and aggregations
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
import uuid

from src.fastmcp.task_management.domain.value_objects.progress import (
    ProgressType, ProgressStatus, ProgressSnapshot, ProgressTimeline,
    ProgressMetadata, ProgressCalculationStrategy
)
from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority
from src.fastmcp.task_management.domain.events.progress_events import (
    ProgressUpdated, ProgressMilestoneReached, ProgressTypeCompleted
)
from src.fastmcp.task_management.application.services.progress_tracking_service import ProgressTrackingService
from src.fastmcp.task_management.application.event_handlers.progress_event_handlers import (
    ProgressUpdatedHandler, ProgressMilestoneReachedHandler
)
from src.fastmcp.task_management.infrastructure.repositories.sqlite.progress_event_store import SQLiteProgressEventStore

pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests


# SQLite Event Store Fixtures
@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sqlite_event_store(temp_db):
    """Create SQLite event store instance for testing"""
    return SQLiteProgressEventStore(db_path=temp_db)


class TestProgressValueObjects:
    """Test progress domain value objects."""
    
    def test_progress_metadata_creation(self):
        """Test creating progress metadata."""
        dep1 = str(uuid.uuid4())
        dep2 = str(uuid.uuid4())
        metadata = ProgressMetadata(
            blockers=["Waiting for API design"],
            dependencies=[dep1, dep2],
            confidence_level=0.8,
            notes="Making good progress",
            estimated_completion=datetime.now(timezone.utc) + timedelta(days=3)
        )
        
        assert len(metadata.blockers) == 1
        assert len(metadata.dependencies) == 2
        assert metadata.confidence_level == 0.8
        assert metadata.notes == "Making good progress"
        assert metadata.estimated_completion is not None
    
    def test_progress_snapshot_validation(self):
        """Test progress snapshot validation."""
        task_id = str(uuid.uuid4())
        # Valid snapshot
        snapshot = ProgressSnapshot(
            task_id=task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=75.0,
            status=ProgressStatus.IN_PROGRESS,
            description="Implementing core features"
        )
        
        assert snapshot.percentage == 75.0
        assert snapshot.progress_type == ProgressType.IMPLEMENTATION
        
        # Invalid percentage should raise error
        with pytest.raises(ValueError, match="percentage must be between 0 and 100"):
            ProgressSnapshot(
                task_id=task_id,
                percentage=150.0
            )
    
    def test_progress_timeline_operations(self):
        """Test progress timeline functionality."""
        task_id = str(uuid.uuid4())
        timeline = ProgressTimeline(task_id=task_id)
        
        # Add snapshots
        snapshot1 = ProgressSnapshot(
            task_id=task_id,
            progress_type=ProgressType.DESIGN,
            percentage=100.0,
            status=ProgressStatus.COMPLETED
        )
        
        snapshot2 = ProgressSnapshot(
            task_id=task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=50.0,
            status=ProgressStatus.IN_PROGRESS
        )
        
        timeline.add_snapshot(snapshot1)
        timeline.add_snapshot(snapshot2)
        
        # Test timeline operations
        assert len(timeline.snapshots) == 2
        assert timeline.get_latest_snapshot() == snapshot2
        
        # Test progress calculation
        overall = timeline.get_overall_progress()
        assert overall == 75.0  # (100 + 50) / 2
        
        # Test milestone tracking
        timeline.add_milestone("MVP", 80.0)
        assert not timeline.is_milestone_reached("MVP")  # 75% < 80%
    
    def test_progress_calculation_strategies(self):
        """Test different progress calculation strategies."""
        # Test weighted average
        progress_values = {
            "implementation": 80.0,
            "testing": 40.0,
            "documentation": 20.0
        }
        weights = {
            "implementation": 0.5,
            "testing": 0.3,
            "documentation": 0.2
        }
        
        result = ProgressCalculationStrategy.calculate_weighted_average(
            progress_values, weights
        )
        # (80*0.5 + 40*0.3 + 20*0.2) = 40 + 12 + 4 = 56
        assert result == 56.0
        
        # Test subtask calculation
        subtasks = [
            {"id": "1", "status": "done", "progress": 100.0},
            {"id": "2", "status": "in_progress", "progress": 50.0},
            {"id": "3", "status": "blocked", "progress": 25.0}
        ]
        
        # Without blocked tasks
        result = ProgressCalculationStrategy.calculate_from_subtasks(
            subtasks, include_blocked=False
        )
        assert result == 75.0  # (100 + 50) / 2
        
        # With blocked tasks
        result = ProgressCalculationStrategy.calculate_from_subtasks(
            subtasks, include_blocked=True
        )
        assert result == 58.333333333333336  # (100 + 50 + 25) / 3


class TestTaskProgressMethods:
    """Test task entity progress tracking methods."""
    
    def test_update_progress(self):
        """Test updating task progress."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Implement user authentication",
            description="Add JWT-based auth"
        )
        
        # Update progress
        task.update_progress(
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=60.0,
            description="Completed login endpoint",
            metadata={"blockers": ["Waiting for security review"]},
            agent_id="test_agent"
        )
        
        # Verify progress update
        assert task.overall_progress > 0
        assert task.progress_timeline is not None
        assert len(task.progress_timeline.snapshots) == 1
        assert task.get_progress_by_type(ProgressType.IMPLEMENTATION) == 60.0
        
        # Check events
        events = task.get_events()
        progress_events = [e for e in events if isinstance(e, ProgressUpdated)]
        assert len(progress_events) == 1
        assert progress_events[0].new_percentage == 60.0
    
    def test_progress_with_subtasks(self):
        """Test progress calculation with subtasks."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Build feature",
            description="Complete feature implementation"
        )
        
        # Add subtasks
        task.add_subtask(title="Design API", status="done")
        task.add_subtask(title="Implement backend", status="in_progress")
        task.add_subtask(title="Write tests", status="todo")
        
        # Calculate progress from subtasks
        progress = task.calculate_progress_from_subtasks()
        assert progress > 0  # Should have some progress
        
        # Update task progress
        task.update_progress(
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=40.0,
            description="Backend partially done"
        )
        
        # Overall progress should consider both
        assert task.overall_progress > 0
        assert task.overall_progress <= 100
    
    def test_progress_milestones(self):
        """Test progress milestone tracking."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Major feature",
            description="Implement major feature"
        )
        
        # Add milestones
        task.add_progress_milestone("Design Complete", 25.0)
        task.add_progress_milestone("MVP Ready", 75.0)
        task.add_progress_milestone("Testing Done", 90.0)
        
        # Update progress and check milestone events
        task.update_progress(ProgressType.DESIGN, 30.0)
        
        events = task.get_events()
        milestone_events = [e for e in events if isinstance(e, ProgressMilestoneReached)]
        assert len(milestone_events) == 1
        assert milestone_events[0].milestone_name == "Design Complete"
    
    def test_progress_type_completion(self):
        """Test progress type completion events."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Feature",
            description="Build feature"
        )
        
        # Complete a progress type
        task.update_progress(ProgressType.DESIGN, 100.0, "Design completed")
        
        events = task.get_events()
        completion_events = [e for e in events if isinstance(e, ProgressTypeCompleted)]
        assert len(completion_events) == 1
        assert completion_events[0].progress_type == ProgressType.DESIGN


@pytest.mark.asyncio
class TestProgressTrackingService:
    """Test progress tracking service."""
    
    async def test_update_progress(self):
        """Test updating progress through service."""
        # Setup mocks
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        event_bus = AsyncMock()
        
        # Create test task
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Test task",
            description="Test description"
        )
        task_repo.get_by_id.return_value = task
        task_repo.update.return_value = None
        event_bus.publish.return_value = None
        
        # Create service
        service = ProgressTrackingService(task_repo, context_service, event_bus)
        
        # Update progress
        result = await service.update_progress(
            task_id=task.id.value,
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=75.0,
            description="Making progress",
            metadata={"blockers": ["Need review"]},
            agent_id="test_agent"
        )
        
        # Verify
        assert result.overall_progress > 0
        assert task_repo.update.called
        assert event_bus.publish.called
    
    async def test_batch_progress_update(self):
        """Test batch progress updates."""
        # Setup
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        event_bus = AsyncMock()
        
        # Create tasks
        task1 = Task.create(TaskId(str(uuid.uuid4())), "Task 1", "Description 1")
        task2 = Task.create(TaskId(str(uuid.uuid4())), "Task 2", "Description 2")
        
        task_repo.get_by_id.side_effect = [task1, task2]
        task_repo.update.return_value = None
        event_bus.publish.return_value = None
        
        service = ProgressTrackingService(task_repo, context_service, event_bus)
        
        # Batch update
        updates = [
            {
                "task_id": task1.id.value,
                "progress_type": ProgressType.IMPLEMENTATION,
                "percentage": 50.0,
                "description": "Half done"
            },
            {
                "task_id": task2.id.value,
                "progress_type": ProgressType.TESTING,
                "percentage": 25.0,
                "description": "Starting tests"
            }
        ]
        
        results = await service.batch_update_progress(updates)
        
        assert len(results) == 2
        assert task_repo.update.call_count == 2
    
    async def test_progress_calculation(self):
        """Test overall progress calculation."""
        # Setup
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        event_bus = AsyncMock()
        
        # Create task with progress
        task = Task.create(TaskId(str(uuid.uuid4())), "Task", "Description")
        task.update_progress(ProgressType.DESIGN, 100.0)
        task.update_progress(ProgressType.IMPLEMENTATION, 60.0)
        task.add_subtask(title="Subtask 1", status="done")
        task.add_subtask(title="Subtask 2", status="in_progress")
        
        task_repo.get_by_id.return_value = task
        
        service = ProgressTrackingService(task_repo, context_service, event_bus)
        
        # Calculate with default weights
        progress = await service.calculate_overall_progress(task.id.value)
        assert progress > 0
        assert progress <= 100
        
        # Calculate with custom weights
        weights = {
            "design": 0.2,
            "implementation": 0.5,
            "subtasks": 0.3
        }
        weighted_progress = await service.calculate_overall_progress(
            task.id.value, 
            weights=weights
        )
        assert weighted_progress > 0
    
    async def test_progress_timeline_retrieval(self):
        """Test getting progress timeline."""
        # Setup
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        event_bus = AsyncMock()
        
        # Create task with history
        task = Task.create(TaskId(str(uuid.uuid4())), "Task", "Description")
        
        # Add multiple progress updates
        for i in range(5):
            task.update_progress(
                ProgressType.IMPLEMENTATION,
                float(i * 20),
                f"Progress update {i}"
            )
        
        task_repo.get_by_id.return_value = task
        
        service = ProgressTrackingService(task_repo, context_service, event_bus)
        
        # Get timeline
        timeline = await service.get_progress_timeline(task.id.value, hours=24)
        
        assert len(timeline) > 0
        assert all(isinstance(s, ProgressSnapshot) for s in timeline)
    
    async def test_milestone_management(self):
        """Test milestone setting and checking."""
        # Setup
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        event_bus = AsyncMock()
        
        task = Task.create(TaskId(str(uuid.uuid4())), "Task", "Description")
        task_repo.get_by_id.return_value = task
        task_repo.update.return_value = None
        
        service = ProgressTrackingService(task_repo, context_service, event_bus)
        
        # Set milestones
        await service.set_progress_milestone(task.id.value, "Alpha", 40.0)
        await service.set_progress_milestone(task.id.value, "Beta", 70.0)
        await service.set_progress_milestone(task.id.value, "Release", 95.0)
        
        # Update progress
        task.update_progress(ProgressType.GENERAL, 75.0)
        
        # Check milestones
        reached = await service.check_milestones(task.id.value)
        
        assert "Alpha" in reached  # 75% > 40%
        assert "Beta" in reached   # 75% > 70%
        assert "Release" not in reached  # 75% < 95%
    
    async def test_progress_inference(self):
        """Test inferring progress from context."""
        # Setup
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        event_bus = AsyncMock()
        
        task = Task.create(TaskId(str(uuid.uuid4())), "Task", "Description")
        task.context_id = "CTX-123"
        
        # Mock context with progress indicators
        context = Mock()
        context.insights = [
            {"content": "Started working on the implementation"},
            {"content": "Making good progress on core features"}
        ]
        context.progress = [
            {"content": "Completed initial setup"}
        ]
        
        task_repo.get_by_id.return_value = task
        context_service.get_by_id.return_value = context
        
        service = ProgressTrackingService(task_repo, context_service, event_bus)
        
        # Infer progress
        inferred = await service.infer_progress_from_context(task.id.value)
        
        assert inferred is not None
        assert inferred > 0  # Should detect "started" keyword


@pytest.mark.asyncio
class TestProgressEventHandlers:
    """Test progress event handlers with SQLite event store."""
    
    async def test_progress_updated_handler_with_sqlite(self, sqlite_event_store):
        """Test handling progress updated events with SQLite event store."""
        # Setup
        task_repo = AsyncMock()
        context_service = AsyncMock()  # Use hierarchical context service
        
        task_id = TaskId(str(uuid.uuid4()))
        task = Task.create(task_id, "Task", "Description")
        task.context_id = "CTX-123"
        task.progress_timeline = ProgressTimeline(task_id=task.id.value)
        task.progress_timeline.add_milestone("Halfway", 50.0)
        
        context = Mock()
        context.insights = []
        
        task_repo.get_by_id.return_value = task
        context_service.get_by_id.return_value = context
        context_service.update.return_value = None
        
        handler = ProgressUpdatedHandler(task_repo, context_service, sqlite_event_store)
        
        # Create event
        event = ProgressUpdated(
            task_id=task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=45.0,
            new_percentage=55.0,
            status=ProgressStatus.IN_PROGRESS,
            description="Crossing milestone threshold"
        )
        
        # Handle event
        await handler.handle(event)
        
        # Verify event was stored in SQLite
        stored_events = await sqlite_event_store.get_events(str(event.task_id))
        assert len(stored_events) == 1
        assert stored_events[0].description == "Crossing milestone threshold"
        assert stored_events[0].new_percentage == 55.0
        
        # Context should be updated when crossing 50% threshold
        assert context_service.update.called
    
    async def test_milestone_reached_handler_with_sqlite(self, sqlite_event_store):
        """Test handling milestone reached events with SQLite event store."""
        # Setup
        notification_service = AsyncMock()
        notification_service.notify.return_value = None
        
        handler = ProgressMilestoneReachedHandler(notification_service, sqlite_event_store)
        
        # Create event
        event = ProgressMilestoneReached(
            task_id=TaskId(str(uuid.uuid4())),
            milestone_name="MVP Complete",
            milestone_percentage=80.0,
            current_progress=82.0
        )
        
        # Handle event
        await handler.handle(event)
        
        # Verify event was stored in SQLite
        stored_events = await sqlite_event_store.get_events(str(event.task_id))
        assert len(stored_events) == 1
        assert stored_events[0].milestone_name == "MVP Complete"
        assert stored_events[0].milestone_percentage == 80.0
        
        # Verify notification was sent
        assert notification_service.notify.called
        
        # Check notification content
        notify_call = notification_service.notify.call_args
        assert notify_call[1]["type"] == "milestone_reached"
        assert notify_call[1]["data"]["milestone"] == "MVP Complete"
    
    async def test_event_store_timeline_integration(self, sqlite_event_store):
        """Test event store timeline generation with actual events."""
        task_id = TaskId(str(uuid.uuid4()))
        
        # Create sequence of events
        events = [
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Started implementation",
                agent_id="test_agent"
            ),
            ProgressMilestoneReached(
                task_id=task_id,
                milestone_name="Quarter Complete",
                milestone_percentage=25.0,
                current_progress=25.0
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=25.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Halfway through implementation"
            )
        ]
        
        # Store events
        for event in events:
            await sqlite_event_store.append(event)
        
        # Get timeline
        timeline = await sqlite_event_store.get_progress_timeline(str(task_id), hours=24)
        
        # Verify timeline structure
        assert len(timeline) == 3
        assert timeline[0]["type"] == "progress_update"
        assert timeline[0]["percentage"] == 25.0
        assert timeline[0]["agent"] == "test_agent"
        
        assert timeline[1]["type"] == "milestone"
        assert timeline[1]["milestone"] == "Quarter Complete"
        
        assert timeline[2]["type"] == "progress_update"
        assert timeline[2]["percentage"] == 50.0
    
    async def test_event_store_summary_integration(self, sqlite_event_store):
        """Test event store summary generation with real events."""
        task_id = TaskId(str(uuid.uuid4()))
        
        # Create comprehensive event set
        events = [
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED,
                description="Design completed"
            ),
            ProgressTypeCompleted(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                completion_timestamp=datetime.now(timezone.utc)
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=60.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation in progress"
            ),
            ProgressMilestoneReached(
                task_id=task_id,
                milestone_name="Implementation Started",
                milestone_percentage=50.0,
                current_progress=60.0
            )
        ]
        
        # Store events
        for event in events:
            await sqlite_event_store.append(event)
        
        # Get summary
        summary = await sqlite_event_store.get_progress_summary(str(task_id))
        
        # Verify summary
        assert summary["total_events"] == 4
        assert summary["total_updates"] == 2
        assert "design" in summary["progress_by_type"]
        assert "implementation" in summary["progress_by_type"]
        assert summary["progress_by_type"]["design"]["current"] == 100.0
        assert summary["progress_by_type"]["implementation"]["current"] == 60.0
        
        # Check milestones
        assert len(summary["milestones_reached"]) == 1
        assert summary["milestones_reached"][0]["name"] == "Implementation Started"


class TestProgressIntegration:
    """Integration tests for progress tracking."""
    
    def test_task_to_dict_includes_progress(self):
        """Test that task serialization includes progress data."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Task with progress",
            description="Description"
        )
        
        # Add progress
        task.update_progress(
            ProgressType.IMPLEMENTATION,
            65.0,
            "Making progress"
        )
        
        # Serialize
        task_dict = task.to_dict()
        
        # Verify progress fields
        assert "overall_progress" in task_dict
        assert task_dict["overall_progress"] == task.overall_progress
        assert "progress_timeline" in task_dict
        assert task_dict["progress_timeline"]["task_id"] == task.id.value
    
    def test_progress_events_in_task_lifecycle(self):
        """Test progress events during task lifecycle."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Lifecycle test",
            description="Test task lifecycle with progress"
        )
        
        # Clear initial events
        task.get_events()
        
        # Add milestone
        task.add_progress_milestone("Halfway", 50.0)
        
        # Progress updates
        task.update_progress(ProgressType.DESIGN, 100.0)
        task.update_progress(ProgressType.IMPLEMENTATION, 60.0)
        
        # Get all events
        events = task.get_events()
        
        # Verify event types
        event_types = [type(e).__name__ for e in events]
        assert "ProgressUpdated" in event_types
        assert "ProgressTypeCompleted" in event_types
        assert "ProgressMilestoneReached" in event_types
    
    def test_subtask_progress_aggregation(self):
        """Test progress aggregation from subtasks."""
        parent = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Parent task",
            description="Has subtasks"
        )
        
        # Add subtasks with different statuses
        st1 = parent.add_subtask(title="Complete subtask", status="done")
        st2 = parent.add_subtask(title="In progress subtask", status="in_progress")
        st3 = parent.add_subtask(title="Not started", status="todo")
        st4 = parent.add_subtask(title="Blocked subtask", status="blocked")
        
        # Calculate progress excluding blocked
        progress = parent.calculate_progress_from_subtasks(include_blocked=False)
        assert progress > 0
        assert progress < 100
        
        # Verify subtask progress info
        progress_info = parent.get_subtask_progress()
        assert progress_info["total"] == 4
        assert progress_info["completed"] == 1
        assert progress_info["percentage"] > 0


class TestSQLiteProgressEventStoreIntegration:
    """Test SQLite-specific progress event store integration"""
    
    @pytest.mark.asyncio
    async def test_progress_tracking_with_sqlite_persistence(self, sqlite_event_store):
        """Test complete progress tracking workflow with SQLite persistence"""
        task_id = TaskId(str(uuid.uuid4()))
        
        # Simulate complete task lifecycle with progress events
        lifecycle_events = [
            # Design phase
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Design phase started"
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=50.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED,
                description="Design phase completed"
            ),
            ProgressTypeCompleted(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                completion_timestamp=datetime.now(timezone.utc)
            ),
            # Implementation phase
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=30.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation started"
            ),
            ProgressMilestoneReached(
                task_id=task_id,
                milestone_name="Development Started",
                milestone_percentage=25.0,
                current_progress=30.0
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=30.0,
                new_percentage=75.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Major implementation progress"
            ),
            ProgressMilestoneReached(
                task_id=task_id,
                milestone_name="Core Features Complete",
                milestone_percentage=70.0,
                current_progress=75.0
            )
        ]
        
        # Store all events in SQLite
        for event in lifecycle_events:
            await sqlite_event_store.append(event)
        
        # Verify complete event history is preserved
        stored_events = await sqlite_event_store.get_events(str(task_id))
        assert len(stored_events) == len(lifecycle_events)
        
        # Verify event types are preserved
        progress_updates = [e for e in stored_events if isinstance(e, ProgressUpdated)]
        milestones = [e for e in stored_events if isinstance(e, ProgressMilestoneReached)]
        completions = [e for e in stored_events if isinstance(e, ProgressTypeCompleted)]
        
        assert len(progress_updates) == 4
        assert len(milestones) == 2
        assert len(completions) == 1
        
        # Verify design completion
        design_completion = completions[0]
        assert design_completion.progress_type == ProgressType.DESIGN
        
        # Verify milestone progression
        milestone_names = [m.milestone_name for m in milestones]
        assert "Development Started" in milestone_names
        assert "Core Features Complete" in milestone_names
        
        # Test progress summary accuracy
        summary = await sqlite_event_store.get_progress_summary(str(task_id))
        assert summary["progress_by_type"]["design"]["current"] == 100.0
        assert summary["progress_by_type"]["implementation"]["current"] == 75.0
        assert len(summary["milestones_reached"]) == 2
        
        # Test timeline visualization
        timeline = await sqlite_event_store.get_progress_timeline(str(task_id), hours=24)
        assert len(timeline) == 6  # 4 progress updates + 2 milestones
        
        # Verify timeline ordering
        timeline_types = [entry["type"] for entry in timeline]
        assert "progress_update" in timeline_types
        assert "milestone" in timeline_types
    
    @pytest.mark.asyncio
    async def test_concurrent_progress_tracking_sqlite(self, sqlite_event_store):
        """Test concurrent progress tracking with SQLite locking"""
        import asyncio
        
        # Create multiple tasks for concurrent testing
        task_ids = [TaskId(str(uuid.uuid4())) for _ in range(3)]
        
        async def update_task_progress(task_id, task_index):
            """Update progress for a single task"""
            events = []
            for i in range(5):
                event = ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=float(i * 20),
                    new_percentage=float((i + 1) * 20),
                    status=ProgressStatus.IN_PROGRESS,
                    description=f"Task {task_index} progress {i + 1}",
                    agent_id=f"agent_{task_index}"
                )
                events.append(event)
                await sqlite_event_store.append(event)
            return events
        
        # Run concurrent progress updates
        tasks = [update_task_progress(task_id, i) for i, task_id in enumerate(task_ids)]
        results = await asyncio.gather(*tasks)
        
        # Verify all events were stored correctly
        for i, task_id in enumerate(task_ids):
            stored_events = await sqlite_event_store.get_events(str(task_id))
            assert len(stored_events) == 5
            
            # Verify agent assignment
            for event in stored_events:
                assert event.agent_id == f"agent_{i}"
            
            # Verify progress sequence
            percentages = [e.new_percentage for e in stored_events]
            assert percentages == [20.0, 40.0, 60.0, 80.0, 100.0]
        
        # Test global statistics
        stats = await sqlite_event_store.get_event_statistics()
        assert stats["total_events"] == 15  # 3 tasks * 5 events each
        assert stats["total_tasks"] == 3
    
    @pytest.mark.asyncio
    async def test_sqlite_event_replay_functionality(self, sqlite_event_store):
        """Test event replay for task state reconstruction"""
        task_id = TaskId(str(uuid.uuid4()))
        
        # Create events representing task state changes
        state_events = [
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED,
                description="Design completed",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=3)
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation started",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=25.0,
                new_percentage=75.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation progressing",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=1)
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.TESTING,
                old_percentage=0.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Testing started",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        # Store events
        for event in state_events:
            await sqlite_event_store.append(event)
        
        # Reconstruct task state through event replay
        reconstructed_state = {
            "design_progress": 0.0,
            "implementation_progress": 0.0,
            "testing_progress": 0.0,
            "last_update": None,
            "event_count": 0
        }
        
        async def state_reconstruction_handler(event):
            """Handler to reconstruct task state from events"""
            if isinstance(event, ProgressUpdated):
                reconstructed_state["event_count"] += 1
                reconstructed_state["last_update"] = event.timestamp
                
                if event.progress_type == ProgressType.DESIGN:
                    reconstructed_state["design_progress"] = event.new_percentage
                elif event.progress_type == ProgressType.IMPLEMENTATION:
                    reconstructed_state["implementation_progress"] = event.new_percentage
                elif event.progress_type == ProgressType.TESTING:
                    reconstructed_state["testing_progress"] = event.new_percentage
        
        # Replay events to reconstruct state
        await sqlite_event_store.replay_events(str(task_id), state_reconstruction_handler)
        
        # Verify reconstructed state
        assert reconstructed_state["design_progress"] == 100.0
        assert reconstructed_state["implementation_progress"] == 75.0
        assert reconstructed_state["testing_progress"] == 50.0
        assert reconstructed_state["event_count"] == 4
        assert reconstructed_state["last_update"] is not None
    
    @pytest.mark.asyncio
    async def test_sqlite_progress_analytics(self, sqlite_event_store):
        """Test progress analytics capabilities with SQLite"""
        # Create multiple tasks with different progress patterns
        tasks_data = [
            {
                "task_id": TaskId(str(uuid.uuid4())),
                "pattern": "fast_start",  # Quick initial progress, then slow
                "final_progress": 80.0
            },
            {
                "task_id": TaskId(str(uuid.uuid4())),
                "pattern": "steady",  # Steady progress
                "final_progress": 60.0
            },
            {
                "task_id": TaskId(str(uuid.uuid4())),
                "pattern": "slow_start",  # Slow initial, then fast
                "final_progress": 90.0
            }
        ]
        
        # Generate progress patterns
        for task_data in tasks_data:
            task_id = task_data["task_id"]
            pattern = task_data["pattern"]
            final = task_data["final_progress"]
            
            if pattern == "fast_start":
                progress_points = [0, 40, 50, 60, final]
            elif pattern == "steady":
                progress_points = [0, 15, 30, 45, final]
            else:  # slow_start
                progress_points = [0, 10, 20, 70, final]
            
            for i, progress in enumerate(progress_points[1:], 1):
                event = ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=progress_points[i-1],
                    new_percentage=progress,
                    status=ProgressStatus.IN_PROGRESS,
                    description=f"{pattern} pattern step {i}",
                    timestamp=datetime.now(timezone.utc) - timedelta(hours=5-i)
                )
                await sqlite_event_store.append(event)
        
        # Test analytics across all tasks
        stats = await sqlite_event_store.get_event_statistics()
        assert stats["total_tasks"] == 3
        assert stats["total_events"] == 12  # 4 events per task
        
        # Test individual task analytics
        for task_data in tasks_data:
            task_id = str(task_data["task_id"])
            summary = await sqlite_event_store.get_progress_summary(task_id)
            
            # Verify final progress matches expected
            current_progress = summary["progress_by_type"]["implementation"]["current"]
            assert current_progress == task_data["final_progress"]
            
            # Verify update count
            assert summary["total_updates"] == 4
            
            # Test timeline for this task
            timeline = await sqlite_event_store.get_progress_timeline(task_id, hours=24)
            assert len(timeline) == 4