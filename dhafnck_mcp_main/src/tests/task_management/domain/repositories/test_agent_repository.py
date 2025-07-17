"""Unit tests for AgentRepository interface."""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock

from src.fastmcp.task_management.domain.repositories.agent_repository import AgentRepository


class MockAgentRepository(AgentRepository):
    """Mock implementation of AgentRepository for testing."""
    
    def __init__(self):
        # In-memory storage
        self.projects = {}  # project_id -> project data
        self.agents = {}    # project_id -> {agent_id -> agent data}
        self.assignments = {}  # project_id -> {tree_id -> agent_id}
    
    def register_agent(self, project_id: str, agent_id: str, name: str, call_agent: str = None) -> Dict[str, Any]:
        """Register a new agent to a project."""
        # Initialize project storage if needed
        if project_id not in self.agents:
            self.agents[project_id] = {}
            self.assignments[project_id] = {}
        
        # Check if agent already exists
        if agent_id in self.agents[project_id]:
            return {
                "status": "error",
                "message": f"Agent {agent_id} already registered in project {project_id}"
            }
        
        # Register agent
        self.agents[project_id][agent_id] = {
            "id": agent_id,
            "name": name,
            "call_agent": call_agent,
            "assigned_trees": []
        }
        
        return {
            "status": "success",
            "agent": self.agents[project_id][agent_id]
        }
    
    def unregister_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Unregister an agent from a project."""
        if project_id not in self.agents or agent_id not in self.agents[project_id]:
            return {
                "status": "error",
                "message": f"Agent {agent_id} not found in project {project_id}"
            }
        
        # Remove agent assignments
        agent_data = self.agents[project_id][agent_id]
        for tree_id in agent_data["assigned_trees"]:
            if tree_id in self.assignments[project_id]:
                del self.assignments[project_id][tree_id]
        
        # Remove agent
        del self.agents[project_id][agent_id]
        
        return {
            "status": "success",
            "message": f"Agent {agent_id} unregistered from project {project_id}"
        }
    
    def assign_agent_to_tree(self, project_id: str, agent_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Assign an agent to a task tree."""
        if project_id not in self.agents or agent_id not in self.agents[project_id]:
            return {
                "status": "error",
                "message": f"Agent {agent_id} not found in project {project_id}"
            }
        
        # Check if tree is already assigned
        if git_branch_id in self.assignments[project_id]:
            current_agent = self.assignments[project_id][git_branch_id]
            if current_agent != agent_id:
                return {
                    "status": "error",
                    "message": f"Tree {git_branch_id} already assigned to agent {current_agent}"
                }
        
        # Assign agent to tree
        self.assignments[project_id][git_branch_id] = agent_id
        
        # Update agent's assigned trees
        if git_branch_id not in self.agents[project_id][agent_id]["assigned_trees"]:
            self.agents[project_id][agent_id]["assigned_trees"].append(git_branch_id)
        
        return {
            "status": "success",
            "assignment": {
                "agent_id": agent_id,
                "git_branch_id": git_branch_id
            }
        }
    
    def unassign_agent_from_tree(self, project_id: str, agent_id: str, git_branch_id: str = None) -> Dict[str, Any]:
        """Unassign an agent from task tree(s)."""
        if project_id not in self.agents or agent_id not in self.agents[project_id]:
            return {
                "status": "error",
                "message": f"Agent {agent_id} not found in project {project_id}"
            }
        
        agent_data = self.agents[project_id][agent_id]
        trees_unassigned = []
        
        if git_branch_id:
            # Unassign from specific tree
            if git_branch_id in agent_data["assigned_trees"]:
                agent_data["assigned_trees"].remove(git_branch_id)
                if git_branch_id in self.assignments[project_id]:
                    del self.assignments[project_id][git_branch_id]
                trees_unassigned.append(git_branch_id)
        else:
            # Unassign from all trees
            for tree_id in agent_data["assigned_trees"]:
                if tree_id in self.assignments[project_id]:
                    del self.assignments[project_id][tree_id]
                trees_unassigned.append(tree_id)
            agent_data["assigned_trees"] = []
        
        return {
            "status": "success",
            "trees_unassigned": trees_unassigned
        }
    
    def get_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Get agent details."""
        if project_id not in self.agents or agent_id not in self.agents[project_id]:
            return {
                "status": "error",
                "message": f"Agent {agent_id} not found in project {project_id}"
            }
        
        return {
            "status": "success",
            "agent": self.agents[project_id][agent_id]
        }
    
    def list_agents(self, project_id: str) -> Dict[str, Any]:
        """List all agents in a project."""
        if project_id not in self.agents:
            return {
                "status": "success",
                "agents": []
            }
        
        agents_list = list(self.agents[project_id].values())
        return {
            "status": "success",
            "agents": agents_list
        }
    
    def update_agent(self, project_id: str, agent_id: str, name: str = None, call_agent: str = None) -> Dict[str, Any]:
        """Update agent details."""
        if project_id not in self.agents or agent_id not in self.agents[project_id]:
            return {
                "status": "error",
                "message": f"Agent {agent_id} not found in project {project_id}"
            }
        
        agent_data = self.agents[project_id][agent_id]
        
        if name is not None:
            agent_data["name"] = name
        if call_agent is not None:
            agent_data["call_agent"] = call_agent
        
        return {
            "status": "success",
            "agent": agent_data
        }
    
    def rebalance_agents(self, project_id: str) -> Dict[str, Any]:
        """Rebalance agent assignments across task trees."""
        if project_id not in self.agents:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        # Simple rebalancing: distribute trees evenly among agents
        agents = list(self.agents[project_id].keys())
        if not agents:
            return {
                "status": "success",
                "message": "No agents to rebalance"
            }
        
        # Get all assigned trees
        all_trees = []
        for agent_id in agents:
            all_trees.extend(self.agents[project_id][agent_id]["assigned_trees"])
        
        # Clear current assignments
        for agent_id in agents:
            self.agents[project_id][agent_id]["assigned_trees"] = []
        self.assignments[project_id] = {}
        
        # Redistribute trees
        if all_trees:
            trees_per_agent = len(all_trees) // len(agents)
            remainder = len(all_trees) % len(agents)
            
            tree_index = 0
            for i, agent_id in enumerate(agents):
                # Calculate how many trees this agent should get
                num_trees = trees_per_agent + (1 if i < remainder else 0)
                
                # Assign trees
                for _ in range(num_trees):
                    if tree_index < len(all_trees):
                        tree_id = all_trees[tree_index]
                        self.agents[project_id][agent_id]["assigned_trees"].append(tree_id)
                        self.assignments[project_id][tree_id] = agent_id
                        tree_index += 1
        
        return {
            "status": "success",
            "rebalanced_agents": len(agents),
            "rebalanced_trees": len(all_trees)
        }


class TestAgentRepositoryInterface:
    """Test the AgentRepository interface contract."""
    
    def test_repository_implements_all_abstract_methods(self):
        """Test that MockAgentRepository implements all abstract methods."""
        repo = MockAgentRepository()
        
        # Check all abstract methods are implemented
        assert hasattr(repo, 'register_agent')
        assert hasattr(repo, 'unregister_agent')
        assert hasattr(repo, 'assign_agent_to_tree')
        assert hasattr(repo, 'unassign_agent_from_tree')
        assert hasattr(repo, 'get_agent')
        assert hasattr(repo, 'list_agents')
        assert hasattr(repo, 'update_agent')
        assert hasattr(repo, 'rebalance_agents')
    
    def test_repository_is_abstract(self):
        """Test that AgentRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgentRepository()


class TestAgentRegistration:
    """Test agent registration operations."""
    
    def test_register_agent_success(self):
        """Test successful agent registration."""
        repo = MockAgentRepository()
        
        result = repo.register_agent(
            project_id="project-1",
            agent_id="agent-1",
            name="Test Agent",
            call_agent="@test_agent"
        )
        
        assert result["status"] == "success"
        assert result["agent"]["id"] == "agent-1"
        assert result["agent"]["name"] == "Test Agent"
        assert result["agent"]["call_agent"] == "@test_agent"
        assert result["agent"]["assigned_trees"] == []
    
    def test_register_agent_without_call_agent(self):
        """Test registering agent without call_agent parameter."""
        repo = MockAgentRepository()
        
        result = repo.register_agent(
            project_id="project-1",
            agent_id="agent-1",
            name="Test Agent"
        )
        
        assert result["status"] == "success"
        assert result["agent"]["call_agent"] is None
    
    def test_register_duplicate_agent(self):
        """Test registering an agent that already exists."""
        repo = MockAgentRepository()
        
        # Register first time
        repo.register_agent("project-1", "agent-1", "Test Agent")
        
        # Try to register again
        result = repo.register_agent("project-1", "agent-1", "Another Agent")
        
        assert result["status"] == "error"
        assert "already registered" in result["message"]
    
    def test_register_agents_in_different_projects(self):
        """Test registering same agent ID in different projects."""
        repo = MockAgentRepository()
        
        # Register in project 1
        result1 = repo.register_agent("project-1", "agent-1", "Agent in Project 1")
        assert result1["status"] == "success"
        
        # Register same agent ID in project 2
        result2 = repo.register_agent("project-2", "agent-1", "Agent in Project 2")
        assert result2["status"] == "success"
        
        # Verify they are separate
        agent1 = repo.get_agent("project-1", "agent-1")
        agent2 = repo.get_agent("project-2", "agent-1")
        
        assert agent1["agent"]["name"] == "Agent in Project 1"
        assert agent2["agent"]["name"] == "Agent in Project 2"


class TestAgentUnregistration:
    """Test agent unregistration operations."""
    
    def test_unregister_existing_agent(self):
        """Test unregistering an existing agent."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Test Agent")
        
        # Unregister
        result = repo.unregister_agent("project-1", "agent-1")
        
        assert result["status"] == "success"
        assert "unregistered" in result["message"]
        
        # Verify agent is gone
        get_result = repo.get_agent("project-1", "agent-1")
        assert get_result["status"] == "error"
    
    def test_unregister_non_existing_agent(self):
        """Test unregistering a non-existing agent."""
        repo = MockAgentRepository()
        
        result = repo.unregister_agent("project-1", "agent-1")
        
        assert result["status"] == "error"
        assert "not found" in result["message"]
    
    def test_unregister_agent_with_assignments(self):
        """Test unregistering an agent that has tree assignments."""
        repo = MockAgentRepository()
        
        # Register and assign agent
        repo.register_agent("project-1", "agent-1", "Test Agent")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-2")
        
        # Unregister
        result = repo.unregister_agent("project-1", "agent-1")
        
        assert result["status"] == "success"
        
        # Verify assignments are cleaned up
        assert "project-1" not in repo.assignments or len(repo.assignments["project-1"]) == 0


class TestAgentAssignment:
    """Test agent assignment operations."""
    
    def test_assign_agent_to_tree(self):
        """Test assigning an agent to a task tree."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Test Agent")
        
        # Assign to tree
        result = repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        
        assert result["status"] == "success"
        assert result["assignment"]["agent_id"] == "agent-1"
        assert result["assignment"]["git_branch_id"] == "tree-1"
        
        # Verify assignment
        agent = repo.get_agent("project-1", "agent-1")
        assert "tree-1" in agent["agent"]["assigned_trees"]
    
    def test_assign_non_existing_agent(self):
        """Test assigning a non-existing agent."""
        repo = MockAgentRepository()
        
        result = repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        
        assert result["status"] == "error"
        assert "not found" in result["message"]
    
    def test_assign_tree_already_assigned_to_different_agent(self):
        """Test assigning a tree that's already assigned to another agent."""
        repo = MockAgentRepository()
        
        # Register two agents
        repo.register_agent("project-1", "agent-1", "Agent 1")
        repo.register_agent("project-1", "agent-2", "Agent 2")
        
        # Assign tree to agent-1
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        
        # Try to assign same tree to agent-2
        result = repo.assign_agent_to_tree("project-1", "agent-2", "tree-1")
        
        assert result["status"] == "error"
        assert "already assigned" in result["message"]
    
    def test_reassign_tree_to_same_agent(self):
        """Test reassigning a tree to the same agent (should succeed)."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Test Agent")
        
        # Assign tree
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        
        # Reassign to same agent
        result = repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        
        assert result["status"] == "success"


class TestAgentUnassignment:
    """Test agent unassignment operations."""
    
    def test_unassign_agent_from_specific_tree(self):
        """Test unassigning an agent from a specific tree."""
        repo = MockAgentRepository()
        
        # Setup
        repo.register_agent("project-1", "agent-1", "Test Agent")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-2")
        
        # Unassign from tree-1
        result = repo.unassign_agent_from_tree("project-1", "agent-1", "tree-1")
        
        assert result["status"] == "success"
        assert "tree-1" in result["trees_unassigned"]
        
        # Verify agent still assigned to tree-2
        agent = repo.get_agent("project-1", "agent-1")
        assert "tree-1" not in agent["agent"]["assigned_trees"]
        assert "tree-2" in agent["agent"]["assigned_trees"]
    
    def test_unassign_agent_from_all_trees(self):
        """Test unassigning an agent from all trees."""
        repo = MockAgentRepository()
        
        # Setup
        repo.register_agent("project-1", "agent-1", "Test Agent")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-1")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-2")
        repo.assign_agent_to_tree("project-1", "agent-1", "tree-3")
        
        # Unassign from all trees
        result = repo.unassign_agent_from_tree("project-1", "agent-1")
        
        assert result["status"] == "success"
        assert len(result["trees_unassigned"]) == 3
        
        # Verify agent has no assignments
        agent = repo.get_agent("project-1", "agent-1")
        assert len(agent["agent"]["assigned_trees"]) == 0
    
    def test_unassign_non_existing_agent(self):
        """Test unassigning a non-existing agent."""
        repo = MockAgentRepository()
        
        result = repo.unassign_agent_from_tree("project-1", "agent-1", "tree-1")
        
        assert result["status"] == "error"
        assert "not found" in result["message"]


class TestAgentRetrieval:
    """Test agent retrieval operations."""
    
    def test_get_existing_agent(self):
        """Test getting an existing agent."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Test Agent", "@test_agent")
        
        # Get agent
        result = repo.get_agent("project-1", "agent-1")
        
        assert result["status"] == "success"
        assert result["agent"]["id"] == "agent-1"
        assert result["agent"]["name"] == "Test Agent"
        assert result["agent"]["call_agent"] == "@test_agent"
    
    def test_get_non_existing_agent(self):
        """Test getting a non-existing agent."""
        repo = MockAgentRepository()
        
        result = repo.get_agent("project-1", "agent-1")
        
        assert result["status"] == "error"
        assert "not found" in result["message"]
    
    def test_list_agents_empty_project(self):
        """Test listing agents in an empty project."""
        repo = MockAgentRepository()
        
        result = repo.list_agents("project-1")
        
        assert result["status"] == "success"
        assert result["agents"] == []
    
    def test_list_agents_with_multiple_agents(self):
        """Test listing multiple agents in a project."""
        repo = MockAgentRepository()
        
        # Register multiple agents
        repo.register_agent("project-1", "agent-1", "Agent 1")
        repo.register_agent("project-1", "agent-2", "Agent 2")
        repo.register_agent("project-1", "agent-3", "Agent 3")
        
        # List agents
        result = repo.list_agents("project-1")
        
        assert result["status"] == "success"
        assert len(result["agents"]) == 3
        
        agent_names = {agent["name"] for agent in result["agents"]}
        assert agent_names == {"Agent 1", "Agent 2", "Agent 3"}


class TestAgentUpdate:
    """Test agent update operations."""
    
    def test_update_agent_name(self):
        """Test updating agent name."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Original Name")
        
        # Update name
        result = repo.update_agent("project-1", "agent-1", name="New Name")
        
        assert result["status"] == "success"
        assert result["agent"]["name"] == "New Name"
    
    def test_update_agent_call_agent(self):
        """Test updating agent call_agent."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Test Agent")
        
        # Update call_agent
        result = repo.update_agent("project-1", "agent-1", call_agent="@new_agent")
        
        assert result["status"] == "success"
        assert result["agent"]["call_agent"] == "@new_agent"
    
    def test_update_agent_both_fields(self):
        """Test updating both name and call_agent."""
        repo = MockAgentRepository()
        
        # Register agent
        repo.register_agent("project-1", "agent-1", "Original Name", "@original")
        
        # Update both
        result = repo.update_agent(
            "project-1", "agent-1",
            name="New Name",
            call_agent="@new_agent"
        )
        
        assert result["status"] == "success"
        assert result["agent"]["name"] == "New Name"
        assert result["agent"]["call_agent"] == "@new_agent"
    
    def test_update_non_existing_agent(self):
        """Test updating a non-existing agent."""
        repo = MockAgentRepository()
        
        result = repo.update_agent("project-1", "agent-1", name="New Name")
        
        assert result["status"] == "error"
        assert "not found" in result["message"]


class TestAgentRebalancing:
    """Test agent rebalancing operations."""
    
    def test_rebalance_agents_empty_project(self):
        """Test rebalancing with no agents."""
        repo = MockAgentRepository()
        
        # Initialize the project first
        repo.agents["project-1"] = {}
        repo.assignments["project-1"] = {}
        
        result = repo.rebalance_agents("project-1")
        
        assert result["status"] == "success"
        assert result["message"] == "No agents to rebalance"
    
    def test_rebalance_agents_even_distribution(self):
        """Test rebalancing with even distribution."""
        repo = MockAgentRepository()
        
        # Register 3 agents
        repo.register_agent("project-1", "agent-1", "Agent 1")
        repo.register_agent("project-1", "agent-2", "Agent 2")
        repo.register_agent("project-1", "agent-3", "Agent 3")
        
        # Assign all trees to agent-1
        for i in range(6):
            repo.assign_agent_to_tree("project-1", "agent-1", f"tree-{i+1}")
        
        # Rebalance
        result = repo.rebalance_agents("project-1")
        
        assert result["status"] == "success"
        assert result["rebalanced_agents"] == 3
        assert result["rebalanced_trees"] == 6
        
        # Verify even distribution (2 trees per agent)
        for agent_id in ["agent-1", "agent-2", "agent-3"]:
            agent = repo.get_agent("project-1", agent_id)
            assert len(agent["agent"]["assigned_trees"]) == 2
    
    def test_rebalance_agents_uneven_distribution(self):
        """Test rebalancing with uneven distribution."""
        repo = MockAgentRepository()
        
        # Register 3 agents
        repo.register_agent("project-1", "agent-1", "Agent 1")
        repo.register_agent("project-1", "agent-2", "Agent 2")
        repo.register_agent("project-1", "agent-3", "Agent 3")
        
        # Assign 7 trees to agent-1 (not evenly divisible by 3)
        for i in range(7):
            repo.assign_agent_to_tree("project-1", "agent-1", f"tree-{i+1}")
        
        # Rebalance
        result = repo.rebalance_agents("project-1")
        
        assert result["status"] == "success"
        assert result["rebalanced_agents"] == 3
        assert result["rebalanced_trees"] == 7
        
        # Verify distribution (3, 2, 2)
        agents = repo.list_agents("project-1")["agents"]
        tree_counts = sorted([len(agent["assigned_trees"]) for agent in agents], reverse=True)
        assert tree_counts == [3, 2, 2]
    
    def test_rebalance_non_existing_project(self):
        """Test rebalancing a non-existing project."""
        repo = MockAgentRepository()
        
        result = repo.rebalance_agents("non-existent-project")
        
        assert result["status"] == "error"
        assert "not found" in result["message"]


class TestAgentRepositoryIntegration:
    """Test repository integration scenarios."""
    
    def test_complete_agent_lifecycle(self):
        """Test complete agent lifecycle through repository."""
        repo = MockAgentRepository()
        project_id = "test-project"
        agent_id = "test-agent"
        
        # Register agent
        register_result = repo.register_agent(
            project_id,
            agent_id,
            "Test Agent",
            "@test_agent"
        )
        assert register_result["status"] == "success"
        
        # Assign to multiple trees
        for i in range(3):
            assign_result = repo.assign_agent_to_tree(
                project_id,
                agent_id,
                f"tree-{i+1}"
            )
            assert assign_result["status"] == "success"
        
        # Verify assignments
        agent = repo.get_agent(project_id, agent_id)
        assert len(agent["agent"]["assigned_trees"]) == 3
        
        # Update agent
        update_result = repo.update_agent(
            project_id,
            agent_id,
            name="Updated Agent"
        )
        assert update_result["status"] == "success"
        
        # Unassign from one tree
        unassign_result = repo.unassign_agent_from_tree(
            project_id,
            agent_id,
            "tree-2"
        )
        assert unassign_result["status"] == "success"
        
        # List agents
        list_result = repo.list_agents(project_id)
        assert len(list_result["agents"]) == 1
        assert list_result["agents"][0]["name"] == "Updated Agent"
        
        # Unregister agent
        unregister_result = repo.unregister_agent(project_id, agent_id)
        assert unregister_result["status"] == "success"
        
        # Verify agent is gone
        get_result = repo.get_agent(project_id, agent_id)
        assert get_result["status"] == "error"
    
    def test_multi_project_agent_management(self):
        """Test managing agents across multiple projects."""
        repo = MockAgentRepository()
        
        # Register agents in different projects
        repo.register_agent("project-1", "agent-1", "Agent 1 in P1")
        repo.register_agent("project-1", "agent-2", "Agent 2 in P1")
        repo.register_agent("project-2", "agent-1", "Agent 1 in P2")
        repo.register_agent("project-2", "agent-3", "Agent 3 in P2")
        
        # Verify project isolation
        p1_agents = repo.list_agents("project-1")
        p2_agents = repo.list_agents("project-2")
        
        assert len(p1_agents["agents"]) == 2
        assert len(p2_agents["agents"]) == 2
        
        # Agent IDs can be same across projects
        p1_agent1 = repo.get_agent("project-1", "agent-1")
        p2_agent1 = repo.get_agent("project-2", "agent-1")
        
        assert p1_agent1["agent"]["name"] == "Agent 1 in P1"
        assert p2_agent1["agent"]["name"] == "Agent 1 in P2"