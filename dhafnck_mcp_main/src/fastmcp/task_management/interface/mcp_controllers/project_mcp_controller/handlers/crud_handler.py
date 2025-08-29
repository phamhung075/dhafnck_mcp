"""
Project CRUD Handler

Handles basic CRUD operations for project management.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from .....application.facades.project_application_facade import ProjectApplicationFacade
from ....utils.response_formatter import StandardResponseFormatter, ResponseStatus, ErrorCodes

logger = logging.getLogger(__name__)


class ProjectCRUDHandler:
    """Handler for project CRUD operations."""
    
    def __init__(self, response_formatter: StandardResponseFormatter):
        self._response_formatter = response_formatter
    
    def create_project(self, facade: ProjectApplicationFacade, name: str, 
                      description: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project."""
        
        async def _run_async(facade, name, description, user_id):
            return await facade.create_project(
                name=name,
                description=description,
                user_id=user_id
            )
        
        try:
            result = asyncio.run(_run_async(facade, name, description, user_id))
            
            return self._response_formatter.create_success_response(
                operation="create",
                data=result,
                message=f"Project '{name}' created successfully",
                metadata={
                    "project_name": name,
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return self._response_formatter.create_error_response(
                operation="create",
                error=f"Failed to create project: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={"project_name": name, "user_id": user_id}
            )
    
    def get_project(self, facade: ProjectApplicationFacade, 
                   project_id: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """Get a project by ID or name."""
        
        async def _run_async(facade, project_id, name, controller_self):
            if project_id:
                result = await facade.get_project(project_id=project_id)
            elif name:
                result = await facade.get_project_by_name(name=name)
            else:
                raise ValueError("Either project_id or name must be provided")
            
            # Include project context
            if result and isinstance(result, dict):
                result = controller_self._include_project_context(result)
            
            return result
        
        try:
            result = asyncio.run(_run_async(facade, project_id, name, self))
            
            return self._response_formatter.create_success_response(
                operation="get",
                data=result,
                message="Project retrieved successfully",
                metadata={
                    "project_id": project_id,
                    "project_name": name
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving project: {str(e)}")
            return self._response_formatter.create_error_response(
                operation="get",
                error=f"Failed to retrieve project: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={"project_id": project_id, "project_name": name}
            )
    
    def list_projects(self, facade: ProjectApplicationFacade) -> Dict[str, Any]:
        """List all projects."""
        
        async def _run_async(facade):
            return await facade.list_projects()
        
        try:
            result = asyncio.run(_run_async(facade))
            
            return self._response_formatter.create_success_response(
                operation="list",
                data=result,
                message=f"Retrieved {len(result.get('projects', []))} projects",
                metadata={"project_count": len(result.get('projects', []))}
            )
            
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return self._response_formatter.create_error_response(
                operation="list",
                error=f"Failed to list projects: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={}
            )
    
    def update_project(self, facade: ProjectApplicationFacade, project_id: str,
                      name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing project."""
        
        async def _run_async(facade, project_id, name, description):
            return await facade.update_project(
                project_id=project_id,
                name=name,
                description=description
            )
        
        try:
            result = asyncio.run(_run_async(facade, project_id, name, description))
            
            return self._response_formatter.create_success_response(
                operation="update",
                data=result,
                message="Project updated successfully",
                metadata={
                    "project_id": project_id,
                    "name": name
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            return self._response_formatter.create_error_response(
                operation="update",
                error=f"Failed to update project: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={"project_id": project_id}
            )
    
    def delete_project(self, facade: ProjectApplicationFacade, project_id: str,
                      force: Optional[bool] = False) -> Dict[str, Any]:
        """Delete a project."""
        
        async def _run_async(facade, project_id, force):
            return await facade.delete_project(project_id=project_id, force=force)
        
        try:
            result = asyncio.run(_run_async(facade, project_id, force))
            
            return self._response_formatter.create_success_response(
                operation="delete",
                data=result,
                message="Project deleted successfully",
                metadata={
                    "project_id": project_id,
                    "force": force
                }
            )
            
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            return self._response_formatter.create_error_response(
                operation="delete",
                error=f"Failed to delete project: {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={"project_id": project_id, "force": force}
            )
    
    def _include_project_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Include project context in the result."""
        
        # Add project context information
        if isinstance(result, dict) and "project" in result:
            project_data = result["project"]
            result["project_context"] = {
                "management_available": True,
                "health_check_available": True,
                "maintenance_operations": [
                    "project_health_check",
                    "cleanup_obsolete", 
                    "validate_integrity",
                    "rebalance_agents"
                ]
            }
        
        return result