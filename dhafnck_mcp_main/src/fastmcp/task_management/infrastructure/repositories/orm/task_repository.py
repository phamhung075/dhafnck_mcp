"""
Task Repository Implementation using SQLAlchemy ORM

This module provides task repository implementation using SQLAlchemy ORM,
supporting both SQLite and PostgreSQL databases.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import joinedload

from ....domain.entities.task import Task as TaskEntity
from ....domain.exceptions.task_exceptions import (
    TaskCreationError,
    TaskNotFoundError,
    TaskUpdateError,
)
from ....domain.repositories.task_repository import TaskRepository
from ....domain.value_objects.priority import Priority
from ....domain.value_objects.task_id import TaskId
from ....domain.value_objects.task_status import TaskStatus
from ...database.models import Task, TaskAssignee, TaskDependency, TaskLabel
from ..base_orm_repository import BaseORMRepository

logger = logging.getLogger(__name__)


class ORMTaskRepository(BaseORMRepository[Task], TaskRepository):
    """
    Task repository implementation using SQLAlchemy ORM.
    
    This repository handles all task-related database operations
    using SQLAlchemy, supporting both SQLite and PostgreSQL.
    """
    
    def __init__(self, git_branch_id: str | None = None, project_id: str | None = None,
                 git_branch_name: str | None = None, user_id: str | None = None):
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
        
        # Convert dependencies to TaskId objects
        dependency_ids = []
        for dependency in task.dependencies:
            dependency_ids.append(TaskId(dependency.depends_on_task_id))
        
        # Convert status and priority to proper value objects
        
        status_obj = TaskStatus(task.status) if task.status else None
        priority_obj = Priority(task.priority) if task.priority else None
        task_id_obj = TaskId(task.id) if task.id else None
        
        # Create the entity
        entity = TaskEntity(
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
            subtasks=subtask_ids,
            dependencies=dependency_ids
        )
        
        # Set progress_percentage if available
        if hasattr(task, 'progress_percentage'):
            entity.progress_percentage = task.progress_percentage
        
        return entity
    
    def create_task(self, title: str, description: str, priority: str = "medium",
                   assignee_ids: list[str] | None = None, label_names: list[str] | None = None,
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
                
                # Handle labels if provided
                if label_names:
                    from ...database.models import Label
                    with self.get_db_session() as session:
                        for label_name in label_names:
                            # Get or create label
                            label = session.query(Label).filter(Label.name == label_name).first()
                            if not label:
                                # Create new label with a unique ID
                                import uuid
                                label = Label(
                                    id=str(uuid.uuid4()),
                                    name=label_name,
                                    color="#0066cc",
                                    description=""
                                )
                                session.add(label)
                                session.flush()  # Ensure label is saved before creating relationship
                            
                            # Create task-label relationship
                            task_label = TaskLabel(
                                task_id=task_id,
                                label_id=label.id
                            )
                            session.add(task_label)
                
                # Reload with relationships
                with self.get_db_session() as session:
                    task = session.query(Task).options(
                        joinedload(Task.assignees),
                        joinedload(Task.labels),
                        joinedload(Task.subtasks),
                        joinedload(Task.dependencies)
                    ).filter(Task.id == task.id).first()
                
                return self._model_to_entity(task)
                
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise TaskCreationError(f"Failed to create task: {str(e)}")
    
    def get_task(self, task_id: str) -> TaskEntity | None:
        """Get a task by ID"""
        with self.get_db_session() as session:
            task = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks),
                joinedload(Task.dependencies)
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
                
                # Update labels if provided
                if 'label_names' in updates or 'labels' in updates:
                    label_names = updates.get('label_names') or updates.get('labels', [])
                    from ...database.models import Label
                    with self.get_db_session() as session:
                        # Remove existing labels
                        session.query(TaskLabel).filter(
                            TaskLabel.task_id == task_id
                        ).delete()
                        
                        # Add new labels
                        for label_name in label_names:
                            # Get or create label
                            label = session.query(Label).filter(Label.name == label_name).first()
                            if not label:
                                # Create new label with a unique ID
                                import uuid
                                label = Label(
                                    id=str(uuid.uuid4()),
                                    name=label_name,
                                    color="#0066cc",
                                    description=""
                                )
                                session.add(label)
                                session.flush()  # Ensure label is saved before creating relationship
                            
                            # Create task-label relationship
                            task_label = TaskLabel(
                                task_id=task_id,
                                label_id=label.id
                            )
                            session.add(task_label)
                
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
    
    def list_tasks(self, status: str | None = None, priority: str | None = None,
                  assignee_id: str | None = None, limit: int = 100,
                  offset: int = 0) -> list[TaskEntity]:
        """List tasks with filters"""
        with self.get_db_session() as session:
            query = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks),
                joinedload(Task.dependencies)
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
    
    def get_task_count(self, status: str | None = None) -> int:
        """Get count of tasks"""
        filters = {}
        if self.git_branch_id:
            filters['git_branch_id'] = self.git_branch_id
        if status:
            filters['status'] = status
        
        return self.count(**filters)
    
    def search_tasks(self, query: str, limit: int = 50) -> list[TaskEntity]:
        """Search tasks by title, description, and labels with multi-word support"""
        with self.get_db_session() as session:
            # Import Label model for label search
            from ...database.models import Label
            
            # Split query into individual words for better matching
            search_words = [word.strip() for word in query.split() if word.strip()]
            if not search_words:
                return []
            
            # Build search filters for each word - a task matches if ANY word matches ANY field
            all_search_filters = []
            
            for word in search_words:
                word_pattern = f"%{word}%"
                word_filters = [
                    Task.title.ilike(word_pattern),
                    Task.description.ilike(word_pattern)
                ]
                
                # Add label search for this word
                label_subquery = session.query(TaskLabel.task_id).join(Label).filter(
                    Label.name.ilike(word_pattern)
                ).subquery()
                
                word_filters.append(Task.id.in_(label_subquery))
                
                # Each word creates an OR condition across all fields
                all_search_filters.append(or_(*word_filters))
            
            # Tasks match if ANY of the search words match (OR across words)
            # This means "authentication JWT" finds tasks with either "authentication" OR "JWT"
            filters = [or_(*all_search_filters)]
            
            # Only add git_branch_id filter if it exists
            if self.git_branch_id:
                filters.append(Task.git_branch_id == self.git_branch_id)
            
            tasks = session.query(Task).options(
                joinedload(Task.assignees),
                joinedload(Task.labels).joinedload(TaskLabel.label),
                joinedload(Task.subtasks)
            ).filter(
                and_(*filters)
            ).order_by(desc(Task.created_at)).limit(limit).all()
            
            return [self._model_to_entity(task) for task in tasks]
    
    def get_tasks_by_assignee(self, assignee_id: str) -> list[TaskEntity]:
        """Get all tasks assigned to a specific user"""
        return self.list_tasks(assignee_id=assignee_id)
    
    def get_overdue_tasks(self) -> list[TaskEntity]:
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
    
    def batch_update_status(self, task_ids: list[str], status: str) -> int:
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
                    
                    # Update dependencies
                    # First, remove all existing dependencies
                    session.query(TaskDependency).filter(TaskDependency.task_id == str(task.id)).delete()
                    
                    # Then add new dependencies
                    for dependency in task.dependencies:
                        new_dependency = TaskDependency(
                            task_id=str(task.id),
                            depends_on_task_id=str(dependency.value if hasattr(dependency, 'value') else dependency),
                            dependency_type="blocks"
                        )
                        session.add(new_dependency)
                    
                    # Update labels
                    # First, remove all existing labels
                    session.query(TaskLabel).filter(TaskLabel.task_id == str(task.id)).delete()
                    
                    # Then add new labels
                    from ...database.models import Label
                    for label_name in task.labels:
                        # Get or create label
                        label = session.query(Label).filter(Label.name == label_name).first()
                        if not label:
                            # Create new label with a unique ID
                            import uuid
                            label = Label(
                                id=str(uuid.uuid4()),
                                name=label_name,
                                color="#0066cc",
                                description=""
                            )
                            session.add(label)
                            session.flush()  # Ensure label is saved before creating relationship
                        
                        # Create task-label relationship
                        task_label = TaskLabel(
                            task_id=str(task.id),
                            label_id=label.id
                        )
                        session.add(task_label)
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
                    
                    # Add dependencies for new task
                    for dependency in task.dependencies:
                        new_dependency = TaskDependency(
                            task_id=str(task.id),
                            depends_on_task_id=str(dependency.value if hasattr(dependency, 'value') else dependency),
                            dependency_type="blocks"
                        )
                        session.add(new_dependency)
                    
                    # Add labels for new task
                    from ...database.models import Label
                    for label_name in task.labels:
                        # Get or create label
                        label = session.query(Label).filter(Label.name == label_name).first()
                        if not label:
                            # Create new label with a unique ID
                            import uuid
                            label = Label(
                                id=str(uuid.uuid4()),
                                name=label_name,
                                color="#0066cc",
                                description=""
                            )
                            session.add(label)
                            session.flush()  # Ensure label is saved before creating relationship
                        
                        # Create task-label relationship
                        task_label = TaskLabel(
                            task_id=str(task.id),
                            label_id=label.id
                        )
                        session.add(task_label)
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            return False
    
    def find_by_id(self, task_id) -> TaskEntity | None:
        """Find task by ID"""
        return self.get_task(str(task_id))
    
    def find_all(self) -> list[TaskEntity]:
        """Find all tasks"""
        return self.list_tasks()
    
    def find_by_status(self, status) -> list[TaskEntity]:
        """Find tasks by status"""
        return self.list_tasks(status=str(status))
    
    def find_by_priority(self, priority) -> list[TaskEntity]:
        """Find tasks by priority"""
        return self.list_tasks(priority=str(priority))
    
    def find_by_assignee(self, assignee: str) -> list[TaskEntity]:
        """Find tasks by assignee"""
        return self.get_tasks_by_assignee(assignee)
    
    def find_by_labels(self, labels: list[str]) -> list[TaskEntity]:
        """Find tasks containing any of the specified labels"""
        # This would need to be implemented based on your label system
        return []
    
    def search(self, query: str, limit: int = 10) -> list[TaskEntity]:
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
    
    def find_by_criteria(self, filters: dict[str, Any], limit: int | None = None) -> list[TaskEntity]:
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
    
    def get_statistics(self) -> dict[str, Any]:
        """Get task statistics"""
        return {
            "total_tasks": self.get_task_count(),
            "completed_tasks": self.get_task_count(status="completed"),
            "in_progress_tasks": self.get_task_count(status="in_progress"),
            "todo_tasks": self.get_task_count(status="todo")
        }
    
    def find_by_id_all_states(self, task_id) -> TaskEntity | None:
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