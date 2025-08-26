import pytest
from unittest.mock import Mock, patch, MagicMock
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route
import json

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastmcp.server.routes.agent_metadata_routes import (
    get_agent_metadata,
    get_agent_by_id,
    get_agents_by_category,
    list_agent_categories,
    register_agent_metadata_routes,
    agent_metadata_routes,
    AGENT_METADATA,
    get_agent_categories,
)


class TestAgentMetadataRoutes:
    """Test the agent metadata route handlers."""
    
    @pytest.fixture
    def app(self):
        """Create a test Starlette app with agent metadata routes."""
        app = Starlette(debug=True)
        register_agent_metadata_routes(app)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)
    
    def test_get_agent_metadata_with_registry(self, client):
        """Test GET /api/agents/metadata with agent registry."""
        # Mock the registry
        with patch('fastmcp.server.routes.agent_metadata_routes.get_agent_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = [
                {
                    "id": "@test_agent",
                    "name": "Test Agent",
                    "category": "testing",
                    "description": "A test agent"
                }
            ]
            mock_get_registry.return_value = mock_registry
            
            response = client.get("/api/agents/metadata")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["agents"]) == 1
            assert data["agents"][0]["id"] == "@test_agent"
            assert data["total"] == 1
            assert data["source"] == "registry"
    
    def test_get_agent_metadata_empty_registry_fallback(self, client):
        """Test GET /api/agents/metadata falls back to static metadata when registry is empty."""
        # Mock empty registry
        with patch('fastmcp.server.routes.agent_metadata_routes.get_agent_registry') as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = []
            mock_get_registry.return_value = mock_registry
            
            response = client.get("/api/agents/metadata")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["agents"]) == len(AGENT_METADATA)
            assert data["total"] == len(AGENT_METADATA)
            assert data["source"] == "static"
            
            # Verify some known agents are present
            agent_ids = [agent["id"] for agent in data["agents"]]
            assert "@uber_orchestrator_agent" in agent_ids
            assert "@coding_agent" in agent_ids
            assert "@debugger_agent" in agent_ids
    
    def test_get_agent_metadata_registry_error(self, client):
        """Test GET /api/agents/metadata handles registry errors gracefully."""
        with patch('fastmcp.server.routes.agent_metadata_routes.get_agent_registry') as mock_get_registry:
            mock_get_registry.side_effect = Exception("Registry error")
            
            response = client.get("/api/agents/metadata")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "Registry error" in data["error"]
    
    def test_get_agent_by_id_found(self, client):
        """Test GET /api/agents/metadata/{agent_id} when agent exists."""
        response = client.get("/api/agents/metadata/@coding_agent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"]["id"] == "@coding_agent"
        assert data["agent"]["name"] == "Coding Agent"
        assert data["agent"]["category"] == "development"
    
    def test_get_agent_by_id_not_found(self, client):
        """Test GET /api/agents/metadata/{agent_id} when agent doesn't exist."""
        response = client.get("/api/agents/metadata/@nonexistent_agent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]
    
    def test_get_agent_by_id_error(self, client):
        """Test GET /api/agents/metadata/{agent_id} error handling."""
        # Mock AGENT_METADATA to cause an error
        with patch('fastmcp.server.routes.agent_metadata_routes.AGENT_METADATA', None):
            response = client.get("/api/agents/metadata/@test_agent")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
    
    def test_get_agents_by_category(self, client):
        """Test GET /api/agents/category/{category}."""
        response = client.get("/api/agents/category/development")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["category"] == "development"
        assert len(data["agents"]) > 0
        
        # Verify all returned agents have the correct category
        for agent in data["agents"]:
            assert agent["category"] == "development"
        
        # Check specific agents are in development category
        agent_ids = [agent["id"] for agent in data["agents"]]
        assert "@coding_agent" in agent_ids
        assert "@debugger_agent" in agent_ids
    
    def test_get_agents_by_category_empty(self, client):
        """Test GET /api/agents/category/{category} with no matching agents."""
        response = client.get("/api/agents/category/nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["category"] == "nonexistent"
        assert len(data["agents"]) == 0
        assert data["total"] == 0
    
    def test_get_agents_by_category_error(self, client):
        """Test GET /api/agents/category/{category} error handling."""
        with patch('fastmcp.server.routes.agent_metadata_routes.AGENT_METADATA', None):
            response = client.get("/api/agents/category/development")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
    
    def test_list_agent_categories(self, client):
        """Test GET /api/agents/categories."""
        response = client.get("/api/agents/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0
        
        # Verify known categories are present
        assert "development" in data["categories"]
        assert "orchestration" in data["categories"]
        assert "security" in data["categories"]
        assert "documentation" in data["categories"]
        
        # Verify categories are sorted
        assert data["categories"] == sorted(data["categories"])
    
    def test_list_agent_categories_error(self, client):
        """Test GET /api/agents/categories error handling."""
        with patch('fastmcp.server.routes.agent_metadata_routes.get_agent_categories') as mock_get_categories:
            mock_get_categories.side_effect = Exception("Categories error")
            
            response = client.get("/api/agents/categories")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "Categories error" in data["error"]


class TestAgentCategoriesFunction:
    """Test the get_agent_categories utility function."""
    
    def test_get_agent_categories(self):
        """Test get_agent_categories returns unique sorted categories."""
        categories = get_agent_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        
        # Verify no duplicates
        assert len(categories) == len(set(categories))
        
        # Verify sorted
        assert categories == sorted(categories)
        
        # Verify known categories
        assert "development" in categories
        assert "orchestration" in categories
        assert "security" in categories
    
    def test_get_agent_categories_handles_missing_category(self):
        """Test get_agent_categories handles agents without category field."""
        # Create test data with missing category
        test_agents = [
            {"id": "agent1", "category": "test"},
            {"id": "agent2"},  # Missing category
            {"id": "agent3", "category": "test"},
        ]
        
        with patch('fastmcp.server.routes.agent_metadata_routes.AGENT_METADATA', test_agents):
            categories = get_agent_categories()
            
            assert "test" in categories
            assert "uncategorized" in categories  # Default for missing category


class TestRegisterAgentMetadataRoutes:
    """Test the route registration function."""
    
    def test_register_agent_metadata_routes(self):
        """Test that routes are properly registered with the app."""
        app = Starlette()
        initial_route_count = len(app.routes)
        
        # Register routes
        register_agent_metadata_routes(app)
        
        # Verify routes were added
        assert len(app.routes) == initial_route_count + len(agent_metadata_routes)
        
        # Verify specific routes exist
        paths = [route.path for route in app.routes if hasattr(route, 'path')]
        assert "/api/agents/metadata" in paths
        assert "/api/agents/metadata/{agent_id}" in paths
        assert "/api/agents/category/{category}" in paths
        assert "/api/agents/categories" in paths
    
    @patch('fastmcp.server.routes.agent_metadata_routes.logger')
    def test_register_routes_logs_success(self, mock_logger):
        """Test that route registration logs success."""
        app = Starlette()
        register_agent_metadata_routes(app)
        
        mock_logger.info.assert_called_once_with("Agent metadata routes registered")


class TestAgentMetadataStructure:
    """Test the structure and validity of agent metadata."""
    
    def test_all_agents_have_required_fields(self):
        """Test that all agents have the required fields."""
        required_fields = ["id", "name", "call_name", "role", "description", 
                          "category", "type", "priority", "capabilities", 
                          "tools", "specializations", "guidelines"]
        
        for agent in AGENT_METADATA:
            for field in required_fields:
                assert field in agent, f"Agent {agent.get('id', 'unknown')} missing field: {field}"
    
    def test_agent_ids_are_unique(self):
        """Test that all agent IDs are unique."""
        ids = [agent["id"] for agent in AGENT_METADATA]
        assert len(ids) == len(set(ids)), "Duplicate agent IDs found"
    
    def test_agent_ids_format(self):
        """Test that agent IDs follow the correct format."""
        for agent in AGENT_METADATA:
            assert agent["id"].startswith("@"), f"Agent ID {agent['id']} should start with @"
            assert agent["id"].endswith("_agent"), f"Agent ID {agent['id']} should end with _agent"
    
    def test_agent_priorities_valid(self):
        """Test that agent priorities are valid."""
        valid_priorities = ["critical", "high", "normal", "low"]
        
        for agent in AGENT_METADATA:
            assert agent["priority"] in valid_priorities, \
                f"Agent {agent['id']} has invalid priority: {agent['priority']}"
    
    def test_agent_types_valid(self):
        """Test that agent types are valid."""
        valid_types = ["orchestrator", "specialist"]
        
        for agent in AGENT_METADATA:
            assert agent["type"] in valid_types, \
                f"Agent {agent['id']} has invalid type: {agent['type']}"


class TestAgentMetadataIntegration:
    """Integration tests for agent metadata routes."""
    
    @pytest.fixture
    def full_app(self):
        """Create a full test app with all routes."""
        app = Starlette(debug=True)
        
        # Add a test route to verify app is working
        async def health_check(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"status": "ok"})
        
        app.routes.append(Route("/health", health_check))
        
        # Register agent metadata routes
        register_agent_metadata_routes(app)
        
        return app
    
    def test_full_agent_metadata_flow(self, full_app):
        """Test a complete flow of agent metadata operations."""
        client = TestClient(full_app)
        
        # 1. Get all agents
        response = client.get("/api/agents/metadata")
        assert response.status_code == 200
        all_agents = response.json()["agents"]
        
        # 2. Get categories
        response = client.get("/api/agents/categories")
        assert response.status_code == 200
        categories = response.json()["categories"]
        
        # 3. For each category, get agents
        for category in categories:
            response = client.get(f"/api/agents/category/{category}")
            assert response.status_code == 200
            category_agents = response.json()["agents"]
            
            # Verify all agents in this category are in the full list
            for agent in category_agents:
                assert any(a["id"] == agent["id"] for a in all_agents)
        
        # 4. Get specific agent details
        for agent in all_agents[:3]:  # Test first 3 agents
            response = client.get(f"/api/agents/metadata/{agent['id']}")
            assert response.status_code == 200
            detailed_agent = response.json()["agent"]
            assert detailed_agent["id"] == agent["id"]


if __name__ == "__main__":
    # Run tests when executing the file directly
    pytest.main([__file__, "-v"])