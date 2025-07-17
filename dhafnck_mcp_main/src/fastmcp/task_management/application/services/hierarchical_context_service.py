"""
Hierarchical Context Service - Main orchestrator for multi-level context management

This service provides the core functionality for managing hierarchical contexts
across Global → Project → Task levels with inheritance and delegation capabilities.
"""

import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from dataclasses import dataclass

from .context_inheritance_service import ContextInheritanceService
from .context_delegation_service import ContextDelegationService
from .context_cache_service import ContextCacheService
from ...infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository
from ...infrastructure.repositories.hierarchical_context_repository_factory import HierarchicalContextRepositoryFactory

logger = logging.getLogger(__name__)

@dataclass
class ContextResolutionResult:
    """Result of context resolution with metadata"""
    resolved_context: Dict[str, Any]
    resolution_path: List[str]
    cache_hit: bool
    dependencies_hash: str
    resolution_time_ms: float

@dataclass
class PropagationResult:
    """Result of context change propagation"""
    affected_contexts: List[Tuple[str, str]]  # (level, id) pairs
    propagation_id: str
    success: bool
    error_details: Optional[str] = None

class HierarchicalContextService:
    """
    Main service for hierarchical context management.
    
    Orchestrates inheritance, delegation, caching, and propagation
    across Global → Project → Task context hierarchy.
    """
    
    def __init__(self, 
                 repository: Optional[ORMHierarchicalContextRepository] = None,
                 inheritance_service: Optional[ContextInheritanceService] = None,
                 delegation_service: Optional[ContextDelegationService] = None,
                 cache_service: Optional[ContextCacheService] = None):
        """Initialize hierarchical context service with dependencies"""
        if repository is None:
            factory = HierarchicalContextRepositoryFactory()
            self.repository = factory.create_hierarchical_context_repository()
        else:
            self.repository = repository
        self.inheritance_service = inheritance_service or ContextInheritanceService(repository=self.repository)
        self.delegation_service = delegation_service or ContextDelegationService(repository=self.repository)
        self.cache_service = cache_service or ContextCacheService(repository=self.repository)
        
        logger.info("HierarchicalContextService initialized")
    
    # ===============================================
    # CONTEXT CRUD OPERATIONS
    # ===============================================
    
    def create_context(self, level: str, context_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new context at the specified level.
        
        Args:
            level: Context level ('global', 'project', 'task')
            context_id: Context identifier
            data: Context data
            
        Returns:
            Created context
        """
        try:
            logger.info(f"Creating {level} context: {context_id}")
            
            if level == "global":
                result = self.repository.create_global_context(context_id, data)
            elif level == "project":
                result = self.repository.create_project_context(context_id, data)
            elif level == "task":
                result = self.repository.create_task_context(context_id, data)
            else:
                raise ValueError(f"Invalid context level: {level}")
            
            # Invalidate cache for new context
            self.cache_service.invalidate_context_cache(level, context_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating {level} context {context_id}: {e}", exc_info=True)
            raise
    
    def get_context(self, level: str, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a raw context without inheritance.
        
        Args:
            level: Context level
            context_id: Context identifier
            
        Returns:
            Raw context data or None
        """
        try:
            if level == "global":
                return self.repository.get_global_context(context_id)
            elif level == "project":
                return self.repository.get_project_context(context_id)
            elif level == "task":
                return self.repository.get_task_context(context_id)
            else:
                raise ValueError(f"Invalid context level: {level}")
                
        except Exception as e:
            logger.error(f"Error getting {level} context {context_id}: {e}", exc_info=True)
            raise
    
    def delete_context(self, level: str, context_id: str) -> bool:
        """
        Delete a context.
        
        Args:
            level: Context level
            context_id: Context identifier
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            logger.info(f"Deleting {level} context: {context_id}")
            
            if level == "global":
                result = self.repository.delete_global_context(context_id)
            elif level == "project":
                result = self.repository.delete_project_context(context_id)
            elif level == "task":
                result = self.repository.delete_task_context(context_id)
            else:
                raise ValueError(f"Invalid context level: {level}")
            
            # Invalidate cache
            self.cache_service.invalidate_context_cache(level, context_id)
            
            # Propagate deletion
            self.propagate_changes(level, context_id, {"_deleted": True})
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting {level} context {context_id}: {e}", exc_info=True)
            raise
    
    def list_contexts_by_level(self, level: str) -> List[Dict[str, Any]]:
        """
        List all contexts at a specific level.
        
        Args:
            level: Context level
            
        Returns:
            List of contexts
        """
        try:
            if level == "global":
                return self.repository.list_global_contexts()
            elif level == "project":
                return self.repository.list_project_contexts()
            elif level == "task":
                return self.repository.list_task_contexts()
            else:
                raise ValueError(f"Invalid context level: {level}")
                
        except Exception as e:
            logger.error(f"Error listing {level} contexts: {e}", exc_info=True)
            raise
    
    # ===============================================
    # CORE CONTEXT RESOLUTION
    # ===============================================
    
    async def resolve_full_context(self, level: str, context_id: str, 
                           force_refresh: bool = False) -> ContextResolutionResult:
        """
        Resolve complete context with full inheritance chain.
        
        Args:
            level: Context level ('task', 'project', 'global')
            context_id: Context identifier
            force_refresh: Skip cache and force fresh resolution
            
        Returns:
            ContextResolutionResult with resolved context and metadata
        """
        start_time = datetime.now()
        
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_result = await self.cache_service.get_cached_context(level, context_id)
                if cached_result:
                    logger.debug(f"Cache hit for {level}:{context_id}")
                    resolution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    return ContextResolutionResult(
                        resolved_context=cached_result['resolved_context'],
                        resolution_path=json.loads(cached_result['resolution_path']),
                        cache_hit=True,
                        dependencies_hash=cached_result['dependencies_hash'],
                        resolution_time_ms=resolution_time
                    )
            
            # Fresh resolution
            logger.debug(f"Resolving fresh context for {level}:{context_id}")
            
            if level == "global":
                result = self._resolve_global_context(context_id)
            elif level == "project":
                result = self._resolve_project_context(context_id)
            elif level == "task":
                result = self._resolve_task_context(context_id)
            else:
                raise ValueError(f"Invalid context level: {level}")
            
            # Cache the result
            await self.cache_service.cache_resolved_context(
                level=level,
                context_id=context_id,
                resolved_context=result.resolved_context,
                dependencies_hash=result.dependencies_hash,
                resolution_path=result.resolution_path
            )
            
            resolution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.resolution_time_ms = resolution_time
            result.cache_hit = False
            
            logger.info(f"Resolved {level}:{context_id} in {resolution_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error resolving context {level}:{context_id}: {e}", exc_info=True)
            raise
    
    def _resolve_global_context(self, context_id: str) -> ContextResolutionResult:
        """Resolve global context (no inheritance needed)"""
        global_context = self.repository.get_global_context(context_id)
        
        if not global_context:
            raise ValueError(f"Global context not found: {context_id}")
        
        # Global context is the root - no inheritance
        resolved = {
            "level": "global",
            "context_id": context_id,
            "autonomous_rules": global_context.get("autonomous_rules", {}),
            "security_policies": global_context.get("security_policies", {}),
            "coding_standards": global_context.get("coding_standards", {}),
            "workflow_templates": global_context.get("workflow_templates", {}),
            "delegation_rules": global_context.get("delegation_rules", {}),
            "metadata": {
                "version": global_context.get("version", 1),
                "updated_at": global_context.get("updated_at"),
                "organization_id": global_context.get("organization_id")
            }
        }
        
        dependencies_hash = self._calculate_dependencies_hash([global_context])
        
        return ContextResolutionResult(
            resolved_context=resolved,
            resolution_path=["global"],
            cache_hit=False,
            dependencies_hash=dependencies_hash,
            resolution_time_ms=0.0
        )
    
    def _resolve_project_context(self, project_id: str) -> ContextResolutionResult:
        """Resolve project context with global inheritance"""
        project_context = self.repository.get_project_context(project_id)
        
        if not project_context:
            raise ValueError(f"Project context not found: {project_id}")
        
        # Get global context for inheritance
        global_id = project_context.get("parent_global_id", "global_singleton")
        global_result = self._resolve_global_context(global_id)
        global_context = global_result.resolved_context
        
        # Apply inheritance
        resolved = self.inheritance_service.inherit_project_from_global(
            global_context=global_context,
            project_context=project_context
        )
        
        # Add project-specific metadata
        resolved.update({
            "level": "project",
            "context_id": project_id,
            "parent_global_id": global_id,
            "inheritance_disabled": project_context.get("inheritance_disabled", False)
        })
        
        dependencies_hash = self._calculate_dependencies_hash([global_context, project_context])
        resolution_path = ["global", "project"]
        
        return ContextResolutionResult(
            resolved_context=resolved,
            resolution_path=resolution_path,
            cache_hit=False,
            dependencies_hash=dependencies_hash,
            resolution_time_ms=0.0
        )
    
    def _resolve_task_context(self, task_id: str) -> ContextResolutionResult:
        """Resolve task context with full inheritance chain"""
        task_context = self.repository.get_task_context(task_id)
        
        if not task_context:
            raise ValueError(f"Task context not found: {task_id}")
        
        # Check if inheritance is disabled
        if task_context.get("inheritance_disabled", False):
            logger.debug(f"Inheritance disabled for task {task_id}, using local only")
            resolved = {
                "level": "task",
                "context_id": task_id,
                **task_context.get("task_data", {}),
                "local_overrides": task_context.get("local_overrides", {}),
                "inheritance_disabled": True
            }
            
            dependencies_hash = self._calculate_dependencies_hash([task_context])
            return ContextResolutionResult(
                resolved_context=resolved,
                resolution_path=["task_local_only"],
                cache_hit=False,
                dependencies_hash=dependencies_hash,
                resolution_time_ms=0.0
            )
        
        # Get project context for inheritance
        project_id = task_context.get("parent_project_context_id")
        project_result = self._resolve_project_context(project_id)
        project_context = project_result.resolved_context
        
        # Apply full inheritance chain
        resolved = self.inheritance_service.inherit_task_from_project(
            project_context=project_context,
            task_context=task_context
        )
        
        # Add task-specific metadata
        resolved.update({
            "level": "task",
            "context_id": task_id,
            "parent_project_id": task_context.get("parent_project_id"),
            "parent_project_context_id": project_id,
            "inheritance_disabled": False,
            "force_local_only": task_context.get("force_local_only", False)
        })
        
        dependencies_hash = self._calculate_dependencies_hash([
            project_context, task_context
        ])
        resolution_path = ["global", "project", "task"]
        
        return ContextResolutionResult(
            resolved_context=resolved,
            resolution_path=resolution_path,
            cache_hit=False,
            dependencies_hash=dependencies_hash,
            resolution_time_ms=0.0
        )
    
    # ===============================================
    # CONTEXT MODIFICATION AND PROPAGATION
    # ===============================================
    
    def update_context(self, level: str, context_id: str, 
                     changes: Dict[str, Any], 
                     propagate: bool = True) -> Dict[str, Any]:
        """
        Update context and optionally propagate changes.
        
        Args:
            level: Context level to update
            context_id: Context identifier  
            changes: Changes to apply
            propagate: Whether to propagate changes to dependent contexts
            
        Returns:
            Result of update operation
        """
        try:
            logger.info(f"Updating {level} context {context_id}")
            
            # Apply update based on level
            if level == "global":
                result = self.repository.update_global_context(context_id, changes)
            elif level == "project":
                result = self.repository.update_project_context(context_id, changes)
            elif level == "task":
                result = self.repository.update_task_context(context_id, changes)
            else:
                raise ValueError(f"Invalid context level: {level}")
            
            # Invalidate cache for this context
            self.cache_service.invalidate_context_cache(level, context_id)
            
            # Propagate changes if requested
            propagation_result = None
            if propagate:
                propagation_result = self.propagate_changes(level, context_id, changes)
            
            # Check for auto-delegation triggers
            self._check_delegation_triggers(level, context_id, changes)
            
            return {
                "success": True,
                "level": level,
                "context_id": context_id,
                "changes_applied": changes,
                "propagation": propagation_result.__dict__ if propagation_result else None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating {level} context {context_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "level": level,
                "context_id": context_id
            }
    
    def propagate_changes(self, source_level: str, source_id: str, 
                        changes: Dict[str, Any]) -> PropagationResult:
        """
        Propagate changes from source context to dependent contexts.
        
        Args:
            source_level: Level of source context
            source_id: ID of source context
            changes: Changes that triggered propagation
            
        Returns:
            PropagationResult with affected contexts
        """
        try:
            logger.info(f"Propagating changes from {source_level}:{source_id}")
            
            affected_contexts = []
            
            if source_level == "global":
                # Global changes affect all projects and tasks
                projects = self.repository.get_all_project_contexts() if hasattr(self.repository, 'get_all_project_contexts') else []
                for project in projects:
                    project_id = project["project_id"]
                    self.cache_service.invalidate_context_cache("project", project_id)
                    affected_contexts.append(("project", project_id))
                    
                    # Also affect all tasks in this project
                    tasks = self.repository.get_task_contexts_by_project(project_id) if hasattr(self.repository, 'get_task_contexts_by_project') else []
                    for task in tasks:
                        task_id = task["task_id"]
                        self.cache_service.invalidate_context_cache("task", task_id)
                        affected_contexts.append(("task", task_id))
            
            elif source_level == "project":
                # Project changes affect all tasks in the project
                tasks = self.repository.get_task_contexts_by_project(source_id) if hasattr(self.repository, 'get_task_contexts_by_project') else []
                for task in tasks:
                    task_id = task["task_id"]
                    self.cache_service.invalidate_context_cache("task", task_id)
                    affected_contexts.append(("task", task_id))
            
            # Log propagation (if repository supports it)
            if hasattr(self.repository, 'log_propagation'):
                propagation_id = self.repository.log_propagation(
                    source_level=source_level,
                    source_id=source_id,
                    change_type="update",
                    affected_contexts=affected_contexts,
                    changes_summary=changes
                )
            else:
                propagation_id = f"propagation_{source_level}_{source_id}_{datetime.now().timestamp()}"
            
            logger.info(f"Propagated changes to {len(affected_contexts)} contexts")
            
            return PropagationResult(
                affected_contexts=affected_contexts,
                propagation_id=propagation_id,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error propagating changes: {e}", exc_info=True)
            return PropagationResult(
                affected_contexts=[],
                propagation_id="",
                success=False,
                error_details=str(e)
            )
    
    # ===============================================
    # DELEGATION MANAGEMENT
    # ===============================================
    
    def delegate_context(self, from_level: str, from_id: str, 
                       to_level: str, data: Dict[str, Any], 
                       reason: str = "Manual delegation") -> Dict[str, Any]:
        """
        Delegate context data from lower level to higher level.
        
        Args:
            from_level: Source context level
            from_id: Source context ID
            to_level: Target context level
            data: Data to delegate
            reason: Reason for delegation
            
        Returns:
            Delegation result
        """
        try:
            logger.info(f"Delegating from {from_level}:{from_id} to {to_level}")
            
            # Validate delegation direction (can only delegate upward)
            level_hierarchy = {"task": 0, "project": 1, "global": 2}
            if level_hierarchy[from_level] >= level_hierarchy[to_level]:
                raise ValueError(f"Cannot delegate from {from_level} to {to_level} - must delegate upward")
            
            # Determine target ID based on hierarchy
            target_id = self._resolve_target_id(from_level, from_id, to_level)
            
            # Process delegation - handle async call in sync context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a new event loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.delegation_service.process_delegation(
                                source_level=from_level,
                                source_id=from_id,
                                target_level=to_level,
                                target_id=target_id,
                                delegated_data=data,
                                reason=reason
                            )
                        )
                        result = future.result()
                else:
                    # Normal case - run the async method
                    result = loop.run_until_complete(
                        self.delegation_service.process_delegation(
                            source_level=from_level,
                            source_id=from_id,
                            target_level=to_level,
                            target_id=target_id,
                            delegated_data=data,
                            reason=reason
                        )
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.delegation_service.process_delegation(
                        source_level=from_level,
                        source_id=from_id,
                        target_level=to_level,
                        target_id=target_id,
                        delegated_data=data,
                        reason=reason
                    )
                )
            
            # Invalidate affected caches (use sync version)
            self.cache_service.invalidate_context(to_level, target_id)
            
            logger.info(f"Delegation completed: {result.get('delegation_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in delegation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "from_level": from_level,
                "from_id": from_id,
                "to_level": to_level
            }
    
    def _check_delegation_triggers(self, level: str, context_id: str, 
                                  changes: Dict[str, Any]) -> None:
        """Check if changes trigger automatic delegation"""
        try:
            if level == "task":
                task_context = self.repository.get_task_context(context_id)
                delegation_triggers = task_context.get("delegation_triggers", {})
                
                # Check pattern-based triggers
                for pattern, target_level in delegation_triggers.get("patterns", {}).items():
                    if self._matches_delegation_pattern(changes, pattern):
                        self.delegate_context(
                            from_level="task",
                            from_id=context_id,
                            to_level=target_level,
                            data=self._extract_pattern_data(changes, pattern),
                            reason=f"Auto-delegation: {pattern} pattern detected"
                        )
                        
        except Exception as e:
            logger.warning(f"Error checking delegation triggers: {e}")
    
    # ===============================================
    # UTILITY METHODS
    # ===============================================
    
    def _calculate_dependencies_hash(self, contexts: List[Dict[str, Any]]) -> str:
        """Calculate hash of all dependencies for cache invalidation"""
        combined_data = json.dumps(contexts, sort_keys=True, default=str)
        return hashlib.sha256(combined_data.encode()).hexdigest()
    
    def _resolve_target_id(self, from_level: str, from_id: str, to_level: str) -> str:
        """Resolve target ID for delegation based on hierarchy"""
        if from_level == "task" and to_level == "project":
            task_context = self.repository.get_task_context(from_id)
            return task_context["parent_project_context_id"]
        elif from_level == "task" and to_level == "global":
            return "global_singleton"
        elif from_level == "project" and to_level == "global":
            return "global_singleton"
        else:
            raise ValueError(f"Invalid delegation path: {from_level} to {to_level}")
    
    def _matches_delegation_pattern(self, changes: Dict[str, Any], pattern: str) -> bool:
        """Check if changes match a delegation pattern"""
        # Implementation of pattern matching logic
        pattern_matchers = {
            "security_discovery": lambda c: any("security" in str(v).lower() for v in c.values()),
            "team_improvement": lambda c: any("team" in str(v).lower() or "process" in str(v).lower() for v in c.values()),
            "reusable_utility": lambda c: any("reusable" in str(v).lower() or "utility" in str(v).lower() for v in c.values()),
            "performance_optimization": lambda c: any("performance" in str(v).lower() or "optimization" in str(v).lower() for v in c.values())
        }
        
        matcher = pattern_matchers.get(pattern)
        return matcher(changes) if matcher else False
    
    def _extract_pattern_data(self, changes: Dict[str, Any], pattern: str) -> Dict[str, Any]:
        """Extract relevant data for pattern-based delegation"""
        return {
            "pattern": pattern,
            "extracted_data": changes,
            "extraction_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ===============================================
    # HEALTH AND MAINTENANCE
    # ===============================================
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of the hierarchical context system"""
        try:
            health = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "components": {}
            }
            
            # Check repository health
            health["components"]["repository"] = await self.repository.health_check() if hasattr(self.repository, 'health_check') else {"status": "ok"}
            
            # Check cache health
            if hasattr(self.cache_service, 'get_cache_stats'):
                try:
                    cache_stats = self.cache_service.get_cache_stats()
                    if asyncio.iscoroutine(cache_stats):
                        health["components"]["cache"] = await cache_stats
                    else:
                        health["components"]["cache"] = cache_stats
                except Exception as e:
                    health["components"]["cache"] = {"status": "error", "error": str(e)}
            else:
                health["components"]["cache"] = {"status": "ok"}
            
            # Check delegation queue
            if hasattr(self.delegation_service, 'get_queue_status'):
                try:
                    queue_status = self.delegation_service.get_queue_status()
                    if asyncio.iscoroutine(queue_status):
                        health["components"]["delegation"] = await queue_status
                    else:
                        health["components"]["delegation"] = queue_status
                except Exception as e:
                    health["components"]["delegation"] = {"status": "error", "error": str(e)}
            else:
                health["components"]["delegation"] = {"status": "ok"}
            
            # Overall status based on components
            if any(comp.get("status") == "error" for comp in health["components"].values()):
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries"""
        return self.cache_service.cleanup_expired() if hasattr(self.cache_service, 'cleanup_expired') else {"cleaned": 0}
    
    async def force_cache_rebuild(self, level: str = None, context_id: str = None) -> Dict[str, Any]:
        """Force rebuild of cache for specific context or all contexts"""
        try:
            if level and context_id:
                # Rebuild specific context
                self.cache_service.invalidate_context_cache(level, context_id)
                await self.resolve_full_context(level, context_id, force_refresh=True)
                return {"success": True, "rebuilt": f"{level}:{context_id}"}
            else:
                # Rebuild all caches
                self.cache_service.clear_all_cache() if hasattr(self.cache_service, 'clear_all_cache') else None
                return {"success": True, "rebuilt": "all_contexts"}
                
        except Exception as e:
            logger.error(f"Error rebuilding cache: {e}", exc_info=True)
            return {"success": False, "error": str(e)}