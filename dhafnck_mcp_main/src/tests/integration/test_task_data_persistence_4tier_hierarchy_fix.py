"""
TDD Test: Fix Task Data Persistence Issue with 4-Tier Context Hierarchy

This test reproduces the exact issue causing task data loss:
1. Tasks are created successfully 
2. When retrieved, they cause AttributeError
3. The 4-tier context hierarchy (Global → Project → Branch → Task) is disrupted

Key Focus Areas:
- Task creation and persistence
- 4-tier context hierarchy integrity
- Foreign key relationships
- Task retrieval without AttributeError
- Context inheritance chain validation
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Optional

from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task, TaskSubtask, GlobalContext, 
    ProjectContext, BranchContext, TaskContext
)
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ORMProjectRepository
from fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestTaskDataPersistence4TierHierarchyFix:
    """TDD tests for fixing task data persistence with 4-tier context hierarchy."""
    
    def test_4tier_context_hierarchy_exists_and_intact(self, module_test_db):
        """
        Test that the 4-tier context hierarchy exists and is properly configured.
        
        This tests the foundation: Global → Project → Branch → Task
        """
        session = get_session()
        try:
            # Test 1: Check that all 4 context tables exist
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()
            
            required_tables = [
                'global_contexts', 'project_contexts', 'branch_contexts', 'task_contexts',
                'projects', 'project_git_branchs', 'tasks'
            ]
            
            for table in required_tables:
                assert table in tables, f"Required table {table} not found in database"
            
            # Test 2: Check foreign key relationships exist
            task_fks = inspector.get_foreign_keys('tasks')
            branch_fks = inspector.get_foreign_keys('project_git_branchs')
            
            # Tasks should have FK to project_git_branchs
            task_fk_columns = [fk['constrained_columns'][0] for fk in task_fks]
            assert 'git_branch_id' in task_fk_columns, "Task table missing git_branch_id FK"
            
            # Branches should have FK to projects
            branch_fk_columns = [fk['constrained_columns'][0] for fk in branch_fks]
            assert 'project_id' in branch_fk_columns, "Branch table missing project_id FK"
            
            # Test 3: Check context foreign keys
            context_tables = ['project_contexts', 'branch_contexts', 'task_contexts']
            for table in context_tables:
                if table in tables:
                    fks = inspector.get_foreign_keys(table)
                    assert len(fks) > 0, f"Context table {table} has no foreign keys"
            
            print("✅ 4-tier context hierarchy is properly configured")
            
        finally:
            session.close()
    
    def test_task_creation_with_full_hierarchy_succeeds(self, module_test_db):
        """
        Test that task creation works with the full 4-tier hierarchy.
        
        This tests the creation flow: Global → Project → Branch → Task
        """
        session = get_session()
        try:
            # Create project
            project = Project(
                id=str(uuid4()),
                name="Test Project for 4-Tier Hierarchy",
                description="Testing 4-tier context hierarchy",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            # Create git branch
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-hierarchy",
                description="Test branch for hierarchy testing"
            )
            session.add(git_branch)
            session.flush()
            
            # Create task with proper foreign keys
            task = Task(
                id=str(uuid4()),
                title="Test Task with 4-Tier Hierarchy",
                description="This task tests the 4-tier hierarchy",
                git_branch_id=git_branch.id,
                status="todo",
                priority="high"
            )
            session.add(task)
            session.flush()
            
            # Verify the hierarchy chain exists
            assert task.git_branch_id == git_branch.id
            assert git_branch.project_id == project.id
            
            # Verify relationships work
            retrieved_task = session.query(Task).filter_by(id=task.id).first()
            assert retrieved_task is not None
            assert retrieved_task.git_branch.id == git_branch.id
            assert retrieved_task.git_branch.project.id == project.id
            
            session.commit()
            print("✅ Task creation with full hierarchy succeeds")
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def test_task_retrieval_without_attributeerror(self, module_test_db):
        """
        Test that task retrieval works without causing AttributeError.
        
        This is the core issue we're fixing - tasks can be created but not retrieved.
        """
        session = get_session()
        try:
            # Create the hierarchy
            project = Project(
                id=str(uuid4()),
                name="Test Project for Retrieval",
                description="Testing task retrieval",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-retrieval",
                description="Test branch for retrieval testing"
            )
            session.add(git_branch)
            session.flush()
            
            # Create task
            task = Task(
                id=str(uuid4()),
                title="Test Task for Retrieval",
                description="This task tests retrieval without AttributeError",
                git_branch_id=git_branch.id,
                status="todo",
                priority="medium"
            )
            session.add(task)
            session.commit()
            
            # NOW THE CRITICAL TEST: Retrieve the task
            # This should NOT cause AttributeError
            retrieved_task = session.query(Task).filter_by(id=task.id).first()
            
            assert retrieved_task is not None
            assert retrieved_task.id == task.id
            assert retrieved_task.title == task.title
            assert retrieved_task.git_branch_id == git_branch.id
            
            # Test accessing the relationship
            assert retrieved_task.git_branch is not None
            assert retrieved_task.git_branch.id == git_branch.id
            
            # Test accessing subtasks (this often causes the AttributeError)
            assert hasattr(retrieved_task, 'subtasks')
            assert isinstance(retrieved_task.subtasks, list)
            
            print("✅ Task retrieval works without AttributeError")
            
        finally:
            session.close()
    
    def test_task_repository_list_tasks_works(self, module_test_db):
        """
        Test that the task repository can list tasks without AttributeError.
        
        This reproduces the exact scenario from the MCP tools testing.
        """
        session = get_session()
        try:
            # Create the hierarchy
            project = Project(
                id=str(uuid4()),
                name="Test Project for Repository",
                description="Testing repository operations",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-repository",
                description="Test branch for repository testing"
            )
            session.add(git_branch)
            session.flush()
            
            # Create multiple tasks
            task1 = Task(
                id=str(uuid4()),
                title="First Repository Test Task",
                description="First task for repository testing",
                git_branch_id=git_branch.id,
                status="todo",
                priority="high"
            )
            
            task2 = Task(
                id=str(uuid4()),
                title="Second Repository Test Task",
                description="Second task for repository testing",
                git_branch_id=git_branch.id,
                status="in_progress",
                priority="medium"
            )
            
            session.add_all([task1, task2])
            session.commit()
            
            # Now use the repository to list tasks
            # This should NOT cause AttributeError
            task_repo = ORMTaskRepository(git_branch_id=git_branch.id)
            
            try:
                task_list = task_repo.list_tasks()
                
                # Verify tasks were retrieved
                assert isinstance(task_list, list)
                assert len(task_list) >= 2
                
                # Find our created tasks
                created_tasks = [t for t in task_list if t.id.value in [task1.id, task2.id]]
                assert len(created_tasks) == 2
                
                # Verify each task has correct structure
                for task in created_tasks:
                    assert hasattr(task, 'subtasks')
                    assert isinstance(task.subtasks, list)
                    
                print("✅ Task repository list_tasks works correctly")
                
            except AttributeError as e:
                pytest.fail(f"AttributeError occurred in task repository: {e}")
                
        finally:
            session.close()
    
    def test_task_with_subtasks_retrieval_works(self, module_test_db):
        """
        Test that tasks with subtasks can be retrieved without AttributeError.
        
        This tests the subtask relationship specifically.
        """
        session = get_session()
        try:
            # Create the hierarchy
            project = Project(
                id=str(uuid4()),
                name="Test Project for Subtasks",
                description="Testing subtask relationships",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-subtasks",
                description="Test branch for subtask testing"
            )
            session.add(git_branch)
            session.flush()
            
            # Create task
            task = Task(
                id=str(uuid4()),
                title="Task with Subtasks",
                description="This task has subtasks",
                git_branch_id=git_branch.id,
                status="todo",
                priority="high"
            )
            session.add(task)
            session.flush()
            
            # Create subtasks
            subtask1 = TaskSubtask(
                id=str(uuid4()),
                title="First Subtask",
                description="First subtask",
                task_id=task.id,
                status="todo",
                priority="medium"
            )
            
            subtask2 = TaskSubtask(
                id=str(uuid4()),
                title="Second Subtask",
                description="Second subtask",
                task_id=task.id,
                status="in_progress",
                priority="high"
            )
            
            session.add_all([subtask1, subtask2])
            session.commit()
            
            # Retrieve the task with subtasks
            retrieved_task = session.query(Task).filter_by(id=task.id).first()
            
            assert retrieved_task is not None
            assert len(retrieved_task.subtasks) == 2
            
            # Verify subtasks are properly loaded
            for subtask in retrieved_task.subtasks:
                assert subtask.task_id == task.id
                assert subtask.title in ["First Subtask", "Second Subtask"]
            
            print("✅ Task with subtasks retrieval works correctly")
            
        finally:
            session.close()
    
    def test_4tier_context_creation_and_retrieval(self, module_test_db):
        """
        Test that 4-tier context creation and retrieval works.
        
        This tests the context hierarchy specifically.
        """
        session = get_session()
        try:
            # Create the full hierarchy with contexts
            project = Project(
                id=str(uuid4()),
                name="Test Project for Context Hierarchy",
                description="Testing context hierarchy",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-context",
                description="Test branch for context testing"
            )
            session.add(git_branch)
            session.flush()
            
            task = Task(
                id=str(uuid4()),
                title="Task for Context Testing",
                description="This task tests context hierarchy",
                git_branch_id=git_branch.id,
                status="todo",
                priority="high"
            )
            session.add(task)
            session.flush()
            
            # Create contexts at each level
            global_context = GlobalContext(
                id="global_singleton",
                autonomous_rules={"global_setting": "test_value"}
            )
            session.merge(global_context)
            
            project_context = ProjectContext(
                project_id=project.id,
                parent_global_id="global_singleton",
                team_preferences={"project_setting": "test_value"}
            )
            session.add(project_context)
            
            branch_context = BranchContext(
                branch_id=git_branch.id,
                parent_project_id=project.id,
                parent_project_context_id=project.id,
                branch_workflow={"branch_setting": "test_value"}
            )
            session.add(branch_context)
            
            task_context = TaskContext(
                task_id=task.id,
                parent_branch_id=git_branch.id,
                parent_branch_context_id=git_branch.id,
                task_data={"task_setting": "test_value"}
            )
            session.add(task_context)
            
            session.commit()
            
            # Test context retrieval
            context_repo = ORMHierarchicalContextRepository()
            
            # Test resolving task context (should inherit from all levels)
            resolved_context = context_repo.resolve_context("task", task.id)
            
            assert resolved_context is not None
            assert isinstance(resolved_context, dict)
            
            # Check that context contains data from all levels
            # This is the actual test for the 4-tier hierarchy
            assert "task_data" in resolved_context
            assert "branch_workflow" in resolved_context
            assert "team_preferences" in resolved_context
            assert "autonomous_rules" in resolved_context
            
            # Verify specific values
            assert resolved_context["task_data"]["task_setting"] == "test_value"
            assert resolved_context["branch_workflow"]["branch_setting"] == "test_value"
            assert resolved_context["team_preferences"]["project_setting"] == "test_value"
            assert resolved_context["autonomous_rules"]["global_setting"] == "test_value"
            
            print("✅ 4-tier context creation and retrieval works correctly")
            
        finally:
            session.close()
    
    def test_mcp_tools_task_creation_and_retrieval_integration(self, module_test_db):
        """
        Test the complete MCP tools integration scenario.
        
        This reproduces the exact scenario from the MCP tools testing that failed.
        """
        # This test simulates the exact MCP tools workflow
        session = get_session()
        try:
            # Step 1: Create project (like in MCP tools test)
            project = Project(
                id=str(uuid4()),
                name="test-project-mcp-integration",
                description="Test project for MCP integration",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            # Step 2: Create git branch (like in MCP tools test)
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-mcp-integration",
                description="Test branch for MCP integration"
            )
            session.add(git_branch)
            session.commit()
            
            # Step 3: Create tasks using repository (like MCP tools do)
            task_repo = ORMTaskRepository(git_branch_id=git_branch.id)
            
            # Create multiple tasks
            task1 = task_repo.create_task(
                title="Implement User Authentication System",
                description="Create a comprehensive user authentication system",
                priority="high"
            )
            
            task2 = task_repo.create_task(
                title="Build User Dashboard Interface",
                description="Create a responsive user dashboard",
                priority="medium"
            )
            
            task3 = task_repo.create_task(
                title="Implement API Rate Limiting",
                description="Add rate limiting middleware",
                priority="medium"
            )
            
            # Step 4: Create subtasks (like in MCP tools test)
            subtask_repo = ORMSubtaskRepository()
            
            subtask1 = Subtask(
                id=SubtaskId(str(uuid4())),
                title="Design JWT Token Structure",
                description="Design the JWT token payload structure",
                parent_task_id=task1.id,
                status=TaskStatus.todo(),
                priority=Priority.high()
            )
            
            subtask2 = Subtask(
                id=SubtaskId(str(uuid4())),
                title="Implement Password Hashing",
                description="Implement bcrypt password hashing",
                parent_task_id=task1.id,
                status=TaskStatus.todo(),
                priority=Priority.high()
            )
            
            subtask_repo.save(subtask1)
            subtask_repo.save(subtask2)
            
            # Step 5: Try to list tasks (this is where the AttributeError occurred)
            try:
                task_list = task_repo.list_tasks()
                
                # Verify we can retrieve tasks
                assert isinstance(task_list, list)
                assert len(task_list) >= 3
                
                # Find our created tasks
                created_tasks = [t for t in task_list if t.id in [task1.id, task2.id, task3.id]]
                assert len(created_tasks) == 3
                
                # Verify tasks have correct structure
                for task in created_tasks:
                    assert hasattr(task, 'subtasks')
                    assert isinstance(task.subtasks, list)
                    
                    # Find the task with subtasks
                    if task.id == task1.id:
                        assert len(task.subtasks) == 2
                        # Verify subtasks are string IDs
                        for subtask_id in task.subtasks:
                            assert isinstance(subtask_id, str)
                    else:
                        assert len(task.subtasks) == 0
                
                print("✅ MCP tools integration scenario works correctly")
                
            except AttributeError as e:
                pytest.fail(f"AttributeError in MCP tools integration: {e}")
                
        finally:
            session.close()
    
    def test_task_count_consistency_in_git_branch(self, module_test_db):
        """
        Test that git branch task_count is consistent with actual tasks.
        
        This tests the branch statistics that were showing 0 tasks.
        """
        session = get_session()
        try:
            # Create project and branch
            project = Project(
                id=str(uuid4()),
                name="Test Project for Task Count",
                description="Testing task count consistency",
                user_id="test_user"
            )
            session.add(project)
            session.flush()
            
            git_branch = ProjectGitBranch(
                id=str(uuid4()),
                project_id=project.id,
                name="feature/test-task-count",
                description="Test branch for task count testing"
            )
            session.add(git_branch)
            session.flush()
            
            # Create tasks
            task1 = Task(
                id=str(uuid4()),
                title="Task 1 for Count Test",
                description="First task for count testing",
                git_branch_id=git_branch.id,
                status="todo",
                priority="high"
            )
            
            task2 = Task(
                id=str(uuid4()),
                title="Task 2 for Count Test",
                description="Second task for count testing",
                git_branch_id=git_branch.id,
                status="done",
                priority="medium"
            )
            
            session.add_all([task1, task2])
            session.commit()
            
            # Verify task count
            actual_task_count = session.query(Task).filter_by(git_branch_id=git_branch.id).count()
            completed_task_count = session.query(Task).filter_by(
                git_branch_id=git_branch.id, 
                status="done"
            ).count()
            
            assert actual_task_count == 2
            assert completed_task_count == 1
            
            # Update branch statistics
            git_branch.task_count = actual_task_count
            git_branch.completed_task_count = completed_task_count
            session.commit()
            
            # Verify updated statistics
            updated_branch = session.query(ProjectGitBranch).filter_by(id=git_branch.id).first()
            assert updated_branch.task_count == 2
            assert updated_branch.completed_task_count == 1
            
            print("✅ Task count consistency works correctly")
            
        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])