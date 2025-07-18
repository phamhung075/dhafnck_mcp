#!/usr/bin/env python3
"""
Test script to validate the dependency management fix
"""

import pytest
import sys
import os
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


class FixedMockTaskRepository(TaskRepository):
    """Mock repository with the fix implemented"""
    
    def __init__(self):
        self.active_tasks = {}
        self.completed_tasks = {}
        self.archived_tasks = {}
    
    def save(self, task: Task) -> bool:
        """Save task to appropriate collection based on status"""
        if task.status.is_done():
            self.completed_tasks[str(task.id)] = task
            # Remove from active if it was there
            self.active_tasks.pop(str(task.id), None)
        else:
            self.active_tasks[str(task.id)] = task
        return True
    
    def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Find task by ID - only checks active tasks (original behavior)"""
        return self.active_tasks.get(str(task_id))
    
    def find_by_id_all_states(self, task_id: TaskId) -> Optional[Task]:
        """Find task by ID across all states - THE FIX!"""
        task_id_str = str(task_id)
        
        # Check active tasks first
        if task_id_str in self.active_tasks:
            return self.active_tasks[task_id_str]
        
        # Check completed tasks
        if task_id_str in self.completed_tasks:
            return self.completed_tasks[task_id_str]
        
        # Check archived tasks
        if task_id_str in self.archived_tasks:
            return self.archived_tasks[task_id_str]
        
        return None
    
    def find_all(self) -> List[Task]:
        """Find all tasks"""
        all_tasks = list(self.active_tasks.values())
        all_tasks.extend(self.completed_tasks.values())
        all_tasks.extend(self.archived_tasks.values())
        return all_tasks
    
    def find_by_status(self, status: TaskStatus) -> List[Task]:
        """Find tasks by status"""
        if status.is_done():
            return list(self.completed_tasks.values())
        else:
            return [t for t in self.active_tasks.values() if t.status == status]
    
    def find_by_priority(self, priority: Priority) -> List[Task]:
        """Find tasks by priority"""
        return [t for t in self.find_all() if t.priority == priority]
    
    def find_by_assignee(self, assignee: str) -> List[Task]:
        """Find tasks by assignee"""
        return [t for t in self.find_all() if assignee in (t.assignees or [])]
    
    def find_by_labels(self, labels: List[str]) -> List[Task]:
        """Find tasks containing any of the specified labels"""
        return [t for t in self.find_all() if any(label in (t.labels or []) for label in labels)]
    
    def search(self, query: str, limit: int = 10) -> List[Task]:
        """Search tasks by query string"""
        results = []
        for task in self.find_all():
            if query.lower() in task.title.lower() or query.lower() in task.description.lower():
                results.append(task)
                if len(results) >= limit:
                    break
        return results
    
    def delete(self, task_id: TaskId) -> bool:
        """Delete a task"""
        task_id_str = str(task_id)
        if task_id_str in self.active_tasks:
            del self.active_tasks[task_id_str]
            return True
        if task_id_str in self.completed_tasks:
            del self.completed_tasks[task_id_str]
            return True
        if task_id_str in self.archived_tasks:
            del self.archived_tasks[task_id_str]
            return True
        return False
    
    def exists(self, task_id: TaskId) -> bool:
        """Check if task exists"""
        task_id_str = str(task_id)
        return (task_id_str in self.active_tasks or 
                task_id_str in self.completed_tasks or 
                task_id_str in self.archived_tasks)
    
    def get_next_id(self) -> TaskId:
        """Get next available task ID"""
        return TaskId(str(uuid4()))
    
    def count(self) -> int:
        """Get total number of tasks"""
        return len(self.active_tasks) + len(self.completed_tasks) + len(self.archived_tasks)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics"""
        return {
            "total": self.count(),
            "active": len(self.active_tasks),
            "completed": len(self.completed_tasks),
            "archived": len(self.archived_tasks)
        }
    
    def find_by_criteria(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Task]:
        """Find tasks by multiple criteria"""
        results = self.find_all()
        
        # Apply filters
        if 'status' in filters:
            results = [t for t in results if t.status == filters['status']]
        if 'priority' in filters:
            results = [t for t in results if t.priority == filters['priority']]
        if 'assignee' in filters:
            results = [t for t in results if filters['assignee'] in (t.assignees or [])]
        if 'label' in filters:
            results = [t for t in results if filters['label'] in (t.labels or [])]
        
        # Apply limit if specified
        if limit:
            results = results[:limit]
        
        return results


def test_fix_validation():
    """Test that the fix works correctly"""
    print("🔧 Testing Dependency Management Fix")
    print("=" * 50)
    
    # Setup
    repository = FixedMockTaskRepository()
    add_dependency_use_case = AddDependencyUseCase(repository)
    
    # Create test tasks
    active_task_id = TaskId(str(uuid4()))
    completed_task_id = TaskId(str(uuid4()))
    archived_task_id = TaskId(str(uuid4()))
    
    # Create and save active task
    active_task = Task(
        id=active_task_id,
        title="Active Task",
        description="This is an active task",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    repository.save(active_task)
    
    # Create and save completed task
    completed_task = Task(
        id=completed_task_id,
        title="Completed Task",
        description="This task is completed",
        status=TaskStatus.done(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    repository.save(completed_task)
    
    # Create and save archived task
    archived_task = Task(
        id=archived_task_id,
        title="Archived Task", 
        description="This task is archived",
        status=TaskStatus.done(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    repository.archived_tasks[str(archived_task_id)] = archived_task
    
    print(f"✅ Setup complete:")
    print(f"   Active tasks: {len(repository.active_tasks)}")
    print(f"   Completed tasks: {len(repository.completed_tasks)}")
    print(f"   Archived tasks: {len(repository.archived_tasks)}")
    
    # Test 1: Active task dependency (should still work)
    print("\n1. Testing active task dependency...")
    dependent_task_id = TaskId(str(uuid4()))
    dependent_task = Task(
        id=dependent_task_id,
        title="Dependent Task",
        description="Task that depends on active task",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    repository.save(dependent_task)
    
    request = AddDependencyRequest(
        task_id=str(dependent_task_id),
        depends_on_task_id=str(active_task_id)
    )
    
    result = add_dependency_use_case.execute(request)
    assert result.success is True, f"Active task dependency failed: {result}"
    print("✅ Active task dependency works correctly")
    
    # Test 2: Completed task dependency (should now work!)
    print("\n2. Testing completed task dependency...")
    dependent_task_id2 = TaskId(str(uuid4()))
    dependent_task2 = Task(
        id=dependent_task_id2,
        title="Dependent Task 2",
        description="Task that depends on completed task",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    repository.save(dependent_task2)
    
    request2 = AddDependencyRequest(
        task_id=str(dependent_task_id2),
        depends_on_task_id=str(completed_task_id)
    )
    
    result2 = add_dependency_use_case.execute(request2)
    assert result2.success is True, f"Completed task dependency failed: {result2}"
    print("✅ Completed task dependency now works! (FIXED)")
    print(f"   Message: {result2.message}")
    
    # Test 3: Archived task dependency (should now work!)
    print("\n3. Testing archived task dependency...")
    dependent_task_id3 = TaskId(str(uuid4()))
    dependent_task3 = Task(
        id=dependent_task_id3,
        title="Dependent Task 3",
        description="Task that depends on archived task",
        status=TaskStatus.todo(),
        priority=Priority.medium(),
        git_branch_id=str(uuid4())
    )
    repository.save(dependent_task3)
    
    request3 = AddDependencyRequest(
        task_id=str(dependent_task_id3),
        depends_on_task_id=str(archived_task_id)
    )
    
    result3 = add_dependency_use_case.execute(request3)
    assert result3.success is True, f"Archived task dependency failed: {result3}"
    print("✅ Archived task dependency now works! (FIXED)")
    print(f"   Message: {result3.message}")
    
    # Test 4: Non-existent task dependency (should still fail appropriately)
    print("\n4. Testing non-existent task dependency...")
    nonexistent_task_id = TaskId(str(uuid4()))
    
    request4 = AddDependencyRequest(
        task_id=str(dependent_task_id),
        depends_on_task_id=str(nonexistent_task_id)
    )
    
    with pytest.raises(Exception) as exc_info:
        add_dependency_use_case.execute(request4)
    
    print(f"✅ Non-existent task dependency correctly fails: {exc_info.value}")
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! The dependency management fix is working correctly.")


if __name__ == "__main__":
    try:
        test_fix_validation()
        print("\n🚀 Ready to run the full test suite!")
    except Exception as e:
        print(f"\n❌ Fix validation failed: {e}")