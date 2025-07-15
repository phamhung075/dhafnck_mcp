"""Test suite for flexible label system"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects import TaskId, TaskStatus, Priority
from fastmcp.task_management.domain.repositories.label_repository import ILabelRepository
from fastmcp.task_management.infrastructure.repositories.sqlite.label_repository import SQLiteLabelRepository

pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests


class TestFlexibleLabels:
    """Test flexible label system with Task entity"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.task_id = TaskId.generate_new()
        self.task = Task.create(
            id=self.task_id,
            title="Test Task",
            description="Test Description",
            git_branch_id="test-branch"
        )
    
    def test_task_accepts_any_valid_labels(self):
        """Task should accept any non-empty labels up to 50 chars"""
        # Test various label formats
        labels = [
            "custom-label",
            "My Custom Label",  # Will be kept as-is in task
            "platform",
            "enterprise",
            "ai-orchestration",
            "multi-tier",
            "production",
            "UPPERCASE",
            "CamelCase",
            "with spaces",
            "with-hyphens",
            "with_underscores",
            "with/slashes",
            "123numeric",
            "a" * 50  # Max length
        ]
        
        # Update labels
        self.task.update_labels(labels)
        
        # All should be accepted
        assert len(self.task.labels) == len(labels)
        for label in labels:
            assert label in self.task.labels
    
    def test_task_rejects_invalid_labels(self):
        """Task should reject empty or too long labels"""
        invalid_labels = [
            "",  # Empty
            "   ",  # Whitespace only
            "a" * 51,  # Too long
            None,  # None type
            123,  # Not a string
        ]
        
        # Update with mix of valid and invalid
        mixed_labels = ["valid-label"] + invalid_labels
        self.task.update_labels(mixed_labels)
        
        # Only valid label should be kept
        assert len(self.task.labels) == 1
        assert self.task.labels[0] == "valid-label"
    
    def test_task_preserves_label_case(self):
        """Task entity preserves original label case"""
        labels = ["Frontend", "BackEnd", "UI/UX", "DevOps"]
        self.task.update_labels(labels)
        
        # Original case preserved in task
        assert self.task.labels == labels
    
    def test_add_label_method(self):
        """Test add_label method works with flexible labels"""
        # Add various labels
        self.task.add_label("custom-label-1")
        self.task.add_label("Custom Label 2")
        self.task.add_label("CUSTOM-LABEL-3")
        
        assert len(self.task.labels) == 3
        assert "custom-label-1" in self.task.labels
        assert "Custom Label 2" in self.task.labels
        assert "CUSTOM-LABEL-3" in self.task.labels
        
        # Duplicate should not be added
        self.task.add_label("custom-label-1")
        assert len(self.task.labels) == 3
    
    def test_remove_label_method(self):
        """Test remove_label method"""
        labels = ["label1", "label2", "label3"]
        self.task.update_labels(labels)
        
        # Remove one
        self.task.remove_label("label2")
        assert len(self.task.labels) == 2
        assert "label2" not in self.task.labels
        assert "label1" in self.task.labels
        assert "label3" in self.task.labels
    
    def test_empty_labels_list(self):
        """Test handling of empty labels list"""
        self.task.update_labels([])
        assert self.task.labels == []
        
        # Add some then clear
        self.task.update_labels(["label1", "label2"])
        assert len(self.task.labels) == 2
        
        self.task.update_labels([])
        assert self.task.labels == []
    
    def test_label_update_triggers_event(self):
        """Test that label updates trigger domain events"""
        # Clear any existing events
        self.task.get_events()
        
        # Update labels
        old_labels = ["old-label"]
        new_labels = ["new-label-1", "new-label-2"]
        
        self.task.update_labels(old_labels)
        self.task.get_events()  # Clear
        
        self.task.update_labels(new_labels)
        
        # Check event
        events = self.task.get_events()
        assert len(events) == 1
        assert events[0].field_name == "labels"
        assert events[0].old_value == old_labels
        assert events[0].new_value == new_labels


class TestLabelNormalization:
    """Test label normalization in repository"""
    
    def test_normalize_label(self):
        """Test label normalization rules"""
        repo = SQLiteLabelRepository(":memory:")
        
        test_cases = [
            # (input, expected)
            ("Simple Label", "simple-label"),
            ("  Spaces Around  ", "spaces-around"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("UPPERCASE", "uppercase"),
            ("CamelCase", "camelcase"),
            ("with-hyphens", "with-hyphens"),
            ("with_underscores", "with_underscores"),
            ("with/slashes", "with/slashes"),
            ("special!@#$%chars", "specialchars"),
            ("multiple---hyphens", "multiple-hyphens"),
            ("--leading-trailing--", "leading-trailing"),
            ("123numeric", "123numeric"),
            ("", ""),  # Empty stays empty
        ]
        
        for input_label, expected in test_cases:
            normalized = repo._normalize_label(input_label)
            assert normalized == expected, f"Failed for '{input_label}': got '{normalized}', expected '{expected}'"


@pytest.mark.asyncio
class TestLabelRepository:
    """Test label repository functionality"""
    
    async def test_create_label(self):
        """Test creating new labels"""
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            initialize_database(db_path)
            repo = SQLiteLabelRepository(db_path)
        
            # Create custom label
            label = await repo.create_label("My Custom Label", "custom")
            assert label == "My Custom Label"
        
            # Verify it was stored with normalized key
            found = await repo.find_label("my custom label")  # Different case
            assert found == "My Custom Label"  # Returns original
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_prevent_duplicates(self):
        """Test that duplicate labels are not created"""
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            initialize_database(db_path)
            repo = SQLiteLabelRepository(db_path)
        
            # Create label
            await repo.create_label("Test Label")
        
            # Try to create again with different case
            label2 = await repo.create_label("test label")
            assert label2 == "Test Label"  # Returns existing
        
            # Try with different spacing
            label3 = await repo.create_label("Test  Label")
            assert label3 == "Test Label"  # Returns existing
        
            # Verify only one exists
            all_labels = await repo.get_all_labels()
            test_labels = [l for l in all_labels if "test" in l.lower() and "label" in l.lower()]
            assert len(test_labels) == 1
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_search_labels(self):
        """Test label search functionality"""
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            initialize_database(db_path)
            repo = SQLiteLabelRepository(db_path)
        
            # Create some labels
            labels = [
                "frontend-feature",
                "backend-api",
                "frontend-bug",
                "database-migration",
                "frontend-enhancement"
            ]
        
            for label in labels:
                await repo.create_label(label)
        
            # Search for frontend
            results = await repo.search_labels("frontend", limit=5)
            # Should find 3 frontend labels plus the pre-initialized "frontend" common label
            assert len(results) >= 3
            assert all("frontend" in r for r in results)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_label_categories(self):
        """Test label categorization"""
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            initialize_database(db_path)
            repo = SQLiteLabelRepository(db_path)
        
            # Create labels in different categories
            await repo.create_label("high-priority", "priority")
            await repo.create_label("new-feature", "type")
            await repo.create_label("ui-component", "component")
            await repo.create_label("my-custom", "custom")
        
            # Get by category
            priority_labels = await repo.get_labels_by_category("priority")
            assert "high-priority" in priority_labels
        
            type_labels = await repo.get_labels_by_category("type")
            assert "new-feature" in type_labels
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_validate_and_create_multiple(self):
        """Test validating and creating multiple labels"""
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            initialize_database(db_path)
            repo = SQLiteLabelRepository(db_path)
        
            input_labels = [
                "Label 1",
                "label-1",  # Duplicate when normalized
                "Label 2",
                "",  # Invalid
                "Label 3",
                None,  # Invalid
                "a" * 60,  # Too long
                "Label 2"  # Duplicate
            ]
        
            result = await repo.validate_and_create_labels(input_labels)
        
            # Should have 3 unique valid labels
            assert len(result) == 3
            assert "Label 1" in result
            assert "Label 2" in result
            assert "Label 3" in result
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_common_labels_initialized(self):
        """Test that common labels are pre-initialized"""
        # For unit tests, we need to explicitly initialize the database
        from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
        import tempfile
        import os
        
        # Use a temporary file database for this test to ensure persistence across connections
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Initialize the database schema
            initialize_database(db_path)
            
            # Now create the repository which will use the initialized database
            repo = SQLiteLabelRepository(db_path)
            
            # Check some common labels exist
            common_labels = ["bug", "feature", "enhancement", "frontend", "backend"]
            
            for label in common_labels:
                found = await repo.find_label(label)
                assert found is not None, f"Label '{label}' should be initialized but was not found"
                assert found == label  # Common labels use lowercase
        finally:
            # Clean up the temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_usage_tracking(self):
        """Test label usage count tracking"""
        import tempfile
        import os
        
        # Create a truly isolated database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            repo = SQLiteLabelRepository(db_path)
            
            # Clear any existing labels to ensure clean state
            with repo._get_connection() as conn:
                conn.execute("DELETE FROM labels")
                conn.commit()
            
            # Create label (starts with usage_count=1)
            await repo.create_label("tracked-label")
            
            # Use it again (increments to 2)
            await repo.create_label("tracked-label")
            
            # Check usage count
            count = await repo.get_label_usage_count("tracked-label")
            assert count == 2
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_popular_labels(self):
        """Test getting popular labels"""
        import tempfile
        import os
        
        # Create a truly isolated database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            repo = SQLiteLabelRepository(db_path)
            
            # Clear any existing labels to ensure clean state
            with repo._get_connection() as conn:
                conn.execute("DELETE FROM labels")
                conn.commit()
            
            # Create labels with different usage
            for i in range(5):
                await repo.create_label("popular-label")
            
            for i in range(3):
                await repo.create_label("medium-label")
            
            await repo.create_label("rare-label")
            
            # Get popular labels
            popular = await repo.get_popular_labels(limit=2)
            assert len(popular) == 2  # Should get exactly 2
            
            # Most popular should be first
            assert popular[0]["label"] == "popular-label"
            assert popular[0]["usage_count"] == 5
            
            # Second should be medium-label
            assert popular[1]["label"] == "medium-label"
            assert popular[1]["usage_count"] == 3
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestTaskWithLabelRepository:
    """Test task integration with label repository"""
    
    @pytest.mark.asyncio
    async def test_task_labels_with_repository(self):
        """Test that task labels work with repository normalization"""
        # This would be an integration test with actual repository
        # For now, we just verify the task accepts the labels
        
        task = Task.create(
            id=TaskId.generate_new(),
            title="Test Task",
            description="Test Description"
        )
        
        # These would be created/normalized by repository
        labels_from_user = ["Frontend Feature", "High Priority", "In Review"]
        
        # Task stores them as provided
        task.update_labels(labels_from_user)
        assert task.labels == labels_from_user
        
        # Repository would handle normalization on save
        # "Frontend Feature" -> "frontend-feature" (in repository)
        # But task keeps original for display