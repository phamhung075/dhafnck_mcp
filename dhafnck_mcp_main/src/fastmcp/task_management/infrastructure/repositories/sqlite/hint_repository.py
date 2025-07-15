"""SQLite Hint Repository Implementation"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from ....domain.value_objects.hints import WorkflowHint, HintType, HintPriority
from ....domain.events.hint_events import (
    HintGenerated, HintAccepted, HintDismissed,
    HintFeedbackProvided, HintEffectivenessCalculated
)
from .base_repository import SQLiteBaseRepository

logger = logging.getLogger(__name__)


class SQLiteHintRepository(SQLiteBaseRepository):
    """SQLite-based implementation of hint repository"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite hint repository"""
        super().__init__(db_path=db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create hint-related tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                # Main hints table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hints (
                        id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        type TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        message TEXT NOT NULL,
                        suggested_action TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        context_data TEXT,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                """)
                
                # Hint events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hint_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hint_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL,
                        occurred_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (hint_id) REFERENCES hints(id) ON DELETE CASCADE
                    )
                """)
                
                # Effectiveness scores table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hint_effectiveness_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_rule TEXT NOT NULL,
                        hint_type TEXT NOT NULL,
                        effectiveness_score REAL NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        UNIQUE(source_rule, hint_type)
                    )
                """)
                
                # Improvement suggestions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hint_improvement_suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hint_id TEXT NOT NULL,
                        suggestion TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (hint_id) REFERENCES hints(id) ON DELETE CASCADE
                    )
                """)
                
                # Detected patterns table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hint_detected_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_id TEXT,
                        pattern_name TEXT,
                        pattern_description TEXT,
                        confidence REAL,
                        detected_at TIMESTAMP NOT NULL,
                        affected_tasks TEXT,
                        suggested_rule TEXT,
                        created_at TIMESTAMP NOT NULL
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hints_task_id ON hints(task_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hints_type ON hints(type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hints_expires_at ON hints(expires_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hint_events_hint_id ON hint_events(hint_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hint_events_type ON hint_events(event_type)")
                
                conn.commit()
                logger.info("Hint tables created successfully")
                
        except Exception as e:
            logger.error(f"Error creating hint tables: {e}")
            raise
    
    async def save(self, hint: WorkflowHint) -> None:
        """Save a workflow hint"""
        try:
            query = """
                INSERT OR REPLACE INTO hints (
                    id, task_id, type, priority, message, suggested_action,
                    metadata, context_data, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                str(hint.id),
                str(hint.task_id),
                hint.type.value,
                hint.priority.value,
                hint.message,
                hint.suggested_action,
                json.dumps(hint.metadata.__dict__) if hint.metadata else "{}",
                json.dumps(hint.context_data) if hint.context_data else None,
                hint.expires_at.isoformat() if hint.expires_at else None,
                hint.created_at.isoformat(),
                datetime.now(timezone.utc).isoformat()
            )
            
            self._execute_update(query, params)
            logger.debug(f"Saved hint {hint.id} for task {hint.task_id}")
            
        except Exception as e:
            logger.error(f"Error saving hint: {e}")
            raise
    
    async def get(self, hint_id: UUID) -> Optional[WorkflowHint]:
        """Get a hint by ID"""
        try:
            query = "SELECT * FROM hints WHERE id = ?"
            row = self._execute_query(query, (str(hint_id),), fetch_one=True)
            
            if row:
                return self._row_to_hint(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting hint {hint_id}: {e}")
            raise
    
    async def get_by_task(
        self,
        task_id: UUID,
        hint_types: Optional[List[HintType]] = None,
        include_expired: bool = False
    ) -> List[WorkflowHint]:
        """Get all hints for a task"""
        try:
            query_parts = ["SELECT * FROM hints WHERE task_id = ?"]
            params = [str(task_id)]
            
            # Filter by type if specified
            if hint_types:
                type_placeholders = ",".join(["?" for _ in hint_types])
                query_parts.append(f"AND type IN ({type_placeholders})")
                params.extend([ht.value for ht in hint_types])
            
            # Filter expired unless requested
            if not include_expired:
                query_parts.append("AND (expires_at IS NULL OR expires_at > ?)")
                params.append(datetime.now(timezone.utc).isoformat())
            
            # Sort by priority and creation time
            query_parts.append("""
                ORDER BY 
                    CASE priority 
                        WHEN 'critical' THEN 0 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END, 
                    created_at
            """)
            
            query = " ".join(query_parts)
            rows = self._execute_query(query, tuple(params))
            
            return [self._row_to_hint(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting hints for task {task_id}: {e}")
            raise
    
    async def store_generated_hint(self, event: HintGenerated) -> None:
        """Store a hint generated event"""
        try:
            event_data = {
                "task_id": str(event.task_id),
                "hint_type": event.hint_type.value,
                "priority": event.priority.value,
                "message": event.message,
                "suggested_action": event.suggested_action,
                "source_rule": event.source_rule,
                "confidence": event.confidence
            }
            
            query = """
                INSERT INTO hint_events (hint_id, event_type, event_data, occurred_at)
                VALUES (?, ?, ?, ?)
            """
            
            params = (
                str(event.hint_id),
                "generated",
                json.dumps(event_data),
                event.occurred_at.isoformat()
            )
            
            self._execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error storing hint generated event: {e}")
            raise
    
    async def store_hint_acceptance(self, event: HintAccepted) -> None:
        """Store a hint acceptance event"""
        try:
            event_data = {
                "user_id": event.user_id,
                "action_taken": event.action_taken
            }
            
            query = """
                INSERT INTO hint_events (hint_id, event_type, event_data, occurred_at)
                VALUES (?, ?, ?, ?)
            """
            
            params = (
                str(event.hint_id),
                "accepted",
                json.dumps(event_data),
                event.occurred_at.isoformat()
            )
            
            self._execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error storing hint acceptance event: {e}")
            raise
    
    async def store_hint_dismissal(self, event: HintDismissed) -> None:
        """Store a hint dismissal event"""
        try:
            event_data = {
                "user_id": event.user_id,
                "reason": event.reason
            }
            
            query = """
                INSERT INTO hint_events (hint_id, event_type, event_data, occurred_at)
                VALUES (?, ?, ?, ?)
            """
            
            params = (
                str(event.hint_id),
                "dismissed",
                json.dumps(event_data),
                event.occurred_at.isoformat()
            )
            
            self._execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error storing hint dismissal event: {e}")
            raise
    
    async def store_hint_feedback(self, event: HintFeedbackProvided) -> None:
        """Store hint feedback"""
        try:
            event_data = {
                "user_id": event.user_id,
                "was_helpful": event.was_helpful,
                "feedback_text": event.feedback_text,
                "effectiveness_score": event.effectiveness_score
            }
            
            query = """
                INSERT INTO hint_events (hint_id, event_type, event_data, occurred_at)
                VALUES (?, ?, ?, ?)
            """
            
            params = (
                str(event.hint_id),
                "feedback",
                json.dumps(event_data),
                event.occurred_at.isoformat()
            )
            
            self._execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error storing hint feedback: {e}")
            raise
    
    async def store_effectiveness_score(self, event: HintEffectivenessCalculated) -> None:
        """Store effectiveness score"""
        try:
            query = """
                INSERT OR REPLACE INTO hint_effectiveness_scores 
                (source_rule, hint_type, effectiveness_score, updated_at)
                VALUES (?, ?, ?, ?)
            """
            
            params = (
                event.source_rule,
                event.hint_type.value,
                event.effectiveness_score,
                datetime.now(timezone.utc).isoformat()
            )
            
            self._execute_update(query, params)
            
            logger.info(
                f"Updated effectiveness score for {event.source_rule}:{event.hint_type}: "
                f"{event.effectiveness_score:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error storing effectiveness score: {e}")
            raise
    
    async def get_effectiveness_score(
        self,
        source_rule: str,
        hint_type: HintType
    ) -> Optional[float]:
        """Get effectiveness score for a rule/type combination"""
        try:
            query = """
                SELECT effectiveness_score FROM hint_effectiveness_scores
                WHERE source_rule = ? AND hint_type = ?
            """
            
            row = self._execute_query(
                query, 
                (source_rule, hint_type.value), 
                fetch_one=True
            )
            
            return row["effectiveness_score"] if row else None
            
        except Exception as e:
            logger.error(f"Error getting effectiveness score: {e}")
            raise
    
    async def store_improvement_suggestion(self, hint_id: UUID, suggestion: str) -> None:
        """Store an improvement suggestion for a hint"""
        try:
            query = """
                INSERT INTO hint_improvement_suggestions 
                (hint_id, suggestion, created_at)
                VALUES (?, ?, ?)
            """
            
            params = (
                str(hint_id),
                suggestion,
                datetime.now(timezone.utc).isoformat()
            )
            
            self._execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error storing improvement suggestion: {e}")
            raise
    
    async def store_detected_pattern(self, event: Dict[str, Any]) -> None:
        """Store a detected pattern"""
        try:
            query = """
                INSERT INTO hint_detected_patterns (
                    pattern_id, pattern_name, pattern_description, confidence,
                    detected_at, affected_tasks, suggested_rule, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                event.get("pattern_id"),
                event.get("pattern_name"),
                event.get("pattern_description"),
                event.get("confidence"),
                event.get("occurred_at", datetime.now(timezone.utc)).isoformat(),
                json.dumps(event.get("affected_tasks", [])),
                event.get("suggested_rule"),
                datetime.now(timezone.utc).isoformat()
            )
            
            self._execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error storing detected pattern: {e}")
            raise
    
    async def get_hint_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get hint statistics for a time period"""
        try:
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            
            stats = {
                "total_hints": 0,
                "hints_by_type": defaultdict(int),
                "hints_by_priority": defaultdict(int),
                "acceptance_rate": 0,
                "dismissal_rate": 0,
                "feedback_count": 0,
                "average_effectiveness": 0
            }
            
            # Count hints in time period
            query = """
                SELECT type, priority, COUNT(*) as count
                FROM hints
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY type, priority
            """
            
            rows = self._execute_query(
                query, 
                (start_time.isoformat(), end_time.isoformat())
            )
            
            for row in rows:
                stats["total_hints"] += row["count"]
                stats["hints_by_type"][row["type"]] += row["count"]
                stats["hints_by_priority"][row["priority"]] += row["count"]
            
            # Count events
            event_query = """
                SELECT event_type, COUNT(*) as count
                FROM hint_events
                WHERE occurred_at >= ? AND occurred_at <= ?
                GROUP BY event_type
            """
            
            event_rows = self._execute_query(
                event_query,
                (start_time.isoformat(), end_time.isoformat())
            )
            
            accepted_count = 0
            dismissed_count = 0
            feedback_count = 0
            
            for row in event_rows:
                if row["event_type"] == "accepted":
                    accepted_count = row["count"]
                elif row["event_type"] == "dismissed":
                    dismissed_count = row["count"]
                elif row["event_type"] == "feedback":
                    feedback_count = row["count"]
            
            # Calculate rates
            if stats["total_hints"] > 0:
                stats["acceptance_rate"] = accepted_count / stats["total_hints"]
                stats["dismissal_rate"] = dismissed_count / stats["total_hints"]
            
            stats["feedback_count"] = feedback_count
            
            # Calculate average effectiveness
            effectiveness_query = """
                SELECT AVG(effectiveness_score) as avg_effectiveness
                FROM hint_effectiveness_scores
            """
            
            effectiveness_row = self._execute_query(
                effectiveness_query, 
                fetch_one=True
            )
            
            if effectiveness_row and effectiveness_row["avg_effectiveness"]:
                stats["average_effectiveness"] = effectiveness_row["avg_effectiveness"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting hint statistics: {e}")
            raise
    
    async def cleanup_expired_hints(self) -> int:
        """Remove expired hints and return count removed"""
        try:
            # Count expired hints first
            count_query = """
                SELECT COUNT(*) as count FROM hints
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """
            
            count_row = self._execute_query(
                count_query,
                (datetime.now(timezone.utc).isoformat(),),
                fetch_one=True
            )
            
            removed_count = count_row["count"] if count_row else 0
            
            if removed_count > 0:
                # Delete expired hints (cascade will handle related records)
                delete_query = """
                    DELETE FROM hints
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """
                
                self._execute_update(
                    delete_query,
                    (datetime.now(timezone.utc).isoformat(),)
                )
                
                logger.info(f"Cleaned up {removed_count} expired hints")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired hints: {e}")
            raise
    
    async def get_patterns(self, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """Get detected patterns above a confidence threshold"""
        try:
            query = """
                SELECT * FROM hint_detected_patterns
                WHERE confidence >= ?
                ORDER BY detected_at DESC
            """
            
            rows = self._execute_query(query, (min_confidence,))
            
            patterns = []
            for row in rows:
                pattern = dict(row)
                # Parse JSON fields
                if pattern.get("affected_tasks"):
                    pattern["affected_tasks"] = json.loads(pattern["affected_tasks"])
                # Convert ISO strings back to datetime
                if pattern.get("detected_at"):
                    pattern["detected_at"] = datetime.fromisoformat(pattern["detected_at"])
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            raise
    
    def _row_to_hint(self, row: sqlite3.Row) -> WorkflowHint:
        """Convert a database row to WorkflowHint object"""
        from ....domain.value_objects.hints import HintMetadata
        
        # Parse metadata
        metadata_dict = json.loads(row["metadata"]) if row["metadata"] else {}
        metadata = HintMetadata(
            source=metadata_dict.get("source", "unknown"),
            confidence=metadata_dict.get("confidence", 0.0),
            reasoning=metadata_dict.get("reasoning", ""),
            related_tasks=[UUID(task_id) for task_id in metadata_dict.get("related_tasks", [])],
            patterns_detected=metadata_dict.get("patterns_detected", []),
            effectiveness_score=metadata_dict.get("effectiveness_score")
        )
        
        return WorkflowHint(
            id=UUID(row["id"]),
            task_id=UUID(row["task_id"]),
            type=HintType(row["type"]),
            priority=HintPriority(row["priority"]),
            message=row["message"],
            suggested_action=row["suggested_action"],
            metadata=metadata,
            context_data=json.loads(row["context_data"]) if row["context_data"] else {},
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"])
        )