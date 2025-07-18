"""
Task Repository Implementation using SQLAlchemy ORM

This module provides task repository implementation using SQLAlchemy ORM,
supporting both SQLite and PostgreSQL databases.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import joinedload

from ..base_orm_repository import BaseORMRepository
from ...database.models import Task, TaskSubtask, TaskAssignee, TaskLabel
from ....domain.repositories.task_repository import TaskRepository
from ....domain.entities.task import Task as TaskEntity
from ....domain.value_objects.task_id import TaskId
from ....domain.value_objects.task_status import TaskStatus
from ....domain.value_objects.priority import Priority
from ....domain.exceptions.task_exceptions import (
    TaskNotFoundError,
    TaskCreationError,
    TaskUpdateError,
    DuplicateTaskError
)

logger = logging.getLogger(__name__)


class ORMTaskRepository(BaseORMRepository[Task], TaskRepository):
    """
    Task repository implementation using SQLAlchemy ORM.
    
    This repository handles all task-related database operations
    using SQLAlchemy, supporting both SQLite and PostgreSQL.
    """
    
    def __init__(self, git_branch_id: Optional[str] = None, project_id: Optional[str] = None,
                 git_branch_name: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize ORM task repository.
        
        Args:
            git_branch_id: Git branch ID for filtering tasks
            project_id: Project ID for context
            git_branch_name: Git branch name for context
            user_id: User ID for context
        """
        super().__init__(Task)
        self.git_branch_id = git_branch_id
        self.project_id = project_id
        self.git_branch_name = git_branch_name
        self.user_id = user_id
    
    def _model_to_entity(self, task: Task) -> TaskEntity:
        """Convert SQLAlchemy model to domain entity"""
        # Get assignee IDs
        assignee_ids = [a.assignee_id for a in task.assignees]
        
        # Get label names
        label_names = [tl.label.name for tl in task.labels]
        
        # Convert subtasks to IDs only (as per Task entity definition)
        subtask_ids = []
        for subtask in task.subtasks:
            subtask_ids.append(subtask.id)  # Only store subtask IDs, not full objects
        
        # Convert status and priority to proper value objects
        
        status_obj = TaskStatus(task.status) if task.status else None
        priority_obj = Priority(task.priority) if task.priority else None
        task_id_obj = TaskId(task.id) if task.id else None
        
        return TaskEntity(
            id=task_id_obj,
            title=task.title,
            description=task.description,
            git_branch_id=task.git_branch_id,
            status=status_obj,
            priority=priority_obj,
            assignees=assignee_ids,
            labels=label_names,
            details=task.details,
            estimated_effort=task.estimated_effort,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
            context_id=task.context_id,
            subtasks=subtask_ids
        )
    
    def create_task(self, title: str, description: str, priority: str = "medium",
                   assignee_ids: Optional[List[str]] = None, label_names: Optional[List[str]] = None,
                   **kwargs) -> TaskEntity:
        """Create a new task"""
        try:
            with self.transaction():
                # Generate task ID if not provided
                task_id = kwargs.get('id')
                if not task_id:
                    import uuid
                    task_id = str(uuid.uuid4())
                
                # Create task
                task = self.create(
                    id=task_id,
                    title=title,
                    description=description,
                    git_branch_id=self.git_branch_id,
                    priority=priority,
                    status=kwargs.get('status', 'todo'),
                    details=kwargs.get('details', ''),
                    estimated_effort=kwargs.get('estimated_effort', ''),
                    due_date=kwargs.get('due_date'),
                    context_id=kwargs.get('context_id')
                )
                
                # Add assignees
                if assignee_ids:
                    with self.get_db_session() as session:
                        for assignee_id in assignee_ids:
                            assignee = TaskAssignee(
                                task_id=task.id,
                                assignee_id=assignee_id,
                                role=kwargs.get('assignee_role', 'contributor')
                            )
                            session.add(assignee)
                
                # Note: Label handling would require label creation/lookup
                # which is not implemented in this example
                
                # Reload with relationships
                with self.get_db_session() as session:
                    task = session.query(Task).options(
                        joinedload(Task.assignees),
                        joinedload(Task.labels),
                        joinedload(Task.subtasks)
                    ).filter(Task.id == task.id).first()
                
                return self._model_to_entity(task)
                
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise TaskCreationError(f"Failed to create task: {str(e)}")
    
    def get_task(self, task_id: str) -> Optional[TaskEntity]:
        """Get a task by ID"""
        with self.get_db_session() as session:
            task = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            ).filter(
                and_(
                    Task.id == task_id,
                    Task.git_branch_id == self.git_branch_id if self.git_branch_id else True
                )
            ).first()
            
            return self._model_to_entity(task) if task else None
    
    def update_task(self, task_id: str, **updates) -> TaskEntity:
        """Update a task"""
        try:
            with self.transaction():
                # Update basic fields
                basic_updates = {k: v for k, v in updates.items() 
                               if k not in ['assignee_ids', 'label_names', 'subtasks']}
                
                updated_task = self.update(task_id, **basic_updates)
                if not updated_task:
                    raise TaskNotFoundError(f"Task {task_id} not found")
                
                # Update assignees if provided
                if 'assignee_ids' in updates:
                    with self.get_db_session() as session:
                        # Remove existing assignees
                        session.query(TaskAssignee).filter(
                            TaskAssignee.task_id == task_id
                        ).delete()
                        
                        # Add new assignees
                        for assignee_id in updates['assignee_ids']:
                            assignee = TaskAssignee(
                                task_id=task_id,
                                assignee_id=assignee_id
                            )
                            session.add(assignee)
                
                # Reload with relationships
                with self.get_db_session() as session:
                    task = session.query(Task).options(
                        joinedload(Task.assignees),
                        joinedload(Task.labels).joinedload(TaskLabel.label),
                        joinedload(Task.subtasks)
                    ).filter(Task.id == task_id).first()
                
                return self._model_to_entity(task)
                
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise TaskUpdateError(f"Failed to update task: {str(e)}")
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        return super().delete(task_id)
    
    def list_tasks(self, status: Optional[str] = None, priority: Optional[str] = None,
                  assignee_id: Optional[str] = None, limit: int = 100,
                  offset: int = 0) -> List[TaskEntity]:
        """List tasks with filters"""
        with self.get_db_session() as session:
            query = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            )
            
            # Apply filters
            filters = []
            if self.git_branch_id:
                filters.append(Task.git_branch_id == self.git_branch_id)
            if status:
                filters.append(Task.status == status)
            if priority:
                filters.append(Task.priority == priority)
            
            if filters:
                query = query.filter(and_(*filters))
            
            # Filter by assignee if specified
            if assignee_id:
                query = query.join(TaskAssignee).filter(
                    TaskAssignee.assignee_id == assignee_id
                )
            
            # Apply ordering and pagination
            query = query.order_by(desc(Task.created_at))
            query = query.offset(offset).limit(limit)
            
            tasks = query.all()
            return [self._model_to_entity(task) for task in tasks]
    
    def get_task_count(self, status: Optional[str] = None) -> int:
        """Get count of tasks"""
        filters = {}
        if self.git_branch_id:
            filters['git_branch_id'] = self.git_branch_id
        if status:
            filters['status'] = status
        
        return self.count(**filters)
    
    def search_tasks(self, query: str, limit: int = 50) -> List[TaskEntity]:
        """Search tasks by title or description"""
        with self.get_db_session() as session:
            search_pattern = f"%{query}%"
            
            tasks = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            ).filter(
                and_(
                    Task.git_branch_id == self.git_branch_id if self.git_branch_id else True,
                    or_(
                        Task.title.ilike(search_pattern),
                        Task.description.ilike(search_pattern)
                    )
                )
            ).order_by(desc(Task.created_at)).limit(limit).all()
            
            return [self._model_to_entity(task) for task in tasks]
    
    def get_tasks_by_assignee(self, assignee_id: str) -> List[TaskEntity]:
        """Get all tasks assigned to a specific user"""
        return self.list_tasks(assignee_id=assignee_id)
    
    def get_overdue_tasks(self) -> List[TaskEntity]:
        """Get tasks that are overdue"""
        with self.get_db_session() as session:
            now = datetime.now().isoformat()
            
            tasks = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            ).filter(
                and_(
                    Task.git_branch_id == self.git_branch_id if self.git_branch_id else True,
                    Task.due_date < now,
                    Task.status != 'completed'
                )
            ).all()
            
            return [self._model_to_entity(task) for task in tasks]
    
    def batch_update_status(self, task_ids: List[str], status: str) -> int:
        """Update status for multiple tasks"""
        with self.get_db_session() as session:
            updated = session.query(Task).filter(
                and_(
                    Task.id.in_(task_ids),
                    Task.git_branch_id == self.git_branch_id if self.git_branch_id else True
                )
            ).update(
                {'status': status, 'updated_at': datetime.now()},
                synchronize_session=False
            )
            
            return updated
    
    # Abstract method implementations for TaskRepository interface
    
    def save(self, task: TaskEntity) -> bool:
        """Save a task entity"""
        try:
            with self.get_db_session() as session:
                # Check if task already exists
                existing = session.query(Task).filter(Task.id == str(task.id)).first()
                
                if existing:
                    # Update existing task
                    existing.title = task.title
                    existing.description = task.description
                    existing.git_branch_id = task.git_branch_id
                    existing.status = str(task.status)
                    existing.priority = str(task.priority)
                    existing.details = task.details
                    existing.estimated_effort = task.estimated_effort
                    existing.due_date = task.due_date
                    existing.updated_at = task.updated_at
                    existing.context_id = task.context_id
                else:
                    # Create new task
                    new_task = Task(
                        id=str(task.id),
                        title=task.title,
                        description=task.description,
                        git_branch_id=task.git_branch_id,
                        status=str(task.status),
                        priority=str(task.priority),
                        details=task.details,
                        estimated_effort=task.estimated_effort,
                        due_date=task.due_date,
                        created_at=task.created_at,
                        updated_at=task.updated_at,
                        context_id=task.context_id
                    )
                    session.add(new_task)
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            return False
    
    def find_by_id(self, task_id) -> Optional[TaskEntity]:
        """Find task by ID"""
        return self.get_task(str(task_id))
    
    def find_all(self) -> List[TaskEntity]:
        """Find all tasks"""
        return self.list_tasks()
    
    def find_by_status(self, status) -> List[TaskEntity]:
        """Find tasks by status"""
        return self.list_tasks(status=str(status))
    
    def find_by_priority(self, priority) -> List[TaskEntity]:
        """Find tasks by priority"""
        return self.list_tasks(priority=str(priority))
    
    def find_by_assignee(self, assignee: str) -> List[TaskEntity]:
        """Find tasks by assignee"""
        return self.get_tasks_by_assignee(assignee)
    
    def find_by_labels(self, labels: List[str]) -> List[TaskEntity]:
        """Find tasks containing any of the specified labels"""
        # This would need to be implemented based on your label system
        return []
    
    def search(self, query: str, limit: int = 10) -> List[TaskEntity]:
        """Search tasks by query string"""
        return self.search_tasks(query, limit)
    
    def delete(self, task_id) -> bool:
        """Delete a task"""
        return self.delete_task(str(task_id))
    
    def exists(self, task_id) -> bool:
        """Check if task exists"""
        return self.get_task(str(task_id)) is not None
    
    def get_next_id(self):
        """Get next available task ID"""
        # Generate a new UUID
        import uuid
        return str(uuid.uuid4())
    
    def count(self) -> int:
        """Get total number of tasks"""
        return self.get_task_count()
    
    def find_by_criteria(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[TaskEntity]:
        """Find tasks by multiple criteria"""
        with self.get_db_session() as session:
            query = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            )
            
            # Apply git branch filter if set
            if self.git_branch_id:
                query = query.filter(Task.git_branch_id == self.git_branch_id)
            
            # Apply filters
            if 'status' in filters:
                # Convert TaskStatus enum to string if needed
                status_value = filters['status']
                if hasattr(status_value, 'value'):
                    status_value = status_value.value
                query = query.filter(Task.status == status_value)
            
            if 'priority' in filters:
                # Convert Priority enum to string if needed
                priority_value = filters['priority']
                if hasattr(priority_value, 'value'):
                    priority_value = priority_value.value
                query = query.filter(Task.priority == priority_value)
            
            if 'assignees' in filters and filters['assignees']:
                # Filter tasks that have at least one of the specified assignees
                query = query.join(TaskAssignee).filter(
                    TaskAssignee.assignee_id.in_(filters['assignees'])
                )
            elif 'assignee' in filters and filters['assignee']:
                # Legacy single assignee filter
                query = query.join(TaskAssignee).filter(
                    TaskAssignee.assignee_id == filters['assignee']
                )
            
            if 'labels' in filters and filters['labels']:
                # Filter tasks that have at least one of the specified labels
                from ...database.models import Label
                query = query.join(TaskLabel).join(Label).filter(
                    Label.name.in_(filters['labels'])
                )
            
            # Order by updated_at desc
            query = query.order_by(desc(Task.updated_at))
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            tasks = query.all()
            return [self._model_to_entity(task) for task in tasks]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics"""
        return {
            "total_tasks": self.get_task_count(),
            "completed_tasks": self.get_task_count(status="completed"),
            "in_progress_tasks": self.get_task_count(status="in_progress"),
            "todo_tasks": self.get_task_count(status="todo")
        }
    
    def find_by_id_all_states(self, task_id) -> Optional[TaskEntity]:
        """Find task by ID across all states (active, completed, archived)"""
        with self.get_db_session() as session:
            # Search across all statuses without any git_branch_id filter
            # This ensures we find tasks regardless of their current state
            task = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            ).filter(Task.id == str(task_id)).first()
            
            return self._model_to_entity(task) if task else None
    
    def git_branch_exists(self, git_branch_id: str) -> bool:
        """Check if git_branch_id exists in the database"""
        from ...database.models import ProjectGitBranch
        
        with self.get_db_session() as session:
            branch = session.query(ProjectGitBranch).filter(
                ProjectGitBranch.id == git_branch_id
            ).first()
            return branch is not None