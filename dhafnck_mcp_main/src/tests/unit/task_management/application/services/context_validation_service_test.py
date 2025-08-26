"""Test suite for ContextValidationService.

Tests for context validation, rule enforcement, and schema compliance functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from datetime import datetime, timezone
import json

from fastmcp.task_management.application.services.context_validation_service import ContextValidationService


class TestContextValidationServiceInit:
    """Test ContextValidationService initialization."""

    def test_initialization_with_defaults(self):
        """Test service initialization with default values."""
        service = ContextValidationService()
        
        assert service.repository is None
        assert service._user_id is None
        assert service.validation_rules is not None
        assert len(service.validation_rules) > 0

    def test_initialization_with_parameters(self):
        """Test service initialization with custom parameters."""
        mock_repo = Mock()
        service = ContextValidationService(repository=mock_repo, user_id="test_user_123")
        
        assert service.repository == mock_repo
        assert service._user_id == "test_user_123"

    def test_with_user_method(self):
        """Test with_user method creates new instance with user context."""
        original_service = ContextValidationService()
        user_id = "test_user_456"
        
        user_scoped_service = original_service.with_user(user_id)
        
        assert user_scoped_service._user_id == user_id
        assert user_scoped_service is not original_service
        assert isinstance(user_scoped_service, ContextValidationService)

    def test_get_user_scoped_repository_with_with_user_method(self):
        """Test _get_user_scoped_repository with repository that has with_user method."""
        service = ContextValidationService(user_id="test_user")
        mock_repo = Mock()
        mock_user_scoped_repo = Mock()
        mock_repo.with_user.return_value = mock_user_scoped_repo
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_user_scoped_repo
        mock_repo.with_user.assert_called_once_with("test_user")

    def test_get_user_scoped_repository_with_user_id_property(self):
        """Test _get_user_scoped_repository with repository that has user_id property."""
        service = ContextValidationService(user_id="test_user")
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
        service = ContextValidationService()  # No user_id
        mock_repo = Mock()
        
        result = service._get_user_scoped_repository(mock_repo)
        
        assert result == mock_repo


class TestSyncWrapperMethods:
    """Test synchronous wrapper methods for facade compatibility."""

    def test_validate_context_sync_wrapper_no_loop(self):
        """Test synchronous validate_context wrapper when no event loop exists."""
        service = ContextValidationService()
        
        context_data = {"level": "task", "context_id": "test_123", "data": {"key": "value"}}
        
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No loop")):
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"valid": True, "score": 95.0}
                
                result = service.validate_context(context_data)
                
                assert result["valid"] is True
                assert result["score"] == 95.0
                mock_run.assert_called_once()

    def test_validate_context_sync_wrapper_running_loop(self):
        """Test synchronous validate_context wrapper when event loop is running."""
        service = ContextValidationService()
        
        context_data = {"level": "task", "context_id": "test_123", "data": {}}
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch('fastmcp.task_management.application.services.context_validation_service.logger') as mock_logger:
                result = service.validate_context(context_data)
                
                # Should return basic validation when loop is running
                assert "valid" in result
                mock_logger.debug.assert_called()

    def test_validate_context_sync_wrapper_exception(self):
        """Test synchronous validate_context wrapper exception handling."""
        service = ContextValidationService()
        
        context_data = {"level": "task", "context_id": "test_123"}
        
        with patch('asyncio.get_event_loop', side_effect=Exception("Unexpected error")):
            with patch('fastmcp.task_management.application.services.context_validation_service.logger') as mock_logger:
                result = service.validate_context(context_data)
                
                assert result["valid"] is False
                assert "error" in result
                mock_logger.error.assert_called()


class TestContextValidation:
    """Test context validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_context_async_success(self):
        """Test successful async context validation."""
        mock_repo = AsyncMock()
        service = ContextValidationService(repository=mock_repo)
        
        context_data = {
            "level": "task",
            "context_id": "task_123",
            "data": {
                "title": "Valid task title",
                "description": "Valid task description",
                "status": "todo",
                "priority": "medium"
            }
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is True
        assert result["score"] >= 80.0
        assert result["level"] == "task"
        assert result["context_id"] == "task_123"
        assert len(result["validation_results"]) > 0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_validate_context_async_missing_required_fields(self):
        """Test validation failure due to missing required fields."""
        service = ContextValidationService()
        
        context_data = {
            "level": "task",
            "context_id": "task_123",
            "data": {
                # Missing title and description
                "status": "todo"
            }
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is False
        assert result["score"] < 70.0
        assert any("required" in str(vr["message"]).lower() for vr in result["validation_results"])

    @pytest.mark.asyncio
    async def test_validate_context_async_invalid_schema(self):
        """Test validation failure due to schema violations."""
        service = ContextValidationService()
        
        context_data = {
            "level": "task",
            "context_id": "task_123",
            "data": {
                "title": "T",  # Too short
                "description": "D",  # Too short
                "status": "invalid_status",  # Invalid enum
                "priority": "invalid_priority"  # Invalid enum
            }
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is False
        assert result["score"] < 50.0
        validation_messages = [vr["message"] for vr in result["validation_results"]]
        assert any("title" in msg.lower() for msg in validation_messages)
        assert any("status" in msg.lower() for msg in validation_messages)

    @pytest.mark.asyncio
    async def test_validate_context_async_global_level(self):
        """Test validation of global level context."""
        service = ContextValidationService()
        
        context_data = {
            "level": "global",
            "context_id": "global_singleton",
            "data": {
                "organizational_standards": "High quality standards",
                "security_policies": ["policy1", "policy2"],
                "compliance_requirements": {"gdpr": True, "soc2": True}
            }
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is True
        assert result["score"] >= 85.0
        assert result["level"] == "global"

    @pytest.mark.asyncio
    async def test_validate_context_async_project_level(self):
        """Test validation of project level context."""
        service = ContextValidationService()
        
        context_data = {
            "level": "project",
            "context_id": "proj_456",
            "data": {
                "name": "Test Project",
                "description": "A comprehensive test project",
                "team_members": ["user1", "user2"],
                "technologies": ["Python", "React"],
                "project_goals": "Build amazing software"
            }
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is True
        assert result["score"] >= 80.0
        assert result["level"] == "project"

    @pytest.mark.asyncio
    async def test_validate_context_async_branch_level(self):
        """Test validation of branch level context."""
        service = ContextValidationService()
        
        context_data = {
            "level": "branch",
            "context_id": "branch_789",
            "data": {
                "git_branch_name": "feature/new-auth",
                "git_branch_description": "Implementing new authentication system",
                "assigned_agents": ["@coding_agent"],
                "feature_scope": "Authentication module implementation"
            }
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is True
        assert result["score"] >= 75.0
        assert result["level"] == "branch"

    @pytest.mark.asyncio
    async def test_validate_context_async_invalid_level(self):
        """Test validation with invalid context level."""
        service = ContextValidationService()
        
        context_data = {
            "level": "invalid_level",
            "context_id": "test_123",
            "data": {"key": "value"}
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is False
        assert result["score"] == 0.0
        assert any("invalid level" in vr["message"].lower() for vr in result["validation_results"])

    @pytest.mark.asyncio
    async def test_validate_context_async_missing_context_id(self):
        """Test validation with missing context_id."""
        service = ContextValidationService()
        
        context_data = {
            "level": "task",
            "data": {"title": "Test task"}
        }
        
        result = await service.validate_context_async(context_data)
        
        assert result["valid"] is False
        assert result["score"] < 30.0
        assert any("context_id" in vr["message"].lower() for vr in result["validation_results"])

    @pytest.mark.asyncio
    async def test_validate_context_async_exception_handling(self):
        """Test async validation exception handling."""
        service = ContextValidationService()
        
        # Create context data that will cause validation exception
        with patch.object(service, '_validate_level_specific_rules', side_effect=Exception("Validation error")):
            result = await service.validate_context_async({"level": "task", "context_id": "test"})
        
        assert result["valid"] is False
        assert "error" in result
        assert result["score"] == 0.0


class TestValidationRules:
    """Test validation rules functionality."""

    def test_validate_level_specific_rules_task(self):
        """Test task-level specific validation rules."""
        service = ContextValidationService()
        
        valid_task_data = {
            "title": "Valid Task Title",
            "description": "Valid task description with enough detail",
            "status": "todo",
            "priority": "high",
            "assignees": ["user1", "user2"]
        }
        
        violations = service._validate_level_specific_rules("task", valid_task_data)
        
        # Should have minimal violations for valid data
        assert len(violations) <= 2

    def test_validate_level_specific_rules_task_violations(self):
        """Test task-level validation with rule violations."""
        service = ContextValidationService()
        
        invalid_task_data = {
            "title": "T",  # Too short
            "description": "D",  # Too short
            "status": "invalid",  # Invalid status
            "priority": "urgent_critical_super_high"  # Invalid priority
        }
        
        violations = service._validate_level_specific_rules("task", invalid_task_data)
        
        assert len(violations) >= 3
        violation_messages = [v["message"] for v in violations]
        assert any("title" in msg.lower() for msg in violation_messages)
        assert any("description" in msg.lower() for msg in violation_messages)
        assert any("status" in msg.lower() for msg in violation_messages)

    def test_validate_level_specific_rules_project(self):
        """Test project-level specific validation rules."""
        service = ContextValidationService()
        
        valid_project_data = {
            "name": "Valid Project Name",
            "description": "Valid project description with sufficient detail",
            "team_members": ["member1", "member2"],
            "technologies": ["Python", "JavaScript"]
        }
        
        violations = service._validate_level_specific_rules("project", valid_project_data)
        
        # Should have minimal violations for valid data
        assert len(violations) <= 1

    def test_validate_level_specific_rules_global(self):
        """Test global-level specific validation rules."""
        service = ContextValidationService()
        
        global_data = {
            "organizational_standards": "Company-wide standards document",
            "security_policies": ["policy1", "policy2"],
            "compliance_requirements": {"gdpr": True}
        }
        
        violations = service._validate_level_specific_rules("global", global_data)
        
        # Global level has fewer restrictions
        assert len(violations) <= 1

    def test_validate_level_specific_rules_branch(self):
        """Test branch-level specific validation rules."""
        service = ContextValidationService()
        
        branch_data = {
            "git_branch_name": "feature/test-branch",
            "git_branch_description": "Test branch for feature implementation",
            "assigned_agents": ["@coding_agent"]
        }
        
        violations = service._validate_level_specific_rules("branch", branch_data)
        
        assert len(violations) <= 2

    def test_validate_data_quality(self):
        """Test data quality validation."""
        service = ContextValidationService()
        
        high_quality_data = {
            "title": "Well-structured task title",
            "description": "Comprehensive description with clear objectives and acceptance criteria",
            "metadata": {"version": "1.0", "author": "user1"},
            "tags": ["important", "urgent"]
        }
        
        quality_score = service._validate_data_quality(high_quality_data)
        
        assert quality_score >= 80.0

    def test_validate_data_quality_low_quality(self):
        """Test data quality validation with low quality data."""
        service = ContextValidationService()
        
        low_quality_data = {
            "title": "T",
            "description": "D",
            "empty_field": "",
            "null_field": None
        }
        
        quality_score = service._validate_data_quality(low_quality_data)
        
        assert quality_score < 60.0

    def test_calculate_validation_score(self):
        """Test validation score calculation."""
        service = ContextValidationService()
        
        violations = [
            {"severity": "error", "score_impact": -20},
            {"severity": "warning", "score_impact": -10},
            {"severity": "info", "score_impact": -5}
        ]
        
        score = service._calculate_validation_score(violations, base_score=100.0)
        
        # Should subtract impact scores: 100 - 20 - 10 - 5 = 65
        assert score == 65.0

    def test_calculate_validation_score_with_minimum(self):
        """Test validation score calculation with minimum threshold."""
        service = ContextValidationService()
        
        severe_violations = [
            {"severity": "error", "score_impact": -50},
            {"severity": "error", "score_impact": -50},
            {"severity": "error", "score_impact": -50}
        ]
        
        score = service._calculate_validation_score(severe_violations, base_score=100.0)
        
        # Should not go below 0
        assert score == 0.0


class TestSchemaValidation:
    """Test schema validation functionality."""

    def test_validate_schema_compliance_valid(self):
        """Test schema compliance validation with valid data."""
        service = ContextValidationService()
        
        valid_context = {
            "level": "task",
            "context_id": "task_123",
            "data": {
                "title": "Valid task",
                "description": "Valid description",
                "status": "in_progress"
            }
        }
        
        violations = service._validate_schema_compliance(valid_context)
        
        # Should have minimal or no schema violations
        assert len(violations) <= 1

    def test_validate_schema_compliance_invalid_structure(self):
        """Test schema compliance with invalid structure."""
        service = ContextValidationService()
        
        invalid_context = {
            "level": "task",
            # Missing context_id
            "data": {
                # Missing required fields
                "invalid_field": "value"
            }
        }
        
        violations = service._validate_schema_compliance(invalid_context)
        
        assert len(violations) >= 1
        violation_messages = [v["message"] for v in violations]
        assert any("context_id" in msg.lower() for msg in violation_messages)

    def test_is_valid_json_structure(self):
        """Test JSON structure validation."""
        service = ContextValidationService()
        
        valid_data = {
            "string_field": "value",
            "number_field": 42,
            "boolean_field": True,
            "array_field": [1, 2, 3],
            "object_field": {"nested": "value"}
        }
        
        assert service._is_valid_json_structure(valid_data) is True

    def test_is_valid_json_structure_with_invalid_types(self):
        """Test JSON structure validation with invalid types."""
        service = ContextValidationService()
        
        # Functions are not JSON serializable
        invalid_data = {
            "valid_field": "value",
            "invalid_field": lambda x: x  # Function not JSON serializable
        }
        
        assert service._is_valid_json_structure(invalid_data) is False

    def test_validate_field_types(self):
        """Test field type validation."""
        service = ContextValidationService()
        
        data = {
            "title": "String value",
            "priority": "high",
            "assignees": ["user1", "user2"],
            "metadata": {"key": "value"}
        }
        
        violations = service._validate_field_types(data)
        
        # Should have no type violations for properly typed data
        assert len(violations) == 0

    def test_validate_field_types_with_violations(self):
        """Test field type validation with type violations."""
        service = ContextValidationService()
        
        data = {
            "title": 123,  # Should be string
            "assignees": "not_a_list",  # Should be list
            "metadata": "not_a_dict"  # Should be dict
        }
        
        violations = service._validate_field_types(data)
        
        assert len(violations) >= 2
        violation_messages = [v["message"] for v in violations]
        assert any("title" in msg.lower() and "string" in msg.lower() for msg in violation_messages)


class TestValidationReporting:
    """Test validation reporting functionality."""

    @pytest.mark.asyncio
    async def test_generate_validation_report(self):
        """Test validation report generation."""
        service = ContextValidationService()
        
        contexts = [
            {"level": "task", "context_id": "task1", "data": {"title": "Valid task"}},
            {"level": "task", "context_id": "task2", "data": {"title": "T"}},  # Invalid
            {"level": "project", "context_id": "proj1", "data": {"name": "Valid project"}}
        ]
        
        report = await service.generate_validation_report(contexts)
        
        assert report["total_contexts"] == 3
        assert report["valid_contexts"] >= 1
        assert report["invalid_contexts"] >= 1
        assert "average_score" in report
        assert "validation_summary" in report
        assert "timestamp" in report

    @pytest.mark.asyncio
    async def test_generate_validation_report_empty_contexts(self):
        """Test validation report generation with empty context list."""
        service = ContextValidationService()
        
        report = await service.generate_validation_report([])
        
        assert report["total_contexts"] == 0
        assert report["valid_contexts"] == 0
        assert report["invalid_contexts"] == 0
        assert report["average_score"] == 100.0  # Default for empty

    @pytest.mark.asyncio
    async def test_get_validation_statistics(self):
        """Test validation statistics collection."""
        mock_repo = AsyncMock()
        mock_repo.get_context_count.return_value = 150
        mock_repo.get_validation_metrics.return_value = {
            "average_score": 87.5,
            "total_validations": 1000,
            "pass_rate": 0.85
        }
        
        service = ContextValidationService(repository=mock_repo)
        
        stats = await service.get_validation_statistics()
        
        assert stats["total_contexts"] == 150
        assert stats["average_validation_score"] == 87.5
        assert stats["validation_pass_rate"] == 0.85
        assert "validation_health" in stats

    @pytest.mark.asyncio
    async def test_get_validation_statistics_exception(self):
        """Test validation statistics exception handling."""
        mock_repo = AsyncMock()
        mock_repo.get_context_count.side_effect = Exception("DB error")
        
        service = ContextValidationService(repository=mock_repo)
        
        stats = await service.get_validation_statistics()
        
        assert stats["error"] is not None
        assert stats["total_contexts"] == 0


class TestUtilityMethods:
    """Test utility methods in validation service."""

    def test_sanitize_context_data(self):
        """Test context data sanitization."""
        service = ContextValidationService()
        
        dirty_data = {
            "title": "  Valid Title  ",
            "description": "Valid description\n\nwith extra spaces  ",
            "empty_field": "",
            "null_field": None,
            "whitespace_only": "   ",
            "nested": {
                "field": "  nested value  ",
                "empty": ""
            }
        }
        
        clean_data = service._sanitize_context_data(dirty_data)
        
        assert clean_data["title"] == "Valid Title"
        assert clean_data["description"] == "Valid description\n\nwith extra spaces"
        assert "empty_field" not in clean_data
        assert "null_field" not in clean_data
        assert "whitespace_only" not in clean_data
        assert clean_data["nested"]["field"] == "nested value"
        assert "empty" not in clean_data["nested"]

    def test_extract_validation_metadata(self):
        """Test validation metadata extraction."""
        service = ContextValidationService()
        
        context_data = {
            "level": "task",
            "context_id": "task_123",
            "data": {"title": "Test", "complex": {"nested": "value"}},
            "metadata": {"version": "1.0"}
        }
        
        metadata = service._extract_validation_metadata(context_data)
        
        assert metadata["level"] == "task"
        assert metadata["context_id"] == "task_123"
        assert metadata["data_complexity"] > 0
        assert metadata["field_count"] >= 2
        assert "has_nested_data" in metadata

    def test_format_validation_result(self):
        """Test validation result formatting."""
        service = ContextValidationService()
        
        raw_result = {
            "valid": True,
            "score": 87.5,
            "violations": [{"message": "Minor issue", "severity": "warning"}],
            "level": "task",
            "context_id": "task_123"
        }
        
        formatted = service._format_validation_result(raw_result)
        
        assert formatted["is_valid"] == True
        assert formatted["validation_score"] == 87.5
        assert formatted["level"] == "task"
        assert formatted["context_identifier"] == "task_123"
        assert len(formatted["validation_issues"]) == 1
        assert "validation_timestamp" in formatted

    def test_merge_validation_results(self):
        """Test merging multiple validation results."""
        service = ContextValidationService()
        
        results = [
            {"valid": True, "score": 90.0, "violations": []},
            {"valid": False, "score": 70.0, "violations": [{"severity": "error"}]},
            {"valid": True, "score": 85.0, "violations": [{"severity": "warning"}]}
        ]
        
        merged = service._merge_validation_results(results)
        
        assert merged["overall_valid"] is False  # At least one invalid
        assert merged["average_score"] == 81.67  # Average of 90, 70, 85
        assert merged["total_violations"] == 2
        assert merged["results_count"] == 3