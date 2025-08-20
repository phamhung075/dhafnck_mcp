import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastmcp.server.routes.agent_registry import (
    AgentRegistry,
    get_agent_registry,
    init_agent_registry,
)


class TestAgentRegistry:
    """Test the AgentRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create a fresh registry instance."""
        return AgentRegistry()
    
    @pytest.fixture
    def custom_agents_data(self):
        """Sample custom agents data."""
        return {
            "@custom_agent": {
                "name": "Custom Agent",
                "role": "Custom Specialist",
                "category": "custom",
                "priority": "normal",
                "tools": ["Read", "Write"],
                "capabilities": ["Custom task handling"]
            }
        }
    
    def test_init_with_defaults(self, registry):
        """Test registry initializes with default agents."""
        assert len(registry.agents) == len(AgentRegistry.DEFAULT_AGENTS)
        assert "@uber_orchestrator_agent" in registry.agents
        assert "@coding_agent" in registry.agents
        assert "@debugger_agent" in registry.agents
    
    def test_init_with_custom_agents_file(self, custom_agents_data):
        """Test registry loads custom agents from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_agents_data, f)
            temp_path = f.name
        
        try:
            registry = AgentRegistry(custom_agents_path=temp_path)
            
            # Should have default agents plus custom ones
            assert len(registry.agents) > len(AgentRegistry.DEFAULT_AGENTS)
            assert "@custom_agent" in registry.agents
            assert registry.agents["@custom_agent"]["name"] == "Custom Agent"
        finally:
            os.unlink(temp_path)
    
    def test_load_custom_agents_file_not_found(self, registry):
        """Test loading custom agents handles missing file gracefully."""
        registry.load_custom_agents("/nonexistent/path.json")
        # Should still have default agents
        assert len(registry.agents) == len(AgentRegistry.DEFAULT_AGENTS)
    
    def test_load_custom_agents_invalid_json(self, registry):
        """Test loading custom agents handles invalid JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            registry.load_custom_agents(temp_path)
            # Should still have default agents
            assert len(registry.agents) == len(AgentRegistry.DEFAULT_AGENTS)
        finally:
            os.unlink(temp_path)
    
    def test_register_agent_new(self, registry):
        """Test registering a new agent."""
        metadata = {
            "name": "New Agent",
            "role": "New Role",
            "category": "testing",
            "priority": "low"
        }
        
        result = registry.register_agent("new_agent", metadata)
        
        assert result is True
        assert "@new_agent" in registry.agents
        assert registry.agents["@new_agent"]["name"] == "New Agent"
        assert "registered_at" in registry.agents["@new_agent"]
    
    def test_register_agent_with_at_prefix(self, registry):
        """Test registering agent with @ prefix already included."""
        metadata = {"name": "Test Agent"}
        
        result = registry.register_agent("@test_agent", metadata)
        
        assert result is True
        assert "@test_agent" in registry.agents
        assert "@@test_agent" not in registry.agents  # Should not double prefix
    
    def test_register_agent_update_existing(self, registry):
        """Test updating an existing agent."""
        # Register initial agent
        initial_metadata = {"name": "Initial Name", "role": "Initial Role"}
        registry.register_agent("test_agent", initial_metadata)
        
        # Update the agent
        updated_metadata = {"name": "Updated Name", "role": "Updated Role"}
        result = registry.register_agent("test_agent", updated_metadata)
        
        assert result is True
        assert registry.agents["@test_agent"]["name"] == "Updated Name"
        assert registry.agents["@test_agent"]["role"] == "Updated Role"
    
    def test_register_agent_error_handling(self, registry):
        """Test register_agent handles errors gracefully."""
        # Mock datetime to raise an exception
        with patch('fastmcp.server.routes.agent_registry.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Time error")
            
            result = registry.register_agent("error_agent", {"name": "Error"})
            
            assert result is False
    
    def test_get_agent_existing(self, registry):
        """Test getting an existing agent."""
        agent = registry.get_agent("coding_agent")
        
        assert agent is not None
        assert agent["id"] == "@coding_agent"
        assert agent["call_name"] == "@coding_agent"
        assert agent["name"] == "Coding Agent"
        assert agent["category"] == "development"
    
    def test_get_agent_with_at_prefix(self, registry):
        """Test getting agent with @ prefix."""
        agent = registry.get_agent("@debugger_agent")
        
        assert agent is not None
        assert agent["id"] == "@debugger_agent"
        assert agent["name"] == "Debugger Agent"
    
    def test_get_agent_not_found(self, registry):
        """Test getting a non-existent agent."""
        agent = registry.get_agent("nonexistent_agent")
        assert agent is None
    
    def test_list_agents_all(self, registry):
        """Test listing all agents."""
        agents = registry.list_agents()
        
        assert len(agents) == len(AgentRegistry.DEFAULT_AGENTS)
        
        # Verify all have required fields
        for agent in agents:
            assert "id" in agent
            assert "call_name" in agent
            assert agent["id"].startswith("@")
            assert agent["id"] == agent["call_name"]
    
    def test_list_agents_by_category(self, registry):
        """Test listing agents filtered by category."""
        dev_agents = registry.list_agents(category="development")
        
        assert len(dev_agents) > 0
        for agent in dev_agents:
            assert agent["category"] == "development"
        
        # Verify specific agents are included
        agent_ids = [agent["id"] for agent in dev_agents]
        assert "@coding_agent" in agent_ids
        assert "@debugger_agent" in agent_ids
    
    def test_list_agents_empty_category(self, registry):
        """Test listing agents with non-existent category."""
        agents = registry.list_agents(category="nonexistent")
        assert len(agents) == 0
    
    def test_get_categories(self, registry):
        """Test getting all unique categories."""
        categories = registry.get_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert categories == sorted(categories)  # Should be sorted
        
        # Verify known categories
        assert "development" in categories
        assert "orchestration" in categories
        assert "security" in categories
        assert "documentation" in categories
    
    def test_export_to_claude_format(self, registry):
        """Test exporting agent to Claude format."""
        export = registry.export_to_claude_format("@coding_agent")
        
        assert "# Coding Agent" in export
        assert "## Role" in export
        assert "Development Specialist" in export
        assert "## Capabilities" in export
        assert "Code implementation" in export
        assert "## Tools Access" in export
        assert 'mcp__dhafnck_mcp_http__call_agent(name_agent="@coding_agent")' in export
    
    def test_export_to_claude_format_not_found(self, registry):
        """Test exporting non-existent agent."""
        export = registry.export_to_claude_format("@nonexistent")
        assert export == ""
    
    def test_export_to_claude_format_minimal_agent(self, registry):
        """Test exporting agent with minimal metadata."""
        registry.register_agent("minimal", {})
        export = registry.export_to_claude_format("@minimal")
        
        assert "# Unknown Agent" in export
        assert "Specialized AI Agent" in export
        assert "No description available" in export
        assert "- None specified" in export  # For empty lists
    
    def test_format_list_empty(self, registry):
        """Test _format_list with empty list."""
        result = registry._format_list([])
        assert result == "- None specified"
    
    def test_format_list_with_items(self, registry):
        """Test _format_list with items."""
        items = ["Item 1", "Item 2", "Item 3"]
        result = registry._format_list(items)
        
        assert result == "- Item 1\n- Item 2\n- Item 3"
    
    def test_save_registry_success(self, registry):
        """Test saving registry to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Add a custom agent
            registry.register_agent("save_test", {"name": "Save Test"})
            
            result = registry.save_registry(temp_path)
            assert result is True
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert "@save_test" in saved_data
            assert saved_data["@save_test"]["name"] == "Save Test"
        finally:
            os.unlink(temp_path)
    
    def test_save_registry_error(self, registry):
        """Test save_registry handles errors gracefully."""
        # Try to save to an invalid path
        result = registry.save_registry("/invalid/path/file.json")
        assert result is False


class TestAgentRegistryGlobalFunctions:
    """Test global registry functions."""
    
    def test_get_agent_registry_singleton(self):
        """Test get_agent_registry returns singleton instance."""
        # Reset global registry
        import fastmcp.server.routes.agent_registry
        fastmcp.server.routes.agent_registry._registry = None
        
        registry1 = get_agent_registry()
        registry2 = get_agent_registry()
        
        assert registry1 is registry2
    
    def test_init_agent_registry(self):
        """Test init_agent_registry creates new instance."""
        # Reset global registry
        import fastmcp.server.routes.agent_registry
        fastmcp.server.routes.agent_registry._registry = None
        
        registry1 = get_agent_registry()
        registry2 = init_agent_registry()
        
        assert registry1 is not registry2
        
        # Verify the new registry is now the global one
        registry3 = get_agent_registry()
        assert registry2 is registry3
    
    def test_init_agent_registry_with_custom_path(self, custom_agents_data):
        """Test init_agent_registry with custom agents path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_agents_data, f)
            temp_path = f.name
        
        try:
            registry = init_agent_registry(custom_agents_path=temp_path)
            
            assert "@custom_agent" in registry.agents
            assert registry.agents["@custom_agent"]["name"] == "Custom Agent"
        finally:
            os.unlink(temp_path)


class TestAgentRegistryDefaultAgents:
    """Test the default agent configurations."""
    
    def test_all_default_agents_have_required_fields(self):
        """Test that all default agents have required fields."""
        required_fields = ["name", "role", "category", "priority", "tools", "capabilities"]
        
        for agent_id, metadata in AgentRegistry.DEFAULT_AGENTS.items():
            for field in required_fields:
                assert field in metadata, f"Agent {agent_id} missing field: {field}"
    
    def test_default_agent_ids_format(self):
        """Test default agent IDs follow correct format."""
        for agent_id in AgentRegistry.DEFAULT_AGENTS.keys():
            assert agent_id.startswith("@"), f"Agent ID {agent_id} should start with @"
            assert agent_id.endswith("_agent"), f"Agent ID {agent_id} should end with _agent"
    
    def test_default_agent_priorities_valid(self):
        """Test default agent priorities are valid."""
        valid_priorities = ["critical", "high", "normal", "low"]
        
        for agent_id, metadata in AgentRegistry.DEFAULT_AGENTS.items():
            assert metadata["priority"] in valid_priorities, \
                f"Agent {agent_id} has invalid priority: {metadata['priority']}"
    
    def test_uber_orchestrator_has_all_tools(self):
        """Test uber orchestrator has access to all tools."""
        uber = AgentRegistry.DEFAULT_AGENTS["@uber_orchestrator_agent"]
        assert uber["tools"] == ["*"]
    
    def test_agent_tool_lists_valid(self):
        """Test agent tool lists contain valid tool names."""
        # These are some known valid tool names
        valid_tools = ["Read", "Write", "Edit", "Bash", "Git", "Grep", 
                      "TodoWrite", "WebFetch", "mcp__dhafnck_mcp_http__manage_task"]
        
        for agent_id, metadata in AgentRegistry.DEFAULT_AGENTS.items():
            if metadata["tools"] != ["*"]:  # Skip uber orchestrator
                for tool in metadata["tools"]:
                    # Tool should either be a known tool or start with mcp__
                    assert tool in valid_tools or tool.startswith("mcp__"), \
                        f"Agent {agent_id} has unknown tool: {tool}"


class TestAgentRegistryIntegration:
    """Integration tests for the agent registry."""
    
    def test_full_agent_lifecycle(self):
        """Test complete agent lifecycle: create, update, export, save."""
        registry = AgentRegistry()
        
        # 1. Register a new agent
        metadata = {
            "name": "Integration Test Agent",
            "role": "Test Specialist",
            "category": "testing",
            "priority": "high",
            "tools": ["Read", "Write", "Test"],
            "capabilities": ["Integration testing", "End-to-end testing"],
            "description": "Handles integration test scenarios"
        }
        
        assert registry.register_agent("integration_agent", metadata) is True
        
        # 2. Retrieve and verify
        agent = registry.get_agent("integration_agent")
        assert agent is not None
        assert agent["name"] == "Integration Test Agent"
        assert "registered_at" in agent
        
        # 3. Update the agent
        updated_metadata = metadata.copy()
        updated_metadata["priority"] = "critical"
        updated_metadata["capabilities"].append("Performance testing")
        
        assert registry.register_agent("integration_agent", updated_metadata) is True
        
        # 4. Verify update
        updated_agent = registry.get_agent("integration_agent")
        assert updated_agent["priority"] == "critical"
        assert "Performance testing" in updated_agent["capabilities"]
        
        # 5. List agents in category
        test_agents = registry.list_agents(category="testing")
        assert any(a["id"] == "@integration_agent" for a in test_agents)
        
        # 6. Export to Claude format
        export = registry.export_to_claude_format("@integration_agent")
        assert "Integration Test Agent" in export
        assert "Test Specialist" in export
        assert "Performance testing" in export
        
        # 7. Save registry
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            assert registry.save_registry(temp_path) is True
            
            # 8. Load in new registry instance
            new_registry = AgentRegistry(custom_agents_path=temp_path)
            loaded_agent = new_registry.get_agent("integration_agent")
            
            assert loaded_agent is not None
            assert loaded_agent["name"] == "Integration Test Agent"
            assert loaded_agent["priority"] == "critical"
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    # Run tests when executing the file directly
    pytest.main([__file__, "-v"])