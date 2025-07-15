"""Directory Utilities

Infrastructure utilities for directory management following DDD principles.
"""

from pathlib import Path
from typing import Optional

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


def ensure_brain_dir(brain_dir: Optional[str] = None) -> Path:
    """
    Ensure brain directory exists.
    
    This is an infrastructure utility function that handles file system paths
    and directory creation concerns.
    
    Args:
        brain_dir: Optional path to brain directory
        
    Returns:
        Path to the brain directory
    """
    if brain_dir is None:
        project_root = _find_project_root()
        brain_dir = project_root / ".cursor" / "brain"
    else:
        brain_dir = Path(brain_dir)
    
    brain_dir.mkdir(parents=True, exist_ok=True)
    return brain_dir