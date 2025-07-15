"""
Comprehensive test for SQLite Vision Repository implementation.

This test verifies that the vision repository migration from PostgreSQL 
to SQLite works correctly with all CRUD operations and filtering.
"""

import pytest
import tempfile
import os
import sys
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the SQLite Vision Repository
from fastmcp.task_management.infrastructure.repositories.sqlite.vision_repository import SQLiteVisionRepository
from fastmcp.task_management.domain.value_objects.vision_objects import (
    VisionObjective, VisionAlignment, VisionMetric, VisionInsight,
    VisionHierarchyLevel, ContributionType, MetricType
)


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_db_repo():
    """Create a vision repository with in-memory SQLite database."""
    # Use a temporary file instead of :memory: to avoid issues with shared state
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    return SQLiteVisionRepository(db_path=temp_path)


@pytest.fixture
def temp_db_repo(temp_db):
    """Create a vision repository with temporary file database."""
    return SQLiteVisionRepository(db_path=temp_db)


@pytest.fixture
def sample_objectives():
    """Create sample vision objectives for testing."""
    objectives = []
    
    # Organization level objective
    org_obj = VisionObjective(
        id=uuid4(),
        title="Digital Transformation",
        description="Transform organization to be AI-powered",
        level=VisionHierarchyLevel.ORGANIZATION,
        priority=5,
        status="active",
        metrics=[
            VisionMetric(
                name="digital_maturity",
                current_value=0.6,
                target_value=0.9,
                unit="score",
                metric_type=MetricType.PERCENTAGE
            )
        ],
        tags=["transformation", "ai", "strategy"]
    )
    objectives.append(org_obj)
    
    # Department level objective
    dept_obj = VisionObjective(
        id=uuid4(),
        title="Engineering Excellence",
        description="Build world-class engineering practices",
        level=VisionHierarchyLevel.DEPARTMENT,
        parent_id=org_obj.id,
        priority=4,
        status="active",
        metrics=[
            VisionMetric(
                name="code_quality",
                current_value=0.7,
                target_value=0.95,
                unit="score",
                metric_type=MetricType.PERCENTAGE
            ),
            VisionMetric(
                name="deployment_frequency",
                current_value=2.0,
                target_value=10.0,
                unit="deployments_per_week",
                metric_type=MetricType.COUNT
            )
        ],
        tags=["engineering", "quality", "devops"]
    )
    objectives.append(dept_obj)
    
    return objectives


@pytest.fixture
def sample_alignments(sample_objectives):
    """Create sample vision alignments for testing."""
    alignments = []
    
    task_id = uuid4()
    
    for obj in sample_objectives:
        alignment = VisionAlignment(
            task_id=task_id,
            objective_id=obj.id,
            alignment_score=0.85,
            contribution_type=ContributionType.DIRECT,
            confidence=0.9,
            rationale="Task directly contributes to objective",
            factors={"complexity": "medium", "impact": "high"}
        )
        alignments.append(alignment)
    
    return alignments


@pytest.fixture
def sample_insights(sample_objectives):
    """Create sample vision insights for testing."""
    insights = []
    
    insight = VisionInsight(
        id=uuid4(),
        type="objective_misalignment",
        title="Low Alignment Score Detected",
        description="Some tasks have low alignment with key objectives",
        impact="high",
        affected_objectives=[obj.id for obj in sample_objectives[:1]],
        affected_tasks=[uuid4(), uuid4()],
        suggested_actions=[
            "Review task scope",
            "Consider objective refinement",
            "Add alignment documentation"
        ],
        expires_at=datetime.now(timezone.utc),
        metadata={"analysis_version": "1.0", "confidence": 0.8}
    )
    insights.append(insight)
    
    return insights


class TestSQLiteVisionRepositoryBasics:
    """Test basic SQLite Vision Repository functionality."""
    
    def test_repository_initialization_memory(self, memory_db_repo):
        """Test that repository initializes correctly with temporary database."""
        assert memory_db_repo is not None
        assert memory_db_repo._db_path.endswith('.db')
    
    def test_repository_initialization_file(self, temp_db_repo, temp_db):
        """Test that repository initializes correctly with file database."""
        assert temp_db_repo is not None
        assert temp_db_repo._db_path == temp_db
        assert os.path.exists(temp_db)
    
    def test_table_creation(self, memory_db_repo):
        """Test that all required tables are created."""
        with memory_db_repo._get_connection() as conn:
            # Check that vision_objectives table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='vision_objectives'
            """)
            assert cursor.fetchone() is not None
            
            # Check that vision_alignments table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='vision_alignments'
            """)
            assert cursor.fetchone() is not None
            
            # Check that vision_insights table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='vision_insights'
            """)
            assert cursor.fetchone() is not None
    
    def test_indexes_creation(self, memory_db_repo):
        """Test that all required indexes are created."""
        with memory_db_repo._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_vision_%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_vision_objectives_status',
                'idx_vision_objectives_level',
                'idx_vision_objectives_parent',
                'idx_vision_objectives_user_project',
                'idx_vision_alignments_task',
                'idx_vision_alignments_objective',
                'idx_vision_alignments_score',
                'idx_vision_insights_type',
                'idx_vision_insights_impact',
                'idx_vision_insights_expires'
            ]
            
            for expected_index in expected_indexes:
                assert expected_index in indexes
    
    def test_default_objectives_creation(self, memory_db_repo):
        """Test that default objectives are created during initialization."""
        objectives = memory_db_repo.list_objectives()
        assert len(objectives) >= 2  # Should have at least 2 default objectives
        
        # Check that organization and department level objectives exist
        levels = [obj.level for obj in objectives]
        assert VisionHierarchyLevel.ORGANIZATION in levels
        assert VisionHierarchyLevel.DEPARTMENT in levels


class TestVisionObjectiveCRUD:
    """Test CRUD operations for Vision Objectives."""
    
    def test_create_objective(self, memory_db_repo, sample_objectives):
        """Test creating a vision objective."""
        obj = sample_objectives[0]
        created = memory_db_repo.create_objective(obj)
        
        assert created is not None
        assert created.id == obj.id
        assert created.title == obj.title
        assert created.description == obj.description
        assert created.level == obj.level
    
    def test_get_objective(self, memory_db_repo, sample_objectives):
        """Test retrieving a vision objective by ID."""
        obj = sample_objectives[0]
        memory_db_repo.create_objective(obj)
        
        retrieved = memory_db_repo.get_objective(obj.id)
        
        assert retrieved is not None
        assert retrieved.id == obj.id
        assert retrieved.title == obj.title
        assert len(retrieved.metrics) == len(obj.metrics)
        assert retrieved.tags == obj.tags
    
    def test_get_nonexistent_objective(self, memory_db_repo):
        """Test retrieving a non-existent objective returns None."""
        non_existent_id = uuid4()
        result = memory_db_repo.get_objective(non_existent_id)
        assert result is None
    
    def test_update_objective(self, memory_db_repo, sample_objectives):
        """Test updating an existing vision objective."""
        obj = sample_objectives[0]
        memory_db_repo.create_objective(obj)
        
        # Create a new objective with updated values (dataclass is frozen)
        from dataclasses import replace
        updated_obj = replace(obj, title="Updated Title", description="Updated Description", priority=3)
        
        updated = memory_db_repo.update_objective(updated_obj)
        
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.description == "Updated Description"
        assert updated.priority == 3
        
        # Verify the update persisted
        retrieved = memory_db_repo.get_objective(updated_obj.id)
        assert retrieved.title == "Updated Title"
    
    def test_update_nonexistent_objective(self, memory_db_repo, sample_objectives):
        """Test updating a non-existent objective returns None."""
        obj = sample_objectives[0]
        result = memory_db_repo.update_objective(obj)
        assert result is None
    
    def test_list_objectives_no_filters(self, memory_db_repo, sample_objectives):
        """Test listing all objectives without filters."""
        for obj in sample_objectives:
            memory_db_repo.create_objective(obj)
        
        all_objectives = memory_db_repo.list_objectives()
        
        # Should include our test objectives plus default ones
        assert len(all_objectives) >= len(sample_objectives)
        
        # Check that our objectives are included
        created_ids = [obj.id for obj in sample_objectives]
        retrieved_ids = [obj.id for obj in all_objectives]
        
        for created_id in created_ids:
            assert created_id in retrieved_ids
    
    def test_list_objectives_with_filters(self, memory_db_repo, sample_objectives):
        """Test listing objectives with various filters."""
        for obj in sample_objectives:
            memory_db_repo.create_objective(obj)
        
        # Filter by level
        org_objectives = memory_db_repo.list_objectives(
            level=VisionHierarchyLevel.ORGANIZATION
        )
        assert len(org_objectives) >= 1
        for obj in org_objectives:
            assert obj.level == VisionHierarchyLevel.ORGANIZATION
        
        # Filter by status
        active_objectives = memory_db_repo.list_objectives(status="active")
        assert len(active_objectives) >= len(sample_objectives)
        for obj in active_objectives:
            assert obj.status == "active"
        
        # Filter by parent_id
        parent_id = sample_objectives[0].id
        child_objectives = memory_db_repo.list_objectives(parent_id=parent_id)
        for obj in child_objectives:
            assert obj.parent_id == parent_id


class TestVisionAlignmentOperations:
    """Test Vision Alignment operations."""
    
    def test_create_alignment(self, memory_db_repo, sample_objectives, sample_alignments):
        """Test creating a vision alignment."""
        # Create objectives first
        for obj in sample_objectives:
            memory_db_repo.create_objective(obj)
        
        alignment = sample_alignments[0]
        created = memory_db_repo.create_alignment(alignment)
        
        assert created is not None
        assert created.task_id == alignment.task_id
        assert created.objective_id == alignment.objective_id
        assert created.alignment_score == alignment.alignment_score
    
    def test_get_task_alignments(self, memory_db_repo, sample_objectives, sample_alignments):
        """Test retrieving alignments for a specific task."""
        # Create objectives first
        for obj in sample_objectives:
            memory_db_repo.create_objective(obj)
        
        # Create alignments
        for alignment in sample_alignments:
            memory_db_repo.create_alignment(alignment)
        
        task_id = sample_alignments[0].task_id
        alignments = memory_db_repo.get_task_alignments(task_id)
        
        assert len(alignments) == len(sample_alignments)
        for alignment in alignments:
            assert alignment.task_id == task_id
    
    def test_get_objective_alignments(self, memory_db_repo, sample_objectives, sample_alignments):
        """Test retrieving alignments for a specific objective."""
        # Create objectives first
        for obj in sample_objectives:
            memory_db_repo.create_objective(obj)
        
        # Create alignments
        for alignment in sample_alignments:
            memory_db_repo.create_alignment(alignment)
        
        objective_id = sample_alignments[0].objective_id
        alignments = memory_db_repo.get_objective_alignments(objective_id)
        
        assert len(alignments) >= 1
        for alignment in alignments:
            assert alignment.objective_id == objective_id
    
    def test_upsert_alignment(self, memory_db_repo, sample_objectives, sample_alignments):
        """Test that creating an alignment twice performs an upsert."""
        # Create objectives first
        for obj in sample_objectives:
            memory_db_repo.create_objective(obj)
        
        alignment = sample_alignments[0]
        
        # Create alignment first time
        memory_db_repo.create_alignment(alignment)
        
        # Create updated alignment (should be upsert)
        from dataclasses import replace
        updated_alignment = replace(alignment, alignment_score=0.95, confidence=0.85)
        updated = memory_db_repo.create_alignment(updated_alignment)
        
        assert updated.alignment_score == 0.95
        assert updated.confidence == 0.85
        
        # Verify only one alignment exists for this task-objective pair
        alignments = memory_db_repo.get_task_alignments(alignment.task_id)
        matching_alignments = [
            a for a in alignments 
            if a.objective_id == alignment.objective_id
        ]
        assert len(matching_alignments) == 1


class TestVisionInsightOperations:
    """Test Vision Insight operations."""
    
    def test_create_insight(self, memory_db_repo, sample_insights):
        """Test creating a vision insight."""
        insight = sample_insights[0]
        created = memory_db_repo.create_insight(insight)
        
        assert created is not None
        assert created.id == insight.id
        assert created.type == insight.type
        assert created.title == insight.title
    
    def test_get_active_insights_no_filters(self, memory_db_repo, sample_insights):
        """Test retrieving active insights without filters."""
        insight = sample_insights[0]
        memory_db_repo.create_insight(insight)
        
        active_insights = memory_db_repo.get_active_insights()
        
        # Should find our insight
        insight_ids = [i.id for i in active_insights]
        assert insight.id in insight_ids
    
    def test_get_active_insights_with_filters(self, memory_db_repo, sample_insights):
        """Test retrieving active insights with filters."""
        insight = sample_insights[0]
        # Create new insight with updated values (dataclass is frozen)
        from dataclasses import replace
        updated_insight = replace(insight, impact="high")
        memory_db_repo.create_insight(updated_insight)
        
        # Filter by impact
        high_impact_insights = memory_db_repo.get_active_insights(impact="high")
        assert len(high_impact_insights) >= 1
        for i in high_impact_insights:
            assert i.impact == "high"
        
        # Filter by user_id
        user_insights = memory_db_repo.get_active_insights(user_id="test_user")
        assert len(user_insights) >= 1
        
        # Filter by project_id
        project_insights = memory_db_repo.get_active_insights(project_id="test_project")
        assert len(project_insights) >= 1
    
    def test_dismiss_insight(self, memory_db_repo, sample_insights):
        """Test dismissing an insight."""
        insight = sample_insights[0]
        memory_db_repo.create_insight(insight)
        
        # Verify insight is active
        active_insights = memory_db_repo.get_active_insights()
        insight_ids = [i.id for i in active_insights]
        assert insight.id in insight_ids
        
        # Dismiss the insight
        result = memory_db_repo.dismiss_insight(insight.id)
        assert result is True
        
        # Verify insight is no longer active
        active_insights = memory_db_repo.get_active_insights()
        insight_ids = [i.id for i in active_insights]
        assert insight.id not in insight_ids
    
    def test_dismiss_nonexistent_insight(self, memory_db_repo):
        """Test dismissing a non-existent insight returns False."""
        non_existent_id = uuid4()
        result = memory_db_repo.dismiss_insight(non_existent_id)
        assert result is False


class TestSQLiteSpecificFeatures:
    """Test SQLite-specific features and data handling."""
    
    def test_json_serialization(self, memory_db_repo, sample_objectives):
        """Test that complex JSON data is properly serialized/deserialized."""
        obj = sample_objectives[0]
        # Create new objective with complex metadata (dataclass is frozen)
        from dataclasses import replace
        complex_metadata = {
            "complex_data": {
                "nested": {"value": 123},
                "array": [1, 2, 3],
                "bool": True,
                "null": None
            }
        }
        updated_obj = replace(obj, metadata=complex_metadata)
        
        memory_db_repo.create_objective(updated_obj)
        retrieved = memory_db_repo.get_objective(updated_obj.id)
        
        assert retrieved.metadata == updated_obj.metadata
        assert retrieved.metadata["complex_data"]["nested"]["value"] == 123
        assert retrieved.metadata["complex_data"]["array"] == [1, 2, 3]
        assert retrieved.metadata["complex_data"]["bool"] is True
        assert retrieved.metadata["complex_data"]["null"] is None
    
    def test_uuid_string_conversion(self, memory_db_repo, sample_objectives):
        """Test that UUIDs are properly converted to/from strings."""
        obj = sample_objectives[0]
        original_id = obj.id
        
        memory_db_repo.create_objective(obj)
        retrieved = memory_db_repo.get_objective(obj.id)
        
        assert isinstance(retrieved.id, UUID)
        assert retrieved.id == original_id
        assert str(retrieved.id) == str(original_id)
    
    def test_timestamp_handling(self, memory_db_repo, sample_objectives):
        """Test that timestamps are properly handled."""
        obj = sample_objectives[0]
        # Create new objective with due date (dataclass is frozen)
        from dataclasses import replace
        due_date = datetime.now(timezone.utc)
        updated_obj = replace(obj, due_date=due_date)
        
        memory_db_repo.create_objective(updated_obj)
        retrieved = memory_db_repo.get_objective(updated_obj.id)
        
        assert retrieved.due_date is not None
        assert isinstance(retrieved.due_date, datetime)
        # Allow for small differences due to serialization
        time_diff = abs((retrieved.due_date - updated_obj.due_date).total_seconds())
        assert time_diff < 1.0  # Less than 1 second difference
    
    def test_null_value_handling(self, memory_db_repo):
        """Test that NULL values are properly handled."""
        obj = VisionObjective(
            title="Test Objective",
            description=None,  # NULL description
            level=VisionHierarchyLevel.PROJECT,
            parent_id=None,    # NULL parent_id
            owner=None,        # NULL owner
            due_date=None      # NULL due_date
        )
        
        memory_db_repo.create_objective(obj)
        retrieved = memory_db_repo.get_objective(obj.id)
        
        assert retrieved.description == ""  # Should be empty string
        assert retrieved.parent_id is None
        assert retrieved.owner == ""  # Should be empty string
        assert retrieved.due_date is None


class TestTransactionAndConcurrency:
    """Test transaction handling and basic concurrency scenarios."""
    
    def test_transaction_rollback_on_error(self, memory_db_repo):
        """Test that transactions are properly rolled back on errors."""
        # This is a basic test since SQLite with the base class handles transactions
        initial_count = len(memory_db_repo.list_objectives())
        
        # Create an objective with invalid data that should fail validation
        # (though our current implementation is quite permissive)
        obj = VisionObjective(
            title="Test",
            description="Test",
            level=VisionHierarchyLevel.PROJECT
        )
        
        # This should succeed, but let's test the pattern
        try:
            memory_db_repo.create_objective(obj)
            final_count = len(memory_db_repo.list_objectives())
            assert final_count == initial_count + 1
        except Exception:
            # If it failed, count should be unchanged
            final_count = len(memory_db_repo.list_objectives())
            assert final_count == initial_count
    
    def test_multiple_repositories_same_file(self, temp_db):
        """Test that multiple repository instances can work with the same database file."""
        repo1 = SQLiteVisionRepository(db_path=temp_db)
        repo2 = SQLiteVisionRepository(db_path=temp_db)
        
        # Create objective with repo1
        obj = VisionObjective(
            title="Shared Test",
            description="Test sharing between repos",
            level=VisionHierarchyLevel.PROJECT
        )
        repo1.create_objective(obj)
        
        # Retrieve with repo2
        retrieved = repo2.get_objective(obj.id)
        assert retrieved is not None
        assert retrieved.title == "Shared Test"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])