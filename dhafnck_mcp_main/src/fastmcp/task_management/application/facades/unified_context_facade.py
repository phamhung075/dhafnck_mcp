"""
Unified Context Application Facade

Orchestrates unified context operations across all levels while maintaining
proper DDD boundaries and providing a clean interface for the Interface layer.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..services.unified_context_service import UnifiedContextService
from ...domain.exceptions.base_exceptions import ValidationException

logger = logging.getLogger(__name__)


class UnifiedContextFacade:
    """
    Application Facade for unified context management.
    
    Provides a high-level interface for all context operations across
    the entire hierarchy (Global → Project → Branch → Task) while
    coordinating services and handling cross-cutting concerns.
    """
    
    def __init__(
        self,
        unified_service: UnifiedContextService,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        git_branch_id: Optional[str] = None
    ):
        """
        Initialize facade with unified context service and scope.
        
        Args:
            unified_service: The unified context service
            user_id: User identifier for context scoping
            project_id: Project identifier for context scoping
            git_branch_id: Git branch UUID for context scoping
        """
        self._service = unified_service
        self._user_id = user_id
        self._project_id = project_id
        self._git_branch_id = git_branch_id
        
        logger.info(f"UnifiedContextFacade initialized for user={user_id}, project={project_id}, branch={git_branch_id}")
    
    def _run_sync(self, func_call):
        """Execute a sync function call directly."""
        return func_call
    
    def _add_scope_to_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add scope information to context data if not already present."""
        if not data:
            data = {}
        
        # Add scope info if available and not already present
        if self._user_id and "user_id" not in data:
            data["user_id"] = self._user_id
        if self._project_id and "project_id" not in data:
            data["project_id"] = self._project_id
        if self._git_branch_id and "git_branch_id" not in data:
            data["git_branch_id"] = self._git_branch_id
            
        return data
    
    def create_context(
        self,
        level: str,
        context_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new context at the specified level.
        
        Args:
            level: Context level (global, project, branch, task)
            context_id: Context identifier
            data: Context data
            
        Returns:
            Response dict with created context
        """
        try:
            # Add scope to data
            data = self._add_scope_to_data(data or {})
            
            # Call sync service
            result = self._service.create_context(level, context_id, data)
            
            return result
            
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
        """
        Get context with optional inheritance.
        
        Args:
            level: Context level
            context_id: Context identifier
            include_inherited: Include inherited context from parents
            force_refresh: Force refresh from source
            
        Returns:
            Response dict with context data
        """
        try:
            result = self._service.get_context(
                level, context_id, include_inherited, force_refresh
            )
            
            return result
            
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
        """
        Update existing context.
        
        Args:
            level: Context level
            context_id: Context identifier
            data: Update data
            propagate_changes: Propagate changes to dependent contexts
            
        Returns:
            Response dict with updated context
        """
        try:
            # Add scope to data
            data = self._add_scope_to_data(data)
            
            result = self._service.update_context(
                level, context_id, data, propagate_changes
            )
            
            return result
            
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
        """
        Delete context.
        
        Args:
            level: Context level
            context_id: Context identifier
            
        Returns:
            Response dict confirming deletion
        """
        try:
            result = self._service.delete_context(level, context_id)
            
            return result
            
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
        """
        Resolve context with full inheritance chain.
        
        Args:
            level: Context level
            context_id: Context identifier
            force_refresh: Force refresh from source
            
        Returns:
            Response dict with resolved context including inheritance
        """
        try:
            result = self._service.resolve_context(level, context_id, force_refresh)
            
            return result
            
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
        """
        Delegate context data to a higher level.
        
        Args:
            level: Source context level
            context_id: Source context identifier
            delegate_to: Target level for delegation
            data: Data to delegate
            delegation_reason: Reason for delegation
            
        Returns:
            Response dict with delegation result
        """
        try:
            result = self._service.delegate_context(
                level, context_id, delegate_to, data, delegation_reason
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delegate context: {e}")
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
        importance: Optional[str] = None,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an insight to context.
        
        Args:
            level: Context level
            context_id: Context identifier
            content: Insight content
            category: Insight category
            importance: Importance level
            agent: Agent identifier
            
        Returns:
            Response dict with updated context
        """
        try:
            result = self._service.add_insight(
                level, context_id, content, category, importance, agent
            )
            
            return result
            
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
        """
        Add progress update to context.
        
        Args:
            level: Context level
            context_id: Context identifier
            content: Progress description
            agent: Agent identifier
            
        Returns:
            Response dict with updated context
        """
        try:
            result = self._service.add_progress(
                level, context_id, content, agent
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add progress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_contexts(
        self,
        level: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List contexts at the specified level.
        
        Args:
            level: Context level
            filters: Optional filters to apply
            
        Returns:
            Response dict with list of contexts
        """
        try:
            # Add scope to filters
            if not filters:
                filters = {}
            
            if self._user_id:
                filters["user_id"] = self._user_id
            if self._project_id:
                filters["project_id"] = self._project_id
            if self._git_branch_id:
                filters["git_branch_id"] = self._git_branch_id
            
            result = self._service.list_contexts(level, filters)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list contexts: {e}")
            return {
                "success": False,
                "error": str(e)
            }