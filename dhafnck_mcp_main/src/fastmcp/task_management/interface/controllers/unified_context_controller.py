"""
Unified Context MCP Controller

This controller handles MCP tool registration for unified context management operations,
following DDD principles by delegating business logic to application services.
Provides a single manage_context tool for all context operations across the hierarchy.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Annotated, TYPE_CHECKING, Union
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
            Standardized response dict with consistent context field names
        """
        # Use the new context-specific formatter for consistent field names
        return StandardResponseFormatter.format_context_response(
            facade_response,
            operation=operation,
            standardize_field_names=True
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
    
    def _normalize_context_data(self, 
                               data: Optional[Union[str, Dict[str, Any]]] = None,
                               **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize context data from various input formats.
        
        Handles:
        1. JSON string: '{"title": "My Task", "description": "Task desc"}'
        2. Dictionary: {"title": "My Task", "description": "Task desc"}
        3. Legacy parameters: data_title="My Task", data_description="Task desc"
        
        Args:
            data: Either a JSON string or dictionary object
            **kwargs: Legacy data_* parameters
            
        Returns:
            Normalized dictionary or None
        """
        # If data is provided, handle it first
        if data is not None:
            if isinstance(data, str):
                try:
                    # Try to parse JSON string
                    parsed_data = json.loads(data)
                    if not isinstance(parsed_data, dict):
                        raise ValueError(f"JSON data must be an object, not {type(parsed_data).__name__}")
                    return parsed_data
                except json.JSONDecodeError as e:
                    # Provide helpful error message
                    raise ValueError(
                        f"Invalid JSON string in 'data' parameter: {str(e)}. "
                        f"Valid formats: data={{'title': 'My Title'}} or "
                        f"data='{json.dumps({'title': 'My Title'})}'"
                    )
            elif isinstance(data, dict):
                return data
            else:
                raise ValueError(
                    f"Parameter 'data' must be a dictionary object or JSON string, "
                    f"not {type(data).__name__}"
                )
        
        # Build from legacy data_* parameters
        context_data = {}
        for key, value in kwargs.items():
            if key.startswith('data_') and value is not None:
                field_name = key[5:]  # Remove 'data_' prefix
                context_data[field_name] = value
        
        return context_data if context_data else None
    
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
            data: Annotated[Optional[Union[str, Dict[str, Any]]], Field(description=self._get_param_description(context_desc, "data", "Context data (dictionary or JSON string)"))] = None,
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
                
                # Normalize context data from various input formats
                try:
                    normalized_data = self._normalize_context_data(
                        data=data,
                        data_title=data_title,
                        data_description=data_description,
                        data_status=data_status,
                        data_priority=data_priority,
                        data_tags=data_tags,
                        data_metadata=data_metadata
                    )
                    data = normalized_data
                except ValueError as e:
                    # Return user-friendly error with examples
                    return StandardResponseFormatter.create_error_response(
                        operation=f"manage_context.{action}",
                        error=str(e),
                        error_code="INVALID_PARAMETER_FORMAT",
                        metadata={
                            "suggestions": [
                                "Use a dictionary object: data={'title': 'My Title', 'description': 'My Description'}",
                                f"Or use a JSON string: data='{json.dumps({'title': 'My Title', 'description': 'My Description'})}'",
                                "Or use legacy parameters: data_title='My Title', data_description='My Description'"
                            ],
                            "examples": {
                                "dictionary_format": "manage_context(action='create', level='task', context_id='task-123', data={'title': 'My Task', 'description': 'Task description'})",
                                "json_string_format": "manage_context(action='create', level='task', context_id='task-123', data='{\"title\": \"My Task\", \"description\": \"Task description\"}')",
                                "legacy_format": "manage_context(action='create', level='task', context_id='task-123', data_title='My Task', data_description='Task description')"
                            }
                        }
                    )
                
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