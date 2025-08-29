"""Dependency MCP Controller

This controller handles MCP protocol concerns for dependency operations.
It converts between MCP request formats and application DTOs, then
delegates all business logic to the TaskApplicationFacade.
"""

import logging
from typing import Dict, Any, Optional, Annotated
from pydantic import Field  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP
    from ....application.facades.task_application_facade import TaskApplicationFacade

from .handlers import DependencyOperationHandler
from .services import DescriptionService

logger = logging.getLogger(__name__)


class DependencyMCPController:
    """
    MCP controller for dependency operations.
    Handles MCP protocol concerns for dependencies:
    - Converting MCP parameters to application DTOs
    - Delegating to application facade
    - Converting responses back to MCP format
    - Handling protocol-specific errors
    """
    def __init__(self, task_facade: "TaskApplicationFacade"):
        self._handler = DependencyOperationHandler(task_facade)
        self._description_service = DescriptionService()
        logger.info("DependencyMCPController initialized")

    def register_tools(self, mcp: "FastMCP"):
        descriptions = self._description_service.get_dependency_management_descriptions()
        manage_dependency_desc = descriptions["manage_dependency"]

        @mcp.tool(description=manage_dependency_desc["description"])
        def manage_dependency(
            action: Annotated[str, Field(description=manage_dependency_desc["parameters"].get("action", "Dependency management action"))],
            task_id: Annotated[str, Field(description=manage_dependency_desc["parameters"].get("task_id", "Task identifier"))],
            project_id: Annotated[str, Field(description=manage_dependency_desc["parameters"].get("project_id", "Project identifier"))] = "default_project",
            git_branch_name: Annotated[str, Field(description=manage_dependency_desc["parameters"].get("git_branch_name", "Task tree identifier"))] = "main",
            user_id: Annotated[Optional[str], Field(description=manage_dependency_desc["parameters"].get("user_id", "User identifier"))] = None,
            dependency_data: Annotated[Optional[Dict[str, Any]], Field(description=manage_dependency_desc["parameters"].get("dependency_data", "Dependency data"))] = None
        ) -> Dict[str, Any]:
            return self.handle_dependency_operations(
                action=action,
                task_id=task_id,
                project_id=project_id,
                git_branch_name=git_branch_name,
                user_id=user_id,
                dependency_data=dependency_data
            )

    def handle_dependency_operations(self, action: str, task_id: str, 
                                     project_id: str = "default_project", 
                                     git_branch_name: str = "main", 
                                     user_id: Optional[str] = None, 
                                     dependency_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle dependency operations by delegating to the handler.
        
        Args:
            action: The dependency action to perform
            task_id: The task ID
            project_id: The project ID
            git_branch_name: The git branch name
            user_id: The user ID
            dependency_data: Additional dependency data
            
        Returns:
            Operation result dictionary
        """
        return self._handler.handle_operation(
            action=action,
            task_id=task_id,
            project_id=project_id,
            git_branch_name=git_branch_name,
            user_id=user_id,
            dependency_data=dependency_data
        )