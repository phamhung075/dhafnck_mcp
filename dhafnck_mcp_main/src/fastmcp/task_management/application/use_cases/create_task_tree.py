"""Create Task Tree Use Case"""

from typing import Dict, Any
from datetime import datetime, timezone
from ...domain.repositories.project_repository import ProjectRepository


class CreateTaskTreeUseCase:
    """Use case for creating a new task tree within a project"""
    
    def __init__(self, project_repository: ProjectRepository):
        self._project_repository = project_repository
    
    async def execute(self, project_id: str, git_branch_name: str, tree_name: str, tree_description: str = "") -> Dict[str, Any]:
        """Execute the create task tree use case"""
        
        project = await self._project_repository.find_by_id(project_id)
        
        if not project:
            return {
                "success": False,
                "error": f"Project with ID '{project_id}' not found"
            }
        
        try:
            # Create task tree using domain logic
            task_tree = project.create_task_tree(
                git_branch_name=git_branch_name,
                name=tree_name,
                description=tree_description
            )
            
            # Save updated project
            await self._project_repository.update(project)
            
            return {
                "success": True,
                "task_tree": {
                    "id": task_tree.id,
                    "name": task_tree.name,
                    "description": task_tree.description,
                    "project_id": task_tree.project_id,
                    "created_at": task_tree.created_at.isoformat(),
                    "task_count": task_tree.get_task_count(),
                    "completed_tasks": task_tree.get_completed_task_count(),
                    "progress": task_tree.get_progress_percentage()
                },
                "message": f"Task tree '{git_branch_name}' created successfully"
            }
        
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }