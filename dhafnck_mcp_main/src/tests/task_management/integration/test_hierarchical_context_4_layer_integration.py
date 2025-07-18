"""
Integration Tests for 4-Layer Hierarchical Context System

Tests the complete 4-layer hierarchy system integration:
Global -> Project -> Branch -> Task
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
from fastmcp.task_management.application.services.context_inheritance_service import ContextInheritanceService
from fastmcp.task_management.application.services.context_delegation_service import ContextDelegationService
from fastmcp.task_management.application.services.context_cache_service import ContextCacheService
from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade


class TestHierarchicalContext4LayerIntegration:
    """Integration tests for 4-layer hierarchical context system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create service instances with mock repositories to avoid cache errors
        self.hierarchy_service = HierarchicalContextService()
        self.inheritance_service = ContextInheritanceService()
        self.delegation_service = ContextDelegationService()
        
        # Create cache service with mock repository
        mock_cache_repo = Mock()
        # Create an async mock that returns a coroutine
        async def mock_invalidate(*args, **kwargs):
            return None
        mock_cache_repo.invalidate_cache_entry = Mock(side_effect=mock_invalidate)
        self.cache_service = ContextCacheService(repository=mock_cache_repo)
        # Mock get_cache_health method
        self.cache_service.get_cache_health = Mock(return_value={
            "cache_entries": {
                "global": 0,
                "project": 0,
                "branch": 0,
                "task": 0
            },
            "cache_hit_rate": 0.0,
            "cache_miss_rate": 0.0,
            "average_resolution_time_ms": 0.0,
            "expired_entries": 0
        })
        
        # Create facade
        self.facade = HierarchicalContextFacade(
            hierarchy_service=self.hierarchy_service,
            inheritance_service=self.inheritance_service,
            delegation_service=self.delegation_service,
            cache_service=self.cache_service
        )
        
        # Test data
        self.project_id = "test-project-123"
        self.branch_id = "test-branch-456"
        self.task_id = "test-task-789"
        
        # Sample context data
        self.global_data = {
            "coding_standards": {
                "max_line_length": 88,
                "test_coverage": 80
            },
            "security_policies": {
                "require_mfa": True,
                "audit_logging": True
            }
        }
        
        self.project_data = {
            "team_preferences": {
                "code_review": "required",
                "testing_framework": "pytest"
            },
            "technology_stack": {
                "language": "python",
                "framework": "fastapi"
            }
        }
        
        self.branch_data = {
            "branch_workflow": {
                "feature_flags": True,
                "ci_cd": True
            },
            "agent_assignments": {
                "primary": "@coding_agent",
                "reviewer": "@code_reviewer_agent"
            }
        }
        
        self.task_data = {
            "task_info": {
                "implementation_approach": "TDD",
                "priority": "high"
            },
            "implementation_notes": {
                "special_requirements": "Performance critical"
            }
        }

    @patch('fastmcp.task_management.infrastructure.database.database_config.get_session')
    @patch('fastmcp.task_management.application.services.hierarchical_context_service.HierarchicalContextService.create_context')
    def test_create_contexts_at_all_levels(self, mock_create, mock_get_session):
        """Test creating contexts at all hierarchy levels"""
        mock_create.return_value = {"success": True}
        
        # Mock the database session and task lookup for task context creation
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Create a mock task with git_branch_id
        mock_task = Mock()
        mock_task.git_branch_id = self.branch_id
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
        
        # Create global context
        global_result = self.facade.create_context("global", "global_singleton", self.global_data)
        assert global_result["success"] is True
        
        # Create project context
        project_result = self.facade.create_context("project", self.project_id, self.project_data)
        assert project_result["success"] is True
        
        # Create branch context
        branch_result = self.facade.create_context("branch", self.branch_id, self.branch_data)
        assert branch_result["success"] is True
        
        # Create task context
        task_result = self.facade.create_context("task", self.task_id, self.task_data)
        if not task_result.get("success"):
            print(f"Task creation failed: {task_result}")
        assert task_result["success"] is True
        
        # Verify all levels were called
        assert mock_create.call_count == 4
        
        # Check that each level was created with correct parameters
        calls = mock_create.call_args_list
        assert calls[0][0] == ("global", "global_singleton", self.global_data)
        assert calls[1][0] == ("project", self.project_id, self.project_data)
        
        # Branch context has additional parent fields added by facade
        expected_branch_data = {
            "branch_workflow": self.branch_data.get("branch_workflow", {}),
            "branch_standards": self.branch_data.get("branch_standards", {}),
            "agent_assignments": self.branch_data.get("agent_assignments", {}),
            "parent_project_id": "default_project",
            "parent_project_context_id": "default_project"
        }
        assert calls[2][0] == ("branch", self.branch_id, expected_branch_data)
        
        # Task context is wrapped in task_data field by facade with actual branch_id
        expected_task_data = {
            "task_data": self.task_data,
            "parent_branch_id": self.branch_id,
            "parent_branch_context_id": self.branch_id
        }
        assert calls[3][0] == ("task", self.task_id, expected_task_data)

    @patch('fastmcp.task_management.application.services.hierarchical_context_service.HierarchicalContextService.get_context')
    def test_resolve_context_with_full_inheritance_chain(self, mock_get_context):
        """Test resolving context with complete 4-layer inheritance"""
        # Mock the get_context result to include all inherited data
        mock_get_context.return_value = {
            "task_data": {
                # Global data
                "coding_standards": {
                    "max_line_length": 88,
                    "test_coverage": 80
                },
                "security_policies": {
                    "require_mfa": True,
                    "audit_logging": True
                },
                # Project data
                "team_preferences": {
                    "code_review": "required",
                    "testing_framework": "pytest"
                },
                "technology_stack": {
                    "language": "python",
                    "framework": "fastapi"
                },
                # Branch data
                "branch_workflow": {
                    "feature_flags": True,
                    "ci_cd": True
                },
                "agent_assignments": {
                    "primary": "@coding_agent",
                    "reviewer": "@code_reviewer_agent"
                },
                # Task data
                "task_info": {
                    "implementation_approach": "TDD",
                    "priority": "high"
                },
                "implementation_notes": {
                    "special_requirements": "Performance critical"
                },
                # Inheritance metadata
                "inheritance_metadata": {
                    "inheritance_chain": ["global", "project", "branch", "task"],
                    "inherited_from": "branch"
                }
            }
        }
        
        # Resolve task context
        result = self.facade.resolve_context("task", self.task_id)
        
        # Verify the result includes data from all levels
        resolved_data = result["resolved_context"]
        
        # Check global data
        assert resolved_data["coding_standards"]["max_line_length"] == 88
        assert resolved_data["security_policies"]["require_mfa"] is True
        
        # Check project data
        assert resolved_data["team_preferences"]["code_review"] == "required"
        assert resolved_data["technology_stack"]["language"] == "python"
        
        # Check branch data
        assert resolved_data["branch_workflow"]["feature_flags"] is True
        assert resolved_data["agent_assignments"]["primary"] == "@coding_agent"
        
        # Check task data
        assert resolved_data["task_info"]["implementation_approach"] == "TDD"
        assert resolved_data["implementation_notes"]["special_requirements"] == "Performance critical"
        
        # Check inheritance metadata
        assert resolved_data["inheritance_metadata"]["inheritance_chain"] == ["global", "project", "branch", "task"]
        assert resolved_data["inheritance_metadata"]["inherited_from"] == "branch"

    @patch('fastmcp.task_management.application.services.hierarchical_context_service.HierarchicalContextService.get_context')
    def test_resolve_branch_context_shows_three_levels(self, mock_get_context):
        """Test resolving branch context shows global + project + branch"""
        mock_get_context.return_value = {
            "branch_workflow": {"feature_flags": True},
            "branch_standards": {},
            "agent_assignments": {"primary": "@coding_agent"},
            # Include inherited data from global and project
            "coding_standards": {"max_line_length": 88},
            "security_policies": {"require_mfa": True},
            "team_preferences": {"code_review": "required"},
            "technology_stack": {"language": "python"},
            # Inheritance metadata
            "inheritance_metadata": {
                "inheritance_chain": ["global", "project", "branch"],
                "inherited_from": "project"
            }
        }
        
        # Resolve branch context
        result = self.facade.resolve_context("branch", self.branch_id)
        
        resolved_data = result["resolved_context"]
        
        # Should have global + project + branch data
        assert "coding_standards" in resolved_data  # Global
        assert "team_preferences" in resolved_data  # Project
        assert "branch_workflow" in resolved_data   # Branch
        
        # Should NOT have task-specific data
        assert "task_info" not in resolved_data
        assert "implementation_notes" not in resolved_data
        
        # Check inheritance chain
        assert resolved_data["inheritance_metadata"]["inheritance_chain"] == ["global", "project", "branch"]

    @patch('fastmcp.task_management.application.services.hierarchical_context_service.HierarchicalContextService.get_context')
    def test_resolve_project_context_shows_two_levels(self, mock_get_context):
        """Test resolving project context shows global + project"""
        mock_get_context.return_value = {
            # Project data
            "team_preferences": {"code_review": "required"},
            "technology_stack": {"language": "python"},
            "project_workflow": {},
            "local_standards": {},
            # Include inherited data from global
            "coding_standards": {"max_line_length": 88},
            "security_policies": {"require_mfa": True},
            # Inheritance metadata
            "inheritance_metadata": {
                "inheritance_chain": ["global", "project"],
                "inherited_from": "global"
            }
        }
        
        # Resolve project context
        result = self.facade.resolve_context("project", self.project_id)
        
        resolved_data = result["resolved_context"]
        
        # Should have global + project data
        assert "coding_standards" in resolved_data  # Global
        assert "team_preferences" in resolved_data  # Project
        
        # Should NOT have branch or task data
        assert "branch_workflow" not in resolved_data
        assert "agent_assignments" not in resolved_data
        assert "task_info" not in resolved_data
        
        # Check inheritance chain
        assert resolved_data["inheritance_metadata"]["inheritance_chain"] == ["global", "project"]

    @patch('fastmcp.task_management.application.services.context_delegation_service.ContextDelegationService.delegate_context')
    def test_delegation_from_task_to_branch(self, mock_delegate):
        """Test delegating context from task to branch level"""
        mock_delegate.return_value = {
            "success": True,
            "delegation_id": "del-123",
            "status": "pending"
        }
        
        # Delegate task context to branch
        delegation_data = {
            "reusable_pattern": {
                "pattern_type": "authentication_flow",
                "implementation": "JWT with refresh tokens"
            }
        }
        
        result = self.facade.delegate_context(
            "task", self.task_id, "branch", delegation_data, "Reusable auth pattern"
        )
        
        assert result["success"] is True
        assert "delegation_id" in result
        
        # Verify delegation was called correctly with request object
        expected_request = {
            "source_level": "task",
            "source_id": self.task_id,
            "target_level": "branch",
            "data": delegation_data,
            "reason": "Reusable auth pattern",
            "created_at": mock_delegate.call_args[0][0]["created_at"]  # Use actual timestamp
        }
        actual_request = mock_delegate.call_args[0][0]
        # Check all fields except created_at (which has timestamp)
        assert actual_request["source_level"] == expected_request["source_level"]
        assert actual_request["source_id"] == expected_request["source_id"]
        assert actual_request["target_level"] == expected_request["target_level"]
        assert actual_request["data"] == expected_request["data"]
        assert actual_request["reason"] == expected_request["reason"]
        assert "created_at" in actual_request

    @patch('fastmcp.task_management.application.services.context_delegation_service.ContextDelegationService.delegate_context')
    def test_delegation_from_branch_to_project(self, mock_delegate):
        """Test delegating context from branch to project level"""
        mock_delegate.return_value = {
            "success": True,
            "delegation_id": "del-456",
            "status": "pending"
        }
        
        # Delegate branch context to project
        delegation_data = {
            "workflow_pattern": {
                "pattern_type": "ci_cd_pipeline",
                "implementation": "GitHub Actions with Docker"
            }
        }
        
        result = self.facade.delegate_context(
            "branch", self.branch_id, "project", delegation_data, "Reusable CI/CD pattern"
        )
        
        assert result["success"] is True
        
        # Verify delegation was called correctly with request object
        actual_request = mock_delegate.call_args[0][0]
        assert actual_request["source_level"] == "branch"
        assert actual_request["source_id"] == self.branch_id
        assert actual_request["target_level"] == "project"
        assert actual_request["data"] == delegation_data
        assert actual_request["reason"] == "Reusable CI/CD pattern"
        assert "created_at" in actual_request

    @patch('fastmcp.task_management.application.services.context_delegation_service.ContextDelegationService.delegate_context')
    def test_delegation_from_project_to_global(self, mock_delegate):
        """Test delegating context from project to global level"""
        mock_delegate.return_value = {
            "success": True,
            "delegation_id": "del-789",
            "status": "pending"
        }
        
        # Delegate project context to global
        delegation_data = {
            "organization_standard": {
                "standard_type": "code_review_process",
                "implementation": "Two-reviewer approval required"
            }
        }
        
        result = self.facade.delegate_context(
            "project", self.project_id, "global", delegation_data, "Organization-wide standard"
        )
        
        assert result["success"] is True
        
        # Verify delegation was called correctly with request object
        actual_request = mock_delegate.call_args[0][0]
        assert actual_request["source_level"] == "project"
        assert actual_request["source_id"] == self.project_id
        assert actual_request["target_level"] == "global"
        assert actual_request["data"] == delegation_data
        assert actual_request["reason"] == "Organization-wide standard"
        assert "created_at" in actual_request

    @patch('fastmcp.task_management.application.services.hierarchical_context_service.HierarchicalContextService.update_context')
    def test_update_context_with_propagation(self, mock_update):
        """Test updating context with change propagation"""
        mock_update.return_value = {
            "success": True,
            "updated_context": {"updated": True}
        }
        
        # Update branch context
        update_data = {
            "branch_workflow": {
                "feature_flags": False,  # Disable feature flags
                "ci_cd": True
            }
        }
        
        result = self.facade.update_context("branch", self.branch_id, update_data, propagate=True)
        
        assert result["success"] is True
        assert "propagation_result" in result
        
        # Verify update was called (propagation is handled in facade)
        mock_update.assert_called_once_with("branch", self.branch_id, update_data)

    def test_cache_health_monitoring(self):
        """Test cache health monitoring for 4-layer hierarchy"""
        # Update the mock on the cache service instance
        self.cache_service.get_cache_health.return_value = {
            "cache_entries": {
                "global": 1,
                "project": 5,
                "branch": 12,
                "task": 45
            },
            "cache_hit_rate": 0.87,
            "cache_miss_rate": 0.13,
            "average_resolution_time_ms": 8.5,
            "expired_entries": 3
        }
        
        # Get cache health
        health = self.facade.get_cache_health()
        
        assert health["cache_entries"]["global"] == 1
        assert health["cache_entries"]["project"] == 5
        assert health["cache_entries"]["branch"] == 12
        assert health["cache_entries"]["task"] == 45
        assert health["cache_hit_rate"] == 0.87

    def test_context_validation_for_4_layer_hierarchy(self):
        """Test context validation for 4-layer hierarchy"""
        # Create a mock resolved context with complete 4-layer inheritance
        resolved_context = {
            "coding_standards": {"max_line_length": 88},
            "team_preferences": {"code_review": "required"},
            "branch_workflow": {"feature_flags": True},
            "task_info": {"implementation_approach": "TDD"},
            "inheritance_metadata": {
                "inheritance_chain": ["global", "project", "branch", "task"],
                "inherited_from": "branch"
            }
        }
        
        # Validate task context
        validation_result = self.inheritance_service.validate_inheritance_chain(
            "task", self.task_id, resolved_context
        )
        
        assert validation_result["valid"] is True
        assert len(validation_result["issues"]) == 0
        assert validation_result["metadata"]["context_level"] == "task"

    def test_error_handling_for_invalid_hierarchy_levels(self):
        """Test error handling for invalid hierarchy levels"""
        # Test with invalid level
        result = self.facade.create_context("invalid_level", "test-id", {})
        
        # Should return error for invalid level
        assert result["success"] is False
        assert "error" in result

    def test_complex_inheritance_override_scenario(self):
        """Test complex inheritance with overrides at multiple levels"""
        # Create contexts with overlapping overrides
        global_context = {
            "settings": {
                "timeout": 30,
                "retries": 3,
                "debug": False
            }
        }
        
        project_context = {
            "global_overrides": {
                "settings.timeout": 60
            }
        }
        
        branch_context = {
            "local_overrides": {
                "settings.debug": True
            }
        }
        
        task_context = {
            "local_overrides": {
                "settings.retries": 5
            }
        }
        
        # Build inheritance chain
        project_inherited = self.inheritance_service.inherit_project_from_global(
            global_context, project_context
        )
        branch_inherited = self.inheritance_service.inherit_branch_from_project(
            project_inherited, branch_context
        )
        task_inherited = self.inheritance_service.inherit_task_from_branch(
            branch_inherited, task_context
        )
        
        # Verify final values
        final_settings = task_inherited["settings"]
        assert final_settings["timeout"] == 60    # Project override
        assert final_settings["debug"] is True    # Branch override
        assert final_settings["retries"] == 5     # Task override

    def test_performance_with_deep_inheritance_chain(self):
        """Test performance with deep inheritance chains"""
        import time
        
        # Create large context data
        large_global_data = {f"global_setting_{i}": f"value_{i}" for i in range(100)}
        large_project_data = {f"project_setting_{i}": f"value_{i}" for i in range(100)}
        large_branch_data = {f"branch_setting_{i}": f"value_{i}" for i in range(100)}
        large_task_data = {f"task_setting_{i}": f"value_{i}" for i in range(100)}
        
        # Measure inheritance time
        start_time = time.time()
        
        project_inherited = self.inheritance_service.inherit_project_from_global(
            large_global_data, large_project_data
        )
        branch_inherited = self.inheritance_service.inherit_branch_from_project(
            project_inherited, large_branch_data
        )
        task_inherited = self.inheritance_service.inherit_task_from_branch(
            branch_inherited, large_task_data
        )
        
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should complete within reasonable time (< 100ms)
        assert execution_time < 100.0
        
        # Verify all data is present
        assert len(task_inherited) >= 400  # At least 400 settings from all levels
        assert "global_setting_50" in task_inherited
        assert "project_setting_50" in task_inherited
        assert "branch_setting_50" in task_inherited
        assert "task_setting_50" in task_inherited