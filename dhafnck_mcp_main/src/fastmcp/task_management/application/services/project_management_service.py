"""Project Management Service

Application service for project lifecycle and multi-agent coordination.
Now uses SQLite database instead of JSON files for better data integrity and performance.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ...infrastructure.utilities.path_resolver import PathResolver
from ...infrastructure.repositories.project_repository_factory import GlobalRepositoryManager
from ...application.use_cases.create_project import CreateProjectUseCase
from ...application.use_cases.get_project import GetProjectUseCase
from ...application.use_cases.list_projects import ListProjectsUseCase
from ...application.use_cases.update_project import UpdateProjectUseCase
from ...application.use_cases.project_health_check import ProjectHealthCheckUseCase
from ...application.use_cases.cleanup_obsolete_use_case import CleanupObsoleteUseCase
from ...application.use_cases.validate_integrity_use_case import ValidateIntegrityUseCase
from ...application.use_cases.rebalance_agents_use_case import RebalanceAgentsUseCase
from ...domain.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class ProjectManagementService:
    """Application service for project lifecycle and multi-agent coordination using SQLite database"""
    
    def __init__(self, project_repo: Optional[ProjectRepository] = None):
        """
        Initialize ProjectManagementService with SQLite repository
        
        Args:
            project_repo: Optional project repository (for testing/dependency injection)
        """
        # Use provided repository or get default SQLite repository
        self._project_repo = project_repo or GlobalRepositoryManager.get_default()
        logger.info("ProjectManagementService initialized with SQLite repository")
    
    async def create_project(self, name: str, description: str = "", user_id: str = "default_id") -> Dict[str, Any]:
        """Create a new project with auto-generated UUID"""
        try:
            use_case = CreateProjectUseCase(self._project_repo)
            # Pass `None` for project_id so the use-case auto-generates one.
            return await use_case.execute(None, name, description)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details by UUID"""
        try:
            use_case = GetProjectUseCase(self._project_repo)
            return await use_case.execute(project_id)
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_project_by_name(self, name: str) -> Dict[str, Any]:
        """Get project details by name"""
        try:
            # Assuming GetProjectUseCase can handle by_name lookups, or we need another use case
            # For now, let's add a method to the repo and use GetProjectUseCase
            project = await self._project_repo.find_by_name(name)
            if not project:
                return {"success": False, "error": f"Project with name '{name}' not found"}
            
            use_case = GetProjectUseCase(self._project_repo)
            return await use_case.execute(project.id)

        except Exception as e:
            logger.error(f"Failed to get project by name '{name}': {e}")
            return {"success": False, "error": str(e)}
    
    async def list_projects(self) -> Dict[str, Any]:
        """List all projects"""
        try:
            use_case = ListProjectsUseCase(self._project_repo)
            return await use_case.execute()
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_project(self, project_id: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """Update an existing project"""
        try:
            use_case = UpdateProjectUseCase(self._project_repo)
            return await use_case.execute(project_id, name, description)
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def project_health_check(self, project_id: str = None) -> Dict[str, Any]:
        """Perform health check on project(s)"""
        try:
            use_case = ProjectHealthCheckUseCase(self._project_repo)
            return await use_case.execute(project_id)
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_obsolete(self, project_id: str = None) -> Dict[str, Any]:
        """Clean up obsolete project data"""
        try:
            use_case = CleanupObsoleteUseCase(self._project_repo)
            return await use_case.execute(project_id)
        except Exception as e:
            logger.error(f"Failed to cleanup obsolete data: {e}")
            return {"success": False, "error": str(e)}

    
    async def validate_integrity(self, project_id: str = None) -> Dict[str, Any]:
        """Validate integrity of project data"""
        try:
            use_case = ValidateIntegrityUseCase(self._project_repo)
            return await use_case.execute(project_id)
        except Exception as e:
            logger.error(f"Failed to validate integrity: {e}")
            return {"success": False, "error": str(e)}

    
    async def rebalance_agents(self, project_id: str = None) -> Dict[str, Any]:
        """Rebalance agent assignments across task trees"""
        try:
            use_case = RebalanceAgentsUseCase(self._project_repo)
            return await use_case.execute(project_id)
        except Exception as e:
            logger.error(f"Failed to rebalance agents: {e}")
            return {"success": False, "error": str(e)}
