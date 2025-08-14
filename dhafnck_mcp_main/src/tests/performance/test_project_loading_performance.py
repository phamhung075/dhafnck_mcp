"""
Performance tests for project loading optimization.

This test suite verifies that the N+1 query performance issue has been resolved
by ensuring projects and their branches are loaded in a single API call.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# Import the components we're testing
from fastmcp.task_management.application.use_cases.list_projects import ListProjectsUseCase
from fastmcp.task_management.application.services.project_management_service import ProjectManagementService
from fastmcp.task_management.application.facades.project_application_facade import ProjectApplicationFacade
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch


class TestProjectLoadingPerformance:
    """Test suite for project loading performance improvements"""
    
    def create_mock_project_with_branches(self, project_num: int, branch_count: int = 3) -> Project:
        """Create a mock project with specified number of branches"""
        project = Mock(spec=Project)
        project.id = str(uuid4())
        project.name = f"Project {project_num}"
        project.description = f"Description for project {project_num}"
        project.created_at = Mock(isoformat=Mock(return_value="2025-01-20T10:00:00"))
        project.updated_at = Mock(isoformat=Mock(return_value="2025-01-20T10:00:00"))
        project.registered_agents = []
        project.agent_assignments = []
        project.active_work_sessions = []
        
        # Create mock branches
        branches = []
        for i in range(branch_count):
            branch = Mock(spec=GitBranch)
            branch.id = str(uuid4())
            branch.git_branch_name = f"branch-{i}"
            branch.git_branch_description = f"Branch {i} description"
            branch.created_at = Mock(isoformat=Mock(return_value="2025-01-20T10:00:00"))
            branch.updated_at = Mock(isoformat=Mock(return_value="2025-01-20T10:00:00"))
            branch.status = "active"
            branch.agent_assignments = []
            branches.append(branch)
        
        project.git_branchs = branches
        return project
    
    @pytest.mark.asyncio
    async def test_list_projects_includes_branches_by_default(self):
        """Test that list_projects includes branch data by default"""
        # Arrange
        mock_repo = AsyncMock()
        projects = [self.create_mock_project_with_branches(i, 3) for i in range(5)]
        mock_repo.find_all.return_value = projects
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Act
        result = await use_case.execute()
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 5
        
        # Verify each project has branch data
        for project_data in result["projects"]:
            assert "git_branchs" in project_data
            assert isinstance(project_data["git_branchs"], dict)
            assert len(project_data["git_branchs"]) == 3
    
    @pytest.mark.asyncio
    async def test_list_projects_can_exclude_branches(self):
        """Test that list_projects can exclude branch data when requested"""
        # Arrange
        mock_repo = AsyncMock()
        projects = [self.create_mock_project_with_branches(i, 3) for i in range(5)]
        mock_repo.find_all.return_value = projects
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Act
        result = await use_case.execute(include_branches=False)
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 5
        
        # Verify projects don't have branch data
        for project_data in result["projects"]:
            assert "git_branchs" not in project_data
    
    @pytest.mark.asyncio
    async def test_performance_single_query_for_projects_with_branches(self):
        """Test that fetching projects with branches only makes one database query"""
        # Arrange
        mock_repo = AsyncMock()
        projects = [self.create_mock_project_with_branches(i, 5) for i in range(10)]
        mock_repo.find_all.return_value = projects
        
        service = ProjectManagementService(mock_repo)
        
        # Act
        start_time = time.time()
        result = await service.list_projects(include_branches=True)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 10
        
        # Verify only one database call was made
        mock_repo.find_all.assert_called_once()
        
        # Performance should be fast (< 500ms for backend processing)
        assert elapsed_time < 0.5, f"Query took {elapsed_time:.3f}s, expected < 0.5s"
        
        # Verify all projects have branches
        for project_data in result["projects"]:
            assert "git_branchs" in project_data
            assert len(project_data["git_branchs"]) == 5
    
    @pytest.mark.asyncio
    async def test_facade_includes_branches_by_default(self):
        """Test that the facade layer includes branches by default"""
        # Arrange
        mock_service = AsyncMock()
        mock_service.list_projects.return_value = {
            "success": True,
            "projects": [
                {
                    "id": str(uuid4()),
                    "name": "Test Project",
                    "git_branchs": {
                        str(uuid4()): {"name": "main", "status": "active"}
                    }
                }
            ],
            "count": 1
        }
        
        facade = ProjectApplicationFacade(mock_service)
        
        # Act
        result = await facade.manage_project(action="list")
        
        # Assert
        mock_service.list_projects.assert_called_once_with(include_branches=True)
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self):
        """Test performance with a large number of projects and branches"""
        # Arrange
        mock_repo = AsyncMock()
        # Create 50 projects with 10 branches each
        projects = [self.create_mock_project_with_branches(i, 10) for i in range(50)]
        mock_repo.find_all.return_value = projects
        
        service = ProjectManagementService(mock_repo)
        
        # Act
        start_time = time.time()
        result = await service.list_projects(include_branches=True)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 50
        
        # Even with 50 projects and 500 total branches, should be fast
        assert elapsed_time < 1.0, f"Large dataset query took {elapsed_time:.3f}s, expected < 1.0s"
        
        # Verify data integrity
        total_branches = sum(len(p["git_branchs"]) for p in result["projects"])
        assert total_branches == 500  # 50 projects * 10 branches each
    
    @pytest.mark.asyncio
    async def test_empty_project_list_performance(self):
        """Test performance when no projects exist"""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        
        service = ProjectManagementService(mock_repo)
        
        # Act
        start_time = time.time()
        result = await service.list_projects(include_branches=True)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 0
        assert result["projects"] == []
        assert elapsed_time < 0.1  # Should be very fast for empty list
    
    @pytest.mark.asyncio
    async def test_projects_without_branches_handling(self):
        """Test handling of projects that have no branches"""
        # Arrange
        mock_repo = AsyncMock()
        projects = []
        for i in range(3):
            project = self.create_mock_project_with_branches(i, 0)  # No branches
            projects.append(project)
        mock_repo.find_all.return_value = projects
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Act
        result = await use_case.execute(include_branches=True)
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 3
        
        # Projects without branches should not have git_branchs key
        for project_data in result["projects"]:
            assert "git_branchs" not in project_data or project_data["git_branchs"] == {}