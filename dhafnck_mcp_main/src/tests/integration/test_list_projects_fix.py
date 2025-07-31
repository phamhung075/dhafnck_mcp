"""
Test to verify the ListProjects use case returns git_branchs_count (correct) and not git_branchs_count (incorrect)
"""
import pytest
from fastmcp.task_management.application.use_cases.list_projects import ListProjectsUseCase
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch
from datetime import datetime, timezone


class MockProjectRepository:
    """Mock repository for testing"""
    
    def __init__(self):
        # Create sample projects with git branches
        self.project1 = Project.create(
            name="Project 1",
            description="First test project"
        )
        
        self.project2 = Project.create(
            name="Project 2", 
            description="Second test project"
        )
        
        # Add git branches to project1
        git_branch1 = GitBranch.create(
            name="main",
            description="Main branch",
            project_id=self.project1.id
        )
        git_branch2 = GitBranch.create(
            name="feature-1",
            description="Feature branch 1",
            project_id=self.project1.id
        )
        self.project1.git_branchs[git_branch1.id] = git_branch1
        self.project1.git_branchs[git_branch2.id] = git_branch2
        
        # Add one git branch to project2
        git_branch3 = GitBranch.create(
            name="main",
            description="Main branch",
            project_id=self.project2.id
        )
        self.project2.git_branchs[git_branch3.id] = git_branch3
        
        self.projects = [self.project1, self.project2]
    
    async def find_all(self):
        return self.projects


@pytest.mark.asyncio
async def test_list_projects_returns_git_branchs_count():
    """Test that ListProjects returns git_branchs_count (correct) and not git_branchs_count (incorrect)"""
    # Arrange
    repo = MockProjectRepository()
    use_case = ListProjectsUseCase(repo)
    
    # Act
    result = await use_case.execute()
    
    # Assert
    assert result["success"] is True
    assert "projects" in result
    assert "count" in result
    
    projects = result["projects"]
    assert len(projects) == 2
    
    # Check each project in the response
    for project_data in projects:
        # Verify correct field name: git_branchs_count (correct)
        assert "git_branchs_count" in project_data, "Response should contain 'git_branchs_count' key"
        
        # Verify other expected fields
        assert "id" in project_data
        assert "name" in project_data
        assert "description" in project_data
        assert "created_at" in project_data
        assert "updated_at" in project_data
        assert "registered_agents_count" in project_data
        assert "active_assignments" in project_data
        assert "active_sessions" in project_data
    
    # Check specific counts
    project1_data = next(p for p in projects if p["name"] == "Project 1")
    project2_data = next(p for p in projects if p["name"] == "Project 2")
    
    assert project1_data["git_branchs_count"] == 2  # Has 2 branches
    assert project2_data["git_branchs_count"] == 1  # Has 1 branch


@pytest.mark.asyncio
async def test_list_projects_empty_repository():
    """Test that ListProjects handles empty repository"""
    # Arrange
    class EmptyMockRepository:
        async def find_all(self):
            return []
    
    repo = EmptyMockRepository()
    use_case = ListProjectsUseCase(repo)
    
    # Act
    result = await use_case.execute()
    
    # Assert
    assert result["success"] is True
    assert result["projects"] == []
    assert result["count"] == 0