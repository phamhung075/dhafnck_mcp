"""Integration test for dependency visibility fix via MCP controller."""
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.database.models import (
    Project,
    ProjectGitBranch,
    Task
)
from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.application.services.context_application_service import ContextApplicationService
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade


@pytest.fixture
def db_session():
    """Get a database session for testing."""
    db_config = get_db_config()
    with db_config.get_session() as session:
        yield session


@pytest.fixture
def setup_test_data(db_session: Session):
    """Set up test project, branch, and tasks."""
    # Create project
    project = Project(
        id=str(uuid.uuid4()),
        name="Test Project",
        description="Project for testing dependencies",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(project)
    
    # Create branch
    branch = ProjectGitBranch(
        id=str(uuid.uuid4()),
        name="test-branch",
        description="Branch for testing",
        project_id=project.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(branch)
    
    # Create tasks
    task1 = Task(
        id=str(uuid.uuid4()),
        title="Main Task",
        description="A task that will have dependencies",
        git_branch_id=branch.id,
        status="todo",
        priority="medium",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(task1)
    
    task2 = Task(
        id=str(uuid.uuid4()),
        title="Dependency Task",
        description="A task that others depend on",
        git_branch_id=branch.id,
        status="todo",
        priority="high",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(task2)
    
    db_session.commit()
    
    return {
        "project": project,
        "branch": branch,
        "task1": task1,
        "task2": task2
    }


@pytest.fixture
def task_controller(db_session: Session):
    """Create TaskMCPController with real repositories."""
    # Create repositories
    task_repository = ORMTaskRepository(db_session)
    git_branch_repository = ORMGitBranchRepository(db_session)
    subtask_repository = ORMSubtaskRepository(db_session)
    context_service = ContextApplicationService(db_session)
    
    # Create facade
    facade = TaskApplicationFacade(
        task_repository=task_repository,
        subtask_repository=subtask_repository,
        context_service=context_service,
        git_branch_repository=git_branch_repository
    )
    
    # Create controller
    controller = TaskMCPController()
    controller._task_facade = facade  # Inject our facade
    
    return controller


class TestDependencyVisibilityMCPIntegration:
    """Test that dependencies are visible immediately after adding them via MCP."""
    
    def test_add_dependency_visible_in_mcp_response(self, task_controller, setup_test_data):
        """Test that dependencies show up immediately in MCP response after adding."""
        task1 = setup_test_data["task1"]
        task2 = setup_test_data["task2"]
        
        # Add dependency via MCP controller
        result = task_controller.manage_task(
            action="add_dependency",
            task_id=task1.id,
            dependency_id=task2.id
        )
        
        # Assert: Operation succeeded
        assert result["success"] is True
        assert "task" in result
        assert result["task"] is not None
        
        # Assert: Dependencies are visible in response
        task_dict = result["task"]
        assert "dependencies" in task_dict
        assert len(task_dict["dependencies"]) == 1
        assert task_dict["dependencies"][0] == task2.id
        
        # Verify by getting the task again
        get_result = task_controller.manage_task(
            action="get",
            task_id=task1.id
        )
        
        assert get_result["success"] is True
        assert "task" in get_result
        task_data = get_result["task"]["task"]
        assert len(task_data["dependencies"]) == 1
        assert task_data["dependencies"][0] == task2.id
    
    def test_multiple_dependencies_all_visible(self, task_controller, setup_test_data, db_session):
        """Test that multiple dependencies are all visible after adding."""
        task1 = setup_test_data["task1"]
        task2 = setup_test_data["task2"]
        branch = setup_test_data["branch"]
        
        # Create a third task
        task3 = Task(
            id=str(uuid.uuid4()),
            title="Another Dependency",
            description="Another task to depend on",
            git_branch_id=branch.id,
            status="todo",
            priority="medium",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(task3)
        db_session.commit()
        
        # Add first dependency
        result1 = task_controller.manage_task(
            action="add_dependency",
            task_id=task1.id,
            dependency_id=task2.id
        )
        assert result1["success"] is True
        assert len(result1["task"]["dependencies"]) == 1
        
        # Add second dependency
        result2 = task_controller.manage_task(
            action="add_dependency",
            task_id=task1.id,
            dependency_id=task3.id
        )
        assert result2["success"] is True
        assert len(result2["task"]["dependencies"]) == 2
        assert task2.id in result2["task"]["dependencies"]
        assert task3.id in result2["task"]["dependencies"]
    
    def test_remove_dependency_updates_response(self, task_controller, setup_test_data, db_session):
        """Test that removing dependencies updates the response immediately."""
        task1 = setup_test_data["task1"]
        task2 = setup_test_data["task2"]
        branch = setup_test_data["branch"]
        
        # Create another task
        task3 = Task(
            id=str(uuid.uuid4()),
            title="Another Task",
            description="Another task",
            git_branch_id=branch.id,
            status="todo",
            priority="medium",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(task3)
        db_session.commit()
        
        # Add two dependencies
        task_controller.manage_task(
            action="add_dependency",
            task_id=task1.id,
            dependency_id=task2.id
        )
        task_controller.manage_task(
            action="add_dependency",
            task_id=task1.id,
            dependency_id=task3.id
        )
        
        # Remove one dependency
        result = task_controller.manage_task(
            action="remove_dependency",
            task_id=task1.id,
            dependency_id=task2.id
        )
        
        # Assert: Operation succeeded and shows updated dependencies
        assert result["success"] is True
        assert "task" in result
        task_dict = result["task"]
        assert len(task_dict["dependencies"]) == 1
        assert task_dict["dependencies"][0] == task3.id
        assert task2.id not in task_dict["dependencies"]