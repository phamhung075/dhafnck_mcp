"""
Unified Context MCP Controller

This controller handles MCP tool registration for unified context management operations,
following DDD principles by delegating business logic to application services.
Provides a single manage_context tool for all context operations across the hierarchy.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Annotated, TYPE_CHECKING
from datetime import datetime, timezone
from pydantic import Field

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

from .desc import description_loader
from ..utils.error_handler import UserFriendlyErrorHandler
from ..utils.response_formatter import StandardResponseFormatter, ResponseStatus

from ...application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from ...application.facades.unified_context_facade import UnifiedContextFacade

logger = logging.getLogger(__name__)


class UnifiedContextMCPController:
    """
    MCP Controller for unified context management operations.
    
    Handles only MCP protocol concerns and delegates business operations
    to the UnifiedContextFacade following proper DDD layer separation.
    """
    
    def __init__(self, unified_context_facade_factory: UnifiedContextFacadeFactory):
        """
        Initialize controller with unified context facade factory.
        
        Args:
            unified_context_facade_factory: Factory for creating unified context facades
        """
        self._facade_factory = unified_context_facade_factory
        logger.info("UnifiedContextMCPController initialized")
    
    def _standardize_facade_response(self, facade_response: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """
        Convert facade response to standardized format using StandardResponseFormatter.
        
        Args:
            facade_response: Raw response from facade
            operation: The operation that was performed
            
        Returns:
            Standardized response dict
        """
        # If the facade already returned a standardized response, pass it through
        if "success" in facade_response:
            return facade_response
            
        # Otherwise standardize it
        return StandardResponseFormatter.format_success(
            facade_response,
            operation=operation
        )
    
    def _get_param_description(self, desc: Dict[str, Any], param_name: str, default: str) -> str:
        """Get parameter description handling both flat and nested formats."""
        params = desc.get("parameters", {})
        param_value = params.get(param_name, default)
        
        # If it's a dict with 'description' key, extract it
        if isinstance(param_value, dict) and "description" in param_value:
            return param_value["description"]
        # Otherwise return as-is (flat string format)
        return str(param_value)
    
    def _get_context_management_descriptions(self) -> Dict[str, Any]:
        """Load and return context management tool descriptions."""
        try:
            # Load all descriptions and navigate to context descriptions
            all_desc = description_loader.get_all_descriptions()
            
            # Look for context descriptions in the 'context' subdirectory
            if "context" in all_desc and isinstance(all_desc["context"], dict):
                context_desc = all_desc["context"]
                # First try to find the unified context description
                if "manage_unified_context" in context_desc:
                    return context_desc["manage_unified_context"]
                # Fall back to manage_context if unified not found
                elif "manage_context" in context_desc:
                    return context_desc["manage_context"]
            
            # If not found, raise to trigger fallback
            raise ValueError("manage_context description not found")
            
        except Exception as e:
            logger.warning(f"Failed to load context descriptions: {e}, using minimal defaults")
            # Return minimal default descriptions if loading fails
            from .desc.context.manage_unified_context_description import (
                MANAGE_UNIFIED_CONTEXT_DESCRIPTION,
                MANAGE_UNIFIED_CONTEXT_PARAMETERS
            )
            return {
                "description": MANAGE_UNIFIED_CONTEXT_DESCRIPTION,
                "parameters": MANAGE_UNIFIED_CONTEXT_PARAMETERS
            }
    
    def register_tools(self, mcp: "FastMCP"):
        """Register unified context management tools with FastMCP."""
        
        # Get tool descriptions
        context_desc = self._get_context_management_descriptions()
        
        @mcp.tool(name="manage_context", description=context_desc.get("description", "Unified context management"))
        def manage_context(
            action: Annotated[str, Field(description=self._get_param_description(context_desc, "action", "Context management action"))],
            level: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "level", "Context level"))] = "task",
            context_id: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "context_id", "Context identifier"))] = None,
            data: Annotated[Optional[Dict[str, Any]], Field(description=self._get_param_description(context_desc, "data", "Context data"))] = None,
            user_id: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "user_id", "User identifier"))] = None,
            project_id: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "project_id", "Project identifier"))] = None,
            git_branch_id: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "git_branch_id", "Git branch UUID"))] = None,
            force_refresh: Annotated[Optional[bool], Field(description=self._get_param_description(context_desc, "force_refresh", "Force refresh"))] = False,
            include_inherited: Annotated[Optional[bool], Field(description=self._get_param_description(context_desc, "include_inherited", "Include inherited"))] = False,
            propagate_changes: Annotated[Optional[bool], Field(description=self._get_param_description(context_desc, "propagate_changes", "Propagate changes"))] = True,
            delegate_to: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "delegate_to", "Delegation target"))] = None,
            delegate_data: Annotated[Optional[Dict[str, Any]], Field(description=self._get_param_description(context_desc, "delegate_data", "Delegation data"))] = None,
            delegation_reason: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "delegation_reason", "Delegation reason"))] = None,
            content: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "content", "Content for insights/progress"))] = None,
            category: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "category", "Insight category"))] = None,
            importance: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "importance", "Importance level"))] = None,
            agent: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "agent", "Agent identifier"))] = None,
            filters: Annotated[Optional[Dict[str, Any]], Field(description=self._get_param_description(context_desc, "filters", "List filters"))] = None,
            # Legacy parameters for backward compatibility
            task_id: Annotated[Optional[str], Field(description="Legacy: Task ID (use context_id instead)")] = None,
            data_title: Annotated[Optional[str], Field(description="Legacy: Context title")] = None,
            data_description: Annotated[Optional[str], Field(description="Legacy: Context description")] = None,
            data_status: Annotated[Optional[str], Field(description="Legacy: Context status")] = None,
            data_priority: Annotated[Optional[str], Field(description="Legacy: Context priority")] = None,
            data_tags: Annotated[Optional[List[str]], Field(description="Legacy: Context tags")] = None,
            data_metadata: Annotated[Optional[Dict[str, Any]], Field(description="Legacy: Context metadata")] = None
        ) -> Dict[str, Any]:

            try:
                # Handle legacy parameter mapping
                if task_id and not context_id:
                    context_id = task_id
                
                # Reconstruct data from legacy parameters if needed
                if not data and any([data_title, data_description, data_status, 
                                     data_priority, data_tags, data_metadata]):
                    data = {}
                    if data_title:
                        data["title"] = data_title
                    if data_description:
                        data["description"] = data_description
                    if data_status:
                        data["status"] = data_status
                    if data_priority:
                        data["priority"] = data_priority
                    if data_tags:
                        data["tags"] = data_tags
                    if data_metadata:
                        data["metadata"] = data_metadata
                
                # Handle special case for delegation
                if action == "delegate" and delegate_data:
                    data = delegate_data
                
                # Create appropriate facade
                facade = self._facade_factory.create_facade(
                    user_id=user_id,
                    project_id=project_id,
                    git_branch_id=git_branch_id
                )
                
                # Execute the operation
                if action == "create":
                    response = facade.create_context(
                        level=level,
                        context_id=context_id,
                        data=data or {}
                    )
                
                elif action == "get":
                    response = facade.get_context(
                        level=level,
                        context_id=context_id,
                        include_inherited=include_inherited,
                        force_refresh=force_refresh
                    )
                
                elif action == "update":
                    response = facade.update_context(
                        level=level,
                        context_id=context_id,
                        data=data or {},
                        propagate_changes=propagate_changes
                    )
                
                elif action == "delete":
                    response = facade.delete_context(
                        level=level,
                        context_id=context_id
                    )
                
                elif action == "resolve":
                    response = facade.resolve_context(
                        level=level,
                        context_id=context_id,
                        force_refresh=force_refresh
                    )
                
                elif action == "delegate":
                    response = facade.delegate_context(
                        level=level,
                        context_id=context_id,
                        delegate_to=delegate_to,
                        data=data or {},
                        delegation_reason=delegation_reason
                    )
                
                elif action == "add_insight":
                    response = facade.add_insight(
                        level=level,
                        context_id=context_id,
                        content=content or "",
                        category=category,
                        importance=importance,
                        agent=agent
                    )
                
                elif action == "add_progress":
                    response = facade.add_progress(
                        level=level,
                        context_id=context_id,
                        content=content or "",
                        agent=agent
                    )
                
                elif action == "list":
                    response = facade.list_contexts(
                        level=level,
                        filters=filters
                    )
                
                else:
                    return StandardResponseFormatter.create_error_response(
                        operation=f"manage_context.{action}",
                        error=f"Unknown action: {action}. Valid actions: create, get, update, delete, resolve, delegate, add_insight, add_progress, list"
                    )
                
                # Standardize response
                return self._standardize_facade_response(response, f"manage_context.{action}")
                
            except ValueError as e:
                logger.warning(f"Validation error in manage_context: {e}")
                return StandardResponseFormatter.create_error_response(
                    operation=f"manage_context.{action}",
                    error=str(e),
                    error_code="VALIDATION_ERROR"
                )
            except Exception as e:
                logger.error(f"Error in manage_context: {e}", exc_info=True)
                return UserFriendlyErrorHandler.handle_error(
                    e,
                    operation=f"manage_context.{action}"
                )
        
        logger.info("Unified context management tools registered successfully")