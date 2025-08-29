"""Unified Context MCP Controller - Modular Implementation

This is the modular implementation of the Unified Context MCP Controller, decomposed from
the original monolithic 362-line controller into specialized components.

This controller handles MCP tool registration for unified context management operations,
following DDD principles by delegating business logic to application services.
Provides a single manage_context tool for all context operations across the hierarchy.

The controller now uses:
- Factory Pattern for operation coordination
- Specialized Handlers for context operations
- Standardized Response Formatting
- Parameter validation and normalization
"""

import logging
import json
from typing import Dict, Any, Optional, Union, Annotated, TYPE_CHECKING
from pydantic import Field

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

from ..desc import description_loader
from ..auth_helper import get_authenticated_user_id
from ...utils.response_formatter import StandardResponseFormatter
from ...utils.parameter_validation_fix import coerce_parameter_types
from ...utils.json_parameter_parser import JSONParameterParser

from fastmcp.task_management.infrastructure.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from ....application.facades.unified_context_facade import UnifiedContextFacade

# Modular components
from .factories.operation_factory import ContextOperationFactory

logger = logging.getLogger(__name__)


class UnifiedContextMCPController:
    """
    MCP Controller for unified context management operations - Modular Implementation.
    
    Handles only MCP protocol concerns and delegates business operations
    to specialized handlers through the ContextOperationFactory following 
    proper DDD layer separation.
    """
    
    def __init__(self, unified_context_facade_factory: UnifiedContextFacadeFactory):
        """
        Initialize controller with unified context facade factory and modular components.
        
        Args:
            unified_context_facade_factory: Factory for creating unified context facades
        """
        self._facade_factory = unified_context_facade_factory
        
        # Initialize modular components
        self._response_formatter = StandardResponseFormatter()
        self._operation_factory = ContextOperationFactory(self._response_formatter)
        
        logger.info("UnifiedContextMCPController initialized with modular architecture")

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
                               data: Optional[Union[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Normalize context data from various input formats."""
        if data is None:
            return None
        
        if isinstance(data, dict):
            return data
        
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string in data parameter: {str(e)}")
        
        # Try to convert other types to dict if possible
        if hasattr(data, '__dict__'):
            return data.__dict__
        
        raise ValueError(f"Data parameter must be a dictionary or valid JSON string, got {type(data)}")

    def _get_context_management_descriptions(self) -> Dict[str, Any]:
        """Get context management descriptions from external files."""
        all_desc = description_loader.get_all_descriptions()
        flat = {}
        # Look for 'manage_context' in any subdict
        for sub in all_desc.values():
            if isinstance(sub, dict) and "manage_context" in sub:
                flat = sub["manage_context"]
                break
        return flat
    
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
            force_refresh: Annotated[Optional[Union[bool, str]], Field(description=self._get_param_description(context_desc, "force_refresh", "Force refresh (boolean or string)"))] = False,
            include_inherited: Annotated[Optional[Union[bool, str]], Field(description=self._get_param_description(context_desc, "include_inherited", "Include inherited (boolean or string)"))] = False,
            propagate_changes: Annotated[Optional[Union[bool, str]], Field(description=self._get_param_description(context_desc, "propagate_changes", "Propagate changes (boolean or string)"))] = True,
            delegate_to: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "delegate_to", "Delegation target"))] = None,
            delegate_data: Annotated[Optional[Union[str, Dict[str, Any]]], Field(description=self._get_param_description(context_desc, "delegate_data", "Delegation data (dictionary or JSON string)"))] = None,
            delegation_reason: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "delegation_reason", "Delegation reason"))] = None,
            content: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "content", "Content for insights/progress"))] = None,
            category: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "category", "Insight category"))] = None,
            importance: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "importance", "Importance level"))] = None,
            agent: Annotated[Optional[str], Field(description=self._get_param_description(context_desc, "agent", "Agent identifier"))] = None,
            filters: Annotated[Optional[Union[str, Dict[str, Any]]], Field(description=self._get_param_description(context_desc, "filters", "List filters (dictionary or JSON string)"))] = None
        ) -> Dict[str, Any]:

            try:
                # Apply parameter type coercion for boolean parameters
                boolean_params = {
                    'force_refresh': force_refresh,
                    'include_inherited': include_inherited,
                    'propagate_changes': propagate_changes
                }
                
                try:
                    coerced_params = coerce_parameter_types(boolean_params)
                    force_refresh = coerced_params.get('force_refresh', force_refresh)
                    include_inherited = coerced_params.get('include_inherited', include_inherited)
                    propagate_changes = coerced_params.get('propagate_changes', propagate_changes)
                except Exception as coercion_error:
                    logger.warning(f"Parameter coercion error: {coercion_error}")
                    # Continue with original values if coercion fails

                # Normalize context data from various input formats
                try:
                    normalized_data = self._normalize_context_data(data=data)
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
                                f"Or use a JSON string: data='{json.dumps({'title': 'My Title', 'description': 'My Description'})}'"
                            ]
                        }
                    )

                # Parse JSON strings for dictionary parameters
                try:
                    # Parse delegate_data if it's a JSON string
                    if delegate_data is not None:
                        delegate_data = JSONParameterParser.parse_dict_parameter(
                            delegate_data, "delegate_data"
                        )
                    
                    # Parse filters if it's a JSON string
                    if filters is not None:
                        filters = JSONParameterParser.parse_dict_parameter(
                            filters, "filters"
                        )
                except ValueError as e:
                    # Return user-friendly error with examples
                    return StandardResponseFormatter.create_error_response(
                        operation=f"manage_context.{action}",
                        error=str(e),
                        error_code="INVALID_PARAMETER_FORMAT"
                    )

                # Handle special case for delegation
                if action == "delegate" and delegate_data:
                    data = delegate_data

                # Get facade and delegate to operation factory
                facade = self._facade_factory.create_facade()
                
                return self._operation_factory.handle_operation(
                    facade=facade,
                    action=action,
                    level=level,
                    context_id=context_id,
                    data=data,
                    user_id=user_id,
                    project_id=project_id,
                    git_branch_id=git_branch_id,
                    force_refresh=force_refresh,
                    include_inherited=include_inherited,
                    propagate_changes=propagate_changes,
                    delegate_to=delegate_to,
                    delegate_data=delegate_data,
                    delegation_reason=delegation_reason,
                    content=content,
                    category=category,
                    importance=importance,
                    agent=agent,
                    filters=filters
                )

            except Exception as e:
                logger.error(f"Unified context management error: {e}")
                return StandardResponseFormatter.create_error_response(
                    operation=f"manage_context.{action}",
                    error=f"Context management failed: {str(e)}",
                    error_code="INTERNAL_ERROR"
                )