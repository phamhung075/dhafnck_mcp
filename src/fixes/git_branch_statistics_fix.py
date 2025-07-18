"""
Fix for Git Branch Statistics Error
Converts sqlite3.Row objects to dictionaries to prevent AttributeError
"""
from typing import Dict, Any, Optional, List
import sqlite3


def row_to_dict(row: Any) -> Optional[Dict[str, Any]]:
    """
    Convert sqlite3.Row or similar object to dictionary
    
    Args:
        row: sqlite3.Row or dict-like object
        
    Returns:
        Dictionary representation of the row
    """
    if row is None:
        return None
    
    # Check if it's already a dict
    if isinstance(row, dict):
        return row
    
    # Try standard sqlite3.Row conversion
    try:
        return dict(row)
    except:
        pass
    
    # Try using keys() method if available
    if hasattr(row, 'keys') and callable(row.keys):
        try:
            return {key: row[key] for key in row.keys()}
        except:
            pass
    
    # Last resort - extract attributes
    result = {}
    for attr in dir(row):
        if not attr.startswith('_'):
            try:
                value = getattr(row, attr)
                if not callable(value):
                    result[attr] = value
            except:
                pass
    
    return result if result else None


class GitBranchStatisticsRepository:
    """Repository for git branch statistics with fixed Row handling"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_statistics(self, project_id: str, git_branch_id: str) -> Dict[str, Any]:
        """
        Get statistics for a git branch with proper Row to dict conversion
        
        Args:
            project_id: Project ID
            git_branch_id: Git branch ID
            
        Returns:
            Dictionary containing branch statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get task statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                    SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) as todo_tasks,
                    SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_tasks
                FROM tasks
                WHERE git_branch_id = ?
            """, (git_branch_id,))
            
            stats_row = cursor.fetchone()
            
            # Convert Row to dict
            stats = row_to_dict(stats_row) or {
                'total_tasks': 0,
                'completed_tasks': 0,
                'in_progress_tasks': 0,
                'todo_tasks': 0,
                'blocked_tasks': 0
            }
            
            # Calculate progress percentage safely
            total = stats.get('total_tasks', 0)
            completed = stats.get('completed_tasks', 0)
            progress_percentage = (completed / total * 100) if total > 0 else 0.0
            
            # Get task breakdown by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM tasks
                WHERE git_branch_id = ?
                GROUP BY priority
            """, (git_branch_id,))
            
            priority_breakdown = {}
            for row in cursor.fetchall():
                row_dict = row_to_dict(row)
                if row_dict:
                    priority_breakdown[row_dict['priority']] = row_dict['count']
            
            # Get branch details
            cursor.execute("""
                SELECT created_at, updated_at
                FROM git_branchs
                WHERE id = ? AND project_id = ?
            """, (git_branch_id, project_id))
            
            branch_row = cursor.fetchone()
            branch_details = row_to_dict(branch_row) or {}
            
            # Build response
            return {
                "success": True,
                "git_branch_id": git_branch_id,
                "statistics": {
                    "git_branch_id": git_branch_id,
                    "total_tasks": stats.get('total_tasks', 0),
                    "completed_tasks": stats.get('completed_tasks', 0),
                    "in_progress_tasks": stats.get('in_progress_tasks', 0),
                    "todo_tasks": stats.get('todo_tasks', 0),
                    "blocked_tasks": stats.get('blocked_tasks', 0),
                    "progress_percentage": round(progress_percentage, 2),
                    "task_breakdown": {
                        "by_status": {
                            "todo": stats.get('todo_tasks', 0),
                            "in_progress": stats.get('in_progress_tasks', 0),
                            "done": stats.get('completed_tasks', 0),
                            "blocked": stats.get('blocked_tasks', 0)
                        },
                        "by_priority": priority_breakdown
                    },
                    "created_at": branch_details.get('created_at'),
                    "last_activity": branch_details.get('updated_at')
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get branch statistics: {str(e)}",
                "git_branch_id": git_branch_id
            }
        finally:
            conn.close()


# Patch for existing repository
def patch_git_branch_repository():
    """
    Monkey patch to fix existing GitBranchRepository
    This can be applied at runtime to fix the issue
    """
    try:
        from src.infrastructure.git_branch_repository import GitBranchRepository
        
        # Save original method
        original_get_statistics = GitBranchRepository.get_statistics
        
        # Create patched version
        def patched_get_statistics(self, project_id: str, git_branch_id: str):
            # Use our fixed implementation
            fixed_repo = GitBranchStatisticsRepository(self.db_path)
            return fixed_repo.get_statistics(project_id, git_branch_id)
        
        # Apply patch
        GitBranchRepository.get_statistics = patched_get_statistics
        
        return True
    except Exception as e:
        print(f"Failed to patch GitBranchRepository: {e}")
        return False