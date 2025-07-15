"""Hierarchical Context Repository Factory for Context Management System"""

from typing import Optional
from pathlib import Path
import os

from .sqlite.hierarchical_context_repository import SQLiteHierarchicalContextRepository
# Removed problematic tool_path import


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
    return Path("/home/daihungpham/agentic-project")


class HierarchicalContextRepositoryFactory:
    """Factory for creating hierarchical context repositories with proper database configuration"""
    
    def __init__(self, base_path: Optional[str] = None, project_root: Optional[Path] = None):
        """
        Initialize hierarchical context repository factory
        
        Args:
            base_path: Base path for database storage (defaults to project root)
            project_root: Injected project root for testing or custom environments
        """
        self.project_root = project_root or _find_project_root()
        self.base_path = base_path or str(self.project_root / "dhafnck_mcp_main" / "database" / "data")
    
    def create_hierarchical_context_repository(self, db_path: Optional[str] = None) -> SQLiteHierarchicalContextRepository:
        """
        Create a hierarchical context repository
        
        Args:
            db_path: Custom database path (optional)
            
        Returns:
            SQLiteHierarchicalContextRepository instance
        """
        if not db_path:
            env_db_path = os.getenv("MCP_DB_PATH")
            if env_db_path:
                db_path = env_db_path
            else:
                db_path = str(self.project_root / "dhafnck_mcp_main" / "database" / "data" / "dhafnck_mcp.db")
        
        return SQLiteHierarchicalContextRepository(db_path=db_path)
    
    def validate_database_exists(self) -> bool:
        """
        Validate if database file exists
        
        Returns:
            True if database exists
        """
        env_db_path = os.getenv("MCP_DB_PATH")
        if env_db_path:
            db_path = Path(env_db_path)
        else:
            db_path = self.project_root / "dhafnck_mcp_main" / "database" / "data" / "dhafnck_mcp.db"
        return db_path.exists()
    
    def get_database_path(self) -> str:
        """
        Get the database path
        
        Returns:
            Full path to database file
        """
        env_db_path = os.getenv("MCP_DB_PATH")
        if env_db_path:
            return env_db_path
        else:
            return str(self.project_root / "dhafnck_mcp_main" / "database" / "data" / "dhafnck_mcp.db")