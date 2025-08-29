"""
Subtask MCP Controller - Refactored Modular Implementation

This is the main entry point for the subtask MCP controller, now refactored into a modular 
architecture using factory pattern to maintain separation of concerns and automatic progress tracking.
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
from .factories.operation_factory import SubtaskOperationFactory

# Import the description directly from the local file
from .manage_subtask_description import MANAGE_SUBTASK_DESCRIPTION
from ...utils.response_formatter import StandardResponseFormatter, ResponseStatus, ErrorCodes
from ...utils.parameter_validation_fix import coerce_parameter_types
from ...utils.schema_monkey_patch import apply_all_schema_patches

from ....application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.infrastructure.factories.subtask_facade_factory import SubtaskFacadeFactory
from ..workflow_guidance.subtask import SubtaskWorkflowFactory
from ..auth_helper import get_authenticated_user_id, log_authentication_details
from ....domain.constants import validate_user_id
from ....domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)
from .....config.auth_config import AuthConfig

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


class SubtaskMCPController(ContextPropagationMixin):
    """
    Refactored Subtask MCP Controller with modular architecture.
    
    This controller now uses factory pattern to delegate operations to specialized handlers,
    maintaining the same interface while improving maintainability and separation of concerns.
    Includes automatic progress tracking and parent task context updates.
    """

    def __init__(self, subtask_facade_factory: SubtaskFacadeFactory, 
                 task_facade=None, context_facade=None, task_repository_factory=None):
        """Initialize the modular subtask MCP controller."""
        
        # Initialize core dependencies
        self._subtask_facade_factory = subtask_facade_factory
        self._task_application_facade = task_facade
        self._context_facade = context_facade
        
        # Initialize response formatter
        self._response_formatter = StandardResponseFormatter()
        
        # Initialize modular operation factory
        self._operation_factory = SubtaskOperationFactory(
            response_formatter=self._response_formatter,
            context_facade=context_facade,
            task_facade=task_facade
        )
        
        # Initialize workflow guidance
        self._workflow_guidance = SubtaskWorkflowFactory.create()
        
        logger.info("SubtaskMCPController initialized with modular architecture and progress tracking")

    def _run_async(self, coro):
        """Run coroutine in async context with proper event loop management."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, run in a new thread with context
                async def _wrapper():
                    return await coro
                return self._run_async_with_context(_wrapper)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(coro)

    def register_tools(self, mcp: "FastMCP"):
        """Register MCP tools with the server."""
        
        # Load description
        tool_description = MANAGE_SUBTASK_DESCRIPTION
        
        def manage_subtask(
            action: Annotated[str, "Action: create, update, delete, get, list, complete"],
            task_id: Annotated[str, "Parent task ID"],
            subtask_id: Annotated[Optional[str], "Subtask ID for operations"] = None,
            title: Annotated[Optional[str], "Subtask title"] = None,
            description: Annotated[Optional[str], "Subtask description"] = None,
            status: Annotated[Optional[str], "Subtask status"] = None,
            priority: Annotated[Optional[str], "Subtask priority"] = None,
            assignees: Annotated[Optional[List[str]], "Subtask assignees"] = None,
            progress_percentage: Annotated[Optional[int], "Progress percentage (0-100)"] = None,
            progress_notes: Annotated[Optional[str], "Progress notes"] = None,
            completion_summary: Annotated[Optional[str], "Completion summary"] = None,
            testing_notes: Annotated[Optional[str], "Testing notes"] = None,
            insights_found: Annotated[Optional[List[str]], "Insights discovered"] = None,
            challenges_overcome: Annotated[Optional[List[str]], "Challenges faced"] = None,
            skills_learned: Annotated[Optional[List[str]], "Skills learned"] = None,
            next_recommendations: Annotated[Optional[List[str]], "Future recommendations"] = None,
            deliverables: Annotated[Optional[List[str]], "Deliverables created"] = None,
            completion_quality: Annotated[Optional[str], "Quality assessment"] = None,
            verification_status: Annotated[Optional[str], "Verification status"] = None,
            impact_on_parent: Annotated[Optional[str], "Impact on parent task"] = None,
            blockers: Annotated[Optional[str], "Current blockers"] = None,
            user_id: Annotated[Optional[str], "User ID for operation"] = None
        ) -> Dict[str, Any]:
            """Main subtask management function with all parameters."""
            return self.manage_subtask(
                action=action, task_id=task_id, subtask_id=subtask_id,
                title=title, description=description, status=status, 
                priority=priority, assignees=assignees, 
                progress_percentage=progress_percentage, progress_notes=progress_notes,
                completion_summary=completion_summary, testing_notes=testing_notes,
                insights_found=insights_found, challenges_overcome=challenges_overcome,
                skills_learned=skills_learned, next_recommendations=next_recommendations,
                deliverables=deliverables, completion_quality=completion_quality,
                verification_status=verification_status, impact_on_parent=impact_on_parent,
                blockers=blockers, user_id=user_id
            )
        
        mcp.tool(description=tool_description)(manage_subtask)

    def manage_subtask(self, action: str, task_id: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Main entry point for subtask management operations."""
        
        try:
            # Authentication
            user_id = get_authenticated_user_id(
                provided_user_id=user_id,
                operation_name=f"manage_subtask:{action}"
            )
            log_authentication_details(user_id, f"manage_subtask:{action}")
            
            # Get facade for request
            facade = self._get_facade_for_request(task_id, user_id)
            
            # Validate basic requirements
            if not task_id:
                return self._response_formatter.create_error_response(
                    operation=action,
                    error="Missing required field: task_id. Expected: A valid task_id string",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    metadata={"field": "task_id", "hint": "Include 'task_id' in your request"}
                )
            
            # Execute operation using factory
            result = self._operation_factory.handle_operation(
                operation=action,
                facade=facade,
                task_id=task_id,
                user_id=user_id,
                **kwargs
            )
            
            # Apply workflow guidance enhancement
            if result.get("success"):
                result = self._enhance_response_with_workflow_guidance(
                    result, action, task_id
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in manage_subtask {action}: {str(e)}")
            return self._response_formatter.create_error_response(
                operation=action,
                error=f"Subtask operation failed: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={"task_id": task_id}
            )

    def _get_facade_for_request(self, task_id: str, user_id: str) -> SubtaskApplicationFacade:
        """Get appropriate facade for the request."""
        
        if not self._subtask_facade_factory:
            raise ValueError("SubtaskFacadeFactory is required but not provided")
        
        # Create facade with user context and task_id for context derivation
        return self._subtask_facade_factory.create_subtask_facade(user_id=user_id, task_id=task_id)

    def _enhance_response_with_workflow_guidance(self, response: Dict[str, Any], 
                                               action: str, task_id: str) -> Dict[str, Any]:
        """Enhance response with workflow guidance using the workflow guidance system."""
        
        try:
            if self._workflow_guidance:
                # Generate workflow guidance
                guidance = self._workflow_guidance.generate_guidance(
                    action=action,
                    context={
                        "task_id": task_id,
                        "response": response
                    }
                )
                
                if guidance:
                    response["workflow_guidance"] = guidance
                    
        except Exception as e:
            logger.error(f"Error enhancing response with workflow guidance: {e}")
            # Don't fail the operation if guidance enhancement fails
        
        return response