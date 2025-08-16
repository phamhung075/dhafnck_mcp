"""
Tests for RuleApplicationFacade - Comprehensive rule facade testing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from fastmcp.task_management.application.facades.rule_application_facade import RuleApplicationFacade


class TestRuleApplicationFacade:
    """Test cases for RuleApplicationFacade"""
    
    @pytest.fixture
    def mock_path_resolver(self):
        """Mock path resolver"""
        resolver = Mock()
        resolver.project_root = Path("/test/project")
        resolver.get_rules_directory_from_settings.return_value = Path("/test/project/rules")
        return resolver
    
    @pytest.fixture
    def mock_orchestration_facade(self):
        """Mock rule orchestration facade"""
        return Mock()
    
    @pytest.fixture
    def facade(self, mock_path_resolver, mock_orchestration_facade):
        """Create facade instance for testing"""
        return RuleApplicationFacade(
            path_resolver=mock_path_resolver,
            orchestration_facade=mock_orchestration_facade
        )
    
    @pytest.fixture
    def minimal_facade(self):
        """Create facade with minimal configuration"""
        with patch('fastmcp.task_management.application.facades.rule_application_facade.PathResolver') as MockPathResolver:
            mock_resolver = Mock()
            mock_resolver.project_root = Path("/test")
            mock_resolver.get_rules_directory_from_settings.return_value = Path("/test/rules")
            MockPathResolver.return_value = mock_resolver
            return RuleApplicationFacade()
    
    def test_facade_initialization_with_dependencies(self, mock_path_resolver, mock_orchestration_facade):
        """Test facade initialization with provided dependencies"""
        facade = RuleApplicationFacade(
            path_resolver=mock_path_resolver,
            orchestration_facade=mock_orchestration_facade
        )
        
        assert facade._path_resolver == mock_path_resolver
        assert facade._orchestration_facade == mock_orchestration_facade
        assert facade._enhanced_orchestrator is None
    
    def test_facade_initialization_minimal(self):
        """Test facade initialization with minimal parameters"""
        with patch('fastmcp.task_management.application.facades.rule_application_facade.PathResolver') as MockPathResolver:
            mock_resolver = Mock()
            MockPathResolver.return_value = mock_resolver
            
            facade = RuleApplicationFacade()
            
            assert facade._path_resolver == mock_resolver
            assert facade._orchestration_facade is None
            MockPathResolver.assert_called_once()
    
    def test_orchestration_facade_property_with_existing(self, facade, mock_orchestration_facade):
        """Test orchestration_facade property when facade already exists"""
        result = facade.orchestration_facade
        
        assert result == mock_orchestration_facade
    
    @patch('fastmcp.task_management.application.facades.rule_application_facade.RuleOrchestrationFacade')
    @patch('fastmcp.task_management.application.facades.rule_application_facade.RuleOrchestrationUseCase')
    @patch('fastmcp.task_management.application.facades.rule_application_facade.RuleCompositionService')
    @patch('fastmcp.task_management.application.facades.rule_application_facade.RuleParserService')
    def test_orchestration_facade_lazy_loading(self, mock_parser, mock_composition, mock_use_case, mock_facade_class, mock_path_resolver):
        """Test lazy loading of orchestration facade"""
        facade = RuleApplicationFacade(path_resolver=mock_path_resolver)
        
        # Mock the created instances
        mock_use_case_instance = Mock()
        mock_composition_instance = Mock()
        mock_parser_instance = Mock()
        mock_facade_instance = Mock()
        
        mock_use_case.return_value = mock_use_case_instance
        mock_composition.return_value = mock_composition_instance
        mock_parser.return_value = mock_parser_instance
        mock_facade_class.return_value = mock_facade_instance
        
        # Access property to trigger lazy loading
        result = facade.orchestration_facade
        
        # Verify all dependencies were created
        mock_use_case.assert_called_once()
        mock_composition.assert_called_once()
        mock_parser.assert_called_once()
        
        # Verify facade was created with correct parameters
        mock_facade_class.assert_called_once_with(
            rule_orchestration_use_case=mock_use_case_instance,
            rule_composition_service=mock_composition_instance,
            rule_parser_service=mock_parser_instance,
            project_root=Path("/test/project"),
            rules_dir=Path("/test/project/rules")
        )
        
        assert result == mock_facade_instance
        assert facade._orchestration_facade == mock_facade_instance
    
    def test_orchestration_facade_setter(self, facade):
        """Test setting orchestration facade"""
        new_facade = Mock()
        
        facade.orchestration_facade = new_facade
        
        assert facade._orchestration_facade == new_facade
        assert facade.orchestration_facade == new_facade
    
    def test_orchestration_facade_deleter(self, facade):
        """Test deleting orchestration facade to reset lazy loading"""
        original_facade = facade._orchestration_facade
        assert original_facade is not None
        
        del facade.orchestration_facade
        
        assert facade._orchestration_facade is None
    
    @patch('fastmcp.task_management.application.facades.rule_application_facade.RuleOrchestrationController')
    def test_enhanced_orchestrator_lazy_loading(self, mock_controller_class, facade):
        """Test lazy loading of enhanced orchestrator for test compatibility"""
        mock_controller_instance = Mock()
        mock_controller_instance.initialize = Mock()
        mock_controller_class.return_value = mock_controller_instance
        
        result = facade.enhanced_orchestrator
        
        mock_controller_class.assert_called_once_with(facade.orchestration_facade)
        mock_controller_instance.initialize.assert_called_once()
        assert result == mock_controller_instance
        assert facade._enhanced_orchestrator == mock_controller_instance
    
    @patch('fastmcp.task_management.application.facades.rule_application_facade.RuleOrchestrationController')
    def test_enhanced_orchestrator_no_initialize_method(self, mock_controller_class, facade):
        """Test enhanced orchestrator when controller has no initialize method"""
        mock_controller_instance = Mock()
        del mock_controller_instance.initialize  # Remove initialize method
        mock_controller_class.return_value = mock_controller_instance
        
        result = facade.enhanced_orchestrator
        
        # Should not raise exception even without initialize method
        assert result == mock_controller_instance
    
    def test_enhanced_orchestrator_setter_getter(self, facade):
        """Test enhanced orchestrator setter and getter"""
        mock_orchestrator = Mock()
        
        facade.enhanced_orchestrator = mock_orchestrator
        
        assert facade._enhanced_orchestrator == mock_orchestrator
        assert facade.enhanced_orchestrator == mock_orchestrator
    
    def test_enhanced_orchestrator_deleter(self, facade):
        """Test deleting enhanced orchestrator"""
        # First access to create it
        _ = facade.enhanced_orchestrator
        assert facade._enhanced_orchestrator is not None
        
        del facade.enhanced_orchestrator
        
        assert facade._enhanced_orchestrator is None
    
    def test_validate_rules_auto_rule_success(self, facade):
        """Test successful auto rule validation"""
        with patch.object(facade, '_validate_auto_rule') as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "validation_result": "passed",
                "rules_checked": 5
            }
            
            result = facade.validate_rules(target="auto_rule")
            
            assert result["success"] is True
            assert result["validation_result"] == "passed"
            mock_validate.assert_called_once()
    
    def test_validate_rules_all_rules_success(self, facade):
        """Test successful validation of all rules"""
        with patch.object(facade, '_validate_all_rules') as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "total_rules": 10,
                "passed": 8,
                "failed": 2
            }
            
            result = facade.validate_rules(target="all")
            
            assert result["success"] is True
            assert result["total_rules"] == 10
            mock_validate.assert_called_once()
    
    def test_validate_rules_specific_rule_success(self, facade):
        """Test successful validation of specific rule"""
        with patch.object(facade, '_validate_specific_rule') as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "rule": "custom_rule.yaml",
                "status": "valid"
            }
            
            result = facade.validate_rules(target="custom_rule.yaml")
            
            assert result["success"] is True
            assert result["rule"] == "custom_rule.yaml"
            mock_validate.assert_called_once_with("custom_rule.yaml")
    
    def test_validate_rules_exception_handling(self, facade):
        """Test validation with exception handling"""
        with patch.object(facade, '_validate_auto_rule') as mock_validate:
            mock_validate.side_effect = Exception("Validation error")
            
            result = facade.validate_rules(target="auto_rule")
            
            assert result["success"] is False
            assert "Validation failed" in result["error"]
            assert "Validation error" in result["error"]
            assert result["target"] == "auto_rule"
    
    def test_manage_rule_success(self, facade, mock_orchestration_facade):
        """Test successful rule management"""
        mock_orchestration_facade.manage_rule.return_value = {
            "success": True,
            "action": "create",
            "rule_created": True
        }
        
        result = facade.manage_rule(
            action="create",
            target="new_rule.yaml",
            content="rule: content"
        )
        
        assert result["success"] is True
        assert result["action"] == "create"
        
        mock_orchestration_facade.manage_rule.assert_called_once_with(
            action="create",
            target="new_rule.yaml",
            content="rule: content"
        )
    
    def test_manage_rule_default_parameters(self, facade, mock_orchestration_facade):
        """Test manage_rule with default parameters"""
        mock_orchestration_facade.manage_rule.return_value = {"success": True}
        
        facade.manage_rule(action="list")
        
        mock_orchestration_facade.manage_rule.assert_called_once_with(
            action="list",
            target="",
            content=""
        )
    
    def test_manage_rule_exception_handling(self, facade, mock_orchestration_facade):
        """Test manage_rule with exception from orchestration facade"""
        mock_orchestration_facade.manage_rule.side_effect = Exception("Management error")
        
        result = facade.manage_rule(action="delete", target="rule.yaml")
        
        assert result["success"] is False
        assert "Management failed" in result["error"]
        assert "Management error" in result["error"]
        assert result["action"] == "delete"
        assert result["target"] == "rule.yaml"
    
    def test_property_chains_work_correctly(self, facade):
        """Test that property access chains work correctly"""
        # Access orchestration_facade multiple times
        facade1 = facade.orchestration_facade
        facade2 = facade.orchestration_facade
        
        # Should return same instance (cached)
        assert facade1 is facade2
        
        # Access enhanced_orchestrator multiple times
        with patch('fastmcp.task_management.application.facades.rule_application_facade.RuleOrchestrationController') as mock_controller:
            mock_instance = Mock()
            mock_instance.initialize = Mock()
            mock_controller.return_value = mock_instance
            
            orch1 = facade.enhanced_orchestrator
            orch2 = facade.enhanced_orchestrator
            
            # Should return same instance (cached)
            assert orch1 is orch2
            # Controller should only be created once
            mock_controller.assert_called_once()


class TestRuleApplicationFacadePrivateMethods:
    """Test private validation methods"""
    
    @pytest.fixture
    def facade_with_mocked_methods(self):
        """Create facade with mocked private methods"""
        facade = RuleApplicationFacade()
        
        # Mock private methods
        facade._validate_auto_rule = Mock()
        facade._validate_all_rules = Mock()
        facade._validate_specific_rule = Mock()
        
        return facade
    
    def test_validate_auto_rule_called(self, facade_with_mocked_methods):
        """Test that _validate_auto_rule is called correctly"""
        facade_with_mocked_methods._validate_auto_rule.return_value = {"success": True}
        
        facade_with_mocked_methods.validate_rules("auto_rule")
        
        facade_with_mocked_methods._validate_auto_rule.assert_called_once()
    
    def test_validate_all_rules_called(self, facade_with_mocked_methods):
        """Test that _validate_all_rules is called correctly"""
        facade_with_mocked_methods._validate_all_rules.return_value = {"success": True}
        
        facade_with_mocked_methods.validate_rules("all")
        
        facade_with_mocked_methods._validate_all_rules.assert_called_once()
    
    def test_validate_specific_rule_called(self, facade_with_mocked_methods):
        """Test that _validate_specific_rule is called correctly"""
        facade_with_mocked_methods._validate_specific_rule.return_value = {"success": True}
        
        facade_with_mocked_methods.validate_rules("custom_rule")
        
        facade_with_mocked_methods._validate_specific_rule.assert_called_once_with("custom_rule")


class TestRuleApplicationFacadeIntegration:
    """Integration-style tests for RuleApplicationFacade"""
    
    def test_complete_rule_management_workflow(self):
        """Test complete workflow from validation to management"""
        with patch('fastmcp.task_management.application.facades.rule_application_facade.PathResolver') as MockPathResolver:
            # Setup path resolver
            mock_resolver = Mock()
            mock_resolver.project_root = Path("/test/project")
            mock_resolver.get_rules_directory_from_settings.return_value = Path("/test/rules")
            MockPathResolver.return_value = mock_resolver
            
            # Create facade
            facade = RuleApplicationFacade()
            
            # Mock validation and management
            with patch.object(facade, '_validate_auto_rule') as mock_validate:
                mock_validate.return_value = {"success": True, "valid": True}
                
                validation_result = facade.validate_rules("auto_rule")
                assert validation_result["success"] is True
                
                # Test management through orchestration facade
                with patch.object(facade.orchestration_facade, 'manage_rule') as mock_manage:
                    mock_manage.return_value = {"success": True, "created": True}
                    
                    management_result = facade.manage_rule("create", "test_rule", "content")
                    assert management_result["success"] is True
    
    def test_error_recovery_and_logging(self):
        """Test error recovery and proper error handling"""
        facade = RuleApplicationFacade()
        
        # Test that facade continues to work after exceptions
        with patch.object(facade, '_validate_auto_rule', side_effect=Exception("First error")):
            result1 = facade.validate_rules("auto_rule")
            assert result1["success"] is False
        
        # Should still work for next call
        with patch.object(facade, '_validate_auto_rule', return_value={"success": True}):
            result2 = facade.validate_rules("auto_rule")
            assert result2["success"] is True
    
    def test_lazy_loading_cache_behavior(self):
        """Test that lazy loading properly caches instances"""
        facade = RuleApplicationFacade()
        
        with patch('fastmcp.task_management.application.facades.rule_application_facade.RuleOrchestrationFacade') as MockOrchestration:
            mock_instance = Mock()
            MockOrchestration.return_value = mock_instance
            
            # First access
            orch1 = facade.orchestration_facade
            # Second access
            orch2 = facade.orchestration_facade
            
            # Should be same instance
            assert orch1 is orch2
            # Constructor called only once
            MockOrchestration.assert_called_once()
            
            # Reset and verify lazy loading works again
            del facade.orchestration_facade
            orch3 = facade.orchestration_facade
            
            # Should create new instance
            assert MockOrchestration.call_count == 2