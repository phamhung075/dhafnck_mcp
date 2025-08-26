"""Comprehensive test suite for Unified Context Service"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.application.services.context_cache_service import ContextCacheService
from fastmcp.task_management.application.services.context_inheritance_service import ContextInheritanceService
from fastmcp.task_management.application.services.context_delegation_service import ContextDelegationService
from fastmcp.task_management.application.services.context_validation_service import ContextValidationService
from fastmcp.task_management.application.services.context_hierarchy_validator import ContextHierarchyValidator
from fastmcp.task_management.domain.entities.context import GlobalContext, ProjectContext, BranchContext, TaskContextUnified as TaskContext
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel
from fastmcp.task_management.infrastructure.database.models import GLOBAL_SINGLETON_UUID


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
    def mock_services(self):
        """Create mock services"""
        return {
            'cache': Mock(spec=ContextCacheService),
            'inheritance': Mock(spec=ContextInheritanceService),
            'delegation': Mock(spec=ContextDelegationService),
            'validation': Mock(spec=ContextValidationService)
        }
    
    @pytest.fixture
    def service(self, mock_repositories, mock_services):
        """Create a UnifiedContextService instance"""
        return UnifiedContextService(
            global_context_repository=mock_repositories[ContextLevel.GLOBAL],
            project_context_repository=mock_repositories[ContextLevel.PROJECT],
            branch_context_repository=mock_repositories[ContextLevel.BRANCH],
            task_context_repository=mock_repositories[ContextLevel.TASK],
            cache_service=mock_services['cache'],
            inheritance_service=mock_services['inheritance'],
            delegation_service=mock_services['delegation'],
            validation_service=mock_services['validation'],
            user_id="test-user"
        )
    
    @pytest.fixture
    def sample_contexts(self):
        """Create sample contexts for testing"""
        return {
            'global': GlobalContext(
                id="global_singleton",
                organization_name="Test Organization",
                global_settings={"timezone": "UTC"},
                metadata={"version": "1.0"}
            ),
            'project': ProjectContext(
                id="project-123",
                project_name="Test Project",
                project_settings={"theme": "dark"},
                metadata={"created_by": "user1"}
            ),
            'branch': BranchContext(
                id="branch-456",
                project_id="project-123",
                git_branch_name="feature/test",
                branch_settings={"workflow": "agile"},
                metadata={"user_id": "test-user"}
            ),
            'task': TaskContext(
                id="task-789",
                branch_id="branch-456",
                task_data={"title": "Test Task"},
                progress=50,
                insights=["Test insight"],
                next_steps=["Next step"],
                metadata={"priority": "high"}
            )
        }
    
    def test_init(self, mock_repositories, mock_services):
        """Test service initialization"""
        service = UnifiedContextService(
            global_context_repository=mock_repositories[ContextLevel.GLOBAL],
            project_context_repository=mock_repositories[ContextLevel.PROJECT],
            branch_context_repository=mock_repositories[ContextLevel.BRANCH],
            task_context_repository=mock_repositories[ContextLevel.TASK],
            user_id="test-user"
        )
        
        assert service._user_id == "test-user"
        assert service.repositories == mock_repositories
        assert isinstance(service.cache_service, ContextCacheService)
        assert isinstance(service.inheritance_service, ContextInheritanceService)
        assert isinstance(service.delegation_service, ContextDelegationService)
        assert isinstance(service.validation_service, ContextValidationService)
        assert isinstance(service.hierarchy_validator, ContextHierarchyValidator)
    
    def test_with_user(self, service):
        """Test creating user-scoped service instance"""
        new_service = service.with_user("new-user")
        
        assert isinstance(new_service, UnifiedContextService)
        assert new_service._user_id == "new-user"
        assert new_service.repositories == service.repositories
        assert new_service.cache_service == service.cache_service
    
    def test_get_user_scoped_repository(self, service, mock_repositories):
        """Test getting user-scoped repository"""
        # Test with repository that has with_user method
        mock_repo = Mock()
        mock_repo.with_user = Mock(return_value="scoped_repo")
        
        result = service._get_user_scoped_repository(mock_repo)
        assert result == "scoped_repo"
        mock_repo.with_user.assert_called_once_with("test-user")
        
        # Test with repository without with_user method
        mock_repo_no_user = Mock(spec=[])
        result = service._get_user_scoped_repository(mock_repo_no_user)
        assert result == mock_repo_no_user
    
    def test_normalize_context_id(self, service):
        """Test context ID normalization"""
        # Test global singleton normalization
        result = service._normalize_context_id("global", "global_singleton")
        assert result == GLOBAL_SINGLETON_UUID
        
        # Test other levels - no normalization
        result = service._normalize_context_id("project", "project-123")
        assert result == "project-123"
        
        result = service._normalize_context_id("branch", "branch-456")
        assert result == "branch-456"
    
    @patch('fastmcp.task_management.application.services.unified_context_service.datetime')
    def test_create_context_global_success(self, mock_datetime, service, mock_repositories, mock_services):
        """Test successful global context creation"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock validation
        mock_services['validation'].validate_context_data.return_value = {"valid": True}
        
        # Mock hierarchy validation
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock repository
        created_context = GlobalContext(
            id="global_singleton",
            organization_name="Test Org",
            global_settings={"setting": "value"},
            metadata={"created": True}
        )
        mock_repositories[ContextLevel.GLOBAL].create.return_value = created_context
        
        # Create context
        result = service.create_context(
            level="global",
            context_id="global_singleton",
            data={
                "organization_name": "Test Org",
                "global_settings": {"setting": "value"},
                "metadata": {"created": True}
            }
        )
        
        # Verify result
        assert result["success"] is True
        assert result["context"]["organization_name"] == "Test Org"
        assert result["level"] == "global"
        assert result["context_id"] == GLOBAL_SINGLETON_UUID
    
    def test_create_context_project_with_auto_parent_creation(self, service, mock_repositories, mock_services):
        """Test project context creation with automatic parent creation"""
        # Mock validation
        mock_services['validation'].validate_context_data.return_value = {"valid": True}
        
        # Mock hierarchy validation to fail first, then succeed
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            side_effect=[
                (False, "Global context missing", {"suggestion": "Create global context"}),
                (True, None, None)
            ]
        )
        
        # Mock auto-creation
        service._auto_create_parent_contexts = Mock(return_value=True)
        
        # Mock repository
        created_context = ProjectContext(
            id="project-123",
            project_name="Test Project",
            project_settings={},
            metadata={}
        )
        mock_repositories[ContextLevel.PROJECT].create.return_value = created_context
        
        # Create context
        result = service.create_context(
            level="project",
            context_id="project-123",
            data={"project_name": "Test Project"}
        )
        
        # Verify auto-creation was attempted
        service._auto_create_parent_contexts.assert_called_once()
        assert result["success"] is True
        assert result["context"]["project_name"] == "Test Project"
    
    @patch('fastmcp.task_management.application.services.unified_context_service.GitBranchRepositoryFactory')
    def test_create_context_branch_auto_detect_project_id(self, mock_factory, service, mock_repositories, mock_services):
        """Test branch context creation with auto-detected project ID"""
        # Mock validation
        mock_services['validation'].validate_context_data.return_value = {"valid": True}
        
        # Mock hierarchy validation
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock git branch repository
        mock_git_repo = Mock()
        mock_branch = Mock()
        mock_branch.project_id = "auto-project-123"
        mock_git_repo.get.return_value = mock_branch
        mock_factory.return_value.create.return_value = mock_git_repo
        
        # Mock repository
        created_context = BranchContext(
            id="branch-456",
            project_id="auto-project-123",
            git_branch_name="main",
            branch_settings={},
            metadata={}
        )
        mock_repositories[ContextLevel.BRANCH].create.return_value = created_context
        
        # Create context without project_id
        result = service.create_context(
            level="branch",
            context_id="branch-456",
            data={"git_branch_name": "main"}
        )
        
        # Verify project_id was auto-detected
        assert result["success"] is True
        assert result["context"]["project_id"] == "auto-project-123"
    
    @patch('fastmcp.task_management.application.services.unified_context_service.TaskRepositoryFactory')
    def test_create_context_task_auto_detect_git_branch_id(self, mock_factory, service, mock_repositories, mock_services):
        """Test task context creation with auto-detected git_branch_id"""
        # Mock validation
        mock_services['validation'].validate_context_data.return_value = {"valid": True}
        
        # Mock hierarchy validation
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock task repository
        mock_task_repo = Mock()
        mock_task = Mock()
        mock_task.git_branch_id = "auto-branch-456"
        mock_task_repo.get.return_value = mock_task
        mock_factory.return_value.create.return_value = mock_task_repo
        
        # Mock repository
        created_context = TaskContext(
            id="task-789",
            branch_id="auto-branch-456",
            task_data={"title": "Test Task"},
            progress=0,
            insights=[],
            next_steps=[],
            metadata={}
        )
        mock_repositories[ContextLevel.TASK].create.return_value = created_context
        
        # Create context without branch_id
        result = service.create_context(
            level="task",
            context_id="task-789",
            data={"task_data": {"title": "Test Task"}}
        )
        
        # Verify git_branch_id was auto-detected
        assert result["success"] is True
        assert result["context"]["branch_id"] == "auto-branch-456"
    
    def test_create_context_validation_failure(self, service, mock_services):
        """Test context creation with validation failure"""
        # Mock hierarchy validation success
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            return_value=(True, None, None)
        )
        
        # Mock validation failure
        mock_services['validation'].validate_context_data.return_value = {
            "valid": False,
            "errors": ["Missing required field: project_name"]
        }
        
        # Create context
        result = service.create_context(
            level="project",
            context_id="project-123",
            data={}
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Validation failed" in result["error"]
        assert "Missing required field" in result["error"]
    
    def test_create_context_repository_not_configured(self, service):
        """Test context creation with unconfigured repository"""
        # Remove project repository
        service.repositories.pop(ContextLevel.PROJECT)
        
        # Create context
        result = service.create_context(
            level="project",
            context_id="project-123",
            data={"project_name": "Test"}
        )
        
        # Verify failure
        assert result["success"] is False
        assert "No repository configured" in result["error"]
    
    def test_create_context_exception(self, service, mock_services):
        """Test context creation with exception"""
        # Mock validation to raise exception
        mock_services['validation'].validate_context_data.side_effect = Exception(
            "Database connection lost"
        )
        
        # Create context
        result = service.create_context(
            level="global",
            context_id="global_singleton",
            data={"organization_name": "Test"}
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Database connection lost" in result["error"]
    
    def test_get_context_success(self, service, mock_repositories, sample_contexts):
        """Test successful context retrieval"""
        # Mock repository
        mock_repositories[ContextLevel.PROJECT].get.return_value = sample_contexts['project']
        
        # Get context
        result = service.get_context(
            level="project",
            context_id="project-123"
        )
        
        # Verify result
        assert result["success"] is True
        assert result["context"]["project_name"] == "Test Project"
        assert result["level"] == "project"
        assert result["inherited"] is False
    
    def test_get_context_with_inheritance(self, service, mock_repositories, sample_contexts):
        """Test context retrieval with inheritance"""
        # Mock repositories
        mock_repositories[ContextLevel.TASK].get.return_value = sample_contexts['task']
        mock_repositories[ContextLevel.BRANCH].get.return_value = sample_contexts['branch']
        mock_repositories[ContextLevel.PROJECT].get.return_value = sample_contexts['project']
        mock_repositories[ContextLevel.GLOBAL].get.return_value = sample_contexts['global']
        
        # Mock inheritance service
        service.inheritance_service.inherit_task_from_branch = Mock(
            side_effect=lambda base, child: {**base, **child}
        )
        service.inheritance_service.inherit_branch_from_project = Mock(
            side_effect=lambda base, child: {**base, **child}
        )
        service.inheritance_service.inherit_project_from_global = Mock(
            side_effect=lambda base, child: {**base, **child}
        )
        
        # Get context with inheritance
        result = service.get_context(
            level="task",
            context_id="task-789",
            include_inherited=True
        )
        
        # Verify result
        assert result["success"] is True
        assert result["inherited"] is True
        assert "_inheritance" in result["context"]
        assert result["context"]["_inheritance"]["inheritance_depth"] == 4
    
    def test_get_context_not_found(self, service, mock_repositories):
        """Test context retrieval when not found"""
        # Mock repository to return None
        mock_repositories[ContextLevel.PROJECT].get.return_value = None
        
        # Get context
        result = service.get_context(
            level="project",
            context_id="nonexistent-project"
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Context not found" in result["error"]
    
    def test_get_context_exception(self, service, mock_repositories):
        """Test context retrieval with exception"""
        # Mock repository to raise exception
        mock_repositories[ContextLevel.PROJECT].get.side_effect = Exception(
            "Query timeout"
        )
        
        # Get context
        result = service.get_context(
            level="project",
            context_id="project-123"
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Query timeout" in result["error"]
    
    @patch('fastmcp.task_management.application.services.unified_context_service.datetime')
    def test_update_context_success(self, mock_datetime, service, mock_repositories, sample_contexts):
        """Test successful context update"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock repository
        existing_context = sample_contexts['project']
        mock_repositories[ContextLevel.PROJECT].get.return_value = existing_context
        
        updated_context = ProjectContext(
            id="project-123",
            project_name="Updated Project",
            project_settings={"theme": "light"},
            metadata={"updated": True}
        )
        mock_repositories[ContextLevel.PROJECT].update.return_value = updated_context
        
        # Update context
        result = service.update_context(
            level="project",
            context_id="project-123",
            data={
                "project_name": "Updated Project",
                "project_settings": {"theme": "light"}
            }
        )
        
        # Verify result
        assert result["success"] is True
        assert result["context"]["project_name"] == "Updated Project"
        assert result["context"]["project_settings"]["theme"] == "light"
        assert result["propagated"] is True
    
    def test_update_context_not_found(self, service, mock_repositories):
        """Test context update when not found"""
        # Mock repository to return None
        mock_repositories[ContextLevel.PROJECT].get.return_value = None
        
        # Update context
        result = service.update_context(
            level="project",
            context_id="nonexistent-project",
            data={"project_name": "Updated"}
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Context not found" in result["error"]
    
    def test_update_context_merge_data(self, service, mock_repositories, sample_contexts):
        """Test context update with data merging"""
        # Mock repository
        existing_context = sample_contexts['project']
        mock_repositories[ContextLevel.PROJECT].get.return_value = existing_context
        
        # Test merge
        merged_data = service._merge_context_data(
            existing_data={
                "project_settings": {"theme": "dark", "language": "en"},
                "metadata": {"version": "1.0"}
            },
            new_data={
                "project_settings": {"theme": "light"},
                "metadata": {"updated_by": "user2"}
            }
        )
        
        # Verify merge
        assert merged_data["project_settings"]["theme"] == "light"
        assert merged_data["project_settings"]["language"] == "en"
        assert merged_data["metadata"]["version"] == "1.0"
        assert merged_data["metadata"]["updated_by"] == "user2"
        assert "updated_at" in merged_data
    
    def test_delete_context_success(self, service, mock_repositories, sample_contexts):
        """Test successful context deletion"""
        # Mock repository
        mock_repositories[ContextLevel.PROJECT].get.return_value = sample_contexts['project']
        mock_repositories[ContextLevel.PROJECT].delete.return_value = True
        
        # Delete context
        result = service.delete_context(
            level="project",
            context_id="project-123"
        )
        
        # Verify result
        assert result["success"] is True
        assert result["level"] == "project"
        assert result["context_id"] == "project-123"
    
    def test_delete_context_not_found(self, service, mock_repositories):
        """Test context deletion when not found"""
        # Mock repository to return None
        mock_repositories[ContextLevel.PROJECT].get.return_value = None
        
        # Delete context
        result = service.delete_context(
            level="project",
            context_id="nonexistent-project"
        )
        
        # Verify failure
        assert result["success"] is False
        assert "Context not found" in result["error"]
    
    def test_resolve_context_success(self, service):
        """Test context resolution with inheritance"""
        # Mock get_context to return success
        expected_result = {
            "success": True,
            "context": {"data": "value"},
            "level": "task",
            "context_id": "task-123",
            "inherited": True
        }
        service.get_context = Mock(return_value=expected_result)
        
        # Resolve context
        result = service.resolve_context(
            level="task",
            context_id="task-123"
        )
        
        # Verify result
        assert result["success"] is True
        assert result["resolved"] is True
        assert result["inheritance_applied"] is True
        service.get_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            include_inherited=True,
            force_refresh=False
        )
    
    def test_delegate_context_success(self, service):
        """Test context delegation"""
        # Delegate context
        result = service.delegate_context(
            level="task",
            context_id="task-123",
            delegate_to="project",
            data={"pattern": "reusable_pattern"},
            delegation_reason="Pattern is reusable across tasks"
        )
        
        # Verify result (delegation is skipped in sync mode)
        assert result["success"] is True
        assert result["source_level"] == "task"
        assert result["target_level"] == "project"
        assert "Delegation skipped in sync mode" in result["delegation"]["message"]
    
    def test_list_contexts_success(self, service, mock_repositories, sample_contexts):
        """Test successful context listing"""
        # Mock repository
        mock_repositories[ContextLevel.PROJECT].list.return_value = [
            sample_contexts['project'],
            ProjectContext(
                id="project-456",
                project_name="Another Project",
                project_settings={},
                metadata={}
            )
        ]
        
        # List contexts
        result = service.list_contexts(
            level="project",
            filters={"active": True}
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["contexts"]) == 2
        assert result["contexts"][0]["project_name"] == "Test Project"
        assert result["count"] == 2
    
    @patch('fastmcp.task_management.application.services.unified_context_service.datetime')
    def test_add_insight_success(self, mock_datetime, service):
        """Test adding insight to context"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock get_context
        service.get_context = Mock(return_value={
            "success": True,
            "context": {"insights": []}
        })
        
        # Mock update_context
        service.update_context = Mock(return_value={
            "success": True,
            "context": {"insights": [{"content": "Test insight"}]}
        })
        
        # Add insight
        result = service.add_insight(
            level="task",
            context_id="task-123",
            content="Test insight",
            category="performance",
            importance="high",
            agent="test-agent"
        )
        
        # Verify result
        assert result["success"] is True
        service.update_context.assert_called_once()
        update_call = service.update_context.call_args[1]
        assert len(update_call["data"]["insights"]) == 1
        assert update_call["data"]["insights"][0]["content"] == "Test insight"
        assert update_call["data"]["insights"][0]["category"] == "performance"
    
    @patch('fastmcp.task_management.application.services.unified_context_service.datetime')
    def test_add_progress_success(self, mock_datetime, service):
        """Test adding progress update to context"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        
        # Mock get_context
        service.get_context = Mock(return_value={
            "success": True,
            "context": {"progress_updates": []}
        })
        
        # Mock update_context
        service.update_context = Mock(return_value={
            "success": True,
            "context": {"progress_updates": [{"content": "Progress made"}]}
        })
        
        # Add progress
        result = service.add_progress(
            level="task",
            context_id="task-123",
            content="Progress made",
            agent="test-agent"
        )
        
        # Verify result
        assert result["success"] is True
        service.update_context.assert_called_once()
        update_call = service.update_context.call_args[1]
        assert len(update_call["data"]["progress_updates"]) == 1
        assert update_call["data"]["progress_updates"][0]["content"] == "Progress made"
    
    def test_create_context_entity_global(self, service):
        """Test creating global context entity"""
        entity = service._create_context_entity(
            level=ContextLevel.GLOBAL,
            context_id="global_singleton",
            data={
                "organization_name": "Test Org",
                "global_settings": {"setting": "value"},
                "metadata": {"key": "value"}
            }
        )
        
        assert isinstance(entity, GlobalContext)
        assert entity.id == "global_singleton"
        assert entity.organization_name == "Test Org"
        assert entity.global_settings["setting"] == "value"
    
    def test_create_context_entity_project(self, service):
        """Test creating project context entity"""
        entity = service._create_context_entity(
            level=ContextLevel.PROJECT,
            context_id="project-123",
            data={
                "project_name": "Test Project",
                "project_settings": {"theme": "dark"},
                "metadata": {"owner": "user1"}
            }
        )
        
        assert isinstance(entity, ProjectContext)
        assert entity.id == "project-123"
        assert entity.project_name == "Test Project"
        assert entity.project_settings["theme"] == "dark"
    
    def test_create_context_entity_branch(self, service):
        """Test creating branch context entity"""
        entity = service._create_context_entity(
            level=ContextLevel.BRANCH,
            context_id="branch-456",
            data={
                "project_id": "project-123",
                "git_branch_name": "feature/test",
                "branch_settings": {"workflow": "agile"}
            },
            user_id="test-user"
        )
        
        assert isinstance(entity, BranchContext)
        assert entity.id == "branch-456"
        assert entity.project_id == "project-123"
        assert entity.git_branch_name == "feature/test"
        assert entity.metadata["user_id"] == "test-user"
    
    def test_create_context_entity_task(self, service):
        """Test creating task context entity"""
        entity = service._create_context_entity(
            level=ContextLevel.TASK,
            context_id="task-789",
            data={
                "branch_id": "branch-456",
                "task_data": {"title": "Test Task"},
                "progress": 25,
                "insights": ["insight1"],
                "next_steps": ["step1"]
            }
        )
        
        assert isinstance(entity, TaskContext)
        assert entity.id == "task-789"
        assert entity.branch_id == "branch-456"
        assert entity.task_data["title"] == "Test Task"
        assert entity.progress == 25
    
    def test_create_context_entity_task_backward_compatibility(self, service):
        """Test creating task context with backward compatibility fields"""
        # Test with parent_branch_id
        entity = service._create_context_entity(
            level=ContextLevel.TASK,
            context_id="task-789",
            data={
                "parent_branch_id": "branch-456",
                "task_data": {"title": "Test Task"}
            }
        )
        assert entity.branch_id == "branch-456"
        
        # Test with git_branch_id
        entity = service._create_context_entity(
            level=ContextLevel.TASK,
            context_id="task-789",
            data={
                "git_branch_id": "branch-789",
                "task_data": {"title": "Test Task"}
            }
        )
        assert entity.branch_id == "branch-789"
    
    def test_auto_create_context_if_missing_already_exists(self, service, mock_repositories, sample_contexts):
        """Test auto-creation when context already exists"""
        # Mock get_context to return existing
        service.get_context = Mock(return_value={
            "success": True,
            "context": {"existing": True}
        })
        
        # Auto-create
        result = service.auto_create_context_if_missing(
            level="project",
            context_id="project-123"
        )
        
        # Verify no creation attempted
        assert result["success"] is True
        assert result["context"]["existing"] is True
        service.get_context.assert_called_once()
    
    def test_auto_create_context_if_missing_creates_new(self, service):
        """Test auto-creation when context doesn't exist"""
        # Mock get_context to return not found
        service.get_context = Mock(return_value={
            "success": False,
            "error": "Context not found"
        })
        
        # Mock create_context to succeed
        service.create_context = Mock(return_value={
            "success": True,
            "context": {"new": True}
        })
        
        # Auto-create
        result = service.auto_create_context_if_missing(
            level="project",
            context_id="project-123",
            data={"project_name": "Auto Project"}
        )
        
        # Verify creation attempted
        assert result["success"] is True
        assert result["created"] is True
        service.create_context.assert_called_once()
    
    def test_build_default_context_data(self, service):
        """Test building default context data for auto-creation"""
        # Test global defaults
        data = service._build_default_context_data(
            level="global",
            context_id="global_singleton"
        )
        assert data["organization_name"] == "Default Organization"
        assert data["global_settings"]["default_timezone"] == "UTC"
        assert data["metadata"]["auto_created"] is True
        
        # Test project defaults
        data = service._build_default_context_data(
            level="project",
            context_id="proj-123"
        )
        assert data["project_name"] == "Project proj-123"
        assert data["project_settings"]["auto_context_creation"] is True
        
        # Test branch defaults
        data = service._build_default_context_data(
            level="branch",
            context_id="branch-456",
            project_id="proj-123"
        )
        assert data["project_id"] == "proj-123"
        assert data["git_branch_name"] == "main"
        assert data["branch_settings"]["auto_created"] is True
        
        # Test task defaults
        data = service._build_default_context_data(
            level="task",
            context_id="task-789",
            git_branch_id="branch-456"
        )
        assert data["branch_id"] == "branch-456"
        assert data["task_data"]["title"] == "Task task-789"
        assert data["progress"] == 0
    
    @patch('fastmcp.task_management.application.services.unified_context_service.UnifiedContextFacadeFactory')
    def test_create_context_task_alternative_validation(self, mock_factory, service, mock_services):
        """Test task context creation with alternative validation approach"""
        # Mock validation
        mock_services['validation'].validate_context_data.return_value = {"valid": True}
        
        # Mock hierarchy validation to fail initially
        service.hierarchy_validator.validate_hierarchy_requirements = Mock(
            side_effect=[
                (False, "Branch context missing", None),
                (True, None, None)
            ]
        )
        
        # Mock auto-creation to fail
        service._auto_create_parent_contexts = Mock(return_value=False)
        
        # Mock alternative validation through facade
        mock_facade = Mock()
        mock_facade.get_context.return_value = {"success": True, "context": {}}
        mock_factory.return_value.create_facade.return_value = mock_facade
        
        # Mock repository
        created_context = TaskContext(
            id="task-789",
            branch_id="branch-456",
            task_data={"title": "Test Task"},
            progress=0,
            insights=[],
            next_steps=[],
            metadata={}
        )
        service.repositories[ContextLevel.TASK].create.return_value = created_context
        
        # Create context
        result = service.create_context(
            level="task",
            context_id="task-789",
            data={
                "git_branch_id": "branch-456",
                "task_data": {"title": "Test Task"}
            }
        )
        
        # Verify alternative validation was used
        assert result["success"] is True
        mock_facade.get_context.assert_called_once_with(
            level="branch",
            context_id="branch-456"
        )
    
    def test_auto_create_parent_contexts_project(self, service):
        """Test auto-creating parent contexts for project"""
        # Mock atomic creation
        service._create_hierarchy_atomically = Mock(return_value=True)
        
        # Auto-create parents for project
        result = service._auto_create_parent_contexts(
            target_level=ContextLevel.PROJECT,
            context_id="project-123",
            data={}
        )
        
        # Verify global context creation attempted
        assert result is True
        service._create_hierarchy_atomically.assert_called_once()
        call_args = service._create_hierarchy_atomically.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0][0] == ContextLevel.GLOBAL
    
    def test_auto_create_parent_contexts_branch(self, service):
        """Test auto-creating parent contexts for branch"""
        # Mock atomic creation
        service._create_hierarchy_atomically = Mock(return_value=True)
        
        # Auto-create parents for branch
        result = service._auto_create_parent_contexts(
            target_level=ContextLevel.BRANCH,
            context_id="branch-456",
            data={"project_id": "project-123"},
            project_id="project-123"
        )
        
        # Verify global and project context creation attempted
        assert result is True
        service._create_hierarchy_atomically.assert_called_once()
        call_args = service._create_hierarchy_atomically.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0][0] == ContextLevel.GLOBAL
        assert call_args[1][0] == ContextLevel.PROJECT
    
    @patch('fastmcp.task_management.application.services.unified_context_service.GitBranchRepositoryFactory')
    def test_auto_create_parent_contexts_task_with_branch_lookup(self, mock_factory, service):
        """Test auto-creating parent contexts for task with branch lookup"""
        # Mock atomic creation
        service._create_hierarchy_atomically = Mock(return_value=True)
        
        # Mock resolve_project_id_from_branch
        service._resolve_project_id_from_branch = Mock(return_value="resolved-project-123")
        
        # Auto-create parents for task
        result = service._auto_create_parent_contexts(
            target_level=ContextLevel.TASK,
            context_id="task-789",
            data={"branch_id": "branch-456"}
        )
        
        # Verify all parent contexts creation attempted
        assert result is True
        service._create_hierarchy_atomically.assert_called_once()
        call_args = service._create_hierarchy_atomically.call_args[0][0]
        assert len(call_args) == 3
        assert call_args[0][0] == ContextLevel.GLOBAL
        assert call_args[1][0] == ContextLevel.PROJECT
        assert call_args[2][0] == ContextLevel.BRANCH
    
    def test_create_context_atomically_exists(self, service, mock_repositories, sample_contexts):
        """Test atomic context creation when context already exists"""
        # Mock repository to return existing context
        mock_repositories[ContextLevel.PROJECT].get.return_value = sample_contexts['project']
        
        # Create atomically
        result = service._create_context_atomically(
            level=ContextLevel.PROJECT,
            context_id="project-123",
            data={}
        )
        
        # Verify no creation attempted
        assert result is True
        mock_repositories[ContextLevel.PROJECT].create.assert_not_called()
    
    def test_create_context_atomically_creates_new(self, service, mock_repositories):
        """Test atomic context creation when context doesn't exist"""
        # Mock repository get to return None
        mock_repositories[ContextLevel.PROJECT].get.return_value = None
        
        # Mock repository create
        created_context = ProjectContext(
            id="project-123",
            project_name="Auto Project",
            project_settings={},
            metadata={}
        )
        mock_repositories[ContextLevel.PROJECT].create.return_value = created_context
        
        # Create atomically
        result = service._create_context_atomically(
            level=ContextLevel.PROJECT,
            context_id="project-123",
            data={"project_name": "Auto Project"}
        )
        
        # Verify creation attempted
        assert result is True
        mock_repositories[ContextLevel.PROJECT].create.assert_called_once()
    
    @patch('fastmcp.task_management.application.services.unified_context_service.GitBranchRepositoryFactory')
    def test_resolve_project_id_from_branch_success(self, mock_factory, service):
        """Test resolving project ID from branch"""
        # Mock git branch repository
        mock_git_repo = Mock()
        mock_branch = Mock()
        mock_branch.project_id = "resolved-project-123"
        mock_git_repo.get.return_value = mock_branch
        mock_factory.return_value.create.return_value = mock_git_repo
        
        # Resolve project ID
        result = service._resolve_project_id_from_branch("branch-456")
        
        # Verify resolution
        assert result == "resolved-project-123"
        mock_git_repo.get.assert_called_once_with("branch-456")
    
    def test_resolve_project_id_from_branch_fallback(self, service, mock_repositories, sample_contexts):
        """Test resolving project ID from branch with fallback"""
        # Mock primary resolution to fail
        with patch('fastmcp.task_management.application.services.unified_context_service.GitBranchRepositoryFactory') as mock_factory:
            mock_factory.side_effect = Exception("Factory error")
            
            # Mock fallback through context repository
            mock_repositories[ContextLevel.BRANCH].get.return_value = sample_contexts['branch']
            
            # Resolve project ID
            result = service._resolve_project_id_from_branch("branch-456")
            
            # Verify fallback used
            assert result == "project-123"
            mock_repositories[ContextLevel.BRANCH].get.assert_called_once_with("branch-456")