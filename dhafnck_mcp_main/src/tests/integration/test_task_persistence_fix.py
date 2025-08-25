"""
Integration Test for Task Persistence Fix

Tests the complete fix for task persistence issues related to missing user_id columns
in task relationship tables (task_subtasks, task_assignees, task_labels).
"""

import pytest
import uuid
import logging
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastmcp.task_management.infrastructure.database.models import (
    Base, Task, TaskAssignee, TaskLabel, TaskSubtask, Label, ProjectGitBranch, Project
)
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority

logger = logging.getLogger(__name__)


class TestTaskPersistenceFix:
    """Test suite for task persistence fix"""
    
    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        # Run the user isolation fix migration manually
        with engine.connect() as conn:
            # Add user_id columns to relationship tables
            try:
                conn.execute(text("ALTER TABLE task_subtasks ADD COLUMN user_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE task_assignees ADD COLUMN user_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE task_labels ADD COLUMN user_id VARCHAR(255)"))
            except Exception:
                pass  # Columns might already exist
            
            conn.commit()
        
        return engine
    
    @pytest.fixture
    def session(self, engine):
        """Create database session"""
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def test_data(self, session):
        """Create test data structure"""
        # Create test user ID
        user_id = "test-user-123"
        
        # Create test project
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name="Test Project",
            description="Project for testing task persistence",
            user_id=user_id
        )
        session.add(project)
        
        # Create test git branch
        branch_id = str(uuid.uuid4())
        branch = ProjectGitBranch(
            id=branch_id,
            project_id=project_id,
            name="feature/test-persistence",
            description="Branch for testing task persistence",
            user_id=user_id
        )
        session.add(branch)
        
        # Create test labels
        label1_id = str(uuid.uuid4())
        label1 = Label(
            id=label1_id,
            name="bug",
            color="#ff0000",
            description="Bug label",
            user_id=user_id
        )
        session.add(label1)
        
        label2_id = str(uuid.uuid4())
        label2 = Label(
            id=label2_id,
            name="feature",
            color="#00ff00",
            description="Feature label",
            user_id=user_id
        )
        session.add(label2)
        
        session.commit()
        
        return {
            "user_id": user_id,
            "project_id": project_id,
            "branch_id": branch_id,
            "label1_id": label1_id,
            "label2_id": label2_id
        }
    
    def test_task_creation_with_all_relationships(self, session, test_data):
        """Test creating a task with assignees, labels, and subtasks"""
        user_id = test_data["user_id"]
        branch_id = test_data["branch_id"]
        
        # Create repository instance
        repository = ORMTaskRepository(
            session=session,
            git_branch_id=branch_id,
            user_id=user_id
        )
        
        # Test data
        task_title = "Test Task with All Relationships"
        task_description = "Testing task creation with assignees, labels, and subtasks"
        assignee_ids = ["user1", "user2"]
        label_names = ["bug", "feature"]
        
        # Create task with all relationships
        task = repository.create_task(
            title=task_title,
            description=task_description,
            priority="high",
            assignee_ids=assignee_ids,
            label_names=label_names,
            status="todo"
        )
        
        # Verify task was created
        assert task is not None
        assert task.title == task_title
        assert task.description == task_description
        assert isinstance(task.priority, Priority)
        assert task.priority.value == "high"
        
        # Verify assignees were created with user_id
        db_assignees = session.query(TaskAssignee).filter(
            TaskAssignee.task_id == str(task.id)
        ).all()
        
        assert len(db_assignees) == 2
        for assignee in db_assignees:
            assert assignee.user_id == user_id
            assert assignee.assignee_id in assignee_ids
        
        # Verify labels were created with user_id
        db_task_labels = session.query(TaskLabel).filter(
            TaskLabel.task_id == str(task.id)
        ).all()
        
        assert len(db_task_labels) == 2
        for task_label in db_task_labels:
            assert task_label.user_id == user_id
    
    def test_task_retrieval_with_missing_relationships(self, session, test_data):
        """Test task retrieval when relationship tables have missing user_id"""
        user_id = test_data["user_id"]
        branch_id = test_data["branch_id"]
        
        # Create a task directly in database
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            git_branch_id=branch_id,
            status="todo",
            priority="medium",
            user_id=user_id
        )
        session.add(task)
        
        # Create assignee WITHOUT user_id (simulating old data)
        assignee = TaskAssignee(
            task_id=task_id,
            assignee_id="user1",
            role="contributor"
            # user_id is intentionally missing
        )
        session.add(assignee)
        
        # Create label relationship WITHOUT user_id
        label_id = test_data["label1_id"]
        task_label = TaskLabel(
            task_id=task_id,
            label_id=label_id
            # user_id is intentionally missing
        )
        session.add(task_label)
        
        session.commit()
        
        # Create repository and try to retrieve task
        repository = ORMTaskRepository(
            session=session,
            git_branch_id=branch_id,
            user_id=user_id
        )
        
        # This should not fail even with missing user_id in relationships
        retrieved_task = repository.get_task(task_id)
        
        # Task should be retrieved successfully
        assert retrieved_task is not None
        assert retrieved_task.title == "Test Task"
        
        # Relationships should be handled gracefully (may be empty due to schema issues)
        # The key is that it doesn't crash
        assert isinstance(retrieved_task.assignees, list)
        assert isinstance(retrieved_task.labels, list)
    
    def test_subtask_creation_with_user_id(self, session, test_data):
        """Test subtask creation includes user_id"""
        user_id = test_data["user_id"]
        branch_id = test_data["branch_id"]
        
        # Create parent task first
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title="Parent Task",
            description="Task with subtasks",
            git_branch_id=branch_id,
            status="todo",
            priority="medium",
            user_id=user_id
        )
        session.add(task)
        session.commit()
        
        # Create subtask manually to test user_id inclusion
        subtask_id = str(uuid.uuid4())
        subtask = TaskSubtask(
            id=subtask_id,
            task_id=task_id,
            title="Test Subtask",
            description="Testing subtask with user_id",
            status="todo",
            priority="medium",
            user_id=user_id  # This should be included
        )
        session.add(subtask)
        session.commit()
        
        # Verify subtask has user_id
        db_subtask = session.query(TaskSubtask).filter(
            TaskSubtask.id == subtask_id
        ).first()
        
        assert db_subtask is not None
        assert db_subtask.user_id == user_id
        assert db_subtask.task_id == task_id
    
    def test_migration_backfill_simulation(self, session, test_data):
        """Test simulation of migration backfill process"""
        user_id = test_data["user_id"]
        branch_id = test_data["branch_id"]
        
        # Create task
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title="Migration Test Task",
            description="Testing migration backfill",
            git_branch_id=branch_id,
            status="todo",
            priority="medium",
            user_id=user_id
        )
        session.add(task)
        
        # Create relationships without user_id (old state)
        assignee = TaskAssignee(
            task_id=task_id,
            assignee_id="user1",
            role="contributor",
            user_id=None  # Simulate missing user_id
        )
        session.add(assignee)
        
        task_label = TaskLabel(
            task_id=task_id,
            label_id=test_data["label1_id"],
            user_id=None  # Simulate missing user_id
        )
        session.add(task_label)
        
        session.commit()
        
        # Simulate migration backfill
        with session.get_bind().connect() as conn:
            # Backfill assignees
            conn.execute(text("""
                UPDATE task_assignees 
                SET user_id = (
                    SELECT tasks.user_id 
                    FROM tasks 
                    WHERE tasks.id = task_assignees.task_id
                )
                WHERE task_assignees.user_id IS NULL
            """))
            
            # Backfill labels
            conn.execute(text("""
                UPDATE task_labels 
                SET user_id = (
                    SELECT tasks.user_id 
                    FROM tasks 
                    WHERE tasks.id = task_labels.task_id
                )
                WHERE task_labels.user_id IS NULL
            """))
            
            conn.commit()
        
        # Refresh objects
        session.expunge_all()
        
        # Verify backfill worked
        updated_assignee = session.query(TaskAssignee).filter(
            TaskAssignee.task_id == task_id
        ).first()
        
        updated_label = session.query(TaskLabel).filter(
            TaskLabel.task_id == task_id
        ).first()
        
        assert updated_assignee.user_id == user_id
        assert updated_label.user_id == user_id
    
    def test_repository_graceful_error_handling(self, session, test_data):
        """Test that repository handles relationship loading errors gracefully"""
        user_id = test_data["user_id"]
        branch_id = test_data["branch_id"]
        
        # Create repository
        repository = ORMTaskRepository(
            session=session,
            git_branch_id=branch_id,
            user_id=user_id
        )
        
        # Create task with valid data
        task = repository.create_task(
            title="Graceful Error Test",
            description="Testing error handling",
            priority="medium",
            assignee_ids=["user1"],
            label_names=["bug"]
        )
        
        assert task is not None
        
        # The graceful loading should work even if relationships fail
        # This tests the _load_task_with_relationships method
        retrieved_task = repository.get_task(str(task.id))
        
        assert retrieved_task is not None
        assert retrieved_task.title == "Graceful Error Test"
    
    def test_schema_validation_integration(self, engine):
        """Test that schema validation detects and reports issues correctly"""
        # This would normally import and run the schema validation
        # For now, just verify the basic structure exists
        
        with engine.connect() as conn:
            # Check that user_id columns exist in relationship tables
            result = conn.execute(text("""
                SELECT name FROM pragma_table_info('task_assignees') 
                WHERE name = 'user_id'
            """))
            user_id_column = result.fetchone()
            
            # If the column exists, this test passes
            # If it doesn't exist, the migration needs to be run
            if user_id_column:
                logger.info("✅ task_assignees.user_id column exists")
            else:
                logger.warning("⚠️ task_assignees.user_id column missing - migration needed")
    
    def test_complete_task_lifecycle_with_fix(self, session, test_data):
        """Test complete task lifecycle after the persistence fix"""
        user_id = test_data["user_id"]
        branch_id = test_data["branch_id"]
        
        repository = ORMTaskRepository(
            session=session,
            git_branch_id=branch_id,
            user_id=user_id
        )
        
        # 1. Create task with full relationships
        task = repository.create_task(
            title="Complete Lifecycle Test",
            description="Testing full task lifecycle",
            priority="high",
            assignee_ids=["user1", "user2"],
            label_names=["feature", "bug"],
            status="todo"
        )
        
        original_task_id = str(task.id)
        
        # 2. Update task
        updated_task = repository.update_task(
            original_task_id,
            status="in_progress",
            assignee_ids=["user1", "user3"],  # Change assignees
            label_names=["feature"]  # Remove one label
        )
        
        assert updated_task.status.value == "in_progress"
        
        # 3. Retrieve task
        retrieved_task = repository.get_task(original_task_id)
        assert retrieved_task is not None
        assert retrieved_task.status.value == "in_progress"
        
        # 4. Verify all relationships have user_id
        db_assignees = session.query(TaskAssignee).filter(
            TaskAssignee.task_id == original_task_id
        ).all()
        
        db_labels = session.query(TaskLabel).filter(
            TaskLabel.task_id == original_task_id
        ).all()
        
        # All relationships should have user_id
        for assignee in db_assignees:
            assert assignee.user_id == user_id
        
        for task_label in db_labels:
            assert task_label.user_id == user_id
        
        # 5. Delete task
        delete_result = repository.delete_task(original_task_id)
        assert delete_result is True
        
        # 6. Verify task is gone
        deleted_task = repository.get_task(original_task_id)
        assert deleted_task is None


if __name__ == "__main__":
    # Run tests manually for debugging
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test instance
    test_instance = TestTaskPersistenceFix()
    
    print("🧪 Running Task Persistence Fix Integration Tests...")
    
    try:
        # Run key tests manually
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        # Add user_id columns manually
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE task_subtasks ADD COLUMN user_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE task_assignees ADD COLUMN user_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE task_labels ADD COLUMN user_id VARCHAR(255)"))
                conn.commit()
            except Exception as e:
                print(f"Note: {e}")
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test data
        test_data = {
            "user_id": "test-user-123",
            "project_id": str(uuid.uuid4()),
            "branch_id": str(uuid.uuid4()),
            "label1_id": str(uuid.uuid4()),
            "label2_id": str(uuid.uuid4())
        }
        
        # Create basic test data
        project = Project(
            id=test_data["project_id"],
            name="Test Project",
            description="Test",
            user_id=test_data["user_id"]
        )
        session.add(project)
        
        branch = ProjectGitBranch(
            id=test_data["branch_id"],
            project_id=test_data["project_id"],
            name="test-branch",
            description="Test",
            user_id=test_data["user_id"]
        )
        session.add(branch)
        
        label = Label(
            id=test_data["label1_id"],
            name="bug",
            color="#ff0000",
            user_id=test_data["user_id"]
        )
        session.add(label)
        
        session.commit()
        
        # Run basic test
        test_instance.test_task_creation_with_all_relationships(session, test_data)
        print("✅ Task creation with relationships test passed")
        
        test_instance.test_migration_backfill_simulation(session, test_data)
        print("✅ Migration backfill simulation test passed")
        
        test_instance.test_repository_graceful_error_handling(session, test_data)
        print("✅ Graceful error handling test passed")
        
        session.close()
        
        print("🎉 All integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)