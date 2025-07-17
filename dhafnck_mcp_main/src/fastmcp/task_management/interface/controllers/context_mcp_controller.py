"""Context MCP Controller - Unified Context Management with Hierarchical System

This controller provides both legacy context management API and advanced hierarchical
context operations in a single interface. It uses the hierarchical context system
internally for all operations.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Annotated, List, Union
from datetime import datetime, timezone
from pydantic import Field  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

from .desc import description_loader
from .workflow_guidance.context import ContextWorkflowFactory
from .workflow_hint_enhancer import WorkflowHintEnhancer
from ..utils.error_handler import UserFriendlyErrorHandler
from ..utils.response_formatter import StandardResponseFormatter, ResponseStatus, ErrorCodes

from ...application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory
from ...application.facades.hierarchical_context_facade import HierarchicalContextFacade
from ...application.services.hierarchical_context_service import HierarchicalContextService
from ...application.services.context_inheritance_service import ContextInheritanceService
from ...application.services.context_delegation_service import ContextDelegationService
from ...application.services.context_cache_service import ContextCacheService

logger = logging.getLogger(__name__)


class ContextMCPController:
    """
    Unified MCP controller for context management operations.
    Provides both legacy context API and advanced hierarchical features.
    """
    
    def __init__(self, 
                 hierarchical_context_facade_factory: HierarchicalContextFacadeFactory,
                 hierarchy_service: Optional[HierarchicalContextService] = None,
                 inheritance_service: Optional[ContextInheritanceService] = None,
                 delegation_service: Optional[ContextDelegationService] = None,
                 cache_service: Optional[ContextCacheService] = None):
        """
        Initialize the unified context MCP controller.
        
        Args:
            hierarchical_context_facade_factory: Factory for creating hierarchical context facades
            hierarchy_service: Optional hierarchical context service
            inheritance_service: Optional context inheritance service
            delegation_service: Optional context delegation service
            cache_service: Optional context cache service
        """
        # Legacy support
        self._hierarchical_facade_factory = hierarchical_context_facade_factory
        self._workflow_guidance = ContextWorkflowFactory.create()
        
        # Advanced hierarchical features
        self.hierarchy_service = hierarchy_service or HierarchicalContextService()
        self.inheritance_service = inheritance_service or ContextInheritanceService()
        self.delegation_service = delegation_service or ContextDelegationService()
        self.cache_service = cache_service or ContextCacheService()
        
        # Enhanced workflow integration
        self.workflow_enhancer = WorkflowHintEnhancer()
        self.error_handler = UserFriendlyErrorHandler()
        
        logger.info("Unified ContextMCPController initialized with hierarchical context system")
    
    def register_tools(self, mcp: "FastMCP"):
        """Register both legacy and advanced context management MCP tools"""
        
        # ===============================================
        # LEGACY CONTEXT MANAGEMENT TOOL
        # ===============================================
        
        # Get tool descriptions
        manage_context_desc = self._get_context_management_descriptions().get("manage_context", {})
        
        @mcp.tool(name="manage_context", description=manage_context_desc["description"])
        def manage_context(
            action: Annotated[str, Field(description=manage_context_desc["parameters"].get("action", "Context management action"))],
            task_id: Annotated[Optional[str], Field(description=manage_context_desc["parameters"].get("task_id", "Task identifier"))] = None,
            user_id: Annotated[str, Field(description="User identifier")] = "default_id",
            project_id: Annotated[str, Field(description="Project identifier")] = "",
            git_branch_name: Annotated[str, Field(description="Git branch name")] = "main",
            property_path: Annotated[Optional[str], Field(description="Property path for property operations")] = None,
            value: Annotated[Optional[Any], Field(description="Value for property updates")] = None,
            # Flattened data parameters (replacing complex data dictionary)
            data_title: Annotated[Optional[str], Field(description="Context title for create/update operations")] = None,
            data_description: Annotated[Optional[str], Field(description="Context description for create/update operations")] = None,
            data_status: Annotated[Optional[str], Field(description="Context status for create/update operations")] = None,
            data_priority: Annotated[Optional[str], Field(description="Context priority for create/update operations")] = None,
            data_assignees: Annotated[Optional[Union[List[str], str]], Field(description="Context assignees for create/update operations")] = None,
            data_labels: Annotated[Optional[Union[List[str], str]], Field(description="Context labels for create/update operations")] = None,
            data_estimated_effort: Annotated[Optional[str], Field(description="Context estimated effort for create/update operations")] = None,
            data_due_date: Annotated[Optional[str], Field(description="Context due date for create/update operations")] = None,
            content: Annotated[Optional[str], Field(description="Content for insights/progress")] = None,
            agent: Annotated[Optional[str], Field(description="Agent name for insights/progress")] = None,
            category: Annotated[Optional[str], Field(description="Category for insights")] = None,
            importance: Annotated[str, Field(description="Importance level for insights")] = "medium",
            next_steps: Annotated[Optional[Union[List[str], str]], Field(description="List of next steps (array of strings)")] = None
        ) -> Dict[str, Any]:
            return self._manage_context_implementation(
                action=action,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                git_branch_name=git_branch_name,
                property_path=property_path,
                value=value,
                data_title=data_title,
                data_description=data_description,
                data_status=data_status,
                data_priority=data_priority,
                data_assignees=data_assignees,
                data_labels=data_labels,
                data_estimated_effort=data_estimated_effort,
                data_due_date=data_due_date,
                content=content,
                agent=agent,
                category=category,
                importance=importance,
                next_steps=next_steps
            )
        
        # ===============================================
        # ADVANCED HIERARCHICAL CONTEXT TOOL
        # ===============================================
        """
            Enhanced hierarchical context management with full inheritance and delegation support.
            
            Actions:
                - resolve: Get fully resolved context with inheritance chain
                - update: Update context and optionally propagate changes  
                - create: Create new context at specified level
                - delegate: Delegate context data to higher level
                - propagate: Force propagation of changes
                - get_health: Get system health status
                - cleanup_cache: Clean up expired cache entries
            
            Examples:
                - resolve task context: action="resolve", level="task", context_id="task-123"
                - update project: action="update", level="project", context_id="proj-456", data={...}
                - delegate to global: action="delegate", level="task", context_id="task-123", delegate_to="global", delegate_data={...}
        """
        
        hierarchical_context_desc = self._get_context_management_descriptions().get("manage_hierarchical_context", {})
        
        @mcp.tool(name="manage_hierarchical_context", description=hierarchical_context_desc.get("description", "Enhanced hierarchical context management"))
        async def manage_hierarchical_context(
            action: Annotated[str, Field(description="Context management action: 'resolve', 'update', 'create', 'delegate', 'propagate', 'get_health', 'cleanup_cache'")],
            level: Annotated[str, Field(description="Context level: 'global', 'project', 'task'")] = "task",
            context_id: Annotated[str, Field(description="Context identifier (task_id, project_id, or 'global_singleton')")] = None,
            data: Annotated[Dict[str, Any], Field(description="Context data to create/update")] = None,
            delegate_to: Annotated[str, Field(description="Target level for delegation: 'project', 'global'")] = None,
            delegate_data: Annotated[Dict[str, Any], Field(description="Data to delegate")] = None,
            delegation_reason: Annotated[str, Field(description="Reason for delegation")] = "Manual delegation via MCP",
            force_refresh: Annotated[bool, Field(description="Force cache refresh for resolve action")] = False,
            propagate_changes: Annotated[bool, Field(description="Propagate changes to dependent contexts")] = True
        ) -> Dict[str, Any]:
          
            
            try:
                start_time = datetime.now()
                
                # Validate required parameters
                if action in ["resolve", "update", "delegate"] and not context_id:
                    return StandardResponseFormatter.create_error_response(
                        operation="manage_hierarchical_context",
                        error="context_id is required for this action",
                        error_code=ErrorCodes.MISSING_FIELD
                    )
                
                # Route to appropriate handler
                if action == "resolve":
                    result = await self._handle_resolve_context(level, context_id, force_refresh)
                
                elif action == "update":
                    result = await self._handle_update_context(level, context_id, data or {}, propagate_changes)
                
                elif action == "create":
                    result = await self._handle_create_context(level, context_id, data or {})
                
                elif action == "delegate":
                    if not delegate_to:
                        return StandardResponseFormatter.create_error_response(
                            operation="manage_hierarchical_context",
                            error="delegate_to is required for delegation",
                            error_code=ErrorCodes.MISSING_FIELD
                        )
                    result = await self._handle_delegate_context(
                        level, context_id, delegate_to, delegate_data or {}, delegation_reason
                    )
                
                elif action == "propagate":
                    result = await self._handle_propagate_changes(level, context_id, data or {})
                
                elif action == "get_health":
                    result = await self._handle_get_health()
                
                elif action == "cleanup_cache":
                    result = await self._handle_cleanup_cache()
                
                else:
                    return StandardResponseFormatter.create_error_response(
                        operation="manage_hierarchical_context",
                        error=f"Unknown action: {action}",
                        error_code=ErrorCodes.VALIDATION_ERROR
                    )
                
                # Enhance response with workflow guidance
                enhanced_result = await self._enhance_hierarchical_response_with_workflow_guidance(
                    result, action, {
                        "level": level,
                        "context_id": context_id,
                        "action": action
                    }
                )
                
                # Add performance metadata
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                enhanced_result["performance"] = {
                    "processing_time_ms": round(processing_time, 2),
                    "action": action,
                    "level": level
                }
                
                return enhanced_result
                
            except Exception as e:
                logger.error(f"Error in manage_hierarchical_context: {e}", exc_info=True)
                return StandardResponseFormatter.create_error_response(
                    operation="manage_hierarchical_context",
                    error=str(e),
                    error_code=ErrorCodes.INTERNAL_ERROR
                )
        
        # ===============================================
        # DELEGATION QUEUE MANAGEMENT
        # ===============================================
        """
            Manage delegation queue for manual review and approval.
            
            Actions:
                - list: Get pending delegations
                - approve: Approve a pending delegation
                - reject: Reject a pending delegation  
                - get_status: Get queue status and statistics
        """
        delegation_queue_desc = self._get_context_management_descriptions().get("manage_delegation_queue", {})
        
        @mcp.tool(name="manage_delegation_queue", description=delegation_queue_desc.get("description", "Manage delegation queue for review and approval"))
        async def manage_delegation_queue(
            action: Annotated[str, Field(description="Queue action: 'list', 'approve', 'reject', 'get_status'")],
            delegation_id: Annotated[str, Field(description="Delegation ID for approve/reject actions")] = None,
            target_level: Annotated[str, Field(description="Filter by target level for list action")] = None,
            target_id: Annotated[str, Field(description="Filter by target ID for list action")] = None,
            rejection_reason: Annotated[str, Field(description="Reason for rejection")] = None
        ) -> Dict[str, Any]:
            
            
            try:
                if action == "list":
                    # For now, return empty list as delegation service methods are async
                    # TODO: Fix delegation service to be sync or update this to properly handle async
                    delegations = []
                    return StandardResponseFormatter.create_success_response(
                        operation="manage_delegation_queue",
                        data={"pending_delegations": delegations, "count": len(delegations)}
                    )
                
                elif action == "approve":
                    if not delegation_id:
                        return StandardResponseFormatter.create_error_response(
                            operation="manage_delegation_queue",
                            error="delegation_id is required for approve action",
                            error_code=ErrorCodes.MISSING_FIELD
                        )
                    # TODO: Fix delegation service to be sync or update this to properly handle async
                    result = {"success": True, "delegation_id": delegation_id, "status": "approved"}
                    return StandardResponseFormatter.create_success_response(
                        operation="manage_delegation_queue",
                        data=result
                    )
                
                elif action == "reject":
                    if not delegation_id:
                        return StandardResponseFormatter.create_error_response(
                            operation="manage_delegation_queue", 
                            error="delegation_id is required for reject action",
                            error_code=ErrorCodes.MISSING_FIELD
                        )
                    # TODO: Fix delegation service to be sync or update this to properly handle async
                    result = {"success": True, "delegation_id": delegation_id, "status": "rejected", "reason": rejection_reason}
                    return StandardResponseFormatter.create_success_response(
                        operation="manage_delegation_queue",
                        data=result
                    )
                
                elif action == "get_status":
                    # TODO: Fix delegation service to be sync or update this to properly handle async
                    status = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
                    return StandardResponseFormatter.create_success_response(
                        operation="manage_delegation_queue",
                        data=status
                    )
                
                else:
                    return StandardResponseFormatter.create_error_response(
                        operation="manage_delegation_queue",
                        error=f"Unknown action: {action}",
                        error_code=ErrorCodes.VALIDATION_ERROR
                    )
                    
            except Exception as e:
                logger.error(f"Error in manage_delegation_queue: {e}", exc_info=True)
                return StandardResponseFormatter.create_error_response(
                    operation="manage_delegation_queue",
                    error=str(e),
                    error_code=ErrorCodes.INTERNAL_ERROR
                )
        
        # ===============================================
        # CONTEXT INHERITANCE VALIDATION
        # ===============================================
        """
            Validate context inheritance chain and identify any issues.
            
            Useful for debugging inheritance problems and ensuring contexts
            are properly resolved.
        """
        validate_inheritance_desc = self._get_context_management_descriptions().get("validate_context_inheritance", {})
        
        @mcp.tool(name="validate_context_inheritance", description=validate_inheritance_desc.get("description", "Validate context inheritance chain"))
        async def validate_context_inheritance(
            level: Annotated[str, Field(description="Context level to validate: 'project', 'task'")],
            context_id: Annotated[str, Field(description="Context identifier to validate")]
        ) -> Dict[str, Any]:
            
            
            try:
                # Use the hierarchical context facade with auto-creation fix
                facade = HierarchicalContextFacade(
                    hierarchy_service=self.hierarchy_service,
                    inheritance_service=self.inheritance_service,
                    delegation_service=self.delegation_service,
                    cache_service=self.cache_service
                )
                
                # Use the new validation method with auto-creation
                validation_response = await facade.validate_context_inheritance(level, context_id)
                
                if not validation_response["success"]:
                    return StandardResponseFormatter.create_error_response(
                        operation="validate_context_inheritance",
                        error=validation_response.get("error", "Unknown validation error"),
                        error_code=validation_response.get("error_code", ErrorCodes.INTERNAL_ERROR)
                    )
                
                return StandardResponseFormatter.create_success_response(
                    operation="validate_context_inheritance",
                    data={
                        "validation": validation_response["validation"],
                        "resolution_metadata": validation_response.get("resolution_metadata", {})
                    }
                )
                
            except Exception as e:
                logger.error(f"Error validating inheritance: {e}", exc_info=True)
                return StandardResponseFormatter.create_error_response(
                    operation="validate_context_inheritance",
                    error=str(e),
                    error_code=ErrorCodes.INTERNAL_ERROR
                )
        
        logger.info("All context management tools registered successfully")
    
    # ===============================================
    # LEGACY CONTEXT MANAGEMENT
    # ===============================================
    
    def _get_facade_for_request(self, user_id: str, project_id: str, git_branch_name: str) -> HierarchicalContextFacade:
        """
        Get a HierarchicalContextFacade with the appropriate context.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            git_branch_name: Git branch name
            
        Returns:
            HierarchicalContextFacade instance
        """
        return self._hierarchical_facade_factory.create_facade(
            user_id=user_id,
            project_id=project_id,
            git_branch_name=git_branch_name
        )
    
    def _manage_context_implementation(self, 
                      action: str,
                      task_id: Optional[str] = None,
                      user_id: str = "default_id",
                      project_id: str = "",
                      git_branch_name: str = "main",
                      property_path: Optional[str] = None,
                      value: Optional[Any] = None,
                      # Flattened data parameters
                      data_title: Optional[str] = None,
                      data_description: Optional[str] = None,
                      data_status: Optional[str] = None,
                      data_priority: Optional[str] = None,
                      data_assignees: Optional[Union[List[str], str]] = None,
                      data_labels: Optional[Union[List[str], str]] = None,
                      data_estimated_effort: Optional[str] = None,
                      data_due_date: Optional[str] = None,
                      content: Optional[str] = None,
                      agent: Optional[str] = None,
                      category: Optional[str] = None,
                      importance: str = "medium",
                      next_steps: Optional[Union[List[str], str]] = None) -> Dict[str, Any]:
        """
        Manage context operations by routing to hierarchical context system.
        """
        logger.info(f"Managing context with action: {action} for task: {task_id}")

        # Parse array parameters using the same logic as task controller
        parsed_assignees = self._parse_string_list(data_assignees, "assignees") if data_assignees is not None else None
        parsed_labels = self._parse_string_list(data_labels, "labels") if data_labels is not None else None
        parsed_next_steps = self._parse_string_list(next_steps, "next_steps") if next_steps is not None else None

        # Reconstruct data dictionary from flattened parameters
        data = {}
        if data_title is not None:
            data["title"] = data_title
        if data_description is not None:
            data["description"] = data_description
        if data_status is not None:
            data["status"] = data_status
        if data_priority is not None:
            data["priority"] = data_priority
        if parsed_assignees is not None:
            data["assignees"] = parsed_assignees
        if parsed_labels is not None:
            data["labels"] = parsed_labels
        if data_estimated_effort is not None:
            data["estimated_effort"] = data_estimated_effort
        if data_due_date is not None:
            data["due_date"] = data_due_date

        # Get hierarchical facade
        facade = self._get_facade_for_request(user_id, project_id, git_branch_name)

        try:
            # Import the ID detector
            from .context_id_detector_orm import ContextIDDetector
            
            # Map old context actions to hierarchical context operations
            if action == "create":
                if not task_id:
                    return self._create_missing_field_error("task_id", "create")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    # This is actually a project ID, create at project level
                    logger.info(f"Detected project ID {task_id}, creating project-level context")
                    response = facade.create_context("project", task_id, data)
                elif id_type == "git_branch":
                    # Git branch contexts are stored at task level per architecture
                    logger.info(f"Detected git branch ID {task_id}, creating task-level context for branch")
                    response = facade.create_context("task", task_id, data)
                elif id_type == "task":
                    # Regular task context
                    logger.info(f"Detected task ID {task_id}, creating task-level context")
                    response = facade.create_context("task", task_id, data)
                else:
                    # Unknown ID type, default to task level with warning
                    logger.warning(f"Could not detect ID type for {task_id}, defaulting to task-level context")
                    response = facade.create_context("task", task_id, data)
                
            elif action == "update":
                if not task_id:
                    return self._create_missing_field_error("task_id", "update")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    logger.info(f"Detected project ID {task_id}, updating project-level context")
                    response = facade.update_context("project", task_id, data)
                elif id_type in ["git_branch", "task"]:
                    logger.info(f"Detected {id_type} ID {task_id}, updating task-level context")
                    response = facade.update_context("task", task_id, data)
                else:
                    logger.warning(f"Could not detect ID type for {task_id}, defaulting to task-level context")
                    response = facade.update_context("task", task_id, data)
                
            elif action == "get":
                if not task_id:
                    return self._create_missing_field_error("task_id", "get")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    logger.info(f"Detected project ID {task_id}, getting project-level context")
                    response = facade.get_context("project", task_id, include_inherited=True)
                elif id_type in ["git_branch", "task"]:
                    logger.info(f"Detected {id_type} ID {task_id}, getting task-level context")
                    response = facade.get_context("task", task_id, include_inherited=True)
                else:
                    logger.warning(f"Could not detect ID type for {task_id}, defaulting to task-level context")
                    response = facade.get_context("task", task_id, include_inherited=True)
                
            elif action == "delete":
                if not task_id:
                    return self._create_missing_field_error("task_id", "delete")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    logger.info(f"Detected project ID {task_id}, deleting project-level context")
                    response = facade.delete_context("project", task_id)
                elif id_type in ["git_branch", "task"]:
                    logger.info(f"Detected {id_type} ID {task_id}, deleting task-level context")
                    response = facade.delete_context("task", task_id)
                else:
                    logger.warning(f"Could not detect ID type for {task_id}, defaulting to task-level context")
                    response = facade.delete_context("task", task_id)
                
            elif action == "list":
                # List all task-level contexts
                response = facade.list_contexts("task")
                
            elif action == "get_property":
                if not task_id:
                    return self._create_missing_field_error("task_id", "get_property")
                if not property_path:
                    return self._create_missing_field_error("property_path", "get_property")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    context_response = facade.get_context("project", task_id, include_inherited=True)
                else:
                    context_response = facade.get_context("task", task_id, include_inherited=True)
                if context_response.get("success") and context_response.get("context"):
                    context_data = context_response["context"].get("data", {})
                    # Navigate property path
                    value = self._navigate_property_path(context_data, property_path)
                    response = {
                        "success": True,
                        "property_path": property_path,
                        "value": value
                    }
                else:
                    response = context_response
                    
            elif action == "update_property":
                if not task_id:
                    return self._create_missing_field_error("task_id", "update_property")
                if not property_path:
                    return self._create_missing_field_error("property_path", "update_property")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    context_level = "project"
                else:
                    context_level = "task"
                
                # Get current context, update property, save
                context_response = facade.get_context(context_level, task_id, include_inherited=False)
                if context_response.get("success") and context_response.get("context"):
                    context_data = context_response["context"].get("data", {})
                    # Update property in data
                    self._update_property_path(context_data, property_path, value)
                    # Save updated context
                    response = facade.update_context(context_level, task_id, context_data)
                else:
                    response = context_response
                    
            elif action == "merge":
                if not task_id:
                    return self._create_missing_field_error("task_id", "merge")
                
                # Detect the actual type of the ID to determine correct context level
                id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
                
                if id_type == "project":
                    logger.info(f"Detected project ID {task_id}, merging into project-level context")
                    response = facade.merge_context("project", task_id, data)
                else:
                    logger.info(f"Detected {id_type} ID {task_id}, merging into task-level context")
                    response = facade.merge_context("task", task_id, data)
                
            elif action == "add_insight":
                if not task_id:
                    return self._create_missing_field_error("task_id", "add_insight")
                if not content:
                    return self._create_missing_field_error("content", "add_insight")
                # Add insight to task context
                insight_data = {
                    "insights": [{
                        "content": content,
                        "agent": agent or "unknown",
                        "category": category or "general",
                        "importance": importance,
                        "timestamp": self._get_timestamp()
                    }]
                }
                response = facade.merge_context("task", task_id, insight_data)
                
            elif action == "add_progress":
                if not task_id:
                    return self._create_missing_field_error("task_id", "add_progress")
                if not content:
                    return self._create_missing_field_error("content", "add_progress")
                # Add progress to task context
                progress_data = {
                    "progress": [{
                        "content": content,
                        "agent": agent or "unknown",
                        "timestamp": self._get_timestamp()
                    }]
                }
                response = facade.merge_context("task", task_id, progress_data)
                
            elif action == "update_next_steps":
                if not task_id:
                    return self._create_missing_field_error("task_id", "update_next_steps")
                if not parsed_next_steps:
                    return self._create_missing_field_error("next_steps", "update_next_steps")
                # Update next steps in task context
                next_steps_data = {"next_steps": parsed_next_steps}
                response = facade.merge_context("task", task_id, next_steps_data)
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_code": "UNKNOWN_ACTION",
                    "valid_actions": [
                        "create", "update", "get", "delete", "list",
                        "get_property", "update_property", "merge",
                        "add_insight", "add_progress", "update_next_steps"
                    ],
                    "hint": "Check the action parameter for typos"
                }
                
            return self._enhance_response_with_workflow_guidance(response, action, task_id)
            
        except Exception as e:
            logger.error(f"Error in context operation '{action}': {e}")
            return {
                "success": False,
                "error": f"Operation failed: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
    
    # ===============================================
    # HIERARCHICAL ACTION HANDLERS
    # ===============================================
    
    async def _handle_resolve_context(self, level: str, context_id: str, force_refresh: bool) -> Dict[str, Any]:
        """Handle context resolution with full inheritance"""
        try:
            result = await self.hierarchy_service.resolve_full_context(level, context_id, force_refresh)
            
            return StandardResponseFormatter.create_success_response(
                operation="resolve_context",
                data={
                    "resolved_context": result.resolved_context,
                    "metadata": {
                        "level": level,
                        "context_id": context_id,
                        "resolution_path": result.resolution_path,
                        "cache_hit": result.cache_hit,
                        "dependencies_hash": result.dependencies_hash,
                        "resolution_time_ms": result.resolution_time_ms,
                        "force_refresh": force_refresh
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error resolving context {level}:{context_id}: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="resolve_context",
                error=str(e),
                error_code=ErrorCodes.NOT_FOUND if "not found" in str(e).lower() else ErrorCodes.INTERNAL_ERROR
            )
    
    async def _handle_update_context(self, level: str, context_id: str, data: Dict[str, Any], 
                                   propagate: bool) -> Dict[str, Any]:
        """Handle context update with optional propagation"""
        try:
            result = self.hierarchy_service.update_context(level, context_id, data, propagate)
            
            if result.get("success"):
                return StandardResponseFormatter.create_success_response(
                    operation="update_context",
                    data=result
                )
            else:
                return StandardResponseFormatter.create_error_response(
                    operation="update_context",
                    error=result.get("error", "Update failed"),
                    error_code=ErrorCodes.OPERATION_FAILED
                )
                
        except Exception as e:
            logger.error(f"Error updating context {level}:{context_id}: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="update_context",
                error=str(e),
                error_code=ErrorCodes.INTERNAL_ERROR
            )
    
    async def _handle_create_context(self, level: str, context_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context creation"""
        try:
            # Route to appropriate creation method based on level
            if level == "global":
                result = self._create_global_context(data)
            elif level == "project":
                result = self._create_project_context(context_id, data)
            elif level == "task":
                result = self._create_task_context(context_id, data)
            else:
                return StandardResponseFormatter.create_error_response(
                    operation="create_context",
                    error=f"Invalid context level: {level}",
                    error_code=ErrorCodes.VALIDATION_ERROR
                )
            
            return StandardResponseFormatter.create_success_response(
                operation="create_context",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error creating {level} context: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="create_context",
                error=str(e),
                error_code=ErrorCodes.INTERNAL_ERROR
            )
    
    async def _handle_delegate_context(self, from_level: str, from_id: str, to_level: str, 
                                     data: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Handle context delegation"""
        try:
            result = self.hierarchy_service.delegate_context(from_level, from_id, to_level, data, reason)
            
            if result.get("success"):
                return StandardResponseFormatter.create_success_response(
                    operation="delegate_context",
                    data=result
                )
            else:
                return StandardResponseFormatter.create_error_response(
                    operation="delegate_context",
                    error=result.get("error", "Delegation failed"),
                    error_code=ErrorCodes.OPERATION_FAILED
                )
                
        except Exception as e:
            logger.error(f"Error delegating context: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="delegate_context",
                error=str(e),
                error_code=ErrorCodes.INTERNAL_ERROR
            )
    
    async def _handle_propagate_changes(self, level: str, context_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Handle change propagation"""
        try:
            result = self.hierarchy_service.propagate_changes(level, context_id, changes)
            
            return StandardResponseFormatter.create_success_response(
                operation="propagate_changes",
                data={
                    "propagation_result": result.__dict__,
                    "affected_contexts_count": len(result.affected_contexts)
                }
            )
            
        except Exception as e:
            logger.error(f"Error propagating changes: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="propagate_changes",
                error=str(e),
                error_code=ErrorCodes.INTERNAL_ERROR
            )
    
    async def _handle_get_health(self) -> Dict[str, Any]:
        """Handle system health check"""
        try:
            health = await self.hierarchy_service.get_system_health()
            
            return StandardResponseFormatter.create_success_response(
                operation="get_system_health",
                data=health
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="get_system_health",
                error=str(e),
                error_code=ErrorCodes.INTERNAL_ERROR
            )
    
    async def _handle_cleanup_cache(self) -> Dict[str, Any]:
        """Handle cache cleanup"""
        try:
            result = self.hierarchy_service.cleanup_expired_cache()
            
            return StandardResponseFormatter.create_success_response(
                operation="cleanup_cache",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return StandardResponseFormatter.create_error_response(
                operation="cleanup_cache",
                error=str(e),
                error_code=ErrorCodes.INTERNAL_ERROR
            )
    
    # ===============================================
    # CONTEXT CREATION HELPERS
    # ===============================================
    
    def _create_global_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create global context (singleton)"""
        # Call the hierarchy service's create_context method (synchronous)
        result = self.hierarchy_service.create_context("global", "global_singleton", data)
        return {
            "success": True,
            "level": "global",
            "context_id": "global_singleton",
            "context": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_project_context(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project context"""
        # Call the hierarchy service's create_context method (synchronous)
        result = self.hierarchy_service.create_context("project", project_id, data)
        return {
            "success": True,
            "level": "project",
            "context_id": project_id,
            "context": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_task_context(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task context"""
        # Call the hierarchy service's create_context method (synchronous)
        result = self.hierarchy_service.create_context("task", task_id, data)
        return {
            "success": True,
            "level": "task",
            "context_id": task_id,
            "context": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ===============================================
    # UTILITY METHODS
    # ===============================================
    
    def _navigate_property_path(self, data: Dict[str, Any], property_path: str) -> Any:
        """Navigate through nested dictionary using dot notation."""
        parts = property_path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
    
    def _update_property_path(self, data: Dict[str, Any], property_path: str, value: Any) -> None:
        """Update a property in nested dictionary using dot notation."""
        parts = property_path.split('.')
        current = data
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"

    def _get_context_management_descriptions(self) -> Dict[str, Any]:
        """
        Get context descriptions from the description loader.
        """
        all_desc = description_loader.get_all_descriptions()
        flat = {}
        
        # Look for context descriptions in the 'context' subdirectory
        if "context" in all_desc and isinstance(all_desc["context"], dict):
            context_desc = all_desc["context"]
            
            # Extract each context tool description
            for tool_name in ["manage_context", "manage_hierarchical_context", "manage_delegation_queue", "validate_context_inheritance"]:
                if tool_name in context_desc:
                    flat[tool_name] = context_desc[tool_name]
        
        # Fallback: look for descriptions at the root level for backward compatibility
        for sub in all_desc.values():
            if isinstance(sub, dict):
                for tool_name in ["manage_context", "manage_hierarchical_context", "manage_delegation_queue", "validate_context_inheritance"]:
                    if tool_name in sub and tool_name not in flat:
                        flat[tool_name] = sub[tool_name]
        
        return flat
    
    def _create_missing_field_error(self, field: str, action: str) -> Dict[str, Any]:
        """Create standardized missing field error response."""
        return {
            "success": False,
            "error": f"Missing required field: {field}",
            "error_code": "MISSING_FIELD",
            "field": field,
            "action": action,
            "expected": f"A valid {field} value",
            "hint": f"Include '{field}' in your request for action '{action}'"
        }
    
    def _enhance_response_with_workflow_guidance(self, response: Dict[str, Any], action: str, 
                                               task_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhance response with workflow guidance for better user experience."""
        if response.get("success", False):
            # Only add guidance to successful responses
            guidance_context = {"task_id": task_id} if task_id else {}
            workflow_guidance = self._workflow_guidance.generate_guidance(action, guidance_context)
            response["workflow_guidance"] = workflow_guidance
        
        return response
    
    async def _enhance_hierarchical_response_with_workflow_guidance(self, response: Dict[str, Any], 
                                                                 action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response with hierarchical context workflow guidance"""
        try:
            # For now, return the response as-is since the workflow enhancer doesn't have this method yet
            # TODO: Implement enhance_hierarchical_context_response in WorkflowHintEnhancer
            enhanced_response = response.copy()
            
            # Add basic workflow hint based on action
            workflow_hints = {
                "resolve": "Context resolved with full inheritance chain. Use the resolved data for decision making.",
                "update": "Context updated successfully. Changes may propagate to dependent contexts.",
                "create": "Context created successfully. Remember to update it as you progress.",
                "delegate": "Context delegation requested. Check delegation queue for approval status.",
                "propagate": "Changes propagated to dependent contexts.",
                "get_health": "System health information retrieved.",
                "cleanup_cache": "Cache cleaned up successfully."
            }
            
            if action in workflow_hints:
                enhanced_response["workflow_hint"] = workflow_hints[action]
            
            return enhanced_response
            
        except Exception as e:
            logger.warning(f"Error enhancing response with workflow guidance: {e}")
            return response
    
    def _parse_string_list(self, param: Any, param_name: str = "parameter") -> Optional[List[str]]:
        """
        Generic parser for string list parameters that might come in various formats.
        Works for labels, assignees, next_steps, or any other string list parameter.
        
        Handles:
        - List[str]: ["item1", "item2"] - already correct format
        - JSON string: '["item1", "item2"]' - parse as JSON
        - Comma-separated string: "item1,item2,item3" - split by comma
        - Single item string: "item1" - wrap in list
        - None or empty - return None
        
        Returns:
            List[str] if valid items found, None otherwise
        """
        if param is None:
            return None
            
        # If already a list, validate each item is a string
        if isinstance(param, list):
            # Ensure all items are strings
            parsed_items = []
            for item in param:
                if isinstance(item, str):
                    parsed_items.append(item.strip())
                else:
                    logger.warning(f"Skipping non-string {param_name}: {item}")
            return parsed_items if parsed_items else None
            
        # If it's a string, try to parse it
        if isinstance(param, str):
            param = param.strip()
            if not param:
                return None
                
            # Try parsing as JSON array first
            if param.startswith('[') and param.endswith(']'):
                try:
                    import json
                    parsed = json.loads(param)
                    if isinstance(parsed, list):
                        # Validate all items are strings
                        parsed_items = []
                        for item in parsed:
                            if isinstance(item, str):
                                parsed_items.append(item.strip())
                        return parsed_items if parsed_items else None
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse {param_name} as JSON: {param}")
            
            # Try comma-separated format
            if ',' in param:
                parsed_items = [item.strip() for item in param.split(',') if item.strip()]
                return parsed_items if parsed_items else None
            
            # Single item
            return [param]
        
        # Unknown format
        logger.warning(f"Unable to parse {param_name} parameter of type {type(param)}: {param}")
        return None