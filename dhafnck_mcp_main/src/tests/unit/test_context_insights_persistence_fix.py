"""
Unit tests for verifying the fix for context insights persistence issue.

This test file verifies that:
1. Insights are properly stored in the task_data JSON field in the database
2. Insights are correctly retrieved when fetching a context
3. Insights are replaced (not extended) when updating a context
4. Progress and next_steps fields are also properly persisted
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from fastmcp.task_management.domain.entities.context import TaskContextUnified as TaskContext
from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository
from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel


class TestContextInsightsPersistenceFix(unittest.TestCase):
    """Test suite for context insights persistence fix."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.task_id = str(uuid4())
        self.branch_id = str(uuid4())
        self.project_id = str(uuid4())
        
        # Create mock session factory
        self.mock_session = Mock()
        self.mock_session_factory = Mock(return_value=self.mock_session)
        
        # Create repository with mock session factory
        self.repository = TaskContextRepository(self.mock_session_factory)
        
        # Create service with mocked repositories
        self.global_repo = Mock()
        self.project_repo = Mock()
        self.branch_repo = Mock()
        
        self.service = UnifiedContextService(
            global_context_repository=self.global_repo,
            project_context_repository=self.project_repo,
            branch_context_repository=self.branch_repo,
            task_context_repository=self.repository
        )
    
    def test_insights_stored_in_task_data_on_create(self):
        """Test that insights are stored within task_data field during create."""
        # Arrange
        insights = [
            {"content": "Found optimization opportunity", "category": "performance"},
            {"content": "Code can be refactored", "category": "quality"}
        ]
        
        task_context = TaskContext(
            id=self.task_id,
            branch_id=self.branch_id,
            task_data={"title": "Test Task"},
            progress=50,
            insights=insights,
            next_steps=["Review changes", "Deploy to staging"]
        )
        
        # Create a mock DB model
        mock_db_model = Mock()
        mock_db_model.task_id = self.task_id
        mock_db_model.parent_branch_id = self.branch_id
        mock_db_model.task_data = {}
        mock_db_model.local_overrides = {}
        mock_db_model.implementation_notes = {}
        mock_db_model.delegation_triggers = {}
        mock_db_model.inheritance_disabled = False
        mock_db_model.force_local_only = False
        mock_db_model.version = 1
        mock_db_model.created_at = datetime.now(timezone.utc)
        mock_db_model.updated_at = datetime.now(timezone.utc)
        
        # Mock session methods
        self.mock_session.get.return_value = None  # No existing context
        self.mock_session.add = Mock()
        self.mock_session.flush = Mock()
        self.mock_session.refresh = Mock(side_effect=lambda model: setattr(model, 'task_data', model.task_data))
        
        # Mock the __enter__ and __exit__ for context manager
        self.mock_session.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.__exit__ = Mock(return_value=None)
        self.mock_session.commit = Mock()
        self.mock_session.rollback = Mock()
        self.mock_session.close = Mock()
        
        # Act
        with patch.object(self.repository, '_to_entity', return_value=task_context):
            result = self.repository.create(task_context)
        
        # Assert
        # Check that add was called with a model containing insights in task_data
        self.mock_session.add.assert_called_once()
        added_model = self.mock_session.add.call_args[0][0]
        
        # Verify insights were stored in task_data
        self.assertIn('insights', added_model.task_data)
        self.assertEqual(added_model.task_data['insights'], insights)
        self.assertEqual(added_model.task_data['progress'], 50)
        self.assertEqual(added_model.task_data['next_steps'], ["Review changes", "Deploy to staging"])
    
    def test_insights_retrieved_from_task_data_on_get(self):
        """Test that insights are properly retrieved from task_data field."""
        # Arrange
        insights = [
            {"content": "Performance improved by 20%", "category": "performance"},
            {"content": "Memory usage reduced", "category": "optimization"}
        ]
        
        # Create mock DB model with insights in task_data
        mock_db_model = Mock()
        mock_db_model.task_id = self.task_id
        mock_db_model.parent_branch_id = self.branch_id
        mock_db_model.task_data = {
            "title": "Test Task",
            "insights": insights,
            "progress": 75,
            "next_steps": ["Final testing", "Documentation"]
        }
        mock_db_model.local_overrides = {}
        mock_db_model.implementation_notes = {}
        mock_db_model.delegation_triggers = {}
        mock_db_model.inheritance_disabled = False
        mock_db_model.force_local_only = False
        mock_db_model.version = 2
        mock_db_model.created_at = datetime.now(timezone.utc)
        mock_db_model.updated_at = datetime.now(timezone.utc)
        
        # Mock session methods
        self.mock_session.get.return_value = mock_db_model
        self.mock_session.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.__exit__ = Mock(return_value=None)
        self.mock_session.commit = Mock()
        self.mock_session.rollback = Mock()
        self.mock_session.close = Mock()
        
        # Act
        result = self.repository.get(self.task_id)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.insights, insights)
        self.assertEqual(result.progress, 75)
        self.assertEqual(result.next_steps, ["Final testing", "Documentation"])
        # Verify task_data doesn't contain duplicates
        self.assertNotIn('insights', result.task_data)
        self.assertNotIn('progress', result.task_data)
        self.assertNotIn('next_steps', result.task_data)
    
    def test_insights_replaced_not_extended_on_update(self):
        """Test that insights are replaced (not extended) when updating context."""
        # Arrange
        # Set up global context to satisfy hierarchy requirements
        self.global_repo.get.return_value = Mock(id="global_singleton")
        self.project_repo.get.return_value = Mock(id=self.project_id)
        self.branch_repo.get.return_value = Mock(id=self.branch_id, project_id=self.project_id)
        
        # Initial context with insights
        existing_insights = [
            {"content": "Initial insight 1", "category": "general"},
            {"content": "Initial insight 2", "category": "general"}
        ]
        
        existing_context = TaskContext(
            id=self.task_id,
            branch_id=self.branch_id,
            task_data={"title": "Test Task"},
            progress=25,
            insights=existing_insights,
            next_steps=["Step 1", "Step 2"]
        )
        
        # Mock repository to return existing context
        self.repository.get = Mock(return_value=existing_context)
        self.repository.update = Mock()
        
        # New insights to update with
        new_insights = [
            {"content": "New insight 1", "category": "performance"},
            {"content": "New insight 2", "category": "security"},
            {"content": "New insight 3", "category": "quality"}
        ]
        
        # Act
        update_result = self.service.update_context(
            level="task",
            context_id=self.task_id,
            data={
                "insights": new_insights,
                "progress": 50
            }
        )
        
        # Assert
        # Verify update was called
        self.repository.update.assert_called_once()
        
        # Get the entity passed to update
        update_args = self.repository.update.call_args[0]
        updated_entity = update_args[1]  # Second positional argument
        
        # Verify insights were replaced, not extended
        self.assertEqual(len(updated_entity.insights), 3)  # Should have 3 new insights, not 5
        self.assertEqual(updated_entity.insights, new_insights)
        self.assertEqual(updated_entity.progress, 50)
    
    def test_empty_insights_handled_correctly(self):
        """Test that empty insights array is handled correctly."""
        # Arrange
        task_context = TaskContext(
            id=self.task_id,
            branch_id=self.branch_id,
            task_data={"title": "Test Task"},
            progress=0,
            insights=[],  # Empty insights
            next_steps=[]
        )
        
        # Create mock DB model
        mock_db_model = Mock()
        mock_db_model.task_id = self.task_id
        mock_db_model.parent_branch_id = self.branch_id
        mock_db_model.task_data = {
            "title": "Test Task",
            "insights": [],
            "progress": 0,
            "next_steps": []
        }
        mock_db_model.local_overrides = {}
        mock_db_model.implementation_notes = {}
        mock_db_model.delegation_triggers = {}
        mock_db_model.inheritance_disabled = False
        mock_db_model.force_local_only = False
        mock_db_model.version = 1
        mock_db_model.created_at = datetime.now(timezone.utc)
        mock_db_model.updated_at = datetime.now(timezone.utc)
        
        # Mock session
        self.mock_session.get.return_value = mock_db_model
        self.mock_session.__enter__ = Mock(return_value=self.mock_session)
        self.mock_session.__exit__ = Mock(return_value=None)
        self.mock_session.commit = Mock()
        self.mock_session.rollback = Mock()
        self.mock_session.close = Mock()
        
        # Act
        result = self.repository.get(self.task_id)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.insights, [])
        self.assertIsInstance(result.insights, list)
    
    def test_add_insight_method_persists_correctly(self):
        """Test that add_insight method in service persists insights correctly."""
        # Arrange
        # Set up hierarchy mocks
        self.global_repo.get.return_value = Mock(id="global_singleton")
        self.project_repo.get.return_value = Mock(id=self.project_id)
        self.branch_repo.get.return_value = Mock(id=self.branch_id, project_id=self.project_id)
        
        # Existing context without insights
        existing_context = TaskContext(
            id=self.task_id,
            branch_id=self.branch_id,
            task_data={"title": "Test Task"},
            progress=0,
            insights=[],
            next_steps=[]
        )
        
        # Mock repository methods
        self.repository.get = Mock(return_value=existing_context)
        self.repository.update = Mock(return_value=existing_context)
        
        # Act
        result = self.service.add_insight(
            level="task",
            context_id=self.task_id,
            content="Important discovery about the codebase",
            category="discovery",
            importance="high",
            agent="debugger_agent"
        )
        
        # Assert
        self.assertTrue(result.get("success"))
        
        # Verify update was called
        self.repository.update.assert_called_once()
        
        # Get the entity passed to update
        update_args = self.repository.update.call_args[0]
        updated_entity = update_args[1]  # Second positional argument
        
        # Verify insight was added
        self.assertEqual(len(updated_entity.insights), 1)
        self.assertEqual(updated_entity.insights[0]['content'], "Important discovery about the codebase")
        self.assertEqual(updated_entity.insights[0]['category'], "discovery")
        self.assertEqual(updated_entity.insights[0]['importance'], "high")
        self.assertEqual(updated_entity.insights[0]['agent'], "debugger_agent")
        self.assertIn('timestamp', updated_entity.insights[0])


if __name__ == '__main__':
    unittest.main()