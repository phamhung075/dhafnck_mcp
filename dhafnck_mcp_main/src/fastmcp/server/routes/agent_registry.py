"""Agent Registry - Dynamic agent registration and metadata management"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from datetime import datetime

class AgentRegistry:
    """Registry for managing agent metadata dynamically"""
    
    # Core agent definitions - can be extended via registration
    DEFAULT_AGENTS = {
        "@uber_orchestrator_agent": {
            "name": "Uber Orchestrator Agent",
            "role": "Master Coordinator",
            "category": "orchestration",
            "priority": "critical",
            "tools": ["*"],  # Access to all tools
            "capabilities": [
                "Multi-agent coordination",
                "Strategic planning",
                "Resource allocation"
            ]
        },
        "@coding_agent": {
            "name": "Coding Agent",
            "role": "Development Specialist",
            "category": "development",
            "priority": "high",
            "tools": ["Edit", "Write", "Read", "Bash", "Git"],
            "capabilities": [
                "Code implementation",
                "Refactoring",
                "API development"
            ]
        },
        "@debugger_agent": {
            "name": "Debugger Agent",
            "role": "Bug Resolution Specialist",
            "category": "development",
            "priority": "high",
            "tools": ["Read", "Grep", "Bash", "Edit"],
            "capabilities": [
                "Error analysis",
                "Performance debugging",
                "Test failure analysis"
            ]
        },
        "@test_orchestrator_agent": {
            "name": "Test Orchestrator Agent",
            "role": "Testing Coordinator",
            "category": "quality",
            "priority": "high",
            "tools": ["Bash", "Read", "Write", "TodoWrite"],
            "capabilities": [
                "Test strategy design",
                "Test suite orchestration",
                "Coverage analysis"
            ]
        },
        "@ui_designer_agent": {
            "name": "UI Designer Agent",
            "role": "Frontend Specialist",
            "category": "frontend",
            "priority": "normal",
            "tools": ["Edit", "Write", "Read", "WebFetch"],
            "capabilities": [
                "Component design",
                "Responsive layouts",
                "State management"
            ]
        },
        "@documentation_agent": {
            "name": "Documentation Agent",
            "role": "Documentation Specialist",
            "category": "documentation",
            "priority": "normal",
            "tools": ["Write", "Read", "Edit"],
            "capabilities": [
                "API documentation",
                "User guides",
                "Technical specifications"
            ]
        },
        "@security_auditor_agent": {
            "name": "Security Auditor Agent",
            "role": "Security Specialist",
            "category": "security",
            "priority": "critical",
            "tools": ["Read", "Grep", "Bash"],
            "capabilities": [
                "Vulnerability scanning",
                "Security best practices",
                "Compliance checking"
            ]
        },
        "@task_planning_agent": {
            "name": "Task Planning Agent",
            "role": "Planning Specialist",
            "category": "planning",
            "priority": "high",
            "tools": ["TodoWrite", "mcp__dhafnck_mcp_http__manage_task"],
            "capabilities": [
                "Task decomposition",
                "Dependency analysis",
                "Timeline estimation"
            ]
        }
    }
    
    def __init__(self, custom_agents_path: Optional[str] = None):
        """Initialize the agent registry"""
        self.agents = self.DEFAULT_AGENTS.copy()
        self.custom_agents_path = custom_agents_path
        
        # Load custom agents if path provided
        if custom_agents_path:
            self.load_custom_agents(custom_agents_path)
    
    def load_custom_agents(self, path: str) -> None:
        """Load custom agent definitions from a JSON file"""
        try:
            config_path = Path(path)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    custom_agents = json.load(f)
                    self.agents.update(custom_agents)
        except Exception as e:
            print(f"Error loading custom agents: {e}")
    
    def register_agent(self, agent_id: str, metadata: Dict[str, Any]) -> bool:
        """Register a new agent or update existing one"""
        try:
            # Ensure agent_id starts with @
            if not agent_id.startswith("@"):
                agent_id = f"@{agent_id}"
            
            # Add timestamp
            metadata["registered_at"] = datetime.now().isoformat()
            
            # Register the agent
            self.agents[agent_id] = metadata
            return True
        except Exception as e:
            print(f"Error registering agent {agent_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific agent"""
        if not agent_id.startswith("@"):
            agent_id = f"@{agent_id}"
        
        agent = self.agents.get(agent_id)
        if agent:
            # Add the ID to the response
            agent_data = agent.copy()
            agent_data["id"] = agent_id
            agent_data["call_name"] = agent_id
            return agent_data
        return None
    
    def list_agents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all agents, optionally filtered by category"""
        agents_list = []
        
        for agent_id, metadata in self.agents.items():
            # Filter by category if specified
            if category and metadata.get("category") != category:
                continue
            
            # Create agent data with ID
            agent_data = metadata.copy()
            agent_data["id"] = agent_id
            agent_data["call_name"] = agent_id
            agents_list.append(agent_data)
        
        return agents_list
    
    def get_categories(self) -> List[str]:
        """Get all unique agent categories"""
        categories = set()
        for metadata in self.agents.values():
            if "category" in metadata:
                categories.add(metadata["category"])
        return sorted(list(categories))
    
    def export_to_claude_format(self, agent_id: str) -> str:
        """Export agent metadata in Claude agent format"""
        agent = self.get_agent(agent_id)
        if not agent:
            return ""
        
        template = f"""# {agent.get('name', 'Unknown Agent')}

## Role
{agent.get('role', 'Specialized AI Agent')}

## Description
{agent.get('description', 'No description available')}

## Capabilities
{self._format_list(agent.get('capabilities', []))}

## Tools Access
{self._format_list(agent.get('tools', ['All available MCP tools']))}

## Category
{agent.get('category', 'general')}

## Priority
{agent.get('priority', 'normal')}

## Usage
```python
mcp__dhafnck_mcp_http__call_agent(name_agent="{agent_id}")
```

## Metadata
- Agent ID: {agent_id}
- Registered: {agent.get('registered_at', 'N/A')}
"""
        return template
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list for markdown output"""
        if not items:
            return "- None specified"
        return "\n".join(f"- {item}" for item in items)
    
    def save_registry(self, path: str) -> bool:
        """Save the current registry to a JSON file"""
        try:
            with open(path, 'w') as f:
                json.dump(self.agents, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving registry: {e}")
            return False

# Global registry instance
_registry = None

def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry

def init_agent_registry(custom_agents_path: Optional[str] = None) -> AgentRegistry:
    """Initialize the global agent registry with optional custom agents"""
    global _registry
    _registry = AgentRegistry(custom_agents_path)
    return _registry