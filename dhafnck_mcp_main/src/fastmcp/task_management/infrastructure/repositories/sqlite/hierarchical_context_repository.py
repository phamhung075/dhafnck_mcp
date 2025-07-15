"""SQLite Hierarchical Context Repository Implementation"""

import json
import logging
import sqlite3
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .base_repository import SQLiteBaseRepository

logger = logging.getLogger(__name__)


class SQLiteHierarchicalContextRepository(SQLiteBaseRepository):
    """
    SQLite-based implementation of Hierarchical Context Repository.
    
    Provides data access methods for:
    - Global contexts (singleton)
    - Project contexts (inheriting from global)
    - Task contexts (inheriting from project)
    - Delegation queue management
    - Cache management
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite hierarchical context repository
        
        Args:
            db_path: Path to SQLite database file
        """
        # Initialize base repository with connection pooling
        super().__init__(db_path=db_path, use_pool=True)
        logger.info(f"SQLiteHierarchicalContextRepository initialized with db_path: {self._db_path}")
    
    # ===============================================
    # GLOBAL CONTEXT OPERATIONS
    # ===============================================
    
    def create_global_context(self, global_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create global context"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO global_contexts (
                        id, organization_id, autonomous_rules, security_policies,
                        coding_standards, workflow_templates, delegation_rules,
                        created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """, (
                    global_id,
                    data.get("organization_id", "default_org"),
                    json.dumps(data.get("autonomous_rules", {})),
                    json.dumps(data.get("security_policies", {})),
                    json.dumps(data.get("coding_standards", {})),
                    json.dumps(data.get("workflow_templates", {})),
                    json.dumps(data.get("delegation_rules", {}))
                ))
                conn.commit()
                
                # Return the created context
                return self.get_global_context(global_id)
                
        except Exception as e:
            logger.error(f"Error creating global context: {e}")
            raise
    
    def get_global_context(self, global_id: str = "global_singleton") -> Optional[Dict[str, Any]]:
        """Get global context (singleton)"""
        try:
            result = self._execute_query(
                """
                SELECT id, organization_id, autonomous_rules, security_policies,
                       coding_standards, workflow_templates, delegation_rules,
                       created_at, updated_at
                FROM global_contexts 
                WHERE id = ?
                """,
                (global_id,),
                fetch_one=True
            )
            
            if not result:
                return None
            
            return {
                "id": result["id"],
                "organization_id": result["organization_id"],
                "autonomous_rules": json.loads(result["autonomous_rules"]) if result["autonomous_rules"] else {},
                "security_policies": json.loads(result["security_policies"]) if result["security_policies"] else {},
                "coding_standards": json.loads(result["coding_standards"]) if result["coding_standards"] else {},
                "workflow_templates": json.loads(result["workflow_templates"]) if result["workflow_templates"] else {},
                "delegation_rules": json.loads(result["delegation_rules"]) if result["delegation_rules"] else {},
                "created_at": result["created_at"],
                "updated_at": result["updated_at"]
            }
            
        except Exception as e:
            logger.error(f"Error getting global context: {e}")
            return None
    
    def update_global_context(self, global_id: str, updates: Dict[str, Any]) -> bool:
        """Update global context"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ["autonomous_rules", "security_policies", "coding_standards", 
                           "workflow_templates", "delegation_rules"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(json.dumps(value))
                elif field in ["organization_id"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(global_id)
            
            query = f"""
                UPDATE global_contexts 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            rows_affected = self._execute_update(query, tuple(params))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating global context: {e}")
            return False
    
    def delete_global_context(self, global_id: str) -> bool:
        """Delete global context"""
        try:
            rows_affected = self._execute_update(
                "DELETE FROM global_contexts WHERE id = ?",
                (global_id,)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting global context: {e}")
            return False
    
    def list_global_contexts(self) -> List[Dict[str, Any]]:
        """List all global contexts"""
        try:
            rows = self._execute_query("SELECT * FROM global_contexts")
            
            contexts = []
            for row in rows:
                contexts.append({
                    "id": row["id"],
                    "organization_id": row["organization_id"],
                    "autonomous_rules": json.loads(row["autonomous_rules"]),
                    "security_policies": json.loads(row["security_policies"]),
                    "coding_standards": json.loads(row["coding_standards"]),
                    "workflow_templates": json.loads(row["workflow_templates"]),
                    "delegation_rules": json.loads(row["delegation_rules"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "version": row["version"]
                })
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error listing global contexts: {e}")
            return []
    
    # ===============================================
    # PROJECT CONTEXT OPERATIONS
    # ===============================================
    
    def create_project_context(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project context"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO project_contexts (
                        project_id, parent_global_id, team_preferences, technology_stack,
                        project_workflow, local_standards, global_overrides, delegation_rules,
                        created_at, updated_at, version, inheritance_disabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, ?)
                """, (
                    project_id,
                    data.get("parent_global_id", "global_singleton"),
                    json.dumps(data.get("team_preferences", {})),
                    json.dumps(data.get("technology_stack", {})),
                    json.dumps(data.get("project_workflow", {})),
                    json.dumps(data.get("local_standards", {})),
                    json.dumps(data.get("global_overrides", {})),
                    json.dumps(data.get("delegation_rules", {})),
                    data.get("inheritance_disabled", False)
                ))
                conn.commit()
                
                # Return the created context
                return self.get_project_context(project_id)
                
        except Exception as e:
            logger.error(f"Error creating project context: {e}")
            raise
    
    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project context"""
        try:
            result = self._execute_query(
                """
                SELECT project_id, parent_global_id, team_preferences, technology_stack,
                       project_workflow, local_standards, global_overrides, delegation_rules,
                       created_at, updated_at
                FROM project_contexts 
                WHERE project_id = ?
                """,
                (project_id,),
                fetch_one=True
            )
            
            if not result:
                return None
            
            return {
                "project_id": result["project_id"],
                "parent_global_id": result["parent_global_id"],
                "team_preferences": json.loads(result["team_preferences"]) if result["team_preferences"] else {},
                "technology_stack": json.loads(result["technology_stack"]) if result["technology_stack"] else {},
                "project_workflow": json.loads(result["project_workflow"]) if result["project_workflow"] else {},
                "local_standards": json.loads(result["local_standards"]) if result["local_standards"] else {},
                "global_overrides": json.loads(result["global_overrides"]) if result["global_overrides"] else {},
                "delegation_rules": json.loads(result["delegation_rules"]) if result["delegation_rules"] else {},
                "created_at": result["created_at"],
                "updated_at": result["updated_at"]
            }
            
        except Exception as e:
            logger.error(f"Error getting project context {project_id}: {e}")
            return None
    
    def update_project_context(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project context"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ["team_preferences", "technology_stack", "project_workflow", 
                           "local_standards", "global_overrides", "delegation_rules"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(json.dumps(value))
                elif field in ["parent_global_id"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(project_id)
            
            query = f"""
                UPDATE project_contexts 
                SET {', '.join(set_clauses)}
                WHERE project_id = ?
            """
            
            rows_affected = self._execute_update(query, tuple(params))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating project context {project_id}: {e}")
            return False
    
    def delete_project_context(self, project_id: str) -> bool:
        """Delete project context"""
        try:
            rows_affected = self._execute_update(
                "DELETE FROM project_contexts WHERE project_id = ?",
                (project_id,)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting project context: {e}")
            return False
    
    def list_project_contexts(self) -> List[Dict[str, Any]]:
        """List all project contexts"""
        try:
            rows = self._execute_query("SELECT * FROM project_contexts")
            
            contexts = []
            for row in rows:
                contexts.append({
                    "project_id": row["project_id"],
                    "parent_global_id": row["parent_global_id"],
                    "team_preferences": json.loads(row["team_preferences"]),
                    "technology_stack": json.loads(row["technology_stack"]),
                    "project_workflow": json.loads(row["project_workflow"]),
                    "local_standards": json.loads(row["local_standards"]),
                    "global_overrides": json.loads(row["global_overrides"]),
                    "delegation_rules": json.loads(row["delegation_rules"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "version": row["version"],
                    "inheritance_disabled": row["inheritance_disabled"]
                })
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error listing project contexts: {e}")
            return []
    
    # ===============================================
    # TASK CONTEXT OPERATIONS
    # ===============================================
    
    def create_task_context(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task context"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Extract project ID from data or use default
                project_id = data.get("parent_project_id", "default_project")
                project_context_id = data.get("parent_project_context_id", project_id)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO task_contexts (
                        task_id, parent_project_id, parent_project_context_id,
                        task_data, local_overrides, implementation_notes,
                        delegation_triggers, inheritance_disabled, force_local_only,
                        created_at, updated_at, version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """, (
                    task_id,
                    project_id,
                    project_context_id,
                    json.dumps(data.get("task_data", {})),
                    json.dumps(data.get("local_overrides", {})),
                    json.dumps(data.get("implementation_notes", {})),
                    json.dumps(data.get("delegation_triggers", {})),
                    data.get("inheritance_disabled", False),
                    data.get("force_local_only", False)
                ))
                conn.commit()
                
                # Return the created context
                return self.get_task_context(task_id)
                
        except Exception as e:
            logger.error(f"Error creating task context: {e}")
            raise
    
    def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task context"""
        try:
            result = self._execute_query(
                """
                SELECT task_id, parent_project_id, parent_project_context_id,
                       task_data, local_overrides, implementation_notes,
                       delegation_triggers, inheritance_disabled, force_local_only,
                       created_at, updated_at, version
                FROM task_contexts 
                WHERE task_id = ?
                """,
                (task_id,),
                fetch_one=True
            )
            
            if not result:
                return None
            
            return {
                "task_id": result["task_id"],
                "parent_project_id": result["parent_project_id"],
                "parent_project_context_id": result["parent_project_context_id"],
                "task_data": json.loads(result["task_data"]) if result["task_data"] else {},
                "local_overrides": json.loads(result["local_overrides"]) if result["local_overrides"] else {},
                "implementation_notes": json.loads(result["implementation_notes"]) if result["implementation_notes"] else {},
                "delegation_triggers": json.loads(result["delegation_triggers"]) if result["delegation_triggers"] else {},
                "inheritance_disabled": result["inheritance_disabled"],
                "force_local_only": result["force_local_only"],
                "created_at": result["created_at"],
                "updated_at": result["updated_at"],
                "version": result["version"]
            }
            
        except Exception as e:
            logger.error(f"Error getting task context {task_id}: {e}")
            return None
    
    def update_task_context(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task context"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ["task_data", "local_overrides", "implementation_notes",
                           "delegation_triggers"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(json.dumps(value))
                elif field in ["parent_project_id", "parent_project_context_id", 
                               "inheritance_disabled", "force_local_only"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(task_id)
            
            query = f"""
                UPDATE task_contexts 
                SET {', '.join(set_clauses)}
                WHERE task_id = ?
            """
            
            rows_affected = self._execute_update(query, tuple(params))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating task context {task_id}: {e}")
            return False
    
    def delete_task_context(self, task_id: str) -> bool:
        """Delete task context"""
        try:
            rows_affected = self._execute_update(
                "DELETE FROM task_contexts WHERE task_id = ?",
                (task_id,)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting task context: {e}")
            return False
    
    def list_task_contexts(self) -> List[Dict[str, Any]]:
        """List all task contexts"""
        try:
            rows = self._execute_query("SELECT * FROM task_contexts")
            
            contexts = []
            for row in rows:
                contexts.append({
                    "task_id": row["task_id"],
                    "parent_project_id": row["parent_project_id"],
                    "parent_project_context_id": row["parent_project_context_id"],
                    "task_data": json.loads(row["task_data"]),
                    "local_overrides": json.loads(row["local_overrides"]),
                    "implementation_notes": json.loads(row["implementation_notes"]),
                    "delegation_triggers": json.loads(row["delegation_triggers"]),
                    "inheritance_disabled": row["inheritance_disabled"],
                    "force_local_only": row["force_local_only"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "version": row["version"]
                })
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error listing task contexts: {e}")
            return []
    
    # ===============================================
    # DELEGATION OPERATIONS
    # ===============================================
    
    async def store_delegation(self, delegation_data: Dict[str, Any]) -> str:
        """Store delegation request and return delegation ID"""
        try:
            # Generate delegation ID using UUID
            delegation_id = str(uuid.uuid4())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO context_delegations (
                        id, source_level, source_id, target_level, target_id,
                        delegated_data, delegation_reason, trigger_type,
                        auto_delegated, confidence_score, processed, approved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    delegation_id,
                    delegation_data["source_level"],
                    delegation_data["source_id"],
                    delegation_data["target_level"],
                    delegation_data["target_id"],
                    json.dumps(delegation_data["delegated_data"]),
                    delegation_data["reason"],
                    delegation_data["trigger_type"],
                    delegation_data.get("auto_delegated", False),
                    delegation_data.get("confidence_score"),
                    False,  # processed
                    None    # approved
                ))
                conn.commit()
                
                return delegation_id
                
        except Exception as e:
            logger.error(f"Error storing delegation: {e}")
            raise
    
    async def get_delegation(self, delegation_id: str) -> Optional[Dict[str, Any]]:
        """Get delegation by ID"""
        try:
            result = self._execute_query(
                """
                SELECT id, source_level, source_id, target_level, target_id,
                       delegated_data, delegation_reason, trigger_type,
                       auto_delegated, confidence_score, processed, approved,
                       created_at, processed_at
                FROM context_delegations 
                WHERE id = ?
                """,
                (delegation_id,),
                fetch_one=True
            )
            
            if not result:
                return None
            
            return {
                "id": result["id"],
                "source_level": result["source_level"],
                "source_id": result["source_id"],
                "target_level": result["target_level"],
                "target_id": result["target_id"],
                "delegated_data": json.loads(result["delegated_data"]) if result["delegated_data"] else {},
                "delegation_reason": result["delegation_reason"],
                "trigger_type": result["trigger_type"],
                "auto_delegated": result["auto_delegated"],
                "confidence_score": result["confidence_score"],
                "processed": result["processed"],
                "approved": result["approved"],
                "created_at": result["created_at"],
                "processed_at": result["processed_at"]
            }
            
        except Exception as e:
            logger.error(f"Error getting delegation {delegation_id}: {e}")
            return None
    
    async def get_delegations(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get delegations with filters"""
        try:
            # Build query with filters
            where_clauses = []
            params = []
            
            for field, value in filters.items():
                if field in ["source_level", "target_level", "trigger_type", "processed", "approved"]:
                    where_clauses.append(f"{field} = ?")
                    params.append(value)
                elif field in ["source_id", "target_id"]:
                    where_clauses.append(f"{field} = ?")
                    params.append(value)
            
            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT id, source_level, source_id, target_level, target_id,
                       delegated_data, delegation_reason, trigger_type,
                       auto_delegated, confidence_score, processed, approved,
                       created_at, processed_at
                FROM context_delegations 
                {where_clause}
                ORDER BY created_at DESC
            """
            
            rows = self._execute_query(query, tuple(params))
            
            return [
                {
                    "id": row["id"],
                    "source_level": row["source_level"],
                    "source_id": row["source_id"],
                    "target_level": row["target_level"],
                    "target_id": row["target_id"],
                    "delegated_data": json.loads(row["delegated_data"]) if row["delegated_data"] else {},
                    "delegation_reason": row["delegation_reason"],
                    "trigger_type": row["trigger_type"],
                    "auto_delegated": row["auto_delegated"],
                    "confidence_score": row["confidence_score"],
                    "processed": row["processed"],
                    "approved": row["approved"],
                    "created_at": row["created_at"],
                    "processed_at": row["processed_at"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting delegations: {e}")
            return []
    
    async def update_delegation(self, delegation_id: str, updates: Dict[str, Any]) -> bool:
        """Update delegation"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ["processed", "approved", "processed_at", "processed_by", "rejected_reason"]:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True
            
            params.append(delegation_id)
            
            query = f"""
                UPDATE context_delegations 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            rows_affected = self._execute_update(query, tuple(params))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error updating delegation {delegation_id}: {e}")
            return False
    
    # ===============================================
    # CACHE OPERATIONS
    # ===============================================
    
    async def get_cache_entry(self, level: str, context_id: str) -> Optional[Dict[str, Any]]:
        """Get cache entry"""
        try:
            result = self._execute_query(
                """
                SELECT context_id, context_level, resolved_context, dependencies_hash,
                       resolution_path, created_at, expires_at, hit_count, last_hit,
                       cache_size_bytes, invalidated, invalidation_reason
                FROM context_inheritance_cache 
                WHERE context_level = ? AND context_id = ?
                """,
                (level, context_id),
                fetch_one=True
            )
            
            if not result:
                return None
            
            return {
                "context_id": result["context_id"],
                "context_level": result["context_level"],
                "resolved_context": json.loads(result["resolved_context"]) if result["resolved_context"] else {},
                "dependencies_hash": result["dependencies_hash"],
                "resolution_path": result["resolution_path"],
                "created_at": result["created_at"],
                "expires_at": result["expires_at"],
                "hit_count": result["hit_count"],
                "last_hit": result["last_hit"],
                "cache_size_bytes": result["cache_size_bytes"],
                "invalidated": result["invalidated"],
                "invalidation_reason": result["invalidation_reason"]
            }
            
        except Exception as e:
            logger.error(f"Error getting cache entry {level}:{context_id}: {e}")
            return None
    
    async def store_cache_entry(self, cache_data: Dict[str, Any]) -> bool:
        """Store cache entry"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO context_inheritance_cache (
                        context_id, context_level, resolved_context, dependencies_hash,
                        resolution_path, created_at, expires_at, hit_count, last_hit,
                        cache_size_bytes, invalidated, invalidation_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_data["context_id"],
                    cache_data["context_level"],
                    json.dumps(cache_data["resolved_context"]),
                    cache_data["dependencies_hash"],
                    cache_data["resolution_path"],
                    cache_data["created_at"],
                    cache_data["expires_at"],
                    cache_data["hit_count"],
                    cache_data["last_hit"],
                    cache_data["cache_size_bytes"],
                    cache_data["invalidated"],
                    cache_data.get("invalidation_reason")
                ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing cache entry: {e}")
            return False
    
    async def invalidate_cache_entry(self, level: str, context_id: str, reason: str) -> bool:
        """Invalidate cache entry"""
        try:
            rows_affected = self._execute_update(
                """
                UPDATE context_inheritance_cache 
                SET invalidated = ?, invalidation_reason = ?
                WHERE context_level = ? AND context_id = ?
                """,
                (True, reason, level, context_id)
            )
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache entry {level}:{context_id}: {e}")
            return False
    
    async def remove_cache_entry(self, level: str, context_id: str) -> bool:
        """Remove cache entry"""
        try:
            rows_affected = self._execute_update(
                """
                DELETE FROM context_inheritance_cache 
                WHERE context_level = ? AND context_id = ?
                """,
                (level, context_id)
            )
            return True
            
        except Exception as e:
            logger.error(f"Error removing cache entry {level}:{context_id}: {e}")
            return False
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            result = self._execute_query(
                """
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(cache_size_bytes) as total_size_bytes,
                    SUM(hit_count) as total_hits,
                    COUNT(CASE WHEN invalidated = 1 THEN 1 END) as invalidated_count,
                    COUNT(CASE WHEN expires_at < datetime('now') THEN 1 END) as expired_count
                FROM context_inheritance_cache
                """,
                fetch_one=True
            )
            
            return {
                "total_entries": result["total_entries"] or 0,
                "total_size_bytes": result["total_size_bytes"] or 0,
                "total_hits": result["total_hits"] or 0,
                "invalidated_count": result["invalidated_count"] or 0,
                "expired_count": result["expired_count"] or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {}
    
    # ===============================================
    # ADDITIONAL CACHE METHODS
    # ===============================================
    
    async def get_cache_entries_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get all cache entries for a specific level"""
        try:
            rows = self._execute_query(
                """
                SELECT context_id, context_level, cache_size_bytes, hit_count,
                       created_at, expires_at, invalidated
                FROM context_inheritance_cache 
                WHERE context_level = ?
                """,
                (level,)
            )
            
            return [
                {
                    "context_id": row["context_id"],
                    "context_level": row["context_level"],
                    "cache_size_bytes": row["cache_size_bytes"],
                    "hit_count": row["hit_count"],
                    "created_at": row["created_at"],
                    "expires_at": row["expires_at"],
                    "invalidated": row["invalidated"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting cache entries by level {level}: {e}")
            return []
    
    async def get_task_caches_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get task cache entries for a specific project"""
        try:
            rows = self._execute_query(
                """
                SELECT c.context_id, c.context_level, c.cache_size_bytes, c.hit_count,
                       c.created_at, c.expires_at, c.invalidated
                FROM context_inheritance_cache c
                INNER JOIN task_contexts t ON c.context_id = t.task_id
                WHERE c.context_level = 'task' AND t.parent_project_id = ?
                """,
                (project_id,)
            )
            
            return [
                {
                    "context_id": row["context_id"],
                    "context_level": row["context_level"],
                    "cache_size_bytes": row["cache_size_bytes"],
                    "hit_count": row["hit_count"],
                    "created_at": row["created_at"],
                    "expires_at": row["expires_at"],
                    "invalidated": row["invalidated"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting task caches by project {project_id}: {e}")
            return []
    
    async def get_expired_cache_entries(self, current_time: datetime) -> List[Dict[str, Any]]:
        """Get expired cache entries"""
        try:
            rows = self._execute_query(
                """
                SELECT context_id, context_level, cache_size_bytes, expires_at
                FROM context_inheritance_cache 
                WHERE expires_at < ?
                """,
                (current_time.isoformat(),)
            )
            
            return [
                {
                    "context_id": row["context_id"],
                    "context_level": row["context_level"],
                    "cache_size_bytes": row["cache_size_bytes"],
                    "expires_at": row["expires_at"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting expired cache entries: {e}")
            return []
    
    async def get_invalidated_cache_entries(self) -> List[Dict[str, Any]]:
        """Get invalidated cache entries"""
        try:
            rows = self._execute_query(
                """
                SELECT context_id, context_level, cache_size_bytes, invalidation_reason
                FROM context_inheritance_cache 
                WHERE invalidated = 1
                """
            )
            
            return [
                {
                    "context_id": row["context_id"],
                    "context_level": row["context_level"],
                    "cache_size_bytes": row["cache_size_bytes"],
                    "invalidation_reason": row["invalidation_reason"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting invalidated cache entries: {e}")
            return []
    
    async def clear_all_cache_entries(self) -> int:
        """Clear all cache entries and return count"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM context_inheritance_cache")
                count = cursor.fetchone()[0]
                
                cursor.execute("DELETE FROM context_inheritance_cache")
                conn.commit()
                
                return count
                
        except Exception as e:
            logger.error(f"Error clearing all cache entries: {e}")
            return 0
    
    async def update_cache_stats(self, level: str, context_id: str, stats: Dict[str, Any]) -> bool:
        """Update cache statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                params = []
                
                for field, value in stats.items():
                    if field == "hit_count":
                        # Handle increment
                        set_clauses.append(f"{field} = {field} + ?")
                        params.append(1)
                    else:
                        set_clauses.append(f"{field} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return True
                
                params.extend([level, context_id])
                
                query = f"""
                    UPDATE context_inheritance_cache 
                    SET {', '.join(set_clauses)}
                    WHERE context_level = ? AND context_id = ?
                """
                
                cursor.execute(query, params)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating cache stats: {e}")
            return False
    
    async def get_top_hit_cache_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top hit cache entries"""
        try:
            rows = self._execute_query(
                """
                SELECT context_id, context_level, hit_count, last_hit,
                       cache_size_bytes, created_at
                FROM context_inheritance_cache 
                ORDER BY hit_count DESC, last_hit DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            return [
                {
                    "context_id": row["context_id"],
                    "context_level": row["context_level"],
                    "hit_count": row["hit_count"],
                    "last_hit": row["last_hit"],
                    "cache_size_bytes": row["cache_size_bytes"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting top hit cache entries: {e}")
            return []
    
    async def get_low_hit_cache_entries(self, hit_threshold: int = 2, limit: int = 50) -> List[Dict[str, Any]]:
        """Get low hit cache entries for cleanup"""
        try:
            rows = self._execute_query(
                """
                SELECT context_id, context_level, hit_count, cache_size_bytes,
                       created_at, last_hit
                FROM context_inheritance_cache 
                WHERE hit_count <= ?
                ORDER BY hit_count ASC, created_at ASC
                LIMIT ?
                """,
                (hit_threshold, limit)
            )
            
            return [
                {
                    "context_id": row["context_id"],
                    "context_level": row["context_level"],
                    "hit_count": row["hit_count"],
                    "cache_size_bytes": row["cache_size_bytes"],
                    "created_at": row["created_at"],
                    "last_hit": row["last_hit"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting low hit cache entries: {e}")
            return []
    
    # ===============================================
    # HEALTH CHECK METHOD
    # ===============================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the repository.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Check database connection
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                # Check table existence
                tables_query = """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN (
                        'global_contexts', 'project_contexts', 'task_contexts',
                        'context_delegations', 'context_inheritance_cache'
                    )
                """
                cursor.execute(tables_query)
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                expected_tables = {
                    'global_contexts', 'project_contexts', 'task_contexts',
                    'context_delegations', 'context_inheritance_cache'
                }
                missing_tables = expected_tables - existing_tables
                
                # Get row counts for each table
                table_stats = {}
                for table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_stats[table] = count
                
                # Get cache statistics
                cache_stats = await self.get_cache_statistics()
                
                # Get delegation queue size
                cursor.execute("""
                    SELECT COUNT(*) FROM context_delegations 
                    WHERE processed = 0
                """)
                pending_delegations = cursor.fetchone()[0]
                
                # Overall health assessment
                status = "healthy"
                issues = []
                
                if missing_tables:
                    status = "degraded"
                    issues.append(f"Missing tables: {', '.join(missing_tables)}")
                
                # Check if cache is too large (more than 10000 entries)
                if cache_stats.get("total_entries", 0) > 10000:
                    status = "warning"
                    issues.append(f"Cache size large: {cache_stats['total_entries']} entries")
                
                # Check if too many pending delegations (more than 100)
                if pending_delegations > 100:
                    status = "warning"
                    issues.append(f"High pending delegations: {pending_delegations}")
                
                return {
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "database": {
                        "connected": True,
                        "path": self._db_path,
                        "tables": {
                            "expected": len(expected_tables),
                            "found": len(existing_tables),
                            "missing": list(missing_tables)
                        },
                        "row_counts": table_stats
                    },
                    "cache": {
                        "total_entries": cache_stats.get("total_entries", 0),
                        "total_size_bytes": cache_stats.get("total_size_bytes", 0),
                        "total_hits": cache_stats.get("total_hits", 0),
                        "invalidated_count": cache_stats.get("invalidated_count", 0),
                        "expired_count": cache_stats.get("expired_count", 0)
                    },
                    "delegations": {
                        "pending_count": pending_delegations
                    },
                    "issues": issues if issues else None
                }
                
        except Exception as e:
            logger.error(f"Error during health check: {e}", exc_info=True)
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "database": {
                    "connected": False
                }
            }