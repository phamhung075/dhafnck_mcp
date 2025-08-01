"""Subtask Repository Factory for Hierarchical Storage with User Support"""

from typing import Optional
from pathlib import Path
import os

from ...domain.repositories.subtask_repository import SubtaskRepository
from .orm.subtask_repository import ORMSubtaskRepository


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


class SubtaskRepositoryFactory:
    """Factory for creating subtask repositories with hierarchical user/project/tree structure"""
    
    def __init__(self, base_path: Optional[str] = None, default_user_id: str = "default_id", 
                 project_root: Optional[Path] = None):
        """
        Initialize subtask repository factory
        
        Args:
            base_path: Base path for subtask storage (defaults to project root)
            default_user_id: Default user ID for single-user mode
            project_root: Injected project root for testing or custom environments
        """
        self.project_root = project_root or _find_project_root()
        self.base_path = base_path or str(self.project_root / ".cursor" / "rules" / "subtasks")
        self.default_user_id = default_user_id
    
    @classmethod
    def create(cls, project_id: str = "test-project", git_branch_name: str = "main", 
               user_id: str = "test-user") -> SubtaskRepository:
        """
        Static factory method for creating subtask repositories (for integration tests)
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
            
        Returns:
            SubtaskRepository instance
        """
        factory = cls()
        return factory.create_subtask_repository(project_id, git_branch_name, user_id)
    
    def create_subtask_repository(self, project_id: str, git_branch_name: str = "main", user_id: Optional[str] = None) -> SubtaskRepository:
        """
        Create a subtask repository for specific user/project/task tree
        
        Args:
            project_id: Project identifier (REQUIRED)
            git_branch_name: Task tree identifier (defaults to "main")
            user_id: User identifier (defaults to default_user_id)
            
        Returns:
            SubtaskRepository instance scoped to user/project/tree
        """
        if not project_id:
            raise ValueError("project_id is required")
        
        if not git_branch_name:
            git_branch_name = "main"
            
        if not user_id:
            user_id = self.default_user_id
        
        # Always use ORM repository
        return ORMSubtaskRepository()
    
    def create_sqlite_subtask_repository(self, project_id: str, git_branch_name: str = "main", 
                                        user_id: Optional[str] = None, db_path: Optional[str] = None) -> SubtaskRepository:
        """
        Create a subtask repository (now always uses ORM)
        
        Args:
            project_id: Project identifier (REQUIRED)
            git_branch_name: Task tree identifier (defaults to "main")
            user_id: User identifier (defaults to default_user_id)
            db_path: Custom database path (optional, ignored for ORM)
            
        Returns:
            ORMSubtaskRepository instance
        """
        if not project_id:
            raise ValueError("project_id is required")
        
        if not git_branch_name:
            git_branch_name = "main"
            
        if not user_id:
            user_id = self.default_user_id
        
        # Always use ORM repository
        return ORMSubtaskRepository()
    
    def create_orm_subtask_repository(self) -> SubtaskRepository:
        """
        Create an ORM subtask repository
        
        Returns:
            ORMSubtaskRepository instance
        """
        return ORMSubtaskRepository()
    
    def validate_user_project_tree(self, project_id: str, git_branch_name: str, user_id: Optional[str] = None) -> bool:
        """
        Validate if user/project/task tree combination exists
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
            
        Returns:
            True if valid combination exists (for SQLite, always True if DB exists)
        """
        if not user_id:
            user_id = self.default_user_id
        
        # Always return True for ORM repositories
        return True
    
    def get_subtask_db_path(self, project_id: str, git_branch_name: str = "main", user_id: Optional[str] = None) -> str:
        """
        Get the database path for a specific user/project/tree combination
        
        Args:
            project_id: Project identifier
            git_branch_name: Task tree identifier
            user_id: User identifier
            
        Returns:
            Full path to database file
        """
        if not user_id:
            user_id = self.default_user_id
        
        env_db_path = os.getenv("MCP_DB_PATH")
        if env_db_path:
            return env_db_path
        else:
            return str(self.project_root / "dhafnck_mcp_main" / "database" / "data" / "dhafnck_mcp.db")