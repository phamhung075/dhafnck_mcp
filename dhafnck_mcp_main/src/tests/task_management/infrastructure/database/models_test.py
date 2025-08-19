"""
Tests for SQLAlchemy ORM Models

This module tests the database models including:
- Model creation and relationships
- Field constraints and validations
- Indexes and unique constraints
- JSON field handling
- Cascade behaviors
- Global singleton UUID handling
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from fastmcp.task_management.infrastructure.database.models import (
    Base,
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
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            user_id="test-user-123"
        )
        
        branch = ProjectGitBranch(
            id=str(uuid4()),
            project_id=project.id,
            name="feature/test",
            description="Test branch"
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
        project = Project(id=str(uuid4()), name="Test Project", user_id="test-user-123")
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main")
        
        # Create task
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test Description",
            git_branch_id=branch.id,
            status="todo",
            priority="high",
            user_id="test-user-123"
        )
        
        # Add subtask
        subtask = TaskSubtask(
            id=str(uuid4()),
            task_id=task.id,
            title="Subtask 1",
            description="Subtask description"
        )
        
        # Add assignee
        assignee = TaskAssignee(
            task_id=task.id,
            assignee_id="assignee-123",
            role="developer"
        )
        
        # Add label
        label = Label(id="bug", name="Bug", color="#ff0000")
        task_label = TaskLabel(task_id=task.id, label_id=label.id)
        
        # Add all to session
        session.add_all([project, branch, task, subtask, assignee, label, task_label])
        session.commit()
        
        # Verify relationships
        saved_task = session.query(Task).first()
        assert saved_task.git_branch is not None
        assert len(saved_task.subtasks) == 1
        assert len(saved_task.assignees) == 1
        assert len(saved_task.labels) == 1
        assert saved_task.assignees[0].assignee_id == "assignee-123"
        assert saved_task.labels[0].label.name == "Bug"
    
    def test_task_dependency_constraints(self, session):
        """Test TaskDependency constraints"""
        project = Project(id=str(uuid4()), name="Test Project", user_id="test-user-123")
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main")
        
        task1 = Task(
            id=str(uuid4()),
            title="Task 1",
            description="First task",
            git_branch_id=branch.id
        )
        
        task2 = Task(
            id=str(uuid4()),
            title="Task 2",
            description="Second task",
            git_branch_id=branch.id
        )
        
        # Valid dependency
        dependency = TaskDependency(
            task_id=task2.id,
            depends_on_task_id=task1.id,
            dependency_type="blocks"
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
            id="agent-123",
            name="Test Agent",
            description="Test agent description",
            capabilities=["DEVELOPER", "TESTER"],
            status="available",
            availability_score=0.95,
            user_id="test-user-123",
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
            id="template-123",
            name="Task Template",
            type="task",
            content={"title": "Template Title", "fields": ["field1", "field2"]},
            category="development",
            tags=["backend", "api"],
            created_by="user-123"
        )
        
        session.add(template)
        session.commit()
        
        saved_template = session.query(Template).first()
        assert saved_template.type == "task"
        assert saved_template.content["title"] == "Template Title"
        assert "backend" in saved_template.tags
        assert saved_template.usage_count == 0
    
    def test_global_context_singleton(self, session):
        """Test GlobalContext with singleton UUID"""
        global_context = GlobalContext(
            id=GLOBAL_SINGLETON_UUID,
            organization_id="org-123",
            autonomous_rules={"rule1": "value1"},
            security_policies={"policy1": "value1"},
            coding_standards={"standard1": "value1"},
            workflow_templates={"template1": "value1"},
            delegation_rules={"delegation1": "value1"},
            user_id="test-user-123"
        )
        
        session.add(global_context)
        session.commit()
        
        saved_context = session.query(GlobalContext).first()
        assert saved_context.id == GLOBAL_SINGLETON_UUID
        assert saved_context.autonomous_rules["rule1"] == "value1"
        assert saved_context.version == 1
    
    def test_hierarchical_context_relationships(self, session):
        """Test hierarchical context relationships"""
        # Create hierarchy
        global_ctx = GlobalContext(
            id=GLOBAL_SINGLETON_UUID,
            organization_id="org-123",
            user_id="test-user-123"
        )
        
        project_ctx = ProjectContext(
            id=str(uuid4()),
            project_id=str(uuid4()),
            parent_global_id=global_ctx.id,
            data={"project": "data"},
            user_id="test-user-123"
        )
        
        branch_ctx = BranchContext(
            id=str(uuid4()),
            branch_id=str(uuid4()),
            parent_project_id=project_ctx.id,
            data={"branch": "data"},
            user_id="test-user-123"
        )
        
        task_ctx = TaskContext(
            id=str(uuid4()),
            task_id=str(uuid4()),
            parent_branch_context_id=branch_ctx.id,
            data={"task": "data"},
            user_id="test-user-123"
        )
        
        session.add_all([global_ctx, project_ctx, branch_ctx, task_ctx])
        session.commit()
        
        # Verify relationships
        saved_global = session.query(GlobalContext).first()
        assert len(saved_global.project_contexts) == 1
        
        saved_project = session.query(ProjectContext).first()
        assert saved_project.global_context == saved_global
        assert len(saved_project.branch_contexts) == 1
        
        saved_branch = session.query(BranchContext).first()
        assert saved_branch.project_context == saved_project
        assert len(saved_branch.task_contexts) == 1
        
        saved_task = session.query(TaskContext).first()
        assert saved_task.branch_context == saved_branch
    
    def test_context_delegation(self, session):
        """Test ContextDelegation model"""
        delegation = ContextDelegation(
            id=str(uuid4()),
            source_level="task",
            source_id="task-123",
            target_level="project",
            target_id="project-123",
            delegated_data={"pattern": "auth_flow"},
            delegation_reason="Reusable pattern",
            trigger_type="manual",
            confidence_score=0.95
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
        cache_entry = ContextInheritanceCache(
            context_id="task-123",
            context_level="task",
            resolved_context={"merged": "data"},
            dependencies_hash="abc123",
            resolution_path="global->project->branch->task",
            expires_at=datetime.utcnow(),
            cache_size_bytes=1024
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
        project = Project(id=str(uuid4()), name="Test Project", user_id="test-user-123")
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main")
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test",
            git_branch_id=branch.id
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
        branch = ProjectGitBranch(id=str(uuid4()), project_id=project.id, name="main")
        task = Task(
            id=str(uuid4()),
            title="Test Task",
            description="Test",
            git_branch_id=branch.id
        )
        
        # Create duplicate assignee
        assignee1 = TaskAssignee(task_id=task.id, assignee_id="user-123", role="developer")
        assignee2 = TaskAssignee(task_id=task.id, assignee_id="user-123", role="reviewer")
        
        session.add_all([project, branch, task, assignee1, assignee2])
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_json_field_mutations(self, session):
        """Test JSON field mutations are persisted"""
        project = Project(
            id=str(uuid4()),
            name="Test Project",
            user_id="test-user-123",
            model_metadata={"initial": "value"}
        )
        
        session.add(project)
        session.commit()
        
        # Modify JSON field
        project.model_metadata["new_key"] = "new_value"
        session.commit()
        
        # Refresh and verify
        session.refresh(project)
        assert project.model_metadata["new_key"] == "new_value"
        assert project.model_metadata["initial"] == "value"