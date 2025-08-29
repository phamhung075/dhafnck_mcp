"""
Project API Controller

This controller handles frontend project management operations following proper DDD architecture.
It serves as the interface layer, delegating business logic to application facades.
"""

import logging
from typing import Dict, Any, Optional

from ...application.facades.project_application_facade import ProjectApplicationFacade
from ...application.dtos.project.create_project_request import CreateProjectRequest
from ...application.dtos.project.update_project_request import UpdateProjectRequest

logger = logging.getLogger(__name__)


class ProjectAPIController:
    """
    API Controller for project management operations.
    
    This controller provides a clean interface between frontend routes and
    application services, ensuring proper separation of concerns.
    """
    
    def __init__(self):
        """Initialize the controller"""
        pass
    
    def create_project(self, request: CreateProjectRequest, user_id: str, session) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            request: Project creation request data
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Project creation result
        """
        try:
            # Create project facade with proper user context
            facade = ProjectApplicationFacade(user_id=user_id)
            
            # Delegate to facade
            result = facade.create_project(request)
            
            logger.info(f"Project created successfully for user {user_id}: {result.get('project', {}).get('id')}")
            
            return {
                "success": True,
                "project": result.get("project"),
                "message": "Project created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating project for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create project"
            }
    
    def list_projects(self, user_id: str, session) -> Dict[str, Any]:
        """
        List projects for a user.
        
        Args:
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            List of projects
        """
        try:
            # Create project facade with proper user context
            facade = ProjectApplicationFacade(user_id=user_id)
            
            # Delegate to facade
            result = facade.list_projects()
            
            logger.info(f"Listed {len(result.get('projects', []))} projects for user {user_id}")
            
            return {
                "success": True,
                "projects": result.get("projects", []),
                "count": len(result.get("projects", [])),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error listing projects for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list projects"
            }
    
    def get_project(self, project_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Get a specific project.
        
        Args:
            project_id: Project identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Project details
        """
        try:
            # Create project facade with proper user context
            facade = ProjectApplicationFacade(user_id=user_id)
            
            # Delegate to facade
            project = facade.get_project(project_id)
            
            if not project:
                return {
                    "success": False,
                    "error": "Project not found",
                    "message": "Project not found or access denied"
                }
            
            logger.info(f"Retrieved project {project_id} for user {user_id}")
            
            return {
                "success": True,
                "project": project
            }
            
        except Exception as e:
            logger.error(f"Error getting project {project_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get project"
            }
    
    def update_project(self, project_id: str, request: UpdateProjectRequest, user_id: str, session) -> Dict[str, Any]:
        """
        Update a project.
        
        Args:
            project_id: Project identifier
            request: Project update request
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Updated project details
        """
        try:
            # Create project facade with proper user context
            facade = ProjectApplicationFacade(user_id=user_id)
            
            # First check if project exists
            existing_project = facade.get_project(project_id)
            if not existing_project:
                return {
                    "success": False,
                    "error": "Project not found",
                    "message": "Project not found or access denied"
                }
            
            # Delegate to facade
            updated_project = facade.update_project(project_id, request)
            
            logger.info(f"Updated project {project_id} for user {user_id}")
            
            return {
                "success": True,
                "project": updated_project,
                "message": "Project updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating project {project_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update project"
            }
    
    def delete_project(self, project_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Delete a project.
        
        Args:
            project_id: Project identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Deletion result
        """
        try:
            # Create project facade with proper user context
            facade = ProjectApplicationFacade(user_id=user_id)
            
            # First check if project exists
            existing_project = facade.get_project(project_id)
            if not existing_project:
                return {
                    "success": False,
                    "error": "Project not found", 
                    "message": "Project not found or access denied"
                }
            
            # Delegate to facade
            facade.delete_project(project_id)
            
            logger.info(f"Deleted project {project_id} for user {user_id}")
            
            return {
                "success": True,
                "message": "Project deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting project {project_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete project"
            }
    
    def get_project_health(self, project_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Get project health status.
        
        Args:
            project_id: Project identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Project health status
        """
        try:
            # Create project facade with proper user context
            facade = ProjectApplicationFacade(user_id=user_id)
            
            # First check if project exists
            existing_project = facade.get_project(project_id)
            if not existing_project:
                return {
                    "success": False,
                    "error": "Project not found",
                    "message": "Project not found or access denied"
                }
            
            # Delegate to facade for health check
            health_result = facade.project_health_check(project_id)
            
            logger.info(f"Retrieved project health for {project_id} by user {user_id}")
            
            return {
                "success": True,
                "health": health_result,
                "message": "Project health retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting project health {project_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get project health"
            }