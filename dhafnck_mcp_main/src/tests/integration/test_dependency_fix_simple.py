#!/usr/bin/env python3
"""
Simple test for dependency management fix (without database dependencies)
"""

import pytest
import sys
from datetime import datetime
from uuid import uuid4
from typing import List, Optional, Dict, Any

# Add the source path to sys.path for imports
sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.application.use_cases.add_dependency import AddDependencyUseCase
from fastmcp.task_management.application.dtos.dependency.add_dependency_request import AddDependencyRequest
from fastmcp.task_management.domain.repositories.task_repository import TaskRepository


class SimpleTaskRepository(TaskRepository):
    """Simple mock repository for testing"""
    
    def __init__(self):
        self.tasks = {}
    
    def save(self, task: Task) -> bool:
        self.tasks[str(task.id)] = task
        return True
    
    def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        return self.tasks.get(str(task_id))
    
    def find_by_id_all_states(self, task_id: TaskId) -> Optional[Task]:
        """The fix - search all tasks regardless of state"""
        return self.tasks.get(str(task_id))
    
    def find_all(self) -> List[Task]:
        return list(self.tasks.values())
    
    def find_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self.tasks.values() if t.status == status]
    
    def find_by_priority(self, priority: Priority) -> List[Task]:
        return [t for t in self.tasks.values() if t.priority == priority]
    
    def find_by_assignee(self, assignee: str) -> List[Task]:
        return [t for t in self.tasks.values() if assignee in (t.assignees or [])]
    
    def find_by_labels(self, labels: List[str]) -> List[Task]:
        return [t for t in self.tasks.values() if any(label in (t.labels or []) for label in labels)]
    
    def search(self, query: str, limit: int = 10) -> List[Task]:
        return []
    
    def delete(self, task_id: TaskId) -> bool:
        if str(task_id) in self.tasks:
            del self.tasks[str(task_id)]
            return True
        return False
    
    def exists(self, task_id: TaskId) -> bool:
        return str(task_id) in self.tasks
    
    def get_next_id(self) -> TaskId:
        return TaskId(str(uuid4()))
    
    def count(self) -> int:
        return len(self.tasks)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {"total": len(self.tasks)}
    
    def find_by_criteria(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Task]:
        return []


def test_dependency_fix_simple():
    """Test the dependency management fix with simple validation"""
    
    print("🧪 DEPENDENCY MANAGEMENT FIX - SIMPLE TEST")
    print("=" * 50)
    
    repository = SimpleTaskRepository()
    use_case = AddDependencyUseCase(repository)
    
    # Test 1: Active task dependency
    print("\n1. Testing active task dependency...")
    
    task1 = Task(
        id=TaskId(str(uuid4())),
        title="Task 1",
        description="Task 1",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    
    task2 = Task(
        id=TaskId(str(uuid4())),
        title="Task 2",
        description="Task 2",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    
    repository.save(task1)
    repository.save(task2)
    
    request = AddDependencyRequest(
        task_id=str(task1.id),
        depends_on_task_id=str(task2.id)
    )
    
    result = use_case.execute(request)
    assert result.success is True, f"Active task dependency failed: {result}"
    print("   ✅ Active task dependency works")
    
    # Test 2: Completed task dependency
    print("\n2. Testing completed task dependency...")
    
    completed_task = Task(
        id=TaskId(str(uuid4())),
        title="Completed Task",
        description="Completed Task",
        status=TaskStatus.done(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    
    active_task = Task(
        id=TaskId(str(uuid4())),
        title="Active Task",
        description="Active Task",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    
    repository.save(completed_task)
    repository.save(active_task)
    
    request = AddDependencyRequest(
        task_id=str(active_task.id),
        depends_on_task_id=str(completed_task.id)
    )
    
    result = use_case.execute(request)
    assert result.success is True, f"Completed task dependency failed: {result}"
    assert "completed" in result.message.lower(), f"Expected 'completed' in message but got: {result.message}"
    print("   ✅ Completed task dependency works (FIXED!)")
    
    # Test 3: Non-existent task dependency
    print("\n3. Testing non-existent task dependency...")
    
    request = AddDependencyRequest(
        task_id=str(task1.id),
        depends_on_task_id=str(uuid4())
    )
    
    with pytest.raises(Exception) as exc_info:
        use_case.execute(request)
    
    error_message = str(exc_info.value).lower()
    assert "not found" in error_message, f"Expected 'not found' error but got: {exc_info.value}"
    print("   ✅ Non-existent task dependency correctly fails")
    
    print("\n" + "="*50)
    print("🎉 ALL TESTS PASSED!")
    print("✅ The dependency management fix is working correctly!")


if __name__ == "__main__":
    try:
        test_dependency_fix_simple()
        print("\n🚀 Ready for production use!")
    except Exception as e:
        print(f"\n❌ Fix validation failed: {e}")