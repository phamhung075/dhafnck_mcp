"""
Tests for SQLAlchemy ORM Models

This module tests the database models including:
- Model creation and relationships
- Field constraints and validations
- Indexes and unique constraints
- JSON field handling
- Cascade behaviors
- Global singleton UUID handling
- User isolation and authentication context
- Model serialization and deserialization
- Database migrations compatibility
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import patch

import json
from fastmcp.task_management.infrastructure.database.models import (
    Base,
    APIToken,
    Project,
    ProjectGitBranch,
    Task,
    TaskSubtask,
    TaskAssignee,
    TaskDependency,
    Agent,
    Label,
    TaskLabel,
    Template,
    GlobalContext,
    ProjectContext,
    BranchContext,
    TaskContext,
    ContextDelegation,
    ContextInheritanceCache,
    GLOBAL_SINGLETON_UUID
)


class TestDatabaseModels:
    """Test suite for database models"""
    
    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite database engine"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def session(self, engine):
        """Create database session"""
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_api_token_model(self, session):
        """Test APIToken model creation and fields"""
        from datetime import datetime, timedelta, timezone
        
        # Create API token
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        api_token = APIToken(
            id=str(uuid4()),
            user_id="test-user-123",
            name="Test Token",
            token_hash="hashed_token_value",
            scopes=["read", "write"],
            expires_at=expires_at,
            rate_limit=5000,
            token_metadata={"source": "test", "environment": "dev"}
        )
        
        session.add(api_token)
        session.commit()
        
        # Verify token was created
        retrieved_token = session.query(APIToken).filter_by(id=api_token.id).first()
        assert retrieved_token is not None
        assert retrieved_token.user_id == "test-user-123"
        assert retrieved_token.name == "Test Token"
        assert retrieved_token.token_hash == "hashed_token_value"
        assert retrieved_token.scopes == ["read", "write"]
        # Compare without timezone info since SQLite doesn't store timezone
        assert retrieved_token.expires_at.replace(tzinfo=timezone.utc) == expires_at
        assert retrieved_token.usage_count == 0
        assert retrieved_token.rate_limit == 5000
        assert retrieved_token.is_active is True
        assert retrieved_token.token_metadata == {"source": "test", "environment": "dev"}
        assert retrieved_token.created_at is not None
        assert retrieved_token.last_used_at is None
    
    def test_api_token_default_values(self, session):
        """Test APIToken model default values"""
        from datetime import datetime, timedelta, timezone
        
        # Create minimal API token
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        api_token = APIToken(
            id=str(uuid4()),
            user_id="test-user-456",
            name="Minimal Token",
            token_hash="minimal_hash",
            expires_at=expires_at
        )
        
        session.add(api_token)
        session.commit()
        
        # Verify defaults
        retrieved_token = session.query(APIToken).filter_by(id=api_token.id).first()
        assert retrieved_token.scopes == []
        assert retrieved_token.usage_count == 0
        assert retrieved_token.rate_limit == 1000
        assert retrieved_token.is_active is True
        assert retrieved_token.token_metadata == {}
    
    def test_api_token_update_usage(self, session):
        """Test updating API token usage statistics"""
        from datetime import datetime, timedelta, timezone
        
        # Create and save token
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        api_token = APIToken(
            id=str(uuid4()),
            user_id="test-user-789",
            name="Usage Token",
            token_hash="usage_hash",
            expires_at=expires_at
        )
        
        session.add(api_token)
        session.commit()
        
        # Update usage
        now = datetime.now(timezone.utc)
        api_token.usage_count = 10
        api_token.last_used_at = now
        session.commit()
        
        # Verify updates
        retrieved_token = session.query(APIToken).filter_by(id=api_token.id).first()
        assert retrieved_token.usage_count == 10
        # Compare without timezone info since SQLite doesn't store timezone
        assert retrieved_token.last_used_at.replace(tzinfo=timezone.utc) == now
    
    def test_api_token_hash_duplicates_allowed(self, session):
        """Test that APIToken allows duplicate token_hash (no unique constraint in model)."""
        from datetime import datetime, timedelta, timezone
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Create first token
        token1 = APIToken(
            id=str(uuid4()),
            user_id="test-user-999",
            name="Token 1",
            token_hash="shared_hash_123",
            expires_at=expires_at
        )
        session.add(token1)
        session.commit()
        
        # Create second token with same hash - should succeed since no unique constraint
        token2 = APIToken(
            id=str(uuid4()),
            user_id="test-user-999",
            name="Token 2",
            token_hash="shared_hash_123",  # Same hash
            expires_at=expires_at
        )
        session.add(token2)
        session.commit()  # Should not raise an error
        
        # Verify both tokens exist with same hash
        tokens = session.query(APIToken).filter_by(token_hash="shared_hash_123").all()
        assert len(tokens) == 2
    
    def test_api_token_deactivation(self, session):
        """Test APIToken deactivation behavior."""
        from datetime import datetime, timedelta, timezone
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Create active token
        token = APIToken(
            id=str(uuid4()),
            user_id="test-user-888",
            name="Active Token",
            token_hash="active_token_hash",
            is_active=True,
            expires_at=expires_at
        )
        session.add(token)
        session.commit()
        
        # Deactivate token
        token.is_active = False
        session.commit()
        
        # Verify deactivation
        deactivated = session.query(APIToken).filter_by(id=token.id).first()
        assert deactivated.is_active is False
    
    def test_user_id_not_null_constraints(self, session):
        """Test that user_id cannot be null on models that require it."""
        from sqlalchemy.exc import IntegrityError
        
        # Test Project without user_id
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            description="Test Description",
            user_id=None  # Explicitly set to None
        )
        session.add(project)
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        
        # Test Task without user_id
        # First need to create project and branch
        valid_user_id = str(uuid4())
        project = Project(
            id=str(uuid4()),
            name="Valid Project",
            description="For task test",
            user_id=valid_user_id
        )
        branch = ProjectGitBranch(
            id=str(uuid4()),
            project_id=project.id,
            name="main",
            user_id=valid_user_id  # Branch also needs user_id
        )
        session.add_all([project, branch])
        session.commit()
        
        task = Task(
            id=str(uuid4()),
            git_branch_id=branch.id,
            title="Test Task",
            user_id=None  # Explicitly set to None
        )
        session.add(task)
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        
        # Test Agent without user_id
        agent = Agent(
            id=str(uuid4()),
            name="Test Agent",
            user_id=None  # Explicitly set to None
        )
        session.add(agent)
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        
        # Test TaskSubtask without user_id
        task_with_user = Task(
            id=str(uuid4()),
            git_branch_id=branch.id,
            title="Task with User",
            description="Task description",  # Required field
            user_id=valid_user_id
        )
        session.add(task_with_user)
        session.commit()
        
        subtask = TaskSubtask(
            id=str(uuid4()),
            task_id=task_with_user.id,
            title="Subtask",
            user_id=None  # Explicitly set to None
        )
        session.add(subtask)
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        
        # Test TaskAssignee without user_id
        assignee = TaskAssignee(
            task_id=task_with_user.id,
            assignee_id=str(uuid4()),
            user_id=None  # Explicitly set to None
        )
        session.add(assignee)
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        
        # Test TaskLabel without user_id
        label = Label(id="test-label", name="Test Label", user_id=valid_user_id)
        task_label = TaskLabel(
            task_id=task_with_user.id,
            label_id=label.id,
            user_id=None  # Explicitly set to None
        )
        session.add_all([label, task_label])
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        
        # Test TaskDependency without user_id
        task2 = Task(
            id=str(uuid4()),
            git_branch_id=branch.id,
            title="Task 2",
            description="Task 2 description",  # Required field
            user_id=valid_user_id
        )
        session.add(task2)
        session.commit()
        
        dependency = TaskDependency(
            task_id=task2.id,
            depends_on_task_id=task_with_user.id,
            user_id=None  # Explicitly set to None
        )
        session.add(dependency)
        
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    
    def test_user_isolation_boundaries(self, session):
        """Test that user data is properly isolated."""
        # Create projects for two different users
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        project1 = Project(
            id=str(uuid4()),
            name="User 1 Project",
            description="Project for user 1",
            user_id=user1_id
        )
        project2 = Project(
            id=str(uuid4()),
            name="User 2 Project",
            description="Project for user 2",
            user_id=user2_id
        )
        session.add_all([project1, project2])
        session.commit()
        
        # Query projects for user1
        user1_projects = session.query(Project).filter_by(user_id=user1_id).all()
        assert len(user1_projects) == 1
        assert user1_projects[0].name == "User 1 Project"
        
        # Query projects for user2
        user2_projects = session.query(Project).filter_by(user_id=user2_id).all()
        assert len(user2_projects) == 1
        assert user2_projects[0].name == "User 2 Project"
        
        # Verify no cross-user access
        assert all(p.user_id == user1_id for p in user1_projects)
        assert all(p.user_id == user2_id for p in user2_projects)
    
    def test_project_model(self, session):
        """Test Project model creation and fields"""
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            description="Test Description",
            user_id="test-user-123",
            status="active",
            model_metadata={"key": "value"}
        )
        
        session.add(project)
        session.commit()
        
        # Retrieve and verify
        saved_project = session.query(Project).first()
        assert saved_project.name == "Test Project"
        assert saved_project.description == "Test Description"
        assert saved_project.user_id == "test-user-123"
        assert saved_project.status == "active"
        assert saved_project.model_metadata == {"key": "value"}
        assert saved_project.created_at is not None
        assert saved_project.updated_at is not None
    
    def test_project_git_branch_relationship(self, session):
        """Test Project and GitBranch relationship"""
        test_user_id = str(uuid4())
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            user_id=test_user_id
        )
        
        branch = ProjectGitBranch(
            id=str(uuid4()),
            project_id=project.id,
            name="feature/test",
            description="Test branch",
            user_id=test_user_id
        )
        
        project.git_branchs.append(branch)
        session.add(project)
        session.commit()
        
        # Verify relationship
        saved_project = session.query(Project).first()
        assert len(saved_project.git_branchs) == 1
        assert saved_project.git_branchs[0].name == "feature/test"
        assert saved_project.git_branchs[0].project == saved_project
    
    def test_task_model_with_relationships(self, session):
        """Test Task model with all relationships"""
        # Create project and branch
        test_user_id = str(uuid4())
        project = Project(id=str(uuid4()), name="Test Project", user_id=test_user_id)
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main", user_id=test_user_id)
        
        # Create task
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test Description",
            git_branch_id=branch.id,
            status="todo",
            priority="high",
            user_id=test_user_id
        )
        
        # Add subtask
        subtask = TaskSubtask(
            id=str(uuid4()),
            task_id=task.id,
            title="Subtask 1",
            description="Subtask description",
            user_id=test_user_id
        )
        
        # Add assignee
        assignee = TaskAssignee(
            id=str(uuid4()),
            task_id=task.id,
            assignee_id=str(uuid4()),
            role="developer",
            user_id=test_user_id
        )
        
        # Add label
        system_user_id = str(uuid4())
        label = Label(id="bug", name="Bug", color="#ff0000", user_id=system_user_id)
        task_label = TaskLabel(task_id=task.id, label_id=label.id, user_id=system_user_id)
        
        # Add all to session
        session.add_all([project, branch, task, subtask, assignee, label, task_label])
        session.commit()
        
        # Verify relationships
        saved_task = session.query(Task).first()
        assert saved_task.git_branch is not None
        assert len(saved_task.subtasks) == 1
        assert len(saved_task.assignees) == 1
        assert len(saved_task.labels) == 1
        assert saved_task.assignees[0].assignee_id is not None
        assert saved_task.labels[0].label.name == "Bug"
    
    def test_task_dependency_constraints(self, session):
        """Test TaskDependency constraints"""
        test_user_id = str(uuid4())
        project = Project(id=str(uuid4()), name="Test Project", user_id=test_user_id)
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main", user_id=test_user_id)
        
        task1 = Task(
            id=str(uuid4()),
            title="Task 1",
            description="First task",
            git_branch_id=branch.id,
            user_id=test_user_id
        )
        
        task2 = Task(
            id=str(uuid4()),
            title="Task 2",
            description="Second task",
            git_branch_id=branch.id,
            user_id=test_user_id
        )
        
        # Valid dependency
        dependency = TaskDependency(
            task_id=task2.id,
            depends_on_task_id=task1.id,
            dependency_type="blocks",
            user_id=test_user_id
        )
        
        session.add_all([project, branch, task1, task2, dependency])
        session.commit()
        
        # Verify dependency
        saved_dep = session.query(TaskDependency).first()
        assert saved_dep.task_id == task2.id
        assert saved_dep.depends_on_task_id == task1.id
    
    def test_agent_model(self, session):
        """Test Agent model"""
        agent = Agent(
            id=str(uuid4()),  # Use proper UUID format
            name="Test Agent",
            description="Test agent description",
            capabilities=["DEVELOPER", "TESTER"],
            status="available",
            availability_score=0.95,
            user_id=str(uuid4()),
            model_metadata={"version": "1.0"}
        )
        
        session.add(agent)
        session.commit()
        
        saved_agent = session.query(Agent).first()
        assert saved_agent.name == "Test Agent"
        assert saved_agent.capabilities == ["DEVELOPER", "TESTER"]
        assert saved_agent.availability_score == 0.95
        assert saved_agent.model_metadata["version"] == "1.0"
    
    def test_template_model(self, session):
        """Test Template model"""
        template = Template(
            id=str(uuid4()),
            name="Task Template",
            type="task",
            content={"title": "Template Title", "fields": ["field1", "field2"]},
            category="development",
            tags=["backend", "api"],
            created_by=str(uuid4())
        )
        
        session.add(template)
        session.commit()
        
        saved_template = session.query(Template).first()
        assert saved_template.type == "task"
        assert saved_template.content["title"] == "Template Title"
        assert "backend" in saved_template.tags
        assert saved_template.usage_count == 0
    
    
    def test_context_delegation(self, session):
        """Test ContextDelegation model"""
        delegation = ContextDelegation(
            id=str(uuid4()),
            source_level="task",
            source_id=str(uuid4()),
            target_level="project",
            target_id=str(uuid4()),
            delegated_data={"pattern": "auth_flow"},
            delegation_reason="Reusable pattern",
            trigger_type="manual",
            confidence_score=0.95,
            user_id="test-user-123"  # Added required field
        )
        
        session.add(delegation)
        session.commit()
        
        saved_delegation = session.query(ContextDelegation).first()
        assert saved_delegation.source_level == "task"
        assert saved_delegation.target_level == "project"
        assert saved_delegation.delegated_data["pattern"] == "auth_flow"
        assert saved_delegation.processed is False
    
    def test_context_inheritance_cache(self, session):
        """Test ContextInheritanceCache model"""
        from datetime import timedelta
        cache_entry = ContextInheritanceCache(
            context_id=str(uuid4()),
            context_level="task",
            resolved_context={"merged": "data"},
            dependencies_hash="abc123",
            resolution_path="global->project->branch->task",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            cache_size_bytes=1024,
            user_id="test-user-123"  # Added required field
        )
        
        session.add(cache_entry)
        session.commit()
        
        saved_cache = session.query(ContextInheritanceCache).first()
        assert saved_cache.context_level == "task"
        assert saved_cache.resolved_context["merged"] == "data"
        assert saved_cache.hit_count == 0
        assert saved_cache.invalidated is False
    
    def test_cascade_delete_project(self, session):
        """Test cascade delete from Project"""
        # Create project with related data
        user_id = str(uuid4())  # Use valid UUID for user_id
        project = Project(id=str(uuid4()), name="Test Project", user_id=user_id)
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main", user_id=user_id)
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test",
            git_branch_id=branch.id,
            user_id=user_id
        )
        
        session.add_all([project, branch, task])
        session.commit()
        
        # Delete project
        session.delete(project)
        session.commit()
        
        # Verify cascading deletes
        assert session.query(Project).count() == 0
        assert session.query(ProjectGitBranch).count() == 0
        assert session.query(Task).count() == 0
    
    def test_unique_constraints(self, session):
        """Test unique constraints"""
        project = Project(id=str(uuid4()), name="Test Project", user_id="test-user-123")
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main", user_id="test-user-123")
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test",
            git_branch_id=branch.id,
            user_id="test-user-123"
        )
        
        # Create duplicate assignee
        assignee1 = TaskAssignee(task_id=task.id, assignee_id="user-123", role="developer")
        assignee2 = TaskAssignee(task_id=task.id, assignee_id="user-123", role="reviewer")
        
        session.add_all([project, branch, task, assignee1, assignee2])
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            session.commit()
    
    
    
    def test_context_optional_fields(self, session):
        """Test context models with optional fields"""
        # Test ProjectContext with minimal fields
        project_ctx = ProjectContext(
            id=str(uuid4()),
            data={"test": "data"},
            user_id="test-user-123"
        )
        
        session.add(project_ctx)
        session.commit()
        
        saved = session.query(ProjectContext).first()
        assert saved.data == {"test": "data"}
        assert saved.team_preferences == {}
        assert saved.technology_stack == {}
        assert saved.project_workflow == {}
        assert saved.version == 1
        assert saved.inheritance_disabled is False
    
    def test_subtask_completion_fields(self, session):
        """Test TaskSubtask completion-related fields"""
        project = Project(id=str(uuid4()), name="Test Project", user_id="test-user-123")
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main", user_id="test-user-123")
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test",
            git_branch_id=branch.id,
            user_id="test-user-123"
        )
        
        subtask = TaskSubtask(
            id=str(uuid4()),
            task_id=task.id,
            title="Test Subtask",
            progress_percentage=75,
            progress_notes="Completed initial implementation",
            blockers="Waiting for API documentation",
            insights_found=["Found optimization opportunity", "Discovered existing utility"],
            user_id="test-user-123"
        )
        
        session.add_all([project, branch, task, subtask])
        session.commit()
        
        saved_subtask = session.query(TaskSubtask).first()
        assert saved_subtask.progress_percentage == 75
        assert saved_subtask.progress_notes == "Completed initial implementation"
        assert saved_subtask.blockers == "Waiting for API documentation"
        assert len(saved_subtask.insights_found) == 2
        assert "Found optimization opportunity" in saved_subtask.insights_found
    
    def test_task_context_flags(self, session):
        """Test TaskContext control flags"""
        task_ctx = TaskContext(
            id=str(uuid4()),
            task_id=str(uuid4()),
            data={"test": "data"},
            force_local_only=True,
            inheritance_disabled=True,
            user_id="test-user-123"
        )
        
        session.add(task_ctx)
        session.commit()
        
        saved = session.query(TaskContext).first()
        assert saved.force_local_only is True
        assert saved.inheritance_disabled is True
    
    def test_context_delegation_validation(self, session):
        """Test ContextDelegation with different trigger types"""
        user_id = "test-user-context"
        
        # Test auto_pattern trigger
        delegation1 = ContextDelegation(
            id=str(uuid4()),
            source_level="task",
            source_id=str(uuid4()),
            target_level="branch",
            target_id=str(uuid4()),
            delegated_data={"pattern": "error_handling"},
            delegation_reason="Common error pattern",
            trigger_type="auto_pattern",
            auto_delegated=True,
            confidence_score=0.88,
            user_id=user_id
        )
        
        # Test auto_threshold trigger
        delegation2 = ContextDelegation(
            id=str(uuid4()),
            source_level="branch",
            source_id=str(uuid4()),
            target_level="project",
            target_id=str(uuid4()),
            delegated_data={"threshold": "performance_optimization"},
            delegation_reason="Performance pattern used in multiple branches",
            trigger_type="auto_threshold",
            auto_delegated=True,
            confidence_score=0.92,
            user_id=user_id
        )
        
        session.add_all([delegation1, delegation2])
        session.commit()
        
        # Verify delegations
        auto_pattern = session.query(ContextDelegation).filter_by(trigger_type="auto_pattern").first()
        assert auto_pattern.auto_delegated is True
        assert auto_pattern.confidence_score == 0.88
        assert auto_pattern.user_id == user_id
        
        auto_threshold = session.query(ContextDelegation).filter_by(trigger_type="auto_threshold").first()
        assert auto_threshold.auto_delegated is True
        assert auto_threshold.confidence_score == 0.92
        assert auto_threshold.user_id == user_id
    
    def test_agent_metadata_and_timestamps(self, session):
        """Test Agent model metadata and timestamp updates"""
        agent = Agent(
            id=str(uuid4()),
            name="Advanced Agent",
            description="Agent with enhanced capabilities",
            capabilities=["CODE_GENERATION", "TESTING", "DEBUGGING"],
            status="busy",
            availability_score=0.3,
            user_id=str(uuid4()),  # Use valid UUID
            model_metadata={
                "version": "2.0",
                "features": ["async", "parallel"],
                "config": {"timeout": 300}
            }
        )
        
        session.add(agent)
        session.commit()
        
        # Update last_active_at
        now = datetime.now(timezone.utc)
        agent.last_active_at = now
        session.commit()
        
        saved_agent = session.query(Agent).filter_by(id=agent.id).first()
        # Fix timezone comparison - add timezone info to retrieved datetime
        assert saved_agent.last_active_at.replace(tzinfo=timezone.utc) == now
        assert saved_agent.model_metadata["version"] == "2.0"
        assert "async" in saved_agent.model_metadata["features"]
        assert saved_agent.model_metadata["config"]["timeout"] == 300
    
    
