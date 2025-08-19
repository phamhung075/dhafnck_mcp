"""Test suite for DependencyApplicationService.

Tests for dependency management and resolution in task workflows.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from fastmcp.task_management.application.services.dependency_application_service import DependencyApplicationService


class TestDependencyApplicationServiceInit:
    """Test DependencyApplicationService initialization."""

    def test_initialization_with_defaults(self):
        """Test service initialization with default values."""
        service = DependencyApplicationService()
        
        assert service.repository is None
        assert service._user_id is None
        assert service.dependency_resolver is not None

    def test_initialization_with_parameters(self):
        """Test service initialization with custom parameters."""
        mock_repo = Mock()
        mock_resolver = Mock()
        service = DependencyApplicationService(
            repository=mock_repo, 
            dependency_resolver=mock_resolver,
            user_id="test_user_123"
        )
        
        assert service.repository == mock_repo
        assert service.dependency_resolver == mock_resolver
        assert service._user_id == "test_user_123"

    def test_with_user_method(self):
        """Test with_user method creates new instance with user context."""
        original_service = DependencyApplicationService()
        user_id = "test_user_456"
        
        user_scoped_service = original_service.with_user(user_id)
        
        assert user_scoped_service._user_id == user_id
        assert user_scoped_service is not original_service
        assert isinstance(user_scoped_service, DependencyApplicationService)

    def test_get_user_scoped_repository_with_with_user_method(self):
        """Test _get_user_scoped_repository with repository that has with_user method."""
        service = DependencyApplicationService(user_id="test_user")
        mock_repo = Mock()
        mock_user_scoped_repo = Mock()
        mock_repo.with_user.return_value = mock_user_scoped_repo
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_user_scoped_repo
        mock_repo.with_user.assert_called_once_with("test_user")

    def test_get_user_scoped_repository_with_user_id_property(self):
        """Test _get_user_scoped_repository with repository that has user_id property."""
        service = DependencyApplicationService(user_id="test_user")
        mock_repo = Mock()
        mock_repo.user_id = "different_user"
        mock_repo.session = Mock()
        
        # Mock the repository class constructor
        with patch('type') as mock_type:
            mock_repo_class = Mock()
            mock_type.return_value = mock_repo_class
            mock_new_repo = Mock()
            mock_repo_class.return_value = mock_new_repo
            
            result = service._get_user_scoped_repository(mock_repo)
            
            # Should create new instance with correct user_id
            mock_repo_class.assert_called_once_with(mock_repo.session, user_id="test_user")
            assert result == mock_new_repo

    def test_get_user_scoped_repository_no_user_context(self):
        """Test _get_user_scoped_repository returns original repo when no user context."""
        service = DependencyApplicationService()  # No user_id
        mock_repo = Mock()
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_repo


class TestSyncWrapperMethods:
    """Test synchronous wrapper methods for facade compatibility."""

    def test_add_dependency_sync_wrapper_no_loop(self):
        """Test synchronous add_dependency wrapper when no event loop exists."""
        service = DependencyApplicationService()
        
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No loop")):
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"success": True, "dependency_id": "dep_123"}
                
                result = service.add_dependency("task_1", "task_2", "blocking")
                
                assert result["success"] is True
                assert result["dependency_id"] == "dep_123"
                mock_run.assert_called_once()

    def test_add_dependency_sync_wrapper_running_loop(self):
        """Test synchronous add_dependency wrapper when event loop is running."""
        service = DependencyApplicationService()
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch('fastmcp.task_management.application.services.dependency_application_service.logger') as mock_logger:
                result = service.add_dependency("task_1", "task_2", "blocking")
                
                # Should return mock response when loop is running
                assert "success" in result
                mock_logger.debug.assert_called()

    def test_add_dependency_sync_wrapper_exception(self):
        """Test synchronous add_dependency wrapper exception handling."""
        service = DependencyApplicationService()
        
        with patch('asyncio.get_event_loop', side_effect=Exception("Unexpected error")):
            with patch('fastmcp.task_management.application.services.dependency_application_service.logger') as mock_logger:
                result = service.add_dependency("task_1", "task_2", "blocking")
                
                assert result["success"] is False
                assert "error" in result
                mock_logger.error.assert_called()


class TestDependencyManagement:
    """Test dependency management functionality."""

    @pytest.mark.asyncio
    async def test_add_dependency_success(self):
        """Test successful dependency addition."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        # Mock dependency validation
        mock_resolver.validate_dependency.return_value = {"valid": True}
        
        # Mock repository operations
        mock_repo.task_exists.return_value = True
        mock_repo.dependency_exists.return_value = False
        mock_dependency_id = str(uuid.uuid4())
        mock_repo.create_dependency.return_value = {"dependency_id": mock_dependency_id}
        
        result = await service.add_dependency_async("task_1", "task_2", "blocking")
        
        assert result["success"] is True
        assert result["dependency_id"] == mock_dependency_id
        assert result["dependent_task"] == "task_1"
        assert result["dependency_task"] == "task_2"
        assert result["dependency_type"] == "blocking"
        
        # Verify repository calls
        mock_repo.task_exists.assert_any_call("task_1")
        mock_repo.task_exists.assert_any_call("task_2")
        mock_repo.dependency_exists.assert_called_once_with("task_1", "task_2")
        mock_repo.create_dependency.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_dependency_circular_detection(self):
        """Test circular dependency detection."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        # Mock circular dependency detection
        mock_resolver.validate_dependency.return_value = {
            "valid": False, 
            "error": "Circular dependency detected"
        }
        
        mock_repo.task_exists.return_value = True
        mock_repo.dependency_exists.return_value = False
        
        result = await service.add_dependency_async("task_1", "task_2", "blocking")
        
        assert result["success"] is False
        assert "circular" in result["error"].lower()
        
        # Should not create dependency
        mock_repo.create_dependency.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_dependency_nonexistent_task(self):
        """Test adding dependency with nonexistent task."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        # Mock task existence checks
        mock_repo.task_exists.side_effect = lambda task_id: task_id == "task_1"
        
        result = await service.add_dependency_async("task_1", "nonexistent_task", "blocking")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
        assert "nonexistent_task" in result["error"]

    @pytest.mark.asyncio
    async def test_add_dependency_already_exists(self):
        """Test adding dependency that already exists."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.task_exists.return_value = True
        mock_repo.dependency_exists.return_value = True
        
        result = await service.add_dependency_async("task_1", "task_2", "blocking")
        
        assert result["success"] is False
        assert "already exists" in result["error"].lower()
        
        # Should not create duplicate dependency
        mock_repo.create_dependency.assert_not_called()

    @pytest.mark.asyncio
    async def test_remove_dependency_success(self):
        """Test successful dependency removal."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.dependency_exists.return_value = True
        mock_repo.remove_dependency.return_value = True
        
        result = await service.remove_dependency_async("task_1", "task_2")
        
        assert result["success"] is True
        assert result["removed"] is True
        assert result["dependent_task"] == "task_1"
        assert result["dependency_task"] == "task_2"
        
        mock_repo.remove_dependency.assert_called_once_with("task_1", "task_2")

    @pytest.mark.asyncio
    async def test_remove_dependency_not_exists(self):
        """Test removing dependency that doesn't exist."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.dependency_exists.return_value = False
        
        result = await service.remove_dependency_async("task_1", "task_2")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
        
        # Should not attempt removal
        mock_repo.remove_dependency.assert_not_called()

    @pytest.mark.asyncio
    async def test_remove_dependency_exception(self):
        """Test dependency removal exception handling."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.dependency_exists.return_value = True
        mock_repo.remove_dependency.side_effect = Exception("Database error")
        
        result = await service.remove_dependency_async("task_1", "task_2")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_task_dependencies_success(self):
        """Test retrieving task dependencies."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_dependencies = [
            {"dependency_task": "task_2", "dependency_type": "blocking", "created_at": "2024-01-01"},
            {"dependency_task": "task_3", "dependency_type": "soft", "created_at": "2024-01-02"}
        ]
        mock_repo.get_task_dependencies.return_value = mock_dependencies
        
        result = await service.get_task_dependencies_async("task_1")
        
        assert result["success"] is True
        assert result["task_id"] == "task_1"
        assert len(result["dependencies"]) == 2
        assert result["dependencies"][0]["dependency_task"] == "task_2"
        assert result["dependencies"][1]["dependency_type"] == "soft"

    @pytest.mark.asyncio
    async def test_get_task_dependencies_empty(self):
        """Test retrieving dependencies for task with no dependencies."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.get_task_dependencies.return_value = []
        
        result = await service.get_task_dependencies_async("task_1")
        
        assert result["success"] is True
        assert len(result["dependencies"]) == 0
        assert result["has_dependencies"] is False

    @pytest.mark.asyncio
    async def test_get_dependent_tasks_success(self):
        """Test retrieving tasks that depend on given task."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_dependents = [
            {"dependent_task": "task_4", "dependency_type": "blocking"},
            {"dependent_task": "task_5", "dependency_type": "soft"}
        ]
        mock_repo.get_dependent_tasks.return_value = mock_dependents
        
        result = await service.get_dependent_tasks_async("task_1")
        
        assert result["success"] is True
        assert result["task_id"] == "task_1"
        assert len(result["dependents"]) == 2
        assert result["dependents"][0]["dependent_task"] == "task_4"
        assert result["has_dependents"] is True


class TestDependencyResolution:
    """Test dependency resolution functionality."""

    @pytest.mark.asyncio
    async def test_resolve_task_dependencies_success(self):
        """Test successful task dependency resolution."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        # Mock dependency resolution
        mock_resolution = {
            "can_start": True,
            "blocking_dependencies": [],
            "ready_dependencies": ["task_2", "task_3"],
            "dependency_chain": ["task_2", "task_3", "task_1"]
        }
        mock_resolver.resolve_task_dependencies.return_value = mock_resolution
        
        result = await service.resolve_task_dependencies_async("task_1")
        
        assert result["success"] is True
        assert result["task_id"] == "task_1"
        assert result["can_start"] is True
        assert len(result["blocking_dependencies"]) == 0
        assert len(result["ready_dependencies"]) == 2
        assert result["dependency_chain"] == ["task_2", "task_3", "task_1"]

    @pytest.mark.asyncio
    async def test_resolve_task_dependencies_blocked(self):
        """Test dependency resolution for blocked task."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        # Mock blocked dependency resolution
        mock_resolution = {
            "can_start": False,
            "blocking_dependencies": ["task_2"],
            "ready_dependencies": ["task_3"],
            "blocking_reasons": ["Task task_2 is not completed"]
        }
        mock_resolver.resolve_task_dependencies.return_value = mock_resolution
        
        result = await service.resolve_task_dependencies_async("task_1")
        
        assert result["success"] is True
        assert result["can_start"] is False
        assert len(result["blocking_dependencies"]) == 1
        assert result["blocking_dependencies"][0] == "task_2"
        assert "task_2 is not completed" in result["blocking_reasons"][0]

    @pytest.mark.asyncio
    async def test_get_dependency_graph_success(self):
        """Test dependency graph generation."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        mock_graph = {
            "nodes": [
                {"id": "task_1", "status": "todo", "title": "Task 1"},
                {"id": "task_2", "status": "done", "title": "Task 2"},
                {"id": "task_3", "status": "in_progress", "title": "Task 3"}
            ],
            "edges": [
                {"from": "task_2", "to": "task_1", "type": "blocking"},
                {"from": "task_3", "to": "task_1", "type": "soft"}
            ],
            "cycles": []
        }
        mock_resolver.build_dependency_graph.return_value = mock_graph
        
        result = await service.get_dependency_graph_async(["task_1", "task_2", "task_3"])
        
        assert result["success"] is True
        assert len(result["graph"]["nodes"]) == 3
        assert len(result["graph"]["edges"]) == 2
        assert len(result["graph"]["cycles"]) == 0
        assert result["has_cycles"] is False

    @pytest.mark.asyncio
    async def test_get_dependency_graph_with_cycles(self):
        """Test dependency graph with circular dependencies."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        mock_graph = {
            "nodes": [{"id": "task_1"}, {"id": "task_2"}],
            "edges": [
                {"from": "task_1", "to": "task_2", "type": "blocking"},
                {"from": "task_2", "to": "task_1", "type": "blocking"}
            ],
            "cycles": [["task_1", "task_2", "task_1"]]
        }
        mock_resolver.build_dependency_graph.return_value = mock_graph
        
        result = await service.get_dependency_graph_async(["task_1", "task_2"])
        
        assert result["success"] is True
        assert result["has_cycles"] is True
        assert len(result["graph"]["cycles"]) == 1

    @pytest.mark.asyncio
    async def test_analyze_dependency_impact_success(self):
        """Test dependency impact analysis."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        mock_impact = {
            "affected_tasks": ["task_3", "task_4", "task_5"],
            "cascade_depth": 2,
            "critical_path": ["task_1", "task_3", "task_5"],
            "impact_score": 85.0
        }
        mock_resolver.analyze_impact.return_value = mock_impact
        
        result = await service.analyze_dependency_impact_async("task_1", "completion")
        
        assert result["success"] is True
        assert result["task_id"] == "task_1"
        assert result["change_type"] == "completion"
        assert len(result["affected_tasks"]) == 3
        assert result["cascade_depth"] == 2
        assert result["impact_score"] == 85.0


class TestDependencyValidation:
    """Test dependency validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_dependency_chain_valid(self):
        """Test validation of valid dependency chain."""
        mock_resolver = Mock()
        service = DependencyApplicationService(dependency_resolver=mock_resolver)
        
        mock_resolver.validate_chain.return_value = {
            "valid": True,
            "chain_length": 3,
            "violations": []
        }
        
        result = await service.validate_dependency_chain_async(["task_1", "task_2", "task_3"])
        
        assert result["success"] is True
        assert result["valid_chain"] is True
        assert result["chain_length"] == 3
        assert len(result["violations"]) == 0

    @pytest.mark.asyncio
    async def test_validate_dependency_chain_invalid(self):
        """Test validation of invalid dependency chain."""
        mock_resolver = Mock()
        service = DependencyApplicationService(dependency_resolver=mock_resolver)
        
        mock_resolver.validate_chain.return_value = {
            "valid": False,
            "violations": [
                {"type": "circular", "description": "Circular dependency detected"},
                {"type": "depth", "description": "Chain too deep"}
            ]
        }
        
        result = await service.validate_dependency_chain_async(["task_1", "task_2", "task_1"])
        
        assert result["success"] is True
        assert result["valid_chain"] is False
        assert len(result["violations"]) == 2
        assert any(v["type"] == "circular" for v in result["violations"])

    @pytest.mark.asyncio
    async def test_check_dependency_constraints_success(self):
        """Test dependency constraint checking."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.check_constraints.return_value = {
            "valid": True,
            "constraints_met": True,
            "constraint_violations": []
        }
        
        result = await service.check_dependency_constraints_async("task_1", "task_2", "blocking")
        
        assert result["success"] is True
        assert result["constraints_met"] is True
        assert len(result["constraint_violations"]) == 0

    @pytest.mark.asyncio
    async def test_check_dependency_constraints_violations(self):
        """Test dependency constraint checking with violations."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.check_constraints.return_value = {
            "valid": False,
            "constraints_met": False,
            "constraint_violations": [
                {"constraint": "max_dependencies", "limit": 5, "current": 6}
            ]
        }
        
        result = await service.check_dependency_constraints_async("task_1", "task_2", "blocking")
        
        assert result["success"] is True
        assert result["constraints_met"] is False
        assert len(result["constraint_violations"]) == 1
        assert result["constraint_violations"][0]["constraint"] == "max_dependencies"


class TestBatchOperations:
    """Test batch dependency operations."""

    @pytest.mark.asyncio
    async def test_batch_add_dependencies_success(self):
        """Test batch dependency addition."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        dependencies = [
            {"dependent": "task_1", "dependency": "task_2", "type": "blocking"},
            {"dependent": "task_1", "dependency": "task_3", "type": "soft"},
            {"dependent": "task_2", "dependency": "task_3", "type": "blocking"}
        ]
        
        # Mock successful validations and additions
        mock_resolver.validate_dependency.return_value = {"valid": True}
        mock_repo.task_exists.return_value = True
        mock_repo.dependency_exists.return_value = False
        mock_repo.create_dependency.return_value = {"dependency_id": "dep_123"}
        
        result = await service.batch_add_dependencies_async(dependencies)
        
        assert result["success"] is True
        assert result["total_requested"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_batch_add_dependencies_partial_success(self):
        """Test batch dependency addition with partial success."""
        mock_repo = AsyncMock()
        mock_resolver = Mock()
        service = DependencyApplicationService(repository=mock_repo, dependency_resolver=mock_resolver)
        
        dependencies = [
            {"dependent": "task_1", "dependency": "task_2", "type": "blocking"},
            {"dependent": "task_1", "dependency": "nonexistent", "type": "soft"}
        ]
        
        # Mock first success, second failure
        mock_resolver.validate_dependency.return_value = {"valid": True}
        mock_repo.task_exists.side_effect = lambda task_id: task_id != "nonexistent"
        mock_repo.dependency_exists.return_value = False
        mock_repo.create_dependency.return_value = {"dependency_id": "dep_123"}
        
        result = await service.batch_add_dependencies_async(dependencies)
        
        assert result["success"] is True  # Partial success still returns True
        assert result["total_requested"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert result["results"][1]["success"] is False

    @pytest.mark.asyncio
    async def test_batch_remove_dependencies_success(self):
        """Test batch dependency removal."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        dependency_pairs = [
            ("task_1", "task_2"),
            ("task_1", "task_3"),
            ("task_2", "task_3")
        ]
        
        mock_repo.dependency_exists.return_value = True
        mock_repo.remove_dependency.return_value = True
        
        result = await service.batch_remove_dependencies_async(dependency_pairs)
        
        assert result["success"] is True
        assert result["total_requested"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_get_all_dependencies_for_tasks(self):
        """Test retrieving all dependencies for multiple tasks."""
        mock_repo = AsyncMock()
        service = DependencyApplicationService(repository=mock_repo)
        
        mock_repo.get_bulk_task_dependencies.return_value = {
            "task_1": [{"dependency_task": "task_2", "type": "blocking"}],
            "task_2": [{"dependency_task": "task_3", "type": "soft"}],
            "task_3": []
        }
        
        result = await service.get_all_dependencies_for_tasks_async(["task_1", "task_2", "task_3"])
        
        assert result["success"] is True
        assert len(result["task_dependencies"]) == 3
        assert len(result["task_dependencies"]["task_1"]) == 1
        assert len(result["task_dependencies"]["task_3"]) == 0


class TestUtilityMethods:
    """Test utility methods in dependency service."""

    def test_format_dependency_result(self):
        """Test dependency result formatting."""
        service = DependencyApplicationService()
        
        raw_result = {
            "dependency_id": "dep_123",
            "dependent_task": "task_1",
            "dependency_task": "task_2",
            "dependency_type": "blocking",
            "created_at": "2024-01-01T10:00:00Z"
        }
        
        formatted = service._format_dependency_result(raw_result)
        
        assert formatted["id"] == "dep_123"
        assert formatted["from_task"] == "task_1"
        assert formatted["to_task"] == "task_2"
        assert formatted["type"] == "blocking"
        assert "created_timestamp" in formatted

    def test_validate_dependency_type(self):
        """Test dependency type validation."""
        service = DependencyApplicationService()
        
        assert service._validate_dependency_type("blocking") is True
        assert service._validate_dependency_type("soft") is True
        assert service._validate_dependency_type("finish_to_start") is True
        assert service._validate_dependency_type("invalid_type") is False

    def test_calculate_dependency_priority(self):
        """Test dependency priority calculation."""
        service = DependencyApplicationService()
        
        # Blocking dependencies should have high priority
        priority = service._calculate_dependency_priority("blocking", "high", "critical")
        assert priority >= 80

        # Soft dependencies should have lower priority
        priority = service._calculate_dependency_priority("soft", "low", "low")
        assert priority <= 50

    def test_generate_dependency_summary(self):
        """Test dependency summary generation."""
        service = DependencyApplicationService()
        
        dependencies = [
            {"type": "blocking", "status": "pending"},
            {"type": "blocking", "status": "satisfied"},
            {"type": "soft", "status": "pending"}
        ]
        
        summary = service._generate_dependency_summary(dependencies)
        
        assert summary["total_dependencies"] == 3
        assert summary["blocking_dependencies"] == 2
        assert summary["soft_dependencies"] == 1
        assert summary["pending_dependencies"] == 2
        assert summary["satisfied_dependencies"] == 1