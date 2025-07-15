"""
TDD Test for Delegation Service Initialization Fix

This test ensures that the delegation service is properly initialized with the repository
to avoid NoneType errors during delegation operations.
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dhafnck_mcp_main', 'src'))

from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
from fastmcp.task_management.application.services.context_delegation_service import ContextDelegationService
from fastmcp.task_management.infrastructure.repositories.sqlite.hierarchical_context_repository import SQLiteHierarchicalContextRepository


class TestDelegationServiceInitializationFix:
    """Test delegation service initialization with repository injection"""
    
    def test_delegation_service_should_be_initialized_with_repository(self):
        """Test that delegation service receives repository during initialization"""
        # Create a mock repository
        mock_repository = Mock(spec=SQLiteHierarchicalContextRepository)
        
        # Create hierarchical context service with repository
        service = HierarchicalContextService(repository=mock_repository)
        
        # Verify delegation service was initialized with repository
        assert service.delegation_service is not None
        assert service.delegation_service.repository is not None
        assert service.delegation_service.repository == mock_repository
    
    def test_delegation_service_should_work_without_repository_none_error(self):
        """Test that delegation service can handle operations without NoneType errors"""
        # Create a mock repository with required methods
        mock_repository = Mock(spec=SQLiteHierarchicalContextRepository)
        mock_repository.store_delegation = AsyncMock(return_value="delegation-id-123")
        mock_repository.get_task_context = AsyncMock(return_value={"parent_project_id": "project-123"})
        mock_repository.get_project_context = AsyncMock(return_value={"project_data": "test"})
        mock_repository.update_project_context = AsyncMock(return_value=True)
        
        # Create hierarchical context service
        service = HierarchicalContextService(repository=mock_repository)
        
        # Test that delegation service can perform operations
        async def test_delegation():
            result = await service.delegation_service.process_delegation(
                source_level="task",
                source_id="task-123",
                target_level="project", 
                target_id="project-123",
                delegated_data={"test": "data"},
                reason="Test delegation"
            )
            return result
        
        # Run the async test
        result = asyncio.run(test_delegation())
        
        # Verify the result is not None and has success status
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        # The result should not have a NoneType error
        assert result.get("error") != "'NoneType' object is not subscriptable"
    
    def test_delegation_service_repository_methods_are_called(self):
        """Test that delegation service properly calls repository methods"""
        # Create a mock repository
        mock_repository = Mock(spec=SQLiteHierarchicalContextRepository)
        mock_repository.store_delegation = AsyncMock(return_value="delegation-id-123")
        mock_repository.get_task_context = AsyncMock(return_value={"parent_project_id": "project-123"})
        mock_repository.get_project_context = AsyncMock(return_value={"project_data": "test"})
        mock_repository.update_project_context = AsyncMock(return_value=True)
        
        # Create hierarchical context service
        service = HierarchicalContextService(repository=mock_repository)
        
        # Test delegation operation
        async def test_delegation_calls():
            await service.delegation_service.process_delegation(
                source_level="task",
                source_id="task-123",
                target_level="project",
                target_id="project-123", 
                delegated_data={"test": "data"},
                reason="Test delegation"
            )
        
        # Run the test
        asyncio.run(test_delegation_calls())
        
        # Verify repository methods were called
        mock_repository.store_delegation.assert_called_once()
        mock_repository.get_task_context.assert_called()
        mock_repository.get_project_context.assert_called()
    
    def test_delegation_service_without_repository_should_get_default(self):
        """Test that delegation service gets a default repository when none provided"""
        # Create service without explicit repository
        with patch('fastmcp.task_management.infrastructure.repositories.hierarchical_context_repository_factory.HierarchicalContextRepositoryFactory') as mock_factory:
            mock_repo = Mock(spec=SQLiteHierarchicalContextRepository)
            mock_factory.return_value.create_hierarchical_context_repository.return_value = mock_repo
            
            service = HierarchicalContextService()
            
            # Verify delegation service has repository
            assert service.delegation_service.repository is not None
            assert service.delegation_service.repository == mock_repo


if __name__ == "__main__":
    pytest.main([__file__, "-v"])