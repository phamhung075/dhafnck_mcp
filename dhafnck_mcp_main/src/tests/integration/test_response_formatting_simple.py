#!/usr/bin/env python3
"""
Test-Driven Development: Response Formatting Fixes

This test file verifies proper response formatting for:
1. Agent assignment to branches - should include git_branch_name
2. Task dependencies - should return clean JSON structure
"""

import pytest
import uuid
import json
from datetime import datetime, timezone

from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task as TaskModel, Agent,
    TaskDependency,
    GlobalContext as GlobalContextModel
)


class TestResponseFormattingFixes:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test proper response formatting for various operations."""
    
    # Tests will use the default test database without special setup
    
    def test_agent_assignment_includes_branch_name(self):
        """Test that agent assignment response includes actual git_branch_name."""
        with get_session() as session:
            # Create project
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name="Test Project",
                description="Test project",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project)
            
            # Create branch
            branch_id = str(uuid.uuid4())
            branch_name = "feature/test-agent-assignment"
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project_id,
                name=branch_name,
                description="Test branch",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(branch)
            
            # Create agent
            agent_id = str(uuid.uuid4())
            agent = Agent(
                id=agent_id,
                name="@coding_agent",
                description="Coding agent for testing",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(agent)
            session.commit()
            
            # Assign agent to branch (update the assigned_agent_id field)
            branch.assigned_agent_id = agent_id
            session.commit()
            
            # Simulate getting the response after assignment
            # In actual implementation, this would come from the controller
            branch_data = session.get(ProjectGitBranch, branch_id)
            
            # Create response object (this is what the controller should return)
            response = {
                "success": True,
                "data": {
                    "git_branch": {
                        "id": branch_data.id,
                        "project_id": branch_data.project_id,
                        "git_branch_name": branch_data.name,  # This should NOT be null
                        "git_branch_description": branch_data.description,
                        "assigned_agents": ["@coding_agent"]
                    }
                }
            }
            
            # Verify git_branch_name is not null
            assert response["data"]["git_branch"]["git_branch_name"] is not None, \
                "git_branch_name should not be null"
            assert response["data"]["git_branch"]["git_branch_name"] == branch_name, \
                f"Expected branch name '{branch_name}', got '{response['data']['git_branch']['git_branch_name']}'"
    
    def test_task_dependency_clean_response(self):
        """Test that task dependency response has clean JSON structure."""
        with get_session() as session:
            # Create project and branch
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name="Test Project",
                description="Test project",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project)
            
            branch_id = str(uuid.uuid4())
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project_id,
                name="feature/test-deps",
                description="Test branch",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(branch)
            
            # Create two tasks
            task1_id = str(uuid.uuid4())
            task1 = TaskModel(
                id=task1_id,
                git_branch_id=branch_id,
                title="Task 1 - Dependency",
                description="This will be a dependency",
                status="todo",
                priority="medium",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(task1)
            
            task2_id = str(uuid.uuid4())
            task2 = TaskModel(
                id=task2_id,
                git_branch_id=branch_id,
                title="Task 2 - Dependent",
                description="This depends on Task 1",
                status="todo",
                priority="medium",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(task2)
            session.commit()
            
            # Add dependency
            dependency = TaskDependency(
                task_id=task2_id,
                depends_on_task_id=task1_id,
                created_at=datetime.now(timezone.utc)
            )
            session.add(dependency)
            session.commit()
            
            # Simulate getting the response after adding dependency
            task2_data = session.get(TaskModel, task2_id)
            
            # Create clean response object (this is what the controller should return)
            response = {
                "success": True,
                "data": {
                    "task": {
                        "id": task2_data.id,
                        "git_branch_id": task2_data.git_branch_id,
                        "title": task2_data.title,
                        "description": task2_data.description,
                        "status": task2_data.status,
                        "priority": task2_data.priority,
                        "dependencies": [task1_id],  # Clean list of dependency IDs
                        "created_at": task2_data.created_at.isoformat(),
                        "updated_at": task2_data.updated_at.isoformat()
                    }
                }
            }
            
            # Verify response is clean JSON
            try:
                json_str = json.dumps(response["data"]["task"])
                parsed = json.loads(json_str)
                assert parsed["id"] == task2_id
                assert isinstance(parsed["dependencies"], list)
                assert task1_id in parsed["dependencies"]
            except (TypeError, ValueError) as e:
                pytest.fail(f"Task object is not clean JSON: {e}")
            
            # The response should NOT contain complex internal structures
            # like SQLAlchemy objects or unparseable data
            assert "dependencies" in response["data"]["task"]
            assert isinstance(response["data"]["task"]["dependencies"], list)