"""
Context Hierarchy Validator

Validates context creation requirements and provides user-friendly guidance
for the 4-tier hierarchy: Global → Project → Branch → Task
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from ...domain.value_objects.context_enums import ContextLevel

logger = logging.getLogger(__name__)


class ContextHierarchyValidator:
    """Validates context hierarchy requirements and provides guidance."""
    
    def __init__(self, global_repo, project_repo, branch_repo, task_repo):
        """Initialize with context repositories."""
        self.global_repo = global_repo
        self.project_repo = project_repo
        self.branch_repo = branch_repo
        self.task_repo = task_repo
    
    def validate_hierarchy_requirements(
        self, 
        level: ContextLevel, 
        context_id: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate that parent contexts exist before creating a child context.
        
        Returns:
            Tuple of (is_valid, error_message, guidance)
        """
        if level == ContextLevel.GLOBAL:
            # Global context has no parent - always valid
            return True, None, None
        
        elif level == ContextLevel.PROJECT:
            # Project requires global context
            return self._validate_project_requirements(context_id)
        
        elif level == ContextLevel.BRANCH:
            # Branch requires project context
            return self._validate_branch_requirements(context_id, data)
        
        elif level == ContextLevel.TASK:
            # Task requires branch context
            return self._validate_task_requirements(context_id, data)
        
        return False, f"Unknown context level: {level}", None
    
    def _validate_project_requirements(self, project_id: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate project context requirements."""
        # Check if global context exists
        try:
            global_context = self.global_repo.get("global_singleton")
            if not global_context:
                return False, "Global context not found", {
                    "error": "Cannot create project context without global context",
                    "explanation": "The system requires a global context to exist before creating project contexts. This ensures organization-wide settings are in place.",
                    "required_action": "Create global context first",
                    "step_by_step": [
                        {
                            "step": 1,
                            "description": "Create global context",
                            "command": 'manage_context(action="create", level="global", context_id="global_singleton", data={"autonomous_rules": {}, "security_policies": {}})'
                        },
                        {
                            "step": 2,
                            "description": "Then create your project context",
                            "command": f'manage_context(action="create", level="project", context_id="{project_id}", data={{"project_name": "Your Project"}})'
                        }
                    ]
                }
            return True, None, None
        except Exception as e:
            logger.debug(f"Global context check error: {e}")
            # If global context doesn't exist, provide guidance
            return False, "Global context must be created first", {
                "error": "Global context is required before creating project contexts",
                "explanation": "The 4-tier hierarchy requires: Global → Project → Branch → Task",
                "required_action": "Create global context",
                "command": 'manage_context(action="create", level="global", context_id="global_singleton", data={"autonomous_rules": {}, "security_policies": {}})'
            }
    
    def _validate_branch_requirements(self, branch_id: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate branch context requirements."""
        # Branch needs project_id in data
        project_id = data.get("project_id") or data.get("parent_project_id")
        
        if not project_id:
            return False, "Branch context requires project_id", {
                "error": "Missing required field: project_id",
                "explanation": "Branch contexts must be associated with a project. If the branch already exists, project_id will be auto-detected.",
                "required_fields": {
                    "project_id": "The ID of the parent project (auto-detected if branch exists)"
                },
                "auto_detection": "If you're creating a context for an existing branch, the system will attempt to auto-detect the project_id from the branch entity.",
                "example": f'manage_context(action="create", level="branch", context_id="{branch_id}", data={{"git_branch_name": "feature/branch"}})',
                "example_with_project": f'manage_context(action="create", level="branch", context_id="{branch_id}", data={{"project_id": "your-project-id", "git_branch_name": "feature/branch"}})'
            }
        
        # Check if project context exists
        try:
            project_context = self.project_repo.get(project_id)
            if not project_context:
                return False, f"Project context not found: {project_id}", {
                    "error": f"Parent project context '{project_id}' does not exist",
                    "explanation": "Branch contexts require their parent project context to exist first",
                    "hierarchy": "Global → Project → Branch → Task",
                    "required_actions": [
                        {
                            "step": 1,
                            "description": "Ensure global context exists",
                            "command": 'manage_context(action="get", level="global", context_id="global_singleton")'
                        },
                        {
                            "step": 2,
                            "description": "Create project context if needed",
                            "command": f'manage_context(action="create", level="project", context_id="{project_id}", data={{"project_name": "Your Project"}})'
                        },
                        {
                            "step": 3,
                            "description": "Then create your branch context",
                            "command": f'manage_context(action="create", level="branch", context_id="{branch_id}", data={{"project_id": "{project_id}", "git_branch_name": "your-branch"}})'
                        }
                    ]
                }
            return True, None, None
        except Exception as e:
            logger.debug(f"Project context check error: {e}")
            return False, "Project context must exist first", {
                "error": f"Cannot verify project context: {project_id}",
                "suggestion": f"Create the project context first, then retry creating the branch context"
            }
    
    def _validate_task_requirements(self, task_id: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate task context requirements."""
        # Task needs branch_id
        branch_id = (data.get("branch_id") or 
                    data.get("parent_branch_id") or
                    data.get("git_branch_id"))
        
        if not branch_id:
            return False, "Task context requires branch_id", {
                "error": "Missing required field: branch_id (or parent_branch_id)",
                "explanation": "Task contexts must be associated with a git branch (task tree)",
                "required_fields": {
                    "branch_id": "The ID of the parent git branch",
                    "alternative_names": ["parent_branch_id", "git_branch_id"]
                },
                "example": f'manage_context(action="create", level="task", context_id="{task_id}", data={{"branch_id": "your-branch-id", "task_data": {{"title": "Task Title"}}}})',
                "tip": "You can find branch IDs using: manage_git_branch(action=\"list\", project_id=\"your-project-id\")"
            }
        
        # Check if branch context exists
        try:
            branch_context = self.branch_repo.get(branch_id)
            if not branch_context:
                # Get project ID from the task if possible
                project_hint = ""
                if "project_id" in data:
                    project_hint = f", project_id=\"{data['project_id']}\""
                
                return False, f"Branch context not found: {branch_id}", {
                    "error": f"Parent branch context '{branch_id}' does not exist",
                    "explanation": "Task contexts require their parent branch context to exist first",
                    "hierarchy": "Global → Project → Branch → Task",
                    "context_creation_order": [
                        "1. Global context (singleton)",
                        "2. Project context",  
                        "3. Branch context",
                        "4. Task context"
                    ],
                    "required_actions": [
                        {
                            "step": 1,
                            "description": "Create branch context first",
                            "command": f'manage_context(action="create", level="branch", context_id="{branch_id}", data={{"project_id": "your-project-id"{project_hint}}})'
                        },
                        {
                            "step": 2,
                            "description": "Then create your task context",
                            "command": f'manage_context(action="create", level="task", context_id="{task_id}", data={{"branch_id": "{branch_id}", "task_data": {{"title": "Your Task"}}}})'
                        }
                    ],
                    "alternative": "If you're unsure of the branch_id, list available branches using manage_git_branch"
                }
            return True, None, None
        except Exception as e:
            logger.debug(f"Branch context check error: {e}")
            return False, "Branch context must exist first", {
                "error": f"Cannot verify branch context: {branch_id}",
                "suggestion": "Create the branch context first, then retry creating the task context"
            }
    
    def get_hierarchy_status(self) -> Dict[str, Any]:
        """Get the current status of the context hierarchy."""
        status = {
            "hierarchy_levels": ["global", "project", "branch", "task"],
            "current_state": {}
        }
        
        # Check global
        try:
            global_ctx = self.global_repo.get("global_singleton")
            status["current_state"]["global"] = {
                "exists": global_ctx is not None,
                "id": "global_singleton"
            }
        except:
            status["current_state"]["global"] = {"exists": False}
        
        # Get counts for other levels
        try:
            status["current_state"]["projects"] = {
                "count": len(self.project_repo.list()),
                "hint": "Use manage_project(action='list') for details"
            }
        except:
            status["current_state"]["projects"] = {"count": 0}
        
        try:
            status["current_state"]["branches"] = {
                "count": len(self.branch_repo.list()),
                "hint": "Use manage_git_branch(action='list') for details"
            }
        except:
            status["current_state"]["branches"] = {"count": 0}
        
        try:
            status["current_state"]["tasks"] = {
                "count": len(self.task_repo.list()),
                "hint": "Use manage_task(action='list') for details"
            }
        except:
            status["current_state"]["tasks"] = {"count": 0}
        
        return status