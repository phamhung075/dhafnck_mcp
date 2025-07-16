"""SQLite Git Branch Repository Implementation"""

import sqlite3
import json
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from ....domain.repositories.git_branch_repository import GitBranchRepository
from ....domain.entities.task_tree import TaskTree
from ....domain.value_objects.task_status import TaskStatus
from ....domain.value_objects.priority import Priority
# Removed problematic tool_path import
from ...database.database_source_manager import get_database_path, get_database_info

logger = logging.getLogger(__name__)


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


class SQLiteGitBranchRepository(GitBranchRepository):
    """SQLite-based implementation of GitBranchRepository using new simplified schema"""
    
    def __init__(self, db_path: Optional[str] = None, user_id: str = "default_id"):
        """
        Initialize SQLiteGitBranchRepository
        
        Args:
            db_path: Path to SQLite database file
            user_id: User identifier
        """
        self.user_id = user_id
        project_root = _find_project_root()
        
        # Use database source manager for single source of truth
        if db_path:
            # If explicit path provided, use it (for testing/override)
            self._db_path = str(Path(db_path) if Path(db_path).is_absolute() else (project_root / db_path))
        else:
            # Use database source manager to determine correct database
            self._db_path = get_database_path()
        
        # Log database info
        db_info = get_database_info()
        logger.info(f"SQLiteGitBranchRepository using db_path: {self._db_path}")
        logger.info(f"Database mode: {db_info['mode']}, is_test: {db_info['is_test']}")
        
        # Ensure database exists and schema is initialized
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with git branch schema"""
        try:
            # Ensure database directory exists
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            
            # Create database if it doesn't exist
            if not os.path.exists(self._db_path):
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute("SELECT 1")  # Create empty database
                logger.info(f"Created new database at {self._db_path}")
            
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _row_to_task_tree(self, row: sqlite3.Row) -> TaskTree:
        """Convert a database row to a TaskTree domain object"""
        # Convert sqlite3.Row to dictionary to avoid attribute errors
        row_dict = dict(row)
        
        # Parse timestamps
        created_at = datetime.fromisoformat(row_dict['created_at'].replace('Z', '+00:00')) if row_dict['created_at'] else datetime.now(timezone.utc)
        updated_at = datetime.fromisoformat(row_dict['updated_at'].replace('Z', '+00:00')) if row_dict['updated_at'] else datetime.now(timezone.utc)
        
        # Create TaskTree entity
        task_tree = TaskTree(
            id=row_dict['id'],
            name=row_dict['name'],
            description=row_dict['description'] or '',
            project_id=row_dict['project_id'],
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Set additional fields
        task_tree.assigned_agent_id = row_dict.get('assigned_agent_id')
        task_tree.priority = Priority(row_dict.get('priority', 'medium'))
        task_tree.status = TaskStatus(row_dict.get('status', 'todo'))
        
        return task_tree
    
    def _task_tree_to_dict(self, task_tree: TaskTree) -> Dict[str, Any]:
        """Convert TaskTree to dictionary for database storage"""
        return {
            'id': task_tree.id,
            'project_id': task_tree.project_id,
            'name': task_tree.name,
            'description': task_tree.description,
            'created_at': task_tree.created_at.isoformat(),
            'updated_at': task_tree.updated_at.isoformat(),
            'assigned_agent_id': task_tree.assigned_agent_id,
            'priority': task_tree.priority.value if hasattr(task_tree.priority, 'value') else str(task_tree.priority),
            'status': task_tree.status.value if hasattr(task_tree.status, 'value') else str(task_tree.status),
            'metadata': json.dumps({}),
            'task_count': task_tree.get_task_count(),
            'completed_task_count': task_tree.get_completed_task_count()
        }
    
    # Repository interface implementation
    
    async def save(self, git_branch: TaskTree) -> None:
        """Save a git branch to the repository"""
        with self._get_connection() as conn:
            data = self._task_tree_to_dict(git_branch)
            
            # Check if branch exists
            existing = conn.execute(
                'SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?',
                (git_branch.id, git_branch.project_id)
            ).fetchone()
            
            if existing:
                # Update existing branch
                conn.execute('''
                    UPDATE project_task_trees SET 
                        name = ?, description = ?, updated_at = ?, assigned_agent_id = ?,
                        priority = ?, status = ?, metadata = ?, task_count = ?, completed_task_count = ?
                    WHERE id = ? AND project_id = ?
                ''', (
                    data['name'], data['description'], data['updated_at'], 
                    data['assigned_agent_id'], data['priority'], data['status'],
                    data['metadata'], data['task_count'], data['completed_task_count'],
                    data['id'], data['project_id']
                ))
            else:
                # Insert new branch
                conn.execute('''
                    INSERT INTO project_task_trees 
                    (id, project_id, name, description, created_at, updated_at, 
                     assigned_agent_id, priority, status, metadata, task_count, completed_task_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['id'], data['project_id'], data['name'], data['description'],
                    data['created_at'], data['updated_at'], data['assigned_agent_id'],
                    data['priority'], data['status'], data['metadata'],
                    data['task_count'], data['completed_task_count']
                ))
            
            conn.commit()
    
    async def find_by_id(self, project_id: str, branch_id: str) -> Optional[TaskTree]:
        """Find a git branch by its project and branch ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM project_task_trees WHERE id = ? AND project_id = ?',
                (branch_id, project_id)
            ).fetchone()
            
            if not row:
                return None
            
            return self._row_to_task_tree(row)
    
    async def find_by_name(self, project_id: str, branch_name: str) -> Optional[TaskTree]:
        """Find a git branch by its project and branch name"""
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM project_task_trees WHERE name = ? AND project_id = ?',
                (branch_name, project_id)
            ).fetchone()
            
            if not row:
                return None
            
            return self._row_to_task_tree(row)
    
    async def find_all_by_project(self, project_id: str) -> List[TaskTree]:
        """Find all git branches for a project"""
        with self._get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM project_task_trees WHERE project_id = ? ORDER BY created_at DESC',
                (project_id,)
            ).fetchall()
            
            branches = []
            for row in rows:
                try:
                    branch = self._row_to_task_tree(row)
                    branches.append(branch)
                except Exception as e:
                    logger.error(f"Error loading branch {row['id']}: {e}")
                    continue
            
            return branches
    
    async def find_all(self) -> List[TaskTree]:
        """Find all git branches"""
        with self._get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM project_task_trees ORDER BY created_at DESC'
            ).fetchall()
            
            branches = []
            for row in rows:
                try:
                    branch = self._row_to_task_tree(row)
                    branches.append(branch)
                except Exception as e:
                    logger.error(f"Error loading branch {row['id']}: {e}")
                    continue
            
            return branches
    
    async def delete(self, project_id: str, branch_id: str) -> bool:
        """Delete a git branch by its project and branch ID"""
        with self._get_connection() as conn:
            # Check if branch exists
            existing = conn.execute(
                'SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?',
                (branch_id, project_id)
            ).fetchone()
            
            if not existing:
                return False
            
            # Delete branch
            conn.execute(
                'DELETE FROM project_task_trees WHERE id = ? AND project_id = ?',
                (branch_id, project_id)
            )
            conn.commit()
            
            return True
    
    async def exists(self, project_id: str, branch_id: str) -> bool:
        """Check if a git branch exists"""
        with self._get_connection() as conn:
            result = conn.execute(
                'SELECT 1 FROM project_task_trees WHERE id = ? AND project_id = ?',
                (branch_id, project_id)
            ).fetchone()
            return result is not None
    
    async def update(self, git_branch: TaskTree) -> None:
        """Update an existing git branch"""
        # Update timestamp
        git_branch.updated_at = datetime.now(timezone.utc)
        await self.save(git_branch)
    
    async def count_by_project(self, project_id: str) -> int:
        """Count total number of git branches for a project"""
        with self._get_connection() as conn:
            result = conn.execute(
                'SELECT COUNT(*) as count FROM project_task_trees WHERE project_id = ?',
                (project_id,)
            ).fetchone()
            return result['count'] if result else 0
    
    async def count_all(self) -> int:
        """Count total number of git branches"""
        with self._get_connection() as conn:
            result = conn.execute(
                'SELECT COUNT(*) as count FROM project_task_trees'
            ).fetchone()
            return result['count'] if result else 0
    
    async def find_by_assigned_agent(self, agent_id: str) -> List[TaskTree]:
        """Find git branches assigned to a specific agent"""
        with self._get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM project_task_trees WHERE assigned_agent_id = ? ORDER BY created_at DESC',
                (agent_id,)
            ).fetchall()
            
            branches = []
            for row in rows:
                try:
                    branch = self._row_to_task_tree(row)
                    branches.append(branch)
                except Exception as e:
                    logger.error(f"Error loading branch {row['id']}: {e}")
                    continue
            
            return branches
    
    async def find_by_status(self, project_id: str, status: str) -> List[TaskTree]:
        """Find git branches by status within a project"""
        with self._get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM project_task_trees WHERE project_id = ? AND status = ? ORDER BY created_at DESC',
                (project_id, status)
            ).fetchall()
            
            branches = []
            for row in rows:
                try:
                    branch = self._row_to_task_tree(row)
                    branches.append(branch)
                except Exception as e:
                    logger.error(f"Error loading branch {row['id']}: {e}")
                    continue
            
            return branches
    
    async def find_available_for_assignment(self, project_id: str) -> List[TaskTree]:
        """Find git branches that can be assigned to agents"""
        with self._get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM project_task_trees 
                WHERE project_id = ? 
                AND assigned_agent_id IS NULL 
                AND status IN ('todo', 'in_progress', 'review')
                ORDER BY priority DESC, created_at ASC
            ''', (project_id,)).fetchall()
            
            branches = []
            for row in rows:
                try:
                    branch = self._row_to_task_tree(row)
                    branches.append(branch)
                except Exception as e:
                    logger.error(f"Error loading branch {row['id']}: {e}")
                    continue
            
            return branches
    
    async def assign_agent(self, project_id: str, branch_id: str, agent_id: str) -> bool:
        """Assign an agent to a git branch"""
        with self._get_connection() as conn:
            # Check if branch exists
            existing = conn.execute(
                'SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?',
                (branch_id, project_id)
            ).fetchone()
            
            if not existing:
                return False
            
            # Update assignment
            conn.execute('''
                UPDATE project_task_trees 
                SET assigned_agent_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND project_id = ?
            ''', (agent_id, branch_id, project_id))
            
            conn.commit()
            return True
    
    async def unassign_agent(self, project_id: str, branch_id: str) -> bool:
        """Unassign the current agent from a git branch"""
        with self._get_connection() as conn:
            # Check if branch exists
            existing = conn.execute(
                'SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?',
                (branch_id, project_id)
            ).fetchone()
            
            if not existing:
                return False
            
            # Remove assignment
            conn.execute('''
                UPDATE project_task_trees 
                SET assigned_agent_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND project_id = ?
            ''', (branch_id, project_id))
            
            conn.commit()
            return True
    
    
    async def get_project_branch_summary(self, project_id: str) -> Dict[str, Any]:
        """Get summary of all branches in a project"""
        with self._get_connection() as conn:
            # Get basic stats
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_branches,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed_branches,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active_branches,
                    SUM(CASE WHEN assigned_agent_id IS NOT NULL THEN 1 ELSE 0 END) as assigned_branches,
                    SUM(task_count) as total_tasks,
                    SUM(completed_task_count) as total_completed_tasks
                FROM project_task_trees 
                WHERE project_id = ?
            ''', (project_id,)).fetchone()
            
            # Get status breakdown
            status_breakdown = {}
            status_rows = conn.execute('''
                SELECT status, COUNT(*) as count
                FROM project_task_trees 
                WHERE project_id = ?
                GROUP BY status
            ''', (project_id,)).fetchall()
            
            for row in status_rows:
                status_breakdown[row['status']] = row['count']
            
            # Calculate overall progress
            overall_progress = 0.0
            if stats['total_tasks'] and stats['total_tasks'] > 0:
                overall_progress = (stats['total_completed_tasks'] / stats['total_tasks']) * 100.0
            
            return {
                "project_id": project_id,
                "summary": {
                    "total_branches": stats['total_branches'],
                    "completed_branches": stats['completed_branches'],
                    "active_branches": stats['active_branches'],
                    "assigned_branches": stats['assigned_branches']
                },
                "tasks": {
                    "total_tasks": stats['total_tasks'],
                    "completed_tasks": stats['total_completed_tasks'],
                    "overall_progress_percentage": overall_progress
                },
                "status_breakdown": status_breakdown,
                "user_id": self.user_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def create_branch(self, project_id: str, branch_name: str, description: str = "") -> TaskTree:
        """Create a new git branch for a project"""
        # Generate unique branch ID
        import uuid
        branch_id = str(uuid.uuid4())
        
        now = datetime.now(timezone.utc)
        
        # Create TaskTree entity
        task_tree = TaskTree(
            id=branch_id,
            name=branch_name,
            description=description,
            project_id=project_id,
            created_at=now,
            updated_at=now
        )
        
        # Save to repository
        await self.save(task_tree)
        
        return task_tree
    
    
    # Implementation of abstract methods from GitBranchRepository interface
    
    async def create_git_branch(self, project_id: str, git_branch_name: str, git_branch_description: str = "") -> Dict[str, Any]:
        """Create a new git branch - implements abstract method"""
        try:
            task_tree = await self.create_branch(project_id, git_branch_name, git_branch_description)
            return {
                "success": True,
                "git_branch": {
                    "id": task_tree.id,
                    "name": task_tree.name,
                    "description": task_tree.description,
                    "project_id": task_tree.project_id,
                    "created_at": task_tree.created_at.isoformat(),
                    "updated_at": task_tree.updated_at.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error creating git branch: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "CREATE_FAILED"
            }
    
    async def get_git_branch_by_id(self, git_branch_id: str) -> Dict[str, Any]:
        """Get git branch by ID - implements abstract method"""
        try:
            # Need to get project_id from the branch itself
            with self._get_connection() as conn:
                row = conn.execute(
                    'SELECT project_id FROM project_task_trees WHERE id = ?',
                    (git_branch_id,)
                ).fetchone()
                
                if not row:
                    return {
                        "success": False,
                        "error": f"Git branch not found: {git_branch_id}",
                        "error_code": "NOT_FOUND"
                    }
                
                project_id = row['project_id']
            
            task_tree = await self.find_by_id(project_id, git_branch_id)
            if not task_tree:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_id}",
                    "error_code": "NOT_FOUND"
                }
            
            return {
                "success": True,
                "git_branch": {
                    "id": task_tree.id,
                    "name": task_tree.name,
                    "description": task_tree.description,
                    "project_id": task_tree.project_id,
                    "created_at": task_tree.created_at.isoformat(),
                    "updated_at": task_tree.updated_at.isoformat(),
                    "assigned_agent_id": task_tree.assigned_agent_id,
                    "status": str(task_tree.status),
                    "priority": str(task_tree.priority)
                }
            }
        except Exception as e:
            logger.error(f"Error getting git branch by ID: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "GET_FAILED"
            }
    
    async def get_git_branch_by_name(self, project_id: str, git_branch_name: str) -> Dict[str, Any]:
        """Get git branch by name within a project - implements abstract method"""
        try:
            task_tree = await self.find_by_name(project_id, git_branch_name)
            if not task_tree:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_name}",
                    "error_code": "NOT_FOUND"
                }
            
            return {
                "success": True,
                "git_branch": {
                    "id": task_tree.id,
                    "name": task_tree.name,
                    "description": task_tree.description,
                    "project_id": task_tree.project_id,
                    "created_at": task_tree.created_at.isoformat(),
                    "updated_at": task_tree.updated_at.isoformat(),
                    "assigned_agent_id": task_tree.assigned_agent_id,
                    "status": str(task_tree.status),
                    "priority": str(task_tree.priority)
                }
            }
        except Exception as e:
            logger.error(f"Error getting git branch by name: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "GET_FAILED"
            }
    
    async def list_git_branches(self, project_id: str) -> Dict[str, Any]:
        """List all git branches for a project - implements abstract method"""
        try:
            task_trees = await self.find_all_by_project(project_id)
            
            branches = []
            for task_tree in task_trees:
                branches.append({
                    "id": task_tree.id,
                    "name": task_tree.name,
                    "description": task_tree.description,
                    "project_id": task_tree.project_id,
                    "created_at": task_tree.created_at.isoformat(),
                    "updated_at": task_tree.updated_at.isoformat(),
                    "assigned_agent_id": task_tree.assigned_agent_id,
                    "status": str(task_tree.status),
                    "priority": str(task_tree.priority)
                })
            
            return {
                "success": True,
                "git_branches": branches,
                "count": len(branches)
            }
        except Exception as e:
            logger.error(f"Error listing git branches: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "LIST_FAILED"
            }
    
    async def update_git_branch(self, git_branch_id: str, git_branch_name: Optional[str] = None, git_branch_description: Optional[str] = None) -> Dict[str, Any]:
        """Update git branch information - implements abstract method"""
        try:
            # Get the branch first
            with self._get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM project_task_trees WHERE id = ?',
                    (git_branch_id,)
                ).fetchone()
                
                if not row:
                    return {
                        "success": False,
                        "error": f"Git branch not found: {git_branch_id}",
                        "error_code": "NOT_FOUND"
                    }
            
            # Convert to TaskTree and update fields
            task_tree = self._row_to_task_tree(row)
            
            if git_branch_name is not None:
                task_tree.name = git_branch_name
            if git_branch_description is not None:
                task_tree.description = git_branch_description
            
            # Save updated branch
            await self.update(task_tree)
            
            return {
                "success": True,
                "message": "Git branch updated successfully",
                "git_branch": {
                    "id": task_tree.id,
                    "name": task_tree.name,
                    "description": task_tree.description,
                    "project_id": task_tree.project_id,
                    "updated_at": task_tree.updated_at.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error updating git branch: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "UPDATE_FAILED"
            }
    
    async def delete_git_branch(self, project_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Delete a git branch - implements abstract method"""
        try:
            deleted = await self.delete(project_id, git_branch_id)
            
            if deleted:
                return {
                    "success": True,
                    "message": f"Git branch {git_branch_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_id}",
                    "error_code": "NOT_FOUND"
                }
        except Exception as e:
            logger.error(f"Error deleting git branch: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "DELETE_FAILED"
            }
    
    async def assign_agent_to_branch(self, project_id: str, agent_id: str, git_branch_name: str) -> Dict[str, Any]:
        """Assign an agent to a git branch - implements abstract method"""
        try:
            # Find branch by name first
            task_tree = await self.find_by_name(project_id, git_branch_name)
            if not task_tree:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_name}",
                    "error_code": "NOT_FOUND"
                }
            
            # Assign agent
            assigned = await self.assign_agent(project_id, task_tree.id, agent_id)
            
            if assigned:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} assigned to branch {git_branch_name}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to assign agent",
                    "error_code": "ASSIGN_FAILED"
                }
        except Exception as e:
            logger.error(f"Error assigning agent to branch: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "ASSIGN_FAILED"
            }
    
    async def unassign_agent_from_branch(self, project_id: str, agent_id: str, git_branch_name: str) -> Dict[str, Any]:
        """Unassign an agent from a git branch - implements abstract method"""
        try:
            # Find branch by name first
            task_tree = await self.find_by_name(project_id, git_branch_name)
            if not task_tree:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_name}",
                    "error_code": "NOT_FOUND"
                }
            
            # Unassign agent
            unassigned = await self.unassign_agent(project_id, task_tree.id)
            
            if unassigned:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} unassigned from branch {git_branch_name}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to unassign agent",
                    "error_code": "UNASSIGN_FAILED"
                }
        except Exception as e:
            logger.error(f"Error unassigning agent from branch: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "UNASSIGN_FAILED"
            }
    
    async def get_branch_statistics(self, project_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Get statistics for a git branch - implements abstract method"""
        # Directly use the internal method which returns the proper dict format
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM project_task_trees WHERE id = ? AND project_id = ?',
                (git_branch_id, project_id)
            ).fetchone()
            
            if not row:
                return {"error": "Branch not found"}
            
            # Convert sqlite3.Row to dictionary to avoid attribute errors
            row_dict = dict(row)
            
            progress = 0.0
            if row_dict.get('task_count') and row_dict['task_count'] > 0:
                progress = (row_dict.get('completed_task_count', 0) or 0) / row_dict['task_count'] * 100.0
            
            return {
                "branch_id": row_dict.get('id'),
                "branch_name": row_dict.get('name'),
                "project_id": row_dict.get('project_id'),
                "status": row_dict.get('status') or 'todo',
                "priority": row_dict.get('priority') or 'medium',
                "assigned_agent_id": row_dict.get('assigned_agent_id'),
                "task_count": row_dict.get('task_count') or 0,
                "completed_task_count": row_dict.get('completed_task_count') or 0,
                "progress_percentage": progress,
                "created_at": row_dict.get('created_at'),
                "updated_at": row_dict.get('updated_at')
            }
    
    async def archive_branch(self, project_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Archive a git branch - implements abstract method"""
        with self._get_connection() as conn:
            # Check if branch exists
            existing = conn.execute(
                'SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?',
                (git_branch_id, project_id)
            ).fetchone()
            
            if not existing:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_id}",
                    "error_code": "NOT_FOUND"
                }
            
            # Archive branch
            conn.execute('''
                UPDATE project_task_trees 
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND project_id = ?
            ''', (git_branch_id, project_id))
            
            conn.commit()
            return {
                "success": True,
                "message": f"Git branch {git_branch_id} archived successfully"
            }
    
    async def restore_branch(self, project_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Restore an archived git branch - implements abstract method"""
        with self._get_connection() as conn:
            # Check if branch exists
            existing = conn.execute(
                'SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?',
                (git_branch_id, project_id)
            ).fetchone()
            
            if not existing:
                return {
                    "success": False,
                    "error": f"Git branch not found: {git_branch_id}",
                    "error_code": "NOT_FOUND"
                }
            
            # Restore branch
            conn.execute('''
                UPDATE project_task_trees 
                SET status = 'todo', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND project_id = ?
            ''', (git_branch_id, project_id))
            
            conn.commit()
            return {
                "success": True,
                "message": f"Git branch {git_branch_id} restored successfully"
            }