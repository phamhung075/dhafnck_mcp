"""Test suite for ContextInheritanceService.

Tests for context inheritance logic across the hierarchy: Global → Project → Branch → Task.
"""

import pytest
from unittest.mock import Mock, patch
from copy import deepcopy
from typing import Dict, Any

from fastmcp.task_management.application.services.context_inheritance_service import ContextInheritanceService


class TestContextInheritanceServiceInit:
    """Test ContextInheritanceService initialization."""

    def test_initialization_with_defaults(self):
        """Test service initialization with default values."""
        service = ContextInheritanceService()
        
        assert service.repository is None
        assert service._user_id is None

    def test_initialization_with_parameters(self):
        """Test service initialization with custom parameters."""
        mock_repo = Mock()
        service = ContextInheritanceService(repository=mock_repo, user_id="test_user_123")
        
        assert service.repository == mock_repo
        assert service._user_id == "test_user_123"

    def test_with_user_method(self):
        """Test with_user method creates new instance with user context."""
        original_service = ContextInheritanceService()
        user_id = "test_user_456"
        
        user_scoped_service = original_service.with_user(user_id)
        
        assert user_scoped_service._user_id == user_id
        assert user_scoped_service is not original_service
        assert isinstance(user_scoped_service, ContextInheritanceService)

    def test_get_user_scoped_repository_with_with_user_method(self):
        """Test _get_user_scoped_repository with repository that has with_user method."""
        service = ContextInheritanceService(user_id="test_user")
        mock_repo = Mock()
        mock_user_scoped_repo = Mock()
        mock_repo.with_user.return_value = mock_user_scoped_repo
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_user_scoped_repo
        mock_repo.with_user.assert_called_once_with("test_user")

    def test_get_user_scoped_repository_with_user_id_property(self):
        """Test _get_user_scoped_repository with repository that has user_id property."""
        service = ContextInheritanceService(user_id="test_user")
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
        service = ContextInheritanceService()  # No user_id
        mock_repo = Mock()
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_repo

    def test_get_inherited_context_simple(self):
        """Test get_inherited_context returns None (simplified implementation)."""
        service = ContextInheritanceService()
        
        result = service.get_inherited_context("task", "task_123")
        
        assert result is None


class TestProjectInheritanceFromGlobal:
    """Test project inheritance from global context."""

    def test_inherit_project_from_global_basic(self):
        """Test basic project inheritance from global context."""
        service = ContextInheritanceService()
        
        global_context = {
            "security_policies": {"mfa_required": True},
            "coding_standards": {"python_version": "3.11"},
            "metadata": {"version": 1}
        }
        
        project_context = {
            "team_preferences": {"code_review": "required"},
            "technology_stack": {"framework": "FastAPI"}
        }
        
        result = service.inherit_project_from_global(global_context, project_context)
        
        # Should inherit from global
        assert result["security_policies"]["mfa_required"] is True
        assert result["coding_standards"]["python_version"] == "3.11"
        
        # Should include project-specific data
        assert result["team_preferences"]["code_review"] == "required"
        assert result["technology_stack"]["framework"] == "FastAPI"
        
        # Should have inheritance metadata
        assert "inheritance_metadata" in result
        assert result["inheritance_metadata"]["inherited_from"] == "global"

    def test_inherit_project_from_global_with_overrides(self):
        """Test project inheritance with global overrides."""
        service = ContextInheritanceService()
        
        global_context = {
            "security_policies": {"mfa_required": False, "password_min_length": 8},
            "deployment": {"environment": "staging"}
        }
        
        project_context = {
            "team_preferences": {"daily_standups": True},
            "global_overrides": {
                "security_policies.mfa_required": True,
                "deployment.environment": "production"
            }
        }
        
        result = service.inherit_project_from_global(global_context, project_context)
        
        # Overrides should be applied
        assert result["security_policies"]["mfa_required"] is True  # Overridden
        assert result["security_policies"]["password_min_length"] == 8  # Inherited unchanged
        assert result["deployment"]["environment"] == "production"  # Overridden
        
        # Project data should be preserved
        assert result["team_preferences"]["daily_standups"] is True
        
        # Metadata should reflect overrides
        assert result["inheritance_metadata"]["project_overrides_applied"] == 2

    def test_inherit_project_from_global_with_delegation_rules(self):
        """Test project inheritance with delegation rule merging."""
        service = ContextInheritanceService()
        
        global_context = {
            "delegation_rules": {
                "auto_delegate": {"security": True},
                "thresholds": {"critical_issues": 1}
            }
        }
        
        project_context = {
            "team_preferences": {"workflow": "agile"},
            "delegation_rules": {
                "auto_delegate": {"performance": True},
                "thresholds": {"critical_issues": 3},  # Override global threshold
                "project_specific": {"code_review_required": True}
            }
        }
        
        result = service.inherit_project_from_global(global_context, project_context)
        
        # Delegation rules should be merged
        delegation_rules = result["delegation_rules"]
        assert delegation_rules["auto_delegate"]["security"] is True  # From global
        assert delegation_rules["auto_delegate"]["performance"] is True  # From project
        assert delegation_rules["thresholds"]["critical_issues"] == 3  # Project override
        assert delegation_rules["project_specific"]["code_review_required"] is True  # Project only

    def test_inherit_project_from_global_inheritance_disabled(self):
        """Test project inheritance with inheritance disabled flag."""
        service = ContextInheritanceService()
        
        global_context = {"security_policies": {"strict": True}}
        project_context = {
            "team_preferences": {"flexible": True},
            "inheritance_disabled": True
        }
        
        result = service.inherit_project_from_global(global_context, project_context)
        
        # Should still inherit (flag is just recorded in metadata)
        assert result["security_policies"]["strict"] is True
        assert result["inheritance_metadata"]["inheritance_disabled"] is True

    def test_inherit_project_from_global_arbitrary_fields(self):
        """Test project inheritance preserves arbitrary fields from project context."""
        service = ContextInheritanceService()
        
        global_context = {"global_setting": "value"}
        project_context = {
            "team_preferences": {"standard": "field"},
            "custom_field": "should_be_preserved",
            "another_custom": {"nested": "data"}
        }
        
        result = service.inherit_project_from_global(global_context, project_context)
        
        # Should preserve custom fields
        assert result["custom_field"] == "should_be_preserved"
        assert result["another_custom"]["nested"] == "data"
        # Should also have standard fields
        assert result["team_preferences"]["standard"] == "field"

    def test_inherit_project_from_global_exception_handling(self):
        """Test project inheritance exception handling."""
        service = ContextInheritanceService()
        
        # Create context that might cause exception (circular reference)
        global_context = {"base": "value"}
        project_context = {"team_preferences": {"ref": None}}
        project_context["team_preferences"]["ref"] = project_context  # Circular reference
        
        with pytest.raises(Exception):
            service.inherit_project_from_global(global_context, project_context)


class TestBranchInheritanceFromProject:
    """Test branch inheritance from project context."""

    def test_inherit_branch_from_project_basic(self):
        """Test basic branch inheritance from project context."""
        service = ContextInheritanceService()
        
        project_context = {
            "security_policies": {"mfa_required": True},
            "team_preferences": {"code_review": "required"},
            "metadata": {"version": 1}
        }
        
        branch_context = {
            "branch_workflow": {"ci_required": True},
            "branch_standards": {"commit_format": "conventional"},
            "agent_assignments": {"coding": "agent_1"}
        }
        
        result = service.inherit_branch_from_project(project_context, branch_context)
        
        # Should inherit from project
        assert result["security_policies"]["mfa_required"] is True
        assert result["team_preferences"]["code_review"] == "required"
        
        # Should include branch-specific data
        assert result["branch_workflow"]["ci_required"] is True
        assert result["branch_standards"]["commit_format"] == "conventional"
        assert result["agent_assignments"]["coding"] == "agent_1"
        
        # Should have inheritance metadata
        assert "inheritance_metadata" in result
        assert result["inheritance_metadata"]["inherited_from"] == "project"
        assert result["inheritance_metadata"]["inheritance_chain"] == ["global", "project", "branch"]

    def test_inherit_branch_from_project_with_overrides(self):
        """Test branch inheritance with local overrides."""
        service = ContextInheritanceService()
        
        project_context = {
            "security_policies": {"session_timeout": 30},
            "team_preferences": {"standup_time": "9:00"}
        }
        
        branch_context = {
            "branch_workflow": {"feature_branch": True},
            "local_overrides": {
                "security_policies.session_timeout": 60,  # Longer session for dev
                "team_preferences.standup_time": "10:00"  # Later standup
            }
        }
        
        result = service.inherit_branch_from_project(project_context, branch_context)
        
        # Overrides should be applied
        assert result["security_policies"]["session_timeout"] == 60  # Overridden
        assert result["team_preferences"]["standup_time"] == "10:00"  # Overridden
        
        # Branch data should be preserved
        assert result["branch_workflow"]["feature_branch"] is True
        
        # Metadata should reflect overrides
        assert result["inheritance_metadata"]["branch_overrides_applied"] == 2

    def test_inherit_branch_from_project_with_delegation_rules(self):
        """Test branch inheritance with delegation rule merging."""
        service = ContextInheritanceService()
        
        project_context = {
            "delegation_rules": {
                "auto_delegate": {"security": True},
                "project_level": {"reviews": "required"}
            }
        }
        
        branch_context = {
            "branch_workflow": {"merge_strategy": "squash"},
            "delegation_rules": {
                "auto_delegate": {"testing": True},
                "branch_level": {"auto_deploy": False}
            }
        }
        
        result = service.inherit_branch_from_project(project_context, branch_context)
        
        # Delegation rules should be merged
        delegation_rules = result["delegation_rules"]
        assert delegation_rules["auto_delegate"]["security"] is True  # From project
        assert delegation_rules["auto_delegate"]["testing"] is True  # From branch
        assert delegation_rules["project_level"]["reviews"] == "required"  # From project
        assert delegation_rules["branch_level"]["auto_deploy"] is False  # From branch

    def test_inherit_branch_from_project_arbitrary_fields(self):
        """Test branch inheritance preserves arbitrary fields."""
        service = ContextInheritanceService()
        
        project_context = {"project_setting": "value"}
        branch_context = {
            "branch_workflow": {"standard": "field"},
            "custom_branch_field": "should_be_preserved",
            "nested_custom": {"branch": "data"}
        }
        
        result = service.inherit_branch_from_project(project_context, branch_context)
        
        # Should preserve custom fields
        assert result["custom_branch_field"] == "should_be_preserved"
        assert result["nested_custom"]["branch"] == "data"
        # Should also have standard fields
        assert result["branch_workflow"]["standard"] == "field"


class TestTaskInheritanceFromBranch:
    """Test task inheritance from branch context."""

    def test_inherit_task_from_branch_basic(self):
        """Test basic task inheritance from branch context."""
        service = ContextInheritanceService()
        
        branch_context = {
            "security_policies": {"encryption": "AES256"},
            "branch_workflow": {"ci_required": True},
            "metadata": {"version": 1}
        }
        
        task_context = {
            "task_data": {
                "title": "Implement authentication",
                "status": "in_progress"
            }
        }
        
        result = service.inherit_task_from_branch(branch_context, task_context)
        
        # Should inherit from branch
        assert result["security_policies"]["encryption"] == "AES256"
        assert result["branch_workflow"]["ci_required"] is True
        
        # Should include task-specific data
        assert result["task_data"]["title"] == "Implement authentication"
        assert result["task_data"]["status"] == "in_progress"
        
        # Should have inheritance metadata
        assert "inheritance_metadata" in result
        assert result["inheritance_metadata"]["inherited_from"] == "branch"
        assert result["inheritance_metadata"]["inheritance_chain"] == ["global", "project", "branch", "task"]

    def test_inherit_task_from_branch_with_overrides(self):
        """Test task inheritance with local overrides."""
        service = ContextInheritanceService()
        
        branch_context = {
            "security_policies": {"audit_logging": True},
            "branch_workflow": {"review_required": True}
        }
        
        task_context = {
            "task_data": {"priority": "high"},
            "local_overrides": {
                "security_policies.audit_logging": False,  # Disable for this task
                "branch_workflow.review_required": False   # Skip review for hotfix
            }
        }
        
        result = service.inherit_task_from_branch(branch_context, task_context)
        
        # Overrides should be applied
        assert result["security_policies"]["audit_logging"] is False  # Overridden
        assert result["branch_workflow"]["review_required"] is False  # Overridden
        
        # Task data should be preserved
        assert result["task_data"]["priority"] == "high"
        
        # Metadata should reflect overrides
        assert result["inheritance_metadata"]["local_overrides_applied"] == 2

    def test_inherit_task_from_branch_with_implementation_notes(self):
        """Test task inheritance with implementation notes."""
        service = ContextInheritanceService()
        
        branch_context = {"branch_setting": "value"}
        task_context = {
            "task_data": {"status": "done"},
            "implementation_notes": {
                "approach": "Used JWT tokens",
                "challenges": "Rate limiting complexity",
                "lessons": "Consider Redis for session storage"
            }
        }
        
        result = service.inherit_task_from_branch(branch_context, task_context)
        
        # Implementation notes should be preserved
        notes = result["implementation_notes"]
        assert notes["approach"] == "Used JWT tokens"
        assert notes["challenges"] == "Rate limiting complexity"
        assert notes["lessons"] == "Consider Redis for session storage"

    def test_inherit_task_from_branch_with_custom_rules(self):
        """Test task inheritance with custom inheritance rules."""
        service = ContextInheritanceService()
        
        branch_context = {
            "security_policies": {"strict_mode": True},
            "performance": {"cache_enabled": True}
        }
        
        task_context = {
            "task_data": {"type": "experimental"},
            "custom_inheritance_rules": {
                "exclude_keys": ["security_policies.strict_mode"],
                "force_values": {"performance.cache_enabled": False}
            }
        }
        
        result = service.inherit_task_from_branch(branch_context, task_context)
        
        # Custom rules should be applied
        assert "strict_mode" not in result["security_policies"]  # Excluded
        assert result["performance"]["cache_enabled"] is False  # Forced value
        
        # Metadata should reflect custom rules
        assert result["inheritance_metadata"]["custom_rules_applied"] == 2

    def test_inherit_task_from_branch_with_delegation_triggers(self):
        """Test task inheritance with delegation triggers."""
        service = ContextInheritanceService()
        
        branch_context = {"branch_setting": "value"}
        task_context = {
            "task_data": {"complexity": "high"},
            "delegation_triggers": {
                "patterns": {"security_discovery": "global"},
                "thresholds": {"error_count": {"value": 5, "delegate_to": "project"}}
            }
        }
        
        result = service.inherit_task_from_branch(branch_context, task_context)
        
        # Delegation triggers should be preserved
        triggers = result["delegation_triggers"]
        assert triggers["patterns"]["security_discovery"] == "global"
        assert triggers["thresholds"]["error_count"]["value"] == 5

    def test_inherit_task_from_branch_force_local_only(self):
        """Test task inheritance with force_local_only flag."""
        service = ContextInheritanceService()
        
        branch_context = {"inherited_setting": "should_be_inherited"}
        task_context = {
            "task_data": {"local_only": True},
            "force_local_only": True
        }
        
        result = service.inherit_task_from_branch(branch_context, task_context)
        
        # Should still inherit (flag is just recorded in metadata)
        assert result["inherited_setting"] == "should_be_inherited"
        assert result["inheritance_metadata"]["force_local_only"] is True


class TestDeepMergeUtility:
    """Test deep merge utility functionality."""

    def test_deep_merge_basic_dictionaries(self):
        """Test basic dictionary deep merge."""
        service = ContextInheritanceService()
        
        base = {
            "a": {"x": 1, "y": 2},
            "b": "base_value"
        }
        override = {
            "a": {"y": 3, "z": 4},
            "c": "new_value"
        }
        
        result = service._deep_merge(base, override)
        
        assert result["a"]["x"] == 1  # From base
        assert result["a"]["y"] == 3  # Override
        assert result["a"]["z"] == 4  # New from override
        assert result["b"] == "base_value"  # From base
        assert result["c"] == "new_value"  # New from override

    def test_deep_merge_list_handling(self):
        """Test deep merge with list handling."""
        service = ContextInheritanceService()
        
        base = {
            "assignees": ["user1", "user2"],
            "labels": ["bug", "urgent"],
            "requirements": ["req1", "req2"]
        }
        override = {
            "assignees": ["user2", "user3"],  # Should deduplicate
            "labels": ["critical"],
            "requirements": ["req3", "req4"]  # Should append
        }
        
        result = service._deep_merge(base, override)
        
        # Assignees should be deduplicated while preserving order
        assert result["assignees"] == ["user1", "user2", "user3"]
        
        # Labels should be deduplicated
        assert result["labels"] == ["bug", "urgent", "critical"]
        
        # Requirements should be appended
        assert result["requirements"] == ["req1", "req2", "req3", "req4"]

    def test_deep_merge_list_override_strategy(self):
        """Test deep merge with list override strategy."""
        service = ContextInheritanceService()
        
        base = {"other_list": ["a", "b"]}
        override = {"other_list": ["c", "d"]}  # Unknown key, should override completely
        
        result = service._deep_merge(base, override)
        
        assert result["other_list"] == ["c", "d"]  # Complete override

    def test_deep_merge_non_dict_override(self):
        """Test deep merge with non-dictionary override."""
        service = ContextInheritanceService()
        
        base = {"setting": {"nested": "value"}}
        override = {"setting": "simple_string"}  # Override complex with simple
        
        result = service._deep_merge(base, override)
        
        assert result["setting"] == "simple_string"

    def test_deep_merge_preserves_original(self):
        """Test that deep merge doesn't modify original dictionaries."""
        service = ContextInheritanceService()
        
        base = {"mutable": {"list": [1, 2]}}
        override = {"mutable": {"list": [3, 4]}}
        
        original_base = deepcopy(base)
        original_override = deepcopy(override)
        
        result = service._deep_merge(base, override)
        
        # Original dictionaries should be unchanged
        assert base == original_base
        assert override == original_override
        
        # Result should be different
        assert result != base


class TestApplyOverrides:
    """Test override application functionality."""

    def test_apply_overrides_simple_keys(self):
        """Test applying overrides to simple keys."""
        service = ContextInheritanceService()
        
        context = {
            "security": {"mfa": False, "timeout": 30},
            "ui": {"theme": "light"}
        }
        overrides = {
            "security.mfa": True,
            "ui.theme": "dark"
        }
        
        result = service._apply_overrides(context, overrides)
        
        assert result["security"]["mfa"] is True
        assert result["security"]["timeout"] == 30  # Unchanged
        assert result["ui"]["theme"] == "dark"

    def test_apply_overrides_nested_creation(self):
        """Test applying overrides that create new nested structures."""
        service = ContextInheritanceService()
        
        context = {"existing": "value"}
        overrides = {
            "new.nested.deep.setting": "created",
            "existing": "modified"
        }
        
        result = service._apply_overrides(context, overrides)
        
        assert result["new"]["nested"]["deep"]["setting"] == "created"
        assert result["existing"] == "modified"

    def test_apply_overrides_complex_values(self):
        """Test applying overrides with complex values."""
        service = ContextInheritanceService()
        
        context = {"config": {"simple": "value"}}
        overrides = {
            "config.complex": {"list": [1, 2, 3], "dict": {"nested": True}},
            "config.simple": "overridden"
        }
        
        result = service._apply_overrides(context, overrides)
        
        assert result["config"]["simple"] == "overridden"
        assert result["config"]["complex"]["list"] == [1, 2, 3]
        assert result["config"]["complex"]["dict"]["nested"] is True

    def test_apply_overrides_preserves_original(self):
        """Test that applying overrides preserves original context."""
        service = ContextInheritanceService()
        
        context = {"data": {"value": 1}}
        overrides = {"data.value": 2}
        
        original_context = deepcopy(context)
        
        result = service._apply_overrides(context, overrides)
        
        # Original should be unchanged
        assert context == original_context
        # Result should be different
        assert result["data"]["value"] == 2


class TestMergeDelegationRules:
    """Test delegation rule merging functionality."""

    def test_merge_delegation_rules_auto_delegate(self):
        """Test merging auto_delegate rules."""
        service = ContextInheritanceService()
        
        base_rules = {
            "auto_delegate": {"security": True, "performance": False}
        }
        project_rules = {
            "auto_delegate": {"performance": True, "testing": True}
        }
        
        result = service._merge_delegation_rules(base_rules, project_rules)
        
        auto_delegate = result["auto_delegate"]
        assert auto_delegate["security"] is True  # From base
        assert auto_delegate["performance"] is True  # Override from project
        assert auto_delegate["testing"] is True  # New from project

    def test_merge_delegation_rules_thresholds(self):
        """Test merging threshold rules."""
        service = ContextInheritanceService()
        
        base_rules = {
            "thresholds": {"error_count": 5, "warning_count": 10}
        }
        project_rules = {
            "thresholds": {"error_count": 3, "critical_count": 1}
        }
        
        result = service._merge_delegation_rules(base_rules, project_rules)
        
        thresholds = result["thresholds"]
        assert thresholds["error_count"] == 3  # Override from project
        assert thresholds["warning_count"] == 10  # From base
        assert thresholds["critical_count"] == 1  # New from project

    def test_merge_delegation_rules_custom_fields(self):
        """Test merging custom delegation rule fields."""
        service = ContextInheritanceService()
        
        base_rules = {
            "auto_delegate": {"base": True},
            "custom_base": {"setting": "value"}
        }
        project_rules = {
            "project_specific": {"rule": "project_rule"},
            "another_custom": {"data": 123}
        }
        
        result = service._merge_delegation_rules(base_rules, project_rules)
        
        # Should preserve all custom fields
        assert result["custom_base"]["setting"] == "value"
        assert result["project_specific"]["rule"] == "project_rule"
        assert result["another_custom"]["data"] == 123
        # Should also preserve standard fields
        assert result["auto_delegate"]["base"] is True

    def test_merge_delegation_rules_empty_inputs(self):
        """Test merging delegation rules with empty inputs."""
        service = ContextInheritanceService()
        
        # Empty base
        result = service._merge_delegation_rules({}, {"auto_delegate": {"test": True}})
        assert result["auto_delegate"]["test"] is True
        
        # Empty project
        result = service._merge_delegation_rules({"thresholds": {"count": 5}}, {})
        assert result["thresholds"]["count"] == 5


class TestCustomInheritanceRules:
    """Test custom inheritance rules functionality."""

    def test_apply_custom_inheritance_rules_exclude_keys(self):
        """Test custom inheritance rules with key exclusion."""
        service = ContextInheritanceService()
        
        context = {
            "security": {"strict": True, "audit": True},
            "performance": {"cache": True}
        }
        custom_rules = {
            "exclude_keys": ["security.strict", "performance"]
        }
        
        result = service._apply_custom_inheritance_rules(context, custom_rules)
        
        assert "strict" not in result["security"]
        assert result["security"]["audit"] is True  # Should remain
        assert "performance" not in result  # Entire key excluded

    def test_apply_custom_inheritance_rules_force_values(self):
        """Test custom inheritance rules with forced values."""
        service = ContextInheritanceService()
        
        context = {
            "config": {"debug": False, "log_level": "INFO"}
        }
        custom_rules = {
            "force_values": {
                "config.debug": True,
                "config.log_level": "DEBUG",
                "new.forced.setting": "created"
            }
        }
        
        result = service._apply_custom_inheritance_rules(context, custom_rules)
        
        assert result["config"]["debug"] is True  # Forced
        assert result["config"]["log_level"] == "DEBUG"  # Forced
        assert result["new"]["forced"]["setting"] == "created"  # Created

    def test_apply_custom_inheritance_rules_conditional_overrides(self):
        """Test custom inheritance rules with conditional overrides."""
        service = ContextInheritanceService()
        
        context = {
            "environment": "development",
            "security": {"strict": True}
        }
        custom_rules = {
            "conditional_overrides": [
                {
                    "name": "dev_relaxed_security",
                    "condition": {"type": "key_equals", "key": "environment", "value": "development"},
                    "overrides": {"security.strict": False}
                }
            ]
        }
        
        result = service._apply_custom_inheritance_rules(context, custom_rules)
        
        assert result["security"]["strict"] is False  # Conditional override applied

    def test_apply_custom_inheritance_rules_conditional_not_met(self):
        """Test conditional overrides when condition is not met."""
        service = ContextInheritanceService()
        
        context = {
            "environment": "production",
            "security": {"strict": True}
        }
        custom_rules = {
            "conditional_overrides": [
                {
                    "condition": {"type": "key_equals", "key": "environment", "value": "development"},
                    "overrides": {"security.strict": False}
                }
            ]
        }
        
        result = service._apply_custom_inheritance_rules(context, custom_rules)
        
        assert result["security"]["strict"] is True  # No change, condition not met

    def test_apply_custom_inheritance_rules_unknown_rule_type(self):
        """Test custom inheritance rules with unknown rule type."""
        service = ContextInheritanceService()
        
        context = {"data": "value"}
        custom_rules = {
            "unknown_rule_type": {"setting": "ignored"}
        }
        
        result = service._apply_custom_inheritance_rules(context, custom_rules)
        
        # Should return context unchanged
        assert result == context


class TestConditionEvaluation:
    """Test condition evaluation functionality."""

    def test_evaluate_condition_key_exists(self):
        """Test condition evaluation for key existence."""
        service = ContextInheritanceService()
        
        context = {"config": {"debug": True}}
        
        # Key exists
        condition = {"type": "key_exists", "key": "config.debug"}
        assert service._evaluate_condition(context, condition) is True
        
        # Key doesn't exist
        condition = {"type": "key_exists", "key": "config.missing"}
        assert service._evaluate_condition(context, condition) is False

    def test_evaluate_condition_key_equals(self):
        """Test condition evaluation for key equality."""
        service = ContextInheritanceService()
        
        context = {"environment": "production", "debug": False}
        
        # Equal
        condition = {"type": "key_equals", "key": "environment", "value": "production"}
        assert service._evaluate_condition(context, condition) is True
        
        # Not equal
        condition = {"type": "key_equals", "key": "debug", "value": True}
        assert service._evaluate_condition(context, condition) is False

    def test_evaluate_condition_key_contains(self):
        """Test condition evaluation for key contains."""
        service = ContextInheritanceService()
        
        context = {"description": "This is a security-related task"}
        
        # Contains
        condition = {"type": "key_contains", "key": "description", "value": "security"}
        assert service._evaluate_condition(context, condition) is True
        
        # Doesn't contain
        condition = {"type": "key_contains", "key": "description", "value": "performance"}
        assert service._evaluate_condition(context, condition) is False

    def test_evaluate_condition_unknown_type(self):
        """Test condition evaluation with unknown condition type."""
        service = ContextInheritanceService()
        
        context = {"data": "value"}
        condition = {"type": "unknown_type"}
        
        assert service._evaluate_condition(context, condition) is False

    def test_evaluate_condition_missing_key(self):
        """Test condition evaluation with missing key."""
        service = ContextInheritanceService()
        
        context = {"data": "value"}
        condition = {"type": "key_equals", "key": "missing.key", "value": "test"}
        
        assert service._evaluate_condition(context, condition) is False


class TestInheritanceValidation:
    """Test inheritance validation functionality."""

    def test_validate_inheritance_chain_task_valid(self):
        """Test validation of valid task inheritance chain."""
        service = ContextInheritanceService()
        
        resolved_context = {
            "data": "test",
            "inheritance_metadata": {
                "inheritance_chain": ["global", "project", "branch", "task"]
            }
        }
        
        result = service.validate_inheritance_chain("task", "task_123", resolved_context)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["warnings"]) == 0

    def test_validate_inheritance_chain_branch_valid(self):
        """Test validation of valid branch inheritance chain."""
        service = ContextInheritanceService()
        
        resolved_context = {
            "data": "test",
            "inheritance_metadata": {
                "inheritance_chain": ["global", "project", "branch"]
            }
        }
        
        result = service.validate_inheritance_chain("branch", "branch_123", resolved_context)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_inheritance_chain_missing_metadata(self):
        """Test validation with missing inheritance metadata."""
        service = ContextInheritanceService()
        
        resolved_context = {"data": "test"}  # No inheritance_metadata
        
        result = service.validate_inheritance_chain("task", "task_123", resolved_context)
        
        assert result["valid"] is False
        assert "Missing inheritance metadata" in result["issues"]

    def test_validate_inheritance_chain_incorrect_chain(self):
        """Test validation with incorrect inheritance chain."""
        service = ContextInheritanceService()
        
        resolved_context = {
            "inheritance_metadata": {
                "inheritance_chain": ["global", "task"]  # Missing project, branch
            }
        }
        
        result = service.validate_inheritance_chain("task", "task_123", resolved_context)
        
        assert len(result["warnings"]) > 0
        warning = result["warnings"][0]
        assert "Unexpected inheritance chain" in warning

    def test_validate_inheritance_chain_override_validation(self):
        """Test validation of override application."""
        service = ContextInheritanceService()
        
        resolved_context = {
            "config": {"setting": "value"},
            "inheritance_metadata": {"inheritance_chain": ["global", "project"]},
            "local_overrides": {
                "config.setting": "overridden",
                "missing.path": "should_fail"
            }
        }
        
        result = service.validate_inheritance_chain("project", "proj_123", resolved_context)
        
        assert result["valid"] is False
        assert any("Override path not found" in issue for issue in result["issues"])

    def test_validate_inheritance_chain_exception_handling(self):
        """Test validation exception handling."""
        service = ContextInheritanceService()
        
        # Create context that might cause exception during validation
        resolved_context = {"inheritance_metadata": None}  # Invalid metadata
        
        result = service.validate_inheritance_chain("task", "task_123", resolved_context)
        
        assert result["valid"] is False
        assert any("Validation error" in issue for issue in result["issues"])


class TestUtilityMethods:
    """Test utility methods."""

    def test_key_exists(self):
        """Test nested key existence checking."""
        service = ContextInheritanceService()
        
        context = {
            "level1": {
                "level2": {
                    "value": "exists"
                }
            }
        }
        
        assert service._key_exists(context, "level1.level2.value") is True
        assert service._key_exists(context, "level1.level2.missing") is False
        assert service._key_exists(context, "missing.path") is False

    def test_get_nested_value(self):
        """Test nested value retrieval."""
        service = ContextInheritanceService()
        
        context = {
            "config": {
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            }
        }
        
        assert service._get_nested_value(context, "config.database.host") == "localhost"
        assert service._get_nested_value(context, "config.database.port") == 5432
        
        # Should raise exception for missing keys
        with pytest.raises(KeyError):
            service._get_nested_value(context, "config.database.missing")

    def test_get_timestamp(self):
        """Test timestamp generation."""
        service = ContextInheritanceService()
        
        timestamp = service._get_timestamp()
        
        assert isinstance(timestamp, str)
        assert timestamp.endswith('Z')  # Should be in Z format
        
        # Should be valid ISO format
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None