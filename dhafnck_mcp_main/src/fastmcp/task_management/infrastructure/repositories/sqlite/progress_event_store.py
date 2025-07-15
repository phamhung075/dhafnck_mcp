"""SQLite Progress Event Store Implementation

This module provides event sourcing capabilities for progress tracking,
storing all progress-related events for audit, replay, and analysis using SQLite.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Type
from uuid import uuid4

from ....domain.events.progress_events import (
    ProgressEvent, ProgressUpdated, ProgressMilestoneReached,
    ProgressStalled, SubtaskProgressAggregated, ProgressTypeCompleted,
    ProgressBlocked, ProgressUnblocked, ProgressSnapshotCreated
)
from ....domain.value_objects.progress import ProgressType, ProgressStatus
from ....domain.value_objects.task_id import TaskId
from .base_repository import SQLiteBaseRepository

logger = logging.getLogger(__name__)


class SQLiteProgressEventStore(SQLiteBaseRepository):
    """SQLite-based event store for progress tracking events."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite progress event store.
        
        Args:
            db_path: Path to SQLite database file (optional)
        """
        super().__init__(db_path=db_path)
        
        # Ensure progress events table exists
        self._create_table()
        
        # Event type mapping for deserialization
        self._event_types = {
            "ProgressUpdated": ProgressUpdated,
            "ProgressMilestoneReached": ProgressMilestoneReached,
            "ProgressStalled": ProgressStalled,
            "SubtaskProgressAggregated": SubtaskProgressAggregated,
            "ProgressTypeCompleted": ProgressTypeCompleted,
            "ProgressBlocked": ProgressBlocked,
            "ProgressUnblocked": ProgressUnblocked,
            "ProgressSnapshotCreated": ProgressSnapshotCreated
        }
    
    def _create_table(self) -> None:
        """Create the progress events table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS progress_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    event_version INTEGER NOT NULL,
                    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_progress_events_aggregate 
                ON progress_events(aggregate_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_progress_events_type 
                ON progress_events(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_progress_events_occurred_at 
                ON progress_events(occurred_at)
            """)
    
    async def append(self, event: ProgressEvent) -> None:
        """
        Append a progress event to the store.
        
        Args:
            event: Progress event to store
        """
        event_data = event.to_dict()
        event_type = type(event).__name__
        
        # Convert event to JSON for storage
        event_json = json.dumps(event_data)
        
        # Generate unique event ID if not present
        event_id = getattr(event, 'event_id', str(uuid4()))
        
        query = """
            INSERT INTO progress_events 
            (event_id, aggregate_id, event_type, event_data, event_version, occurred_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            event_id,
            str(event.task_id),
            event_type,
            event_json,
            1,  # event_version
            event.timestamp.isoformat(),
            None  # metadata
        )
        
        try:
            self._execute_insert(query, params)
            logger.debug(f"Appended event {event_id} for task {event.task_id}")
        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            raise
    
    async def get_events(self, 
                        task_id: str,
                        event_type: Optional[Type[ProgressEvent]] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[ProgressEvent]:
        """
        Get events for a task with optional filtering.
        
        Args:
            task_id: Task ID to get events for
            event_type: Optional filter by event type
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of progress events
        """
        query = """
            SELECT event_id, aggregate_id, event_type, event_data, event_version, occurred_at, metadata
            FROM progress_events 
            WHERE aggregate_id = ?
        """
        params = [task_id]
        
        # Add event type filter
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.__name__)
        
        # Add date filters
        if start_date:
            query += " AND occurred_at >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND occurred_at <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY occurred_at ASC"
        
        try:
            rows = self._execute_query(query, tuple(params))
            events = []
            
            for row in rows:
                event = self._deserialize_event(dict(row))
                if event:
                    events.append(event)
            
            return events
        except Exception as e:
            logger.error(f"Failed to get events for task {task_id}: {e}")
            return []
    
    async def get_progress_timeline(self,
                                  task_id: str,
                                  hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get progress timeline for visualization.
        
        Args:
            task_id: Task ID
            hours: Number of hours to look back
            
        Returns:
            Timeline data for visualization
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = await self.get_events(task_id, start_date=cutoff)
        
        timeline = []
        for event in events:
            if isinstance(event, ProgressUpdated):
                timeline.append({
                    "timestamp": event.timestamp.isoformat(),
                    "type": "progress_update",
                    "progress_type": event.progress_type.value,
                    "percentage": event.new_percentage,
                    "delta": event.progress_delta,
                    "description": event.description,
                    "agent": event.agent_id
                })
            elif isinstance(event, ProgressMilestoneReached):
                timeline.append({
                    "timestamp": event.timestamp.isoformat(),
                    "type": "milestone",
                    "milestone": event.milestone_name,
                    "percentage": event.milestone_percentage
                })
            elif isinstance(event, ProgressStalled):
                timeline.append({
                    "timestamp": event.timestamp.isoformat(),
                    "type": "stalled",
                    "duration_hours": event.stall_duration_hours,
                    "blockers": event.blockers
                })
        
        return sorted(timeline, key=lambda x: x["timestamp"])
    
    async def get_progress_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get progress summary from events.
        
        Args:
            task_id: Task ID
            
        Returns:
            Summary of progress from events
        """
        events = await self.get_events(task_id)
        
        summary = {
            "task_id": task_id,
            "total_events": len(events),
            "progress_by_type": {},
            "milestones_reached": [],
            "stall_periods": [],
            "last_update": None,
            "total_updates": 0
        }
        
        # Process events
        for event in events:
            if isinstance(event, ProgressUpdated):
                summary["total_updates"] += 1
                summary["last_update"] = event.timestamp.isoformat()
                
                # Track progress by type
                progress_type = event.progress_type.value
                if progress_type not in summary["progress_by_type"]:
                    summary["progress_by_type"][progress_type] = {
                        "current": 0,
                        "updates": 0,
                        "history": []
                    }
                
                type_data = summary["progress_by_type"][progress_type]
                type_data["current"] = event.new_percentage
                type_data["updates"] += 1
                type_data["history"].append({
                    "timestamp": event.timestamp.isoformat(),
                    "percentage": event.new_percentage
                })
            
            elif isinstance(event, ProgressMilestoneReached):
                summary["milestones_reached"].append({
                    "name": event.milestone_name,
                    "percentage": event.milestone_percentage,
                    "timestamp": event.timestamp.isoformat()
                })
            
            elif isinstance(event, ProgressStalled):
                summary["stall_periods"].append({
                    "start": event.last_update_timestamp.isoformat(),
                    "duration_hours": event.stall_duration_hours,
                    "blockers": event.blockers
                })
        
        return summary
    
    async def replay_events(self,
                          task_id: str,
                          handler_func: Any,
                          start_date: Optional[datetime] = None) -> None:
        """
        Replay events for a task through a handler function.
        
        Args:
            task_id: Task ID
            handler_func: Async function to handle each event
            start_date: Optional start date for replay
        """
        events = await self.get_events(task_id, start_date=start_date)
        
        for event in events:
            try:
                await handler_func(event)
            except Exception as e:
                logger.error(f"Error replaying event {getattr(event, 'event_id', 'unknown')}: {e}")
    
    async def cleanup_old_events(self, days: int = 90) -> int:
        """
        Clean up events older than specified days.
        
        Args:
            days: Number of days to keep events
            
        Returns:
            Number of events cleaned up
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = "DELETE FROM progress_events WHERE occurred_at < ?"
        params = (cutoff.isoformat(),)
        
        try:
            affected_rows = self._execute_update(query, params)
            logger.info(f"Cleaned up {affected_rows} progress events older than {days} days")
            return affected_rows
        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")
            return 0
    
    def _deserialize_event(self, data: Dict[str, Any]) -> Optional[ProgressEvent]:
        """Deserialize event from dictionary."""
        event_type = data.get("event_type")
        if event_type not in self._event_types:
            logger.warning(f"Unknown event type: {event_type}")
            return None
        
        event_class = self._event_types[event_type]
        
        try:
            # Parse the stored event data
            event_data = json.loads(data["event_data"])
            
            # Remove event_type from data as it's not a field in the event class
            event_data.pop("event_type", None)
            
            # Convert ISO timestamps back to datetime
            if "timestamp" in event_data:
                event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
            
            # Convert task_id back to TaskId object if it's a string
            if "task_id" in event_data and isinstance(event_data["task_id"], str):
                event_data["task_id"] = TaskId(event_data["task_id"])
            
            # Handle specific event type conversions
            if event_type == "ProgressUpdated":
                if "progress_type" in event_data:
                    event_data["progress_type"] = ProgressType(event_data["progress_type"])
                if "status" in event_data:
                    event_data["status"] = ProgressStatus(event_data["status"])
                # Remove progress_delta as it's a calculated property, not a field
                event_data.pop("progress_delta", None)
            elif event_type == "ProgressTypeCompleted":
                if "progress_type" in event_data:
                    event_data["progress_type"] = ProgressType(event_data["progress_type"])
                if "completion_timestamp" in event_data:
                    event_data["completion_timestamp"] = datetime.fromisoformat(event_data["completion_timestamp"])
            
            # Handle other timestamp fields
            if "last_update_timestamp" in event_data:
                event_data["last_update_timestamp"] = datetime.fromisoformat(event_data["last_update_timestamp"])
            
            return event_class(**event_data)
        except Exception as e:
            logger.error(f"Failed to deserialize event: {e}")
            return None
    
    async def get_event_statistics(self) -> Dict[str, Any]:
        """Get overall event statistics."""
        stats = {
            "total_tasks": 0,
            "total_events": 0,
            "events_by_type": {},
            "active_tasks": [],
            "stalled_tasks": []
        }
        
        # Get total events and event type counts
        try:
            # Get total counts first
            count_query = """
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT aggregate_id) as total_tasks
                FROM progress_events
            """
            count_row = self._execute_query(count_query, fetch_one=True)
            if count_row:
                stats["total_events"] = count_row["total_events"]
                stats["total_tasks"] = count_row["total_tasks"]
            
            # Get event type counts
            type_query = """
                SELECT event_type, COUNT(*) as type_count
                FROM progress_events
                GROUP BY event_type
            """
            type_rows = self._execute_query(type_query)
            for row in type_rows:
                stats["events_by_type"][row["event_type"]] = row["type_count"]
            
            # Get active tasks (tasks with events in last 7 days)
            active_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            active_query = """
                SELECT DISTINCT aggregate_id 
                FROM progress_events 
                WHERE occurred_at >= ?
            """
            active_rows = self._execute_query(active_query, (active_cutoff.isoformat(),))
            stats["active_tasks"] = [row["aggregate_id"] for row in active_rows]
            
            # Get tasks with stall events
            stall_query = """
                SELECT DISTINCT aggregate_id 
                FROM progress_events 
                WHERE event_type = 'ProgressStalled'
            """
            stall_rows = self._execute_query(stall_query)
            stats["stalled_tasks"] = [row["aggregate_id"] for row in stall_rows]
            
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
        
        return stats