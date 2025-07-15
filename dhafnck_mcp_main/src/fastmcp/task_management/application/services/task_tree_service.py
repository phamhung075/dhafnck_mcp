"""
Service for managing Task Trees (Git Branches)
"""
from typing import Dict, Any, Optional

from ...domain.repositories.project_repository import ProjectRepository
from ...domain.entities.task_tree import TaskTree
from ...infrastructure.repositories.project_repository_factory import GlobalRepositoryManager

class TaskTreeService:
    def __init__(self, project_repo: Optional[ProjectRepository] = None):
        self._project_repo = project_repo or GlobalRepositoryManager.get_default()

    async def create_task_tree(self, project_id: str, tree_name: str, description: str = "") -> Dict[str, Any]:
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
            
        if tree_name in project.task_trees:
            return {"success": False, "error": f"Task tree '{tree_name}' already exists in project {project_id}"}

        task_tree = TaskTree.create(name=tree_name, description=description, project_id=project_id)
        project.add_task_tree(task_tree)
        
        await self._project_repo.update(project)
        
        # Return format expected by integration test
        return {
            "success": True, 
            "git_branch": {
                "id": task_tree.id,
                "name": task_tree.name,
                "description": task_tree.description,
                "project_id": task_tree.project_id
            },
            "message": f"Git branch '{tree_name}' created successfully"
        }

    async def get_task_tree(self, project_id: str, tree_name: str) -> Dict[str, Any]:
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
        
        task_tree = project.get_task_tree(tree_name)
        if not task_tree:
            return {"success": False, "error": f"Task tree '{tree_name}' not found in project {project_id}"}
            
        return {"success": True, "task_tree": task_tree.to_dict()}

    async def list_task_trees(self, project_id: str) -> Dict[str, Any]:
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
            
        return {"success": True, "task_trees": [tree.to_dict() for tree in project.task_trees.values()]} 