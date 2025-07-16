"""SQLite Project Repository Implementation"""

import sqlite3
import json
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from ....domain.repositories.project_repository import ProjectRepository
from ....domain.entities.project import Project
from ....domain.entities.task_tree import TaskTree
from ....domain.entities.agent import Agent, AgentCapability, AgentStatus
from ....domain.value_objects.task_status import TaskStatus
from ....domain.value_objects.priority import Priority
# Removed problematic tool_path import
from ...database.database_source_manager import get_database_path, get_database_info
from ...database.database_initializer import initialize_database, reset_initialization_cache

logger = logging.getLogger(__name__)


class SQLiteProjectRepository(ProjectRepository):
    """SQLite-based implementation of ProjectRepository using new simplified schema"""
    
    def __init__(self, db_path: Optional[str] = None, user_id: str = "default_id"):
        """
        Initialize SQLiteProjectRepository
        
        Args:
            db_path: Path to SQLite database file
            user_id: User identifier for multi-user support
        """
        # Store user_id for filtering
        self.user_id = user_id
        
        # Use database source manager for single source of truth
        if db_path:
            # If explicit path provided, use it (for testing/override)
            self._db_path = str(Path(db_path).resolve()) if not Path(db_path).is_absolute() else str(db_path)
        else:
            # Use database source manager to determine correct database
            self._db_path = get_database_path()
        
        # Log database info
        db_info = get_database_info()
        logger.info(f"SQLiteProjectRepository using db_path: {self._db_path}")
        logger.info(f"Database mode: {db_info['mode']}, is_test: {db_info['is_test']}")
        logger.info(f"User ID: {self.user_id}")
        
        # Ensure database exists and schema is initialized
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database using the central initializer."""
        try:
            # The central initializer is idempotent and thread-safe
            initialize_database(self._db_path)
        except Exception as e:
            logger.critical(f"Failed to initialize database via central initializer: {e}", exc_info=True)
            raise

    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _project_row_to_domain(self, project_row: sqlite3.Row) -> Project:
        """Convert a database row to a Project domain object"""
        # Parse metadata
        metadata = json.loads(project_row['metadata']) if project_row['metadata'] else {}
        
        # Parse timestamps
        created_at = datetime.fromisoformat(project_row['created_at'].replace('Z', '+00:00')) if project_row['created_at'] else datetime.now(timezone.utc)
        updated_at = datetime.fromisoformat(project_row['updated_at'].replace('Z', '+00:00')) if project_row['updated_at'] else datetime.now(timezone.utc)
        
        # Create project entity
        project = Project(
            id=project_row['id'],
            name=project_row['name'],
            description=project_row['description'] or '',
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Load task trees
        project.task_trees = self._load_task_trees(project_row['id'])
        
        # Load agents
        project.registered_agents = self._load_agents(project_row['id'])
        
        # Load agent assignments
        project.agent_assignments = self._load_agent_assignments(project_row['id'])
        
        # Load cross-tree dependencies
        project.cross_tree_dependencies = self._load_cross_tree_dependencies(project_row['id'])
        
        # Load active work sessions
        project.active_work_sessions = self._load_work_sessions(project_row['id'])
        
        # Load resource locks
        project.resource_locks = self._load_resource_locks(project_row['id'])
        
        return project
    
    def _load_task_trees(self, project_id: str) -> Dict[str, TaskTree]:
        """Load task trees for a project"""
        task_trees = {}
        
        with self._get_connection() as conn:
            tree_rows = conn.execute(
                'SELECT * FROM project_task_trees WHERE project_id = ?',
                (project_id,)
            ).fetchall()
            
            for row in tree_rows:
                tree = TaskTree(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'] or '',
                    project_id=row['project_id'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(timezone.utc),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now(timezone.utc)
                )
                
                # Set additional fields  
                tree.assigned_agent_id = row['assigned_agent_id'] if row['assigned_agent_id'] else None
                tree.priority = Priority(row['priority'] if row['priority'] else 'medium')
                tree.status = TaskStatus(row['status'] if row['status'] else 'todo')
                
                task_trees[row['id']] = tree
        
        return task_trees
    
    def _load_agents(self, project_id: str) -> Dict[str, Agent]:
        """Load agents for a project"""
        agents = {}
        
        with self._get_connection() as conn:
            agent_rows = conn.execute(
                'SELECT * FROM project_agents WHERE project_id = ?',
                (project_id,)
            ).fetchall()
            
            for row in agent_rows:
                # Parse JSON fields
                capabilities = json.loads(row['capabilities'] if row['capabilities'] else '[]')
                specializations = json.loads(row['specializations'] if row['specializations'] else '[]')
                preferred_languages = json.loads(row['preferred_languages'] if row['preferred_languages'] else '[]')
                preferred_frameworks = json.loads(row['preferred_frameworks'] if row['preferred_frameworks'] else '[]')
                work_hours = json.loads(row['work_hours'] if row['work_hours'] else '{}')
                
                # Convert capabilities to enum
                capability_set = set()
                for cap in capabilities:
                    try:
                        capability_set.add(AgentCapability(cap))
                    except ValueError:
                        logger.warning(f"Unknown capability: {cap}")
                
                agent = Agent(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'] if row['description'] else '',
                    capabilities=capability_set,
                    specializations=specializations,
                    preferred_languages=preferred_languages,
                    preferred_frameworks=preferred_frameworks,
                    status=AgentStatus(row['status'] if row['status'] else 'available'),
                    max_concurrent_tasks=row['max_concurrent_tasks'] if row['max_concurrent_tasks'] else 1,
                    current_workload=row['current_workload'] if row['current_workload'] else 0,
                    completed_tasks=row['completed_tasks'] if row['completed_tasks'] else 0,
                    average_task_duration=row['average_task_duration'] if row['average_task_duration'] else None,
                    success_rate=row['success_rate'] if row['success_rate'] else 100.0,
                    work_hours=work_hours if work_hours else None,
                    timezone=row['timezone'] if row['timezone'] else 'UTC',
                    priority_preference=row['priority_preference'] if row['priority_preference'] else 'high',
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now()
                )
                
                # Add project and tree assignments
                agent.assigned_projects.add(project_id)
                
                agents[row['id']] = agent
        
        return agents
    
    def _load_agent_assignments(self, project_id: str) -> Dict[str, str]:
        """Load agent assignments for a project"""
        assignments = {}
        
        with self._get_connection() as conn:
            assignment_rows = conn.execute(
                'SELECT * FROM project_agent_assignments WHERE project_id = ?',
                (project_id,)
            ).fetchall()
            
            for row in assignment_rows:
                assignments[row['git_branch_id']] = row['agent_id']
        
        return assignments
    
    def _load_cross_tree_dependencies(self, project_id: str) -> Dict[str, set]:
        """Load cross-tree dependencies for a project"""
        dependencies = {}
        
        with self._get_connection() as conn:
            dep_rows = conn.execute(
                'SELECT * FROM project_cross_tree_dependencies WHERE project_id = ?',
                (project_id,)
            ).fetchall()
            
            for row in dep_rows:
                dependent_task_id = row['dependent_task_id']
                if dependent_task_id not in dependencies:
                    dependencies[dependent_task_id] = set()
                dependencies[dependent_task_id].add(row['prerequisite_task_id'])
        
        return dependencies
    
    def _load_work_sessions(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Load active work sessions for a project"""
        sessions = {}
        
        with self._get_connection() as conn:
            session_rows = conn.execute(
                'SELECT * FROM project_work_sessions WHERE project_id = ? AND status = ?',
                (project_id, 'active')
            ).fetchall()
            
            for row in session_rows:
                session_data = {
                    'id': row['id'],
                    'agent_id': row['agent_id'],
                    'task_id': row['task_id'],
                    'git_branch_id': row['git_branch_id'],
                    'status': row['status'],
                    'started_at': datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                    'ended_at': datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
                    'max_duration_hours': row['max_duration_hours'] if row['max_duration_hours'] else None
                }
                sessions[row['id']] = session_data
        
        return sessions
    
    def _load_resource_locks(self, project_id: str) -> Dict[str, str]:
        """Load resource locks for a project"""
        locks = {}
        
        with self._get_connection() as conn:
            lock_rows = conn.execute(
                'SELECT * FROM project_resource_locks WHERE project_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)',
                (project_id,)
            ).fetchall()
            
            for row in lock_rows:
                locks[row['resource_name']] = row['locked_by_agent_id']
        
        return locks
    
    def _save_task_trees(self, project: Project):
        """Save task trees for a project"""
        with self._get_connection() as conn:
            # Clear existing task trees
            conn.execute('DELETE FROM project_task_trees WHERE project_id = ?', 
                        (project.id,))
            
            # Save task trees
            for tree_id, tree in project.task_trees.items():
                conn.execute('''
                    INSERT INTO project_task_trees 
                    (id, project_id, name, description, created_at, updated_at, 
                     assigned_agent_id, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tree.id,
                    project.id,
                    tree.name,
                    tree.description,
                    tree.created_at.isoformat(),
                    tree.updated_at.isoformat(),
                    tree.assigned_agent_id,
                    tree.priority.value if hasattr(tree.priority, 'value') else str(tree.priority),
                    tree.status.value if hasattr(tree.status, 'value') else str(tree.status),
                    ))
            
            conn.commit()
    
    def _save_agents(self, project: Project):
        """Save agents for a project"""
        with self._get_connection() as conn:
            # Clear existing agents
            conn.execute('DELETE FROM project_agents WHERE project_id = ?', 
                        (project.id,))
            
            # Save agents
            for agent_id, agent in project.registered_agents.items():
                capabilities_json = json.dumps([cap.value for cap in agent.capabilities])
                specializations_json = json.dumps(agent.specializations)
                languages_json = json.dumps(agent.preferred_languages)
                frameworks_json = json.dumps(agent.preferred_frameworks)
                work_hours_json = json.dumps(agent.work_hours) if agent.work_hours else '{}'
                
                conn.execute('''
                    INSERT INTO project_agents 
                    (id, project_id, name, description, call_agent, capabilities, specializations,
                     preferred_languages, preferred_frameworks, status, max_concurrent_tasks,
                     current_workload, completed_tasks, average_task_duration, success_rate,
                     work_hours, timezone, priority_preference, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent.id,
                    project.id,
                    agent.name,
                    agent.description,
                    getattr(agent, 'call_agent', None),
                    capabilities_json,
                    specializations_json,
                    languages_json,
                    frameworks_json,
                    agent.status.value,
                    agent.max_concurrent_tasks,
                    agent.current_workload,
                    agent.completed_tasks,
                    agent.average_task_duration,
                    agent.success_rate,
                    work_hours_json,
                    agent.timezone,
                    agent.priority_preference,
                    agent.created_at.isoformat(),
                    agent.updated_at.isoformat(),
                    ))
            
            conn.commit()
    
    def _save_agent_assignments(self, project: Project):
        """Save agent assignments for a project"""
        with self._get_connection() as conn:
            # Clear existing assignments
            conn.execute('DELETE FROM project_agent_assignments WHERE project_id = ?', 
                        (project.id,))
            
            # Save assignments
            for git_branch_id, agent_id in project.agent_assignments.items():
                conn.execute('''
                    INSERT INTO project_agent_assignments 
                    (project_id, agent_id, git_branch_id)
                    VALUES (?, ?, ?)
                ''', (project.id, agent_id, git_branch_id))
            
            conn.commit()
    
    def _save_cross_tree_dependencies(self, project: Project):
        """Save cross-tree dependencies for a project"""
        with self._get_connection() as conn:
            # Clear existing dependencies
            conn.execute('DELETE FROM project_cross_tree_dependencies WHERE project_id = ?', 
                        (project.id,))
            
            # Save dependencies
            for dependent_task_id, prerequisite_set in project.cross_tree_dependencies.items():
                for prerequisite_task_id in prerequisite_set:
                    conn.execute('''
                        INSERT INTO project_cross_tree_dependencies 
                        (project_id, dependent_task_id, prerequisite_task_id)
                        VALUES (?, ?, ?)
                    ''', (project.id, dependent_task_id, prerequisite_task_id))
            
            conn.commit()
    
    def _save_work_sessions(self, project: Project):
        """Save work sessions for a project"""
        with self._get_connection() as conn:
            # Clear existing sessions
            conn.execute('DELETE FROM project_work_sessions WHERE project_id = ?', 
                        (project.id,))
            
            # Save active sessions
            for session_id, session_data in project.active_work_sessions.items():
                conn.execute('''
                    INSERT INTO project_work_sessions 
                    (id, project_id, agent_id, task_id, git_branch_id, status, 
                     started_at, ended_at, max_duration_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    project.id,
                    session_data.get('agent_id'),
                    session_data.get('task_id'),
                    session_data.get('git_branch_id'),
                    session_data.get('status', 'active'),
                    session_data.get('started_at').isoformat() if session_data.get('started_at') else None,
                    session_data.get('ended_at').isoformat() if session_data.get('ended_at') else None,
                    session_data.get('max_duration_hours'),
                    ))
            
            conn.commit()
    
    def _save_resource_locks(self, project: Project):
        """Save resource locks for a project"""
        with self._get_connection() as conn:
            # Clear existing locks
            conn.execute('DELETE FROM project_resource_locks WHERE project_id = ?', 
                        (project.id,))
            
            # Save locks
            for resource_name, agent_id in project.resource_locks.items():
                conn.execute('''
                    INSERT INTO project_resource_locks 
                    (project_id, resource_name, locked_by_agent_id)
                    VALUES (?, ?, ?)
                ''', (project.id, resource_name, agent_id))
            
            conn.commit()
    
    # Repository interface implementation
    
    async def save(self, project: Project) -> None:
        """Save a project to the repository"""
        # Ensure core tables exist (safety for test databases that might have
        # been cleared after repository construction).

        with self._get_connection() as conn:
            # Save main project record
            project_dict = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
                'user_id': self.user_id,
                'status': 'active',
                'metadata': json.dumps({})
            }
            
            # Check if project exists
            existing = conn.execute('SELECT id FROM projects WHERE id = ? AND user_id = ?', 
                                  (project.id, self.user_id)).fetchone()
            
            if existing:
                # Update existing project
                conn.execute('''
                    UPDATE projects SET 
                        name = ?, description = ?, updated_at = ?, status = ?, metadata = ?
                    WHERE id = ? AND user_id = ?
                ''', (
                    project_dict['name'], project_dict['description'], 
                    project_dict['updated_at'], project_dict['status'], 
                    project_dict['metadata'], project_dict['id'], self.user_id))
            else:
                # Insert new project
                conn.execute('''
                    INSERT INTO projects (id, name, description, created_at, updated_at, user_id, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_dict['id'], project_dict['name'], project_dict['description'],
                    project_dict['created_at'], project_dict['updated_at'], 
                    project_dict['user_id'], project_dict['status'], project_dict['metadata']
                ))
            
            conn.commit()
        
        # Save related entities
        self._save_task_trees(project)
        self._save_agents(project)
        self._save_agent_assignments(project)
        self._save_cross_tree_dependencies(project)
        self._save_work_sessions(project)
        self._save_resource_locks(project)

    async def create_new(self, project: Project) -> None:
        """Create a new project, ensuring it doesn't already exist"""
        with self._get_connection() as conn:
            # Check if project already exists
            existing = conn.execute(
                'SELECT id FROM projects WHERE id = ? AND user_id = ?',
                (project.id, self.user_id)
            ).fetchone()
            
            if existing:
                raise ValueError(f"Project with ID '{project.id}' already exists for user '{self.user_id}'")
            
            # Create the project using save method
            await self.save(project)
    
    async def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find a project by its ID"""
        with self._get_connection() as conn:
            project_row = conn.execute(
                'SELECT * FROM projects WHERE id = ? AND user_id = ?',
                (project_id, self.user_id)
            ).fetchone()
            
            if not project_row:
                return None
            
            return self._project_row_to_domain(project_row)
    
    async def find_all(self) -> List[Project]:
        """Find all projects"""
        with self._get_connection() as conn:
            project_rows = conn.execute(
                'SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC',
                (self.user_id,)
            ).fetchall()
            
            projects = []
            for project_row in project_rows:
                try:
                    project = self._project_row_to_domain(project_row)
                    projects.append(project)
                except Exception as e:
                    logger.error(f"Error loading project {project_row['id']}: {e}")
                    continue
            
            return projects
    
    async def delete(self, project_id: str) -> bool:
        """Delete a project by its ID"""
        with self._get_connection() as conn:
            # Check if project exists
            existing = conn.execute(
                'SELECT id FROM projects WHERE id = ? AND user_id = ?',
                (project_id, self.user_id)
            ).fetchone()
            
            if not existing:
                return False
            
            # Delete project (cascading will handle related records)
            conn.execute('DELETE FROM projects WHERE id = ? AND user_id = ?', 
                        (project_id, self.user_id))
            conn.commit()
            
            return True
    
    async def exists(self, project_id: str) -> bool:
        """Check if a project exists"""
        with self._get_connection() as conn:
            result = conn.execute(
                'SELECT 1 FROM projects WHERE id = ? AND user_id = ?',
                (project_id, self.user_id)
            ).fetchone()
            return result is not None
    
    async def update(self, project: Project) -> None:
        """Update an existing project"""
        # Update timestamp
        project.updated_at = datetime.now(timezone.utc)
        await self.save(project)
    
    async def find_by_name(self, name: str) -> Optional[Project]:
        """Find a project by its name"""
        with self._get_connection() as conn:
            project_row = conn.execute(
                'SELECT * FROM projects WHERE name = ? AND user_id = ?',
                (name, self.user_id)
            ).fetchone()
            
            if not project_row:
                return None
            
            return self._project_row_to_domain(project_row)
    
    async def count(self) -> int:
        """Count total number of projects"""
        with self._get_connection() as conn:
            result = conn.execute(
                'SELECT COUNT(*) as count FROM projects WHERE user_id = ?',
                (self.user_id,)
            ).fetchone()
            return result['count'] if result else 0
    
    async def find_projects_with_agent(self, agent_id: str) -> List[Project]:
        """Find projects that have a specific agent registered"""
        with self._get_connection() as conn:
            project_rows = conn.execute('''
                SELECT DISTINCT p.* FROM projects p
                JOIN project_agents pa ON p.id = pa.project_id
                WHERE pa.id = ?
                ORDER BY p.created_at DESC
            ''', (agent_id,)).fetchall()
            
            projects = []
            for project_row in project_rows:
                try:
                    project = self._project_row_to_domain(project_row)
                    projects.append(project)
                except Exception as e:
                    logger.error(f"Error loading project {project_row['id']}: {e}")
                    continue
            
            return projects
    
    async def find_projects_by_status(self, status: str) -> List[Project]:
        """Find projects by their status"""
        with self._get_connection() as conn:
            project_rows = conn.execute(
                'SELECT * FROM projects WHERE status = ? AND user_id = ? ORDER BY created_at DESC',
                (status, self.user_id)
            ).fetchall()
            
            projects = []
            for project_row in project_rows:
                try:
                    project = self._project_row_to_domain(project_row)
                    projects.append(project)
                except Exception as e:
                    logger.error(f"Error loading project {project_row['id']}: {e}")
                    continue
            
            return projects
    
    async def get_project_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all projects"""
        with self._get_connection() as conn:
            # Get basic project stats
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_projects,
                    SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) as inactive_projects,
                    SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) as archived_projects
                FROM projects
            ''').fetchone()
            
            # Get agent stats
            agent_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_agents,
                    COUNT(DISTINCT project_id) as projects_with_agents,
                    AVG(success_rate) as avg_success_rate,
                    SUM(completed_tasks) as total_completed_tasks
                FROM project_agents
            ''').fetchone()
            
            # Get task tree stats
            tree_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_trees,
                    COUNT(DISTINCT project_id) as projects_with_trees,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed_trees,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active_trees
                FROM project_task_trees
            ''').fetchone()
            
            # Get work session stats
            session_stats = conn.execute('''
                SELECT 
                    COUNT(*) as active_sessions,
                    COUNT(DISTINCT agent_id) as agents_working
                FROM project_work_sessions
                WHERE status = 'active'
            ''').fetchone()
            
            return {
                "summary": {
                    "total_projects": stats['total_projects'],
                    "active_projects": stats['active_projects'],
                    "inactive_projects": stats['inactive_projects'],
                    "archived_projects": stats['archived_projects']
                },
                "agents": {
                    "total_agents": agent_stats['total_agents'],
                    "projects_with_agents": agent_stats['projects_with_agents'],
                    "average_success_rate": round(agent_stats['avg_success_rate'] or 0, 2),
                    "total_completed_tasks": agent_stats['total_completed_tasks'] or 0
                },
                "task_trees": {
                    "total_trees": tree_stats['total_trees'],
                    "projects_with_trees": tree_stats['projects_with_trees'],
                    "completed_trees": tree_stats['completed_trees'],
                    "active_trees": tree_stats['active_trees']
                },
                "activity": {
                    "active_work_sessions": session_stats['active_sessions'],
                    "agents_currently_working": session_stats['agents_working']
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def unassign_agent_from_tree(self, project_id: str, agent_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Unassign an agent from a specific task tree within a project."""
        try:
            with self._get_connection() as conn:
                # Check if the assignment exists
                existing = conn.execute('''
                    SELECT 1 FROM project_agent_assignments 
                    WHERE project_id = ? AND agent_id = ? AND git_branch_id = ?
                ''', (project_id, agent_id, git_branch_id)).fetchone()
                
                if not existing:
                    return {
                        "success": False,
                        "message": f"Agent {agent_id} is not assigned to tree {git_branch_id} in project {project_id}"
                    }
                
                # Remove the assignment
                conn.execute('''
                    DELETE FROM project_agent_assignments 
                    WHERE project_id = ? AND agent_id = ? AND git_branch_id = ?
                ''', (project_id, agent_id, git_branch_id))
                
                # Update task tree to remove assigned agent
                conn.execute('''
                    UPDATE project_task_trees 
                    SET assigned_agent_id = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = ? AND id = ?
                ''', (project_id, git_branch_id))
                
                conn.commit()
                
                logger.info(f"Successfully unassigned agent {agent_id} from tree {git_branch_id} in project {project_id}")
                
                return {
                    "success": True,
                    "message": f"Agent {agent_id} unassigned from tree {git_branch_id} in project {project_id}",
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "git_branch_id": git_branch_id,
                    "unassigned_at": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error unassigning agent {agent_id} from tree {git_branch_name} in project {project_id}: {e}")
            return {
                "success": False,
                "message": f"Error unassigning agent: {str(e)}"
            }
    
    # Additional utility methods
    
    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific project"""
        with self._get_connection() as conn:
            # Get project info
            project_info = conn.execute(
                'SELECT * FROM projects WHERE id = ? AND user_id = ?',
                (project_id, self.user_id)
            ).fetchone()
            
            if not project_info:
                return {"error": "Project not found"}
            
            # Get task tree stats
            tree_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_trees,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed_trees,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active_trees,
                    SUM(CASE WHEN assigned_agent_id IS NOT NULL THEN 1 ELSE 0 END) as assigned_trees
                FROM project_task_trees 
                WHERE project_id = ?
            ''', (project_id,)).fetchone()
            
            # Get agent stats
            agent_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_agents,
                    AVG(success_rate) as avg_success_rate,
                    SUM(completed_tasks) as total_completed_tasks,
                    SUM(current_workload) as total_workload
                FROM project_agents 
                WHERE project_id = ?
            ''', (project_id,)).fetchone()
            
            # Get active sessions
            active_sessions = conn.execute('''
                SELECT COUNT(*) as count
                FROM project_work_sessions 
                WHERE project_id = ? AND status = 'active'
            ''', (project_id,)).fetchone()
            
            return {
                "project": {
                    "id": project_info['id'],
                    "name": project_info['name'],
                    "status": project_info['status'],
                    "created_at": project_info['created_at'],
                    "updated_at": project_info['updated_at']
                },
                "task_trees": {
                    "total": tree_stats['total_trees'],
                    "completed": tree_stats['completed_trees'],
                    "active": tree_stats['active_trees'],
                    "assigned": tree_stats['assigned_trees']
                },
                "agents": {
                    "total": agent_stats['total_agents'],
                    "average_success_rate": round(agent_stats['avg_success_rate'] or 0, 2),
                    "total_completed_tasks": agent_stats['total_completed_tasks'] or 0,
                    "total_workload": agent_stats['total_workload'] or 0
                },
                "activity": {
                    "active_work_sessions": active_sessions['count']
                }
            } 