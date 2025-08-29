"""
Project MCP Controller - Refactored Modular Implementation

This is the main entry point for the project MCP controller, now refactored into a modular 
architecture using factory pattern to maintain separation of concerns.
"""

import logging
from typing import Dict, Any, Optional, Annotated
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

# Import modular components
from .factories.operation_factory import ProjectOperationFactory

# Import existing dependencies
# Import the description directly from the local file
from .manage_project_description import MANAGE_PROJECT_DESCRIPTION
from ...utils.response_formatter import StandardResponseFormatter, ResponseStatus, ErrorCodes
from ....application.facades.project_application_facade import ProjectApplicationFacade
from fastmcp.task_management.infrastructure.factories.project_facade_factory import ProjectFacadeFactory
from ....domain.constants import validate_user_id
from ....domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)
from .....config.auth_config import AuthConfig
from ..auth_helper import get_authenticated_user_id, log_authentication_details

logger = logging.getLogger(__name__)

# Import user context utilities - REQUIRED for authentication
try:
    from fastmcp.auth.middleware.request_context_middleware import get_current_user_id
    from fastmcp.auth.mcp_integration.thread_context_manager import ContextPropagationMixin
except ImportError:
    # Use auth_helper which is already imported
    get_current_user_id = get_authenticated_user_id
    # Fallback mixin if thread context manager is not available
    class ContextPropagationMixin:
        def _run_async_with_context(self, async_func, *args, **kwargs):
            import asyncio
            import threading
            result = None
            exception = None
            def run_in_new_loop():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(async_func(*args, **kwargs))
                    finally:
                        new_loop.close()
                        asyncio.set_event_loop(None)
                except Exception as e:
                    exception = e
            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join()
            if exception:
                raise exception
            return result


class ProjectMCPController(ContextPropagationMixin):
    """
    Refactored Project MCP Controller with modular architecture.
    
    This controller now uses factory pattern to delegate operations to specialized handlers,
    maintaining the same interface while improving maintainability and separation of concerns.
    """

    def __init__(self, project_facade_factory: ProjectFacadeFactory):
        """Initialize the modular project MCP controller."""
        
        # Store facade factory
        self._project_facade_factory = project_facade_factory
        
        # Initialize response formatter
        self._response_formatter = StandardResponseFormatter()
        
        # Initialize modular operation factory
        self._operation_factory = ProjectOperationFactory(
            response_formatter=self._response_formatter
        )
        
        logger.info("ProjectMCPController initialized with modular architecture")

    def register_tools(self, mcp: "FastMCP"):
        """Register MCP tools with the server."""
        
        # Load description
        tool_description = MANAGE_PROJECT_DESCRIPTION
        
        async def manage_project(
            action: Annotated[str, "Project management action"],
            project_id: Annotated[Optional[str], "Project ID"] = None,
            name: Annotated[Optional[str], "Project name"] = None,
            description: Annotated[Optional[str], "Project description"] = None,
            force: Annotated[Optional[bool], "Force operation"] = False,
            user_id: Annotated[Optional[str], "User ID"] = None
        ) -> Dict[str, Any]:
            """Main project management function with all parameters."""
            return await self.manage_project(
                action=action, project_id=project_id, name=name,
                description=description, force=force, user_id=user_id
            )
        
        mcp.tool(description=tool_description)(manage_project)

    async def manage_project(self, action: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Main entry point for project management operations."""
        
        try:
            # Authentication
            user_id = get_authenticated_user_id(
                provided_user_id=user_id,
                operation_name=f"manage_project:{action}"
            )
            log_authentication_details(user_id, f"manage_project:{action}")
            
            # Get facade for request
            facade = self._get_facade_for_request(user_id)
            
            # Validate required fields for specific actions
            validation_error = self._validate_operation_parameters(action, **kwargs)
            if validation_error:
                return validation_error
            
            # Execute operation using factory
            result = await self._operation_factory.handle_operation(
                operation=action,
                facade=facade,
                user_id=user_id,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in manage_project {action}: {str(e)}")
            return self._response_formatter.create_error_response(
                operation=action,
                error=f"Project operation failed: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={"action": action}
            )

    def _get_facade_for_request(self, user_id: str = None) -> ProjectApplicationFacade:
        """Get appropriate facade for the request."""
        
        if not self._project_facade_factory:
            raise ValueError("ProjectFacadeFactory is required but not provided")
        
        # Create facade with user context
        return self._project_facade_factory.create_project_facade(user_id)

    def _validate_operation_parameters(self, action: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Validate parameters for specific operations."""
        
        # Validate required parameters
        if action == "create":
            if not kwargs.get('name'):
                return self._create_missing_field_error("name", action)
        
        elif action == "get":
            if not kwargs.get('project_id') and not kwargs.get('name'):
                return self._response_formatter.create_error_response(
                    operation=action,
                    error="Either 'project_id' or 'name' must be provided for get operation",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    metadata={"required_fields": ["project_id OR name"]}
                )
        
        elif action in ["update", "delete", "project_health_check", "cleanup_obsolete", 
                       "validate_integrity", "rebalance_agents"]:
            if not kwargs.get('project_id'):
                return self._create_missing_field_error("project_id", action)
        
        return None

    def _create_missing_field_error(self, field: str, action: str) -> Dict[str, Any]:
        """Create a standardized missing field error response."""
        
        return self._response_formatter.create_error_response(
            operation=action,
            error=f"Missing required field: {field}. Expected: A valid {field} string",
            error_code=ErrorCodes.VALIDATION_ERROR,
            metadata={
                "field": field,
                "hint": f"Include '{field}' in your request",
                "action": action
            }
        )