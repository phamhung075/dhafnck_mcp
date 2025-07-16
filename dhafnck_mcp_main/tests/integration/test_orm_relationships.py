#!/usr/bin/env python3
"""
Integration tests for ORM model relationships and constraints.

This test suite validates that all model relationships work correctly,
including foreign key constraints, cascading deletes, and referential integrity.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.infrastructure.database.models import (
    Project, Agent, ProjectTaskTree, Task, TaskSubtask, TaskLabel, Label,
    GlobalContext, ProjectContext, TaskContext, ContextDelegation, 
    ContextInheritanceCache, Template, Base
)
from fastmcp.task_management.infrastructure.database.database_config import get_db_config


class TestORMRelationships:
    """Test suite for ORM model relationships and constraints"""
    
    def setup_method(self):
        """Set up test environment with in-memory database"""
        # Use in-memory SQLite for testing
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()
    
    def teardown_method(self):
        """Clean up test environment"""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    def test_project_agent_relationship(self):
        """Test Project-Agent relationship"""
        # Create a project
        project = Project(
            name="Test Project",
            description="Test project for relationships",
            user_id="test_user",
            metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        # Create an agent
        agent = Agent(
            name="test_agent",
            agent_type="coding",
            status="available",
            capabilities=["coding", "testing"],
            metadata={}
        )
        self.session.add(agent)
        self.session.commit()
        
        # Create a project task tree (branch) linking project and agent
        branch = ProjectTaskTree(
            project_id=project.project_id,
            agent_id=agent.agent_id,
            git_branch_name="main",
            git_branch_description="Main branch",
            git_branch_status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Verify relationships
        assert branch.project == project
        assert branch.agent == agent
        assert project.task_trees[0] == branch
        assert agent.task_trees[0] == branch
        
        print("✅ Project-Agent relationship test passed")
    
    def test_task_subtask_relationship(self):
        """Test Task-Subtask relationship"""
        # Create a project and branch first
        project = Project(
            name="Test Project",
            description="Test project",
            user_id="test_user",
            metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        branch = ProjectTaskTree(
            project_id=project.project_id,
            git_branch_name="main",
            git_branch_description="Main branch",
            git_branch_status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Create a task
        task = Task(
            git_branch_id=branch.git_branch_id,
            title="Test Task",
            description="Test task for relationships",
            priority="medium",
            status="pending",
            metadata={}
        )
        self.session.add(task)
        self.session.commit()
        
        # Create subtasks
        subtask1 = TaskSubtask(
            task_id=task.task_id,
            title="Subtask 1",
            description="First subtask",
            status="pending",
            priority="high",
            assignees=["user1", "user2"],
            progress_percentage=0
        )
        
        subtask2 = TaskSubtask(
            task_id=task.task_id,
            title="Subtask 2",
            description="Second subtask",
            status="in_progress",
            priority="medium",
            assignees=["user1"],
            progress_percentage=50
        )
        
        self.session.add_all([subtask1, subtask2])
        self.session.commit()
        
        # Verify relationships
        assert len(task.subtasks) == 2
        assert subtask1.task == task
        assert subtask2.task == task
        assert subtask1 in task.subtasks
        assert subtask2 in task.subtasks
        
        print("✅ Task-Subtask relationship test passed")
    
    def test_task_label_many_to_many_relationship(self):
        """Test Task-Label many-to-many relationship"""
        # Create project and branch
        project = Project(
            name="Test Project",
            description="Test project",
            user_id="test_user",
            metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        branch = ProjectTaskTree(
            project_id=project.project_id,
            git_branch_name="main",
            git_branch_description="Main branch",
            git_branch_status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Create tasks
        task1 = Task(
            git_branch_id=branch.git_branch_id,
            title="Task 1",
            description="First task",
            priority="high",
            status="pending",
            metadata={}
        )
        
        task2 = Task(
            git_branch_id=branch.git_branch_id,
            title="Task 2",
            description="Second task",
            priority="medium",
            status="pending",
            metadata={}
        )
        
        self.session.add_all([task1, task2])
        self.session.commit()
        
        # Create labels
        label1 = Label(
            name="bug",
            color="#ff0000",
            description="Bug label"
        )
        
        label2 = Label(
            name="feature",
            color="#00ff00",
            description="Feature label"
        )
        
        self.session.add_all([label1, label2])
        self.session.commit()
        
        # Create many-to-many relationships
        task_label1 = TaskLabel(
            task_id=task1.task_id,
            label_id=label1.label_id
        )
        
        task_label2 = TaskLabel(
            task_id=task1.task_id,
            label_id=label2.label_id
        )
        
        task_label3 = TaskLabel(
            task_id=task2.task_id,
            label_id=label1.label_id
        )
        
        self.session.add_all([task_label1, task_label2, task_label3])
        self.session.commit()
        
        # Verify relationships
        assert len(task1.labels) == 2
        assert len(task2.labels) == 1
        assert len(label1.tasks) == 2
        assert len(label2.tasks) == 1
        
        assert label1 in task1.labels
        assert label2 in task1.labels
        assert label1 in task2.labels
        assert task1 in label1.tasks
        assert task2 in label1.tasks
        assert task1 in label2.tasks
        
        print("✅ Task-Label many-to-many relationship test passed")
    
    def test_context_hierarchy_relationships(self):
        """Test hierarchical context relationships"""
        # Create project
        project = Project(
            name="Test Project",
            description="Test project",
            user_id="test_user",
            metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        # Create branch
        branch = ProjectTaskTree(
            project_id=project.project_id,
            git_branch_name="main",
            git_branch_description="Main branch",
            git_branch_status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Create task
        task = Task(
            git_branch_id=branch.git_branch_id,
            title="Test Task",
            description="Test task",
            priority="medium",
            status="pending",
            metadata={}
        )
        self.session.add(task)
        self.session.commit()
        
        # Create context hierarchy
        global_context = GlobalContext(
            data_title="Global Context",
            data_description="Global level context",
            data_content={"global_setting": "value"}
        )
        
        project_context = ProjectContext(
            project_id=project.project_id,
            data_title="Project Context",
            data_description="Project level context",
            data_content={"project_setting": "value"}
        )
        
        task_context = TaskContext(
            task_id=task.task_id,
            data_title="Task Context",
            data_description="Task level context",
            data_content={"task_setting": "value"}
        )
        
        self.session.add_all([global_context, project_context, task_context])
        self.session.commit()
        
        # Verify relationships
        assert project_context.project == project
        assert task_context.task == task
        assert project.contexts[0] == project_context
        assert task.contexts[0] == task_context
        
        print("✅ Context hierarchy relationships test passed")
    
    def test_cascading_deletes(self):
        """Test cascading deletes work correctly"""
        # Create project with related data
        project = Project(
            name="Test Project",
            description="Test project",
            user_id="test_user",
            metadata={}
        )
        self.session.add(project)
        self.session.commit()
        
        # Create branch
        branch = ProjectTaskTree(
            project_id=project.project_id,
            git_branch_name="main",
            git_branch_description="Main branch",
            git_branch_status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Create task
        task = Task(
            git_branch_id=branch.git_branch_id,
            title="Test Task",
            description="Test task",
            priority="medium",
            status="pending",
            metadata={}
        )
        self.session.add(task)
        self.session.commit()
        
        # Create subtask
        subtask = TaskSubtask(
            task_id=task.task_id,
            title="Test Subtask",
            description="Test subtask",
            status="pending",
            priority="medium",
            assignees=["user1"],
            progress_percentage=0
        )
        self.session.add(subtask)
        self.session.commit()
        
        # Create project context
        project_context = ProjectContext(
            project_id=project.project_id,
            data_title="Project Context",
            data_description="Project level context",
            data_content={"setting": "value"}
        )
        self.session.add(project_context)
        self.session.commit()
        
        # Verify data exists
        assert self.session.query(Project).count() == 1
        assert self.session.query(ProjectTaskTree).count() == 1
        assert self.session.query(Task).count() == 1
        assert self.session.query(TaskSubtask).count() == 1
        assert self.session.query(ProjectContext).count() == 1
        
        # Delete project - should cascade to related data
        self.session.delete(project)
        self.session.commit()
        
        # Verify cascading deletes
        assert self.session.query(Project).count() == 0
        assert self.session.query(ProjectTaskTree).count() == 0
        assert self.session.query(Task).count() == 0
        assert self.session.query(TaskSubtask).count() == 0
        assert self.session.query(ProjectContext).count() == 0
        
        print("✅ Cascading deletes test passed")
    
    def test_foreign_key_constraints(self):
        """Test foreign key constraints are enforced"""
        # Test invalid project_id in ProjectTaskTree
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            invalid_branch = ProjectTaskTree(
                project_id="invalid_project_id",
                git_branch_name="main",
                git_branch_description="Main branch",
                git_branch_status="active"
            )
            self.session.add(invalid_branch)
            self.session.commit()
        
        # Test invalid task_id in TaskSubtask
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            invalid_subtask = TaskSubtask(
                task_id="invalid_task_id",
                title="Invalid Subtask",
                description="This should fail",
                status="pending",
                priority="medium",
                assignees=["user1"],
                progress_percentage=0
            )
            self.session.add(invalid_subtask)
            self.session.commit()
        
        print("✅ Foreign key constraints test passed")
    
    def test_unique_constraints(self):
        """Test unique constraints are enforced"""
        # Test unique project name constraint
        project1 = Project(
            name="Unique Project",
            description="First project",
            user_id="test_user",
            metadata={}
        )
        self.session.add(project1)
        self.session.commit()
        
        # Try to create another project with same name - should fail
        with pytest.raises(Exception):  # Should raise unique constraint error
            project2 = Project(
                name="Unique Project",
                description="Second project",
                user_id="test_user",
                metadata={}
            )
            self.session.add(project2)
            self.session.commit()
        
        # Test unique label name constraint
        label1 = Label(
            name="unique_label",
            color="#ff0000",
            description="First label"
        )
        self.session.add(label1)
        self.session.commit()
        
        # Try to create another label with same name - should fail
        with pytest.raises(Exception):  # Should raise unique constraint error
            label2 = Label(
                name="unique_label",
                color="#00ff00",
                description="Second label"
            )
            self.session.add(label2)
            self.session.commit()
        
        print("✅ Unique constraints test passed")
    
    def test_json_field_relationships(self):
        """Test relationships with JSON fields"""
        # Create project with JSON metadata
        project = Project(
            name="JSON Test Project",
            description="Testing JSON fields",
            user_id="test_user",
            metadata={
                "custom_field": "value",
                "nested": {
                    "key": "nested_value"
                }
            }
        )
        self.session.add(project)
        self.session.commit()
        
        # Create agent with JSON capabilities
        agent = Agent(
            name="json_agent",
            agent_type="coding",
            status="available",
            capabilities=["json_processing", "data_analysis"],
            metadata={
                "version": "1.0",
                "config": {
                    "timeout": 30,
                    "retries": 3
                }
            }
        )
        self.session.add(agent)
        self.session.commit()
        
        # Create relationship
        branch = ProjectTaskTree(
            project_id=project.project_id,
            agent_id=agent.agent_id,
            git_branch_name="json_branch",
            git_branch_description="Branch for JSON testing",
            git_branch_status="active"
        )
        self.session.add(branch)
        self.session.commit()
        
        # Verify JSON data is preserved through relationships
        retrieved_project = self.session.query(Project).filter_by(name="JSON Test Project").first()
        assert retrieved_project.metadata["custom_field"] == "value"
        assert retrieved_project.metadata["nested"]["key"] == "nested_value"
        
        retrieved_agent = self.session.query(Agent).filter_by(name="json_agent").first()
        assert retrieved_agent.capabilities == ["json_processing", "data_analysis"]
        assert retrieved_agent.metadata["version"] == "1.0"
        assert retrieved_agent.metadata["config"]["timeout"] == 30
        
        print("✅ JSON field relationships test passed")


def run_orm_relationships_tests():
    """Run all ORM relationships tests"""
    print("🔗 Running ORM Relationships Integration Tests...\n")
    
    test_instance = TestORMRelationships()
    
    test_methods = [
        'test_project_agent_relationship',
        'test_task_subtask_relationship',
        'test_task_label_many_to_many_relationship',
        'test_context_hierarchy_relationships',
        'test_cascading_deletes',
        'test_foreign_key_constraints',
        'test_unique_constraints',
        'test_json_field_relationships'
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            test_instance.setup_method()
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {method_name} - FAILED: {e}")
        finally:
            test_instance.teardown_method()
    
    print(f"\n📊 ORM Relationships Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    return failed == 0, {"passed": passed, "failed": failed}


if __name__ == "__main__":
    success, results = run_orm_relationships_tests()
    
    if success:
        print("\n🎉 All ORM relationships tests passed!")
        print("✅ All model relationships work correctly")
        print("✅ Foreign key constraints are enforced")
        print("✅ Cascading deletes work properly")
        print("✅ Unique constraints are enforced")
        print("✅ JSON fields work with relationships")
    else:
        print("\n💥 Some ORM relationships tests failed!")
        print("Check the output above for details.")
    
    sys.exit(0 if success else 1)