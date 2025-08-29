"""Test for Unified Context Service"""

import pytest
import json
import uuid
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Dict, Any, List

from fastmcp.task_management.application.orchestrators.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.domain.entities.context import GlobalContext, ProjectContext, BranchContext, TaskContextUnified as TaskContext
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel


class TestUnifiedContextService:
    """Test suite for UnifiedContextService"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for all context levels"""
        return {
            ContextLevel.GLOBAL: Mock(),
            ContextLevel.PROJECT: Mock(),
            ContextLevel.BRANCH: Mock(),
            ContextLevel.TASK: Mock()
        }
    
    @pytest.fixture
    def mock_cache_service(self):
        """Create a mock cache service"""
        return Mock()
    
    @pytest.fixture
    def mock_inheritance_service(self):
        """Create a mock inheritance service"""
        mock = Mock()
        mock.inherit_project_from_global = Mock(side_effect=lambda g, p: {**g, **p})
        mock.inherit_branch_from_project = Mock(side_effect=lambda p, b: {**p, **b})
        mock.inherit_task_from_branch = Mock(side_effect=lambda b, t: {**b, **t})
        return mock
    
    @pytest.fixture
    def mock_delegation_service(self):
        """Create a mock delegation service"""
        return Mock()
    
    @pytest.fixture
    def mock_validation_service(self):
        """Create a mock validation service"""
        mock = Mock()
        mock.validate_context_data = Mock(return_value={"valid": True})
        return mock
    
    @pytest.fixture
    def service(self, mock_repositories, mock_cache_service, mock_inheritance_service, 
                mock_delegation_service, mock_validation_service):
        """Create a unified context service instance"""
        return UnifiedContextService(
            mock_repositories[ContextLevel.GLOBAL],
            mock_repositories[ContextLevel.PROJECT],
            mock_repositories[ContextLevel.BRANCH],
            mock_repositories[ContextLevel.TASK],
            mock_cache_service,
            mock_inheritance_service,
            mock_delegation_service,
            mock_validation_service
        )
    
    @pytest.fixture
    def sample_global_context(self):
        """Create a sample global context"""
        return GlobalContext(
            id="global-123",
            organization_name="Test Org",
            global_settings={"timezone": "UTC"},
            metadata={"created_at": "2025-01-01"}
        )
    
    @pytest.fixture
    def sample_project_context(self):
        """Create a sample project context"""
        return ProjectContext(
            id="project-123",
            project_name="Test Project",
            project_settings={"default_branch": "main"},
            metadata={"created_at": "2025-01-01"}
        )
    
    @pytest.fixture
    def sample_branch_context(self):
        """Create a sample branch context"""
        return BranchContext(
            id="branch-123",
            project_id="project-123",
            git_branch_name="feature/test",
            branch_settings={"workflow_type": "standard"},
            metadata={"created_at": "2025-01-01"}
        )
    
    @pytest.fixture
    def sample_task_context(self):
        """Create a sample task context"""
        return TaskContext(
            id="task-123",
            branch_id="branch-123",
            task_data={"title": "Test Task"},
            progress=50,
            insights=[],
            next_steps=[],
            metadata={"created_at": "2025-01-01"}
        )
    
    def test_init(self, mock_repositories, mock_cache_service, mock_inheritance_service,
                  mock_delegation_service, mock_validation_service):
        """Test service initialization"""
        service = UnifiedContextService(
            mock_repositories[ContextLevel.GLOBAL],
            mock_repositories[ContextLevel.PROJECT],
            mock_repositories[ContextLevel.BRANCH],
            mock_repositories[ContextLevel.TASK],
            mock_cache_service,
            mock_inheritance_service,
            mock_delegation_service,
            mock_validation_service
        )
        
        assert service.repositories == mock_repositories
        assert service.cache_service == mock_cache_service
        assert service.inheritance_service == mock_inheritance_service
        assert service.delegation_service == mock_delegation_service
        assert service.validation_service == mock_validation_service
        assert service._user_id is None
        assert hasattr(service, 'hierarchy_validator')
    
    def test_init_with_user_id(self, mock_repositories):
        """Test service initialization with user_id"""
        user_id = "test-user-123"
        service = UnifiedContextService(
            mock_repositories[ContextLevel.GLOBAL],
            mock_repositories[ContextLevel.PROJECT],
            mock_repositories[ContextLevel.BRANCH],
            mock_repositories[ContextLevel.TASK],
            user_id=user_id
        )
        assert service._user_id == user_id
    
    def test_with_user(self, service):
        """Test creating user-scoped service"""
        user_id = "test-user-456"
        
        # Mock repositories to have with_user method
        for repo in service.repositories.values():
            repo.with_user = Mock(return_value=repo)
        
        user_scoped_service = service.with_user(user_id)
        
        assert isinstance(user_scoped_service, UnifiedContextService)
        assert user_scoped_service._user_id == user_id
        
        # Verify all repositories were scoped
        for repo in service.repositories.values():
            repo.with_user.assert_called_once_with(user_id)
    
    def test_serialize_for_json_basic_types(self, service):
        """Test JSON serialization for basic types"""
        # Test None
        assert service._serialize_for_json(None) is None
        
        # Test string, int, float, bool
        assert service._serialize_for_json("test") == "test"
        assert service._serialize_for_json(123) == 123
        assert service._serialize_for_json(45.6) == 45.6
        assert service._serialize_for_json(True) is True
        
        # Test UUID
        test_uuid = uuid.uuid4()
        assert service._serialize_for_json(test_uuid) == str(test_uuid)
        
        # Test datetime
        test_datetime = datetime.now(timezone.utc)
        assert service._serialize_for_json(test_datetime) == str(test_datetime)
        
        # Test date
        test_date = date.today()
        assert service._serialize_for_json(test_date) == str(test_date)
        
        # Test Decimal
        test_decimal = Decimal("123.45")
        assert service._serialize_for_json(test_decimal) == 123.45
    
    def test_serialize_for_json_collections(self, service):
        """Test JSON serialization for collections"""
        # Test dict
        test_dict = {
            "uuid": uuid.uuid4(),
            "datetime": datetime.now(timezone.utc),
            "decimal": Decimal("123.45")
        }
        result = service._serialize_for_json(test_dict)
        assert isinstance(result["uuid"], str)
        assert isinstance(result["datetime"], str)
        assert isinstance(result["decimal"], float)
        
        # Test list
        test_list = [uuid.uuid4(), datetime.now(timezone.utc), Decimal("123.45")]
        result = service._serialize_for_json(test_list)
        assert all(isinstance(item, (str, float)) for item in result)
        
        # Test tuple
        test_tuple = (uuid.uuid4(), datetime.now(timezone.utc))
        result = service._serialize_for_json(test_tuple)
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_serialize_for_json_nested(self, service):
        """Test JSON serialization for nested structures"""
        nested_data = {
            "level1": {
                "level2": {
                    "uuid": uuid.uuid4(),
                    "list": [Decimal("1.1"), Decimal("2.2")],
                    "date": date.today()
                }
            }
        }
        result = service._serialize_for_json(nested_data)
        assert isinstance(result["level1"]["level2"]["uuid"], str)
        assert all(isinstance(x, float) for x in result["level1"]["level2"]["list"])
        assert isinstance(result["level1"]["level2"]["date"], str)
    
    def test_normalize_global_context_id_no_change(self, service):
        """Test normalize global context ID when not 'global'"""
        context_id = "some-uuid-123"
        result = service._normalize_global_context_id(context_id)
        assert result == context_id
    
    def test_normalize_global_context_id_global_with_user(self, service):
        """Test normalize global context ID from 'global' with user_id"""
        service._user_id = "test-user-123"
        context_id = "global"
        
        result = service._normalize_global_context_id(context_id)
        
        assert result != "global"
        assert len(result) == 36  # UUID length
        # Should be consistent for same user
        result2 = service._normalize_global_context_id(context_id)
        assert result == result2
    
    def test_normalize_global_context_id_global_with_explicit_user(self, service):
        """Test normalize global context ID with explicit user_id parameter"""
        context_id = "global"
        user_id = "explicit-user-456"
        
        result = service._normalize_global_context_id(context_id, user_id)
        
        assert result != "global"
        assert len(result) == 36
    
    @patch('fastmcp.task_management.application.orchestrators.services.unified_context_service.get_current_user_context')
    def test_normalize_global_context_id_from_context(self, mock_get_user, service):
        """Test normalize global context ID from request context"""
        mock_user = Mock()
        mock_user.user_id = "context-user-789"
        mock_get_user.return_value = mock_user
        
        context_id = "global"
        result = service._normalize_global_context_id(context_id)
        
        assert result != "global"
        assert len(result) == 36
    
    def test_create_context_global_success(self, service, mock_validation_service):
        """Test successful global context creation"""
        context_id = "global-123"
        data = {
            "organization_name": "Test Org",
            "global_settings": {"timezone": "UTC"},
            "metadata": {"source": "test"}
        }
        
        # Mock hierarchy validator
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock repository
        mock_repo = service.repositories[ContextLevel.GLOBAL]
        created_context = GlobalContext(id=context_id, **data)
        mock_repo.create.return_value = created_context
        
        result = service.create_context("global", context_id, data)
        
        assert result["success"] is True
        assert result["context_id"] == context_id
        assert result["level"] == "global"
        assert "context" in result
        
        # Verify validation was called
        mock_validation_service.validate_context_data.assert_called_once()
        
        # Verify repository create was called
        mock_repo.create.assert_called_once()
    
    def test_create_context_invalid_level(self, service):
        """Test context creation with invalid level"""
        result = service.create_context("invalid", "test-id", {})
        
        assert result["success"] is False
        assert "error" in result
    
    def test_create_context_validation_failure(self, service, mock_validation_service):
        """Test context creation with validation failure"""
        mock_validation_service.validate_context_data.return_value = {
            "valid": False,
            "errors": ["Missing required field"]
        }
        
        result = service.create_context("project", "project-123", {})
        
        assert result["success"] is False
        assert "Validation failed" in result["error"]
    
    def test_create_context_hierarchy_validation_failure(self, service):
        """Test context creation with hierarchy validation failure"""
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(False, "Parent context missing", {"hint": "Create parent first"})
        )
        
        result = service.create_context("branch", "branch-123", {"project_id": "missing-project"})
        
        assert result["success"] is False
        assert "Parent context missing" in result["error"]
        assert result.get("hint") == "Create parent first"
    
    def test_create_context_auto_create_parents(self, service, mock_validation_service):
        """Test context creation with auto parent creation"""
        branch_id = "branch-123"
        project_id = "project-123"
        data = {"project_id": project_id, "git_branch_name": "main"}
        
        # Mock ensure parent contexts
        service._ensure_parent_contexts_exist = Mock(return_value={
            "success": True,
            "created_contexts": ["global", "project"]
        })
        
        # Mock hierarchy validator
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock repository
        mock_repo = service.repositories[ContextLevel.BRANCH]
        created_context = BranchContext(id=branch_id, **data)
        mock_repo.create.return_value = created_context
        
        result = service.create_context("branch", branch_id, data, auto_create_parents=True)
        
        assert result["success"] is True
        service._ensure_parent_contexts_exist.assert_called_once()
    
    def test_create_context_project_with_custom_fields(self, service):
        """Test project context creation with custom fields"""
        context_id = "project-123"
        data = {
            "project_name": "Test Project",
            "project_settings": {"default_branch": "main"},
            "custom_field": "custom_value",
            "team_preferences": {"review_required": True}
        }
        
        # Mock hierarchy validator
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock validation
        service.validation_service.validate_context_data = Mock(return_value={"valid": True})
        
        # Mock repository
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.create = Mock(return_value=Mock(id=context_id))
        
        result = service.create_context("project", context_id, data)
        
        assert result["success"] is True
        
        # Verify entity was created with proper structure
        create_call = mock_repo.create.call_args[0][0]
        assert isinstance(create_call, ProjectContext)
    
    def test_get_context_success(self, service, sample_project_context):
        """Test successful context retrieval"""
        context_id = "project-123"
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.get.return_value = sample_project_context
        
        result = service.get_context("project", context_id)
        
        assert result["success"] is True
        assert result["context_id"] == context_id
        assert result["level"] == "project"
        assert result["inherited"] is False
        assert "context" in result
    
    def test_get_context_not_found(self, service):
        """Test get context when not found"""
        context_id = "missing-123"
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.get.return_value = None
        
        result = service.get_context("project", context_id)
        
        assert result["success"] is False
        assert "Context not found" in result["error"]
    
    def test_get_context_no_context_id(self, service):
        """Test get context with missing context_id"""
        result = service.get_context("project", "")
        
        assert result["success"] is False
        assert "Context ID is required" in result["error"]
    
    def test_get_context_with_inheritance(self, service, sample_task_context, 
                                         sample_branch_context, sample_project_context):
        """Test get context with inheritance resolution"""
        context_id = "task-123"
        
        # Mock repository
        mock_repo = service.repositories[ContextLevel.TASK]
        mock_repo.get.return_value = sample_task_context
        
        # Mock inheritance resolution
        service._resolve_inheritance_sync = Mock(return_value={
            "id": context_id,
            "inherited_data": "test",
            "_inheritance": {"chain": ["global", "project", "branch", "task"]}
        })
        
        result = service.get_context("task", context_id, include_inherited=True)
        
        assert result["success"] is True
        assert result["inherited"] is True
        service._resolve_inheritance_sync.assert_called_once()
    
    def test_update_context_success(self, service, sample_project_context):
        """Test successful context update"""
        context_id = "project-123"
        update_data = {"project_settings": {"new_setting": "value"}}
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.get.return_value = sample_project_context
        updated_context = Mock(id=context_id)
        mock_repo.update.return_value = updated_context
        
        result = service.update_context("project", context_id, update_data)
        
        assert result["success"] is True
        assert result["context_id"] == context_id
        assert result["propagated"] is True
        mock_repo.update.assert_called_once_with(context_id, ANY)
    
    def test_update_context_not_found(self, service):
        """Test update context when not found"""
        context_id = "missing-123"
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.get.return_value = None
        
        result = service.update_context("project", context_id, {})
        
        assert result["success"] is False
        assert "Context not found" in result["error"]
    
    def test_update_context_merge_data(self, service):
        """Test context data merging"""
        existing_data = {
            "name": "Test",
            "settings": {"a": 1, "b": 2},
            "tags": ["tag1", "tag2"]
        }
        new_data = {
            "settings": {"b": 3, "c": 4},
            "tags": ["tag3"],
            "new_field": "value"
        }
        
        merged = service._merge_context_data(existing_data, new_data)
        
        assert merged["name"] == "Test"
        assert merged["settings"] == {"a": 1, "b": 3, "c": 4}
        assert merged["tags"] == ["tag1", "tag2", "tag3"]
        assert merged["new_field"] == "value"
        assert "updated_at" in merged
    
    def test_update_context_replace_list_fields(self, service):
        """Test that certain list fields are replaced, not extended"""
        existing_data = {
            "insights": ["old1", "old2"],
            "next_steps": ["step1"],
            "other_list": ["item1"]
        }
        new_data = {
            "insights": ["new1"],
            "next_steps": ["new_step"],
            "other_list": ["item2"]
        }
        
        merged = service._merge_context_data(existing_data, new_data)
        
        # insights and next_steps should be replaced
        assert merged["insights"] == ["new1"]
        assert merged["next_steps"] == ["new_step"]
        # other lists should be extended
        assert merged["other_list"] == ["item1", "item2"]
    
    def test_delete_context_success(self, service, sample_project_context):
        """Test successful context deletion"""
        context_id = "project-123"
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.get.return_value = sample_project_context
        mock_repo.delete.return_value = True
        
        result = service.delete_context("project", context_id)
        
        assert result["success"] is True
        assert result["context_id"] == context_id
        mock_repo.delete.assert_called_once_with(context_id)
    
    def test_delete_context_not_found(self, service):
        """Test delete context when not found"""
        context_id = "missing-123"
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.get.return_value = None
        
        result = service.delete_context("project", context_id)
        
        assert result["success"] is False
        assert "Context not found" in result["error"]
    
    def test_resolve_context(self, service, sample_project_context):
        """Test resolve context (get with inheritance)"""
        context_id = "project-123"
        
        # Mock get_context to return success
        service.get_context = Mock(return_value={
            "success": True,
            "context": {"id": context_id},
            "inherited": True
        })
        
        result = service.resolve_context("project", context_id)
        
        assert result["success"] is True
        assert result["resolved"] is True
        assert result["inheritance_applied"] is True
        
        # Verify get_context was called with inheritance
        service.get_context.assert_called_once_with(
            level="project",
            context_id=context_id,
            include_inherited=True,
            force_refresh=False
        )
    
    def test_list_contexts_success(self, service):
        """Test successful context listing"""
        contexts = [Mock(id=f"project-{i}") for i in range(3)]
        
        mock_repo = service.repositories[ContextLevel.PROJECT]
        mock_repo.list.return_value = contexts
        
        # Mock entity_to_dict
        service._entity_to_dict = Mock(side_effect=lambda x: {"id": x.id})
        
        result = service.list_contexts("project", {"filter": "value"})
        
        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["contexts"]) == 3
        mock_repo.list.assert_called_once_with(filters={"filter": "value"})
    
    def test_list_contexts_no_repository(self, service):
        """Test list contexts with no repository configured"""
        service.repositories[ContextLevel.PROJECT] = None
        
        result = service.list_contexts("project")
        
        assert result["success"] is False
        assert "No repository configured" in result["error"]
    
    def test_add_insight_success(self, service):
        """Test adding insight to context"""
        context_id = "task-123"
        content = "Important discovery"
        category = "technical"
        
        # Mock get_context and update_context
        service.get_context = Mock(return_value={
            "success": True,
            "context": {"insights": []}
        })
        service.update_context = Mock(return_value={"success": True})
        
        result = service.add_insight("task", context_id, content, category, "high", "agent-1")
        
        assert result["success"] is True
        
        # Verify update was called with new insight
        update_call = service.update_context.call_args
        insights = update_call[1]["data"]["insights"]
        assert len(insights) == 1
        assert insights[0]["content"] == content
        assert insights[0]["category"] == category
        assert insights[0]["importance"] == "high"
        assert insights[0]["agent"] == "agent-1"
    
    def test_add_progress_success(self, service):
        """Test adding progress update to context"""
        context_id = "task-123"
        content = "Completed step 1"
        
        # Mock get_context and update_context
        service.get_context = Mock(return_value={
            "success": True,
            "context": {"progress_updates": []}
        })
        service.update_context = Mock(return_value={"success": True})
        
        result = service.add_progress("task", context_id, content, "agent-2")
        
        assert result["success"] is True
        
        # Verify update was called with new progress
        update_call = service.update_context.call_args
        progress_updates = update_call[1]["data"]["progress_updates"]
        assert len(progress_updates) == 1
        assert progress_updates[0]["content"] == content
        assert progress_updates[0]["agent"] == "agent-2"
    
    def test_entity_to_dict_with_dict_method(self, service):
        """Test entity to dict conversion with dict method"""
        entity = Mock()
        entity.dict.return_value = {"id": "123", "data": "test"}
        
        result = service._entity_to_dict(entity)
        assert result == {"id": "123", "data": "test"}
    
    def test_entity_to_dict_with_vars(self, service):
        """Test entity to dict conversion using vars()"""
        class TestEntity:
            def __init__(self):
                self.id = "456"
                self.data = "test"
        
        entity = TestEntity()
        result = service._entity_to_dict(entity)
        assert result == {"id": "456", "data": "test"}
    
    def test_create_context_entity_global(self, service):
        """Test creation of global context entity"""
        data = {
            "organization_name": "Test Org",
            "global_settings": {"key": "value"},
            "metadata": {"source": "test"}
        }
        
        entity = service._create_context_entity(ContextLevel.GLOBAL, "global-id", data)
        
        assert isinstance(entity, GlobalContext)
        assert entity.id == "global-id"
        assert entity.organization_name == "Test Org"
        assert entity.global_settings == {"key": "value"}
    
    def test_create_context_entity_project(self, service):
        """Test creation of project context entity"""
        data = {
            "project_name": "Test Project",
            "project_settings": {"key": "value"},
            "metadata": {"source": "test"}
        }
        
        entity = service._create_context_entity(ContextLevel.PROJECT, "project-id", data)
        
        assert isinstance(entity, ProjectContext)
        assert entity.id == "project-id"
        assert entity.project_name == "Test Project"
    
    def test_create_context_entity_branch(self, service):
        """Test creation of branch context entity"""
        data = {
            "project_id": "project-123",
            "git_branch_name": "main",
            "branch_settings": {"workflow": "gitflow"},
            "metadata": {"source": "test"}
        }
        
        entity = service._create_context_entity(
            ContextLevel.BRANCH, "branch-id", data, user_id="test-user"
        )
        
        assert isinstance(entity, BranchContext)
        assert entity.id == "branch-id"
        assert entity.project_id == "project-123"
        assert entity.git_branch_name == "main"
        assert entity.metadata["user_id"] == "test-user"
    
    def test_create_context_entity_task(self, service):
        """Test creation of task context entity"""
        data = {
            "branch_id": "branch-123",
            "task_data": {"title": "Test Task"},
            "progress": 75,
            "insights": ["insight1"],
            "next_steps": ["step1"],
            "metadata": {"source": "test"}
        }
        
        entity = service._create_context_entity(ContextLevel.TASK, "task-id", data)
        
        assert isinstance(entity, TaskContext)
        assert entity.id == "task-id"
        assert entity.branch_id == "branch-123"
        assert entity.progress == 75
    
    def test_create_context_entity_task_branch_id_alternatives(self, service):
        """Test task entity creation with alternative branch_id fields"""
        # Test with parent_branch_id
        data = {"parent_branch_id": "branch-456", "task_data": {}}
        entity = service._create_context_entity(ContextLevel.TASK, "task-id", data)
        assert entity.branch_id == "branch-456"
        
        # Test with git_branch_id
        data = {"git_branch_id": "branch-789", "task_data": {}}
        entity = service._create_context_entity(ContextLevel.TASK, "task-id", data)
        assert entity.branch_id == "branch-789"
        
        # Test with no branch_id
        data = {"task_data": {}}
        with pytest.raises(ValueError) as exc_info:
            service._create_context_entity(ContextLevel.TASK, "task-id", data)
        assert "requires branch_id" in str(exc_info.value)
    
    def test_create_context_entity_invalid_level(self, service):
        """Test entity creation with invalid level"""
        with pytest.raises(ValueError) as exc_info:
            service._create_context_entity("invalid", "id", {})
        assert "Unknown context level" in str(exc_info.value)