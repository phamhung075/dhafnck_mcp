"""
Test to verify the GetProject use case returns git_branchs instead of git_branchs
"""
import pytest
from fastmcp.task_management.application.use_cases.get_project import GetProjectUseCase
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch
from datetime import datetime, timezone


class MockProjectRepository:
    """Mock repository for testing"""
    
    def __init__(self):
        # Create a sample project with git branches
        self.project = Project.create(
            name="Test Project",
            description="Test project for git_branchs fix"
        )
        
        # Add a git branch
        git_branch = GitBranch.create(
            name="test-branch",
            description="Test branch",
            project_id=self.project.id
        )
        self.project.git_branchs[git_branch.id] = git_branch
    
    async def find_by_id(self, project_id: str):
        if project_id == self.project.id:
            return self.project
        return None


@pytest.mark.asyncio
async def test_get_project_returns_git_branchs():
    """Test that GetProject returns git_branchs instead of git_branchs"""
    # Arrange
    repo = MockProjectRepository()
    use_case = GetProjectUseCase(repo)
    
    # Act
    result = await use_case.execute(repo.project.id)
    
    # Assert
    assert result["success"] is True
    assert "project" in result
    
    project_data = result["project"]
    
    # Verify correct field name: git_branchs (correct)
    assert "git_branchs" in project_data, "Response should contain 'git_branchs' key"
    
    # Verify the structure of git_branchs
    git_branchs = project_data["git_branchs"]
    assert isinstance(git_branchs, dict)
    
    # Should have one branch
    assert len(git_branchs) == 1
    
    # Get the branch data
    branch_id = list(git_branchs.keys())[0]
    branch_data = git_branchs[branch_id]
    
    # Verify branch structure
    assert "id" in branch_data
    assert "name" in branch_data
    assert "description" in branch_data
    assert "created_at" in branch_data
    assert "task_count" in branch_data
    assert "completed_tasks" in branch_data
    assert "progress" in branch_data
    
    assert branch_data["name"] == "test-branch"
    assert branch_data["description"] == "Test branch"


@pytest.mark.asyncio
async def test_get_project_not_found():
    """Test that GetProject handles non-existent project"""
    # Arrange
    repo = MockProjectRepository()
    use_case = GetProjectUseCase(repo)
    
    # Act
    result = await use_case.execute("non-existent-id")
    
    # Assert
    assert result["success"] is False
    assert "error" in result
    assert "not found" in result["error"].lower()