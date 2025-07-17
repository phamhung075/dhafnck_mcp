"""
Service for managing Git Branches
"""
from typing import Dict, Any, Optional

from ...domain.repositories.project_repository import ProjectRepository
from ...domain.entities.git_branch import GitBranch
from ...infrastructure.repositories.project_repository_factory import GlobalRepositoryManager

class GitBranchService:
    def __init__(self, project_repo: Optional[ProjectRepository] = None):
        self._project_repo = project_repo or GlobalRepositoryManager.get_default()
        # Initialize git branch repository
        from ...infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
        self._git_branch_repo = ORMGitBranchRepository()

    async def create_git_branch(self, project_id: str, branch_name: str, description: str = "") -> Dict[str, Any]:
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
            
        # Check if branch already exists using the repository
        existing_branch = await self._git_branch_repo.find_by_name(project_id, branch_name)
        if existing_branch:
            return {"success": False, "error": f"Git branch '{branch_name}' already exists in project {project_id}"}

        # Create branch using the repository which properly persists it
        git_branch = await self._git_branch_repo.create_branch(project_id, branch_name, description)
        
        # Also add to project entity for consistency
        project.add_git_branch(git_branch)
        await self._project_repo.update(project)
        
        # Return format expected by integration test
        return {
            "success": True, 
            "git_branch": {
                "id": git_branch.id,
                "name": git_branch.name,
                "description": git_branch.description,
                "project_id": git_branch.project_id
            },
            "message": f"Git branch '{branch_name}' created successfully"
        }

    async def get_git_branch(self, project_id: str, branch_name: str) -> Dict[str, Any]:
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
        
        git_branch = project.get_git_branch(branch_name)
        if not git_branch:
            return {"success": False, "error": f"Git branch '{branch_name}' not found in project {project_id}"}
            
        return {"success": True, "git_branch": git_branch.to_dict()}

    async def list_git_branchs(self, project_id: str) -> Dict[str, Any]:
        project = await self._project_repo.find_by_id(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}
            
        return {"success": True, "git_branchs": [branch.to_dict() for branch in project.git_branchs.values()]} 