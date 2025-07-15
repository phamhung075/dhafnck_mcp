"""SQLite implementation of SubtaskRepository"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from ....domain.repositories.subtask_repository import SubtaskRepository
from ....domain.entities.subtask import Subtask
from ....domain.value_objects.task_id import TaskId
from ....domain.value_objects.subtask_id import SubtaskId
from ....domain.value_objects.task_status import TaskStatus
from ....domain.value_objects.priority import Priority
from .base_repository import SQLiteBaseRepository

logger = logging.getLogger(__name__)


class SQLiteSubtaskRepository(SQLiteBaseRepository, SubtaskRepository):
    """SQLite implementation of SubtaskRepository"""
    
    def __init__(self, db_path: str, user_id: Optional[str] = None, 
                 project_id: Optional[str] = None, git_branch_name: Optional[str] = None):
        """
        Initialize SQLite subtask repository
        
        Args:
            db_path: Path to SQLite database
            user_id: User ID (compatibility parameter)
            project_id: Project ID (compatibility parameter)
            git_branch_name: Git branch name (compatibility parameter)
        """
        # Initialize base repository (no context needed for subtasks)
        super().__init__(db_path=db_path)
    
    
    def _subtask_from_row(self, row: sqlite3.Row) -> Subtask:
        """Convert database row to Subtask entity"""
        try:
            assignees = json.loads(row['assignees']) if row['assignees'] else []

            # Create subtask entity, converting IDs to value objects
            subtask = Subtask(
                id=SubtaskId(row['id']),
                parent_task_id=TaskId(row['task_id']),
                title=row['title'],
                description=row['description'] or "",
                status=TaskStatus(row['status']),
                priority=Priority(row['priority']),
                assignees=assignees,
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )

            return subtask

        except Exception as e:
            logger.error(f"Error converting row to Subtask: {e}, row: {dict(row)}")
            raise
    
    
    def save(self, subtask: Subtask) -> bool:
        """Save a subtask"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if subtask exists
                cursor.execute(
                    "SELECT id FROM task_subtasks WHERE id = ?",
                    (subtask.id.value,)
                )
                exists = cursor.fetchone() is not None
                
                # Convert assignees to JSON
                assignees_json = json.dumps(subtask.assignees)
                
                if exists:
                    # Update existing subtask
                    cursor.execute("""
                        UPDATE task_subtasks
                        SET title = ?, description = ?, assignees = ?,
                            updated_at = ?, status = ?, priority = ?,
                            completed_at = ?
                        WHERE id = ?
                    """, (
                        subtask.title,
                        subtask.description,
                        assignees_json,
                        subtask.updated_at.isoformat(),
                        str(subtask.status),
                        str(subtask.priority),
                        subtask.updated_at.isoformat() if subtask.status.is_completed() else None,
                        subtask.id.value
                    ))
                else:
                    # Insert new subtask
                    cursor.execute("""
                        INSERT INTO task_subtasks
                        (id, task_id, title, description, assignees,
                         created_at, updated_at, status, priority, completed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        subtask.id.value,
                        subtask.parent_task_id.value,
                        subtask.title,
                        subtask.description,
                        assignees_json,
                        subtask.created_at.isoformat(),
                        subtask.updated_at.isoformat(),
                        str(subtask.status),
                        str(subtask.priority),
                        subtask.updated_at.isoformat() if subtask.status.is_completed() else None
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving subtask {subtask.id.value}: {e}")
            return False

    def create_new(self, subtask: Subtask) -> bool:
        """Create a new subtask, ensuring it doesn't already exist"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if subtask already exists
                cursor.execute("""
                    SELECT id FROM task_subtasks 
                    WHERE id = ?
                """, (subtask.id.value,))
                
                if cursor.fetchone() is not None:
                    raise ValueError(f"Subtask with ID '{subtask.id.value}' already exists in task '{subtask.parent_task_id.value}'")
                
                # Create the subtask using save method
                return self.save(subtask)
                
        except Exception as e:
            logger.error(f"Error creating new subtask {subtask.id.value}: {e}")
            raise
    
    def find_by_id(self, subtask_id: Union[SubtaskId, str]) -> Optional[Subtask]:
        """Find subtask by ID"""
        try:
            # Support raw string IDs in addition to SubtaskId value objects
            if isinstance(subtask_id, SubtaskId):
                subtask_id_value = subtask_id.value
            else:
                subtask_id_value = str(subtask_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM task_subtasks
                    WHERE id = ?
                """, (subtask_id_value,))
                
                row = cursor.fetchone()
                if row:
                    return self._subtask_from_row(row)
                return None
                
        except Exception as e:
            logger.error(f"Error finding subtask by ID {subtask_id.value}: {e}")
            return None
    
    def find_by_parent_task_id(self, parent_task_id: TaskId) -> List[Subtask]:
        """Find all subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM task_subtasks
                    WHERE task_id = ?
                """, (parent_task_id.value,))
                
                rows = cursor.fetchall()
                return [self._subtask_from_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error finding subtasks for parent task {parent_task_id.value}: {e}")
            return []
    
    def find_by_assignee(self, assignee: str) -> List[Subtask]:
        """Find subtasks by assignee"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, task_id, title, description, status, priority, assignees, 
                           estimated_effort, created_at, updated_at, completed_at,
                           user_id, project_id, git_branch_name
                    FROM task_subtasks 
                    WHERE assignees LIKE ?
                    ORDER BY created_at
                """, (f"%{assignee}%",))
                
                rows = cursor.fetchall()
                return [self._subtask_from_row(tuple(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Error finding subtasks by assignee {assignee}: {e}")
            return []
    
    def find_by_status(self, status: str) -> List[Subtask]:
        """Find all subtasks with a specific status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM task_subtasks
                    WHERE status = ?
                """, (status,))
                
                rows = cursor.fetchall()
                return [self._subtask_from_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error finding subtasks by status {status}: {e}")
            return []
    
    def find_completed(self, parent_task_id: TaskId) -> List[Subtask]:
        """Find completed subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM task_subtasks
                    WHERE task_id = ? AND status = ?
                """, (parent_task_id.value, TaskStatus.done().value))
                
                rows = cursor.fetchall()
                return [self._subtask_from_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error finding completed subtasks for parent task {parent_task_id.value}: {e}")
            return []
    
    def find_pending(self, parent_task_id: TaskId) -> List[Subtask]:
        """Find all non-completed subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM task_subtasks
                    WHERE task_id = ? AND status != ?
                """, (parent_task_id.value, TaskStatus.done().value))
                
                rows = cursor.fetchall()
                return [self._subtask_from_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error finding pending subtasks for task {parent_task_id.value}: {e}")
            return []
    
    def delete(self, subtask_id: Union[SubtaskId, str]) -> bool:
        """Delete a subtask by its ID"""
        try:
            subtask_id_value = subtask_id.value if isinstance(subtask_id, SubtaskId) else str(subtask_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM task_subtasks WHERE id = ?", (subtask_id_value,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting subtask {subtask_id.value}: {e}")
            return False
    
    def delete_by_parent_task_id(self, parent_task_id: TaskId) -> bool:
        """Delete all subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM task_subtasks WHERE task_id = ?",
                    (parent_task_id.value,)
                )
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting subtasks for task {parent_task_id.value}: {e}")
            return False
    
    def exists(self, subtask_id: SubtaskId) -> bool:
        """Check if a subtask exists by its ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM task_subtasks WHERE id = ?", (subtask_id.value,))
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking existence of subtask {subtask_id.value}: {e}")
            return False
    
    def count_by_parent_task_id(self, parent_task_id: TaskId) -> int:
        """Count subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM task_subtasks WHERE task_id = ?",
                    (parent_task_id.value,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error counting subtasks for task {parent_task_id.value}: {e}")
            return 0
    
    def count_completed_by_parent_task_id(self, parent_task_id: TaskId) -> int:
        """Count completed subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM task_subtasks
                    WHERE task_id = ? AND status = ?
                """, (parent_task_id.value, TaskStatus.done().value))
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error counting completed subtasks for task {parent_task_id.value}: {e}")
            return 0
    
    def get_next_id(self, parent_task_id: TaskId) -> SubtaskId:
        """Generate a new unique subtask ID"""
        return SubtaskId.generate_new()
    
    def get_subtask_progress(self, parent_task_id: TaskId) -> Dict[str, Any]:
        """Get subtask progress statistics for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM task_subtasks
                    WHERE task_id = ?
                    GROUP BY status
                """, (parent_task_id.value,))
                
                rows = cursor.fetchall()
                if rows:
                    total = sum(count for status, count in rows)
                    completed = sum(count for status, count in rows if status == TaskStatus.done().value)
                    percentage = (completed / total) * 100 if total > 0 else 0
                    
                    return {
                        "total": total,
                        "completed": completed,
                        "percentage": percentage
                    }
                
                return {
                    "total": 0,
                    "completed": 0,
                    "percentage": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting subtask progress for task {parent_task_id.value}: {e}")
            return {"total": 0, "completed": 0, "percentage": 0.0}
    
    def bulk_update_status(self, parent_task_id: TaskId, status: str) -> bool:
        """Update status of all subtasks for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE task_subtasks
                    SET status = ?, updated_at = ?
                    WHERE task_id = ?
                """, (status, datetime.now().isoformat(), parent_task_id.value))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error bulk updating status for subtasks of task {parent_task_id.value}: {e}")
            return False
    
    def bulk_complete(self, parent_task_id: TaskId) -> bool:
        """Mark all subtasks as completed for a parent task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE task_subtasks
                    SET status = ?, updated_at = ?, completed_at = ?
                    WHERE task_id = ?
                """, (TaskStatus.done().value, now, now, parent_task_id.value))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error bulk completing subtasks for task {parent_task_id.value}: {e}")
            return False
    
    def remove_subtask(self, parent_task_id: Union[TaskId, str], subtask_id: Union[SubtaskId, str]) -> bool:
        """Remove a single subtask by its ID"""
        # Normalize IDs to string representations
        parent_id_value = parent_task_id.value if hasattr(parent_task_id, 'value') else str(parent_task_id)
        subtask_id_value = subtask_id.value if hasattr(subtask_id, 'value') else str(subtask_id)

        logging.debug(f"[SQLiteSubtaskRepository] remove_subtask: parent_task_id={parent_id_value}, subtask_id={subtask_id_value}")

        with self._get_connection() as conn:
            result = conn.execute(
                'DELETE FROM task_subtasks WHERE task_id = ? AND id = ?',
                (parent_id_value, subtask_id_value)
            )
            conn.commit()
            return result.rowcount > 0