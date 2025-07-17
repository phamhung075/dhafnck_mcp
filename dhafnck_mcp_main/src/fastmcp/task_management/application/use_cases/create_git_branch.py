"""Create Git Branch Use Case"""

from typing import Dict, Any
from datetime import datetime, timezone
from ...domain.repositories.project_repository import ProjectRepository


class CreateGitBranchUseCase:
    """Use case for creating a new git branch within a project"""
    
    def __init__(self, project_repository: ProjectRepository):
        self._project_repository = project_repository
    
    async def execute(self, project_id: str, git_branch_name: str, branch_name: str, branch_description: str = "") -> Dict[str, Any]:
        """Execute the create git branch use case"""
        
        project = await self._project_repository.find_by_id(project_id)
        
        if not project:
            return {
                "success": False,
                "error": f"Project with ID '{project_id}' not found"
            }
        
        try:
            # Create git branch using domain logic
            git_branch = project.create_git_branch(
                git_branch_name=git_branch_name,
                name=branch_name,
                description=branch_description
            )
            
            # Save updated project
            await self._project_repository.update(project)
            
            return {
                "success": True,
                "git_branch": {
                    "id": git_branch.id,
                    "name": git_branch.name,
                    "description": git_branch.description,
                    "project_id": git_branch.project_id,
                    "created_at": git_branch.created_at.isoformat(),
                    "task_count": git_branch.get_task_count(),
                    "completed_tasks": git_branch.get_completed_task_count(),
                    "progress": git_branch.get_progress_percentage()
                },
                "message": f"Git branch '{git_branch_name}' created successfully"
            }
        
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }