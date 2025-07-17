#!/usr/bin/env python3
"""
Unit tests for HierarchicalContextService async/await fixes.

Tests the fix for coroutine error in get_system_health method.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
from fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository


class TestHierarchicalContextAsync:
    """Test HierarchicalContextService async methods work correctly"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository with async health_check method"""
        mock = Mock(spec=ORMHierarchicalContextRepository)
        # Make health_check return an async mock
        mock.health_check = AsyncMock(return_value={
            "status": "healthy",
            "cache_entries": 10,
            "last_cleanup": "2024-01-01T00:00:00Z"
        })
        return mock
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create HierarchicalContextService instance"""
        return HierarchicalContextService(repository=mock_repository)
    
    def test_get_system_health_is_async(self, service):
        """Test that get_system_health is properly defined as async"""
        # Check the method is a coroutine function
        assert asyncio.iscoroutinefunction(service.get_system_health), \
            "get_system_health should be an async method"
    
    @pytest.mark.asyncio
    async def test_get_system_health_calls_repository_with_await(self, service, mock_repository):
        """Test that get_system_health properly awaits repository.health_check"""
        # Call the async method
        result = await service.get_system_health()
        
        # Verify repository method was called
        mock_repository.health_check.assert_called_once()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "status" in result
        
        # The actual implementation may have different structure, check for error
        if "error" in result:
            # If there's an error, make sure it's not a coroutine error
            assert "'coroutine' object" not in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_system_health_no_coroutine_error(self, service):
        """Test that get_system_health doesn't return a coroutine object"""
        # Call the method with await
        result = await service.get_system_health()
        
        # Result should be a dict, not a coroutine
        assert isinstance(result, dict), "Result should be a dict, not a coroutine"
        assert not asyncio.iscoroutine(result), "Result should not be a coroutine object"
    
    @pytest.mark.asyncio
    async def test_health_check_error_handling(self, service, mock_repository):
        """Test error handling when repository health check fails"""
        # Make repository raise an exception
        mock_repository.health_check = AsyncMock(side_effect=Exception("Database error"))
        
        # Should still return a result with error status
        result = await service.get_system_health()
        
        assert result["status"] == "error"
        assert "error" in result
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_controller_integration(self, mock_repository):
        """Test that the fix works in controller context"""
        # Create hierarchy service with mocked repository
        hierarchy_service = HierarchicalContextService(repository=mock_repository)
        
        # Mock the handler method that calls get_system_health
        # This simulates the controller properly awaiting the async method
        async def mock_handler():
            health = await hierarchy_service.get_system_health()
            return {"success": True, "health": health}
        
        result = await mock_handler()
        
        # Should succeed without coroutine error
        assert result["success"]
        assert "health" in result
        assert isinstance(result["health"], dict)
    
    def test_async_method_signature(self):
        """Test the method signature is correct"""
        import inspect
        
        # Get the method
        method = HierarchicalContextService.get_system_health
        
        # Check it's a coroutine function
        assert inspect.iscoroutinefunction(method), \
            "get_system_health should be a coroutine function"
        
        # Check signature
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert params == ['self'], \
            "get_system_health should only have 'self' parameter"
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, service, mock_repository):
        """Test that concurrent health checks work correctly"""
        # Reset call count
        mock_repository.health_check.reset_mock()
        
        # Call health check multiple times concurrently
        tasks = [service.get_system_health() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All results should be valid
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
            assert "status" in result
            # Check that no coroutine error occurred
            if "error" in result:
                assert "'coroutine' object" not in result["error"]
        
        # Repository should have been called 5 times
        assert mock_repository.health_check.call_count == 5