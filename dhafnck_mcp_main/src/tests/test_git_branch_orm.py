"""
Test Suite for ORM Git Branch Repository

Tests for the ORM-based implementation of the Git Branch Repository
using SQLAlchemy models.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch, Project
from fastmcp.task_management.domain.entities.git_branch import GitBranch
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.exceptions.base_exceptions import (
    DatabaseException,
    ResourceNotFoundException,
    ValidationException
)


@pytest.fixture
def mock_session():
    """Mock database session for testing"""
    return Mock()


@pytest.fixture
def repository():
    """Create ORM git branch repository instance for testing"""
    return ORMGitBranchRepository(user_id="test_user")


@pytest.fixture
def sample_git_branch():
    """Create a sample GitBranch for testing"""
    now = datetime.now(timezone.utc)
    git_branch = GitBranch(
        id="branch-123",
        name="feature/auth-system",
        description="Implement user authentication system",
        project_id="project-456",
        created_at=now,
        updated_at=now
    )
    git_branch.assigned_agent_id = "@coding_agent"
    git_branch.priority = Priority.high()
    git_branch.status = TaskStatus.in_progress()
    return git_branch


@pytest.fixture
def sample_model():
    """Create a sample ProjectGitBranch model for testing"""
    now = datetime.now(timezone.utc)
    return ProjectGitBranch(
        id="branch-123",
        name="feature/auth-system",
        description="Implement user authentication system",
        project_id="project-456",
        created_at=now,
        updated_at=now,
        assigned_agent_id="@coding_agent",
        priority="high",
        status="in_progress",
        task_count=5,
        completed_task_count=2,
        model_metadata={}
    )


class TestORMGitBranchRepository:
    
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

    """Test cases for ORM Git Branch Repository"""
    
    def test_init(self):
        """Test repository initialization"""
        repo = ORMGitBranchRepository(user_id="test_user")
        assert repo.user_id == "test_user"
        assert repo.model_class == ProjectGitBranch
    
    def test_model_to_git_branch_conversion(self, repository, sample_model):
        """Test converting ProjectGitBranch model to GitBranch entity"""
        git_branch = repository._model_to_git_branch(sample_model)
        
        assert git_branch.id == sample_model.id
        assert git_branch.name == sample_model.name
        assert git_branch.description == sample_model.description
        assert git_branch.project_id == sample_model.project_id
        assert git_branch.assigned_agent_id == sample_model.assigned_agent_id
        assert str(git_branch.priority) == sample_model.priority
        assert str(git_branch.status) == sample_model.status
        assert git_branch.created_at == sample_model.created_at
        assert git_branch.updated_at == sample_model.updated_at
    
    def test_git_branch_to_model_data_conversion(self, repository, sample_git_branch):
        """Test converting GitBranch entity to model data"""
        model_data = repository._git_branch_to_model_data(sample_git_branch)
        
        assert model_data['id'] == sample_git_branch.id
        assert model_data['name'] == sample_git_branch.name
        assert model_data['description'] == sample_git_branch.description
        assert model_data['project_id'] == sample_git_branch.project_id
        assert model_data['assigned_agent_id'] == sample_git_branch.assigned_agent_id
        assert model_data['priority'] == str(sample_git_branch.priority)
        assert model_data['status'] == str(sample_git_branch.status)
        assert model_data['created_at'] == sample_git_branch.created_at
        assert model_data['updated_at'] == sample_git_branch.updated_at
        assert isinstance(model_data['model_metadata'], dict)
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_save_new_branch(self, mock_get_session, repository, sample_git_branch):
        """Test saving a new git branch"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        await repository.save(sample_git_branch)
        
        # Verify session interactions
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_save_existing_branch(self, mock_get_session, repository, sample_git_branch, sample_model):
        """Test updating an existing git branch"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_model
        
        await repository.save(sample_git_branch)
        
        # Verify session interactions
        mock_session.add.assert_not_called()  # Should not add new, but update existing
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_find_by_id_success(self, mock_get_session, repository, sample_model):
        """Test finding a branch by ID successfully"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_model
        
        result = await repository.find_by_id("project-456", "branch-123")
        
        assert result is not None
        assert result.id == sample_model.id
        assert result.name == sample_model.name
        assert result.project_id == sample_model.project_id
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_find_by_id_not_found(self, mock_get_session, repository):
        """Test finding a branch by ID when not found"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await repository.find_by_id("project-456", "nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_find_by_name_success(self, mock_get_session, repository, sample_model):
        """Test finding a branch by name successfully"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_model
        
        result = await repository.find_by_name("project-456", "feature/auth-system")
        
        assert result is not None
        assert result.name == sample_model.name
        assert result.project_id == sample_model.project_id
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_find_all_by_project(self, mock_get_session, repository, sample_model):
        """Test finding all branches for a project"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_model]
        
        result = await repository.find_all_by_project("project-456")
        
        assert len(result) == 1
        assert result[0].id == sample_model.id
        assert result[0].project_id == sample_model.project_id
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_delete_success(self, mock_get_session, repository):
        """Test deleting a branch successfully"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.delete.return_value = 1
        
        result = await repository.delete("project-456", "branch-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_delete_not_found(self, mock_get_session, repository):
        """Test deleting a branch that doesn't exist"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.delete.return_value = 0
        
        result = await repository.delete("project-456", "nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_exists_true(self, mock_get_session, repository, sample_model):
        """Test checking existence when branch exists"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = sample_model
        
        result = await repository.exists("project-456", "branch-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_exists_false(self, mock_get_session, repository):
        """Test checking existence when branch doesn't exist"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await repository.exists("project-456", "nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_assign_agent_success(self, mock_get_session, repository):
        """Test assigning an agent to a branch successfully"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.update.return_value = 1
        
        result = await repository.assign_agent("project-456", "branch-123", "@coding_agent")
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_unassign_agent_success(self, mock_get_session, repository):
        """Test unassigning an agent from a branch successfully"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.update.return_value = 1
        
        result = await repository.unassign_agent("project-456", "branch-123")
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_count_by_project(self, mock_get_session, repository):
        """Test counting branches by project"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.count.return_value = 3
        
        result = await repository.count_by_project("project-456")
        
        assert result == 3
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_find_by_assigned_agent(self, mock_get_session, repository, sample_model):
        """Test finding branches assigned to a specific agent"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_model]
        
        result = await repository.find_by_assigned_agent("@coding_agent")
        
        assert len(result) == 1
        assert result[0].assigned_agent_id == "@coding_agent"
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_find_by_status(self, mock_get_session, repository, sample_model):
        """Test finding branches by status"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_model]
        
        result = await repository.find_by_status("project-456", "in_progress")
        
        assert len(result) == 1
        assert str(result[0].status) == "in_progress"
    
    @pytest.mark.asyncio
    @patch.object(ORMGitBranchRepository, 'get_db_session')
    async def test_create_branch(self, mock_get_session, repository):
        """Test creating a new branch"""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('uuid.uuid4', return_value=Mock()):
            result = await repository.create_branch(
                "project-456",
                "feature/new-feature",
                "New feature description"
            )
        
        assert result is not None
        assert result.name == "feature/new-feature"
        assert result.description == "New feature description"
        assert result.project_id == "project-456"
    
    @pytest.mark.asyncio
    async def test_create_git_branch_success(self, repository):
        """Test the create_git_branch interface method"""
        with patch.object(repository, 'create_branch') as mock_create:
            mock_git_branch = Mock()
            mock_git_branch.id = "branch-123"
            mock_git_branch.name = "feature/test"
            mock_git_branch.description = "Test branch"
            mock_git_branch.project_id = "project-456"
            mock_git_branch.created_at = datetime.now(timezone.utc)
            mock_git_branch.updated_at = datetime.now(timezone.utc)
            mock_create.return_value = mock_git_branch
            
            result = await repository.create_git_branch(
                "project-456",
                "feature/test",
                "Test branch"
            )
            
            assert result["success"] is True
            assert "git_branch" in result
            assert result["git_branch"]["name"] == "feature/test"
    
    @pytest.mark.asyncio
    async def test_create_git_branch_failure(self, repository):
        """Test the create_git_branch interface method failure"""
        with patch.object(repository, 'create_branch', side_effect=Exception("Database error")):
            result = await repository.create_git_branch(
                "project-456",
                "feature/test",
                "Test branch"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert result["error_code"] == "CREATE_FAILED"
    
    @pytest.mark.asyncio
    async def test_get_git_branch_by_id_success(self, repository, sample_model):
        """Test getting a branch by ID via interface method"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = sample_model
            
            result = await repository.get_git_branch_by_id("branch-123")
            
            assert result["success"] is True
            assert "git_branch" in result
            assert result["git_branch"]["id"] == "branch-123"
    
    @pytest.mark.asyncio
    async def test_get_git_branch_by_id_not_found(self, repository):
        """Test getting a branch by ID when not found"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            result = await repository.get_git_branch_by_id("nonexistent")
            
            assert result["success"] is False
            assert result["error_code"] == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_list_git_branchs_success(self, repository):
        """Test listing git branches"""
        with patch.object(repository, 'find_all_by_project') as mock_find:
            mock_git_branch = Mock()
            mock_git_branch.id = "branch-123"
            mock_git_branch.name = "feature/test"
            mock_git_branch.description = "Test branch"
            mock_git_branch.project_id = "project-456"
            mock_git_branch.created_at = datetime.now(timezone.utc)
            mock_git_branch.updated_at = datetime.now(timezone.utc)
            mock_git_branch.assigned_agent_id = "@coding_agent"
            mock_git_branch.status = TaskStatus.in_progress()
            mock_git_branch.priority = Priority.high()
            mock_find.return_value = [mock_git_branch]
            
            result = await repository.list_git_branchs("project-456")
            
            assert result["success"] is True
            assert "git_branchs" in result
            assert result["count"] == 1
            assert len(result["git_branchs"]) == 1
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_branch_success(self, repository):
        """Test assigning agent to branch via interface method"""
        with patch.object(repository, 'find_by_name') as mock_find, \
             patch.object(repository, 'assign_agent') as mock_assign:
            
            mock_git_branch = Mock()
            mock_git_branch.id = "branch-123"
            mock_find.return_value = mock_git_branch
            mock_assign.return_value = True
            
            result = await repository.assign_agent_to_branch(
                "project-456",
                "@coding_agent",
                "feature/test"
            )
            
            assert result["success"] is True
            assert "assigned to branch" in result["message"]
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_branch_not_found(self, repository):
        """Test assigning agent to non-existent branch"""
        with patch.object(repository, 'find_by_name', return_value=None):
            result = await repository.assign_agent_to_branch(
                "project-456",
                "@coding_agent",
                "nonexistent"
            )
            
            assert result["success"] is False
            assert result["error_code"] == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_get_branch_statistics_success(self, repository, sample_model):
        """Test getting branch statistics"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = sample_model
            
            result = await repository.get_branch_statistics("project-456", "branch-123")
            
            assert "branch_id" in result
            assert "branch_name" in result
            assert "task_count" in result
            assert "progress_percentage" in result
            assert result["branch_id"] == "branch-123"
    
    @pytest.mark.asyncio
    async def test_get_branch_statistics_not_found(self, repository):
        """Test getting statistics for non-existent branch"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            result = await repository.get_branch_statistics("project-456", "nonexistent")
            
            assert "error" in result
            assert result["error"] == "Branch not found"
    
    @pytest.mark.asyncio
    async def test_archive_branch_success(self, repository):
        """Test archiving a branch"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.update.return_value = 1
            
            result = await repository.archive_branch("project-456", "branch-123")
            
            assert result["success"] is True
            assert "archived successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_restore_branch_success(self, repository):
        """Test restoring a branch"""
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.update.return_value = 1
            
            result = await repository.restore_branch("project-456", "branch-123")
            
            assert result["success"] is True
            assert "restored successfully" in result["message"]


class TestErrorHandling:
    
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

    """Test error handling in ORM Git Branch Repository"""
    
    @pytest.mark.asyncio
    async def test_database_exception_handling(self, repository):
        """Test that database exceptions are properly handled"""
        from sqlalchemy.exc import SQLAlchemyError
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.side_effect = SQLAlchemyError("Database connection failed")
            
            with pytest.raises(DatabaseException):
                await repository.find_by_id("project-456", "branch-123")
    
    @pytest.mark.asyncio 
    async def test_conversion_error_handling(self, repository):
        """Test handling of model conversion errors"""
        mock_session = Mock()
        
        # Create a mock model with invalid data that will cause conversion error
        mock_model = Mock()
        mock_model.id = "branch-123"
        mock_model.name = "test-branch"
        mock_model.priority = "invalid_priority"  # This should cause conversion error
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_model]
            
            # Should handle the error gracefully and return empty list
            result = await repository.find_all_by_project("project-456")
            assert len(result) == 0  # Conversion errors should be logged and skipped


class TestIntegrationScenarios:
    
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

    """Integration test scenarios for common workflows"""
    
    @pytest.mark.asyncio
    async def test_full_branch_lifecycle(self, repository):
        """Test complete branch lifecycle: create, update, assign, archive, restore, delete"""
        project_id = "project-456"
        branch_name = "feature/integration-test"
        
        with patch.object(repository, 'get_db_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            # Mock database responses for the lifecycle
            mock_session.query.return_value.filter.return_value.first.return_value = None  # For create
            mock_session.query.return_value.filter.return_value.update.return_value = 1  # For updates
            mock_session.query.return_value.filter.return_value.delete.return_value = 1  # For delete
            
            # 1. Create branch
            with patch('uuid.uuid4', return_value=Mock()):
                create_result = await repository.create_git_branch(
                    project_id,
                    branch_name,
                    "Integration test branch"
                )
                assert create_result["success"] is True
            
            # 2. Assign agent
            with patch.object(repository, 'find_by_name') as mock_find:
                mock_git_branch = Mock()
                mock_git_branch.id = "branch-123"
                mock_find.return_value = mock_git_branch
                
                assign_result = await repository.assign_agent_to_branch(
                    project_id,
                    "@coding_agent",
                    branch_name
                )
                assert assign_result["success"] is True
            
            # 3. Archive branch
            archive_result = await repository.archive_branch(project_id, "branch-123")
            assert archive_result["success"] is True
            
            # 4. Restore branch
            restore_result = await repository.restore_branch(project_id, "branch-123")
            assert restore_result["success"] is True
            
            # 5. Delete branch
            delete_result = await repository.delete_git_branch(project_id, "branch-123")
            assert delete_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])