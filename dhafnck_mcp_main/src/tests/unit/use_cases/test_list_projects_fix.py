"""Unit tests for list_projects use case - GitBranch iteration fix"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from fastmcp.task_management.application.use_cases.list_projects import ListProjectsUseCase
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch


class TestListProjectsFix:
    """Test suite for the list_projects GitBranch iteration fix"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock project repository"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_repository):
        """Create the list projects use case with mock repository"""
        return ListProjectsUseCase(mock_repository)
    
    @pytest.fixture
    def sample_project_with_branches(self):
        """Create a sample project with git branches as a dictionary"""
        project = Project(
            id="test-project-id",
            name="Test Project",
            description="Test project description",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Add git branches as a dictionary (this is what caused the original issue)
        branch1 = GitBranch(
            id="branch-1-id",
            name="main",
            description="Main branch",
            project_id="test-project-id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        branch2 = GitBranch(
            id="branch-2-id", 
            name="feature/test",
            description="Test feature branch",
            project_id="test-project-id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Store branches as dictionary (matching the actual entity structure)
        project.git_branchs = {
            "branch-1-id": branch1,
            "branch-2-id": branch2
        }
        
        return project
    
    @pytest.mark.asyncio
    async def test_list_projects_iterates_branches_correctly(self, use_case, mock_repository, sample_project_with_branches):
        """Test that list_projects correctly iterates over git_branchs dictionary"""
        # Arrange
        mock_repository.find_all = AsyncMock(return_value=[sample_project_with_branches])
        
        # Act
        result = await use_case.execute(include_branches=True)
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 1
        assert len(result["projects"]) == 1
        
        project_info = result["projects"][0]
        assert "git_branchs" in project_info
        assert len(project_info["git_branchs"]) == 2
        
        # Check that branches are correctly extracted with their IDs as keys
        assert "branch-1-id" in project_info["git_branchs"]
        assert "branch-2-id" in project_info["git_branchs"]
        
        # Verify branch details are correct
        branch1_info = project_info["git_branchs"]["branch-1-id"]
        assert branch1_info["id"] == "branch-1-id"
        assert branch1_info["name"] == "main"
        assert branch1_info["description"] == "Main branch"
        
        branch2_info = project_info["git_branchs"]["branch-2-id"]
        assert branch2_info["id"] == "branch-2-id"
        assert branch2_info["name"] == "feature/test"
        assert branch2_info["description"] == "Test feature branch"
    
    @pytest.mark.asyncio
    async def test_list_projects_handles_empty_branches(self, use_case, mock_repository):
        """Test that list_projects handles projects with no branches"""
        # Arrange
        project = Project(
            id="test-project-id",
            name="Test Project",
            description="Test project description",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        project.git_branchs = {}  # Empty dictionary
        
        mock_repository.find_all = AsyncMock(return_value=[project])
        
        # Act
        result = await use_case.execute(include_branches=True)
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 1
        project_info = result["projects"][0]
        assert "git_branchs" not in project_info  # Should not include empty branches
    
    @pytest.mark.asyncio
    async def test_list_projects_without_including_branches(self, use_case, mock_repository, sample_project_with_branches):
        """Test that list_projects can exclude branch information when requested"""
        # Arrange
        mock_repository.find_all = AsyncMock(return_value=[sample_project_with_branches])
        
        # Act
        result = await use_case.execute(include_branches=False)
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 1
        project_info = result["projects"][0]
        assert "git_branchs" not in project_info  # Branches should not be included
        assert project_info["git_branchs_count"] == 2  # But count should still be there
    
    @pytest.mark.asyncio
    async def test_list_projects_multiple_projects_with_branches(self, use_case, mock_repository):
        """Test listing multiple projects with branches"""
        # Arrange
        project1 = Project(
            id="project-1",
            name="Project 1",
            description="First project",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        branch1 = GitBranch(
            id="p1-branch-1",
            name="main",
            description="Main branch",
            project_id="project-1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        project1.git_branchs = {"p1-branch-1": branch1}
        
        project2 = Project(
            id="project-2",
            name="Project 2",
            description="Second project",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        branch2 = GitBranch(
            id="p2-branch-1",
            name="develop",
            description="Development branch",
            project_id="project-2",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        project2.git_branchs = {"p2-branch-1": branch2}
        
        mock_repository.find_all = AsyncMock(return_value=[project1, project2])
        
        # Act
        result = await use_case.execute(include_branches=True)
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 2
        
        # Check both projects have their branches correctly listed
        for project_info in result["projects"]:
            assert "git_branchs" in project_info
            assert len(project_info["git_branchs"]) == 1
            
            # Each project should have its own branch
            if project_info["id"] == "project-1":
                assert "p1-branch-1" in project_info["git_branchs"]
            elif project_info["id"] == "project-2":
                assert "p2-branch-1" in project_info["git_branchs"]