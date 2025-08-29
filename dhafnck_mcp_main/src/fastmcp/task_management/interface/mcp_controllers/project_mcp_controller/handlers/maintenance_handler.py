"""
Project Maintenance Handler

Handles maintenance operations for project management.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from .....application.facades.project_application_facade import ProjectApplicationFacade
from ....utils.response_formatter import StandardResponseFormatter, ResponseStatus, ErrorCodes

logger = logging.getLogger(__name__)


class ProjectMaintenanceHandler:
    """Handler for project maintenance operations."""
    
    def __init__(self, response_formatter: StandardResponseFormatter):
        self._response_formatter = response_formatter
    
    def handle_maintenance_action(self, facade: ProjectApplicationFacade, action: str,
                                 project_id: str, force: Optional[bool] = False,
                                 user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle various maintenance actions."""
        
        async def _run_async(facade, action, project_id, force, user_id):
            if action == "project_health_check":
                return await facade.project_health_check(
                    project_id=project_id,
                    user_id=user_id
                )
            elif action == "cleanup_obsolete":
                return await facade.cleanup_obsolete(
                    project_id=project_id,
                    force=force,
                    user_id=user_id
                )
            elif action == "validate_integrity":
                return await facade.validate_integrity(
                    project_id=project_id,
                    force=force,
                    user_id=user_id
                )
            elif action == "rebalance_agents":
                return await facade.rebalance_agents(
                    project_id=project_id,
                    force=force,
                    user_id=user_id
                )
            else:
                raise ValueError(f"Unknown maintenance action: {action}")
        
        try:
            result = asyncio.run(_run_async(facade, action, project_id, force, user_id))
            
            return self._response_formatter.create_success_response(
                operation=action,
                data=result,
                message=f"Maintenance action '{action}' completed successfully",
                metadata={
                    "action": action,
                    "project_id": project_id,
                    "force": force,
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error in maintenance action '{action}': {str(e)}")
            return self._response_formatter.create_error_response(
                operation=action,
                error=f"Failed to execute maintenance action '{action}': {str(e)}",
                error_code=ErrorCodes.OPERATION_FAILED,
                metadata={
                    "action": action,
                    "project_id": project_id,
                    "force": force,
                    "user_id": user_id
                }
            )
    
    def project_health_check(self, facade: ProjectApplicationFacade, project_id: str,
                           user_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform a project health check."""
        
        return self.handle_maintenance_action(
            facade=facade,
            action="project_health_check",
            project_id=project_id,
            user_id=user_id
        )
    
    def cleanup_obsolete(self, facade: ProjectApplicationFacade, project_id: str,
                        force: Optional[bool] = False, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Clean up obsolete project data."""
        
        return self.handle_maintenance_action(
            facade=facade,
            action="cleanup_obsolete",
            project_id=project_id,
            force=force,
            user_id=user_id
        )
    
    def validate_integrity(self, facade: ProjectApplicationFacade, project_id: str,
                          force: Optional[bool] = False, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate project data integrity."""
        
        return self.handle_maintenance_action(
            facade=facade,
            action="validate_integrity",
            project_id=project_id,
            force=force,
            user_id=user_id
        )
    
    def rebalance_agents(self, facade: ProjectApplicationFacade, project_id: str,
                        force: Optional[bool] = False, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Rebalance agents across the project."""
        
        return self.handle_maintenance_action(
            facade=facade,
            action="rebalance_agents",
            project_id=project_id,
            force=force,
            user_id=user_id
        )