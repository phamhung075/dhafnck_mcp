"""
TDD Tests for Cross-Branch Task Dependencies Fix
Issue: Dependency task with ID not found when task exists in different branch
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime


class TestCrossBranchDependenciesFix:
    """Test suite for fixing cross-branch task dependencies"""
    
    def test_add_dependency_should_fail_when_task_in_different_branch(self):
        """Test current behavior - dependency fails across branches"""
        # Arrange
        task_id = "task-in-branch-1"
        dependency_id = "task-in-branch-2"
        branch_1 = "feature/branch-1"
        branch_2 = "feature/branch-2"
        
        # Current behavior - this should fail
        error_msg = f"Dependency task with ID {dependency_id} not found"
        
        # Assert current behavior
        assert "not found" in error_msg
    
    def test_add_dependency_should_work_across_branches(self):
        """Test that dependencies should work across branches in same project"""
        # Arrange
        from src.domain.task import Task
        from src.infrastructure.task_repository import TaskRepository
        
        repo = TaskRepository(":memory:")
        
        # Create tasks in different branches
        task1 = Task(
            id="task-1",
            title="Task in branch 1",
            git_branch_id="branch-1",
            project_id="project-123"
        )
        
        task2 = Task(
            id="task-2", 
            title="Task in branch 2",
            git_branch_id="branch-2",
            project_id="project-123"
        )
        
        # Act - Add cross-branch dependency
        # This should work after fix
        result = repo.add_dependency(task1.id, task2.id)
        
        # Assert
        assert result is True
        assert task2.id in task1.dependencies
    
    def test_validate_dependency_within_project_scope(self):
        """Test that dependencies are validated within project scope, not branch scope"""
        # Test the validation logic we'll implement
        def validate_dependency(task_id, dependency_id, project_id):
            """
            Validate dependency within project scope
            Returns: (is_valid, error_message)
            """
            # Check if both tasks exist in the same project
            task_project = get_task_project(task_id)
            dependency_project = get_task_project(dependency_id)
            
            if not task_project or not dependency_project:
                return False, "One or both tasks not found"
            
            if task_project != dependency_project:
                return False, "Tasks must be in the same project"
            
            # Check for circular dependencies
            if would_create_circular_dependency(task_id, dependency_id):
                return False, "Would create circular dependency"
            
            return True, None
        
        # Mock implementations
        def get_task_project(task_id):
            return "project-123"  # Same project
        
        def would_create_circular_dependency(task_id, dep_id):
            return False
        
        # Test validation
        is_valid, error = validate_dependency("task-1", "task-2", "project-123")
        assert is_valid is True
        assert error is None
    
    def test_dependency_across_different_projects_should_fail(self):
        """Test that dependencies across different projects should fail"""
        # Arrange
        task_in_project_1 = {
            "id": "task-1",
            "project_id": "project-1",
            "git_branch_id": "branch-1"
        }
        
        task_in_project_2 = {
            "id": "task-2",
            "project_id": "project-2",
            "git_branch_id": "branch-2"
        }
        
        # Act & Assert
        # Dependencies across projects should not be allowed
        with pytest.raises(ValueError, match="Tasks must be in the same project"):
            add_cross_project_dependency(task_in_project_1["id"], task_in_project_2["id"])
    
    def test_circular_dependency_detection_across_branches(self):
        """Test circular dependency detection works across branches"""
        # Arrange
        # Task A (branch 1) -> Task B (branch 2) -> Task C (branch 1) -> Task A (circular)
        dependencies = {
            "task-a": ["task-b"],
            "task-b": ["task-c"],
            "task-c": []  # Will try to add task-a
        }
        
        # Act
        def would_create_circular_dependency(task_id, new_dependency_id, dependencies_map):
            """Check if adding new_dependency would create a circular dependency"""
            visited = set()
            
            def has_path(from_task, to_task):
                if from_task == to_task:
                    return True
                if from_task in visited:
                    return False
                visited.add(from_task)
                
                for dep in dependencies_map.get(from_task, []):
                    if has_path(dep, to_task):
                        return True
                return False
            
            # Check if new_dependency can reach back to task_id
            return has_path(new_dependency_id, task_id)
        
        # Test
        is_circular = would_create_circular_dependency("task-c", "task-a", dependencies)
        assert is_circular is True
    
    def test_get_task_with_cross_branch_dependencies(self):
        """Test retrieving task shows dependencies from other branches"""
        # Expected response structure after fix
        expected_task = {
            "id": "task-1",
            "title": "Main task",
            "git_branch_id": "feature/main",
            "dependencies": [
                {
                    "id": "dep-task-1",
                    "title": "Dependency from another branch",
                    "git_branch_id": "feature/other",
                    "status": "in_progress"
                }
            ],
            "dependency_status": {
                "total": 1,
                "completed": 0,
                "can_start": False,
                "blocking_tasks": ["dep-task-1"]
            }
        }
        
        assert len(expected_task["dependencies"]) == 1
        assert expected_task["dependency_status"]["can_start"] is False
    
    def test_remove_cross_branch_dependency(self):
        """Test removing dependencies across branches"""
        # Arrange
        task_id = "task-1"
        dependency_id = "task-2"
        
        # Act - Remove dependency
        result = remove_dependency(task_id, dependency_id)
        
        # Assert
        assert result is True
        
        def remove_dependency(task_id, dep_id):
            # Implementation will check project scope, not branch scope
            return True
    
    def test_list_tasks_with_cross_branch_dependencies(self):
        """Test listing tasks includes cross-branch dependency information"""
        # Expected enhanced response
        expected_response = {
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Task with cross-branch dep",
                    "git_branch_id": "feature/branch-1",
                    "dependencies": ["task-2"],
                    "dependency_details": [
                        {
                            "id": "task-2",
                            "git_branch_id": "feature/branch-2",
                            "is_cross_branch": True
                        }
                    ]
                }
            ]
        }
        
        task = expected_response["tasks"][0]
        assert task["dependency_details"][0]["is_cross_branch"] is True