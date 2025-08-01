"""Project MCP Controller

This controller handles project management operations following DDD principles.
It delegates business logic to the project facade and handles MCP-specific concerns.
"""

import logging
from typing import Dict, Any, Optional, Annotated
from pydantic import Field  # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

from .desc import description_loader
from ...application.factories.project_facade_factory import ProjectFacadeFactory
from ...application.facades.project_application_facade import ProjectApplicationFacade

logger = logging.getLogger(__name__)


class ProjectMCPController:
    """
    MCP Controller for project management operations.

    Handles only MCP protocol concerns and delegates business operations
    to the ProjectApplicationFacade following proper DDD layer separation.
    """

    def __init__(self, project_facade_factory: ProjectFacadeFactory):
        """
        Initialize controller with project facade factory.

        Args:
            project_facade_factory: Factory for creating project application facades
        """
        self._project_facade_factory = project_facade_factory
        logger.info("ProjectMCPController initialized with factory pattern")
    
    def register_tools(self, mcp: "FastMCP"):
        """Register project management MCP tools"""
        descriptions = self._get_project_management_descriptions()
        manage_project_desc = descriptions.get("manage_project", {})

        @mcp.tool(name="manage_project", description=manage_project_desc["description"])
        def manage_project(
            action: Annotated[str, Field(description=manage_project_desc["parameters"].get("action", "Project management action"))],
            project_id: Annotated[Optional[str], Field(description=manage_project_desc["parameters"].get("project_id", "Project identifier"))] = None,
            name: Annotated[Optional[str], Field(description=manage_project_desc["parameters"].get("name", "Project name"))] = None,
            description: Annotated[Optional[str], Field(description=manage_project_desc["parameters"].get("description", "Project description"))] = None,
            user_id: Annotated[Optional[str], Field(description=manage_project_desc["parameters"].get("user_id", "User identifier"))] = None,
            force: Annotated[bool, Field(description=manage_project_desc["parameters"].get("force", "Force operation flag"))] = False
        ) -> Dict[str, Any]:
            """Manage project operations including CRUD and maintenance tasks."""
            return self.manage_project(
                action=action,
                project_id=project_id,
                name=name,
                description=description,
                user_id=user_id,
                force=force
            )
    
    def _get_facade_for_request(self, user_id: str = "default_id") -> ProjectApplicationFacade:
        """
        Get a ProjectApplicationFacade with the appropriate context.
        
        Args:
            user_id: User identifier
            
        Returns:
            ProjectApplicationFacade instance
        """
        return self._project_facade_factory.create_project_facade(user_id=user_id)
    
    def manage_project(
        self,
        action: str,
        project_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Handle project management operations by routing to appropriate handlers.
        
        Args:
            action: The action to perform
            project_id: Project identifier
            name: Project name
            description: Project description
            user_id: User identifier
            force: Force operation flag
            
        Returns:
            Dict containing operation result
        """
        logger.info(f"Managing project with action: {action}, project_id: {project_id}")
        
        # Use default user_id if not provided
        if user_id is None:
            user_id = "default_id"
        
        # Route to appropriate handler based on action
        if action in ["create", "get", "list", "update"]:
            return self.handle_crud_operations(
                action, project_id, name, description, user_id
            )
        elif action in ["project_health_check", "cleanup_obsolete", "validate_integrity", "rebalance_agents"]:
            return self.handle_maintenance_operations(
                action, project_id, force, user_id
            )
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "error_code": "UNKNOWN_ACTION",
                "valid_actions": [
                    "create", "get", "list", "update",
                    "project_health_check", "cleanup_obsolete",
                    "validate_integrity", "rebalance_agents"
                ],
                "hint": "Check the action parameter for typos"
            }
    
    def handle_crud_operations(
        self,
        action: str,
        project_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_id: str = "default_id"
    ) -> Dict[str, Any]:
        """
        Handle core CRUD operations by converting MCP parameters 
        and delegating to the application facade.
        """
        try:
            # Get facade for this request
            facade = self._get_facade_for_request(user_id)
            
            # Basic validation at controller level
            if action == "create":
                if not name:
                    return self._create_missing_field_error("name", "create")
                return self._handle_create_project(facade, name, description, user_id)
                
            elif action == "get":
                if not project_id and not name:
                    return {
                        "success": False,
                        "error": "Missing required field: either project_id or name is required",
                        "error_code": "MISSING_FIELD",
                        "hint": "Provide either project_id or name for get action"
                    }
                return self._handle_get_project(facade, project_id, name)
                
            elif action == "list":
                return self._handle_list_projects(facade)
                
            elif action == "update":
                if not project_id:
                    return self._create_missing_field_error("project_id", "update")
                return self._handle_update_project(facade, project_id, name, description)
                
            else:
                return self._create_invalid_action_error(action)

        except Exception as e:
            logger.error(f"Error in CRUD operation '{action}': {e}")
            return {
                "success": False,
                "error": f"Operation failed: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }
    
    def handle_maintenance_operations(
        self,
        action: str,
        project_id: Optional[str] = None,
        force: bool = False,
        user_id: str = "default_id"
    ) -> Dict[str, Any]:
        """
        Handle maintenance operations by converting MCP parameters 
        and delegating to the application facade.
        """
        try:
            # Get facade for this request
            facade = self._get_facade_for_request(user_id)
            
            # All maintenance operations require project_id
            if not project_id:
                return self._create_missing_field_error("project_id", action)
            
            # Delegate to facade's manage_project method which handles all actions
            return self._handle_maintenance_action(facade, action, project_id, force, user_id)

        except Exception as e:
            logger.error(f"Error in maintenance operation '{action}': {e}")
            return {
                "success": False,
                "error": f"Operation failed: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "details": str(e)
            }

    # Private helper methods for converting MCP parameters and delegating to facade
    
    def _handle_create_project(self, facade: ProjectApplicationFacade, name: str, 
                               description: Optional[str], user_id: str) -> Dict[str, Any]:
        """Convert MCP create parameters and delegate to facade."""
        import asyncio
        import threading
        
        async def _run_async():
            return await facade.manage_project(
                action="create",
                name=name,
                description=description,
                user_id=user_id
            )
        
        # Always use threading approach to avoid asyncio.run() issues
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(_run_async())
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
    
    def _handle_get_project(self, facade: ProjectApplicationFacade, 
                           project_id: Optional[str], name: Optional[str]) -> Dict[str, Any]:
        """Handle get project request with enhanced context inclusion."""
        import asyncio
        import threading
        
        async def _run_async():
            # Get the basic project data
            result = await facade.manage_project(
                action="get",
                project_id=project_id,
                name=name
            )
            
            # Enhance with project context if successful
            if result.get("success") and result.get("project"):
                result = self._include_project_context(result)
            
            return result
        
        # Always use threading approach to avoid asyncio.run() issues
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(_run_async())
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
    
    def _handle_list_projects(self, facade: ProjectApplicationFacade) -> Dict[str, Any]:
        """Handle list projects request."""
        import asyncio
        import threading
        
        async def _run_async():
            return await facade.manage_project(action="list")
        
        # Always use threading approach to avoid asyncio.run() issues
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(_run_async())
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
    
    def _handle_update_project(self, facade: ProjectApplicationFacade, project_id: str,
                              name: Optional[str], description: Optional[str]) -> Dict[str, Any]:
        """Handle update project request."""
        import asyncio
        import threading
        
        async def _run_async():
            return await facade.manage_project(
                action="update",
                project_id=project_id,
                name=name,
                description=description
            )
        
        # Always use threading approach to avoid asyncio.run() issues
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(_run_async())
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
    
    def _handle_maintenance_action(self, facade: ProjectApplicationFacade, action: str,
                                  project_id: str, force: bool, user_id: str) -> Dict[str, Any]:
        """Handle maintenance action request."""
        import asyncio
        import threading
        
        async def _run_async():
            return await facade.manage_project(
                action=action,
                project_id=project_id,
                force=force,
                user_id=user_id
            )
        
        # Always use threading approach to avoid asyncio.run() issues
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(_run_async())
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

    def _get_project_management_descriptions(self) -> Dict[str, Any]:
        """
        Flatten project descriptions for robust access, similar to other controllers.
        """
        all_desc = description_loader.get_all_descriptions()
        flat = {}
        # Look for 'manage_project' in any subdict
        for sub in all_desc.values():
            if isinstance(sub, dict) and "manage_project" in sub:
                flat["manage_project"] = sub["manage_project"]
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
    
    def _create_invalid_action_error(self, action: str) -> Dict[str, Any]:
        """Create standardized invalid action error response."""
        return {
            "success": False,
            "error": f"Invalid action: {action}",
            "error_code": "INVALID_ACTION",
            "field": "action",
            "valid_actions": [
                "create", "get", "list", "update",
                "project_health_check", "cleanup_obsolete",
                "validate_integrity", "rebalance_agents"
            ],
            "hint": "Check the action parameter for valid values"
        }
    
    def _include_project_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Include project context in the response."""
        try:
            project_data = result.get("project", {})
            project_id = project_data.get("id")
            
            if not project_id:
                return result
            
            # Get hierarchical context facade
            from ...application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
            context_factory = UnifiedContextFacadeFactory()
            context_facade = context_factory.create_facade()
            
            # Get project context
            project_context = context_facade.get_context("project", project_id, include_inherited=True)
            
            if project_context.get("success"):
                result["project_context"] = project_context.get("context", {})
                logger.info(f"Added project context for project {project_id}")
            else:
                logger.warning(f"Failed to get project context for {project_id}: {project_context.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error including project context: {e}")
        
        return result