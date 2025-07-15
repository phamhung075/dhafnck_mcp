"""Unit tests for SQLite Progress Event Store Implementation

Tests the SQLite-based progress event store functionality including:
- Event storage and retrieval
- Event serialization/deserialization  
- Timeline generation
- Event filtering and querying
- Performance and concurrency aspects
"""

import pytest
import tempfile
import os
import json
import asyncio
import sqlite3
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import patch, Mock
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.fastmcp.task_management.infrastructure.repositories.sqlite.progress_event_store import SQLiteProgressEventStore
from src.fastmcp.task_management.domain.events.progress_events import (
    ProgressEvent, ProgressUpdated, ProgressMilestoneReached,
    ProgressStalled, SubtaskProgressAggregated, ProgressTypeCompleted,
    ProgressBlocked, ProgressUnblocked, ProgressSnapshotCreated
)
from src.fastmcp.task_management.domain.value_objects.progress import ProgressType, ProgressStatus
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId

pytestmark = pytest.mark.unit


class TestSQLiteProgressEventStore:
    """Test SQLite progress event store functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store instance for testing"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.fixture
    def sample_task_id(self):
        """Sample task ID for testing"""
        return TaskId(str(uuid4()))
    
    @pytest.fixture
    def sample_progress_updated_event(self, sample_task_id):
        """Sample ProgressUpdated event"""
        return ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=30.0,
            new_percentage=60.0,
            status=ProgressStatus.IN_PROGRESS,
            description="Making good progress on implementation",
            agent_id="test_agent"
        )
    
    @pytest.fixture
    def sample_milestone_event(self, sample_task_id):
        """Sample ProgressMilestoneReached event"""
        return ProgressMilestoneReached(
            task_id=sample_task_id,
            milestone_name="Alpha Release",
            milestone_percentage=50.0,
            current_progress=55.0
        )
    
    def test_event_store_initialization(self, temp_db):
        """Test event store proper initialization"""
        store = SQLiteProgressEventStore(db_path=temp_db)
        
        # Verify table creation
        with store._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='progress_events'
            """)
            assert cursor.fetchone() is not None
        
        # Verify indexes creation
        with store._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='progress_events'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            assert 'idx_progress_events_aggregate' in indexes
            assert 'idx_progress_events_type' in indexes
            assert 'idx_progress_events_occurred_at' in indexes

    @pytest.mark.asyncio
    async def test_append_progress_updated_event(self, event_store, sample_progress_updated_event):
        """Test appending ProgressUpdated event"""
        await event_store.append(sample_progress_updated_event)
        
        # Verify event was stored
        events = await event_store.get_events(str(sample_progress_updated_event.task_id))
        assert len(events) == 1
        
        stored_event = events[0]
        assert isinstance(stored_event, ProgressUpdated)
        assert stored_event.task_id == sample_progress_updated_event.task_id
        assert stored_event.progress_type == ProgressType.IMPLEMENTATION
        assert stored_event.old_percentage == 30.0
        assert stored_event.new_percentage == 60.0
        assert stored_event.status == ProgressStatus.IN_PROGRESS
        assert stored_event.description == "Making good progress on implementation"
        assert stored_event.agent_id == "test_agent"

    @pytest.mark.asyncio
    async def test_append_milestone_event(self, event_store, sample_milestone_event):
        """Test appending ProgressMilestoneReached event"""
        await event_store.append(sample_milestone_event)
        
        events = await event_store.get_events(str(sample_milestone_event.task_id))
        assert len(events) == 1
        
        stored_event = events[0]
        assert isinstance(stored_event, ProgressMilestoneReached)
        assert stored_event.milestone_name == "Alpha Release"
        assert stored_event.milestone_percentage == 50.0
        assert stored_event.current_progress == 55.0

    @pytest.mark.asyncio
    async def test_append_multiple_events(self, event_store, sample_task_id):
        """Test appending multiple different event types"""
        events_to_store = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS
            ),
            ProgressMilestoneReached(
                task_id=sample_task_id,
                milestone_name="Design Complete",
                milestone_percentage=25.0,
                current_progress=25.0
            ),
            ProgressStalled(
                task_id=sample_task_id,
                last_update_timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
                stall_duration_hours=2,
                blockers=["Waiting for review"]
            ),
            ProgressTypeCompleted(
                task_id=sample_task_id,
                progress_type=ProgressType.DESIGN,
                completion_timestamp=datetime.now(timezone.utc)
            )
        ]
        
        # Store all events
        for event in events_to_store:
            await event_store.append(event)
        
        # Retrieve and verify
        stored_events = await event_store.get_events(str(sample_task_id))
        assert len(stored_events) == 4
        
        # Verify event types
        event_types = [type(e).__name__ for e in stored_events]
        expected_types = ['ProgressUpdated', 'ProgressMilestoneReached', 'ProgressStalled', 'ProgressTypeCompleted']
        assert set(event_types) == set(expected_types)

    @pytest.mark.asyncio
    async def test_get_events_with_type_filter(self, event_store, sample_task_id):
        """Test filtering events by type"""
        # Store multiple event types
        events = [
            ProgressUpdated(task_id=sample_task_id, progress_type=ProgressType.IMPLEMENTATION, 
                          old_percentage=0.0, new_percentage=30.0, status=ProgressStatus.IN_PROGRESS),
            ProgressUpdated(task_id=sample_task_id, progress_type=ProgressType.IMPLEMENTATION,
                          old_percentage=30.0, new_percentage=60.0, status=ProgressStatus.IN_PROGRESS),
            ProgressMilestoneReached(task_id=sample_task_id, milestone_name="Halfway", 
                                   milestone_percentage=50.0, current_progress=60.0)
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Filter by ProgressUpdated
        progress_events = await event_store.get_events(str(sample_task_id), event_type=ProgressUpdated)
        assert len(progress_events) == 2
        assert all(isinstance(e, ProgressUpdated) for e in progress_events)
        
        # Filter by ProgressMilestoneReached
        milestone_events = await event_store.get_events(str(sample_task_id), event_type=ProgressMilestoneReached)
        assert len(milestone_events) == 1
        assert isinstance(milestone_events[0], ProgressMilestoneReached)

    @pytest.mark.asyncio
    async def test_get_events_with_date_filter(self, event_store, sample_task_id):
        """Test filtering events by date range"""
        now = datetime.now(timezone.utc)
        
        # Create events with different timestamps
        old_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=25.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=now - timedelta(days=2)
        )
        
        recent_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=25.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=now - timedelta(hours=1)
        )
        
        await event_store.append(old_event)
        await event_store.append(recent_event)
        
        # Filter by start date (only recent)
        recent_events = await event_store.get_events(
            str(sample_task_id),
            start_date=now - timedelta(hours=2)
        )
        assert len(recent_events) == 1
        assert recent_events[0].new_percentage == 50.0
        
        # Filter by end date (only old)
        old_events = await event_store.get_events(
            str(sample_task_id),
            end_date=now - timedelta(hours=2)
        )
        assert len(old_events) == 1
        assert old_events[0].new_percentage == 25.0

    @pytest.mark.asyncio
    async def test_get_progress_timeline(self, event_store, sample_task_id):
        """Test progress timeline generation"""
        now = datetime.now(timezone.utc)
        
        # Create events for timeline
        events = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Started implementation",
                agent_id="agent_1",
                timestamp=now - timedelta(hours=3)
            ),
            ProgressMilestoneReached(
                task_id=sample_task_id,
                milestone_name="Quarter Done",
                milestone_percentage=25.0,
                current_progress=25.0,
                timestamp=now - timedelta(hours=2)
            ),
            ProgressStalled(
                task_id=sample_task_id,
                last_update_timestamp=now - timedelta(hours=2),
                stall_duration_hours=1,
                blockers=["Code review pending"],
                timestamp=now - timedelta(hours=1)
            )
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Get timeline
        timeline = await event_store.get_progress_timeline(str(sample_task_id), hours=24)
        
        assert len(timeline) == 3
        assert timeline[0]["type"] == "progress_update"
        assert timeline[0]["percentage"] == 25.0
        assert timeline[0]["agent"] == "agent_1"
        
        assert timeline[1]["type"] == "milestone"
        assert timeline[1]["milestone"] == "Quarter Done"
        
        assert timeline[2]["type"] == "stalled"
        assert timeline[2]["duration_hours"] == 1
        assert timeline[2]["blockers"] == ["Code review pending"]
        
        # Verify timeline is sorted by timestamp
        timestamps = [entry["timestamp"] for entry in timeline]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_get_progress_summary(self, event_store, sample_task_id):
        """Test progress summary generation"""
        # Create comprehensive event set
        events = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED
            ),
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS
            ),
            ProgressMilestoneReached(
                task_id=sample_task_id,
                milestone_name="Design Done",
                milestone_percentage=25.0,
                current_progress=100.0
            ),
            ProgressStalled(
                task_id=sample_task_id,
                last_update_timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
                stall_duration_hours=1,
                blockers=["Waiting for API"]
            )
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Get summary
        summary = await event_store.get_progress_summary(str(sample_task_id))
        
        assert summary["task_id"] == str(sample_task_id)
        assert summary["total_events"] == 4
        assert summary["total_updates"] == 2
        assert summary["last_update"] is not None
        
        # Check progress by type
        assert "design" in summary["progress_by_type"]
        assert "implementation" in summary["progress_by_type"]
        assert summary["progress_by_type"]["design"]["current"] == 100.0
        assert summary["progress_by_type"]["implementation"]["current"] == 50.0
        
        # Check milestones
        assert len(summary["milestones_reached"]) == 1
        assert summary["milestones_reached"][0]["name"] == "Design Done"
        
        # Check stall periods
        assert len(summary["stall_periods"]) == 1
        assert summary["stall_periods"][0]["duration_hours"] == 1

    @pytest.mark.asyncio
    async def test_event_serialization_deserialization(self, event_store, sample_task_id):
        """Test event serialization and deserialization with various data types"""
        complex_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.TESTING,
            old_percentage=75.5,
            new_percentage=85.75,
            status=ProgressStatus.IN_PROGRESS,
            description="Testing with special chars: àáâãäå øæ ñ ç",
            metadata={"test_results": {"passed": 15, "failed": 2}, "coverage": 89.5},
            agent_id="agent_with_unicode_αβγ"
        )
        
        await event_store.append(complex_event)
        
        # Retrieve and verify
        events = await event_store.get_events(str(sample_task_id))
        assert len(events) == 1
        
        retrieved_event = events[0]
        assert retrieved_event.progress_type == ProgressType.TESTING
        assert retrieved_event.old_percentage == 75.5
        assert retrieved_event.new_percentage == 85.75
        assert retrieved_event.description == "Testing with special chars: àáâãäå øæ ñ ç"
        assert retrieved_event.agent_id == "agent_with_unicode_αβγ"
        assert retrieved_event.metadata["test_results"]["passed"] == 15
        assert retrieved_event.metadata["coverage"] == 89.5

    @pytest.mark.asyncio
    async def test_replay_events(self, event_store, sample_task_id):
        """Test event replay functionality"""
        # Store events
        events = [
            ProgressUpdated(task_id=sample_task_id, progress_type=ProgressType.IMPLEMENTATION,
                          old_percentage=0.0, new_percentage=30.0, status=ProgressStatus.IN_PROGRESS),
            ProgressUpdated(task_id=sample_task_id, progress_type=ProgressType.IMPLEMENTATION,
                          old_percentage=30.0, new_percentage=60.0, status=ProgressStatus.IN_PROGRESS),
            ProgressMilestoneReached(task_id=sample_task_id, milestone_name="Halfway",
                                   milestone_percentage=50.0, current_progress=60.0)
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Replay events
        replayed_events = []
        
        async def handler(event):
            replayed_events.append(event)
        
        await event_store.replay_events(str(sample_task_id), handler)
        
        assert len(replayed_events) == 3
        assert isinstance(replayed_events[0], ProgressUpdated)
        assert isinstance(replayed_events[1], ProgressUpdated)
        assert isinstance(replayed_events[2], ProgressMilestoneReached)

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, event_store, sample_task_id):
        """Test cleanup of old events"""
        now = datetime.now(timezone.utc)
        
        # Create old and new events
        old_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=25.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=now - timedelta(days=100)  # Very old
        )
        
        new_event = ProgressUpdated(
            task_id=sample_task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=25.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS,
            timestamp=now - timedelta(days=1)  # Recent
        )
        
        await event_store.append(old_event)
        await event_store.append(new_event)
        
        # Verify both events exist
        all_events = await event_store.get_events(str(sample_task_id))
        assert len(all_events) == 2
        
        # Cleanup events older than 90 days
        cleaned_count = await event_store.cleanup_old_events(days=90)
        assert cleaned_count == 1
        
        # Verify only new event remains
        remaining_events = await event_store.get_events(str(sample_task_id))
        assert len(remaining_events) == 1
        assert remaining_events[0].new_percentage == 50.0

    @pytest.mark.asyncio
    async def test_get_event_statistics(self, event_store):
        """Test event statistics generation"""
        task1 = TaskId(str(uuid4()))
        task2 = TaskId(str(uuid4()))
        
        # Create events for multiple tasks
        events = [
            ProgressUpdated(task_id=task1, progress_type=ProgressType.IMPLEMENTATION,
                          old_percentage=0.0, new_percentage=30.0, status=ProgressStatus.IN_PROGRESS),
            ProgressUpdated(task_id=task1, progress_type=ProgressType.IMPLEMENTATION,
                          old_percentage=30.0, new_percentage=60.0, status=ProgressStatus.IN_PROGRESS),
            ProgressMilestoneReached(task_id=task1, milestone_name="Halfway",
                                   milestone_percentage=50.0, current_progress=60.0),
            ProgressStalled(task_id=task2, last_update_timestamp=datetime.now(timezone.utc),
                          stall_duration_hours=1, blockers=["Blocked"])
        ]
        
        for event in events:
            await event_store.append(event)
        
        # Get statistics
        stats = await event_store.get_event_statistics()
        
        assert stats["total_events"] == 4
        assert stats["total_tasks"] == 2
        assert stats["events_by_type"]["ProgressUpdated"] == 2
        assert stats["events_by_type"]["ProgressMilestoneReached"] == 1
        assert stats["events_by_type"]["ProgressStalled"] == 1
        
        # Check active tasks (should include tasks with recent events)
        assert len(stats["active_tasks"]) >= 2
        
        # Check stalled tasks
        assert str(task2) in stats["stalled_tasks"]

    @pytest.mark.asyncio
    async def test_concurrent_event_appending(self, event_store, sample_task_id):
        """Test concurrent event appending with SQLite locking"""
        async def append_events(event_store, task_id, start_idx, count):
            """Helper to append events concurrently"""
            for i in range(start_idx, start_idx + count):
                event = ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=float(i),
                    new_percentage=float(i + 1),
                    status=ProgressStatus.IN_PROGRESS,
                    description=f"Progress update {i}"
                )
                await event_store.append(event)
        
        # Run concurrent append operations
        tasks = []
        for i in range(3):  # 3 concurrent threads
            task = append_events(event_store, sample_task_id, i * 10, 5)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify all events were stored
        events = await event_store.get_events(str(sample_task_id))
        assert len(events) == 15  # 3 threads * 5 events each
        
        # Verify no data corruption
        descriptions = [e.description for e in events]
        assert len(set(descriptions)) == 15  # All unique

    def test_event_store_error_handling(self, temp_db):
        """Test error handling for database issues"""
        store = SQLiteProgressEventStore(db_path=temp_db)
        
        # Remove database file to cause error
        os.unlink(temp_db)
        
        # Attempting to append should handle the error gracefully
        event = ProgressUpdated(
            task_id=TaskId(str(uuid4())),
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=25.0,
            status=ProgressStatus.IN_PROGRESS
        )
        
        # This should raise an exception but not crash the application
        with pytest.raises(Exception):
            asyncio.run(store.append(event))

    def test_invalid_event_deserialization(self, event_store):
        """Test handling of corrupted event data"""
        # Insert corrupted event data directly into database
        corrupted_data = '{"invalid": "json", "missing_fields": true'
        
        with event_store._get_connection() as conn:
            conn.execute("""
                INSERT INTO progress_events 
                (event_id, aggregate_id, event_type, event_data, event_version, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid4()),
                str(uuid4()),
                "ProgressUpdated",
                corrupted_data,
                1,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
        
        # Event store should handle corrupted data gracefully
        task_id = str(uuid4())
        events = asyncio.run(event_store.get_events(task_id))
        # Should return empty list for unknown task, not crash
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_performance_bulk_operations(self, event_store, sample_task_id):
        """Test performance of bulk event operations"""
        import time
        
        # Test bulk insert performance
        events = []
        for i in range(100):
            event = ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=float(i),
                new_percentage=float(i + 1),
                status=ProgressStatus.IN_PROGRESS,
                description=f"Bulk event {i}"
            )
            events.append(event)
        
        # Measure insert time
        start_time = time.time()
        for event in events:
            await event_store.append(event)
        insert_time = time.time() - start_time
        
        # Should complete bulk insert reasonably quickly
        assert insert_time < 5.0  # 5 seconds for 100 events
        
        # Measure retrieval time
        start_time = time.time()
        retrieved_events = await event_store.get_events(str(sample_task_id))
        retrieval_time = time.time() - start_time
        
        assert len(retrieved_events) == 100
        assert retrieval_time < 1.0  # 1 second for retrieval
        
        # Test summary generation performance
        start_time = time.time()
        summary = await event_store.get_progress_summary(str(sample_task_id))
        summary_time = time.time() - start_time
        
        assert summary_time < 1.0  # 1 second for summary generation

    def test_database_schema_integrity(self, event_store):
        """Test database schema integrity and constraints"""
        # Test table structure
        with event_store._get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(progress_events)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'event_id': 'TEXT',
                'aggregate_id': 'TEXT',
                'event_type': 'TEXT',
                'event_data': 'TEXT',
                'event_version': 'INTEGER',
                'occurred_at': 'TIMESTAMP',
                'metadata': 'TEXT'
            }
            
            for col_name, col_type in expected_columns.items():
                assert col_name in columns
                assert col_type in columns[col_name]
        
        # Test unique constraint on event_id
        with event_store._get_connection() as conn:
            event_id = str(uuid4())
            
            # First insert should succeed
            conn.execute("""
                INSERT INTO progress_events 
                (event_id, aggregate_id, event_type, event_data, event_version)
                VALUES (?, ?, ?, ?, ?)
            """, (event_id, str(uuid4()), "ProgressUpdated", "{}", 1))
            
            # Second insert with same event_id should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO progress_events 
                    (event_id, aggregate_id, event_type, event_data, event_version)
                    VALUES (?, ?, ?, ?, ?)
                """, (event_id, str(uuid4()), "ProgressUpdated", "{}", 1))

    @pytest.mark.asyncio
    async def test_event_ordering_consistency(self, event_store, sample_task_id):
        """Test that events are retrieved in correct chronological order"""
        now = datetime.now(timezone.utc)
        
        # Create events with specific timestamps (out of order insertion)
        events = [
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=50.0,
                new_percentage=75.0,
                status=ProgressStatus.IN_PROGRESS,
                timestamp=now + timedelta(minutes=2)  # Third chronologically
            ),
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS,
                timestamp=now  # First chronologically
            ),
            ProgressUpdated(
                task_id=sample_task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=25.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                timestamp=now + timedelta(minutes=1)  # Second chronologically
            )
        ]
        
        # Insert events in random order
        for event in events:
            await event_store.append(event)
        
        # Retrieve events
        retrieved_events = await event_store.get_events(str(sample_task_id))
        
        # Verify chronological order
        assert len(retrieved_events) == 3
        assert retrieved_events[0].old_percentage == 0.0  # First event
        assert retrieved_events[1].old_percentage == 25.0  # Second event
        assert retrieved_events[2].old_percentage == 50.0  # Third event
        
        # Verify timestamps are in order
        timestamps = [event.timestamp for event in retrieved_events]
        assert timestamps == sorted(timestamps)


class TestEventStoreIntegration:
    """Integration tests for event store with other components"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for integration testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store for integration testing"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_event_store_with_task_aggregate(self, event_store):
        """Test event store integration with task aggregate reconstruction"""
        task_id = TaskId(str(uuid4()))
        
        # Simulate task lifecycle events
        lifecycle_events = [
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED,
                description="Design phase completed"
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
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation in progress"
            ),
            ProgressMilestoneReached(
                task_id=task_id,
                milestone_name="Half Way",
                milestone_percentage=50.0,
                current_progress=50.0
            )
        ]
        
        # Store all events
        for event in lifecycle_events:
            await event_store.append(event)
        
        # Reconstruct task state from events
        events = await event_store.get_events(str(task_id))
        
        # Verify complete lifecycle captured
        assert len(events) == 4
        
        # Verify design completion
        design_events = [e for e in events if hasattr(e, 'progress_type') and e.progress_type == ProgressType.DESIGN]
        assert len(design_events) >= 1
        assert any(e.status == ProgressStatus.COMPLETED for e in design_events if hasattr(e, 'status'))
        
        # Verify implementation progress
        impl_events = [e for e in events if hasattr(e, 'progress_type') and e.progress_type == ProgressType.IMPLEMENTATION]
        assert len(impl_events) >= 1
        assert any(e.new_percentage == 50.0 for e in impl_events if hasattr(e, 'new_percentage'))
        
        # Verify milestone reached
        milestone_events = [e for e in events if isinstance(e, ProgressMilestoneReached)]
        assert len(milestone_events) == 1
        assert milestone_events[0].milestone_name == "Half Way"

    @pytest.mark.asyncio 
    async def test_event_sourcing_consistency(self, event_store):
        """Test event sourcing consistency across multiple task aggregates"""
        # Create multiple tasks with overlapping events
        tasks = [TaskId(str(uuid4())) for _ in range(3)]
        
        # Create events for each task
        all_events = []
        for i, task_id in enumerate(tasks):
            task_events = [
                ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=0.0,
                    new_percentage=33.0 * (i + 1),
                    status=ProgressStatus.IN_PROGRESS,
                    description=f"Task {i} progress"
                ),
                ProgressMilestoneReached(
                    task_id=task_id,
                    milestone_name=f"Task {i} Milestone",
                    milestone_percentage=25.0,
                    current_progress=33.0 * (i + 1)
                )
            ]
            all_events.extend(task_events)
        
        # Store all events
        for event in all_events:
            await event_store.append(event)
        
        # Verify each task's events are isolated
        for i, task_id in enumerate(tasks):
            task_events = await event_store.get_events(str(task_id))
            assert len(task_events) == 2
            
            # Verify progress events
            progress_events = [e for e in task_events if isinstance(e, ProgressUpdated)]
            assert len(progress_events) == 1
            assert progress_events[0].new_percentage == 33.0 * (i + 1)
            
            # Verify milestone events
            milestone_events = [e for e in task_events if isinstance(e, ProgressMilestoneReached)]
            assert len(milestone_events) == 1
            assert milestone_events[0].milestone_name == f"Task {i} Milestone"
        
        # Verify global statistics
        stats = await event_store.get_event_statistics()
        assert stats["total_events"] == 6  # 2 events per task * 3 tasks
        assert stats["total_tasks"] == 3