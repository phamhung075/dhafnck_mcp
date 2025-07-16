"""Task Repository Factory for Hierarchical Storage with User Support"""

from typing import Optional
from pathlib import Path
import os

from ...domain.repositories.task_repository import TaskRepository
from .orm.task_repository import ORMTaskRepository


def _find_project_root() -> Path:
    """Find project root by looking for dhafnck_mcp_main directory"""
    current_path = Path(__file__).resolve()
    
    # Walk up the directory tree looking for dhafnck_mcp_main
    while current_path.parent != current_path:
        if (current_path / "dhafnck_mcp_main").exists():
            return current_path
        current_path = current_path.parent
    
    # If not found, use current working directory as fallback
    cwd = Path.cwd()
    if (cwd / "dhafnck_mcp_main").exists():
        return cwd
        
    # Last resort - use the directory containing dhafnck_mcp_main
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        if current_path.name == "dhafnck_mcp_main":
            return current_path.parent
        current_path = current_path.parent
    
    # Absolute fallback
    # Use environment variable or default data path
    data_path = os.environ.get('DHAFNCK_DATA_PATH', '/data')
    # If running in development, try to find project root
    if not os.path.exists(data_path):
        # Try current working directory
        cwd = Path.cwd()
        if (cwd / "dhafnck_mcp_main").exists():
            return cwd
        # Try parent directories
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / "dhafnck_mcp_main").exists():
                return current
            current = current.parent
        # Fall back to temp directory for safety
        return Path("/tmp/dhafnck_project")
    return Path(data_path)


class TaskRepositoryFactory:
    """Factory for creating task repositories with hierarchical user/project/tree structure"""
    
    def __init__(self, base_path: Optional[str] = None, default_user_id: str = "default_id", 
                 project_root: Optional[Path] = None):
        """
        Initialize repository factory
        
        Args:
            base_path: Base path for task storage (defaults to project root)
            default_user_id: Default user ID for single-user mode
            project_root: Injected project root for testing or custom environments
        """
        self.project_root = project_root or _find_project_root()
        self.base_path = base_path or str(self.project_root / ".cursor" / "rules" / "tasks")
        self.default_user_id = default_user_id
    
    def create_repository(self, project_id: str, git_branch_name: str = "main", user_id: Optional[str] = None) -> TaskRepository:
        """
        Create a task repository for specific user/project/task tree
        
        Args:
            project_id: Project identifier (REQUIRED)
            git_branch_name: Task tree identifier (defaults to "main")
            user_id: User identifier (defaults to default_user_id)
            
        Returns:
            TaskRepository instance scoped to user/project/tree
        """
        if not project_id:
            raise ValueError("project_id is required")
        
        if not git_branch_name:
            git_branch_name = "main"
            
        if not user_id:
            user_id = self.default_user_id
        
        # Always use ORM repository
        return ORMTaskRepository(
            project_id=project_id,
            git_branch_name=git_branch_name,
            user_id=user_id
        )

    def create_repository_with_git_branch_id(self, project_id: str, git_branch_name: str, user_id: str, git_branch_id: str) -> TaskRepository:
        """
        Create a task repository with a specific git_branch_id.
        
        This method creates a repository that is initialized with the git_branch_id directly,
        which is useful when the git_branch_id is known but context resolution is unreliable.
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
            git_branch_id: Specific git branch ID to use
            
        Returns:
            TaskRepository instance scoped to the git_branch_id
        """
        # Always use ORM repository
        return ORMTaskRepository(
            git_branch_id=git_branch_id,
            project_id=project_id,
            git_branch_name=git_branch_name,
            user_id=user_id
        )
    
    def create_sqlite_repository(self, project_id: str, git_branch_name: str = "main", 
                                user_id: Optional[str] = None, db_path: Optional[str] = None) -> TaskRepository:
        """
        Create a task repository (now always uses ORM)
        
        Args:
            project_id: Project identifier (REQUIRED)
            git_branch_name: Task tree identifier (defaults to "main")
            user_id: User identifier (defaults to default_user_id)
            db_path: Custom database path (optional, ignored for ORM)
            
        Returns:
            ORMTaskRepository instance
        """
        if not project_id:
            raise ValueError("project_id is required")
        
        if not git_branch_name:
            git_branch_name = "main"
            
        if not user_id:
            user_id = self.default_user_id
        
        # Always use ORM repository
        return ORMTaskRepository(
            project_id=project_id,
            git_branch_name=git_branch_name,
            user_id=user_id
        )
    
    def create_system_repository(self, db_path: Optional[str] = None) -> TaskRepository:
        """
        Create a system-level task repository with no context restrictions.
        Used for system operations that need to access all tasks regardless of context.
        
        Args:
            db_path: Custom database path (optional)
            
        Returns:
            TaskRepository instance with system-level access
        """
        # Always use ORM repository
        return ORMTaskRepository(
            project_id=None,
            git_branch_name=None,
            user_id=None
        )
    
    def get_all_user_repositories(self, user_id: Optional[str] = None) -> dict[str, dict[str, TaskRepository]]:
        """
        Get repositories for all projects and task trees for a specific user
        
        Args:
            user_id: User identifier (defaults to default_user_id)
            
        Returns:
            Dict structure: {project_id: {git_branch_name: repository}}
        """
        if not user_id:
            user_id = self.default_user_id
            
        repositories = {}
        
        user_path = Path(self.base_path) / user_id
        if not user_path.exists():
            return repositories
        
        # Scan for existing project directories under user
        for project_dir in user_path.iterdir():
            if project_dir.is_dir():
                project_id = project_dir.name
                repositories[project_id] = {}
                
                # Scan for task tree directories within project
                for tree_dir in project_dir.iterdir():
                    if tree_dir.is_dir() and (tree_dir / "tasks.json").exists():
                        git_branch_name = tree_dir.name
                        repositories[project_id][git_branch_name] = self.create_repository(
                            project_id, git_branch_name, user_id
                        )
        
        return repositories
    
    def validate_user_project_tree(self, project_id: str, git_branch_name: str, user_id: Optional[str] = None) -> bool:
        """
        Validate if user/project/task tree combination exists
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
            
        Returns:
            True if valid combination exists
        """
        if not user_id:
            user_id = self.default_user_id
            
        file_path = Path(self.base_path) / user_id / project_id / git_branch_name / "tasks.json"
        return file_path.parent.exists()
    
    def create_user_project_structure(self, project_id: str, git_branch_name: str = "main", user_id: Optional[str] = None) -> None:
        """
        Create directory structure for new user/project/tree combination
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
        """
        if not user_id:
            user_id = self.default_user_id
            
        file_path = Path(self.base_path) / user_id / project_id / git_branch_name / "tasks.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create empty tasks.json if it doesn't exist
        if not file_path.exists():
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"tasks": []}, f, indent=2)
    
    def get_task_file_path(self, project_id: str, git_branch_name: str = "main", user_id: Optional[str] = None) -> str:
        """
        Get the full file path for a specific user/project/tree combination
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
            
        Returns:
            Full path to tasks.json file
        """
        if not user_id:
            user_id = self.default_user_id
            
        return str(Path(self.base_path) / user_id / project_id / git_branch_name / "tasks.json")