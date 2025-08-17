"""
Supabase Single-Query Optimized Repository

Ultra-optimized for Supabase cloud to minimize network latency by combining
multiple operations into single database round-trips using CTEs and window functions.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
import time

from .supabase_optimized_repository import SupabaseOptimizedRepository

logger = logging.getLogger(__name__)


class SupabaseSingleQueryRepository(SupabaseOptimizedRepository):
    """Repository with single-query optimizations for Supabase cloud"""
    
    def get_tasks_with_total_single_query(
        self, 
        status: str = None, 
        priority: str = None,
        assignee_id: str = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get task list AND total count in a SINGLE query using window functions.
        This eliminates the double network round-trip to Supabase cloud.
        
        Returns both tasks and total count in one response.
        """
        method_start = time.time()
        logger.info(f"[PERF] Starting single-query task fetch - branch_id={self.git_branch_id}")
        
        # Parameter validation
        limit = min(max(limit or 20, 1), 1000)
        offset = max(offset or 0, 0)
        
        with self.get_db_session() as session:
            session_time = time.time()
            
            # Build filters
            filters = []
            params = {"limit": limit, "offset": offset}
            
            if self.git_branch_id:
                filters.append("git_branch_id = :git_branch_id")
                params["git_branch_id"] = self.git_branch_id
            
            if status:
                filters.append("status = :status")
                params["status"] = status
            
            if priority:
                filters.append("priority = :priority")
                params["priority"] = priority
            
            if assignee_id:
                filters.append("""
                    EXISTS (
                        SELECT 1 FROM task_assignees 
                        WHERE task_id = tasks.id AND assignee_id = :assignee_id
                    )
                """)
                params["assignee_id"] = assignee_id
            
            where_clause = " AND ".join(filters) if filters else "1=1"
            
            # SINGLE QUERY with window function for total count ONLY
            # REMOVED subtask/assignee/dependency counts for performance
            # These counts were causing 3x slowdown with correlated subqueries
            sql = text(f"""
                WITH task_data AS (
                    SELECT 
                        t.id,
                        t.title,
                        t.status,
                        t.priority,
                        t.created_at,
                        t.updated_at,
                        t.git_branch_id,
                        t.context_id,
                        -- Get total count using window function (calculated once)
                        COUNT(*) OVER() as total_count,
                        -- Get row number for efficient pagination
                        ROW_NUMBER() OVER(ORDER BY t.created_at DESC) as rn
                    FROM tasks t
                    WHERE {where_clause}
                )
                SELECT 
                    id,
                    title,
                    status,
                    priority,
                    created_at,
                    updated_at,
                    git_branch_id,
                    context_id,
                    total_count
                FROM task_data
                WHERE rn > :offset AND rn <= :offset + :limit
                ORDER BY rn
            """)
            
            logger.info(f"[PERF] Session ready in {(time.time() - session_time)*1000:.1f}ms")
            
            # Execute the single query
            query_start = time.time()
            result = session.execute(sql, params)
            rows = result.fetchall()
            query_time = (time.time() - query_start) * 1000
            logger.info(f"[PERF] Single query executed in {query_time:.1f}ms")
            
            # Process results
            process_start = time.time()
            tasks = []
            total_count = 0
            
            for row in rows:
                # Extract total count from first row (same for all rows)
                if total_count == 0 and hasattr(row, 'total_count'):
                    total_count = row.total_count
                
                tasks.append({
                    "id": str(row.id) if row.id else None,
                    "title": row.title,
                    "status": row.status,
                    "priority": row.priority,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "git_branch_id": str(row.git_branch_id) if row.git_branch_id else None,
                    "context_id": str(row.context_id) if row.context_id else None,
                    # Set counts to 0 - NOT fetched for performance reasons
                    # Fetching these counts causes 3x slowdown due to correlated subqueries
                    "subtask_count": 0,
                    "assignee_count": 0,
                    "assignees_count": 0,  # Compatibility
                    "dependency_count": 0,
                    "has_dependencies": False,
                    "has_context": bool(row.context_id) if hasattr(row, 'context_id') else False
                })
            
            # If no rows returned but we need the count, run a simple count query
            # This only happens when offset >= total_count
            if not rows and (offset > 0 or where_clause != "1=1"):
                count_sql = text(f"""
                    SELECT COUNT(*) as total FROM tasks WHERE {where_clause}
                """)
                count_result = session.execute(count_sql, params).first()
                total_count = count_result.total if count_result else 0
            
            process_time = (time.time() - process_start) * 1000
            total_time = (time.time() - method_start) * 1000
            
            logger.info(f"[PERF] Processed {len(tasks)} tasks with total_count={total_count}")
            logger.info(f"[PERF] Single-query total time: {total_time:.1f}ms (query={query_time:.1f}ms, process={process_time:.1f}ms)")
            
            return {
                "tasks": tasks,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
    
    def get_tasks_ultra_optimized(self, status: str = None, priority: str = None,
                                 limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        ULTRA-OPTIMIZED version using JSON aggregation for minimum latency.
        Gets all task data with counts in a single, highly optimized query.
        """
        method_start = time.time()
        logger.info(f"[PERF] Starting ultra-optimized task fetch - branch_id={self.git_branch_id}")
        
        # Parameter validation
        limit = min(max(limit or 20, 1), 100)
        offset = max(offset or 0, 0)
        
        with self.get_db_session() as session:
            # Build filters
            filters = []
            params = {"limit": limit, "offset": offset}
            
            if self.git_branch_id:
                filters.append("t.git_branch_id = :git_branch_id")
                params["git_branch_id"] = self.git_branch_id
            
            if status:
                filters.append("t.status = :status")
                params["status"] = status
            
            if priority:
                filters.append("t.priority = :priority")
                params["priority"] = priority
            
            where_clause = " AND ".join(filters) if filters else "1=1"
            
            # ULTRA-OPTIMIZED: Single pass with JSON aggregation
            sql = text(f"""
                SELECT 
                    json_agg(
                        json_build_object(
                            'id', task_data.id,
                            'title', task_data.title,
                            'status', task_data.status,
                            'priority', task_data.priority,
                            'created_at', task_data.created_at,
                            'updated_at', task_data.updated_at,
                            'git_branch_id', task_data.git_branch_id,
                            'context_id', task_data.context_id,
                            'subtask_count', task_data.subtask_count,
                            'assignee_count', task_data.assignee_count,
                            'dependency_count', task_data.dependency_count,
                            'has_context', task_data.context_id IS NOT NULL,
                            'has_dependencies', task_data.dependency_count > 0
                        ) ORDER BY task_data.rn
                    ) as tasks,
                    COALESCE(MAX(task_data.total_count), 0) as total_count
                FROM (
                    SELECT 
                        t.id,
                        t.title,
                        t.status,
                        t.priority,
                        t.created_at,
                        t.updated_at,
                        t.git_branch_id,
                        t.context_id,
                        COUNT(*) OVER() as total_count,
                        ROW_NUMBER() OVER(ORDER BY t.created_at DESC) as rn,
                        (SELECT COUNT(*) FROM task_subtasks WHERE task_id = t.id) as subtask_count,
                        (SELECT COUNT(*) FROM task_assignees WHERE task_id = t.id) as assignee_count,
                        (SELECT COUNT(*) FROM task_dependencies WHERE task_id = t.id) as dependency_count
                    FROM tasks t
                    WHERE {where_clause}
                    LIMIT :limit OFFSET :offset
                ) as task_data
            """)
            
            # Execute the single ultra-optimized query
            query_start = time.time()
            result = session.execute(sql, params).first()
            query_time = (time.time() - query_start) * 1000
            
            # Process results
            tasks = result.tasks if result and result.tasks else []
            total_count = result.total_count if result else 0
            
            # Convert timestamps to ISO format
            for task in tasks:
                if task.get('created_at'):
                    task['created_at'] = task['created_at'].isoformat()
                if task.get('updated_at'):
                    task['updated_at'] = task['updated_at'].isoformat()
                # Ensure compatibility fields
                task['assignees_count'] = task.get('assignee_count', 0)
            
            total_time = (time.time() - method_start) * 1000
            logger.info(f"[PERF] Ultra-optimized query: {total_time:.1f}ms for {len(tasks)} tasks")
            
            return {
                "tasks": tasks,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
    
    def get_tasks_with_counts_batch(self, status: str = None, priority: str = None,
                                   limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Advanced single-query version that includes relationship counts.
        Uses lateral joins for efficient count aggregation in one query.
        """
        method_start = time.time()
        
        # Parameter validation
        limit = min(max(limit or 20, 1), 100)  # Cap at 100 for counts query
        offset = max(offset or 0, 0)
        
        with self.get_db_session() as session:
            # Build filters
            filters = []
            params = {"limit": limit, "offset": offset}
            
            if self.git_branch_id:
                filters.append("t.git_branch_id = :git_branch_id")
                params["git_branch_id"] = self.git_branch_id
            
            if status:
                filters.append("t.status = :status")
                params["status"] = status
            
            if priority:
                filters.append("t.priority = :priority")
                params["priority"] = priority
            
            where_clause = " AND ".join(filters) if filters else "1=1"
            
            # Single query with lateral joins for counts
            # This is more complex but gets everything in one round-trip
            sql = text(f"""
                WITH task_page AS (
                    SELECT 
                        t.id,
                        t.title,
                        t.status,
                        t.priority,
                        t.created_at,
                        t.updated_at,
                        t.git_branch_id,
                        t.context_id,
                        COUNT(*) OVER() as total_count
                    FROM tasks t
                    WHERE {where_clause}
                    ORDER BY t.created_at DESC
                    LIMIT :limit OFFSET :offset
                ),
                task_counts AS (
                    SELECT 
                        tp.*,
                        COALESCE(st.subtask_count, 0) as subtask_count,
                        COALESCE(ta.assignee_count, 0) as assignee_count,
                        COALESCE(td.dependency_count, 0) as dependency_count
                    FROM task_page tp
                    LEFT JOIN LATERAL (
                        SELECT COUNT(*) as subtask_count 
                        FROM task_subtasks 
                        WHERE task_id = tp.id
                    ) st ON true
                    LEFT JOIN LATERAL (
                        SELECT COUNT(*) as assignee_count 
                        FROM task_assignees 
                        WHERE task_id = tp.id
                    ) ta ON true
                    LEFT JOIN LATERAL (
                        SELECT COUNT(*) as dependency_count 
                        FROM task_dependencies 
                        WHERE task_id = tp.id
                    ) td ON true
                )
                SELECT * FROM task_counts
            """)
            
            # Execute the single query
            query_start = time.time()
            result = session.execute(sql, params)
            rows = result.fetchall()
            query_time = (time.time() - query_start) * 1000
            
            # Process results
            tasks = []
            total_count = 0
            
            for row in rows:
                if total_count == 0:
                    total_count = row.total_count
                
                tasks.append({
                    "id": str(row.id),
                    "title": row.title,
                    "status": row.status,
                    "priority": row.priority,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "subtask_count": row.subtask_count,
                    "assignee_count": row.assignee_count,  
                    "dependency_count": row.dependency_count,
                    "has_dependencies": row.dependency_count > 0,
                    "has_context": bool(row.context_id)
                })
            
            total_time = (time.time() - method_start) * 1000
            logger.info(f"[PERF] Single-query with counts: {total_time:.1f}ms for {len(tasks)} tasks")
            
            return {
                "tasks": tasks,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }