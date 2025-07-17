"""
Real-world integration test for task completion with multiple subtasks and context validation.

This test ensures that:
1. Tasks cannot be completed if any subtasks are incomplete
2. Tasks cannot be completed if context is not updated (context_id is None)
3. Tasks can only be completed when ALL subtasks are done AND context is updated
4. The integration between subtask management and context management works correctly

This reflects real-world scenarios where tasks have multiple subtasks and context requirements.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.services.task_completion_service import TaskCompletionService
from fastmcp.task_management.domain.exceptions.task_exceptions import TaskCompletionError
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade


class TestRealTaskWithMultiSubtasksIntegration:
    """Integration test suite for real-world task completion scenarios"""
    
    def setup_method(self):
        """Setup comprehensive test environment"""
        self.task_id = "aaaaaaaa-1111-4444-8888-111111111111"
        self.project_id = "integration_test_project"
        self.git_branch = "test_branch"
        self.user_id = "test_user"
        
        # Mock repositories
        self.mock_task_repository = Mock()
        self.mock_subtask_repository = Mock()
        self.mock_context_service = Mock()  # Use hierarchical context service
        
        # Create task completion service
        self.completion_service = TaskCompletionService(self.mock_subtask_repository)
        
        # Create test task WITHOUT context (real-world scenario)
        self.test_task = Task(
            id=TaskId(self.task_id),
            title="Real World Task with Multiple Subtasks",
            description="This task simulates a real-world scenario with multiple subtasks",
            status=TaskStatus.in_progress(),
            priority=Priority.high(),
            context_id=None  # Initially no context - real scenario
        )
        
        # Create multiple subtasks with different states
        self.subtasks = self._create_test_subtasks()
        
    def teardown_method(self):
        """Clean up after each test"""
        self.mock_task_repository.reset_mock()
        self.mock_subtask_repository.reset_mock()
        self.mock_context_service.reset_mock()
        
    def _create_test_subtasks(self):
        """Create realistic subtasks for testing"""
        return [
            Subtask(
                id="SUB-001",
                title="Design System Architecture",
                description="Design the overall system architecture",
                parent_task_id=self.task_id,
                status=TaskStatus.done()
            ),
            Subtask(
                id="SUB-002", 
                title="Implement Core Features",
                description="Implement the main functionality",
                parent_task_id=self.task_id,
                status=TaskStatus.in_progress()
            ),
            Subtask(
                id="SUB-003",
                title="Write Unit Tests",
                description="Write comprehensive unit tests",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="SUB-004",
                title="Integration Testing",
                description="Perform integration testing",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="SUB-005",
                title="Documentation",
                description="Create documentation",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            )
        ]
    
    def test_task_cannot_complete_with_incomplete_subtasks_and_no_context(self):
        """Test: Task fails completion when subtasks are incomplete AND no context"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.return_value = self.subtasks
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is False
        assert "Task completion requires context to be created first" in error_message
        # Should also mention incomplete subtasks
        assert "4 of 5 subtasks are incomplete" in error_message
        
        # Verify blocker details
        blockers = self.completion_service.get_completion_blockers(self.test_task)
        assert len(blockers) == 2  # Context + subtasks
        
        context_blocker = [b for b in blockers if "Task completion requires context" in b][0]
        assert "Task completion requires context to be created first" in context_blocker
        
        subtask_blocker = [b for b in blockers if "subtasks are incomplete" in b][0]
        assert "Implement Core Features" in subtask_blocker
        assert "Write Unit Tests" in subtask_blocker
        
    def test_task_cannot_complete_with_context_but_incomplete_subtasks(self):
        """Test: Task fails completion when context is set but subtasks are incomplete"""
        # Arrange
        self.test_task.context_id = "test_context_123"  # Set context
        self.mock_subtask_repository.find_by_parent_task_id.return_value = self.subtasks
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is False
        assert "Cannot complete task: 4 of 5 subtasks are incomplete" in error_message
        assert "Task completion requires context" not in error_message  # Context is OK
        
        # Should list incomplete subtasks
        assert "Implement Core Features" in error_message
        assert "Write Unit Tests" in error_message
        assert "Integration Testing" in error_message
        
    def test_task_cannot_complete_with_all_subtasks_done_but_no_context(self):
        """Test: Task fails completion when all subtasks are done but no context"""
        # Arrange
        completed_subtasks = [self._complete_subtask(st) for st in self.subtasks]
        self.mock_subtask_repository.find_by_parent_task_id.return_value = completed_subtasks
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is False
        assert "Task completion requires context to be created first" in error_message
        # Should NOT mention subtasks as they're all done
        assert "subtasks are incomplete" not in error_message
        
    def test_task_can_complete_only_when_all_subtasks_done_and_context_updated(self):
        """Test: Task succeeds completion ONLY when ALL subtasks are done AND context is updated"""
        # Arrange
        completed_subtasks = [self._complete_subtask(st) for st in self.subtasks]
        self.mock_subtask_repository.find_by_parent_task_id.return_value = completed_subtasks
        self.test_task.context_id = "test_context_123"  # Set context
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is True
        assert error_message is None
        
        # Verify completion summary
        summary = self.completion_service.get_subtask_completion_summary(self.test_task)
        assert summary["total"] == 5
        assert summary["completed"] == 5
        assert summary["incomplete"] == 0
        assert summary["completion_percentage"] == 100
        assert summary["can_complete_parent"] is True
        
    def test_progressive_subtask_completion_workflow(self):
        """Test: Progressive workflow where subtasks are completed one by one"""
        # Start with all subtasks incomplete, no context
        self.mock_subtask_repository.find_by_parent_task_id.return_value = self.subtasks
        
        # Step 1: Cannot complete with incomplete subtasks and no context
        can_complete, error = self.completion_service.can_complete_task(self.test_task)
        assert can_complete is False
        assert "4 of 5 subtasks are incomplete" in error
        assert "Task completion requires context to be created first" in error
        
        # Step 2: Complete first subtask - still cannot complete
        self.subtasks[1] = self._complete_subtask(self.subtasks[1])  # Complete "Implement Core Features"
        can_complete, error = self.completion_service.can_complete_task(self.test_task)
        assert can_complete is False
        assert "3 of 5 subtasks are incomplete" in error
        
        # Step 3: Complete all subtasks but no context - still cannot complete
        completed_subtasks = [self._complete_subtask(st) for st in self.subtasks]
        self.mock_subtask_repository.find_by_parent_task_id.return_value = completed_subtasks
        can_complete, error = self.completion_service.can_complete_task(self.test_task)
        assert can_complete is False
        assert "Task completion requires context to be created first" in error
        assert "subtasks are incomplete" not in error
        
        # Step 4: Add context - now can complete
        self.test_task.context_id = "final_context_123"
        can_complete, error = self.completion_service.can_complete_task(self.test_task)
        assert can_complete is True
        assert error is None
        
    def test_real_world_error_messages_are_helpful(self):
        """Test: Error messages provide helpful guidance for real-world scenarios"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.return_value = self.subtasks
        
        # Act
        blockers = self.completion_service.get_completion_blockers(self.test_task)
        
        # Assert
        assert len(blockers) == 2
        
        # Context blocker should be helpful
        context_blocker = [b for b in blockers if "Task completion requires context" in b][0]
        # The new error message should provide recovery instructions
        assert "Task completion requires context to be created first" in context_blocker
        
        # Subtask blocker should list specific incomplete subtasks
        subtask_blocker = [b for b in blockers if "subtasks are incomplete" in b][0]
        assert "4 of 5 subtasks are incomplete" in subtask_blocker
        assert "Implement Core Features" in subtask_blocker
        assert "Write Unit Tests" in subtask_blocker
        assert "Integration Testing" in subtask_blocker
        assert "Complete all subtasks first" in subtask_blocker
        
    def test_completion_service_validate_method_with_comprehensive_scenario(self):
        """Test: validate_task_completion method with comprehensive real-world scenario"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.return_value = self.subtasks
        
        # Act & Assert
        with pytest.raises(TaskCompletionError) as exc_info:
            self.completion_service.validate_task_completion(self.test_task)
        
        # Should mention both issues
        error_msg = str(exc_info.value)
        assert "Task completion requires context to be created first" in error_msg
        assert "4 of 5 subtasks are incomplete" in error_msg
        
    def test_large_number_of_subtasks_handling(self):
        """Test: Service handles large numbers of subtasks gracefully"""
        # Arrange
        large_subtask_list = []
        for i in range(20):
            status = TaskStatus.done() if i < 5 else TaskStatus.todo()  # 5 done, 15 incomplete
            large_subtask_list.append(Subtask(
                id=f"SUB-{i:03d}",
                title=f"Large Subtask {i}",
                description=f"Description for subtask {i}",
                parent_task_id=self.task_id,
                status=status
            ))
        
        self.mock_subtask_repository.find_by_parent_task_id.return_value = large_subtask_list
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is False
        assert "Cannot complete task: 15 of 20 subtasks are incomplete" in error_message
        # Should show first few and indicate there are more
        assert "Large Subtask 5" in error_message
        assert "Large Subtask 6" in error_message
        assert "Large Subtask 7" in error_message
        assert "and 12 more" in error_message
        
    def test_edge_case_empty_subtask_list_with_context(self):
        """Test: Task with no subtasks but with context can complete"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.return_value = []
        self.test_task.context_id = "context_123"
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is True
        assert error_message is None
        
    def test_edge_case_empty_subtask_list_without_context(self):
        """Test: Task with no subtasks but no context cannot complete"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.return_value = []
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is False
        assert "Task completion requires context to be created first" in error_message
        
    def test_repository_error_handling_in_real_scenario(self):
        """Test: Service handles repository errors gracefully in real scenarios"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.side_effect = Exception("Database connection failed")
        
        # Act
        can_complete, error_message = self.completion_service.can_complete_task(self.test_task)
        
        # Assert
        assert can_complete is False
        assert "Internal error validating task completion" in error_message
        assert "Database connection failed" in error_message
        
    def test_subtask_completion_summary_comprehensive(self):
        """Test: Comprehensive subtask completion summary"""
        # Arrange
        self.mock_subtask_repository.find_by_parent_task_id.return_value = self.subtasks
        
        # Act
        summary = self.completion_service.get_subtask_completion_summary(self.test_task)
        
        # Assert
        assert summary["total"] == 5
        assert summary["completed"] == 1  # Only first subtask is done
        assert summary["incomplete"] == 4
        assert summary["completion_percentage"] == 20  # 1/5 = 20%
        assert summary["can_complete_parent"] is False
        
        # Verify incomplete subtasks are listed
        incomplete_subtasks = [st for st in self.subtasks if not st.status.is_completed()]
        assert len(incomplete_subtasks) == 4
        
    def _complete_subtask(self, subtask: Subtask) -> Subtask:
        """Helper method to mark a subtask as completed"""
        return Subtask(
            id=subtask.id,
            title=subtask.title,
            description=subtask.description,
            parent_task_id=subtask.parent_task_id,
            status=TaskStatus.done()
        )


class TestRealWorldWorkflowIntegration:
    """Integration tests for real-world workflow scenarios"""
    
    def setup_method(self):
        """Setup for workflow integration tests"""
        self.task_id = "bbbbbbbb-2222-4444-8888-222222222222"
        self.project_id = "workflow_test_project"
        self.git_branch = "main"
        self.user_id = "workflow_user"
        
    def test_typical_software_development_task_workflow(self):
        """Test: Typical software development task with multiple phases"""
        # This test simulates a real software development task
        
        # Task: "Implement User Authentication Feature"
        task = Task(
            id=TaskId(self.task_id),
            title="Implement User Authentication Feature",
            description="Add complete user authentication system",
            status=TaskStatus.in_progress(),
            priority=Priority.high(),
            context_id=None  # No context initially
        )
        
        # Subtasks representing typical development phases
        development_subtasks = [
            Subtask(
                id="AUTH-001",
                title="Design Authentication API",
                description="Design REST API endpoints for authentication",
                parent_task_id=self.task_id,
                status=TaskStatus.done()
            ),
            Subtask(
                id="AUTH-002",
                title="Implement JWT Token System",
                description="Implement JWT token generation and validation",
                parent_task_id=self.task_id,
                status=TaskStatus.done()
            ),
            Subtask(
                id="AUTH-003",
                title="Create User Registration",
                description="Implement user registration functionality",
                parent_task_id=self.task_id,
                status=TaskStatus.in_progress()
            ),
            Subtask(
                id="AUTH-004",
                title="Implement Login/Logout",
                description="Implement user login and logout functionality",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="AUTH-005",
                title="Add Password Reset",
                description="Implement password reset functionality",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="AUTH-006",
                title="Write Integration Tests",
                description="Write comprehensive integration tests",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="AUTH-007",
                title="Update Documentation",
                description="Update API documentation",
                parent_task_id=self.task_id,
                status=TaskStatus.todo()
            )
        ]
        
        # Mock repository
        mock_repository = Mock()
        mock_repository.find_by_parent_task_id.return_value = development_subtasks
        
        # Create completion service
        completion_service = TaskCompletionService(mock_repository)
        
        # Phase 1: Task cannot complete - incomplete subtasks, no context
        can_complete, error = completion_service.can_complete_task(task)
        assert can_complete is False
        assert "5 of 7 subtasks are incomplete" in error
        assert "Task completion requires context to be created first" in error
        
        # Phase 2: Complete more subtasks but still no context
        development_subtasks[2].status = TaskStatus.done()
        development_subtasks[3].status = TaskStatus.done()
        
        can_complete, error = completion_service.can_complete_task(task)
        assert can_complete is False
        assert "3 of 7 subtasks are incomplete" in error
        assert "Task completion requires context to be created first" in error
        
        # Phase 3: Complete all subtasks but no context
        for subtask in development_subtasks:
            subtask.status = TaskStatus.done()
            
        can_complete, error = completion_service.can_complete_task(task)
        assert can_complete is False
        assert "Task completion requires context to be created first" in error
        assert "subtasks are incomplete" not in error
        
        # Phase 4: Add context - now ready for completion
        task.context_id = "auth_feature_complete_context"
        can_complete, error = completion_service.can_complete_task(task)
        assert can_complete is True
        assert error is None
        
        # Final verification
        summary = completion_service.get_subtask_completion_summary(task)
        assert summary["total"] == 7
        assert summary["completed"] == 7
        assert summary["completion_percentage"] == 100
        assert summary["can_complete_parent"] is True
        
    def test_content_creation_task_workflow(self):
        """Test: Content creation task with typical content phases"""
        # Task: "Create Product Launch Blog Post"
        task = Task(
            id=TaskId("cccccccc-3333-4444-8888-333333333333"),
            title="Create Product Launch Blog Post",
            description="Write comprehensive blog post for product launch",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            context_id=None
        )
        
        # Content creation subtasks
        content_subtasks = [
            Subtask(
                id="BLOG-001",
                title="Research Competition",
                description="Research competitor products and messaging",
                parent_task_id=task.id.value,
                status=TaskStatus.done()
            ),
            Subtask(
                id="BLOG-002",
                title="Create Content Outline",
                description="Create detailed outline for blog post",
                parent_task_id=task.id.value,
                status=TaskStatus.done()
            ),
            Subtask(
                id="BLOG-003",
                title="Write First Draft",
                description="Write initial draft of blog post",
                parent_task_id=task.id.value,
                status=TaskStatus.in_progress()
            ),
            Subtask(
                id="BLOG-004",
                title="Review and Edit",
                description="Review and edit content for clarity",
                parent_task_id=task.id.value,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="BLOG-005",
                title="SEO Optimization",
                description="Optimize content for search engines",
                parent_task_id=task.id.value,
                status=TaskStatus.todo()
            ),
            Subtask(
                id="BLOG-006",
                title="Final Review",
                description="Final review and approval",
                parent_task_id=task.id.value,
                status=TaskStatus.todo()
            )
        ]
        
        mock_repository = Mock()
        mock_repository.find_by_parent_task_id.return_value = content_subtasks
        completion_service = TaskCompletionService(mock_repository)
        
        # Verify progressive completion workflow
        can_complete, error = completion_service.can_complete_task(task)
        assert can_complete is False
        assert "4 of 6 subtasks are incomplete" in error
        assert "Task completion requires context to be created first" in error
        
        # Complete all subtasks and add context
        for subtask in content_subtasks:
            subtask.status = TaskStatus.done()
            
        task.context_id = "blog_post_ready_for_publish"
        
        can_complete, error = completion_service.can_complete_task(task)
        assert can_complete is True
        assert error is None


if __name__ == "__main__":
    print("🧪 Running Real Task with Multi-Subtasks Integration Tests...")
    pytest.main([__file__, "-v"])
    print("✅ Integration Tests Complete!")