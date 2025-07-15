"""List Projects Use Case"""

from typing import Dict, Any, List
from ...domain.repositories.project_repository import ProjectRepository


class ListProjectsUseCase:
    """Use case for listing all projects"""
    
    def __init__(self, project_repository: ProjectRepository):
        self._project_repository = project_repository
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the list projects use case"""
        
        projects = await self._project_repository.find_all()
        
        project_list = []
        for project in projects:
            project_info = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "task_trees_count": len(project.task_trees),
                "registered_agents_count": len(project.registered_agents),
                "active_assignments": len(project.agent_assignments),
                "active_sessions": len(project.active_work_sessions)
            }
            project_list.append(project_info)
        
        return {
            "success": True,
            "projects": project_list,
            "count": len(project_list)
        }