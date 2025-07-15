"""SQLite Label Repository Implementation"""

import sqlite3
import logging
import re
from typing import List, Optional, Set, Dict, Any
from datetime import datetime

from ....domain.repositories.label_repository import ILabelRepository
from ....domain.enums.common_labels import CommonLabel
from .base_repository import SQLiteBaseRepository

logger = logging.getLogger(__name__)


class SQLiteLabelRepository(SQLiteBaseRepository, ILabelRepository):
    """SQLite-based implementation of label repository"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite label repository"""
        super().__init__(db_path=db_path)
        self._initialize_common_labels()
    
    def _initialize_common_labels(self):
        """Initialize repository with common labels"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if labels table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='labels'")
                if not cursor.fetchone():
                    logger.warning("Labels table does not exist yet, skipping initialization")
                    return
                
                # Check if we already have common labels
                cursor.execute("SELECT COUNT(*) FROM labels WHERE is_common = 1")
                result = cursor.fetchone()
                if result and result[0] > 0:
                    logger.debug(f"Common labels already initialized ({result[0]} found)")
                    return  # Already initialized
                
                # Add all common labels from enum
                inserted_count = 0
                for label in CommonLabel:
                    normalized = self._normalize_label(label.value)
                    category = self._get_label_category(label)
                    
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO labels (label, normalized, category, is_common, usage_count)
                            VALUES (?, ?, ?, 1, 0)
                        """, (label.value, normalized, category))
                        
                        if cursor.rowcount > 0:
                            inserted_count += 1
                    except sqlite3.IntegrityError:
                        # Label already exists, skip
                        pass
                
                conn.commit()
                
                if inserted_count > 0:
                    logger.info(f"Initialized {inserted_count} common labels in database")
                else:
                    logger.debug("No new common labels to initialize")
                
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.warning("Labels table does not exist, database may not be initialized yet")
            else:
                logger.error(f"Database error initializing common labels: {e}")
        except Exception as e:
            logger.error(f"Error initializing common labels: {e}")
    
    def _get_label_category(self, label: CommonLabel) -> str:
        """Get category for a common label"""
        if label in [CommonLabel.URGENT, CommonLabel.CRITICAL, CommonLabel.HOT_FIX, CommonLabel.BLOCKER]:
            return "priority"
        elif label in [CommonLabel.BUG, CommonLabel.FEATURE, CommonLabel.ENHANCEMENT, CommonLabel.REFACTOR,
                       CommonLabel.DOCUMENTATION, CommonLabel.TESTING, CommonLabel.RESEARCH, CommonLabel.SPIKE]:
            return "type"
        elif label in [CommonLabel.FRONTEND, CommonLabel.BACKEND, CommonLabel.API, CommonLabel.DATABASE,
                       CommonLabel.UI_UX, CommonLabel.INFRASTRUCTURE, CommonLabel.DEVOPS, CommonLabel.SECURITY]:
            return "component"
        elif label in [CommonLabel.CODE_REVIEW, CommonLabel.QA, CommonLabel.DEPLOYMENT, CommonLabel.MONITORING,
                       CommonLabel.PERFORMANCE, CommonLabel.OPTIMIZATION]:
            return "process"
        elif label in [CommonLabel.BLOCKED, CommonLabel.WAITING, CommonLabel.READY, CommonLabel.IN_REVIEW,
                       CommonLabel.NEEDS_CLARIFICATION]:
            return "status"
        else:
            return "custom"
    
    def _normalize_label(self, label: str) -> str:
        """Normalize label to standard format"""
        # Remove extra whitespace, convert to lowercase
        normalized = label.strip().lower()
        normalized = ' '.join(normalized.split())  # Remove multiple spaces
        
        # Replace spaces with hyphens
        normalized = normalized.replace(' ', '-')
        
        # Remove invalid characters (keep alphanumeric, hyphens, underscores, slashes)
        normalized = re.sub(r'[^a-z0-9\-_/]', '', normalized)
        
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        
        return normalized
    
    async def create_label(self, label: str, category: Optional[str] = None) -> str:
        """Create a new label if it doesn't exist, return normalized label"""
        normalized = self._normalize_label(label)
        
        if not normalized:
            raise ValueError("Label cannot be empty after normalization")
        
        if len(normalized) > 50:
            raise ValueError(f"Label too long: {label} (max 50 characters)")
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if already exists
                cursor.execute("SELECT label FROM labels WHERE normalized = ?", (normalized,))
                existing = cursor.fetchone()
                
                if existing:
                    # Increment usage count
                    cursor.execute("""
                        UPDATE labels 
                        SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE normalized = ?
                    """, (normalized,))
                    conn.commit()
                    return existing[0]
                
                # Create new label
                if category is None:
                    category = "custom"
                
                cursor.execute("""
                    INSERT INTO labels (label, normalized, category, usage_count)
                    VALUES (?, ?, ?, 1)
                """, (label, normalized, category))
                
                conn.commit()
                logger.info(f"Created new label: {label} (normalized: {normalized})")
                
                return label
                
        except Exception as e:
            logger.error(f"Error creating label: {e}")
            raise
    
    async def find_label(self, label: str) -> Optional[str]:
        """Find an existing label (case-insensitive), return normalized version"""
        normalized = self._normalize_label(label)
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT label FROM labels WHERE normalized = ?", (normalized,))
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error finding label: {e}")
            return None
    
    async def get_all_labels(self) -> List[str]:
        """Get all existing labels"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT label FROM labels ORDER BY category, label")
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting all labels: {e}")
            return []
    
    async def get_labels_by_category(self, category: str) -> List[str]:
        """Get labels by category"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT label FROM labels WHERE category = ? ORDER BY label", (category,))
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting labels by category: {e}")
            return []
    
    async def search_labels(self, query: str, limit: int = 10) -> List[str]:
        """Search for labels matching query"""
        query_lower = f"%{query.lower()}%"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT label, usage_count 
                    FROM labels 
                    WHERE label LIKE ? OR normalized LIKE ?
                    ORDER BY usage_count DESC, label
                    LIMIT ?
                """, (query_lower, query_lower, limit))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error searching labels: {e}")
            return []
    
    async def get_label_usage_count(self, label: str) -> int:
        """Get usage count for a label"""
        normalized = self._normalize_label(label)
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT usage_count FROM labels WHERE normalized = ?", (normalized,))
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting label usage count: {e}")
            return 0
    
    async def delete_unused_labels(self) -> int:
        """Delete labels with zero usage, return count deleted"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Count labels to delete (custom labels with zero usage)
                cursor.execute("SELECT COUNT(*) FROM labels WHERE usage_count = 0 AND is_common = 0")
                count = cursor.fetchone()[0]
                
                # Delete unused custom labels
                cursor.execute("DELETE FROM labels WHERE usage_count = 0 AND is_common = 0")
                conn.commit()
                
                if count > 0:
                    logger.info(f"Deleted {count} unused labels")
                
                return count
                
        except Exception as e:
            logger.error(f"Error deleting unused labels: {e}")
            return 0
    
    async def normalize_label(self, label: str) -> str:
        """Normalize a label to standard format"""
        return self._normalize_label(label)
    
    async def validate_and_create_labels(self, labels: List[str]) -> List[str]:
        """Validate and create multiple labels, return normalized list"""
        if not labels:
            return []
        
        normalized_to_original = {}
        normalized_labels = []
        
        # First, normalize and validate all labels
        for label in labels:
            if not label or not isinstance(label, str):
                continue
            
            try:
                # Normalize the label
                normalized = self._normalize_label(label)
                
                if not normalized:
                    raise ValueError("Label cannot be empty after normalization")
                
                if len(normalized) > 50:
                    raise ValueError(f"Label too long: {label} (max 50 characters)")
                
                # Track the mapping from normalized to original
                if normalized not in normalized_to_original:
                    normalized_to_original[normalized] = label.strip()
                    normalized_labels.append(normalized)
                    
            except ValueError as e:
                logger.warning(f"Invalid label '{label}': {e}")
                continue
        
        if not normalized_labels:
            return []
        
        # Batch insert all labels at once
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get existing labels in batch
                placeholders = ','.join(['?' for _ in normalized_labels])
                cursor.execute(f"""
                    SELECT label, normalized FROM labels 
                    WHERE normalized IN ({placeholders})
                """, normalized_labels)
                
                existing_map = {row[1]: row[0] for row in cursor.fetchall()}
                
                # Prepare labels to insert (only non-existing ones)
                labels_to_insert = []
                for normalized in normalized_labels:
                    if normalized not in existing_map:
                        original = normalized_to_original[normalized]
                        labels_to_insert.append((original, normalized, 'custom', 1))
                
                # Batch insert new labels
                if labels_to_insert:
                    cursor.executemany("""
                        INSERT INTO labels (label, normalized, category, usage_count)
                        VALUES (?, ?, ?, ?)
                    """, labels_to_insert)
                    logger.info(f"Created {len(labels_to_insert)} new labels in batch")
                
                # Update usage count for existing labels in batch
                existing_normalized = list(existing_map.keys())
                if existing_normalized:
                    placeholders = ','.join(['?' for _ in existing_normalized])
                    cursor.execute(f"""
                        UPDATE labels 
                        SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE normalized IN ({placeholders})
                    """, existing_normalized)
                
                conn.commit()
                
                # Return the original label names (not normalized)
                result_labels = []
                for normalized in normalized_labels:
                    if normalized in existing_map:
                        result_labels.append(existing_map[normalized])
                    else:
                        result_labels.append(normalized_to_original[normalized])
                
                return result_labels
                
        except Exception as e:
            logger.error(f"Error creating labels in batch: {e}")
            raise
    
    async def get_labels_for_task(self, task_id: str) -> List[str]:
        """Get all labels for a specific task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT l.label 
                    FROM labels l
                    JOIN task_labels tl ON l.id = tl.label_id
                    WHERE tl.task_id = ?
                    ORDER BY l.category, l.label
                """, (task_id,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting labels for task: {e}")
            return []
    
    async def update_task_labels(self, task_id: str, labels: List[str]):
        """Update labels for a task"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Remove existing task labels
                cursor.execute("DELETE FROM task_labels WHERE task_id = ?", (task_id,))
                
                # Add new labels
                for label in labels:
                    normalized = self._normalize_label(label)
                    
                    # Get or create label
                    cursor.execute("SELECT id FROM labels WHERE normalized = ?", (normalized,))
                    result = cursor.fetchone()
                    
                    if result:
                        label_id = result[0]
                    else:
                        # Create new label
                        cursor.execute("""
                            INSERT INTO labels (label, normalized, category)
                            VALUES (?, ?, 'custom')
                        """, (label, normalized))
                        label_id = cursor.lastrowid
                    
                    # Add to task_labels
                    cursor.execute("""
                        INSERT INTO task_labels (task_id, label_id)
                        VALUES (?, ?)
                    """, (task_id, label_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating task labels: {e}")
            raise
    
    async def get_popular_labels(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular labels with usage counts"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT label, category, usage_count, is_common
                    FROM labels
                    WHERE usage_count > 0
                    ORDER BY usage_count DESC, label
                    LIMIT ?
                """, (limit,))
                
                return [
                    {
                        "label": row[0],
                        "category": row[1],
                        "usage_count": row[2],
                        "is_common": bool(row[3])
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting popular labels: {e}")
            return []
    
    async def update_label_usage(self, labels: List[str], increment: bool = True):
        """Update usage count for multiple labels"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for label in labels:
                    normalized = self._normalize_label(label)
                    
                    if increment:
                        cursor.execute("""
                            UPDATE labels 
                            SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                            WHERE normalized = ?
                        """, (normalized,))
                    else:
                        cursor.execute("""
                            UPDATE labels 
                            SET usage_count = CASE 
                                WHEN usage_count > 0 THEN usage_count - 1 
                                ELSE 0 
                            END,
                            updated_at = CURRENT_TIMESTAMP
                            WHERE normalized = ?
                        """, (normalized,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating label usage: {e}")
            raise