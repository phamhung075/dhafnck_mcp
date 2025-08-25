"""
Comprehensive V2 API Integration Tests for Context System

This test suite validates:
1. All v2 context API endpoints work correctly with authentication
2. Context buttons in frontend can access v2 API endpoints
3. Response formats match task/subtask v2 API patterns
4. Authentication is required for all v2 context endpoints
5. Context data consistency across API versions
6. Error handling and user-friendly messages
7. Context operations integration with existing task/subtask workflows

Author: Test Orchestrator Agent
Date: 2025-08-25
"""

import pytest
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Core imports
from fastmcp.auth.api_server import app
from fastmcp.auth.domain.entities.user import User
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.infrastructure.database.models import (
    GLOBAL_SINGLETON_UUID,
    Project,
    ProjectGitBranch,
    Task
)
from fastmcp.task_management.infrastructure.database.database_config import get_db_config


class TestContextV2APIComplete:
    """Complete integration tests for Context v2 API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user."""
        user = MagicMock(spec=User)
        user.id = "test-user-" + str(uuid.uuid4())[:8]
        user.email = "test@example.com"
        user.username = "testuser"
        return user
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data following v2 API patterns."""
        return {
            "title": "V2 API Test Context",
            "description": "Testing v2 API endpoints for context management",
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "2.0",
                "api_version": "v2"
            },
            "settings": {
                "auto_sync": True,
                "notifications_enabled": True,
                "theme": "dark"
            },
            "insights": [
                "V2 API provides better structure",
                "Authentication is properly integrated",
                "Response formats are consistent"
            ],
            "progress_indicators": {
                "completion_percentage": 75,
                "milestones_completed": 3,
                "milestones_total": 4
            }
        }
    
    @pytest.fixture
    def mock_facade_with_success(self, sample_context_data):
        """Mock facade that returns successful responses."""
        mock_facade = MagicMock()
        
        # Default successful responses for all operations
        mock_facade.create_context.return_value = {
            "success": True,
            "message": "Context created successfully",
            "context": {"id": "test-context-123", "data": sample_context_data}
        }
        
        mock_facade.get_context.return_value = {
            "success": True,
            "context": {"id": "test-context-123", "data": sample_context_data}
        }
        
        mock_facade.update_context.return_value = {
            "success": True,
            "message": "Context updated successfully",
            "context": {"id": "test-context-123", "data": sample_context_data}
        }
        
        mock_facade.delete_context.return_value = {
            "success": True,
            "message": "Context deleted successfully"
        }
        
        mock_facade.resolve_context.return_value = {
            "success": True,
            "resolved_context": {
                "task": sample_context_data,
                "branch": {"git_branch_name": "feature/v2-api"},
                "project": {"project_name": "V2 API Project"},
                "global": {"autonomous_rules": {"v2_rule": "enabled"}}
            }
        }
        
        mock_facade.list_contexts.return_value = {
            "success": True,
            "contexts": [
                {"id": "context-1", "data": sample_context_data},
                {"id": "context-2", "data": {"title": "Another Context"}}
            ]
        }
        
        mock_facade.delegate_context.return_value = {
            "success": True,
            "message": "Context delegated successfully",
            "delegation_id": "delegation-123"
        }
        
        mock_facade.add_insight.return_value = {
            "success": True,
            "message": "Insight added successfully",
            "insight_id": "insight-123"
        }
        
        mock_facade.add_progress.return_value = {
            "success": True,
            "message": "Progress update added successfully",
            "progress_id": "progress-123"
        }
        
        mock_facade.get_context_summary.return_value = {
            "success": True,
            "summary": {
                "total_contexts": 5,
                "active_contexts": 3,
                "insights_count": 12,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        
        return mock_facade
    
    def setup_authenticated_request(self, mock_get_current_user, mock_get_db, user, session):
        """Setup common mocks for authenticated requests."""
        mock_get_current_user.return_value = user
        mock_get_db.return_value = session
    
    # V2 API Endpoint Tests - Authentication Required
    
    def test_all_v2_context_endpoints_require_authentication(self, client):
        """Test that all v2 context endpoints require authentication."""
        test_context_id = str(uuid.uuid4())
        
        endpoints_to_test = [
            # Context CRUD operations
            ("POST", "/api/v2/contexts/task", {"level": "task", "context_id": test_context_id, "data": {"test": "data"}}),
            ("POST", "/api/v2/contexts/project", {"level": "project", "context_id": test_context_id, "data": {"test": "data"}}),
            ("POST", "/api/v2/contexts/branch", {"level": "branch", "context_id": test_context_id, "data": {"test": "data"}}),
            ("POST", "/api/v2/contexts/global", {"level": "global", "context_id": test_context_id, "data": {"test": "data"}}),
            
            # Get operations
            ("GET", f"/api/v2/contexts/task/{test_context_id}", {}),
            ("GET", f"/api/v2/contexts/project/{test_context_id}", {}),
            ("GET", f"/api/v2/contexts/branch/{test_context_id}", {}),
            ("GET", f"/api/v2/contexts/global/{test_context_id}", {}),
            
            # Update operations
            ("PUT", f"/api/v2/contexts/task/{test_context_id}", {"data": {"updated": "data"}}),
            ("PUT", f"/api/v2/contexts/project/{test_context_id}", {"data": {"updated": "data"}}),
            ("PUT", f"/api/v2/contexts/branch/{test_context_id}", {"data": {"updated": "data"}}),
            ("PUT", f"/api/v2/contexts/global/{test_context_id}", {"data": {"updated": "data"}}),
            
            # Delete operations
            ("DELETE", f"/api/v2/contexts/task/{test_context_id}", {}),
            ("DELETE", f"/api/v2/contexts/project/{test_context_id}", {}),
            ("DELETE", f"/api/v2/contexts/branch/{test_context_id}", {}),
            ("DELETE", f"/api/v2/contexts/global/{test_context_id}", {}),
            
            # List operations
            ("GET", "/api/v2/contexts/task/list", {}),
            ("GET", "/api/v2/contexts/project/list", {}),
            ("GET", "/api/v2/contexts/branch/list", {}),
            ("GET", "/api/v2/contexts/global/list", {}),
            
            # Advanced operations
            ("GET", f"/api/v2/contexts/task/{test_context_id}/resolve", {}),
            ("POST", f"/api/v2/contexts/task/{test_context_id}/delegate", {
                "delegate_to": "project",
                "delegate_data": {"pattern": "test"},
                "delegation_reason": "Testing"
            }),
            ("POST", f"/api/v2/contexts/task/{test_context_id}/insights", {
                "content": "Test insight",
                "category": "technical"
            }),
            ("POST", f"/api/v2/contexts/task/{test_context_id}/progress", {
                "content": "Progress update"
            }),
            ("GET", f"/api/v2/contexts/task/{test_context_id}/summary", {}),
        ]
        
        for method, endpoint, json_data in endpoints_to_test:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json=json_data)
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 401, f"{method} {endpoint} should require authentication"
    
    # V2 API Context CRUD Operations Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_creation_all_levels(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                           client, mock_user, mock_session, mock_facade_with_success, sample_context_data):
        """Test context creation through v2 API for all levels."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        levels_to_test = ["global", "project", "branch", "task"]
        
        for level in levels_to_test:
            context_id = f"{level}-context-{uuid.uuid4()}"
            
            request_data = {
                "level": level,
                "context_id": context_id,
                "data": sample_context_data
            }
            
            response = client.post(f"/api/v2/contexts/{level}", json=request_data)
            
            assert response.status_code == 200, f"Failed to create {level} context"
            data = response.json()
            assert data["success"] is True
            assert "Context created successfully" in data["message"]
            assert "context" in data
            
            # Verify facade was called correctly
            mock_facade_with_success.create_context.assert_called_with(
                level=level,
                context_id=context_id,
                data=sample_context_data
            )
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_retrieval_with_include_inherited(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                                         client, mock_user, mock_session, mock_facade_with_success):
        """Test context retrieval with include_inherited parameter."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        
        # Test without include_inherited
        response = client.get(f"/api/v2/contexts/task/{context_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "context" in data
        
        # Test with include_inherited=true
        response = client.get(f"/api/v2/contexts/task/{context_id}?include_inherited=true")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "context" in data
        
        # Verify facade was called with correct parameters
        mock_facade_with_success.get_context.assert_called_with(
            level="task",
            context_id=context_id,
            include_inherited=True
        )
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_update_with_propagate_changes(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                                      client, mock_user, mock_session, mock_facade_with_success, sample_context_data):
        """Test context update with propagate_changes parameter."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        update_data = {
            "data": sample_context_data,
            "propagate_changes": True
        }
        
        response = client.put(f"/api/v2/contexts/task/{context_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Context updated successfully" in data["message"]
        
        # Verify facade was called with propagate_changes
        mock_facade_with_success.update_context.assert_called_with(
            level="task",
            context_id=context_id,
            data=sample_context_data,
            propagate_changes=True
        )
    
    # V2 API Advanced Operations Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_resolution(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                   client, mock_user, mock_session, mock_facade_with_success):
        """Test context resolution endpoint."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        
        response = client.get(f"/api/v2/contexts/task/{context_id}/resolve")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "resolved_context" in data
        assert "task" in data["resolved_context"]
        assert "branch" in data["resolved_context"]
        assert "project" in data["resolved_context"]
        assert "global" in data["resolved_context"]
        
        # Verify facade was called correctly
        mock_facade_with_success.resolve_context.assert_called_with(
            level="task",
            context_id=context_id
        )
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_delegation(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                   client, mock_user, mock_session, mock_facade_with_success):
        """Test context delegation endpoint."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        delegation_data = {
            "delegate_to": "project",
            "delegate_data": {
                "pattern": "authentication_flow",
                "reusable_components": ["jwt_validation", "user_context"]
            },
            "delegation_reason": "Pattern is reusable across multiple tasks in this project"
        }
        
        response = client.post(f"/api/v2/contexts/task/{context_id}/delegate", json=delegation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Context delegated successfully" in data["message"]
        assert "delegation_id" in data
        
        # Verify facade was called correctly
        mock_facade_with_success.delegate_context.assert_called_with(
            level="task",
            context_id=context_id,
            delegate_to="project",
            delegate_data=delegation_data["delegate_data"],
            delegation_reason=delegation_data["delegation_reason"]
        )
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_insights_addition(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                          client, mock_user, mock_session, mock_facade_with_success):
        """Test adding insights to context via v2 API."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        insight_data = {
            "content": "V2 API provides better error handling and response structure",
            "category": "technical",
            "importance": "high",
            "agent": "test_orchestrator_agent"
        }
        
        response = client.post(f"/api/v2/contexts/task/{context_id}/insights", json=insight_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Insight added successfully" in data["message"]
        assert "insight_id" in data
        
        # Verify facade was called correctly
        mock_facade_with_success.add_insight.assert_called_with(
            level="task",
            context_id=context_id,
            content=insight_data["content"],
            category=insight_data["category"],
            importance=insight_data["importance"],
            agent=insight_data["agent"]
        )
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_progress_updates(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                         client, mock_user, mock_session, mock_facade_with_success):
        """Test adding progress updates to context via v2 API."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        progress_data = {
            "content": "Completed v2 API endpoint testing - all tests passing",
            "agent": "test_orchestrator_agent"
        }
        
        response = client.post(f"/api/v2/contexts/task/{context_id}/progress", json=progress_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Progress update added successfully" in data["message"]
        assert "progress_id" in data
        
        # Verify facade was called correctly
        mock_facade_with_success.add_progress.assert_called_with(
            level="task",
            context_id=context_id,
            content=progress_data["content"],
            agent=progress_data["agent"]
        )
    
    # V2 API List Operations Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_listing_with_filters(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                             client, mock_user, mock_session, mock_facade_with_success):
        """Test context listing with various filter parameters."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        # Test with JSON filters
        filters = {
            "status": "active",
            "created_after": "2024-01-01",
            "tags": ["v2-api", "testing"]
        }
        filters_json = json.dumps(filters)
        
        response = client.get(f"/api/v2/contexts/task/list?filters={filters_json}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contexts" in data
        assert len(data["contexts"]) == 2  # Based on mock setup
        
        # Verify facade was called with parsed filters
        mock_facade_with_success.list_contexts.assert_called_with(
            level="task",
            filters=filters
        )
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_context_listing_includes_user_info(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                                   client, mock_user, mock_session, mock_facade_with_success):
        """Test that context listing includes user information in response."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        response = client.get("/api/v2/contexts/task/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"] == mock_user.email
        assert "contexts" in data
        assert len(data["contexts"]) > 0
    
    # Response Format Consistency Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_api_response_format_consistency(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                                client, mock_user, mock_session, mock_facade_with_success, sample_context_data):
        """Test that v2 API responses follow consistent format patterns."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        mock_get_facade.return_value = mock_facade_with_success
        
        context_id = "test-context-123"
        
        # Test all operations have consistent response structure
        operations = [
            ("POST", f"/api/v2/contexts/task", {"level": "task", "context_id": context_id, "data": sample_context_data}),
            ("GET", f"/api/v2/contexts/task/{context_id}", {}),
            ("PUT", f"/api/v2/contexts/task/{context_id}", {"data": sample_context_data}),
            ("GET", f"/api/v2/contexts/task/{context_id}/resolve", {}),
            ("GET", "/api/v2/contexts/task/list", {}),
        ]
        
        for method, endpoint, json_data in operations:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json=json_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # All responses should have success field
            assert "success" in data
            assert data["success"] is True
            
            # Responses should have appropriate content based on operation
            if method == "GET" and "list" in endpoint:
                assert "contexts" in data
                assert "user" in data
            elif method == "GET" and "resolve" in endpoint:
                assert "resolved_context" in data
            elif method in ["POST", "PUT"]:
                assert "message" in data
    
    # Error Handling Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    def test_v2_api_invalid_json_filters_error_handling(self, mock_get_db, mock_get_current_user, client, mock_user, mock_session):
        """Test error handling for invalid JSON in filters parameter."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        
        response = client.get("/api/v2/contexts/task/list?filters=invalid-json-string")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid filters JSON" in data["detail"]
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_api_facade_error_propagation(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                             client, mock_user, mock_session):
        """Test that facade errors are properly propagated with appropriate HTTP status codes."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        
        error_scenarios = [
            ("Context not found", 404),
            ("Validation failed: Invalid context data", 400),
            ("Permission denied: Cannot access context", 403),
            ("Internal processing error", 500),
        ]
        
        for error_message, expected_status in error_scenarios:
            mock_facade = MagicMock()
            mock_facade.get_context.return_value = {
                "success": False,
                "error": error_message
            }
            mock_get_facade.return_value = mock_facade
            
            response = client.get("/api/v2/contexts/task/test-context-123")
            
            # Map error types to appropriate HTTP status codes
            if "not found" in error_message.lower():
                assert response.status_code == 404
            elif "validation" in error_message.lower():
                assert response.status_code == 400
            elif "permission" in error_message.lower():
                assert response.status_code == 403
            else:
                assert response.status_code in [400, 500]  # Default error handling
    
    # Frontend Integration Tests
    
    def test_v2_api_endpoints_support_frontend_context_buttons(self, client):
        """Test that v2 API endpoints can be accessed by frontend context buttons."""
        # This test simulates frontend AJAX calls to context endpoints
        # All these endpoints should be available for frontend context buttons
        
        frontend_accessible_endpoints = [
            "/api/v2/contexts/task/list",
            "/api/v2/contexts/project/list",
            "/api/v2/contexts/branch/list",
            "/api/v2/contexts/global/list",
        ]
        
        for endpoint in frontend_accessible_endpoints:
            # Test OPTIONS request (CORS preflight)
            options_response = client.options(endpoint)
            # Should not return 404 (endpoint exists)
            assert options_response.status_code != 404
            
            # Test GET request returns authentication error (not 404)
            get_response = client.get(endpoint)
            assert get_response.status_code == 401  # Requires auth, but endpoint exists
    
    # Performance Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_api_performance_with_large_context_list(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                                        client, mock_user, mock_session):
        """Test v2 API performance with large context lists."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        
        # Mock facade to return large context list
        large_context_list = [
            {"id": f"context-{i}", "data": {"title": f"Context {i}", "index": i}}
            for i in range(100)
        ]
        
        mock_facade = MagicMock()
        mock_facade.list_contexts.return_value = {
            "success": True,
            "contexts": large_context_list
        }
        mock_get_facade.return_value = mock_facade
        
        import time
        start_time = time.time()
        
        response = client.get("/api/v2/contexts/task/list")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["contexts"]) == 100
        
        # Response time should be reasonable (less than 1 second for 100 contexts)
        assert response_time < 1.0, f"Response time too slow: {response_time}s"
    
    # Data Consistency Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade')
    def test_v2_api_data_consistency_across_operations(self, mock_get_facade, mock_get_db, mock_get_current_user,
                                                       client, mock_user, mock_session, sample_context_data):
        """Test data consistency across create, read, update operations."""
        self.setup_authenticated_request(mock_get_current_user, mock_get_db, mock_user, mock_session)
        
        context_id = "consistency-test-context"
        
        # Mock facade to track data changes
        context_store = {}
        
        def mock_create_context(level, context_id, data, **kwargs):
            context_store[context_id] = data
            return {"success": True, "context": {"id": context_id, "data": data}}
        
        def mock_get_context(level, context_id, **kwargs):
            if context_id in context_store:
                return {"success": True, "context": {"id": context_id, "data": context_store[context_id]}}
            return {"success": False, "error": "Context not found"}
        
        def mock_update_context(level, context_id, data, **kwargs):
            if context_id in context_store:
                context_store[context_id].update(data)
                return {"success": True, "context": {"id": context_id, "data": context_store[context_id]}}
            return {"success": False, "error": "Context not found"}
        
        mock_facade = MagicMock()
        mock_facade.create_context.side_effect = mock_create_context
        mock_facade.get_context.side_effect = mock_get_context
        mock_facade.update_context.side_effect = mock_update_context
        mock_get_facade.return_value = mock_facade
        
        # Create context
        create_response = client.post("/api/v2/contexts/task", json={
            "level": "task",
            "context_id": context_id,
            "data": sample_context_data
        })
        assert create_response.status_code == 200
        
        # Read context
        read_response = client.get(f"/api/v2/contexts/task/{context_id}")
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data["context"]["data"]["title"] == sample_context_data["title"]
        
        # Update context
        updated_data = {"title": "Updated V2 API Test Context"}
        update_response = client.put(f"/api/v2/contexts/task/{context_id}", json={
            "data": updated_data
        })
        assert update_response.status_code == 200
        
        # Read updated context
        read_updated_response = client.get(f"/api/v2/contexts/task/{context_id}")
        assert read_updated_response.status_code == 200
        read_updated_data = read_updated_response.json()
        assert read_updated_data["context"]["data"]["title"] == "Updated V2 API Test Context"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])