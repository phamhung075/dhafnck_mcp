"""
Task MCP Controller - Refactored Modular Implementation

This is the main entry point for the task MCP controller, now refactored into a modular 
architecture using factory pattern to maintain separation of concerns.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List, Annotated, Union
from datetime import datetime, timezone

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

# Import modular components
from .factories.operation_factory import OperationFactory
from .factories.validation_factory import ValidationFactory
from .factories.response_factory import ResponseFactory

# Import existing dependencies
from ..desc import description_loader
from ..workflow_hint_enhancer import WorkflowHintEnhancer
from ..workflow_guidance.task import TaskWorkflowFactory
from ...utils.error_handler import UserFriendlyErrorHandler
from ...utils.response_formatter import StandardResponseFormatter, ResponseStatus, ErrorCodes

from ....application.dtos.task.create_task_request import CreateTaskRequest
from ....application.dtos.task.list_tasks_request import ListTasksRequest
from ....application.dtos.task.search_tasks_request import SearchTasksRequest
from ....application.dtos.task.update_task_request import UpdateTaskRequest
from fastmcp.task_management.infrastructure.factories.unified_context_facade_factory import UnifiedContextFacadeFactory

from ....application.facades.task_application_facade import TaskApplicationFacade
from ....application.facades.unified_context_facade import UnifiedContextFacade
from fastmcp.task_management.infrastructure.factories.task_facade_factory import TaskFacadeFactory
# Services are created by factories with their required dependencies
from ....application.orchestrators.services.parameter_enforcement_service import (
    ParameterEnforcementService, 
    EnforcementLevel,
    EnforcementResult
)
from ....application.orchestrators.services.progressive_enforcement_service import ProgressiveEnforcementService
from ....application.orchestrators.services.response_enrichment_service import (
    ResponseEnrichmentService,
    ContextState,
    ContextStalnessLevel
)
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
    # Try alternative import path for RequestContextMiddleware
    try:
        from ..auth_helper import get_authenticated_user_id as get_current_user_id
    except ImportError:
        # Authentication is required - no fallbacks allowed
        from ....domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError
        def get_current_user_id():
            raise UserAuthenticationRequiredError("User context middleware not available")
    
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


class TaskMCPController(ContextPropagationMixin):
    """
    Refactored Task MCP Controller with modular architecture.
    
    This controller now uses factory pattern to delegate operations to specialized handlers,
    maintaining the same interface while improving maintainability and separation of concerns.
    """

    def __init__(self, 
                 facade_factory: Optional[TaskFacadeFactory] = None,
                 context_facade_factory: Optional[UnifiedContextFacadeFactory] = None,
                 workflow_hint_enhancer: Optional[WorkflowHintEnhancer] = None):
        """Initialize the modular task MCP controller."""
        
        # Initialize core dependencies
        self._facade_factory = facade_factory
        self._context_facade_factory = context_facade_factory
        self._workflow_hint_enhancer = workflow_hint_enhancer
        
        # Initialize response formatter and error handler
        self._response_formatter = StandardResponseFormatter()
        self._error_handler = UserFriendlyErrorHandler()
        
        # Initialize modular factories
        self._operation_factory = OperationFactory(
            response_formatter=self._response_formatter,
            context_facade_factory=context_facade_factory
        )
        
        self._validation_factory = ValidationFactory(
            response_formatter=self._response_formatter
        )
        
        self._response_factory = ResponseFactory(
            response_formatter=self._response_formatter
        )
        
        # Initialize workflow components
        workflow_factory = TaskWorkflowFactory()
        self._workflow_guidance = workflow_factory.create()
        
        # Note: Orchestrator services are created by factories as needed
        # They require repositories and other dependencies that are not available here
        
        # Initialize enforcement services
        self._enforcement_service = ParameterEnforcementService(EnforcementLevel.WARNING)
        self._progressive_enforcement = ProgressiveEnforcementService(
            enforcement_service=self._enforcement_service,
            default_level=EnforcementLevel.WARNING
        )
        
        # Initialize response enrichment service
        self._response_enrichment = ResponseEnrichmentService()
        
        logger.info("TaskMCPController initialized with modular architecture")
        
        # Store last known git_branch_id for context operations
        self._last_git_branch_id = None

    def register_tools(self, mcp: "FastMCP"):
        """Register MCP tools with the server."""
        
        # Load description
        tool_description = description_loader.get_task_manage_description()
        
        def manage_task(
            action: Annotated[str, "Action to perform: create, update, delete, get, list, search, next, complete, count"],
            task_id: Annotated[Optional[str], "Task ID for operations"] = None,
            git_branch_id: Annotated[Optional[str], "Git branch ID"] = None,
            title: Annotated[Optional[str], "Task title"] = None,
            description: Annotated[Optional[str], "Task description"] = None,
            status: Annotated[Optional[str], "Task status"] = None,
            priority: Annotated[Optional[str], "Task priority"] = None,
            details: Annotated[Optional[str], "Additional details"] = None,
            estimated_effort: Annotated[Optional[str], "Estimated effort"] = None,
            assignees: Annotated[Optional[List[str]], "Task assignees"] = None,
            labels: Annotated[Optional[List[str]], "Task labels"] = None,
            due_date: Annotated[Optional[str], "Due date"] = None,
            dependencies: Annotated[Optional[List[str]], "Task dependencies"] = None,
            context_id: Annotated[Optional[str], "Context ID"] = None,
            completion_summary: Annotated[Optional[str], "Completion summary"] = None,
            testing_notes: Annotated[Optional[str], "Testing notes"] = None,
            query: Annotated[Optional[str], "Search query"] = None,
            limit: Annotated[Optional[int], "Result limit"] = None,
            offset: Annotated[Optional[int], "Result offset"] = None,
            sort_by: Annotated[Optional[str], "Sort field"] = None,
            sort_order: Annotated[Optional[str], "Sort order"] = None,
            include_context: Annotated[Optional[bool], "Include context"] = False,
            assignee: Annotated[Optional[str], "Filter by assignee"] = None,
            tag: Annotated[Optional[str], "Filter by tag"] = None,
            user_id: Annotated[Optional[str], "User ID for operation"] = None
        ) -> Dict[str, Any]:
            """Main task management function with all parameters."""
            return self.manage_task(
                action=action, task_id=task_id, git_branch_id=git_branch_id,
                title=title, description=description, status=status, 
                priority=priority, details=details, estimated_effort=estimated_effort,
                assignees=assignees, labels=labels, due_date=due_date,
                dependencies=dependencies, context_id=context_id,
                completion_summary=completion_summary, testing_notes=testing_notes,
                query=query, limit=limit, offset=offset, sort_by=sort_by,
                sort_order=sort_order, include_context=include_context,
                assignee=assignee, tag=tag, user_id=user_id
            )
        
        mcp.tool(description=tool_description)(manage_task)

    def manage_task(self, *args, **kwargs):
        """Main entry point for task management operations."""
        return asyncio.run(self._async_manage_task(*args, **kwargs))

    async def _async_manage_task(self, action: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Async implementation of task management with modular architecture."""
        
        try:
            # Step 1: Authentication
            user_id = get_authenticated_user_id(
                provided_user_id=user_id,
                operation_name=f"manage_task:{action}"
            )
            log_authentication_details(user_id, f"manage_task:{action}")
            
            # Step 2: Get facade for request
            facade = self._get_facade_for_request(
                task_id=kwargs.get('task_id'),
                git_branch_id=kwargs.get('git_branch_id'),
                user_id=user_id
            )
            
            # Step 3: Validation using factory
            validation_result = self._validate_request(action, **kwargs)
            if not validation_result[0]:
                return validation_result[1]  # Return validation error
            
            # Step 4: Execute operation using factory
            result = self._operation_factory.handle_operation(
                operation=action,
                facade=facade,
                user_id=user_id,
                **kwargs
            )
            
            # Step 5: Standardize response using factory
            standardized_result = self._response_factory.standardize_facade_response(result, action)
            
            # Step 6: Apply workflow hints and enrichment
            if self._workflow_hint_enhancer and standardized_result.get("success"):
                enriched_result = await self._workflow_hint_enhancer.enhance_response(
                    response=standardized_result,
                    action=action,
                    context=kwargs
                )
                return enriched_result
            
            return standardized_result
            
        except Exception as e:
            logger.error(f"Error in manage_task {action}: {str(e)}")
            return self._response_factory.create_error_response(
                operation=action,
                error=str(e),
                error_code=ErrorCodes.OPERATION_FAILED
            )

    def _get_facade_for_request(self, task_id: Optional[str] = None, 
                               git_branch_id: Optional[str] = None, 
                               user_id: Optional[str] = None) -> TaskApplicationFacade:
        """Get appropriate facade for the request."""
        
        if not self._facade_factory:
            raise ValueError("TaskFacadeFactory is required but not provided")
        
        # Create facade with appropriate context
        if git_branch_id:
            return self._facade_factory.create_task_facade(git_branch_id, user_id)
        elif task_id:
            # For task-specific operations, create facade without specific branch
            return self._facade_factory.create_task_facade(None, user_id)
        else:
            # For general operations
            return self._facade_factory.create_task_facade(None, user_id)

    def _validate_request(self, action: str, **kwargs):
        """Validate request using validation factory."""
        
        if action == "create":
            return self._validation_factory.validate_create_request(
                title=kwargs.get('title'),
                git_branch_id=kwargs.get('git_branch_id'),
                description=kwargs.get('description'),
                status=kwargs.get('status'),
                priority=kwargs.get('priority'),
                due_date=kwargs.get('due_date'),
                assignees=kwargs.get('assignees'),
                labels=kwargs.get('labels'),
                dependencies=kwargs.get('dependencies')
            )
        elif action in ["update", "complete"]:
            return self._validation_factory.validate_update_request(
                task_id=kwargs.get('task_id'),
                **kwargs
            )
        elif action in ["list", "search"]:
            return self._validation_factory.validate_search_request(
                operation=action,
                query=kwargs.get('query'),
                **kwargs
            )
        elif action == "delete":
            return self._validation_factory.validate_deletion_request(
                task_id=kwargs.get('task_id')
            )
        else:
            # For other actions, basic validation
            return True, None