"""
Project Repository Implementation using SQLAlchemy ORM

This module provides project repository implementation using SQLAlchemy ORM,
supporting both SQLite and PostgreSQL databases.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import joinedload

from ..base_orm_repository import BaseORMRepository
from ...database.models import Project, ProjectTaskTree
from ....domain.repositories.project_repository import ProjectRepository
from ....domain.entities.project import Project as ProjectEntity
from ....domain.exceptions.base_exceptions import (
    ResourceNotFoundException,
    ValidationException,
    DatabaseException
)

logger = logging.getLogger(__name__)


class ORMProjectRepository(BaseORMRepository[Project], ProjectRepository):
    """
    Project repository implementation using SQLAlchemy ORM.
    
    This repository handles all project-related database operations
    using SQLAlchemy, supporting both SQLite and PostgreSQL.
    """
    
    def __init__(self):
        """Initialize ORM project repository."""
        super().__init__(Project)
    
    def _model_to_entity(self, project: Project) -> ProjectEntity:
        """Convert SQLAlchemy model to domain entity"""
        return ProjectEntity(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
    
    async def save(self, project: ProjectEntity) -> None:
        """Save a project to the repository"""
        try:
            with self.transaction():
                existing = self.get_by_id(project.id)
                
                if existing:
                    # Update existing project
                    self.update(
                        project.id,
                        name=project.name,
                        description=project.description,
                        updated_at=datetime.now(),
                        status=getattr(project, 'status', 'active'),
                        metadata=getattr(project, 'metadata', {})
                    )
                else:
                    # Create new project
                    self.create(
                        id=project.id,
                        name=project.name,
                        description=project.description,
                        created_at=project.created_at,
                        updated_at=project.updated_at,
                        user_id="default_id",  # Default user ID
                        status="active",
                        metadata={}
                    )
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise DatabaseException(
                message=f"Failed to save project: {str(e)}",
                operation="save",
                table="projects"
            )
    
    async def find_by_id(self, project_id: str) -> Optional[ProjectEntity]:
        """Find a project by its ID"""
        with self.get_db_session() as session:
            project = session.query(Project).options(
                joinedload(Project.git_branches)
            ).filter(Project.id == project_id).first()
            
            return self._model_to_entity(project) if project else None
    
    async def find_all(self) -> List[ProjectEntity]:
        """Find all projects"""
        with self.get_db_session() as session:
            projects = session.query(Project).options(
                joinedload(Project.git_branches)
            ).order_by(desc(Project.created_at)).all()
            
            return [self._model_to_entity(project) for project in projects]
    
    async def delete(self, project_id: str) -> bool:
        """Delete a project by its ID"""
        try:
            return super().delete(project_id)
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False
    
    async def exists(self, project_id: str) -> bool:
        """Check if a project exists"""
        return self.exists(id=project_id)
    
    async def update(self, project: ProjectEntity) -> None:
        """Update an existing project"""
        try:
            with self.transaction():
                updated = super().update(
                    project.id,
                    name=project.name,
                    description=project.description,
                    updated_at=datetime.now()
                )
                
                if not updated:
                    raise ResourceNotFoundException(
                        resource_type="Project",
                        resource_id=project.id
                    )
        except Exception as e:
            logger.error(f"Failed to update project {project.id}: {e}")
            raise DatabaseException(
                message=f"Failed to update project: {str(e)}",
                operation="update",
                table="projects"
            )
    
    async def find_by_name(self, name: str) -> Optional[ProjectEntity]:
        """Find a project by its name"""
        with self.get_db_session() as session:
            project = session.query(Project).filter(
                Project.name == name
            ).first()
            
            return self._model_to_entity(project) if project else None
    
    async def count(self) -> int:
        """Count total number of projects"""
        return super().count()
    
    async def find_projects_with_agent(self, agent_id: str) -> List[ProjectEntity]:
        """Find projects that have a specific agent registered"""
        with self.get_db_session() as session:
            # Find projects with git branches assigned to the agent
            projects = session.query(Project).join(ProjectTaskTree).filter(
                ProjectTaskTree.assigned_agent_id == agent_id
            ).distinct().all()
            
            return [self._model_to_entity(project) for project in projects]
    
    async def find_projects_by_status(self, status: str) -> List[ProjectEntity]:
        """Find projects by their status"""
        with self.get_db_session() as session:
            projects = session.query(Project).filter(
                Project.status == status
            ).order_by(desc(Project.created_at)).all()
            
            return [self._model_to_entity(project) for project in projects]
    
    async def get_project_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all projects"""
        with self.get_db_session() as session:
            # Get total projects
            total_projects = session.query(Project).count()
            
            # Get projects by status
            status_counts = {}
            statuses = session.query(Project.status).distinct().all()
            for (status,) in statuses:
                count = session.query(Project).filter(
                    Project.status == status
                ).count()
                status_counts[status] = count
            
            # Get projects with branches
            projects_with_branches = session.query(Project).join(
                ProjectTaskTree
            ).distinct().count()
            
            # Get total branches
            total_branches = session.query(ProjectTaskTree).count()
            
            # Get branches with assigned agents
            assigned_branches = session.query(ProjectTaskTree).filter(
                ProjectTaskTree.assigned_agent_id.isnot(None)
            ).count()
            
            return {
                "total_projects": total_projects,
                "projects_by_status": status_counts,
                "projects_with_branches": projects_with_branches,
                "total_branches": total_branches,
                "assigned_branches": assigned_branches,
                "unassigned_branches": total_branches - assigned_branches,
                "average_branches_per_project": (
                    total_branches / total_projects if total_projects > 0 else 0
                )
            }
    
    async def unassign_agent_from_tree(self, project_id: str, agent_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Unassign an agent from a specific task tree within a project."""
        try:
            with self.transaction():
                with self.get_db_session() as session:
                    # Find the git branch
                    branch = session.query(ProjectTaskTree).filter(
                        and_(
                            ProjectTaskTree.id == git_branch_id,
                            ProjectTaskTree.project_id == project_id,
                            ProjectTaskTree.assigned_agent_id == agent_id
                        )
                    ).first()
                    
                    if not branch:
                        raise ResourceNotFoundException(
                            resource_type="Git Branch",
                            resource_id=git_branch_id
                        )
                    
                    # Unassign the agent
                    branch.assigned_agent_id = None
                    branch.updated_at = datetime.now()
                    
                    return {
                        "success": True,
                        "project_id": project_id,
                        "git_branch_id": git_branch_id,
                        "unassigned_agent_id": agent_id
                    }
        except Exception as e:
            logger.error(f"Failed to unassign agent {agent_id} from tree {git_branch_id}: {e}")
            raise DatabaseException(
                message=f"Failed to unassign agent: {str(e)}",
                operation="unassign_agent_from_tree",
                table="project_task_trees"
            )
    
    # Additional ORM-specific methods
    def create_project(self, name: str, description: str = "", user_id: str = "default_id") -> ProjectEntity:
        """Create a new project with ORM"""
        try:
            with self.transaction():
                import uuid
                project_id = str(uuid.uuid4())
                
                project = self.create(
                    id=project_id,
                    name=name,
                    description=description,
                    user_id=user_id,
                    status="active",
                    metadata={}
                )
                
                return self._model_to_entity(project)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise DatabaseException(
                message=f"Failed to create project: {str(e)}",
                operation="create_project",
                table="projects"
            )
    
    def get_project(self, project_id: str) -> Optional[ProjectEntity]:
        """Synchronous version of find_by_id for compatibility"""
        with self.get_db_session() as session:
            project = session.query(Project).options(
                joinedload(Project.git_branches)
            ).filter(Project.id == project_id).first()
            
            return self._model_to_entity(project) if project else None
    
    def update_project(self, project_id: str, **updates) -> ProjectEntity:
        """Update a project with ORM"""
        try:
            with self.transaction():
                # Update timestamp
                updates['updated_at'] = datetime.now()
                
                updated_project = super().update(project_id, **updates)
                if not updated_project:
                    raise ResourceNotFoundException(
                        resource_type="Project",
                        resource_id=project_id
                    )
                
                return self._model_to_entity(updated_project)
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            raise DatabaseException(
                message=f"Failed to update project: {str(e)}",
                operation="update_project",
                table="projects"
            )
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project with ORM"""
        return super().delete(project_id)
    
    def list_projects(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[ProjectEntity]:
        """List projects with filters"""
        with self.get_db_session() as session:
            query = session.query(Project).options(
                joinedload(Project.git_branches)
            )
            
            if status:
                query = query.filter(Project.status == status)
            
            query = query.order_by(desc(Project.created_at))
            query = query.offset(offset).limit(limit)
            
            projects = query.all()
            return [self._model_to_entity(project) for project in projects]
    
    def get_project_by_name(self, name: str) -> Optional[ProjectEntity]:
        """Get a project by name"""
        with self.get_db_session() as session:
            project = session.query(Project).filter(
                Project.name == name
            ).first()
            
            return self._model_to_entity(project) if project else None
    
    def search_projects(self, query: str, limit: int = 50) -> List[ProjectEntity]:
        """Search projects by name or description"""
        with self.get_db_session() as session:
            search_pattern = f"%{query}%"
            
            projects = session.query(Project).filter(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern)
                )
            ).order_by(desc(Project.created_at)).limit(limit).all()
            
            return [self._model_to_entity(project) for project in projects]
    
    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for a specific project"""
        with self.get_db_session() as session:
            project = session.query(Project).options(
                joinedload(Project.git_branches)
            ).filter(Project.id == project_id).first()
            
            if not project:
                raise ResourceNotFoundException(
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Calculate statistics
            total_branches = len(project.git_branches)
            assigned_branches = sum(
                1 for branch in project.git_branches 
                if branch.assigned_agent_id is not None
            )
            
            total_tasks = sum(branch.task_count for branch in project.git_branches)
            completed_tasks = sum(branch.completed_task_count for branch in project.git_branches)
            
            return {
                "project_id": project_id,
                "project_name": project.name,
                "status": project.status,
                "total_branches": total_branches,
                "assigned_branches": assigned_branches,
                "unassigned_branches": total_branches - assigned_branches,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": (
                    (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                ),
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }