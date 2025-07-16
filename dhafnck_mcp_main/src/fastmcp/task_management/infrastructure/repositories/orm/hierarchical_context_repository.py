"""ORM Hierarchical Context Repository Implementation"""

import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, delete, func, and_, or_

from ..base_orm_repository import BaseORMRepository
from ...database.models import (
    GlobalContext, ProjectContext, TaskContext, 
    ContextDelegation, ContextInheritanceCache
)
from ...logging import TaskManagementLogger, log_operation

logger = TaskManagementLogger.get_logger(__name__)


class ORMHierarchicalContextRepository(BaseORMRepository):
    """
    ORM-based implementation of Hierarchical Context Repository.
    
    Provides data access methods for:
    - Global contexts (singleton)
    - Project contexts (inheriting from global)
    - Task contexts (inheriting from project)
    - Delegation queue management
    - Cache management
    """
    
    # ===============================================
    # GLOBAL CONTEXT OPERATIONS
    # ===============================================
    
    @log_operation("create_global_context")
    def create_global_context(self, global_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create global context"""
        try:
            logger.info(f"Creating global context with id: {global_id}")
            
            with self.get_session() as session:
                # Check if context already exists
                existing = session.get(GlobalContext, global_id)
                if existing:
                    # Update existing context
                    existing.organization_id = data.get("organization_id", existing.organization_id)
                    existing.autonomous_rules = data.get("autonomous_rules", existing.autonomous_rules)
                    existing.security_policies = data.get("security_policies", existing.security_policies)
                    existing.coding_standards = data.get("coding_standards", existing.coding_standards)
                    existing.workflow_templates = data.get("workflow_templates", existing.workflow_templates)
                    existing.delegation_rules = data.get("delegation_rules", existing.delegation_rules)
                    existing.updated_at = datetime.now(timezone.utc)
                    existing.version += 1
                else:
                    # Create new context
                    context = GlobalContext(
                        id=global_id,
                        organization_id=data.get("organization_id", "default_org"),
                        autonomous_rules=data.get("autonomous_rules", {}),
                        security_policies=data.get("security_policies", {}),
                        coding_standards=data.get("coding_standards", {}),
                        workflow_templates=data.get("workflow_templates", {}),
                        delegation_rules=data.get("delegation_rules", {}),
                        version=1
                    )
                    session.add(context)
                
                session.commit()
                
                logger.debug(f"Successfully created global context: {global_id}")
                
                # Return the created context
                return self.get_global_context(global_id)
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating global context {global_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating global context {global_id}: {e}", exc_info=True)
            raise
    
    def get_global_context(self, global_id: str = "global_singleton") -> Optional[Dict[str, Any]]:
        """Get global context (singleton)"""
        try:
            with self.get_session() as session:
                context = session.get(GlobalContext, global_id)
                if not context:
                    return None
                
                return {
                    "id": context.id,
                    "organization_id": context.organization_id,
                    "autonomous_rules": context.autonomous_rules,
                    "security_policies": context.security_policies,
                    "coding_standards": context.coding_standards,
                    "workflow_templates": context.workflow_templates,
                    "delegation_rules": context.delegation_rules,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "version": context.version
                }
                
        except Exception as e:
            logger.error(f"Error getting global context: {e}")
            return None
    
    def update_global_context(self, global_id: str, updates: Dict[str, Any]) -> bool:
        """Update global context"""
        try:
            with self.get_session() as session:
                context = session.get(GlobalContext, global_id)
                if not context:
                    # Create context if it doesn't exist
                    default_data = {
                        "autonomous_rules": {},
                        "security_policies": {},
                        "coding_standards": {},
                        "workflow_templates": {},
                        "delegation_rules": {},
                        "organization_id": "default_org"
                    }
                    return self.create_global_context(global_id, default_data) is not None
                
                # Update fields
                if "autonomous_rules" in updates:
                    # Handle custom data by merging with existing autonomous_rules
                    custom_data = {k: v for k, v in updates.items() 
                                 if k not in ["autonomous_rules", "security_policies", "coding_standards", 
                                            "workflow_templates", "delegation_rules", "organization_id"]}
                    if custom_data:
                        merged_rules = context.autonomous_rules.copy()
                        merged_rules.update(custom_data)
                        context.autonomous_rules = merged_rules
                    else:
                        context.autonomous_rules = updates["autonomous_rules"]
                
                for field in ["security_policies", "coding_standards", "workflow_templates", "delegation_rules"]:
                    if field in updates:
                        setattr(context, field, updates[field])
                
                if "organization_id" in updates:
                    context.organization_id = updates["organization_id"]
                
                context.updated_at = datetime.now(timezone.utc)
                context.version += 1
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating global context: {e}")
            return False
    
    def delete_global_context(self, global_id: str) -> bool:
        """Delete global context"""
        try:
            with self.get_session() as session:
                context = session.get(GlobalContext, global_id)
                if context:
                    session.delete(context)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting global context: {e}")
            return False
    
    def list_global_contexts(self) -> List[Dict[str, Any]]:
        """List all global contexts"""
        try:
            with self.get_session() as session:
                contexts = session.execute(select(GlobalContext)).scalars().all()
                
                return [
                    {
                        "id": ctx.id,
                        "organization_id": ctx.organization_id,
                        "autonomous_rules": ctx.autonomous_rules,
                        "security_policies": ctx.security_policies,
                        "coding_standards": ctx.coding_standards,
                        "workflow_templates": ctx.workflow_templates,
                        "delegation_rules": ctx.delegation_rules,
                        "created_at": ctx.created_at.isoformat(),
                        "updated_at": ctx.updated_at.isoformat(),
                        "version": ctx.version
                    }
                    for ctx in contexts
                ]
                
        except Exception as e:
            logger.error(f"Error listing global contexts: {e}")
            return []
    
    # ===============================================
    # PROJECT CONTEXT OPERATIONS
    # ===============================================
    
    def create_project_context(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project context"""
        try:
            with self.get_session() as session:
                # Check if context already exists
                existing = session.get(ProjectContext, project_id)
                if existing:
                    # Update existing context
                    existing.parent_global_id = data.get("parent_global_id", existing.parent_global_id)
                    existing.team_preferences = data.get("team_preferences", existing.team_preferences)
                    existing.technology_stack = data.get("technology_stack", existing.technology_stack)
                    existing.project_workflow = data.get("project_workflow", existing.project_workflow)
                    existing.local_standards = data.get("local_standards", existing.local_standards)
                    existing.global_overrides = data.get("global_overrides", existing.global_overrides)
                    existing.delegation_rules = data.get("delegation_rules", existing.delegation_rules)
                    existing.inheritance_disabled = data.get("inheritance_disabled", existing.inheritance_disabled)
                    existing.updated_at = datetime.now(timezone.utc)
                    existing.version += 1
                else:
                    # Create new context
                    context = ProjectContext(
                        project_id=project_id,
                        parent_global_id=data.get("parent_global_id", "global_singleton"),
                        team_preferences=data.get("team_preferences", {}),
                        technology_stack=data.get("technology_stack", {}),
                        project_workflow=data.get("project_workflow", {}),
                        local_standards=data.get("local_standards", {}),
                        global_overrides=data.get("global_overrides", {}),
                        delegation_rules=data.get("delegation_rules", {}),
                        inheritance_disabled=data.get("inheritance_disabled", False),
                        version=1
                    )
                    session.add(context)
                
                session.commit()
                
                # Return the created context
                return self.get_project_context(project_id)
                
        except Exception as e:
            logger.error(f"Error creating project context: {e}")
            raise
    
    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project context"""
        try:
            with self.get_session() as session:
                context = session.get(ProjectContext, project_id)
                if not context:
                    return None
                
                return {
                    "project_id": context.project_id,
                    "parent_global_id": context.parent_global_id,
                    "team_preferences": context.team_preferences,
                    "technology_stack": context.technology_stack,
                    "project_workflow": context.project_workflow,
                    "local_standards": context.local_standards,
                    "global_overrides": context.global_overrides,
                    "delegation_rules": context.delegation_rules,
                    "inheritance_disabled": context.inheritance_disabled,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "version": context.version
                }
                
        except Exception as e:
            logger.error(f"Error getting project context {project_id}: {e}")
            return None
    
    def update_project_context(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project context"""
        try:
            with self.get_session() as session:
                context = session.get(ProjectContext, project_id)
                if not context:
                    return False
                
                # Update fields
                for field in ["team_preferences", "technology_stack", "project_workflow", 
                           "local_standards", "global_overrides", "delegation_rules"]:
                    if field in updates:
                        setattr(context, field, updates[field])
                
                if "parent_global_id" in updates:
                    context.parent_global_id = updates["parent_global_id"]
                
                if "inheritance_disabled" in updates:
                    context.inheritance_disabled = updates["inheritance_disabled"]
                
                context.updated_at = datetime.now(timezone.utc)
                context.version += 1
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating project context {project_id}: {e}")
            return False
    
    def delete_project_context(self, project_id: str) -> bool:
        """Delete project context"""
        try:
            with self.get_session() as session:
                context = session.get(ProjectContext, project_id)
                if context:
                    session.delete(context)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting project context: {e}")
            return False
    
    def list_project_contexts(self) -> List[Dict[str, Any]]:
        """List all project contexts"""
        try:
            with self.get_session() as session:
                contexts = session.execute(select(ProjectContext)).scalars().all()
                
                return [
                    {
                        "project_id": ctx.project_id,
                        "parent_global_id": ctx.parent_global_id,
                        "team_preferences": ctx.team_preferences,
                        "technology_stack": ctx.technology_stack,
                        "project_workflow": ctx.project_workflow,
                        "local_standards": ctx.local_standards,
                        "global_overrides": ctx.global_overrides,
                        "delegation_rules": ctx.delegation_rules,
                        "inheritance_disabled": ctx.inheritance_disabled,
                        "created_at": ctx.created_at.isoformat(),
                        "updated_at": ctx.updated_at.isoformat(),
                        "version": ctx.version
                    }
                    for ctx in contexts
                ]
                
        except Exception as e:
            logger.error(f"Error listing project contexts: {e}")
            return []
    
    # ===============================================
    # TASK CONTEXT OPERATIONS
    # ===============================================
    
    def create_task_context(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task context"""
        try:
            with self.get_session() as session:
                # Extract project ID from data or use default
                project_id = data.get("parent_project_id", "default_project")
                project_context_id = data.get("parent_project_context_id", project_id)
                
                # Check if context already exists
                existing = session.get(TaskContext, task_id)
                if existing:
                    # Update existing context
                    existing.parent_project_id = project_id
                    existing.parent_project_context_id = project_context_id
                    existing.task_data = data.get("task_data", existing.task_data)
                    existing.local_overrides = data.get("local_overrides", existing.local_overrides)
                    existing.implementation_notes = data.get("implementation_notes", existing.implementation_notes)
                    existing.delegation_triggers = data.get("delegation_triggers", existing.delegation_triggers)
                    existing.inheritance_disabled = data.get("inheritance_disabled", existing.inheritance_disabled)
                    existing.force_local_only = data.get("force_local_only", existing.force_local_only)
                    existing.updated_at = datetime.now(timezone.utc)
                    existing.version += 1
                else:
                    # Create new context
                    context = TaskContext(
                        task_id=task_id,
                        parent_project_id=project_id,
                        parent_project_context_id=project_context_id,
                        task_data=data.get("task_data", {}),
                        local_overrides=data.get("local_overrides", {}),
                        implementation_notes=data.get("implementation_notes", {}),
                        delegation_triggers=data.get("delegation_triggers", {}),
                        inheritance_disabled=data.get("inheritance_disabled", False),
                        force_local_only=data.get("force_local_only", False),
                        version=1
                    )
                    session.add(context)
                
                session.commit()
                
                # Return the created context
                return self.get_task_context(task_id)
                
        except Exception as e:
            logger.error(f"Error creating task context: {e}")
            raise
    
    def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task context"""
        try:
            with self.get_session() as session:
                context = session.get(TaskContext, task_id)
                if not context:
                    return None
                
                return {
                    "task_id": context.task_id,
                    "parent_project_id": context.parent_project_id,
                    "parent_project_context_id": context.parent_project_context_id,
                    "task_data": context.task_data,
                    "local_overrides": context.local_overrides,
                    "implementation_notes": context.implementation_notes,
                    "delegation_triggers": context.delegation_triggers,
                    "inheritance_disabled": context.inheritance_disabled,
                    "force_local_only": context.force_local_only,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "version": context.version
                }
                
        except Exception as e:
            logger.error(f"Error getting task context {task_id}: {e}")
            return None
    
    def update_task_context(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task context"""
        try:
            with self.get_session() as session:
                context = session.get(TaskContext, task_id)
                if not context:
                    return False
                
                # Update fields
                for field in ["task_data", "local_overrides", "implementation_notes", "delegation_triggers"]:
                    if field in updates:
                        setattr(context, field, updates[field])
                
                for field in ["parent_project_id", "parent_project_context_id", 
                           "inheritance_disabled", "force_local_only"]:
                    if field in updates:
                        setattr(context, field, updates[field])
                
                context.updated_at = datetime.now(timezone.utc)
                context.version += 1
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating task context {task_id}: {e}")
            return False
    
    def delete_task_context(self, task_id: str) -> bool:
        """Delete task context"""
        try:
            with self.get_session() as session:
                context = session.get(TaskContext, task_id)
                if context:
                    session.delete(context)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting task context: {e}")
            return False
    
    def list_task_contexts(self) -> List[Dict[str, Any]]:
        """List all task contexts"""
        try:
            with self.get_session() as session:
                contexts = session.execute(select(TaskContext)).scalars().all()
                
                return [
                    {
                        "task_id": ctx.task_id,
                        "parent_project_id": ctx.parent_project_id,
                        "parent_project_context_id": ctx.parent_project_context_id,
                        "task_data": ctx.task_data,
                        "local_overrides": ctx.local_overrides,
                        "implementation_notes": ctx.implementation_notes,
                        "delegation_triggers": ctx.delegation_triggers,
                        "inheritance_disabled": ctx.inheritance_disabled,
                        "force_local_only": ctx.force_local_only,
                        "created_at": ctx.created_at.isoformat(),
                        "updated_at": ctx.updated_at.isoformat(),
                        "version": ctx.version
                    }
                    for ctx in contexts
                ]
                
        except Exception as e:
            logger.error(f"Error listing task contexts: {e}")
            return []
    
    # ===============================================
    # DELEGATION OPERATIONS
    # ===============================================
    
    async def store_delegation(self, delegation_data: Dict[str, Any]) -> str:
        """Store delegation request and return delegation ID"""
        try:
            delegation_id = str(uuid.uuid4())
            
            with self.get_session() as session:
                delegation = ContextDelegation(
                    id=delegation_id,
                    source_level=delegation_data["source_level"],
                    source_id=delegation_data["source_id"],
                    target_level=delegation_data["target_level"],
                    target_id=delegation_data["target_id"],
                    delegated_data=delegation_data["delegated_data"],
                    delegation_reason=delegation_data["reason"],
                    trigger_type=delegation_data["trigger_type"],
                    auto_delegated=delegation_data.get("auto_delegated", False),
                    confidence_score=delegation_data.get("confidence_score"),
                    processed=False,
                    approved=None
                )
                session.add(delegation)
                session.commit()
                
                return delegation_id
                
        except Exception as e:
            logger.error(f"Error storing delegation: {e}")
            raise
    
    async def get_delegation(self, delegation_id: str) -> Optional[Dict[str, Any]]:
        """Get delegation by ID"""
        try:
            with self.get_session() as session:
                delegation = session.get(ContextDelegation, delegation_id)
                if not delegation:
                    return None
                
                return {
                    "id": delegation.id,
                    "source_level": delegation.source_level,
                    "source_id": delegation.source_id,
                    "target_level": delegation.target_level,
                    "target_id": delegation.target_id,
                    "delegated_data": delegation.delegated_data,
                    "delegation_reason": delegation.delegation_reason,
                    "trigger_type": delegation.trigger_type,
                    "auto_delegated": delegation.auto_delegated,
                    "confidence_score": delegation.confidence_score,
                    "processed": delegation.processed,
                    "approved": delegation.approved,
                    "processed_by": delegation.processed_by,
                    "rejected_reason": delegation.rejected_reason,
                    "created_at": delegation.created_at.isoformat(),
                    "processed_at": delegation.processed_at.isoformat() if delegation.processed_at else None
                }
                
        except Exception as e:
            logger.error(f"Error getting delegation {delegation_id}: {e}")
            return None
    
    async def get_delegations(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get delegations with filters"""
        try:
            with self.get_session() as session:
                query = select(ContextDelegation)
                
                # Apply filters
                for field, value in filters.items():
                    if field in ["source_level", "target_level", "trigger_type", "processed", "approved"]:
                        query = query.where(getattr(ContextDelegation, field) == value)
                    elif field in ["source_id", "target_id"]:
                        query = query.where(getattr(ContextDelegation, field) == value)
                
                query = query.order_by(ContextDelegation.created_at.desc())
                
                delegations = session.execute(query).scalars().all()
                
                return [
                    {
                        "id": del_.id,
                        "source_level": del_.source_level,
                        "source_id": del_.source_id,
                        "target_level": del_.target_level,
                        "target_id": del_.target_id,
                        "delegated_data": del_.delegated_data,
                        "delegation_reason": del_.delegation_reason,
                        "trigger_type": del_.trigger_type,
                        "auto_delegated": del_.auto_delegated,
                        "confidence_score": del_.confidence_score,
                        "processed": del_.processed,
                        "approved": del_.approved,
                        "processed_by": del_.processed_by,
                        "rejected_reason": del_.rejected_reason,
                        "created_at": del_.created_at.isoformat(),
                        "processed_at": del_.processed_at.isoformat() if del_.processed_at else None
                    }
                    for del_ in delegations
                ]
                
        except Exception as e:
            logger.error(f"Error getting delegations: {e}")
            return []
    
    async def update_delegation(self, delegation_id: str, updates: Dict[str, Any]) -> bool:
        """Update delegation"""
        try:
            with self.get_session() as session:
                delegation = session.get(ContextDelegation, delegation_id)
                if not delegation:
                    return False
                
                # Update fields
                for field in ["processed", "approved", "processed_by", "rejected_reason"]:
                    if field in updates:
                        setattr(delegation, field, updates[field])
                
                if "processed_at" in updates:
                    delegation.processed_at = updates["processed_at"]
                elif updates.get("processed"):
                    delegation.processed_at = datetime.now(timezone.utc)
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating delegation {delegation_id}: {e}")
            return False
    
    # ===============================================
    # CACHE OPERATIONS
    # ===============================================
    
    async def get_cache_entry(self, level: str, context_id: str) -> Optional[Dict[str, Any]]:
        """Get cache entry"""
        try:
            with self.get_session() as session:
                cache_entry = session.get(ContextInheritanceCache, (context_id, level))
                if not cache_entry:
                    return None
                
                return {
                    "context_id": cache_entry.context_id,
                    "context_level": cache_entry.context_level,
                    "resolved_context": cache_entry.resolved_context,
                    "dependencies_hash": cache_entry.dependencies_hash,
                    "resolution_path": cache_entry.resolution_path,
                    "created_at": cache_entry.created_at.isoformat(),
                    "expires_at": cache_entry.expires_at.isoformat(),
                    "hit_count": cache_entry.hit_count,
                    "last_hit": cache_entry.last_hit.isoformat(),
                    "cache_size_bytes": cache_entry.cache_size_bytes,
                    "invalidated": cache_entry.invalidated,
                    "invalidation_reason": cache_entry.invalidation_reason
                }
                
        except Exception as e:
            logger.error(f"Error getting cache entry {level}:{context_id}: {e}")
            return None
    
    async def store_cache_entry(self, cache_data: Dict[str, Any]) -> bool:
        """Store cache entry"""
        try:
            with self.get_session() as session:
                cache_entry = ContextInheritanceCache(
                    context_id=cache_data["context_id"],
                    context_level=cache_data["context_level"],
                    resolved_context=cache_data["resolved_context"],
                    dependencies_hash=cache_data["dependencies_hash"],
                    resolution_path=cache_data["resolution_path"],
                    created_at=datetime.fromisoformat(cache_data["created_at"]),
                    expires_at=datetime.fromisoformat(cache_data["expires_at"]),
                    hit_count=cache_data["hit_count"],
                    last_hit=datetime.fromisoformat(cache_data["last_hit"]),
                    cache_size_bytes=cache_data["cache_size_bytes"],
                    invalidated=cache_data["invalidated"],
                    invalidation_reason=cache_data.get("invalidation_reason")
                )
                session.merge(cache_entry)
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing cache entry: {e}")
            return False
    
    async def invalidate_cache_entry(self, level: str, context_id: str, reason: str) -> bool:
        """Invalidate cache entry"""
        try:
            with self.get_session() as session:
                cache_entry = session.get(ContextInheritanceCache, (context_id, level))
                if cache_entry:
                    cache_entry.invalidated = True
                    cache_entry.invalidation_reason = reason
                    session.commit()
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error invalidating cache entry {level}:{context_id}: {e}")
            return False
    
    async def remove_cache_entry(self, level: str, context_id: str) -> bool:
        """Remove cache entry"""
        try:
            with self.get_session() as session:
                cache_entry = session.get(ContextInheritanceCache, (context_id, level))
                if cache_entry:
                    session.delete(cache_entry)
                    session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error removing cache entry {level}:{context_id}: {e}")
            return False
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    select(
                        func.count(ContextInheritanceCache.context_id).label("total_entries"),
                        func.sum(ContextInheritanceCache.cache_size_bytes).label("total_size_bytes"),
                        func.sum(ContextInheritanceCache.hit_count).label("total_hits"),
                        func.count().filter(ContextInheritanceCache.invalidated == True).label("invalidated_count"),
                        func.count().filter(ContextInheritanceCache.expires_at < datetime.now(timezone.utc)).label("expired_count")
                    )
                ).first()
                
                return {
                    "total_entries": result.total_entries or 0,
                    "total_size_bytes": result.total_size_bytes or 0,
                    "total_hits": result.total_hits or 0,
                    "invalidated_count": result.invalidated_count or 0,
                    "expired_count": result.expired_count or 0
                }
                
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {}
    
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
            with self.get_session() as session:
                # Test basic query
                session.execute(select(1)).scalar()
                
                # Get table counts
                table_stats = {
                    "global_contexts": session.execute(select(func.count(GlobalContext.id))).scalar(),
                    "project_contexts": session.execute(select(func.count(ProjectContext.project_id))).scalar(),
                    "task_contexts": session.execute(select(func.count(TaskContext.task_id))).scalar(),
                    "context_delegations": session.execute(select(func.count(ContextDelegation.id))).scalar(),
                    "context_inheritance_cache": session.execute(select(func.count(ContextInheritanceCache.context_id))).scalar()
                }
                
                # Get cache statistics
                cache_stats = await self.get_cache_statistics()
                
                # Get delegation queue size
                pending_delegations = session.execute(
                    select(func.count(ContextDelegation.id)).where(ContextDelegation.processed == False)
                ).scalar()
                
                # Overall health assessment
                status = "healthy"
                issues = []
                
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
                        "type": "orm",
                        "row_counts": table_stats
                    },
                    "cache": cache_stats,
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
                    "connected": False,
                    "type": "orm"
                }
            }
    
    # ===============================================
    # CONTEXT RESOLUTION AND INHERITANCE
    # ===============================================
    
    def resolve_context(self, level: str, context_id: str, 
                       include_inheritance: bool = True) -> Dict[str, Any]:
        """
        Resolve context with inheritance from parent levels.
        
        Args:
            level: Context level ('global', 'project', 'task')
            context_id: Context identifier
            include_inheritance: Whether to include inherited context
            
        Returns:
            Resolved context dictionary
        """
        try:
            resolved_context = {}
            
            if level == "global":
                global_context = self.get_global_context(context_id)
                if global_context:
                    resolved_context.update(global_context)
                    
            elif level == "project":
                project_context = self.get_project_context(context_id)
                if project_context:
                    resolved_context.update(project_context)
                    
                    # Include global context if inheritance is enabled
                    if include_inheritance and not project_context.get("inheritance_disabled", False):
                        global_context = self.get_global_context(project_context.get("parent_global_id", "global_singleton"))
                        if global_context:
                            # Merge global context first, then project overrides
                            merged_context = global_context.copy()
                            merged_context.update(project_context)
                            resolved_context = merged_context
                            
            elif level == "task":
                task_context = self.get_task_context(context_id)
                if task_context:
                    resolved_context.update(task_context)
                    
                    # Include project and global context if inheritance is enabled
                    if include_inheritance and not task_context.get("inheritance_disabled", False):
                        project_context = self.get_project_context(task_context.get("parent_project_context_id"))
                        if project_context and not project_context.get("inheritance_disabled", False):
                            global_context = self.get_global_context(project_context.get("parent_global_id", "global_singleton"))
                            
                            # Merge contexts in order: global -> project -> task
                            merged_context = {}
                            if global_context:
                                merged_context.update(global_context)
                            merged_context.update(project_context)
                            merged_context.update(task_context)
                            resolved_context = merged_context
            
            return resolved_context
            
        except Exception as e:
            logger.error(f"Error resolving context {level}:{context_id}: {e}")
            return {}
    
    def delegate_context(self, source_level: str, source_id: str, 
                        target_level: str, target_id: str,
                        delegate_data: Dict[str, Any], reason: str) -> bool:
        """
        Delegate context data from source to target level.
        
        Args:
            source_level: Source context level
            source_id: Source context ID
            target_level: Target context level
            target_id: Target context ID
            delegate_data: Data to delegate
            reason: Reason for delegation
            
        Returns:
            True if delegation was successful
        """
        try:
            delegation_data = {
                "source_level": source_level,
                "source_id": source_id,
                "target_level": target_level,
                "target_id": target_id,
                "delegated_data": delegate_data,
                "reason": reason,
                "trigger_type": "manual",
                "auto_delegated": False
            }
            
            # Store delegation for processing
            import asyncio
            delegation_id = asyncio.run(self.store_delegation(delegation_data))
            
            # Process delegation immediately for manual delegations
            if target_level == "global":
                # Update global context
                global_context = self.get_global_context(target_id)
                if global_context:
                    # Merge delegated data with existing autonomous_rules
                    merged_rules = global_context.get("autonomous_rules", {})
                    merged_rules.update(delegate_data)
                    self.update_global_context(target_id, {"autonomous_rules": merged_rules})
                    
            elif target_level == "project":
                # Update project context
                project_context = self.get_project_context(target_id)
                if project_context:
                    # Merge delegated data with existing local_standards
                    merged_standards = project_context.get("local_standards", {})
                    merged_standards.update(delegate_data)
                    self.update_project_context(target_id, {"local_standards": merged_standards})
            
            # Mark delegation as processed
            asyncio.run(self.update_delegation(delegation_id, {
                "processed": True,
                "approved": True,
                "processed_by": "system"
            }))
            
            return True
            
        except Exception as e:
            logger.error(f"Error delegating context: {e}")
            return False
    
    def search_contexts(self, query: str, levels: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search contexts across all levels.
        
        Args:
            query: Search query string
            levels: List of context levels to search ('global', 'project', 'task')
            
        Returns:
            List of matching contexts
        """
        try:
            results = []
            levels = levels or ["global", "project", "task"]
            
            if "global" in levels:
                global_contexts = self.list_global_contexts()
                for ctx in global_contexts:
                    if query.lower() in json.dumps(ctx).lower():
                        ctx["_level"] = "global"
                        results.append(ctx)
            
            if "project" in levels:
                project_contexts = self.list_project_contexts()
                for ctx in project_contexts:
                    if query.lower() in json.dumps(ctx).lower():
                        ctx["_level"] = "project"
                        results.append(ctx)
            
            if "task" in levels:
                task_contexts = self.list_task_contexts()
                for ctx in task_contexts:
                    if query.lower() in json.dumps(ctx).lower():
                        ctx["_level"] = "task"
                        results.append(ctx)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching contexts: {e}")
            return []
    
    def get_context_hierarchy(self, level: str, context_id: str) -> Dict[str, Any]:
        """
        Get complete context hierarchy for a given context.
        
        Args:
            level: Context level
            context_id: Context identifier
            
        Returns:
            Dictionary containing the complete hierarchy
        """
        try:
            hierarchy = {
                "global": None,
                "project": None,
                "task": None
            }
            
            if level == "task":
                task_context = self.get_task_context(context_id)
                if task_context:
                    hierarchy["task"] = task_context
                    project_context = self.get_project_context(task_context.get("parent_project_context_id"))
                    if project_context:
                        hierarchy["project"] = project_context
                        global_context = self.get_global_context(project_context.get("parent_global_id", "global_singleton"))
                        if global_context:
                            hierarchy["global"] = global_context
                            
            elif level == "project":
                project_context = self.get_project_context(context_id)
                if project_context:
                    hierarchy["project"] = project_context
                    global_context = self.get_global_context(project_context.get("parent_global_id", "global_singleton"))
                    if global_context:
                        hierarchy["global"] = global_context
                        
            elif level == "global":
                global_context = self.get_global_context(context_id)
                if global_context:
                    hierarchy["global"] = global_context
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Error getting context hierarchy: {e}")
            return {"global": None, "project": None, "task": None}
    
    def merge_contexts(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple contexts with proper precedence.
        
        Args:
            contexts: List of context dictionaries to merge
            
        Returns:
            Merged context dictionary
        """
        try:
            merged = {}
            
            # Sort contexts by level precedence (global -> project -> task)
            level_order = {"global": 0, "project": 1, "task": 2}
            sorted_contexts = sorted(contexts, key=lambda x: level_order.get(x.get("_level", "global"), 0))
            
            for context in sorted_contexts:
                for key, value in context.items():
                    if key.startswith("_"):
                        continue
                    
                    if isinstance(value, dict) and key in merged:
                        # Merge dictionaries
                        merged[key].update(value)
                    else:
                        # Override value
                        merged[key] = value
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging contexts: {e}")
            return {}