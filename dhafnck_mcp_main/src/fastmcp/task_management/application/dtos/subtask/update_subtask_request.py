"""Request DTO for updating a subtask"""

from dataclasses import dataclass
from typing import Union, Optional

@dataclass
class UpdateSubtaskRequest:
    task_id: Union[str, int]
    id: Union[str, int]
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignees: Optional[list] = None

    def __init__(self, task_id: str, id: str, title: str = None, description: str = None, 
                 status: str = None, priority: str = None, assignees: list = None):
        self.task_id = task_id
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.assignees = assignees 