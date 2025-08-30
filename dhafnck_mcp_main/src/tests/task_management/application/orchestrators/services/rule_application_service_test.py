"""Test for Rule Application Service"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from fastmcp.task_management.application.orchestrators.services.rule_application_service import RuleApplicationService
from fastmcp.task_management.domain.entities.rule_entity import Rule
from fastmcp.task_management.domain.enums.rule_enums import RuleFormat, RuleType


class TestRuleApplicationService:
    """Test suite for RuleApplicationService"""
    
    @pytest.fixture
    def mock_rule_repository(self):
        """Create a mock rule repository"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_rule_repository):
        """Create a rule application service instance"""
        return RuleApplicationService(mock_rule_repository)
    
    @pytest.fixture
    def sample_rule(self):
        """Create a sample rule"""
        rule = Mock(spec=Rule)
        rule.metadata = Mock()
        rule.metadata.path = "/test/rule/path"
        rule.metadata.type = RuleType.VALIDATION
        rule.metadata.format = RuleFormat.YAML
        rule.metadata.description = "Test rule"
        rule.metadata.tags = ["test", "sample"]
        rule.content = "test rule content"
        return rule
    
    def test_init(self, mock_rule_repository):
        """Test service initialization"""
        service = RuleApplicationService(mock_rule_repository)
        assert service._rule_repository == mock_rule_repository
        assert service._user_id is None
        assert hasattr(service, '_create_rule_use_case')
        assert hasattr(service, '_get_rule_use_case')
        assert hasattr(service, '_list_rules_use_case')
        assert hasattr(service, '_update_rule_use_case')
        assert hasattr(service, '_delete_rule_use_case')
        assert hasattr(service, '_validate_rule_use_case')
    
    def test_init_with_user_id(self, mock_rule_repository):
        """Test service initialization with user_id"""
        user_id = "test-user-123"
        service = RuleApplicationService(mock_rule_repository, user_id=user_id)
        assert service._user_id == user_id
    
    def test_with_user(self, service):
        """Test creating user-scoped service"""
        user_id = "test-user-456"
        user_scoped_service = service.with_user(user_id)
        assert isinstance(user_scoped_service, RuleApplicationService)
        assert user_scoped_service._user_id == user_id
        assert user_scoped_service._rule_repository == service._rule_repository
    
    def test_get_user_scoped_repository_no_repository(self, service):
        """Test getting user-scoped repository with None repository"""
        result = service._get_user_scoped_repository(None)
        assert result is None
    
    def test_get_user_scoped_repository_with_user_method(self):
        """Test getting user-scoped repository with with_user method"""
        mock_repo = Mock()
        mock_scoped_repo = Mock()
        mock_repo.with_user.return_value = mock_scoped_repo
        
        service = RuleApplicationService(mock_repo, user_id="test-user")
        result = service._get_user_scoped_repository(mock_repo)
        
        mock_repo.with_user.assert_called_once_with("test-user")
        assert result == mock_scoped_repo
    
    def test_get_user_scoped_repository_with_user_property(self):
        """Test getting user-scoped repository with user_id property"""
        mock_repo = Mock()
        mock_repo.with_user = None  # No with_user method
        mock_repo.user_id = "different-user"
        mock_repo.session = Mock()
        
        with patch('fastmcp.task_management.application.orchestrators.services.rule_application_service.type') as mock_type:
            MockRepoClass = Mock()
            mock_type.return_value = MockRepoClass
            mock_scoped_repo = Mock()
            MockRepoClass.return_value = mock_scoped_repo
            
            service = RuleApplicationService(mock_repo, user_id="test-user")
            result = service._get_user_scoped_repository(mock_repo)
            
            MockRepoClass.assert_called_once_with(mock_repo.session, user_id="test-user")
            assert result == mock_scoped_repo
    
    @pytest.mark.asyncio
    async def test_create_rule(self, service):
        """Test create rule"""
        rule_path = "/test/rule"
        content = "rule content"
        rule_type = RuleType.VALIDATION
        rule_format = RuleFormat.YAML
        metadata = {"key": "value"}
        expected_result = {"success": True, "rule_path": rule_path}
        
        service._create_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.create_rule(rule_path, content, rule_type, rule_format, metadata)
        
        service._create_rule_use_case.execute.assert_called_once_with(
            rule_path=rule_path,
            content=content,
            rule_type=rule_type,
            rule_format=rule_format,
            metadata=metadata
        )
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_rule(self, service):
        """Test get rule"""
        rule_path = "/test/rule"
        expected_result = {"success": True, "rule": {"path": rule_path}}
        
        service._get_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.get_rule(rule_path)
        
        service._get_rule_use_case.execute.assert_called_once_with(rule_path)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_list_rules(self, service):
        """Test list rules"""
        filters = {"type": "validation"}
        metadata_only = True
        expected_result = {"success": True, "rules": []}
        
        service._list_rules_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.list_rules(filters, metadata_only)
        
        service._list_rules_use_case.execute.assert_called_once_with(filters, metadata_only)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_list_rules_default_params(self, service):
        """Test list rules with default parameters"""
        expected_result = {"success": True, "rules": []}
        
        service._list_rules_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.list_rules()
        
        service._list_rules_use_case.execute.assert_called_once_with(None, False)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_update_rule(self, service):
        """Test update rule"""
        rule_path = "/test/rule"
        content = "updated content"
        metadata_updates = {"key": "new_value"}
        expected_result = {"success": True, "rule_path": rule_path}
        
        service._update_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.update_rule(rule_path, content, metadata_updates)
        
        service._update_rule_use_case.execute.assert_called_once_with(
            rule_path=rule_path,
            content=content,
            metadata_updates=metadata_updates
        )
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_delete_rule(self, service):
        """Test delete rule"""
        rule_path = "/test/rule"
        force = True
        expected_result = {"success": True, "deleted": rule_path}
        
        service._delete_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.delete_rule(rule_path, force)
        
        service._delete_rule_use_case.execute.assert_called_once_with(rule_path, force)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_delete_rule_default_force(self, service):
        """Test delete rule with default force parameter"""
        rule_path = "/test/rule"
        expected_result = {"success": True}
        
        service._delete_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.delete_rule(rule_path)
        
        service._delete_rule_use_case.execute.assert_called_once_with(rule_path, False)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_validate_rule(self, service):
        """Test validate rule"""
        rule_path = "/test/rule"
        expected_result = {"success": True, "valid": True}
        
        service._validate_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.validate_rule(rule_path)
        
        service._validate_rule_use_case.execute.assert_called_once_with(rule_path)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_validate_rule_all(self, service):
        """Test validate all rules"""
        expected_result = {"success": True, "valid": True}
        
        service._validate_rule_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.validate_rule()
        
        service._validate_rule_use_case.execute.assert_called_once_with(None)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_backup_rules_success(self, service):
        """Test successful rules backup"""
        backup_path = "/backup/rules.tar.gz"
        
        mock_repo = Mock()
        mock_repo.backup_rules = Mock(return_value=True)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.backup_rules(backup_path)
        
        assert result["success"] is True
        assert backup_path in result["message"]
        assert result["backup_path"] == backup_path
        mock_repo.backup_rules.assert_called_once_with(backup_path)
    
    @pytest.mark.asyncio
    async def test_backup_rules_failure(self, service):
        """Test failed rules backup"""
        backup_path = "/backup/rules.tar.gz"
        
        mock_repo = Mock()
        mock_repo.backup_rules = Mock(return_value=False)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.backup_rules(backup_path)
        
        assert result["success"] is False
        assert result["error"] == "Failed to backup rules"
    
    @pytest.mark.asyncio
    async def test_backup_rules_exception(self, service):
        """Test rules backup with exception"""
        backup_path = "/backup/rules.tar.gz"
        
        mock_repo = Mock()
        mock_repo.backup_rules = Mock(side_effect=Exception("Backup error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.backup_rules(backup_path)
        
        assert result["success"] is False
        assert "Backup error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_restore_rules_success(self, service):
        """Test successful rules restore"""
        backup_path = "/backup/rules.tar.gz"
        
        mock_repo = Mock()
        mock_repo.restore_rules = Mock(return_value=True)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.restore_rules(backup_path)
        
        assert result["success"] is True
        assert backup_path in result["message"]
        assert result["backup_path"] == backup_path
        mock_repo.restore_rules.assert_called_once_with(backup_path)
    
    @pytest.mark.asyncio
    async def test_restore_rules_failure(self, service):
        """Test failed rules restore"""
        backup_path = "/backup/rules.tar.gz"
        
        mock_repo = Mock()
        mock_repo.restore_rules = Mock(return_value=False)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.restore_rules(backup_path)
        
        assert result["success"] is False
        assert result["error"] == "Failed to restore rules"
    
    @pytest.mark.asyncio
    async def test_restore_rules_exception(self, service):
        """Test rules restore with exception"""
        backup_path = "/backup/rules.tar.gz"
        
        mock_repo = Mock()
        mock_repo.restore_rules = Mock(side_effect=Exception("Restore error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.restore_rules(backup_path)
        
        assert result["success"] is False
        assert "Restore error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_rules_success(self, service):
        """Test successful obsolete rules cleanup"""
        cleaned_paths = ["/old/rule1", "/old/rule2"]
        
        mock_repo = Mock()
        mock_repo.cleanup_obsolete_rules = Mock(return_value=cleaned_paths)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.cleanup_obsolete_rules()
        
        assert result["success"] is True
        assert "2" in result["message"]
        assert result["cleaned_paths"] == cleaned_paths
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_rules_exception(self, service):
        """Test obsolete rules cleanup with exception"""
        mock_repo = Mock()
        mock_repo.cleanup_obsolete_rules = Mock(side_effect=Exception("Cleanup error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.cleanup_obsolete_rules()
        
        assert result["success"] is False
        assert "Cleanup error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_rule_statistics_success(self, service):
        """Test get rule statistics success"""
        stats = {
            "total_rules": 100,
            "by_type": {"validation": 50, "transformation": 30, "policy": 20},
            "by_format": {"yaml": 60, "json": 40}
        }
        
        mock_repo = Mock()
        mock_repo.get_rule_statistics = Mock(return_value=stats)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rule_statistics()
        
        assert result["success"] is True
        assert result["statistics"] == stats
    
    @pytest.mark.asyncio
    async def test_get_rule_statistics_exception(self, service):
        """Test get rule statistics with exception"""
        mock_repo = Mock()
        mock_repo.get_rule_statistics = Mock(side_effect=Exception("Stats error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rule_statistics()
        
        assert result["success"] is False
        assert "Stats error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_rule_dependencies_success(self, service):
        """Test get rule dependencies success"""
        rule_path = "/test/rule"
        dependencies = ["/dep/rule1", "/dep/rule2"]
        
        mock_repo = Mock()
        mock_repo.get_rule_dependencies = Mock(return_value=dependencies)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rule_dependencies(rule_path)
        
        assert result["success"] is True
        assert result["rule_path"] == rule_path
        assert result["dependencies"] == dependencies
        mock_repo.get_rule_dependencies.assert_called_once_with(rule_path)
    
    @pytest.mark.asyncio
    async def test_get_rule_dependencies_exception(self, service):
        """Test get rule dependencies with exception"""
        rule_path = "/test/rule"
        
        mock_repo = Mock()
        mock_repo.get_rule_dependencies = Mock(side_effect=Exception("Dependency error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rule_dependencies(rule_path)
        
        assert result["success"] is False
        assert "Dependency error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_dependent_rules_success(self, service):
        """Test get dependent rules success"""
        rule_path = "/test/rule"
        dependent_rules = ["/dependent/rule1", "/dependent/rule2"]
        
        mock_repo = Mock()
        mock_repo.get_dependent_rules = Mock(return_value=dependent_rules)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_dependent_rules(rule_path)
        
        assert result["success"] is True
        assert result["rule_path"] == rule_path
        assert result["dependent_rules"] == dependent_rules
        mock_repo.get_dependent_rules.assert_called_once_with(rule_path)
    
    @pytest.mark.asyncio
    async def test_get_dependent_rules_exception(self, service):
        """Test get dependent rules with exception"""
        rule_path = "/test/rule"
        
        mock_repo = Mock()
        mock_repo.get_dependent_rules = Mock(side_effect=Exception("Dependent error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_dependent_rules(rule_path)
        
        assert result["success"] is False
        assert "Dependent error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_rules_by_type_success(self, service, sample_rule):
        """Test get rules by type success"""
        rule_type = "validation"
        rules = [sample_rule]
        
        mock_repo = Mock()
        mock_repo.get_rules_by_type = Mock(return_value=rules)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rules_by_type(rule_type)
        
        assert result["success"] is True
        assert result["rule_type"] == rule_type
        assert len(result["rules"]) == 1
        assert result["rules"][0]["path"] == sample_rule.metadata.path
        assert result["rules"][0]["type"] == sample_rule.metadata.type.value
        assert result["rules"][0]["format"] == sample_rule.metadata.format.value
        assert result["rules"][0]["description"] == sample_rule.metadata.description
        assert result["rules"][0]["tags"] == sample_rule.metadata.tags
        mock_repo.get_rules_by_type.assert_called_once_with(rule_type)
    
    @pytest.mark.asyncio
    async def test_get_rules_by_type_exception(self, service):
        """Test get rules by type with exception"""
        rule_type = "validation"
        
        mock_repo = Mock()
        mock_repo.get_rules_by_type = Mock(side_effect=Exception("Type error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rules_by_type(rule_type)
        
        assert result["success"] is False
        assert "Type error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_rules_by_tag_success(self, service, sample_rule):
        """Test get rules by tag success"""
        tag = "test"
        rules = [sample_rule]
        
        mock_repo = Mock()
        mock_repo.get_rules_by_tag = Mock(return_value=rules)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rules_by_tag(tag)
        
        assert result["success"] is True
        assert result["tag"] == tag
        assert len(result["rules"]) == 1
        assert result["rules"][0]["path"] == sample_rule.metadata.path
        assert result["rules"][0]["type"] == sample_rule.metadata.type.value
        assert result["rules"][0]["format"] == sample_rule.metadata.format.value
        assert result["rules"][0]["description"] == sample_rule.metadata.description
        assert result["rules"][0]["tags"] == sample_rule.metadata.tags
        mock_repo.get_rules_by_tag.assert_called_once_with(tag)
    
    @pytest.mark.asyncio
    async def test_get_rules_by_tag_exception(self, service):
        """Test get rules by tag with exception"""
        tag = "test"
        
        mock_repo = Mock()
        mock_repo.get_rules_by_tag = Mock(side_effect=Exception("Tag error"))
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rules_by_tag(tag)
        
        assert result["success"] is False
        assert "Tag error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_rules_by_tag_multiple_rules(self, service):
        """Test get rules by tag with multiple rules"""
        tag = "important"
        
        # Create multiple rules
        rule1 = Mock()
        rule1.metadata.path = "/rule1"
        rule1.metadata.type = RuleType.VALIDATION
        rule1.metadata.format = RuleFormat.YAML
        rule1.metadata.description = "Rule 1"
        rule1.metadata.tags = ["important", "test"]
        
        rule2 = Mock()
        rule2.metadata.path = "/rule2"
        rule2.metadata.type = RuleType.POLICY
        rule2.metadata.format = RuleFormat.JSON
        rule2.metadata.description = "Rule 2"
        rule2.metadata.tags = ["important", "production"]
        
        rules = [rule1, rule2]
        
        mock_repo = Mock()
        mock_repo.get_rules_by_tag = Mock(return_value=rules)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.get_rules_by_tag(tag)
        
        assert result["success"] is True
        assert result["tag"] == tag
        assert len(result["rules"]) == 2
        assert result["rules"][0]["path"] == "/rule1"
        assert result["rules"][1]["path"] == "/rule2"
        assert result["rules"][0]["type"] == "VALIDATION"
        assert result["rules"][1]["type"] == "POLICY"