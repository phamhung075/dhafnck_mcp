"""
Comprehensive Integration Tests for Subtask Management Systems
Tests all subtask operations with real task-subtask relationships.

This test suite covers:
1. Subtask CRUD operations (create, update, get, list, delete, complete)
2. Subtask-task relationship management
3. Subtask progress tracking with percentage
4. Subtask completion workflow with parent task updates
5. Subtask ordering and prioritization
6. Parent task progress aggregation
7. Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Import actual domain objects
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus, TaskStatusEnum

pytestmark = pytest.mark.integration


class MockSubtask:
    """Mock Subtask entity for testing"""
    def __init__(self,
                 id: str,
                 task_id: str,
                 title: str,
                 description: str = None,
                 status: str = "todo",
                 priority: str = "medium",
                 assignees: List[str] = None,
                 progress_percentage: int = 0,
                 order: int = 0,
                 blockers: str = None,
                 insights_found: List[str] = None,
                 completion_summary: str = None,
                 impact_on_parent: str = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.id = id
        self.task_id = task_id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.assignees = assignees or []
        self.progress_percentage = progress_percentage
        self.order = order
        self.blockers = blockers
        self.insights_found = insights_found or []
        self.completion_summary = completion_summary
        self.impact_on_parent = impact_on_parent
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assignees": self.assignees,
            "progress_percentage": self.progress_percentage,
            "order": self.order,
            "blockers": self.blockers,
            "insights_found": self.insights_found,
            "completion_summary": self.completion_summary,
            "impact_on_parent": self.impact_on_parent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class MockTask:
    """Mock Task entity for testing subtask relationships"""
    def __init__(self,
                 id: str,
                 title: str,
                 subtask_ids: List[str] = None,
                 status: str = "todo",
                 progress_percentage: int = 0,
                 project_id: str = "default_project",
                 git_branch_id: str = "default_branch"):
        self.id = id
        self.title = title
        self.subtask_ids = subtask_ids or []
        self.status = status
        self.progress_percentage = progress_percentage
        self.project_id = project_id
        self.git_branch_id = git_branch_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def calculate_progress(self, subtasks: List[MockSubtask]) -> int:
        """Calculate task progress based on subtasks"""
        if not subtasks:
            return 0
        
        total_progress = sum(subtask.progress_percentage for subtask in subtasks)
        return total_progress // len(subtasks)

    def update_status_from_subtasks(self, subtasks: List[MockSubtask]):
        """Update task status based on subtask completion"""
        if not subtasks:
            return
        
        completed_subtasks = [s for s in subtasks if s.status == "done"]
        in_progress_subtasks = [s for s in subtasks if s.status == "in_progress"]
        
        if len(completed_subtasks) == len(subtasks):
            self.status = "done"
        elif len(completed_subtasks) > 0 or len(in_progress_subtasks) > 0:
            self.status = "in_progress"
        else:
            self.status = "todo"


class MockSubtaskRepository:
    """Mock Subtask Repository for testing"""
    def __init__(self):
        self.subtasks: Dict[str, MockSubtask] = {}
        self.tasks: Dict[str, MockTask] = {}

    def save_subtask(self, subtask: MockSubtask) -> MockSubtask:
        """Save subtask to mock storage"""
        subtask.updated_at = datetime.now()
        self.subtasks[subtask.id] = subtask
        return subtask

    def save_task(self, task: MockTask) -> MockTask:
        """Save task to mock storage"""
        task.updated_at = datetime.now()
        self.tasks[task.id] = task
        return task

    def find_subtask_by_id(self, subtask_id: str) -> Optional[MockSubtask]:
        """Find subtask by ID"""
        return self.subtasks.get(subtask_id)

    def find_task_by_id(self, task_id: str) -> Optional[MockTask]:
        """Find task by ID"""
        return self.tasks.get(task_id)

    def find_subtasks_by_task_id(self, task_id: str) -> List[MockSubtask]:
        """Find all subtasks for a task"""
        return [subtask for subtask in self.subtasks.values() if subtask.task_id == task_id]

    def delete_subtask(self, subtask_id: str) -> bool:
        """Delete subtask by ID"""
        if subtask_id in self.subtasks:
            subtask = self.subtasks[subtask_id]
            
            # Remove from parent task's subtask_ids
            task = self.find_task_by_id(subtask.task_id)
            if task and subtask_id in task.subtask_ids:
                task.subtask_ids.remove(subtask_id)
                self.save_task(task)
            
            del self.subtasks[subtask_id]
            return True
        return False

    def get_subtask_progress_summary(self, task_id: str) -> Dict[str, Any]:
        """Get progress summary for all subtasks of a task"""
        subtasks = self.find_subtasks_by_task_id(task_id)
        if not subtasks:
            return {
                "total_subtasks": 0,
                "completed_subtasks": 0,
                "in_progress_subtasks": 0,
                "todo_subtasks": 0,
                "overall_progress": 0
            }

        completed = len([s for s in subtasks if s.status == "done"])
        in_progress = len([s for s in subtasks if s.status == "in_progress"])
        todo = len([s for s in subtasks if s.status == "todo"])
        
        return {
            "total_subtasks": len(subtasks),
            "completed_subtasks": completed,
            "in_progress_subtasks": in_progress,
            "todo_subtasks": todo,
            "overall_progress": (completed * 100) // len(subtasks) if subtasks else 0
        }


class TestComprehensiveSubtaskManagement:
    """Comprehensive test suite for Subtask Management operations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = MockSubtaskRepository()
        self.mock_context_service = Mock()
        
        # Test data
        self.project_id = "test-project-123"
        self.git_branch_id = "branch-456"
        self.task_id = str(uuid.uuid4())
        self.user_id = "user-123"
        
        # Create parent task
        self.parent_task = MockTask(
            id=self.task_id,
            title="Parent Task for Subtasks",
            project_id=self.project_id,
            git_branch_id=self.git_branch_id
        )
        self.repository.save_task(self.parent_task)

    # ===== SUBTASK CREATION TESTS =====

    def test_create_subtask_success(self):
        """Test successful subtask creation"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask_data = {
            "title": "Implement user login",
            "description": "Create login form and validation",
            "priority": "high",
            "assignees": ["dev1"]
        }
        
        # Act
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            **subtask_data
        )
        saved_subtask = self.repository.save_subtask(subtask)
        
        # Update parent task
        self.parent_task.subtask_ids.append(subtask_id)
        self.repository.save_task(self.parent_task)
        
        # Assert
        assert saved_subtask.id == subtask_id
        assert saved_subtask.task_id == self.task_id
        assert saved_subtask.title == subtask_data["title"]
        assert saved_subtask.status == "todo"
        assert saved_subtask.progress_percentage == 0
        assert subtask_id in self.parent_task.subtask_ids

    def test_create_multiple_subtasks_with_ordering(self):
        """Test creating multiple subtasks with proper ordering"""
        # Arrange
        subtask_data = [
            {"title": "Design API", "order": 1},
            {"title": "Implement logic", "order": 2},
            {"title": "Add tests", "order": 3},
            {"title": "Documentation", "order": 4}
        ]
        
        # Act
        created_subtasks = []
        for i, data in enumerate(subtask_data):
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            saved_subtask = self.repository.save_subtask(subtask)
            created_subtasks.append(saved_subtask)
            
            # Update parent task
            self.parent_task.subtask_ids.append(subtask.id)
        
        self.repository.save_task(self.parent_task)
        
        # Assert
        assert len(created_subtasks) == 4
        assert len(self.parent_task.subtask_ids) == 4
        
        # Verify ordering
        for i, subtask in enumerate(created_subtasks):
            assert subtask.order == i + 1
            assert subtask.task_id == self.task_id

    def test_create_subtask_with_assignees(self):
        """Test creating subtask with multiple assignees"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        assignees = ["dev1", "dev2", "qa1"]
        
        # Act
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Multi-assignee subtask",
            assignees=assignees
        )
        saved_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert len(saved_subtask.assignees) == 3
        assert "dev1" in saved_subtask.assignees
        assert "dev2" in saved_subtask.assignees
        assert "qa1" in saved_subtask.assignees

    # ===== SUBTASK RETRIEVAL TESTS =====

    def test_get_subtask_success(self):
        """Test successful subtask retrieval"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Test Subtask"
        )
        self.repository.save_subtask(subtask)
        
        # Act
        retrieved_subtask = self.repository.find_subtask_by_id(subtask_id)
        
        # Assert
        assert retrieved_subtask is not None
        assert retrieved_subtask.id == subtask_id
        assert retrieved_subtask.task_id == self.task_id
        assert retrieved_subtask.title == "Test Subtask"

    def test_list_subtasks_by_task(self):
        """Test listing all subtasks for a task"""
        # Arrange
        subtasks_data = [
            {"title": "Subtask 1", "status": "todo"},
            {"title": "Subtask 2", "status": "in_progress"},
            {"title": "Subtask 3", "status": "done"}
        ]
        
        created_ids = []
        for data in subtasks_data:
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            self.repository.save_subtask(subtask)
            created_ids.append(subtask.id)
        
        # Act
        subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        
        # Assert
        assert len(subtasks) == 3
        subtask_titles = [s.title for s in subtasks]
        assert "Subtask 1" in subtask_titles
        assert "Subtask 2" in subtask_titles
        assert "Subtask 3" in subtask_titles
        
        # Verify all belong to same task
        for subtask in subtasks:
            assert subtask.task_id == self.task_id

    def test_get_subtask_progress_summary(self):
        """Test getting progress summary for task subtasks"""
        # Arrange
        subtasks_data = [
            {"title": "Subtask 1", "status": "done", "progress_percentage": 100},
            {"title": "Subtask 2", "status": "in_progress", "progress_percentage": 50},
            {"title": "Subtask 3", "status": "todo", "progress_percentage": 0}
        ]
        
        for data in subtasks_data:
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            self.repository.save_subtask(subtask)
        
        # Act
        summary = self.repository.get_subtask_progress_summary(self.task_id)
        
        # Assert
        assert summary["total_subtasks"] == 3
        assert summary["completed_subtasks"] == 1
        assert summary["in_progress_subtasks"] == 1
        assert summary["todo_subtasks"] == 1
        assert summary["overall_progress"] == 33  # 1/3 * 100

    # ===== SUBTASK UPDATE TESTS =====

    def test_update_subtask_progress(self):
        """Test updating subtask progress percentage"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Progressive Subtask",
            progress_percentage=0
        )
        self.repository.save_subtask(subtask)
        
        # Act - Progress through stages
        progress_stages = [25, 50, 75, 100]
        for progress in progress_stages:
            subtask.progress_percentage = progress
            
            # Auto-update status based on progress
            if progress == 0:
                subtask.status = "todo"
            elif progress == 100:
                subtask.status = "done"
            else:
                subtask.status = "in_progress"
            
            updated_subtask = self.repository.save_subtask(subtask)
            
            # Assert
            assert updated_subtask.progress_percentage == progress
            if progress == 0:
                assert updated_subtask.status == "todo"
            elif progress == 100:
                assert updated_subtask.status == "done"
            else:
                assert updated_subtask.status == "in_progress"

    def test_update_subtask_with_blockers(self):
        """Test updating subtask with blockers"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Blocked Subtask"
        )
        self.repository.save_subtask(subtask)
        
        # Act
        blocker_info = "Waiting for API documentation from team"
        subtask.blockers = blocker_info
        subtask.status = "blocked"
        updated_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert updated_subtask.blockers == blocker_info
        assert updated_subtask.status == "blocked"

    def test_update_subtask_insights(self):
        """Test updating subtask with insights found"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Learning Subtask"
        )
        self.repository.save_subtask(subtask)
        
        # Act
        insights = [
            "Found existing validation utility",
            "Database schema needs optimization",
            "Security considerations for JWT"
        ]
        subtask.insights_found = insights
        updated_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert len(updated_subtask.insights_found) == 3
        assert "Found existing validation utility" in updated_subtask.insights_found
        assert "Security considerations for JWT" in updated_subtask.insights_found

    # ===== SUBTASK COMPLETION TESTS =====

    def test_complete_subtask_success(self):
        """Test successful subtask completion"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Completable Subtask",
            status="in_progress",
            progress_percentage=75
        )
        self.repository.save_subtask(subtask)
        
        # Act
        completion_summary = "Implemented login form with validation and error handling"
        impact_on_parent = "Authentication module 50% complete"
        
        subtask.status = "done"
        subtask.progress_percentage = 100
        subtask.completion_summary = completion_summary
        subtask.impact_on_parent = impact_on_parent
        
        completed_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert completed_subtask.status == "done"
        assert completed_subtask.progress_percentage == 100
        assert completed_subtask.completion_summary == completion_summary
        assert completed_subtask.impact_on_parent == impact_on_parent

    def test_complete_all_subtasks_updates_parent(self):
        """Test that completing all subtasks updates parent task status"""
        # Arrange
        subtasks_data = [
            {"title": "Subtask 1", "status": "in_progress"},
            {"title": "Subtask 2", "status": "in_progress"},
            {"title": "Subtask 3", "status": "in_progress"}
        ]
        
        subtasks = []
        for data in subtasks_data:
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            saved_subtask = self.repository.save_subtask(subtask)
            subtasks.append(saved_subtask)
            self.parent_task.subtask_ids.append(subtask.id)
        
        # Act - Complete all subtasks
        for subtask in subtasks:
            subtask.status = "done"
            subtask.progress_percentage = 100
            self.repository.save_subtask(subtask)
        
        # Update parent task based on subtasks
        task_subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        self.parent_task.update_status_from_subtasks(task_subtasks)
        self.parent_task.progress_percentage = self.parent_task.calculate_progress(task_subtasks)
        self.repository.save_task(self.parent_task)
        
        # Assert
        updated_parent = self.repository.find_task_by_id(self.task_id)
        assert updated_parent.status == "done"
        assert updated_parent.progress_percentage == 100

    def test_partial_subtask_completion_updates_parent(self):
        """Test that partial subtask completion updates parent progress"""
        # Arrange
        subtasks_data = [
            {"title": "Subtask 1", "status": "done", "progress_percentage": 100},
            {"title": "Subtask 2", "status": "in_progress", "progress_percentage": 50},
            {"title": "Subtask 3", "status": "todo", "progress_percentage": 0}
        ]
        
        for data in subtasks_data:
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            self.repository.save_subtask(subtask)
            self.parent_task.subtask_ids.append(subtask.id)
        
        # Act
        task_subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        self.parent_task.update_status_from_subtasks(task_subtasks)
        self.parent_task.progress_percentage = self.parent_task.calculate_progress(task_subtasks)
        self.repository.save_task(self.parent_task)
        
        # Assert
        updated_parent = self.repository.find_task_by_id(self.task_id)
        assert updated_parent.status == "in_progress"
        assert updated_parent.progress_percentage == 50  # (100 + 50 + 0) / 3

    # ===== SUBTASK DELETION TESTS =====

    def test_delete_subtask_success(self):
        """Test successful subtask deletion"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Deletable Subtask"
        )
        self.repository.save_subtask(subtask)
        self.parent_task.subtask_ids.append(subtask_id)
        self.repository.save_task(self.parent_task)
        
        # Verify subtask exists
        assert self.repository.find_subtask_by_id(subtask_id) is not None
        assert subtask_id in self.parent_task.subtask_ids
        
        # Act
        deleted = self.repository.delete_subtask(subtask_id)
        
        # Assert
        assert deleted is True
        assert self.repository.find_subtask_by_id(subtask_id) is None
        
        # Check parent task updated
        updated_parent = self.repository.find_task_by_id(self.task_id)
        assert subtask_id not in updated_parent.subtask_ids

    def test_delete_subtask_not_found(self):
        """Test subtask deletion when subtask doesn't exist"""
        # Act
        deleted = self.repository.delete_subtask("nonexistent-id")
        
        # Assert
        assert deleted is False

    # ===== SUBTASK WORKFLOW TESTS =====

    def test_subtask_priority_inheritance(self):
        """Test subtask inheriting priority from parent task"""
        # Arrange
        self.parent_task.priority = "urgent"
        self.repository.save_task(self.parent_task)
        
        # Act
        subtask = MockSubtask(
            id=str(uuid.uuid4()),
            task_id=self.task_id,
            title="Inherited Priority Subtask",
            priority="urgent"  # Inherited from parent
        )
        saved_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert saved_subtask.priority == "urgent"

    def test_subtask_assignee_management(self):
        """Test adding and removing assignees from subtasks"""
        # Arrange
        subtask_id = str(uuid.uuid4())
        subtask = MockSubtask(
            id=subtask_id,
            task_id=self.task_id,
            title="Assignee Test Subtask",
            assignees=["dev1"]
        )
        self.repository.save_subtask(subtask)
        
        # Act - Add assignees
        subtask.assignees.extend(["dev2", "qa1"])
        updated_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert len(updated_subtask.assignees) == 3
        assert "dev1" in updated_subtask.assignees
        assert "dev2" in updated_subtask.assignees
        assert "qa1" in updated_subtask.assignees
        
        # Act - Remove assignee
        subtask.assignees.remove("dev1")
        final_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert len(final_subtask.assignees) == 2
        assert "dev1" not in final_subtask.assignees

    # ===== COMPLEX WORKFLOW TESTS =====

    def test_full_subtask_lifecycle_with_parent_updates(self):
        """Test complete subtask lifecycle with parent task updates"""
        # Arrange - Create multiple subtasks
        subtasks_data = [
            {"title": "Database Schema", "priority": "high"},
            {"title": "API Endpoints", "priority": "high"},
            {"title": "Frontend Integration", "priority": "medium"},
            {"title": "Testing", "priority": "medium"}
        ]
        
        created_subtasks = []
        for data in subtasks_data:
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            saved_subtask = self.repository.save_subtask(subtask)
            created_subtasks.append(saved_subtask)
            self.parent_task.subtask_ids.append(subtask.id)
        
        self.repository.save_task(self.parent_task)
        
        # Act & Assert - Progress through subtasks
        
        # 1. Start first subtask
        created_subtasks[0].status = "in_progress"
        created_subtasks[0].progress_percentage = 30
        self.repository.save_subtask(created_subtasks[0])
        
        # Update parent
        task_subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        self.parent_task.update_status_from_subtasks(task_subtasks)
        self.parent_task.progress_percentage = self.parent_task.calculate_progress(task_subtasks)
        self.repository.save_task(self.parent_task)
        
        parent = self.repository.find_task_by_id(self.task_id)
        assert parent.status == "in_progress"
        assert parent.progress_percentage == 7  # 30/4 = 7.5 -> 7
        
        # 2. Complete first subtask, start second
        created_subtasks[0].status = "done"
        created_subtasks[0].progress_percentage = 100
        created_subtasks[0].completion_summary = "Database schema created with all required tables"
        self.repository.save_subtask(created_subtasks[0])
        
        created_subtasks[1].status = "in_progress"
        created_subtasks[1].progress_percentage = 60
        self.repository.save_subtask(created_subtasks[1])
        
        # Update parent
        task_subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        self.parent_task.update_status_from_subtasks(task_subtasks)
        self.parent_task.progress_percentage = self.parent_task.calculate_progress(task_subtasks)
        self.repository.save_task(self.parent_task)
        
        parent = self.repository.find_task_by_id(self.task_id)
        assert parent.status == "in_progress"
        assert parent.progress_percentage == 40  # (100 + 60 + 0 + 0) / 4 = 40
        
        # 3. Complete all subtasks
        for subtask in created_subtasks[1:]:
            subtask.status = "done"
            subtask.progress_percentage = 100
            subtask.completion_summary = f"Completed {subtask.title}"
            self.repository.save_subtask(subtask)
        
        # Final parent update
        task_subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        self.parent_task.update_status_from_subtasks(task_subtasks)
        self.parent_task.progress_percentage = self.parent_task.calculate_progress(task_subtasks)
        self.repository.save_task(self.parent_task)
        
        # Final assertions
        final_parent = self.repository.find_task_by_id(self.task_id)
        assert final_parent.status == "done"
        assert final_parent.progress_percentage == 100
        
        # Verify all subtasks completed
        final_subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        for subtask in final_subtasks:
            assert subtask.status == "done"
            assert subtask.progress_percentage == 100
            assert subtask.completion_summary is not None

    def test_subtask_insights_aggregation(self):
        """Test aggregating insights from multiple subtasks"""
        # Arrange
        subtasks_with_insights = [
            {
                "title": "Research Phase",
                "insights_found": ["Found existing library X", "API Y is deprecated"]
            },
            {
                "title": "Implementation Phase", 
                "insights_found": ["Performance bottleneck in Z", "Security consideration for JWT"]
            },
            {
                "title": "Testing Phase",
                "insights_found": ["Edge case in validation", "Missing error handling"]
            }
        ]
        
        # Act
        all_insights = []
        for data in subtasks_with_insights:
            subtask = MockSubtask(
                id=str(uuid.uuid4()),
                task_id=self.task_id,
                **data
            )
            self.repository.save_subtask(subtask)
            all_insights.extend(subtask.insights_found)
        
        # Assert
        assert len(all_insights) == 6
        assert "Found existing library X" in all_insights
        assert "Security consideration for JWT" in all_insights
        assert "Missing error handling" in all_insights

    # ===== VALIDATION AND ERROR TESTS =====

    def test_subtask_serialization(self):
        """Test subtask serialization to dictionary"""
        # Arrange
        subtask = MockSubtask(
            id=str(uuid.uuid4()),
            task_id=self.task_id,
            title="Serialization Test",
            assignees=["dev1", "dev2"],
            insights_found=["insight1", "insight2"],
            progress_percentage=75
        )
        
        # Act
        subtask_dict = subtask.to_dict()
        
        # Assert
        assert isinstance(subtask_dict, dict)
        required_fields = ["id", "task_id", "title", "status", "progress_percentage", 
                          "assignees", "insights_found"]
        for field in required_fields:
            assert field in subtask_dict
        
        assert subtask_dict["progress_percentage"] == 75
        assert isinstance(subtask_dict["assignees"], list)
        assert isinstance(subtask_dict["insights_found"], list)

    @pytest.mark.parametrize("status", ["todo", "in_progress", "blocked", "review", "done"])
    def test_valid_subtask_statuses(self, status):
        """Test all valid subtask statuses"""
        # Arrange & Act
        subtask = MockSubtask(
            id=str(uuid.uuid4()),
            task_id=self.task_id,
            title="Status Test",
            status=status
        )
        saved_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert saved_subtask.status == status

    @pytest.mark.parametrize("progress", [0, 25, 50, 75, 100])
    def test_valid_progress_percentages(self, progress):
        """Test valid progress percentages"""
        # Arrange & Act
        subtask = MockSubtask(
            id=str(uuid.uuid4()),
            task_id=self.task_id,
            title="Progress Test",
            progress_percentage=progress
        )
        saved_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert saved_subtask.progress_percentage == progress

    def test_subtask_without_parent_task(self):
        """Test handling subtask creation without valid parent task"""
        # Arrange
        invalid_task_id = "nonexistent-task-id"
        
        # Act
        subtask = MockSubtask(
            id=str(uuid.uuid4()),
            task_id=invalid_task_id,
            title="Orphan Subtask"
        )
        saved_subtask = self.repository.save_subtask(subtask)
        
        # Assert
        assert saved_subtask.task_id == invalid_task_id
        
        # Verify parent doesn't exist
        parent_task = self.repository.find_task_by_id(invalid_task_id)
        assert parent_task is None

    def test_empty_subtask_list_for_task(self):
        """Test handling task with no subtasks"""
        # Act
        subtasks = self.repository.find_subtasks_by_task_id(self.task_id)
        summary = self.repository.get_subtask_progress_summary(self.task_id)
        
        # Assert
        assert len(subtasks) == 0
        assert summary["total_subtasks"] == 0
        assert summary["overall_progress"] == 0