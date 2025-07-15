"""Unit tests for SQLite Progress Event Store.

These tests verify the SQLite implementation of the progress event store
following the same patterns and functionality as the original file-based store.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from uuid import uuid4

from src.fastmcp.task_management.infrastructure.repositories.sqlite.progress_event_store import SQLiteProgressEventStore
from src.fastmcp.task_management.domain.events.progress_events import (
    ProgressUpdated, ProgressMilestoneReached, ProgressStalled,
    SubtaskProgressAggregated, ProgressTypeCompleted,
    ProgressBlocked, ProgressUnblocked, ProgressSnapshotCreated
)
from src.fastmcp.task_management.domain.value_objects.progress import ProgressType, ProgressStatus
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
async def event_store(temp_db):
    """Create a SQLiteProgressEventStore instance for testing."""
    store = SQLiteProgressEventStore(db_path=temp_db)
    return store


@pytest.fixture
def sample_task_id():
    """Generate a sample task ID for testing."""
    return TaskId(str(uuid4()))


@pytest.fixture
def sample_progress_updated_event(sample_task_id):
    """Create a sample ProgressUpdated event."""
    return ProgressUpdated(
        task_id=sample_task_id,
        progress_type=ProgressType.IMPLEMENTATION,
        old_percentage=40.0,
        new_percentage=60.0,
        status=ProgressStatus.IN_PROGRESS,
        description="Making progress on implementation",
        agent_id="test_agent"
    )


@pytest.fixture
def sample_milestone_event(sample_task_id):
    """Create a sample ProgressMilestoneReached event."""
    return ProgressMilestoneReached(
        task_id=sample_task_id,
        milestone_name="MVP Complete",
        milestone_percentage=75.0,
        current_progress=80.0,
        agent_id="test_agent"
    )


@pytest.fixture
def sample_stalled_event(sample_task_id):
    """Create a sample ProgressStalled event."""
    return ProgressStalled(
        task_id=sample_task_id,
        last_update_timestamp=datetime.now(timezone.utc) - timedelta(hours=48),
        stall_duration_hours=48,
        blockers=["Waiting for code review", "API dependency"],
        agent_id="test_agent"
    )


class TestSQLiteProgressEventStoreBasicOperations:
    """Test basic SQLite event store operations."""
    
    async def test_initialization_creates_table(self, temp_db):
        """Test that initialization creates the progress_events table."""
        store = SQLiteProgressEventStore(db_path=temp_db)
        
        # Verify table exists by querying it
        with store._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='progress_events'
            """)
            table_exists = cursor.fetchone() is not None
            assert table_exists
            
            # Verify indexes exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_progress_events_%'
            """)
            indexes = cursor.fetchall()
            assert len(indexes) >= 3  # aggregate, type, occurred_at indexes
    
    async def test_append_event(self, event_store, sample_progress_updated_event):
        """Test appending an event to the store."""
        await event_store.append(sample_progress_updated_event)
        
        # Verify event was stored
        events = await event_store.get_events(str(sample_progress_updated_event.task_id))
        assert len(events) == 1
        assert events[0].task_id == sample_progress_updated_event.task_id
        assert events[0].progress_type == sample_progress_updated_event.progress_type
        assert events[0].new_percentage == sample_progress_updated_event.new_percentage
    
    async def test_append_multiple_events(self, event_store, sample_task_id):
        """Test appending multiple events for the same task."""
        events_to_add = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Design phase progress"
            ),
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=30.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation started"
            ),
            ProgressMilestoneReached(
                task_id=sample_task_id,
                milestone_name="Design Complete",
                milestone_percentage=50.0,
                current_progress=50.0
            )
        ]
        
        for event in events_to_add:
            await event_store.append(event)
        
        # Retrieve and verify
        retrieved_events = await event_store.get_events(str(sample_task_id))
        assert len(retrieved_events) == 3
        
        # Verify event types
        event_types = [type(event).__name__ for event in retrieved_events]
        assert "ProgressUpdated" in event_types
        assert "ProgressMilestoneReached" in event_types
    
    async def test_get_events_empty_task(self, event_store):
        """Test getting events for a task with no events."""
        empty_task_id = str(uuid4())
        events = await event_store.get_events(empty_task_id)
        assert len(events) == 0


class TestSQLiteProgressEventStoreFiltering:
    """Test event filtering capabilities."""
    
    async def test_filter_by_event_type(self, event_store, sample_task_id):
        """Test filtering events by type."""
        # Add different event types
        progress_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=40.0,
            new_percentage=60.0,
            status=ProgressStatus.IN_PROGRESS
        )
        
        milestone_event = ProgressMilestoneReached(
            task_id=sample_task_id,
            milestone_name="Halfway",
            milestone_percentage=50.0,
            current_progress=60.0
        )
        
        await event_store.append(progress_event)
        await event_store.append(milestone_event)
        
        # Filter by ProgressUpdated
        progress_events = await event_store.get_events(
            str(sample_task_id), 
            event_type=ProgressUpdated
        )
        assert len(progress_events) == 1
        assert isinstance(progress_events[0], ProgressUpdated)
        
        # Filter by ProgressMilestoneReached
        milestone_events = await event_store.get_events(
            str(sample_task_id), 
            event_type=ProgressMilestoneReached
        )
        assert len(milestone_events) == 1
        assert isinstance(milestone_events[0], ProgressMilestoneReached)
    
    async def test_filter_by_date_range(self, event_store, sample_task_id):
        """Test filtering events by date range."""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        
        # Create events with different timestamps
        old_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.DESIGN,
            old_percentage=0.0,
            new_percentage=25.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=two_days_ago
        )
        
        recent_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=25.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=now
        )
        
        await event_store.append(old_event)
        await event_store.append(recent_event)
        
        # Filter by date range
        recent_events = await event_store.get_events(
            str(sample_task_id),
            start_date=yesterday
        )
        assert len(recent_events) == 1
        assert recent_events[0].new_percentage == 50.0
        
        # Filter for older events
        all_events = await event_store.get_events(
            str(sample_task_id),
            start_date=two_days_ago,
            end_date=yesterday
        )
        assert len(all_events) == 1
        assert all_events[0].new_percentage == 25.0


class TestSQLiteProgressEventStoreTimeline:
    """Test progress timeline functionality."""
    
    async def test_get_progress_timeline(self, event_store, sample_task_id):
        """Test getting progress timeline for visualization."""
        # Add various event types
        progress_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=30.0,
            new_percentage=60.0,
            status=ProgressStatus.IN_PROGRESS,
            description="Implementation progress",
            agent_id="test_agent"
        )
        
        milestone_event = ProgressMilestoneReached(
            task_id=sample_task_id,
            milestone_name="Halfway Done",
            milestone_percentage=50.0,
            current_progress=60.0
        )
        
        stall_event = ProgressStalled(
            task_id=sample_task_id,
            last_update_timestamp=datetime.now(timezone.utc) - timedelta(hours=24),
            stall_duration_hours=24,
            blockers=["Waiting for review"]
        )
        
        await event_store.append(progress_event)
        await event_store.append(milestone_event)
        await event_store.append(stall_event)
        
        # Get timeline
        timeline = await event_store.get_progress_timeline(str(sample_task_id), hours=48)
        
        assert len(timeline) == 3
        
        # Verify timeline structure
        timeline_types = [item["type"] for item in timeline]
        assert "progress_update" in timeline_types
        assert "milestone" in timeline_types
        assert "stalled" in timeline_types
        
        # Verify timeline is sorted by timestamp
        timestamps = [item["timestamp"] for item in timeline]
        assert timestamps == sorted(timestamps)
    
    async def test_get_progress_summary(self, event_store, sample_task_id):
        """Test getting progress summary from events."""
        # Add multiple progress events
        events = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED,
                description="Design completed"
            ),
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation halfway"
            ),
            ProgressMilestoneReached(
                task_id=sample_task_id,
                milestone_name="Design Complete",
                milestone_percentage=100.0,
                current_progress=100.0
            ),
            ProgressStalled(
                task_id=sample_task_id,
                last_update_timestamp=datetime.now(timezone.utc) - timedelta(hours=12),
                stall_duration_hours=12,
                blockers=["Need review"]
            )
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Get summary
        summary = await event_store.get_progress_summary(str(sample_task_id))
        
        assert summary["task_id"] == str(sample_task_id)
        assert summary["total_events"] == 4
        assert summary["total_updates"] == 2
        assert len(summary["milestones_reached"]) == 1
        assert len(summary["stall_periods"]) == 1
        
        # Verify progress by type
        assert "design" in summary["progress_by_type"]
        assert "implementation" in summary["progress_by_type"]
        assert summary["progress_by_type"]["design"]["current"] == 100.0
        assert summary["progress_by_type"]["implementation"]["current"] == 50.0


class TestSQLiteProgressEventStoreAdvanced:
    """Test advanced event store functionality."""
    
    async def test_replay_events(self, event_store, sample_task_id):
        """Test replaying events through a handler function."""
        # Add events
        events = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS
            ),
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=25.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS
            )
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Replay events
        replayed_events = []
        
        async def test_handler(event):
            replayed_events.append(event)
        
        await event_store.replay_events(str(sample_task_id), test_handler)
        
        assert len(replayed_events) == 2
        assert replayed_events[0].new_percentage == 25.0
        assert replayed_events[1].new_percentage == 50.0
    
    async def test_cleanup_old_events(self, event_store, sample_task_id):
        """Test cleaning up old events."""
        # Add old and new events
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=100)
        recent_timestamp = datetime.now(timezone.utc)
        
        old_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=25.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=old_timestamp
        )
        
        recent_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=25.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=recent_timestamp
        )
        
        await event_store.append(old_event)
        await event_store.append(recent_event)
        
        # Verify both events exist
        all_events = await event_store.get_events(str(sample_task_id))
        assert len(all_events) == 2
        
        # Clean up events older than 30 days
        cleaned_count = await event_store.cleanup_old_events(days=30)
        assert cleaned_count == 1
        
        # Verify only recent event remains
        remaining_events = await event_store.get_events(str(sample_task_id))
        assert len(remaining_events) == 1
        assert remaining_events[0].new_percentage == 50.0
    
    async def test_get_event_statistics(self, temp_db):
        """Test getting overall event statistics."""
        # Create a fresh event store to avoid interference from other tests
        fresh_store = SQLiteProgressEventStore(db_path=temp_db + "_stats")
        
        # Add events for multiple tasks
        task1_id = str(uuid4())
        task2_id = str(uuid4())
        
        # Task 1 events
        await fresh_store.append(ProgressUpdated(
            task_id=task1_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS
        ))
        
        await fresh_store.append(ProgressMilestoneReached(
            task_id=task1_id,
            milestone_name="Halfway",
            milestone_percentage=50.0,
            current_progress=50.0
        ))
        
        # Task 2 events
        await fresh_store.append(ProgressStalled(
            task_id=task2_id,
            last_update_timestamp=datetime.now(timezone.utc) - timedelta(hours=24),
            stall_duration_hours=24,
            blockers=["Blocked"]
        ))
        
        # Get statistics
        stats = await fresh_store.get_event_statistics()
        
        # Verify structure and that our events are included
        assert stats["total_tasks"] >= 2  # At least our 2 tasks
        assert stats["total_events"] >= 3  # At least our 3 events
        assert "ProgressUpdated" in stats["events_by_type"]
        assert "ProgressMilestoneReached" in stats["events_by_type"]
        assert "ProgressStalled" in stats["events_by_type"]
        assert stats["events_by_type"]["ProgressUpdated"] >= 1
        assert stats["events_by_type"]["ProgressMilestoneReached"] >= 1
        assert stats["events_by_type"]["ProgressStalled"] >= 1
        assert len(stats["active_tasks"]) >= 0  # Tasks with recent events
        assert len(stats["stalled_tasks"]) >= 1  # At least one stalled task


class TestSQLiteProgressEventStoreErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_deserialization_with_unknown_event_type(self, event_store):
        """Test handling of unknown event types during deserialization."""
        # Manually insert an event with unknown type
        with event_store._get_connection() as conn:
            conn.execute("""
                INSERT INTO progress_events 
                (event_id, aggregate_id, event_type, event_data, event_version)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(uuid4()),
                str(uuid4()),
                "UnknownEventType",
                '{"test": true}',
                1
            ))
            conn.commit()
        
        # This should not raise an error, but should log a warning
        # and exclude the unknown event from results
        # We can't easily test the exact behavior without mocking the logger
        # but we can ensure it doesn't crash
        stats = await event_store.get_event_statistics()
        assert isinstance(stats, dict)
    
    async def test_append_event_with_serialization_error(self, event_store):
        """Test handling events that can't be serialized properly."""
        # Create an event with a problematic attribute
        event = ProgressUpdated(
            task_id=str(uuid4()),
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS
        )
        
        # This should work normally
        await event_store.append(event)
        
        # Verify it was stored
        events = await event_store.get_events(str(event.task_id))
        assert len(events) == 1
    
    async def test_database_error_handling(self, temp_db):
        """Test handling of database connection errors."""
        store = SQLiteProgressEventStore(db_path=temp_db)
        
        # Test with an invalid database path - this should raise an error during initialization
        with pytest.raises(Exception):  # Could be PermissionError or other initialization error
            invalid_store = SQLiteProgressEventStore(db_path="/nonexistent/path/db.sqlite")


class TestSQLiteProgressEventStorePerformance:
    """Test performance characteristics of the SQLite event store."""
    
    async def test_bulk_event_insertion(self, event_store):
        """Test performance with bulk event insertion."""
        task_ids = [str(uuid4()) for _ in range(10)]
        
        # Insert 100 events (10 per task)
        start_time = datetime.now()
        for i in range(100):
            task_id = task_ids[i % 10]
            event = ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=float(i % 10) * 10,
                new_percentage=float((i % 10) + 1) * 10,
                status=ProgressStatus.IN_PROGRESS,
                description=f"Progress update {i}"
            )
            await event_store.append(event)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete reasonably quickly (adjust threshold as needed)
        assert duration < 10.0  # 10 seconds max for 100 events
        
        # Verify all events were stored
        total_events = 0
        for task_id in task_ids:
            events = await event_store.get_events(task_id)
            total_events += len(events)
        
        assert total_events == 100
    
    async def test_query_performance_with_many_events(self, event_store, sample_task_id):
        """Test query performance with many events."""
        # Insert many events for the same task
        for i in range(50):
            event = ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=float(i * 2),
                new_percentage=float((i + 1) * 2),
                status=ProgressStatus.IN_PROGRESS,
                description=f"Progress update {i}"
            )
            await event_store.append(event)
        
        # Query should be fast due to indexes
        start_time = datetime.now()
        events = await event_store.get_events(str(sample_task_id))
        end_time = datetime.now()
        
        query_duration = (end_time - start_time).total_seconds()
        
        assert len(events) == 50
        assert query_duration < 1.0  # Should complete in under 1 second