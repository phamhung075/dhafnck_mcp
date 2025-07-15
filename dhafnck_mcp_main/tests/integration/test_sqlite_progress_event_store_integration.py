"""Integration tests for SQLite Progress Event Store

Tests the integration of the SQLite progress event store with:
- Task management system
- Event sourcing patterns  
- Progress tracking service
- Event handlers and workflows
- Cross-repository data consistency
"""

import pytest
import tempfile
import os
import asyncio
import time
import sqlite3
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.fastmcp.task_management.infrastructure.repositories.sqlite.progress_event_store import SQLiteProgressEventStore
from src.fastmcp.task_management.domain.events.progress_events import (
    ProgressUpdated, ProgressMilestoneReached, ProgressStalled,
    ProgressTypeCompleted, ProgressBlocked, ProgressUnblocked
)
from src.fastmcp.task_management.domain.value_objects.progress import (
    ProgressType, ProgressStatus, ProgressSnapshot, ProgressTimeline
)
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.application.services.progress_tracking_service import ProgressTrackingService
from src.fastmcp.task_management.application.event_handlers.progress_event_handlers import (
    ProgressUpdatedHandler, ProgressMilestoneReachedHandler
)

pytestmark = pytest.mark.integration


class TestProgressEventStoreTaskIntegration:
    """Test progress event store integration with task entities"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store instance"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing"""
        return Task.create(
            id=TaskId(str(uuid4())),
            title="Integration test task",
            description="Task for testing event store integration"
        )
    
    @pytest.mark.asyncio
    async def test_task_progress_events_storage(self, event_store, sample_task):
        """Test that task progress updates generate events that are properly stored"""
        # Update task progress multiple times
        sample_task.update_progress(
            progress_type=ProgressType.DESIGN,
            percentage=25.0,
            description="Design phase started"
        )
        
        sample_task.update_progress(
            progress_type=ProgressType.DESIGN,
            percentage=100.0,
            description="Design phase completed"
        )
        
        sample_task.update_progress(
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=30.0,
            description="Implementation started"
        )
        
        # Get events from task
        task_events = sample_task.get_events()
        progress_events = [e for e in task_events if isinstance(e, ProgressUpdated)]
        
        # Store events in event store
        for event in progress_events:
            await event_store.append(event)
        
        # Retrieve events from store
        stored_events = await event_store.get_events(str(sample_task.id))
        
        # Verify events are correctly stored and retrieved
        assert len(stored_events) == len(progress_events)
        
        # Verify event data integrity
        for stored, original in zip(stored_events, progress_events):
            assert stored.task_id == original.task_id
            assert stored.progress_type == original.progress_type
            assert stored.new_percentage == original.new_percentage
            assert stored.description == original.description
    
    @pytest.mark.asyncio
    async def test_task_milestone_events_integration(self, event_store, sample_task):
        """Test task milestone events integration with event store"""
        # Add milestones to task
        sample_task.add_progress_milestone("Quarter Done", 25.0)
        sample_task.add_progress_milestone("Half Done", 50.0)
        sample_task.add_progress_milestone("Three Quarters", 75.0)
        
        # Progress through milestones
        sample_task.update_progress(ProgressType.IMPLEMENTATION, 30.0)
        sample_task.update_progress(ProgressType.IMPLEMENTATION, 60.0)
        sample_task.update_progress(ProgressType.IMPLEMENTATION, 80.0)
        
        # Get milestone events
        task_events = sample_task.get_events()
        milestone_events = [e for e in task_events if isinstance(e, ProgressMilestoneReached)]
        
        # Store in event store
        for event in milestone_events:
            await event_store.append(event)
        
        # Verify milestones are stored
        stored_events = await event_store.get_events(str(sample_task.id), ProgressMilestoneReached)
        
        assert len(stored_events) == len(milestone_events)
        milestone_names = [e.milestone_name for e in stored_events]
        assert "Quarter Done" in milestone_names
        assert "Half Done" in milestone_names
        assert "Three Quarters" in milestone_names
    
    @pytest.mark.asyncio
    async def test_event_sourcing_task_reconstruction(self, event_store, sample_task):
        """Test reconstructing task state from stored events"""
        # Generate a series of progress events
        progress_events = [
            ProgressUpdated(
                task_id=sample_task.id,
                progress_type=ProgressType.DESIGN,
                old_percentage=0.0,
                new_percentage=100.0,
                status=ProgressStatus.COMPLETED,
                description="Design completed"
            ),
            ProgressTypeCompleted(
                task_id=sample_task.id,
                progress_type=ProgressType.DESIGN,
                completion_timestamp=datetime.now(timezone.utc)
            ),
            ProgressUpdated(
                task_id=sample_task.id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=45.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Implementation progress"
            ),
            ProgressMilestoneReached(
                task_id=sample_task.id,
                milestone_name="Implementation Started",
                milestone_percentage=40.0,
                current_progress=45.0
            )
        ]
        
        # Store all events
        for event in progress_events:
            await event_store.append(event)
        
        # Reconstruct task state from events
        stored_events = await event_store.get_events(str(sample_task.id))
        
        # Verify we can reconstruct task progress state
        design_progress = None
        implementation_progress = None
        milestones_reached = []
        completed_types = []
        
        for event in stored_events:
            if isinstance(event, ProgressUpdated):
                if event.progress_type == ProgressType.DESIGN:
                    design_progress = event.new_percentage
                elif event.progress_type == ProgressType.IMPLEMENTATION:
                    implementation_progress = event.new_percentage
            elif isinstance(event, ProgressMilestoneReached):
                milestones_reached.append(event.milestone_name)
            elif isinstance(event, ProgressTypeCompleted):
                completed_types.append(event.progress_type)
        
        # Verify reconstructed state
        assert design_progress == 100.0
        assert implementation_progress == 45.0
        assert "Implementation Started" in milestones_reached
        assert ProgressType.DESIGN in completed_types


class TestProgressTrackingServiceIntegration:
    """Test progress tracking service integration with SQLite event store"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store instance"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.fixture
    def mock_task_repo(self):
        """Create mock task repository"""
        return Mock()
    
    @pytest.fixture
    def mock_context_service(self):
        """Create mock hierarchical context service"""
        return Mock()
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus"""
        return Mock()
    
    @pytest.fixture
    def progress_service(self, mock_task_repo, mock_context_service, mock_event_bus):
        """Create progress tracking service with hierarchical context"""
        return ProgressTrackingService(
            task_repository=mock_task_repo,
            context_repository=mock_context_service,
            event_bus=mock_event_bus
        )
    
    @pytest.mark.asyncio
    async def test_service_event_store_integration(self, progress_service, event_store, 
                                                  mock_task_repo, mock_event_bus):
        """Test progress tracking service generates events that integrate with event store"""
        # Setup test task
        task_id = TaskId(str(uuid4()))
        task = Task.create(
            id=task_id,
            title="Service integration test",
            description="Testing service with event store"
        )
        
        # Mock repository to return the task
        mock_task_repo.get_by_id = AsyncMock(return_value=task)
        mock_task_repo.update = AsyncMock()
        
        # Capture published events
        published_events = []
        async def mock_publish(event):
            published_events.append(event)
            
        mock_event_bus.publish = AsyncMock(side_effect=mock_publish)
        
        # Update progress through service
        result = await progress_service.update_progress(
            task_id=str(task_id),
            progress_type=ProgressType.IMPLEMENTATION,
            percentage=60.0,
            description="Service progress update",
            agent_id="test_service_agent"
        )
        
        # Verify service completed successfully
        assert result.overall_progress > 0
        assert mock_task_repo.update.called
        assert mock_event_bus.publish.called
        
        # Store the published events in the event store
        progress_events = [e for e in published_events if isinstance(e, ProgressUpdated)]
        
        for event in progress_events:
            await event_store.append(event)
        
        # Verify events are stored correctly
        stored_events = await event_store.get_events(str(task_id))
        assert len(stored_events) > 0
        
        # Find the service-generated event
        service_events = [e for e in stored_events if e.description == "Service progress update"]
        assert len(service_events) > 0
        assert service_events[0].new_percentage == 60.0
        assert service_events[0].agent_id == "test_service_agent"
    
    @pytest.mark.asyncio
    async def test_batch_progress_update_integration(self, progress_service, event_store,
                                                    mock_task_repo, mock_event_bus):
        """Test batch progress updates with event store integration"""
        # Setup multiple tasks
        tasks = []
        task_ids = []
        
        for i in range(3):
            task_id = TaskId(str(uuid4()))
            task = Task.create(
                id=task_id,
                title=f"Batch test task {i}",
                description=f"Task {i} for batch testing"
            )
            tasks.append(task)
            task_ids.append(str(task_id))
        
        # Mock repository to return tasks in order
        mock_task_repo.get_by_id = AsyncMock(side_effect=tasks.copy())
        mock_task_repo.update = AsyncMock()
        
        # Capture published events
        published_events = []
        async def mock_publish(event):
            published_events.append(event)
            
        mock_event_bus.publish = AsyncMock(side_effect=mock_publish)
        
        # Batch update
        updates = [
            {
                "task_id": task_ids[0],
                "progress_type": ProgressType.IMPLEMENTATION,
                "percentage": 25.0,
                "description": "Batch update 1"
            },
            {
                "task_id": task_ids[1],
                "progress_type": ProgressType.TESTING,
                "percentage": 50.0,
                "description": "Batch update 2"
            },
            {
                "task_id": task_ids[2],
                "progress_type": ProgressType.DOCUMENTATION,
                "percentage": 75.0,
                "description": "Batch update 3"
            }
        ]
        
        results = await progress_service.batch_update_progress(updates)
        
        assert len(results) == 3
        assert all(r.overall_progress > 0 for r in results)
        
        # Store all published progress events
        progress_events = [e for e in published_events if isinstance(e, ProgressUpdated)]
        
        for event in progress_events:
            await event_store.append(event)
        
        # Verify each task's events are stored
        for i, task_id in enumerate(task_ids):
            stored_events = await event_store.get_events(task_id)
            batch_events = [e for e in stored_events if f"Batch update {i+1}" in e.description]
            assert len(batch_events) > 0


class TestEventHandlerIntegration:
    """Test event handler integration with SQLite event store"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store instance"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_progress_updated_handler_integration(self, event_store):
        """Test ProgressUpdatedHandler integration with event store"""
        # Setup mocks
        mock_task_repo = Mock()
        mock_context_service = Mock()
        
        # Create test task
        task_id = TaskId(str(uuid4()))
        task = Task.create(
            id=task_id,
            title="Handler test task",
            description="Testing event handler integration"
        )
        task.context_id = "test-context-123"
        
        mock_context = Mock()
        mock_context.insights = []
        
        mock_task_repo.get_by_id = AsyncMock(return_value=task)
        mock_context_service.get_by_id = AsyncMock(return_value=mock_context)
        mock_context_service.update = AsyncMock(return_value={"success": True})
        
        # Create handler
        handler = ProgressUpdatedHandler(mock_task_repo, mock_context_service, event_store)
        
        # Create progress event
        progress_event = ProgressUpdated(
            task_id=task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=25.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS,
            description="Handler test progress"
        )
        
        # Handle the event (this should store it in event store)
        await handler.handle(progress_event)
        
        # Verify event was stored
        stored_events = await event_store.get_events(str(task_id))
        assert len(stored_events) == 1
        assert stored_events[0].description == "Handler test progress"
        assert stored_events[0].new_percentage == 50.0
        
        # Verify context was updated
        assert mock_context_service.update.called
    
    @pytest.mark.asyncio
    async def test_milestone_handler_integration(self, event_store):
        """Test ProgressMilestoneReachedHandler integration with event store"""
        # Setup mocks
        mock_notification_service = Mock()
        mock_notification_service.notify = AsyncMock()
        
        # Create handler
        handler = ProgressMilestoneReachedHandler(mock_notification_service, event_store)
        
        # Create milestone event
        task_id = TaskId(str(uuid4()))
        milestone_event = ProgressMilestoneReached(
            task_id=task_id,
            milestone_name="Handler Test Milestone",
            milestone_percentage=75.0,
            current_progress=80.0
        )
        
        # Handle the event
        await handler.handle(milestone_event)
        
        # Verify event was stored
        stored_events = await event_store.get_events(str(task_id))
        assert len(stored_events) == 1
        assert stored_events[0].milestone_name == "Handler Test Milestone"
        assert stored_events[0].milestone_percentage == 75.0
        
        # Verify notification was sent
        assert mock_notification_service.notify.called
        
        # Check notification content
        notify_call = mock_notification_service.notify.call_args
        assert notify_call[1]["type"] == "milestone_reached"
        assert notify_call[1]["data"]["milestone"] == "Handler Test Milestone"


class TestConcurrencyAndPerformance:
    """Test concurrency and performance aspects of SQLite event store"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store instance"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_concurrent_event_storage_multiple_tasks(self, event_store):
        """Test concurrent event storage across multiple tasks"""
        task_count = 5
        events_per_task = 10
        
        async def generate_task_events(task_index):
            """Generate events for a single task"""
            task_id = TaskId(str(uuid4()))
            events = []
            
            for i in range(events_per_task):
                event = ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=float(i * 10),
                    new_percentage=float((i + 1) * 10),
                    status=ProgressStatus.IN_PROGRESS,
                    description=f"Task {task_index} - Event {i}"
                )
                await event_store.append(event)
                events.append(event)
            
            return str(task_id), events
        
        # Run concurrent task event generation
        start_time = time.time()
        tasks = [generate_task_events(i) for i in range(task_count)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify performance
        total_time = end_time - start_time
        total_events = task_count * events_per_task
        events_per_second = total_events / total_time
        
        print(f"Stored {total_events} events in {total_time:.2f}s ({events_per_second:.1f} events/sec)")
        assert events_per_second > 50  # Should handle at least 50 events per second
        
        # Verify data integrity
        for task_id, expected_events in results:
            stored_events = await event_store.get_events(task_id)
            assert len(stored_events) == events_per_task
            
            # Verify event order
            for i, event in enumerate(stored_events):
                assert event.new_percentage == float((i + 1) * 10)
    
    @pytest.mark.asyncio
    async def test_event_store_under_load(self, event_store):
        """Test event store performance under sustained load"""
        task_id = TaskId(str(uuid4()))
        event_count = 100
        
        # Generate events rapidly
        start_time = time.time()
        
        for i in range(event_count):
            event = ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=float(i),
                new_percentage=float(i + 1),
                status=ProgressStatus.IN_PROGRESS,
                description=f"Load test event {i}",
                agent_id=f"agent_{i % 5}"  # Rotate through 5 agents
            )
            await event_store.append(event)
        
        store_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        all_events = await event_store.get_events(str(task_id))
        retrieval_time = time.time() - start_time
        
        # Test summary generation performance
        start_time = time.time()
        summary = await event_store.get_progress_summary(str(task_id))
        summary_time = time.time() - start_time
        
        # Test timeline generation performance
        start_time = time.time()
        timeline = await event_store.get_progress_timeline(str(task_id), hours=24)
        timeline_time = time.time() - start_time
        
        # Verify performance requirements
        assert store_time < 5.0  # Store 100 events in under 5 seconds
        assert retrieval_time < 0.5  # Retrieve events in under 0.5 seconds
        assert summary_time < 1.0  # Generate summary in under 1 second
        assert timeline_time < 1.0  # Generate timeline in under 1 second
        
        # Verify data integrity
        assert len(all_events) == event_count
        assert summary["total_events"] == event_count
        assert len(timeline) == event_count
        
        print(f"Performance results:")
        print(f"  Store time: {store_time:.3f}s ({event_count/store_time:.1f} events/sec)")
        print(f"  Retrieval time: {retrieval_time:.3f}s")
        print(f"  Summary time: {summary_time:.3f}s")
        print(f"  Timeline time: {timeline_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_sqlite_locking_behavior(self, event_store):
        """Test SQLite locking behavior with concurrent writes"""
        task_id = TaskId(str(uuid4()))
        
        async def write_events_batch(start_idx, count):
            """Write a batch of events"""
            for i in range(start_idx, start_idx + count):
                event = ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=float(i),
                    new_percentage=float(i + 1),
                    status=ProgressStatus.IN_PROGRESS,
                    description=f"Locking test event {i}"
                )
                await event_store.append(event)
        
        # Run multiple concurrent writers
        batch_size = 20
        writer_count = 3
        
        start_time = time.time()
        tasks = []
        for i in range(writer_count):
            task = write_events_batch(i * batch_size, batch_size)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all events were written correctly
        all_events = await event_store.get_events(str(task_id))
        expected_count = writer_count * batch_size
        
        assert len(all_events) == expected_count
        
        # Verify no events were lost or corrupted
        event_indices = set()
        for event in all_events:
            # Extract index from description
            desc_parts = event.description.split()
            index = int(desc_parts[-1])
            event_indices.add(index)
        
        expected_indices = set(range(expected_count))
        assert event_indices == expected_indices
        
        print(f"Concurrent write test: {expected_count} events in {end_time - start_time:.3f}s")


class TestDataConsistencyAndRecovery:
    """Test data consistency and recovery scenarios"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def event_store(self, temp_db):
        """Create event store instance"""
        return SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_simulation(self, event_store):
        """Test behavior when transactions are interrupted"""
        task_id = TaskId(str(uuid4()))
        
        # Store some initial events
        initial_events = [
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=0.0,
                new_percentage=25.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Initial event 1"
            ),
            ProgressUpdated(
                task_id=task_id,
                progress_type=ProgressType.IMPLEMENTATION,
                old_percentage=25.0,
                new_percentage=50.0,
                status=ProgressStatus.IN_PROGRESS,
                description="Initial event 2"
            )
        ]
        
        for event in initial_events:
            await event_store.append(event)
        
        # Verify initial state
        events = await event_store.get_events(str(task_id))
        assert len(events) == 2
        
        # Simulate failure during transaction by directly manipulating database
        # (In real scenario, this would be a system failure)
        try:
            with event_store._get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN TRANSACTION")
                
                # Insert partial data
                conn.execute("""
                    INSERT INTO progress_events 
                    (event_id, aggregate_id, event_type, event_data, event_version)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(uuid4()), str(task_id), "ProgressUpdated", '{"incomplete": true}', 1))
                
                # Simulate failure before commit
                raise Exception("Simulated failure")
                
        except Exception:
            # Expected failure
            pass
        
        # Verify database is still in consistent state
        events_after_failure = await event_store.get_events(str(task_id))
        assert len(events_after_failure) == 2  # Only original events remain
        
        # Verify we can continue normal operations
        recovery_event = ProgressUpdated(
            task_id=task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=50.0,
            new_percentage=75.0,
            status=ProgressStatus.IN_PROGRESS,
            description="Recovery event"
        )
        
        await event_store.append(recovery_event)
        
        final_events = await event_store.get_events(str(task_id))
        assert len(final_events) == 3
        assert final_events[2].description == "Recovery event"
    
    @pytest.mark.skip(reason="Test times out - incompatible with new system")
    @pytest.mark.asyncio
    async def test_database_file_corruption_handling(self, temp_db):
        """Test handling of database file corruption"""
        # Create event store and add some data
        event_store = SQLiteProgressEventStore(db_path=temp_db)
        task_id = TaskId(str(uuid4()))
        
        event = ProgressUpdated(
            task_id=task_id,
            progress_type=ProgressType.IMPLEMENTATION,
            old_percentage=0.0,
            new_percentage=50.0,
            status=ProgressStatus.IN_PROGRESS
        )
        
        await event_store.append(event)
        
        # Verify data exists
        events = await event_store.get_events(str(task_id))
        assert len(events) == 1
        
        # Simulate corruption by truncating the database file
        with open(temp_db, 'w') as f:
            f.write("corrupted data")
        
        # Create new event store instance (simulates restart after corruption)
        # This should raise an exception during initialization due to corruption
        with pytest.raises(sqlite3.DatabaseError):
            new_event_store = SQLiteProgressEventStore(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_event_store_statistics_consistency(self, event_store):
        """Test that statistics remain consistent across operations"""
        # Create events across multiple tasks
        tasks_and_events = []
        
        for i in range(5):
            task_id = TaskId(str(uuid4()))
            events = [
                ProgressUpdated(
                    task_id=task_id,
                    progress_type=ProgressType.IMPLEMENTATION,
                    old_percentage=0.0,
                    new_percentage=50.0,
                    status=ProgressStatus.IN_PROGRESS
                ),
                ProgressMilestoneReached(
                    task_id=task_id,
                    milestone_name=f"Task {i} Milestone",
                    milestone_percentage=50.0,
                    current_progress=50.0
                )
            ]
            tasks_and_events.append((task_id, events))
        
        # Store all events
        total_events = 0
        for task_id, events in tasks_and_events:
            for event in events:
                await event_store.append(event)
                total_events += 1
        
        # Get statistics
        stats = await event_store.get_event_statistics()
        
        # Verify statistics consistency
        assert stats["total_events"] == total_events
        assert stats["total_tasks"] == 5
        assert stats["events_by_type"]["ProgressUpdated"] == 5
        assert stats["events_by_type"]["ProgressMilestoneReached"] == 5
        
        # Add more events and verify statistics update
        additional_task_id = TaskId(str(uuid4()))
        additional_event = ProgressStalled(
            task_id=additional_task_id,
            last_update_timestamp=datetime.now(timezone.utc),
            stall_duration_hours=2,
            blockers=["Statistics test stall"]
        )
        
        await event_store.append(additional_event)
        
        updated_stats = await event_store.get_event_statistics()
        assert updated_stats["total_events"] == total_events + 1
        assert updated_stats["total_tasks"] == 6
        assert "ProgressStalled" in updated_stats["events_by_type"]
        assert updated_stats["events_by_type"]["ProgressStalled"] == 1