"""List Tasks Use Case"""

from typing import List

from ...application.dtos.task import (
    ListTasksRequest,
    TaskListResponse
)

from ...domain import TaskRepository, TaskStatus, Priority


class ListTasksUseCase:
    """Use case for listing tasks with optional filtering"""
    
    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository
    
    def execute(self, request: ListTasksRequest) -> TaskListResponse:
        """Execute the list tasks use case"""
        # Build filter criteria
        filters = {}
        
        if request.status:
            filters['status'] = TaskStatus(request.status)
        
        if request.priority:
            filters['priority'] = Priority(request.priority)
        
        # Handle both new assignees field and legacy assignee field
        if hasattr(request, 'assignees') and request.assignees:
            filters['assignees'] = request.assignees
        elif hasattr(request, 'assignee') and request.assignee:
            filters['assignee'] = request.assignee
        
        if request.labels:
            filters['labels'] = request.labels
        
        # Get tasks from repository
        tasks = self._task_repository.find_by_criteria(filters, limit=request.limit)
        
        # Prepare filters_applied for response
        filters_applied = {}
        if request.status:
            filters_applied['status'] = request.status
        if request.priority:
            filters_applied['priority'] = request.priority
        if hasattr(request, 'assignees') and request.assignees:
            filters_applied['assignees'] = request.assignees
        elif hasattr(request, 'assignee') and request.assignee:
            filters_applied['assignee'] = request.assignee
        if request.labels:
            filters_applied['labels'] = request.labels
        if request.limit:
            filters_applied['limit'] = request.limit
        
        # Convert to response DTO
        return TaskListResponse.from_domain_list(tasks, filters_applied=filters_applied) 