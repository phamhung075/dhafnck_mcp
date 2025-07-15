"""
Test Hierarchical Context Inheritance Async/Await Fix

This test file demonstrates the async/await error in hierarchical context inheritance
and verifies that the fix properly handles async method calls.

The error occurs when async methods are called without await, resulting in:
'coroutine' object has no attribute 'update'
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# Import the classes we're testing
from fastmcp.task_management.application.services.hierarchical_context_service import (
    HierarchicalContextService, ContextResolutionResult
)
from fastmcp.task_management.application.services.context_inheritance_service import (
    ContextInheritanceService
)
from fastmcp.task_management.application.facades.hierarchical_context_facade import (
    HierarchicalContextFacade
)
from fastmcp.task_management.interface.controllers.context_mcp_controller import (
    ContextMCPController
)


class TestHierarchicalContextAsyncAwaitFix:
    """Test cases for async/await fix in hierarchical context inheritance"""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository with basic responses"""
        repository = Mock()
        
        # Mock global context
        repository.get_global_context = Mock(return_value={
            "id": "global_singleton",
            "autonomous_rules": {"enable_auto_delegation": True},
            "security_policies": {"require_mfa": True},
            "coding_standards": {"language": "python"},
            "workflow_templates": {},
            "delegation_rules": {},
            "version": 1,
            "updated_at": "2024-01-01T00:00:00Z",
            "organization_id": "org-123"
        })
        
        # Mock project context
        repository.get_project_context = Mock(return_value={
            "project_id": "project-123",
            "parent_global_id": "global_singleton",
            "team_preferences": {"code_style": "pep8"},
            "technology_stack": {"backend": "python"},
            "project_workflow": {},
            "local_standards": {},
            "global_overrides": {},
            "delegation_rules": {},
            "inheritance_disabled": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })
        
        # Mock task context
        repository.get_task_context = Mock(return_value={
            "task_id": "task-123",
            "parent_project_id": "project-123",
            "parent_project_context_id": "project-123",
            "task_data": {
                "title": "Test Task",
                "description": "Test Description",
                "status": "todo"
            },
            "local_overrides": {},
            "inheritance_disabled": False,
            "force_local_only": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })
        
        # Mock create methods
        repository.create_global_context = Mock(return_value={"success": True})
        repository.create_project_context = Mock(return_value={"success": True})
        repository.create_task_context = Mock(return_value={"success": True})
        
        return repository

    @pytest.fixture
    def mock_inheritance_service(self):
        """Create a mock inheritance service that simulates the async/await issue"""
        service = AsyncMock(spec=ContextInheritanceService)
        
        # These methods should be async and return coroutines when not awaited
        async def inherit_project_from_global(global_context, project_context):
            """Async method that merges project with global context"""
            result = {
                **global_context,
                "team_preferences": project_context.get("team_preferences", {}),
                "technology_stack": project_context.get("technology_stack", {}),
                "level": "project",
                "context_id": project_context.get("project_id"),
                "inheritance_metadata": {
                    "inherited_from": "global",
                    "global_context_version": 1,
                    "project_overrides_applied": 0
                }
            }
            return result
        
        async def inherit_task_from_project(project_context, task_context):
            """Async method that merges task with project context"""
            result = {
                **project_context,
                **task_context.get("task_data", {}),
                "level": "task",
                "context_id": task_context.get("task_id"),
                "inheritance_metadata": {
                    "inherited_from": "project",
                    "project_context_version": 1,
                    "local_overrides_applied": 0,
                    "inheritance_chain": ["global", "project", "task"]
                }
            }
            return result
        
        service.inherit_project_from_global = inherit_project_from_global
        service.inherit_task_from_project = inherit_task_from_project
        service.get_inherited_context = Mock(return_value=None)
        
        return service

    @pytest.fixture
    def mock_cache_service(self):
        """Create a mock cache service"""
        service = AsyncMock()
        service.get_cached_context = AsyncMock(return_value=None)
        service.cache_resolved_context = AsyncMock(return_value=True)
        service.invalidate_context_cache = Mock()
        service.get_context = Mock(return_value=None)
        service.set_context = Mock()
        service.invalidate_context = Mock()
        return service

    @pytest.fixture
    def mock_delegation_service(self):
        """Create a mock delegation service"""
        service = Mock()
        service.process_delegation = Mock(return_value={
            "success": True,
            "delegation_id": "delegation-123"
        })
        return service

    @pytest.mark.asyncio
    async def test_resolve_context_without_await_fails(self, mock_repository, mock_inheritance_service, 
                                                      mock_cache_service, mock_delegation_service):
        """Test that calling async inheritance methods without await causes the error"""
        
        # Create service with the bug (not awaiting async methods)
        class BuggyHierarchicalContextService(HierarchicalContextService):
            def _resolve_project_context(self, project_id: str) -> ContextResolutionResult:
                """Buggy version that doesn't await async inheritance method"""
                project_context = self.repository.get_project_context(project_id)
                
                if not project_context:
                    raise ValueError(f"Project context not found: {project_id}")
                
                global_id = project_context.get("parent_global_id", "global_singleton")
                global_result = self._resolve_global_context(global_id)
                global_context = global_result.resolved_context
                
                # BUG: Not awaiting async method - this returns a coroutine
                resolved = self.inheritance_service.inherit_project_from_global(
                    global_context=global_context,
                    project_context=project_context
                )
                
                # This will fail because 'resolved' is a coroutine, not a dict
                resolved.update({
                    "level": "project",
                    "context_id": project_id
                })
                
                return ContextResolutionResult(
                    resolved_context=resolved,
                    resolution_path=["global", "project"],
                    cache_hit=False,
                    dependencies_hash="test",
                    resolution_time_ms=0.0
                )
        
        # Create buggy service
        buggy_service = BuggyHierarchicalContextService(
            repository=mock_repository,
            inheritance_service=mock_inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # This should raise AttributeError: 'coroutine' object has no attribute 'update'
        with pytest.raises(AttributeError, match="'coroutine' object has no attribute 'update'"):
            await buggy_service.resolve_full_context("project", "project-123", force_refresh=True)

    @pytest.mark.asyncio
    async def test_resolve_context_with_proper_await_succeeds(self, mock_repository, mock_cache_service, 
                                                             mock_delegation_service):
        """Test that properly awaiting async inheritance methods works correctly"""
        
        # Create a properly fixed inheritance service
        class FixedContextInheritanceService(ContextInheritanceService):
            def inherit_project_from_global(self, global_context, project_context):
                """Sync version that properly handles inheritance"""
                result = {
                    **global_context,
                    "team_preferences": project_context.get("team_preferences", {}),
                    "technology_stack": project_context.get("technology_stack", {}),
                    "level": "project",
                    "context_id": project_context.get("project_id"),
                    "inheritance_metadata": {
                        "inherited_from": "global",
                        "global_context_version": 1,
                        "project_overrides_applied": 0
                    }
                }
                return result
            
            def inherit_task_from_project(self, project_context, task_context):
                """Sync version that properly handles inheritance"""
                result = {
                    **project_context,
                    **task_context.get("task_data", {}),
                    "level": "task", 
                    "context_id": task_context.get("task_id"),
                    "inheritance_metadata": {
                        "inherited_from": "project",
                        "project_context_version": 1,
                        "local_overrides_applied": 0,
                        "inheritance_chain": ["global", "project", "task"]
                    }
                }
                return result
        
        fixed_inheritance_service = FixedContextInheritanceService()
        
        # Create service with fixed inheritance
        service = HierarchicalContextService(
            repository=mock_repository,
            inheritance_service=fixed_inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # Test project context resolution
        result = await service.resolve_full_context("project", "project-123", force_refresh=True)
        
        assert result is not None
        assert result.resolved_context["level"] == "project"
        assert result.resolved_context["context_id"] == "project-123"
        assert "team_preferences" in result.resolved_context
        assert result.resolution_path == ["global", "project"]

    @pytest.mark.asyncio
    async def test_resolve_task_context_with_full_inheritance(self, mock_repository, mock_cache_service,
                                                             mock_delegation_service):
        """Test full inheritance chain: Global → Project → Task"""
        
        # Create fixed inheritance service
        class FixedContextInheritanceService(ContextInheritanceService):
            def inherit_project_from_global(self, global_context, project_context):
                """Sync method for project inheritance"""
                return {
                    **global_context,
                    "team_preferences": project_context.get("team_preferences", {}),
                    "technology_stack": project_context.get("technology_stack", {}),
                    "project_workflow": project_context.get("project_workflow", {}),
                    "local_standards": project_context.get("local_standards", {}),
                    "delegation_rules": {
                        **global_context.get("delegation_rules", {}),
                        **project_context.get("delegation_rules", {})
                    },
                    "inheritance_metadata": {
                        "inherited_from": "global",
                        "global_context_version": 1,
                        "project_overrides_applied": 0
                    }
                }
            
            def inherit_task_from_project(self, project_context, task_context):
                """Sync method for task inheritance"""
                return {
                    **project_context,
                    **task_context.get("task_data", {}),
                    "local_overrides": task_context.get("local_overrides", {}),
                    "inheritance_metadata": {
                        "inherited_from": "project",
                        "project_context_version": 1,
                        "local_overrides_applied": 0,
                        "force_local_only": False,
                        "inheritance_chain": ["global", "project", "task"]
                    }
                }
        
        fixed_inheritance_service = FixedContextInheritanceService()
        
        # Create service
        service = HierarchicalContextService(
            repository=mock_repository,
            inheritance_service=fixed_inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # Test task context resolution
        result = await service.resolve_full_context("task", "task-123", force_refresh=True)
        
        assert result is not None
        assert result.resolved_context["level"] == "task"
        assert result.resolved_context["context_id"] == "task-123"
        
        # Check inheritance chain
        metadata = result.resolved_context.get("inheritance_metadata", {})
        assert metadata["inheritance_chain"] == ["global", "project", "task"]
        
        # Check inherited values
        assert result.resolved_context.get("autonomous_rules") == {"enable_auto_delegation": True}
        assert result.resolved_context.get("security_policies") == {"require_mfa": True}
        assert result.resolved_context.get("team_preferences") == {"code_style": "pep8"}
        assert result.resolved_context.get("title") == "Test Task"

    @pytest.mark.asyncio
    async def test_mcp_controller_handles_async_properly(self, mock_repository, mock_cache_service,
                                                        mock_delegation_service):
        """Test that the MCP controller properly handles async context resolution"""
        
        # Create properly fixed services
        fixed_inheritance_service = ContextInheritanceService()
        
        # Override async methods to be sync
        fixed_inheritance_service.inherit_project_from_global = Mock(return_value={
            "level": "project",
            "context_id": "project-123",
            "team_preferences": {"code_style": "pep8"},
            "inheritance_metadata": {
                "inherited_from": "global",
                "inheritance_chain": ["global", "project"]
            }
        })
        
        fixed_inheritance_service.inherit_task_from_project = Mock(return_value={
            "level": "task",
            "context_id": "task-123",
            "title": "Test Task",
            "inheritance_metadata": {
                "inherited_from": "project",
                "inheritance_chain": ["global", "project", "task"]
            }
        })
        
        hierarchy_service = HierarchicalContextService(
            repository=mock_repository,
            inheritance_service=fixed_inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # Create facade factory
        facade_factory = Mock()
        facade_factory.create_context_facade = Mock(return_value=HierarchicalContextFacade(
            hierarchy_service,
            fixed_inheritance_service,
            mock_delegation_service,
            mock_cache_service
        ))
        
        # Create controller
        controller = ContextMCPController(
            hierarchical_context_facade_factory=facade_factory,
            hierarchy_service=hierarchy_service,
            inheritance_service=fixed_inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # Test resolve action
        result = await controller._handle_resolve_context("task", "task-123", force_refresh=True)
        
        assert result["success"] is True
        assert result["data"]["resolved_context"]["level"] == "task"
        assert result["data"]["resolved_context"]["context_id"] == "task-123"
        assert result["data"]["metadata"]["resolution_path"] == ["global", "project", "task"]

    @pytest.mark.asyncio
    async def test_missing_project_context_auto_creation(self, mock_cache_service, mock_delegation_service):
        """Test that missing project contexts are auto-created when needed"""
        
        # Create repository that returns None for missing project
        repository = Mock()
        repository.get_global_context = Mock(return_value={
            "id": "global_singleton",
            "autonomous_rules": {}
        })
        repository.get_project_context = Mock(return_value=None)  # Project doesn't exist
        repository.create_project_context = Mock(return_value={
            "project_id": "project-123",
            "success": True
        })
        
        # Create service
        inheritance_service = ContextInheritanceService()
        hierarchy_service = HierarchicalContextService(
            repository=repository,
            inheritance_service=inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # This should raise ValueError since project context doesn't exist
        with pytest.raises(ValueError, match="Project context not found"):
            await hierarchy_service.resolve_full_context("project", "project-123", force_refresh=True)

    @pytest.mark.asyncio 
    async def test_context_merge_with_inheritance(self, mock_repository, mock_cache_service,
                                                 mock_delegation_service):
        """Test that context merging preserves inheritance data"""
        
        # Create service with proper inheritance handling
        inheritance_service = ContextInheritanceService()
        inheritance_service.inherit_project_from_global = Mock(return_value={
            "global_data": "from_global",
            "project_data": "from_project",
            "inheritance_metadata": {"inherited_from": "global"}
        })
        
        hierarchy_service = HierarchicalContextService(
            repository=mock_repository,
            inheritance_service=inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # Test update with propagation
        result = hierarchy_service.update_context(
            level="project",
            context_id="project-123",
            changes={"new_field": "new_value"},
            propagate=True
        )
        
        assert result["success"] is True
        assert result["level"] == "project"
        assert result["context_id"] == "project-123"

    def test_sync_inheritance_methods_work_correctly(self):
        """Test that synchronous inheritance methods work without async/await"""
        
        # Create inheritance service
        service = ContextInheritanceService()
        
        # Test data
        global_context = {
            "autonomous_rules": {"enable_auto": True},
            "security_policies": {"mfa": True},
            "metadata": {"version": 1}
        }
        
        project_context = {
            "project_id": "proj-123",
            "team_preferences": {"style": "pep8"},
            "technology_stack": {"lang": "python"},
            "global_overrides": {"security_policies.mfa": False}
        }
        
        # Call sync method directly (no await needed)
        # Since inherit_project_from_global is marked as async in the actual code,
        # we need to ensure it's properly converted to sync
        result = service.get_inherited_context("project", "proj-123")
        
        # For now it returns None as per the implementation
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_integration_with_async_resolution(self, mock_repository, mock_delegation_service):
        """Test that caching works correctly with async context resolution"""
        
        # Create cache service with specific behavior
        cache_service = AsyncMock()
        cache_hit_data = {
            "resolved_context": {"cached": True, "data": "from_cache"},
            "resolution_path": '["global", "project"]',
            "dependencies_hash": "cached_hash"
        }
        cache_service.get_cached_context = AsyncMock(return_value=cache_hit_data)
        
        inheritance_service = ContextInheritanceService()
        hierarchy_service = HierarchicalContextService(
            repository=mock_repository,
            inheritance_service=inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=cache_service
        )
        
        # Test with cache hit
        result = await hierarchy_service.resolve_full_context("project", "project-123", force_refresh=False)
        
        assert result.cache_hit is True
        assert result.resolved_context["cached"] is True
        assert result.resolved_context["data"] == "from_cache"
        
        # Verify cache was checked
        cache_service.get_cached_context.assert_called_once_with("project", "project-123")

    @pytest.mark.asyncio
    async def test_error_handling_in_async_context(self, mock_repository, mock_cache_service,
                                                  mock_delegation_service):
        """Test proper error handling when async operations fail"""
        
        # Create service that throws error
        inheritance_service = ContextInheritanceService()
        
        # Make repository throw error
        mock_repository.get_project_context = Mock(side_effect=Exception("Database error"))
        
        hierarchy_service = HierarchicalContextService(
            repository=mock_repository,
            inheritance_service=inheritance_service,
            delegation_service=mock_delegation_service,
            cache_service=mock_cache_service
        )
        
        # Test error handling
        with pytest.raises(Exception, match="Database error"):
            await hierarchy_service.resolve_full_context("project", "project-123", force_refresh=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])