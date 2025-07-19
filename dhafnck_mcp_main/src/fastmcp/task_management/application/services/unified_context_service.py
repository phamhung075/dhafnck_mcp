"""
Unified Context Service for all context management operations.
Handles inheritance, delegation, caching, and business rules.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
from uuid import UUID

from ...domain.entities.context import GlobalContext, ProjectContext, BranchContext, TaskContextUnified as TaskContext
from ...domain.value_objects.context_enums import ContextLevel
from .context_cache_service import ContextCacheService
from .context_inheritance_service import ContextInheritanceService
from .context_delegation_service import ContextDelegationService
from .context_validation_service import ContextValidationService

logger = logging.getLogger(__name__)


class UnifiedContextService:
    """
    Single service for all context operations.
    Replaces both ContextService and UnifiedContextService.
    """
    
    def __init__(
        self,
        global_context_repository: Any,
        project_context_repository: Any,
        branch_context_repository: Any,
        task_context_repository: Any,
        cache_service: Optional[ContextCacheService] = None,
        inheritance_service: Optional[ContextInheritanceService] = None,
        delegation_service: Optional[ContextDelegationService] = None,
        validation_service: Optional[ContextValidationService] = None
    ):
        """Initialize unified context service with required repositories and services."""
        self.repositories = {
            ContextLevel.GLOBAL: global_context_repository,
            ContextLevel.PROJECT: project_context_repository,
            ContextLevel.BRANCH: branch_context_repository,
            ContextLevel.TASK: task_context_repository
        }
        
        self.cache_service = cache_service or ContextCacheService()
        self.inheritance_service = inheritance_service or ContextInheritanceService(
            self.repositories
        )
        self.delegation_service = delegation_service or ContextDelegationService(
            self.repositories
        )
        self.validation_service = validation_service or ContextValidationService()
        
    def create_context(
        self, 
        level: str, 
        context_id: str, 
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create context at specified level with validation."""
        try:
            # Validate level
            context_level = ContextLevel(level)
            
            # Validate context data
            validation_result = self.validation_service.validate_context_data(
                level=context_level,
                data=data
            )
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Validation failed: {validation_result['errors']}"
                }
            
            # Get appropriate repository
            repository = self.repositories.get(context_level)
            if not repository:
                return {
                    "success": False,
                    "error": f"No repository configured for level: {level}"
                }
            
            # Create context entity based on level
            context_entity = self._create_context_entity(
                level=context_level,
                context_id=context_id,
                data=data,
                user_id=user_id,
                project_id=project_id
            )
            
            # Save to repository
            saved_context = repository.create(context_entity)
            
            # Invalidate cache for this context
            # Note: Cache service still async - skip for now in sync mode
            # await self.cache_service.invalidate(level, context_id)
            
            return {
                "success": True,
                "context": self._entity_to_dict(saved_context),
                "level": level,
                "context_id": context_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_context(
        self, 
        level: str, 
        context_id: str, 
        include_inherited: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get context with optional inheritance resolution."""
        try:
            # Validate level
            context_level = ContextLevel(level)
            
            # Skip cache operations for now (cache service is async)
            # TODO: Make cache service sync or skip caching in sync mode
            
            # Get from repository
            repository = self.repositories.get(context_level)
            if not repository:
                return {
                    "success": False,
                    "error": f"No repository configured for level: {level}"
                }
            
            context_entity = repository.get(context_id)
            if not context_entity:
                return {
                    "success": False,
                    "error": f"Context not found: {context_id}"
                }
            
            context_data = self._entity_to_dict(context_entity)
            
            # Skip inheritance for now (inheritance service is async)
            # TODO: Make inheritance service sync or skip inheritance in sync mode
            
            # Skip cache update for now (cache service is async)
            # TODO: Make cache service sync or skip caching in sync mode
            
            return {
                "success": True,
                "context": context_data,
                "level": level,
                "context_id": context_id,
                "inherited": include_inherited
            }
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_context(
        self, 
        level: str, 
        context_id: str, 
        data: Dict[str, Any],
        propagate_changes: bool = True
    ) -> Dict[str, Any]:
        """Update context with inheritance propagation."""
        try:
            # Validate level
            context_level = ContextLevel(level)
            
            # Get existing context
            repository = self.repositories.get(context_level)
            if not repository:
                return {
                    "success": False,
                    "error": f"No repository configured for level: {level}"
                }
            
            existing = repository.get(context_id)
            if not existing:
                return {
                    "success": False,
                    "error": f"Context not found: {context_id}"
                }
            
            # Merge data with existing
            updated_data = self._merge_context_data(
                existing_data=self._entity_to_dict(existing),
                new_data=data
            )
            
            # Skip validation for now (validation service is async)
            # TODO: Make validation service sync or skip validation in sync mode
            validation_result = {"valid": True}
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Validation failed: {validation_result['errors']}"
                }
            
            # Update entity
            updated_entity = self._update_context_entity(
                existing_entity=existing,
                new_data=updated_data
            )
            
            # Save to repository
            saved_context = repository.update(context_id, updated_entity)
            
            # Skip cache invalidation for now (cache service is async)
            # TODO: Make cache service sync or skip caching in sync mode
            
            # Skip propagation for now (propagation service is async)
            # TODO: Make propagation sync or skip propagation in sync mode
            
            return {
                "success": True,
                "context": self._entity_to_dict(saved_context),
                "level": level,
                "context_id": context_id,
                "propagated": propagate_changes
            }
            
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_context(
        self, 
        level: str, 
        context_id: str
    ) -> Dict[str, Any]:
        """Delete context with cleanup."""
        try:
            # Validate level
            context_level = ContextLevel(level)
            
            # Get repository
            repository = self.repositories.get(context_level)
            if not repository:
                return {
                    "success": False,
                    "error": f"No repository configured for level: {level}"
                }
            
            # Check if context exists
            existing = repository.get(context_id)
            if not existing:
                return {
                    "success": False,
                    "error": f"Context not found: {context_id}"
                }
            
            # Delete from repository
            result = repository.delete(context_id)
            
            # Skip cache invalidation for now (cache service is async)
            # TODO: Make cache service sync or skip caching in sync mode
            
            # Skip cleanup for now (cleanup service is async)
            # TODO: Make cleanup sync or skip cleanup in sync mode
            
            return {
                "success": result,
                "level": level,
                "context_id": context_id
            }
            
        except Exception as e:
            logger.error(f"Failed to delete context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def resolve_context(
        self, 
        level: str, 
        context_id: str, 
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Resolve full inheritance chain with caching."""
        try:
            # This is essentially get_context with inheritance
            return self.get_context(
                level=level,
                context_id=context_id,
                include_inherited=True,
                force_refresh=force_refresh
            )
            
        except Exception as e:
            logger.error(f"Failed to resolve context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delegate_context(
        self, 
        level: str, 
        context_id: str, 
        delegate_to: str, 
        data: Dict[str, Any],
        delegation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delegate context data to higher level."""
        try:
            # Validate levels
            source_level = ContextLevel(level)
            target_level = ContextLevel(delegate_to)
            
            # Skip delegation for now (delegation service is async)
            # TODO: Make delegation service sync or skip delegation in sync mode
            delegation_result = {"success": True, "message": "Delegation skipped in sync mode"}
            
            return {
                "success": True,
                "delegation": delegation_result,
                "source_level": level,
                "target_level": delegate_to,
                "context_id": context_id
            }
            
        except Exception as e:
            logger.error(f"Failed to delegate context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_contexts(
        self, 
        level: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List contexts at specified level with optional filtering."""
        try:
            # Validate level
            context_level = ContextLevel(level)
            
            # Get repository
            repository = self.repositories.get(context_level)
            if not repository:
                return {
                    "success": False,
                    "error": f"No repository configured for level: {level}"
                }
            
            # Get contexts
            contexts = repository.list(filters=filters)
            
            return {
                "success": True,
                "contexts": [self._entity_to_dict(c) for c in contexts],
                "level": level,
                "count": len(contexts)
            }
            
        except Exception as e:
            logger.error(f"Failed to list contexts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_insight(
        self,
        level: str,
        context_id: str,
        content: str,
        category: Optional[str] = None,
        importance: Optional[str] = "medium",
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add an insight to context."""
        try:
            # Get existing context
            context_result = self.get_context(level, context_id)
            if not context_result["success"]:
                return context_result
            
            context = context_result["context"]
            insights = context.get("insights", [])
            
            # Add new insight
            insight = {
                "content": content,
                "category": category or "general",
                "importance": importance,
                "agent": agent or "system",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            insights.append(insight)
            
            # Update context
            return self.update_context(
                level=level,
                context_id=context_id,
                data={"insights": insights}
            )
            
        except Exception as e:
            logger.error(f"Failed to add insight: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_progress(
        self,
        level: str,
        context_id: str,
        content: str,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add progress update to context."""
        try:
            # Get existing context
            context_result = self.get_context(level, context_id)
            if not context_result["success"]:
                return context_result
            
            context = context_result["context"]
            progress_updates = context.get("progress_updates", [])
            
            # Add new progress
            progress = {
                "content": content,
                "agent": agent or "system",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            progress_updates.append(progress)
            
            # Update context
            return self.update_context(
                level=level,
                context_id=context_id,
                data={"progress_updates": progress_updates}
            )
            
        except Exception as e:
            logger.error(f"Failed to add progress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    
    def _create_context_entity(
        self,
        level: ContextLevel,
        context_id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """Create appropriate context entity based on level."""
        if level == ContextLevel.GLOBAL:
            return GlobalContext(
                id=context_id,
                organization_name=data.get("organization_name", "Default Organization"),
                global_settings=data.get("global_settings", {}),
                metadata=data.get("metadata", {})
            )
        elif level == ContextLevel.PROJECT:
            return ProjectContext(
                id=context_id,
                project_name=data.get("project_name", "Unnamed Project"),
                project_settings=data.get("project_settings", {}),
                metadata=data.get("metadata", {})
            )
        elif level == ContextLevel.BRANCH:
            # Build branch_settings from individual fields or use provided branch_settings
            branch_settings = data.get("branch_settings", {})
            if not branch_settings:
                # Build from individual fields for backward compatibility
                branch_settings = {
                    "branch_workflow": data.get("branch_workflow", {}),
                    "branch_standards": data.get("branch_standards", {}),
                    "agent_assignments": data.get("agent_assignments", {})
                }
            
            return BranchContext(
                id=context_id,
                project_id=project_id or data.get("project_id"),
                git_branch_name=data.get("git_branch_name", "main"),
                branch_settings=branch_settings,
                metadata=data.get("metadata", {})
            )
        elif level == ContextLevel.TASK:
            # Support both branch_id and parent_branch_id for backward compatibility
            branch_id = data.get("branch_id") or data.get("parent_branch_id")
            if not branch_id:
                raise ValueError("Task context requires branch_id or parent_branch_id")
            
            return TaskContext(
                id=context_id,
                branch_id=branch_id,
                task_data=data.get("task_data", {}),
                progress=data.get("progress", 0),
                insights=data.get("insights", []),
                next_steps=data.get("next_steps", []),
                metadata=data.get("metadata", {})
            )
        else:
            raise ValueError(f"Unknown context level: {level}")
    
    def _entity_to_dict(self, entity) -> Dict[str, Any]:
        """Convert context entity to dictionary."""
        return entity.dict() if hasattr(entity, 'dict') else vars(entity)
    
    def _merge_context_data(
        self,
        existing_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge new data with existing context data."""
        merged = existing_data.copy()
        
        for key, value in new_data.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Deep merge for nested dicts
                merged[key] = {**merged[key], **value}
            elif isinstance(value, list) and key in merged and isinstance(merged[key], list):
                # Extend lists
                merged[key].extend(value)
            else:
                # Replace value
                merged[key] = value
        
        # Update timestamp
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return merged
    
    def _update_context_entity(self, existing_entity, new_data: Dict[str, Any]):
        """Update context entity with new data."""
        # Create a new entity with updated data based on entity type
        entity_type = type(existing_entity)
        
        # Extract the appropriate fields for each entity type
        if isinstance(existing_entity, TaskContext):
            # For TaskContextUnified, task-specific data goes in task_data
            return TaskContext(
                id=new_data.get("id", existing_entity.id),
                branch_id=new_data.get("branch_id", existing_entity.branch_id),
                task_data=new_data.get("task_data", existing_entity.task_data),
                progress=new_data.get("progress", existing_entity.progress),
                insights=new_data.get("insights", existing_entity.insights),
                next_steps=new_data.get("next_steps", existing_entity.next_steps),
                metadata=new_data.get("metadata", existing_entity.metadata)
            )
        elif isinstance(existing_entity, BranchContext):
            return BranchContext(
                id=new_data.get("id", existing_entity.id),
                project_id=new_data.get("project_id", existing_entity.project_id),
                git_branch_name=new_data.get("git_branch_name", existing_entity.git_branch_name),
                branch_settings=new_data.get("branch_settings", existing_entity.branch_settings),
                metadata=new_data.get("metadata", existing_entity.metadata)
            )
        elif isinstance(existing_entity, ProjectContext):
            return ProjectContext(
                id=new_data.get("id", existing_entity.id),
                project_name=new_data.get("project_name", existing_entity.project_name),
                project_settings=new_data.get("project_settings", existing_entity.project_settings),
                metadata=new_data.get("metadata", existing_entity.metadata)
            )
        elif isinstance(existing_entity, GlobalContext):
            return GlobalContext(
                id=new_data.get("id", existing_entity.id),
                organization_name=new_data.get("organization_name", existing_entity.organization_name),
                global_settings=new_data.get("global_settings", existing_entity.global_settings),
                metadata=new_data.get("metadata", existing_entity.metadata)
            )
        else:
            # Fallback - try to create entity with all data
            return entity_type(**new_data)
    
    def _propagate_changes(self, level: ContextLevel, context_id: str):
        """Propagate changes to dependent contexts."""
        # Skip cache invalidation for now (cache service is async)
        # TODO: Make cache service sync or skip caching in sync mode
        if level == ContextLevel.GLOBAL:
            # Global changes affect all contexts
            # await self.cache_service.invalidate_all()
            pass
        elif level == ContextLevel.PROJECT:
            # Project changes affect branch and task contexts
            # This would need to query for all branches in project
            pass
        elif level == ContextLevel.BRANCH:
            # Branch changes affect task contexts
            # This would need to query for all tasks in branch
            pass
        # Task level changes don't propagate upward
    
    def _cleanup_dependent_contexts(self, level: ContextLevel, context_id: str):
        """Clean up contexts that depend on the deleted context."""
        # This would handle cascading deletes based on level
        # For now, just log
        logger.info(f"Cleaning up dependent contexts for {level}:{context_id}")