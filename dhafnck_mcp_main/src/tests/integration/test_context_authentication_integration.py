"""
Comprehensive Integration Tests for Context Dual Authentication System

This test suite validates:
1. Context operations require authentication like tasks/subtasks
2. User isolation works correctly across all context levels
3. Context operations fail gracefully without authentication
4. Context MCP tools use authenticated user_id
5. Authentication works consistently across all context API endpoints
6. Context inheritance respects user boundaries
7. Error handling provides user-friendly messages

Author: Test Orchestrator Agent
Date: 2025-08-25
"""

import pytest
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Core imports
from fastmcp.auth.api_server import app
from fastmcp.auth.domain.entities.user import User
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.infrastructure.database.models import (
    GLOBAL_SINGLETON_UUID,
    GlobalContext as GlobalContextModel,
    ProjectContext as ProjectContextModel,
    BranchContext as BranchContextModel,
    TaskContext as TaskContextModel,
    Project,
    ProjectGitBranch,
    Task
)
from fastmcp.task_management.infrastructure.database.database_config import get_db_config


class TestContextAuthenticationIntegration:
    """Integration tests for context authentication and user isolation."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def user_alice(self):
        """Mock user Alice for testing."""
        user = MagicMock(spec=User)
        user.id = "alice-uuid-" + str(uuid.uuid4())[:8]
        user.email = "alice@example.com"
        user.username = "alice"
        return user
    
    @pytest.fixture
    def user_bob(self):
        """Mock user Bob for testing."""
        user = MagicMock(spec=User)
        user.id = "bob-uuid-" + str(uuid.uuid4())[:8]
        user.email = "bob@example.com"
        user.username = "bob"
        return user
    
    @pytest.fixture
    def db_session(self):
        """Get database session for test setup."""
        db_config = get_db_config()
        with db_config.get_session() as session:
            yield session
    
    @pytest.fixture
    def setup_test_hierarchy(self, db_session: Session, user_alice: User):
        """Setup project hierarchy owned by user Alice."""
        project = Project(
            id=str(uuid.uuid4()),
            name="Alice's Test Project",
            description="Project owned by Alice",
            user_id=user_alice.id
        )
        db_session.add(project)
        
        git_branch = ProjectGitBranch(
            id=str(uuid.uuid4()),
            project_id=project.id,
            name="feature/alice-authentication",
            description="Alice's feature branch"
        )
        db_session.add(git_branch)
        
        task = Task(
            id=str(uuid.uuid4()),
            title="Alice's Authentication Task",
            description="Task owned by Alice",
            status="todo",
            git_branch_id=git_branch.id,
            user_id=user_alice.id
        )
        db_session.add(task)
        
        db_session.commit()
        
        return {
            "project_id": project.id,
            "git_branch_id": git_branch.id,
            "task_id": task.id,
            "owner_id": user_alice.id
        }
    
    @pytest.fixture
    def facade_factory(self):
        """Create unified context facade factory."""
        return UnifiedContextFacadeFactory()
    
    # Authentication Requirement Tests
    
    def test_context_operations_require_authentication_v1_api(self, client):
        """Test that all v1 context API endpoints require authentication."""
        test_context_id = str(uuid.uuid4())
        
        endpoints_to_test = [
            ("POST", "/api/v1/contexts", {"level": "task", "context_id": test_context_id, "data": {"test": "data"}}),
            ("GET", f"/api/v1/contexts/{test_context_id}", {}),
            ("PUT", f"/api/v1/contexts/{test_context_id}", {"data": {"updated": "data"}}),
            ("DELETE", f"/api/v1/contexts/{test_context_id}", {}),
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
            assert "Unauthorized" in response.text or "Not authenticated" in response.text
    
    def test_context_operations_require_authentication_v2_api(self, client):
        """Test that all v2 context API endpoints require authentication."""
        test_context_id = str(uuid.uuid4())
        
        v2_endpoints_to_test = [
            ("POST", "/api/v2/contexts/task", {"level": "task", "context_id": test_context_id, "data": {"test": "data"}}),
            ("GET", f"/api/v2/contexts/task/{test_context_id}", {}),
            ("PUT", f"/api/v2/contexts/task/{test_context_id}", {"data": {"updated": "data"}}),
            ("DELETE", f"/api/v2/contexts/task/{test_context_id}", {}),
            ("GET", f"/api/v2/contexts/task/{test_context_id}/resolve", {}),
            ("GET", "/api/v2/contexts/task/list", {}),
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
        ]
        
        for method, endpoint, json_data in v2_endpoints_to_test:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json=json_data)
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 401, f"{method} {endpoint} should require authentication"
    
    # User Isolation Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    def test_context_user_isolation_all_levels(self, mock_get_db, mock_get_current_user, 
                                               client, user_alice, user_bob):
        """Test user isolation works across all context levels (global, project, branch, task)."""
        mock_get_db.return_value = MagicMock(spec=Session)
        
        # Test data for each level
        levels_and_data = [
            ("global", f"{GLOBAL_SINGLETON_UUID}_{user_alice.id}", {"autonomous_rules": {"alice_rule": "value"}}),
            ("project", str(uuid.uuid4()), {"project_name": "Alice's Project"}),
            ("branch", str(uuid.uuid4()), {"git_branch_name": "alice-feature"}),
            ("task", str(uuid.uuid4()), {"task_data": {"title": "Alice's Task"}})
        ]
        
        for level, context_id, test_data in levels_and_data:
            # Alice creates context
            mock_get_current_user.return_value = user_alice
            
            with patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade') as mock_get_facade:
                mock_facade = MagicMock()
                mock_facade.create_context.return_value = {
                    "success": True,
                    "context": {"id": context_id, "level": level, "data": test_data}
                }
                mock_facade.get_context.return_value = {
                    "success": True,
                    "context": {"id": context_id, "level": level, "data": test_data}
                }
                mock_get_facade.return_value = mock_facade
                
                # Alice creates context
                create_response = client.post(f"/api/v2/contexts/{level}", json={
                    "level": level,
                    "context_id": context_id,
                    "data": test_data
                })
                assert create_response.status_code == 200
                
                # Alice can access her own context
                get_response = client.get(f"/api/v2/contexts/{level}/{context_id}")
                assert get_response.status_code == 200
                
                # Verify facade was called with Alice's user_id
                mock_get_facade.assert_called_with(user_id=user_alice.id)
            
            # Bob attempts to access Alice's context (should fail)
            mock_get_current_user.return_value = user_bob
            
            with patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade') as mock_get_facade:
                mock_facade = MagicMock()
                mock_facade.get_context.return_value = {
                    "success": False,
                    "error": "Context not found"
                }
                mock_get_facade.return_value = mock_facade
                
                # Bob cannot access Alice's context
                bob_response = client.get(f"/api/v2/contexts/{level}/{context_id}")
                assert bob_response.status_code == 404
                
                # Verify facade was called with Bob's user_id (not Alice's)
                mock_get_facade.assert_called_with(user_id=user_bob.id)
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    def test_context_inheritance_respects_user_boundaries(self, mock_get_db, mock_get_current_user,
                                                          client, user_alice, user_bob, setup_test_hierarchy):
        """Test that context inheritance only works within user boundaries."""
        hierarchy = setup_test_hierarchy
        mock_get_db.return_value = MagicMock(spec=Session)
        
        # Alice (owner) creates contexts at multiple levels
        mock_get_current_user.return_value = user_alice
        
        with patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade') as mock_get_facade:
            mock_facade = MagicMock()
            
            # Mock successful creation and inheritance resolution for Alice
            mock_facade.create_context.return_value = {"success": True, "context": {"id": "test"}}
            mock_facade.resolve_context.return_value = {
                "success": True,
                "resolved_context": {
                    "task": {"task_data": {"title": "Alice's Task"}},
                    "branch": {"git_branch_name": "alice-feature"},
                    "project": {"project_name": "Alice's Project"},
                    "global": {"autonomous_rules": {"alice_rule": "value"}}
                }
            }
            mock_get_facade.return_value = mock_facade
            
            # Alice creates contexts at all levels
            levels_data = [
                ("global", f"{GLOBAL_SINGLETON_UUID}_{user_alice.id}", {"autonomous_rules": {"alice_rule": "value"}}),
                ("project", hierarchy["project_id"], {"project_name": "Alice's Project"}),
                ("branch", hierarchy["git_branch_id"], {"git_branch_name": "alice-feature"}),
                ("task", hierarchy["task_id"], {"task_data": {"title": "Alice's Task"}})
            ]
            
            for level, context_id, data in levels_data:
                create_response = client.post(f"/api/v2/contexts/{level}", json={
                    "level": level,
                    "context_id": context_id,
                    "data": data
                })
                assert create_response.status_code == 200
            
            # Alice can resolve full inheritance chain
            resolve_response = client.get(f"/api/v2/contexts/task/{hierarchy['task_id']}/resolve")
            assert resolve_response.status_code == 200
            
            resolved_data = resolve_response.json()
            assert resolved_data["success"] is True
            assert "task" in str(resolved_data["resolved_context"])
            assert "Alice's Task" in str(resolved_data["resolved_context"])
        
        # Bob attempts to resolve Alice's context inheritance (should fail)
        mock_get_current_user.return_value = user_bob
        
        with patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade') as mock_get_facade:
            mock_facade = MagicMock()
            mock_facade.resolve_context.return_value = {
                "success": False,
                "error": "Context not found"
            }
            mock_get_facade.return_value = mock_facade
            
            # Bob cannot resolve Alice's context
            bob_resolve_response = client.get(f"/api/v2/contexts/task/{hierarchy['task_id']}/resolve")
            assert bob_resolve_response.status_code == 404
            
            # Verify facade was called with Bob's user_id
            mock_get_facade.assert_called_with(user_id=user_bob.id)
    
    # MCP Tools Authentication Integration Tests
    
    def test_mcp_context_tool_uses_authenticated_user_id(self, facade_factory, user_alice):
        """Test that MCP context tools use authenticated user_id."""
        
        # Mock the authentication system
        with patch('fastmcp.task_management.interface.controllers.unified_context_controller.get_authenticated_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = user_alice.id
            
            # Import the MCP controller
            from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
            
            controller = UnifiedContextMCPController(facade_factory)
            
            # Mock the facade factory to track calls
            with patch.object(facade_factory, 'create_facade') as mock_create_facade:
                mock_facade = MagicMock()
                mock_facade.create_context.return_value = {
                    "success": True,
                    "context": {"id": "test-context", "data": {"test": "data"}}
                }
                mock_create_facade.return_value = mock_facade
                
                # Call the manage_context method (simulating MCP tool call)
                result = controller.manage_context(
                    action="create",
                    level="task",
                    context_id="test-context-123",
                    data={"test": "data"}
                )
                
                # Verify that get_authenticated_user_id was called
                mock_get_user_id.assert_called_once()
                
                # Verify that facade was created with authenticated user's ID
                mock_create_facade.assert_called_once()
                call_kwargs = mock_create_facade.call_args[1]
                assert call_kwargs["user_id"] == user_alice.id
                
                # Verify successful result
                assert result["success"] is True
    
    def test_mcp_context_tool_fails_without_authentication(self, facade_factory):
        """Test that MCP context tools fail gracefully without authentication."""
        
        # Mock authentication to return None (unauthenticated)
        with patch('fastmcp.task_management.interface.controllers.unified_context_controller.get_authenticated_user_id') as mock_get_user_id:
            mock_get_user_id.return_value = None
            
            from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
            
            controller = UnifiedContextMCPController(facade_factory)
            
            # Call should fail due to lack of authentication
            result = controller.manage_context(
                action="create",
                level="task",
                context_id="test-context-123",
                data={"test": "data"}
            )
            
            # Verify authentication was checked
            mock_get_user_id.assert_called_once()
            
            # Verify operation failed with authentication error
            assert result["success"] is False
            assert "authentication" in result.get("error", "").lower() or "unauthorized" in result.get("error", "").lower()
    
    # Context Integration with Tasks/Subtasks Tests
    
    def test_context_operations_work_alongside_tasks(self, facade_factory, user_alice, setup_test_hierarchy):
        """Test that context operations work correctly alongside task/subtask operations."""
        hierarchy = setup_test_hierarchy
        
        # Create facade for Alice
        facade = facade_factory.create_facade(
            user_id=user_alice.id,
            project_id=hierarchy["project_id"],
            git_branch_id=hierarchy["git_branch_id"]
        )
        
        # Create task context
        task_context_result = facade.create_context(
            level="task",
            context_id=hierarchy["task_id"],
            data={
                "task_data": {"title": "Authenticated Task", "status": "in_progress"},
                "progress": 50,
                "insights": ["Authentication working correctly"],
                "next_steps": ["Add more tests"]
            }
        )
        assert task_context_result["success"] is True
        
        # Verify context can be retrieved
        get_result = facade.get_context(
            level="task",
            context_id=hierarchy["task_id"]
        )
        assert get_result["success"] is True
        assert get_result["context"]["task_data"]["title"] == "Authenticated Task"
        
        # Update context
        update_result = facade.update_context(
            level="task",
            context_id=hierarchy["task_id"],
            data={
                "task_data": {"title": "Updated Authenticated Task", "status": "completed"},
                "progress": 100,
                "completion_notes": ["All authentication tests passing"]
            }
        )
        assert update_result["success"] is True
        
        # Verify update was applied
        updated_get_result = facade.get_context(
            level="task",
            context_id=hierarchy["task_id"]
        )
        assert updated_get_result["success"] is True
        assert updated_get_result["context"]["task_data"]["title"] == "Updated Authenticated Task"
        assert updated_get_result["context"]["progress"] == 100
    
    # Error Handling Tests
    
    def test_authentication_error_messages_are_user_friendly(self, client):
        """Test that authentication errors provide user-friendly messages."""
        test_endpoints = [
            ("GET", "/api/v2/contexts/task/test-context-123"),
            ("POST", "/api/v2/contexts/task", {"level": "task", "context_id": "test", "data": {}}),
            ("PUT", "/api/v2/contexts/task/test-context-123", {"data": {"updated": True}}),
            ("DELETE", "/api/v2/contexts/task/test-context-123"),
        ]
        
        for method, endpoint, *json_data in test_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=json_data[0])
            elif method == "PUT":
                response = client.put(endpoint, json=json_data[0])
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 401
            
            # Check for user-friendly error messages
            response_text = response.text.lower()
            user_friendly_indicators = ["unauthorized", "authentication", "login", "token"]
            assert any(indicator in response_text for indicator in user_friendly_indicators), \
                f"Response should contain user-friendly authentication error: {response.text}"
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    def test_facade_errors_are_handled_gracefully(self, mock_get_db, mock_get_current_user, client, user_alice):
        """Test that facade errors are handled gracefully with appropriate HTTP status codes."""
        mock_get_current_user.return_value = user_alice
        mock_get_db.return_value = MagicMock(spec=Session)
        
        error_scenarios = [
            ("Context not found", 404),
            ("Validation failed", 400),
            ("Permission denied", 403),
            ("Internal error", 500)
        ]
        
        for error_message, expected_status in error_scenarios:
            with patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade') as mock_get_facade:
                mock_facade = MagicMock()
                mock_facade.get_context.return_value = {
                    "success": False,
                    "error": error_message
                }
                mock_get_facade.return_value = mock_facade
                
                response = client.get("/api/v2/contexts/task/test-context-123")
                
                # Verify appropriate HTTP status code based on error type
                if "not found" in error_message.lower():
                    assert response.status_code == 404
                elif "validation" in error_message.lower():
                    assert response.status_code == 400
                elif "permission" in error_message.lower():
                    assert response.status_code == 403
                else:
                    # Default to 500 for other errors
                    assert response.status_code in [400, 500]
                
                # Verify error message is included in response
                if response.status_code != 500:  # 500 responses might not include detailed errors
                    response_data = response.json()
                    assert error_message in str(response_data)
    
    # Performance and Consistency Tests
    
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_current_user')
    @patch('fastmcp.server.routes.user_scoped_context_routes.get_db')
    def test_authentication_performance_overhead_is_minimal(self, mock_get_db, mock_get_current_user, 
                                                            client, user_alice):
        """Test that authentication doesn't add significant overhead to context operations."""
        mock_get_current_user.return_value = user_alice
        mock_get_db.return_value = MagicMock(spec=Session)
        
        with patch('fastmcp.server.routes.user_scoped_context_routes.get_context_facade') as mock_get_facade:
            mock_facade = MagicMock()
            mock_facade.list_contexts.return_value = {
                "success": True,
                "contexts": [{"id": f"context-{i}", "data": {"test": i}} for i in range(100)]
            }
            mock_get_facade.return_value = mock_facade
            
            import time
            
            # Measure response time for context listing with authentication
            start_time = time.time()
            response = client.get("/api/v2/contexts/task/list")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # Authentication overhead should be minimal (less than 100ms for test)
            assert response_time < 0.1, f"Authentication overhead too high: {response_time}s"
            
            # Verify authentication was performed
            mock_get_current_user.assert_called_once()
            mock_get_facade.assert_called_once_with(user_id=user_alice.id)
    
    def test_context_authentication_consistency_across_api_versions(self, client):
        """Test that authentication requirements are consistent across v1 and v2 APIs."""
        test_context_id = str(uuid.uuid4())
        
        # Test v1 and v2 endpoints for consistency
        api_versions = [
            ("v1", f"/api/v1/contexts/{test_context_id}"),
            ("v2", f"/api/v2/contexts/task/{test_context_id}")
        ]
        
        for version, endpoint in api_versions:
            response = client.get(endpoint)
            
            # Both versions should require authentication
            assert response.status_code == 401, f"API {version} should require authentication"
            
            # Both should have similar error response structure
            assert "401" in response.text or "Unauthorized" in response.text or "Not authenticated" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])