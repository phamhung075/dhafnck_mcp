"""
Integration test for V2 API endpoint git branch filtering fix.

This test verifies that the /api/v2/tasks endpoint properly accepts and processes
git_branch_id parameter for branch-specific task filtering.
"""

import pytest
import uuid
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from fastmcp.server.routes.user_scoped_task_routes import list_tasks, UserScopedRepositoryFactory
from fastmcp.auth.domain.entities.user import User
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository as TaskRepository


class TestV2APIGitBranchFiltering:
    """Test V2 API endpoint git branch filtering functionality"""
    
    def test_list_tasks_endpoint_signature_includes_git_branch_id(self):
        """Test that the list_tasks endpoint accepts git_branch_id parameter"""
        import inspect
        sig = inspect.signature(list_tasks)
        
        # Verify git_branch_id parameter exists with correct type and default
        assert 'git_branch_id' in sig.parameters
        param = sig.parameters['git_branch_id']
        assert param.default is None
        # Check for Optional[str] annotation
        annotation_str = str(param.annotation)
        assert 'Optional[str]' in annotation_str or 'str | None' in annotation_str
    
    def test_user_scoped_repository_factory_accepts_git_branch_id(self):
        """Test that UserScopedRepositoryFactory.create_task_repository accepts git_branch_id"""
        import inspect
        sig = inspect.signature(UserScopedRepositoryFactory.create_task_repository)
        
        # Verify git_branch_id parameter exists
        assert 'git_branch_id' in sig.parameters
        param = sig.parameters['git_branch_id']
        assert param.default is None
        
        # Test factory creates repository with git_branch_id
        mock_session = Mock(spec=Session)
        user_id = "test-user-123"
        branch_id = str(uuid.uuid4())
        
        repo = UserScopedRepositoryFactory.create_task_repository(
            session=mock_session,
            user_id=user_id,
            git_branch_id=branch_id
        )
        
        # Verify repository has git_branch_id set
        assert repo.git_branch_id == branch_id
    
    def test_list_tasks_request_construction_with_git_branch_id(self):
        """Test that ListTasksRequest includes git_branch_id correctly"""
        branch_id = str(uuid.uuid4())
        
        # Test request construction with all parameters
        request = ListTasksRequest(
            git_branch_id=branch_id,
            status="in_progress",
            priority="high",
            limit=25
        )
        
        # Verify all parameters are set
        assert request.git_branch_id == branch_id
        assert request.status == "in_progress"
        assert request.priority == "high"
        assert request.limit == 25
    
    @patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory')
    @patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade')
    def test_list_tasks_endpoint_passes_git_branch_id_to_repository(self, mock_facade_class, mock_factory):
        """Test that the endpoint properly passes git_branch_id to repository factory"""
        # Setup mocks
        mock_repo = Mock()
        mock_factory.create_task_repository.return_value = mock_repo
        
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        mock_facade.list_tasks.return_value = {"success": True, "tasks": []}
        
        mock_user = User(id="test-user", email="test@example.com")
        mock_db = Mock(spec=Session)
        
        # Test parameters
        branch_id = str(uuid.uuid4())
        task_status = "todo"
        priority = "high"
        limit = 50
        
        # Call the endpoint function directly
        with patch('fastmcp.server.routes.user_scoped_task_routes.get_current_user', return_value=mock_user):
            with patch('fastmcp.server.routes.user_scoped_task_routes.get_db', return_value=mock_db):
                # This should work with our updated signature
                from fastmcp.server.routes.user_scoped_task_routes import list_tasks
                
                # Create an async function to test
                async def test_call():
                    return await list_tasks(
                        task_status=task_status,
                        priority=priority,
                        git_branch_id=branch_id,
                        limit=limit,
                        current_user=mock_user,
                        db=mock_db
                    )
                
                # Run the async call
                result = asyncio.run(test_call())
        
        # Verify factory was called with git_branch_id
        mock_factory.create_task_repository.assert_called_once_with(
            mock_db, mock_user.id, branch_id
        )
        
        # Verify facade.list_tasks was called with correct request
        facade_call_args = mock_facade.list_tasks.call_args[0][0]
        assert isinstance(facade_call_args, ListTasksRequest)
        assert facade_call_args.git_branch_id == branch_id
        assert facade_call_args.status == task_status
        assert facade_call_args.priority == priority
        assert facade_call_args.limit == limit
    
    def test_repository_constructor_accepts_git_branch_id(self):
        """Test that TaskRepository constructor accepts git_branch_id parameter"""
        mock_session = Mock(spec=Session)
        branch_id = str(uuid.uuid4())
        
        # Create repository with git_branch_id
        repo = TaskRepository(session=mock_session, git_branch_id=branch_id)
        
        # Verify git_branch_id is stored
        assert repo.git_branch_id == branch_id
    
    def test_repository_filters_by_git_branch_id_in_list_tasks(self):
        """Test that repository uses git_branch_id in query filters"""
        # This test verifies the filtering logic exists in the repository
        mock_session = Mock(spec=Session)
        branch_id = str(uuid.uuid4())
        user_id = "test-user"
        
        # Create repository with git_branch_id
        repo = TaskRepository(session=mock_session, git_branch_id=branch_id, user_id=user_id)
        
        # Verify git_branch_id is set for filtering
        assert repo.git_branch_id == branch_id
        
        # The actual filtering logic is tested in repository unit tests
        # Here we just verify the setup is correct
    
    def test_api_endpoint_docstring_documents_git_branch_id(self):
        """Test that the API endpoint docstring mentions git_branch_id parameter"""
        docstring = list_tasks.__doc__
        assert docstring is not None
        assert 'git_branch_id' in docstring.lower()
        assert 'branch' in docstring.lower()


class TestV2APIGitBranchFilteringEndToEnd:
    """End-to-end integration tests for V2 API git branch filtering"""
    
    @pytest.fixture
    def mock_user(self):
        return User(id="test-user-789", email="test@example.com")
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=Session)
    
    def test_v2_api_endpoint_mock_integration(self):
        """Test the V2 API endpoint logic with mocks"""
        # This test verifies the fix without requiring FastAPI TestClient
        mock_user = User(id="test-user-api", email="api-test@example.com")
        mock_session = Mock(spec=Session)
        branch_id = "test-branch-123"
        
        # Mock the repository and facade
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as mock_factory:
            with patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as mock_facade_class:
                # Setup mock returns
                mock_repo = Mock()
                mock_factory.create_task_repository.return_value = mock_repo
                
                mock_facade = Mock()
                mock_facade_class.return_value = mock_facade
                mock_facade.list_tasks.return_value = {
                    "success": True,
                    "tasks": [
                        {
                            "id": str(uuid.uuid4()),
                            "title": "Test Task",
                            "status": "todo",
                            "git_branch_id": branch_id
                        }
                    ]
                }
                
                # Test the endpoint function directly
                async def run_test():
                    return await list_tasks(
                        task_status="todo",
                        priority="high", 
                        git_branch_id=branch_id,
                        limit=50,
                        current_user=mock_user,
                        db=mock_session
                    )
                
                result = asyncio.run(run_test())
                
                # Verify repository was created with git_branch_id
                mock_factory.create_task_repository.assert_called_once_with(
                    mock_session, mock_user.id, branch_id
                )
                
                # Verify facade.list_tasks was called with correct request
                facade_call_args = mock_facade.list_tasks.call_args[0][0]
                assert isinstance(facade_call_args, ListTasksRequest)
                assert facade_call_args.git_branch_id == branch_id
    
    def test_git_branch_id_optional_parameter_behavior(self):
        """Test that git_branch_id parameter is truly optional"""
        # Test without git_branch_id
        request_without_branch = ListTasksRequest(
            git_branch_id=None,
            status="todo",
            priority="high",
            limit=100
        )
        
        assert request_without_branch.git_branch_id is None
        assert request_without_branch.status == "todo"
        assert request_without_branch.priority == "high"
        
        # Test with git_branch_id
        branch_id = str(uuid.uuid4())
        request_with_branch = ListTasksRequest(
            git_branch_id=branch_id,
            status="in_progress",
            priority="medium",
            limit=50
        )
        
        assert request_with_branch.git_branch_id == branch_id
        assert request_with_branch.status == "in_progress"
        assert request_with_branch.priority == "medium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])