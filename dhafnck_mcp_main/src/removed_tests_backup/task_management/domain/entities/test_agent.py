"""Unit tests for Agent entity."""

import pytest
from datetime import datetime
from unittest.mock import patch
from fastmcp.task_management.domain.entities.agent import (
    Agent, AgentStatus, AgentCapability
)


class TestAgentCreation:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent creation with valid and invalid data."""
    
    def test_agent_creation_with_minimal_data(self):
        """Test creating Agent with minimal required data."""
        agent = Agent(
            id="agent-123",
            name="Test Agent"
        )
        
        assert agent.id == "agent-123"
        assert agent.name == "Test Agent"
        assert agent.description == ""
        assert agent.status == AgentStatus.AVAILABLE
        assert agent.max_concurrent_tasks == 1
        assert agent.current_workload == 0
        assert agent.completed_tasks == 0
        assert agent.success_rate == 100.0
        assert len(agent.capabilities) == 0
        assert len(agent.assigned_projects) == 0
        assert len(agent.assigned_trees) == 0
        assert len(agent.active_tasks) == 0
        assert agent.created_at is not None
        assert agent.updated_at is not None
    
    def test_agent_creation_with_full_data(self):
        """Test creating Agent with all optional data."""
        created_time = datetime.now()
        agent = Agent(
            id="agent-456",
            name="Full Agent",
            description="A fully configured agent",
            created_at=created_time,
            updated_at=created_time,
            capabilities={AgentCapability.BACKEND_DEVELOPMENT, AgentCapability.TESTING},
            specializations=["API Development", "Unit Testing"],
            preferred_languages=["Python", "JavaScript"],
            preferred_frameworks=["Django", "React"],
            status=AgentStatus.BUSY,
            max_concurrent_tasks=3,
            current_workload=2,
            work_hours={"start": "09:00", "end": "17:00"},
            timezone="US/Eastern",
            priority_preference="high",
            completed_tasks=10,
            average_task_duration=2.5,
            success_rate=95.0,
            assigned_projects={"project-1", "project-2"},
            assigned_trees={"main", "feature-branch"},
            active_tasks={"task-1", "task-2"}
        )
        
        assert agent.id == "agent-456"
        assert agent.name == "Full Agent"
        assert agent.description == "A fully configured agent"
        assert agent.status == AgentStatus.BUSY
        assert agent.max_concurrent_tasks == 3
        assert agent.current_workload == 2
        assert agent.completed_tasks == 10
        assert agent.success_rate == 95.0
        assert AgentCapability.BACKEND_DEVELOPMENT in agent.capabilities
        assert AgentCapability.TESTING in agent.capabilities
        assert "API Development" in agent.specializations
        assert "Python" in agent.preferred_languages
        assert "Django" in agent.preferred_frameworks
        assert agent.work_hours["start"] == "09:00"
        assert agent.timezone == "US/Eastern"
        assert agent.priority_preference == "high"
        assert agent.average_task_duration == 2.5
        assert "project-1" in agent.assigned_projects
        assert "main" in agent.assigned_trees
        assert "task-1" in agent.active_tasks
    
    def test_agent_post_init_sets_timestamps(self):
        """Test that __post_init__ sets timestamps if not provided."""
        with patch('src.fastmcp.task_management.domain.entities.agent.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            agent = Agent(id="agent-789", name="Timestamp Agent")
            
            assert agent.created_at == mock_now
            assert agent.updated_at == mock_now
    
    def test_agent_factory_method(self):
        """Test create_agent factory method."""
        agent = Agent.create_agent(
            agent_id="factory-agent",
            name="Factory Agent",
            description="Created via factory",
            capabilities=[AgentCapability.FRONTEND_DEVELOPMENT],
            specializations=["React", "Vue"],
            preferred_languages=["TypeScript", "JavaScript"]
        )
        
        assert agent.id == "factory-agent"
        assert agent.name == "Factory Agent"
        assert agent.description == "Created via factory"
        assert AgentCapability.FRONTEND_DEVELOPMENT in agent.capabilities
        assert "React" in agent.specializations
        assert "TypeScript" in agent.preferred_languages
        assert agent.created_at is not None


class TestAgentCapabilities:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent capability management."""
    
    def test_add_capability(self):
        """Test adding capabilities to agent."""
        agent = Agent(id="cap-agent", name="Capability Agent")
        original_updated = agent.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        agent.add_capability(AgentCapability.DEVOPS)
        
        assert AgentCapability.DEVOPS in agent.capabilities
        assert agent.updated_at > original_updated
    
    def test_remove_capability(self):
        """Test removing capabilities from agent."""
        agent = Agent(
            id="cap-agent",
            name="Capability Agent",
            capabilities={AgentCapability.TESTING, AgentCapability.SECURITY}
        )
        
        agent.remove_capability(AgentCapability.TESTING)
        
        assert AgentCapability.TESTING not in agent.capabilities
        assert AgentCapability.SECURITY in agent.capabilities
    
    def test_remove_nonexistent_capability(self):
        """Test removing capability that doesn't exist (should not raise error)."""
        agent = Agent(id="cap-agent", name="Capability Agent")
        
        # Should not raise error
        agent.remove_capability(AgentCapability.ARCHITECTURE)
        
        assert len(agent.capabilities) == 0
    
    def test_has_capability(self):
        """Test checking if agent has specific capability."""
        agent = Agent(
            id="cap-agent",
            name="Capability Agent",
            capabilities={AgentCapability.CODE_REVIEW}
        )
        
        assert agent.has_capability(AgentCapability.CODE_REVIEW) is True
        assert agent.has_capability(AgentCapability.DATA_ANALYSIS) is False
    
    def test_can_handle_task_with_capabilities(self):
        """Test if agent can handle task based on capabilities."""
        agent = Agent(
            id="task-agent",
            name="Task Agent",
            capabilities={AgentCapability.BACKEND_DEVELOPMENT, AgentCapability.TESTING}
        )
        
        # Task requiring backend development
        task_requirements = {
            "capabilities": [AgentCapability.BACKEND_DEVELOPMENT]
        }
        assert agent.can_handle_task(task_requirements) is True
        
        # Task requiring frontend development
        task_requirements = {
            "capabilities": [AgentCapability.FRONTEND_DEVELOPMENT]
        }
        assert agent.can_handle_task(task_requirements) is False
        
        # Task requiring multiple capabilities
        task_requirements = {
            "capabilities": [AgentCapability.BACKEND_DEVELOPMENT, AgentCapability.TESTING]
        }
        assert agent.can_handle_task(task_requirements) is True
        
        # Task requiring capabilities as strings
        task_requirements = {
            "capabilities": ["backend_development"]
        }
        assert agent.can_handle_task(task_requirements) is True
    
    def test_can_handle_task_with_languages(self):
        """Test if agent can handle task based on programming languages."""
        agent = Agent(
            id="lang-agent",
            name="Language Agent",
            preferred_languages=["Python", "Go"]
        )
        
        # Task requiring Python
        task_requirements = {"languages": ["Python"]}
        assert agent.can_handle_task(task_requirements) is True
        
        # Task requiring Java
        task_requirements = {"languages": ["Java"]}
        assert agent.can_handle_task(task_requirements) is False
        
        # Task requiring any of multiple languages
        task_requirements = {"languages": ["Java", "Python", "Ruby"]}
        assert agent.can_handle_task(task_requirements) is True
    
    def test_can_handle_task_with_frameworks(self):
        """Test if agent can handle task based on frameworks."""
        agent = Agent(
            id="fw-agent",
            name="Framework Agent",
            preferred_frameworks=["Django", "FastAPI"]
        )
        
        # Task requiring Django
        task_requirements = {"frameworks": ["Django"]}
        assert agent.can_handle_task(task_requirements) is True
        
        # Task requiring Spring
        task_requirements = {"frameworks": ["Spring"]}
        assert agent.can_handle_task(task_requirements) is False
    
    def test_can_handle_task_with_invalid_capability(self):
        """Test handling task with invalid capability string."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            capabilities={AgentCapability.TESTING}
        )
        
        # Invalid capability should be skipped
        task_requirements = {
            "capabilities": ["invalid_capability", "testing"]
        }
        assert agent.can_handle_task(task_requirements) is True


class TestAgentAssignment:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent assignment to projects and task trees."""
    
    def test_assign_to_project(self):
        """Test assigning agent to project."""
        agent = Agent(id="proj-agent", name="Project Agent")
        original_updated = agent.updated_at
        
        import time
        time.sleep(0.01)
        
        agent.assign_to_project("project-123")
        
        assert "project-123" in agent.assigned_projects
        assert agent.updated_at > original_updated
        
        # Assign to same project again (should not duplicate)
        agent.assign_to_project("project-123")
        assert len(agent.assigned_projects) == 1
    
    def test_assign_to_tree(self):
        """Test assigning agent to task tree."""
        agent = Agent(id="tree-agent", name="Tree Agent")
        
        agent.assign_to_tree("feature-branch")
        
        assert "feature-branch" in agent.assigned_trees
        
        # Assign to multiple trees
        agent.assign_to_tree("hotfix-branch")
        assert len(agent.assigned_trees) == 2
        assert "hotfix-branch" in agent.assigned_trees
    
    def test_unassignment_not_implemented(self):
        """Test that unassignment methods are not implemented (no methods exist)."""
        agent = Agent(
            id="unassign-agent",
            name="Unassign Agent",
            assigned_projects={"project-1"},
            assigned_trees={"branch-1"}
        )
        
        # No unassignment methods exist in the implementation
        # This test documents that limitation
        assert "project-1" in agent.assigned_projects
        assert "branch-1" in agent.assigned_trees
        
        # Direct removal would work but bypasses business logic
        agent.assigned_projects.remove("project-1")
        assert "project-1" not in agent.assigned_projects


class TestAgentTaskManagement:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent task management functionality."""
    
    def test_start_task_when_available(self):
        """Test starting a task when agent is available."""
        agent = Agent(
            id="task-agent",
            name="Task Agent",
            max_concurrent_tasks=2
        )
        
        agent.start_task("task-001")
        
        assert "task-001" in agent.active_tasks
        assert agent.current_workload == 1
        assert agent.status == AgentStatus.AVAILABLE
        
        # Start another task
        agent.start_task("task-002")
        
        assert "task-002" in agent.active_tasks
        assert agent.current_workload == 2
        assert agent.status == AgentStatus.BUSY  # Reached max capacity
    
    def test_start_task_when_not_available(self):
        """Test starting a task when agent is not available."""
        agent = Agent(
            id="busy-agent",
            name="Busy Agent",
            max_concurrent_tasks=1,
            current_workload=1,
            status=AgentStatus.BUSY
        )
        
        with pytest.raises(ValueError, match="not available for new tasks"):
            agent.start_task("task-003")
    
    def test_complete_task_success(self):
        """Test completing a task successfully."""
        agent = Agent(
            id="complete-agent",
            name="Complete Agent",
            active_tasks={"task-001", "task-002"},
            current_workload=2,
            status=AgentStatus.BUSY,
            completed_tasks=5,
            success_rate=90.0,
            max_concurrent_tasks=2  # Need to set this higher than 1
        )
        
        agent.complete_task("task-001", success=True)
        
        assert "task-001" not in agent.active_tasks
        assert agent.current_workload == 1
        assert agent.status == AgentStatus.AVAILABLE  # No longer at capacity
        assert agent.completed_tasks == 6
        assert agent.success_rate > 90.0  # Should increase
    
    def test_complete_task_failure(self):
        """Test completing a task with failure."""
        agent = Agent(
            id="fail-agent",
            name="Fail Agent",
            active_tasks={"task-001"},
            current_workload=1,
            completed_tasks=5,
            success_rate=90.0
        )
        
        agent.complete_task("task-001", success=False)
        
        assert "task-001" not in agent.active_tasks
        assert agent.completed_tasks == 6
        assert agent.success_rate < 90.0  # Should decrease
    
    def test_complete_unassigned_task(self):
        """Test completing a task not assigned to agent."""
        agent = Agent(id="test-agent", name="Test Agent")
        
        with pytest.raises(ValueError, match="not assigned to agent"):
            agent.complete_task("unassigned-task")
    
    def test_is_available(self):
        """Test agent availability check."""
        # Available agent
        agent = Agent(
            id="avail-agent",
            name="Available Agent",
            status=AgentStatus.AVAILABLE,
            max_concurrent_tasks=2,
            current_workload=1
        )
        assert agent.is_available() is True
        
        # Busy agent
        agent.status = AgentStatus.BUSY
        assert agent.is_available() is False
        
        # Available but at capacity
        agent.status = AgentStatus.AVAILABLE
        agent.current_workload = 2
        assert agent.is_available() is False
        
        # Paused agent
        agent.current_workload = 0
        agent.status = AgentStatus.PAUSED
        assert agent.is_available() is False


class TestAgentStateTransitions:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent state transitions."""
    
    def test_pause_and_resume_work(self):
        """Test pausing and resuming agent work."""
        agent = Agent(
            id="pause-agent",
            name="Pause Agent",
            status=AgentStatus.AVAILABLE
        )
        
        # Pause work
        agent.pause_work()
        assert agent.status == AgentStatus.PAUSED
        
        # Resume work - should be available
        agent.resume_work()
        assert agent.status == AgentStatus.AVAILABLE
        
        # Resume when at capacity
        agent.current_workload = agent.max_concurrent_tasks
        agent.pause_work()
        agent.resume_work()
        assert agent.status == AgentStatus.BUSY
    
    def test_go_offline_and_online(self):
        """Test setting agent offline and online."""
        agent = Agent(
            id="offline-agent",
            name="Offline Agent",
            status=AgentStatus.BUSY
        )
        
        # Go offline
        agent.go_offline()
        assert agent.status == AgentStatus.OFFLINE
        
        # Go online
        agent.go_online()
        assert agent.status == AgentStatus.AVAILABLE  # Always available when going online


class TestAgentMetrics:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent metrics and performance tracking."""
    
    def test_get_workload_percentage(self):
        """Test calculating workload percentage."""
        agent = Agent(
            id="metric-agent",
            name="Metric Agent",
            max_concurrent_tasks=4,
            current_workload=2
        )
        
        assert agent.get_workload_percentage() == 50.0
        
        # Full capacity
        agent.current_workload = 4
        assert agent.get_workload_percentage() == 100.0
        
        # No capacity (edge case)
        agent.max_concurrent_tasks = 0
        assert agent.get_workload_percentage() == 100.0
    
    def test_calculate_task_suitability_score(self):
        """Test calculating task suitability score."""
        agent = Agent(
            id="suit-agent",
            name="Suitability Agent",
            capabilities={AgentCapability.BACKEND_DEVELOPMENT},
            status=AgentStatus.AVAILABLE,
            max_concurrent_tasks=2,
            current_workload=0,
            success_rate=90.0,
            priority_preference="high"
        )
        
        # Perfect match
        task_requirements = {
            "capabilities": [AgentCapability.BACKEND_DEVELOPMENT],
            "priority": "high"
        }
        score = agent.calculate_task_suitability_score(task_requirements)
        assert score > 80.0  # High score for good match
        
        # Cannot handle task
        task_requirements = {
            "capabilities": [AgentCapability.FRONTEND_DEVELOPMENT]
        }
        score = agent.calculate_task_suitability_score(task_requirements)
        assert score == 0.0
        
        # Partial match (different priority)
        task_requirements = {
            "capabilities": [AgentCapability.BACKEND_DEVELOPMENT],
            "priority": "low"
        }
        score = agent.calculate_task_suitability_score(task_requirements)
        assert 70.0 < score < 90.0  # Still high score, just no priority bonus
    
    def test_get_agent_profile(self):
        """Test getting comprehensive agent profile."""
        agent = Agent(
            id="profile-agent",
            name="Profile Agent",
            description="Test profile",
            capabilities={AgentCapability.TESTING},
            specializations=["Unit Testing"],
            preferred_languages=["Python"],
            preferred_frameworks=["pytest"],
            status=AgentStatus.AVAILABLE,
            max_concurrent_tasks=2,
            current_workload=1,
            completed_tasks=10,
            success_rate=95.0,
            average_task_duration=1.5,
            assigned_projects={"proj-1"},
            assigned_trees={"main"},
            active_tasks={"task-1"},
            work_hours={"start": "09:00", "end": "17:00"},
            timezone="UTC",
            priority_preference="high"
        )
        
        profile = agent.get_agent_profile()
        
        assert profile["id"] == "profile-agent"
        assert profile["name"] == "Profile Agent"
        assert profile["description"] == "Test profile"
        assert profile["status"] == "available"
        assert "testing" in profile["capabilities"]
        assert "Unit Testing" in profile["specializations"]
        assert "Python" in profile["preferred_languages"]
        assert "pytest" in profile["preferred_frameworks"]
        
        assert profile["workload"]["current"] == 1
        assert profile["workload"]["max"] == 2
        assert profile["workload"]["percentage"] == 50.0
        assert profile["workload"]["available"] is True
        
        assert profile["performance"]["completed_tasks"] == 10
        assert profile["performance"]["success_rate"] == 95.0
        assert profile["performance"]["average_duration"] == 1.5
        
        assert "proj-1" in profile["assignments"]["projects"]
        assert "main" in profile["assignments"]["trees"]
        assert "task-1" in profile["assignments"]["active_tasks"]
        
        assert profile["preferences"]["work_hours"]["start"] == "09:00"
        assert profile["preferences"]["timezone"] == "UTC"
        assert profile["preferences"]["priority_preference"] == "high"
        
        assert "created_at" in profile
        assert "updated_at" in profile


class TestAgentEqualityAndHashing:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test Agent equality and hashing behavior."""
    
    def test_agent_equality_by_id(self):
        """Test that agents are compared by identity (default object behavior)."""
        agent1 = Agent(id="agent-123", name="Agent One")
        agent2 = Agent(id="agent-123", name="Agent One")
        agent3 = agent1
        
        # Different instances with same ID are not equal (default object behavior)
        assert agent1 != agent2
        
        # Same instance is equal
        assert agent1 == agent3
    
    def test_agent_hashing(self):
        """Test that agents cannot be used in sets/dicts by default (not hashable)."""
        agent1 = Agent(id="agent-1", name="Agent 1")
        agent2 = Agent(id="agent-2", name="Agent 2")
        
        # Agent is not hashable by default (uses @dataclass without frozen=True)
        with pytest.raises(TypeError, match="unhashable type"):
            agent_set = {agent1, agent2}
        
        with pytest.raises(TypeError, match="unhashable type"):
            agent_dict = {agent1: "First"}


class TestAgentEdgeCases:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test edge cases and error scenarios."""
    
    def test_success_rate_calculation(self):
        """Test success rate calculation with weighted average."""
        agent = Agent(
            id="rate-agent",
            name="Rate Agent",
            success_rate=80.0,
            active_tasks={"task-1"}
        )
        
        # Complete with success - should increase
        original_rate = agent.success_rate
        agent.complete_task("task-1", success=True)
        # New rate = (80.0 * 0.9) + (100.0 * 0.1) = 72 + 10 = 82
        assert agent.success_rate == pytest.approx(82.0)
        
        # Complete with failure - should decrease
        agent.active_tasks.add("task-2")
        agent.complete_task("task-2", success=False)
        # New rate = (82.0 * 0.9) + (0.0 * 0.1) = 73.8 + 0 = 73.8
        assert agent.success_rate == pytest.approx(73.8)
    
    def test_current_workload_never_negative(self):
        """Test that current workload never goes negative."""
        agent = Agent(
            id="workload-agent",
            name="Workload Agent",
            current_workload=1,
            active_tasks={"task-1"}
        )
        
        agent.complete_task("task-1")
        assert agent.current_workload == 0
        
        # Even if we somehow have workload 0 and complete a task
        agent.active_tasks.add("task-2")
        agent.current_workload = 0
        agent.complete_task("task-2")
        assert agent.current_workload == 0  # Should not go negative
    
    def test_empty_requirements_can_handle_task(self):
        """Test that agent can handle task with no requirements."""
        agent = Agent(id="empty-req-agent", name="Empty Req Agent")
        
        # Empty requirements
        assert agent.can_handle_task({}) is True
        
        # No capability requirements
        assert agent.can_handle_task({"capabilities": []}) is True
        
        # No language requirements
        assert agent.can_handle_task({"languages": []}) is True
        
        # No framework requirements
        assert agent.can_handle_task({"frameworks": []}) is True


class TestAgentIntegration:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Integration tests for Agent entity."""
    
    def test_full_agent_lifecycle(self):
        """Test complete agent lifecycle from creation to task completion."""
        # Create agent
        agent = Agent.create_agent(
            agent_id="lifecycle-agent",
            name="Lifecycle Agent",
            description="Testing full lifecycle",
            capabilities=[AgentCapability.BACKEND_DEVELOPMENT, AgentCapability.TESTING],
            specializations=["API Development"],
            preferred_languages=["Python"]
        )
        
        # Assign to project and tree
        agent.assign_to_project("proj-123")
        agent.assign_to_tree("main")
        
        # Check initial state
        assert agent.is_available()
        assert agent.get_workload_percentage() == 0.0
        
        # Start tasks
        agent.start_task("task-1")
        assert agent.current_workload == 1
        assert agent.status == AgentStatus.BUSY  # At capacity with max_concurrent_tasks=1
        
        # Try to start another task (should fail)
        with pytest.raises(ValueError):
            agent.start_task("task-2")
        
        # Complete task successfully
        agent.complete_task("task-1", success=True)
        assert agent.current_workload == 0
        assert agent.status == AgentStatus.AVAILABLE
        assert agent.completed_tasks == 1
        assert agent.success_rate == 100.0
        
        # Pause agent
        agent.pause_work()
        assert agent.status == AgentStatus.PAUSED
        assert not agent.is_available()
        
        # Resume work
        agent.resume_work()
        assert agent.status == AgentStatus.AVAILABLE
        
        # Go offline
        agent.go_offline()
        assert agent.status == AgentStatus.OFFLINE
        
        # Get final profile
        profile = agent.get_agent_profile()
        assert profile["performance"]["completed_tasks"] == 1
        assert profile["assignments"]["projects"] == ["proj-123"]
        assert profile["assignments"]["trees"] == ["main"]
        assert len(profile["assignments"]["active_tasks"]) == 0