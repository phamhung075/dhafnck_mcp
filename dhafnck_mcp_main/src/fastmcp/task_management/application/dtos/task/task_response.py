"""Response DTO for task operations"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from .dependency_info import DependencyRelationships

@dataclass
class TaskResponse:
    """Response DTO for task operations following clean relationship chain"""
    id: str
    title: str
    description: str
    status: str
    priority: str
    details: str
    estimated_effort: str
    assignees: List[str]
    labels: List[str]
    dependencies: List[str]
    subtasks: List[Dict[str, Any]]
    due_date: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    git_branch_id: Optional[str] = None  # Links to git_branch which contains project and user info
    context_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    dependency_relationships: Optional[DependencyRelationships] = None  # Enhanced dependency information
    
    def __init__(
            self, 
            id: str, 
            title: str, 
            description: str, 
            status: str, 
            priority: str,                  
            details: str, 
            estimated_effort: str, 
            assignees: List[str], 
            labels: List[str],
            dependencies: List[str], 
            subtasks: List[Dict[str, Any]], 
            due_date: Optional[str],
            created_at: Optional[datetime], 
            updated_at: Optional[datetime], 
            git_branch_id: Optional[str] = None,  # Following clean relationship chain
            context_id: Optional[str] = None,
            context_data: Optional[Dict[str, Any]] = None,
            dependency_relationships: Optional[DependencyRelationships] = None 
        ):
        """Initialize TaskResponse following clean relationship chain with git_branch_id, context_id, and context_data"""
        self.id = id
        self.title = title
        self.description = description
        self.git_branch_id = git_branch_id
        self.status = status
        self.priority = priority
        self.details = details
        self.estimated_effort = estimated_effort
        self.assignees = assignees
        self.labels = labels
        self.dependencies = dependencies
        self.subtasks = subtasks
        self.due_date = due_date
        self.created_at = created_at
        self.updated_at = updated_at
        self.context_id = context_id
        self.context_data = context_data
        self.dependency_relationships = dependency_relationships    
    @classmethod
    def from_domain(cls, task, context_data: Optional[Dict[str, Any]] = None, 
                   dependency_relationships: Optional[DependencyRelationships] = None) -> 'TaskResponse':
        """Create response DTO from domain entity with optional context data"""
        task_dict = task.to_dict()
        
        # Parse datetime strings back to datetime objects if they're strings
        created_at = task_dict["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = task_dict["updated_at"]  
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        
        return cls(
            id=task_dict["id"],
            title=task_dict["title"],
            description=task_dict["description"],
            status=task_dict["status"],
            priority=task_dict["priority"],
            details=task_dict["details"],
            estimated_effort=task_dict["estimatedEffort"],
            assignees=task_dict["assignees"],
            labels=task_dict["labels"],
            dependencies=task_dict["dependencies"],
            subtasks=task_dict["subtasks"],
            due_date=task_dict["dueDate"],
            created_at=created_at,
            updated_at=updated_at,
            git_branch_id=task_dict.get("git_branch_id"),  # Following clean relationship chain
            context_id=task_dict.get("context_id"),
            context_data=context_data,
            dependency_relationships=dependency_relationships
        ) 