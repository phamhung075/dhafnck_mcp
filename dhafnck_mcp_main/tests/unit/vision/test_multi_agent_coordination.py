"""Unit tests for Multi-Agent Coordination (Phase 4 of Vision System)"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import uuid

from fastmcp.task_management.domain.entities.agent import Agent, AgentStatus, AgentCapability
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus, TaskStatusEnum
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.value_objects.agents import (
    AgentRole, AgentExpertise, AgentCapabilities, AgentProfile, AgentStatus as VOAgentStatus,
    AgentPerformanceMetrics
)
from fastmcp.task_management.domain.value_objects.coordination import (
    CoordinationType, HandoffStatus, ConflictType, ResolutionStrategy,
    CoordinationRequest, WorkAssignment, WorkHandoff, ConflictResolution,
    AgentCommunication
)
from fastmcp.task_management.domain.events.agent_events import (
    AgentAssigned, WorkHandoffRequested, ConflictDetected, AgentStatusBroadcast
)
from fastmcp.task_management.application.services.agent_coordination_service import (
    AgentCoordinationService, CoordinationContext
)
from fastmcp.task_management.application.services.work_distribution_service import (
    WorkDistributionService, DistributionStrategy, TaskRequirements, DistributionPlan
)
from fastmcp.task_management.infrastructure.repositories.sqlite.agent_coordination_repository import (
    AgentCoordinationRepository
)

pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests


class MockTaskRepository:
    """Mock task repository for testing"""
    def __init__(self):
        self.tasks = {}
    
    async def get(self, task_id: str):
        return self.tasks.get(task_id)
    
    async def save(self, task: Task):
        self.tasks[task.id] = task


class MockAgentRepository:
    """Mock agent repository for testing"""
    def __init__(self):
        self.agents = {}
    
    async def get(self, agent_id: str):
        return self.agents.get(agent_id)
    
    async def save(self, agent: Agent):
        self.agents[agent.id] = agent
    
    async def get_all(self):
        return list(self.agents.values())
    
    async def get_by_project(self, project_id: str):
        return [a for a in self.agents.values() if project_id in a.assigned_projects]


class MockEventBus:
    """Mock event bus for testing"""
    def __init__(self):
        self.events = []
    
    async def publish(self, event):
        self.events.append(event)


class TestAgentValueObjects:
    """Test agent-related value objects"""
    
    def test_agent_capabilities(self):
        """Test AgentCapabilities value object"""
        capabilities = AgentCapabilities(
            primary_role=AgentRole.DEVELOPER,
            secondary_roles={AgentRole.REVIEWER, AgentRole.TESTER},
            expertise_areas={AgentExpertise.BACKEND, AgentExpertise.DATABASE},
            skill_levels={"python": 0.9, "javascript": 0.7, "sql": 0.8},
            max_task_complexity=8
        )
        
        # Test role checking
        assert capabilities.can_handle_role(AgentRole.DEVELOPER)
        assert capabilities.can_handle_role(AgentRole.REVIEWER)
        assert not capabilities.can_handle_role(AgentRole.MANAGER)
        
        # Test expertise matching
        required = {AgentExpertise.BACKEND, AgentExpertise.DATABASE}
        assert capabilities.expertise_match_score(required) == 1.0
        
        required_partial = {AgentExpertise.BACKEND, AgentExpertise.FRONTEND}
        assert capabilities.expertise_match_score(required_partial) == 0.5
        
        # Test skill matching
        required_skills = {"python": 0.8, "sql": 0.7}
        assert capabilities.skill_match_score(required_skills) == 1.0
        
        required_high = {"python": 1.0, "rust": 0.5}
        score = capabilities.skill_match_score(required_high)
        assert 0 < score < 1  # Partial match
    
    def test_agent_profile(self):
        """Test AgentProfile value object"""
        capabilities = AgentCapabilities(
            primary_role=AgentRole.DEVELOPER,
            expertise_areas={AgentExpertise.BACKEND}
        )
        
        profile = AgentProfile(
            agent_id="agent-123",
            display_name="Senior Developer",
            capabilities=capabilities,
            availability_score=0.8,
            performance_score=0.9
        )
        
        # Test suitability scoring
        requirements = {
            "role": AgentRole.DEVELOPER,
            "expertise": [AgentExpertise.BACKEND],
            "skills": {}
        }
        
        score = profile.overall_suitability_score(requirements)
        assert score > 0.5  # Should be suitable
        
        # Test unsuitable role
        requirements_wrong = {
            "role": AgentRole.MANAGER,
            "expertise": [],
            "skills": {}
        }
        score_wrong = profile.overall_suitability_score(requirements_wrong)
        assert score_wrong < score  # Should be less suitable
    
    def test_agent_performance_metrics(self):
        """Test AgentPerformanceMetrics value object"""
        metrics = AgentPerformanceMetrics(
            agent_id="agent-123",
            tasks_completed=10,
            tasks_failed=2,
            average_completion_time=4.5,
            quality_score=0.85
        )
        
        # Test success rate
        assert metrics.success_rate == pytest.approx(10/12)
        
        # Test overall score
        score = metrics.overall_performance_score
        assert 0 <= score <= 1
        
        # Test update with task result
        metrics.update_with_task_result(
            success=True,
            completion_time=3.0,
            quality_rating=0.9
        )
        
        assert metrics.tasks_completed == 11
        assert metrics.average_completion_time != 4.5  # Should change
        assert len(metrics.feedback_scores) == 1


class TestCoordinationValueObjects:
    """Test coordination-related value objects"""
    
    def test_coordination_request(self):
        """Test CoordinationRequest value object"""
        request = CoordinationRequest(
            request_id="req-123",
            coordination_type=CoordinationType.HANDOFF,
            requesting_agent_id="agent-1",
            target_agent_id="agent-2",
            task_id="task-123",
            created_at=datetime.now(),
            reason="Switching to testing phase",
            priority="high",
            handoff_notes="All unit tests passing"
        )
        
        # Test expiry
        assert not request.is_expired()
        
        # Test notification format
        notification = request.to_notification()
        assert notification["type"] == "coordination_handoff"
        assert notification["from_agent"] == "agent-1"
        assert notification["priority"] == "high"
    
    def test_work_assignment(self):
        """Test WorkAssignment value object"""
        assignment = WorkAssignment(
            assignment_id="assign-123",
            task_id="task-123",
            assigned_agent_id="agent-1",
            assigned_by_agent_id="manager-1",
            assigned_at=datetime.now(),
            role="developer",
            responsibilities=["Implement API", "Write tests"],
            estimated_hours=8.0,
            due_date=datetime.now() + timedelta(days=2)
        )
        
        # Test overdue check
        assert not assignment.is_overdue()
        
        # Test task context conversion
        context = assignment.to_task_context()
        assert context["assignment"]["role"] == "developer"
        assert len(context["assignment"]["responsibilities"]) == 2
    
    def test_work_handoff(self):
        """Test WorkHandoff value object"""
        handoff = WorkHandoff(
            handoff_id="handoff-123",
            from_agent_id="agent-1",
            to_agent_id="agent-2",
            task_id="task-123",
            initiated_at=datetime.now(),
            work_summary="Core functionality implemented",
            completed_items=["API endpoints", "Database schema"],
            remaining_items=["Integration tests", "Documentation"]
        )
        
        # Test status transitions
        assert handoff.status == HandoffStatus.PENDING
        
        handoff.accept()
        assert handoff.status == HandoffStatus.ACCEPTED
        assert handoff.accepted_at is not None
        
        # Test rejection
        handoff2 = WorkHandoff(
            handoff_id="handoff-456",
            from_agent_id="agent-1",
            to_agent_id="agent-3",
            task_id="task-456",
            initiated_at=datetime.now()
        )
        
        handoff2.reject("Agent unavailable")
        assert handoff2.status == HandoffStatus.REJECTED
        assert handoff2.rejection_reason == "Agent unavailable"
    
    def test_conflict_resolution(self):
        """Test ConflictResolution value object"""
        conflict = ConflictResolution(
            conflict_id="conflict-123",
            conflict_type=ConflictType.CONCURRENT_EDIT,
            involved_agents=["agent-1", "agent-2"],
            task_id="task-123",
            detected_at=datetime.now(),
            description="Both agents modified the same file"
        )
        
        # Test unresolved state
        assert not conflict.is_resolved()
        
        # Test voting
        conflict.add_vote("agent-1", "merge")
        conflict.add_vote("agent-2", "merge")
        conflict.add_vote("agent-3", "override")
        
        votes = conflict.get_vote_summary()
        assert votes["merge"] == 2
        assert votes["override"] == 1
        
        # Test resolution
        conflict.resolve(
            ResolutionStrategy.MERGE,
            "manager-1",
            "Merged both changes preserving all functionality"
        )
        
        assert conflict.is_resolved()
        assert conflict.resolution_strategy == ResolutionStrategy.MERGE


class TestAgentCoordinationService:
    """Test agent coordination service"""
    
    @pytest.fixture
    def setup(self):
        """Setup test dependencies"""
        task_repo = MockTaskRepository()
        agent_repo = MockAgentRepository()
        event_bus = MockEventBus()
        coord_repo = AgentCoordinationRepository()
        
        service = AgentCoordinationService(
            task_repository=task_repo,
            agent_repository=agent_repo,
            event_bus=event_bus,
            coordination_repository=coord_repo
        )
        
        # Create test data
        task_uuid = str(uuid.uuid4())
        task = Task.create(
            id=TaskId(task_uuid),
            title="Implement authentication",
            description="Implement user authentication system",
            status=TaskStatus(TaskStatusEnum.IN_PROGRESS.value)
        )
        task_repo.tasks[task.id.value] = task
        # Also add with original id for lookups
        task_repo.tasks["task-123"] = task
        
        agent1 = Agent.create_agent(
            agent_id="agent-1",
            name="Developer Agent",
            description="Handles development tasks",
            capabilities=[AgentCapability.BACKEND_DEVELOPMENT]
        )
        agent1.max_concurrent_tasks = 3  # Allow multiple concurrent tasks
        agent_repo.agents["agent-1"] = agent1
        
        agent2 = Agent.create_agent(
            agent_id="agent-2",
            name="Tester Agent",
            description="Handles testing tasks",
            capabilities=[AgentCapability.TESTING]
        )
        agent2.max_concurrent_tasks = 3  # Allow multiple concurrent tasks
        agent_repo.agents["agent-2"] = agent2
        
        return service, task_repo, agent_repo, event_bus, coord_repo
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_task(self, setup):
        """Test assigning an agent to a task"""
        service, task_repo, agent_repo, event_bus, coord_repo = setup
        
        # Assign agent
        assignment = await service.assign_agent_to_task(
            task_id="task-123",
            agent_id="agent-1",
            role="developer",
            assigned_by="manager",
            responsibilities=["Implement login", "Add validation"],
            estimated_hours=6.0
        )
        
        # Verify assignment
        assert assignment.task_id == "task-123"
        assert assignment.assigned_agent_id == "agent-1"
        assert assignment.role == "developer"
        assert len(assignment.responsibilities) == 2
        
        # Verify agent state updated
        agent = agent_repo.agents["agent-1"]
        assert "task-123" in agent.active_tasks
        assert agent.current_workload == 1
        
        # Verify event published
        assert len(event_bus.events) == 1
        assert isinstance(event_bus.events[0], AgentAssigned)
    
    @pytest.mark.asyncio
    async def test_request_work_handoff(self, setup):
        """Test requesting work handoff"""
        service, task_repo, agent_repo, event_bus, coord_repo = setup
        
        # Request handoff
        handoff = await service.request_work_handoff(
            from_agent_id="agent-1",
            to_agent_id="agent-2",
            task_id="task-123",
            work_summary="Implementation complete",
            completed_items=["Login endpoint", "User model"],
            remaining_items=["Integration tests", "Edge case testing"],
            handoff_notes="See README for API documentation"
        )
        
        # Verify handoff created
        assert handoff.from_agent_id == "agent-1"
        assert handoff.to_agent_id == "agent-2"
        assert handoff.status == HandoffStatus.PENDING
        assert len(handoff.completed_items) == 2
        
        # Verify event published
        events = [e for e in event_bus.events if isinstance(e, WorkHandoffRequested)]
        assert len(events) == 1
    
    @pytest.mark.asyncio
    async def test_detect_and_resolve_conflict(self, setup):
        """Test conflict detection and resolution"""
        service, task_repo, agent_repo, event_bus, coord_repo = setup
        
        # Detect conflict
        conflict = await service.detect_and_resolve_conflict(
            task_id="task-123",
            conflict_type=ConflictType.CONCURRENT_EDIT,
            involved_agents=["agent-1", "agent-2"],
            description="Both agents modified auth.py",
            resolution_strategy=ResolutionStrategy.MERGE
        )
        
        # Verify conflict created and resolved
        assert conflict.conflict_type == ConflictType.CONCURRENT_EDIT
        assert conflict.is_resolved()
        assert conflict.resolution_strategy == ResolutionStrategy.MERGE
        
        # Verify events published
        detect_events = [e for e in event_bus.events if isinstance(e, ConflictDetected)]
        assert len(detect_events) == 1
    
    @pytest.mark.asyncio
    async def test_get_agent_workload(self, setup):
        """Test getting agent workload"""
        service, task_repo, agent_repo, event_bus, coord_repo = setup
        
        # First assign some work
        await service.assign_agent_to_task(
            task_id="task-123",
            agent_id="agent-1",
            role="developer",
            assigned_by="manager"
        )
        
        # Get workload
        workload = await service.get_agent_workload("agent-1")
        
        assert workload["agent_id"] == "agent-1"
        assert workload["current_tasks"] == 1
        assert workload["workload_percentage"] > 0
        assert workload["can_accept_work"] is True
        assert len(workload["active_assignments"]) == 1
    
    @pytest.mark.asyncio
    async def test_find_best_agent_for_task(self, setup):
        """Test finding best agent for a task"""
        service, task_repo, agent_repo, event_bus, coord_repo = setup
        
        # Find agent for development task
        best_agent = await service.find_best_agent_for_task(
            task_id="task-123",
            required_role=AgentRole.DEVELOPER,
            required_expertise={AgentExpertise.BACKEND}
        )
        
        # Should find agent-1 (developer)
        assert best_agent is not None
        assert best_agent.id == "agent-1"


class TestWorkDistributionService:
    """Test work distribution service"""
    
    @pytest.fixture
    def setup(self):
        """Setup test dependencies"""
        task_repo = MockTaskRepository()
        agent_repo = MockAgentRepository()
        event_bus = MockEventBus()
        
        # Create coordination service
        coord_service = AgentCoordinationService(
            task_repository=task_repo,
            agent_repository=agent_repo,
            event_bus=event_bus
        )
        
        # Create distribution service
        dist_service = WorkDistributionService(
            task_repository=task_repo,
            agent_repository=agent_repo,
            coordination_service=coord_service,
            event_bus=event_bus
        )
        
        # Create test tasks
        for i in range(5):
            task_uuid = str(uuid.uuid4())
            task = Task.create(
                id=TaskId(task_uuid),
                title=f"Task {i}",
                description=f"Test task {i} description",
                status=TaskStatus(TaskStatusEnum.TODO.value),
                priority=Priority("medium" if i < 3 else "high")
            )
            task_repo.tasks[task.id.value] = task
            # Also add with original id for lookups
            task_repo.tasks[f"task-{i}"] = task
        
        # Create test agents
        for i in range(3):
            agent = Agent.create_agent(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                description=f"Test agent {i}",
                capabilities=[AgentCapability.BACKEND_DEVELOPMENT]
            )
            agent.max_concurrent_tasks = 2
            agent_repo.agents[agent.id] = agent
        
        return dist_service, task_repo, agent_repo, event_bus
    
    @pytest.mark.asyncio
    async def test_distribute_round_robin(self, setup):
        """Test round-robin distribution strategy"""
        service, task_repo, agent_repo, event_bus = setup
        
        task_ids = ["task-0", "task-1", "task-2", "task-3", "task-4"]
        
        plan = await service.distribute_tasks(
            task_ids=task_ids,
            strategy=DistributionStrategy.ROUND_ROBIN
        )
        
        # Should distribute evenly
        assert len(plan.assignments) == 5
        assert len(plan.unassignable_tasks) == 0
        
        # Check round-robin pattern
        agents_assigned = [assignment[1] for assignment in plan.assignments]
        assert agents_assigned == ["agent-0", "agent-1", "agent-2", "agent-0", "agent-1"]
    
    @pytest.mark.asyncio
    async def test_distribute_load_balanced(self, setup):
        """Test load-balanced distribution strategy"""
        service, task_repo, agent_repo, event_bus = setup
        
        # Give agent-0 some existing work
        agent_repo.agents["agent-0"].current_workload = 1
        
        task_ids = ["task-0", "task-1", "task-2"]
        
        plan = await service.distribute_tasks(
            task_ids=task_ids,
            strategy=DistributionStrategy.LOAD_BALANCED
        )
        
        # Should prefer less loaded agents
        assert len(plan.assignments) == 3
        agents_assigned = [assignment[1] for assignment in plan.assignments]
        
        # agent-1 and agent-2 should get tasks first
        assert agents_assigned.count("agent-1") >= 1
        assert agents_assigned.count("agent-2") >= 1
    
    @pytest.mark.asyncio
    async def test_distribute_priority_based(self, setup):
        """Test priority-based distribution strategy"""
        service, task_repo, agent_repo, event_bus = setup
        
        # Set different performance scores
        service.agent_performance_cache = {
            "agent-0": 0.9,  # Best performer
            "agent-1": 0.7,
            "agent-2": 0.5
        }
        
        task_ids = ["task-3", "task-4"]  # High priority tasks
        
        plan = await service.distribute_tasks(
            task_ids=task_ids,
            strategy=DistributionStrategy.PRIORITY_BASED
        )
        
        # High priority tasks should go to best performers
        assert len(plan.assignments) == 2
        agents_assigned = [assignment[1] for assignment in plan.assignments]
        
        # agent-0 (best performer) should get assignments
        assert "agent-0" in agents_assigned
    
    @pytest.mark.asyncio
    async def test_task_requirements(self, setup):
        """Test task requirements extraction"""
        service, task_repo, agent_repo, event_bus = setup
        
        # Create task with metadata
        task_uuid = str(uuid.uuid4())
        task = Task.create(
            id=TaskId(task_uuid),
            title="Special task",
            description="Special task requiring specific expertise",
            status=TaskStatus(TaskStatusEnum.TODO.value)
        )
        # Set metadata manually since Task.create doesn't support it directly
        task.metadata = {
            "required_role": "developer",
            "required_expertise": ["backend", "database"],
            "required_skills": {"python": 0.8},
            "preferred_agents": ["agent-0"],
            "estimated_hours": 10.0
        }
        
        requirements = TaskRequirements.from_task(task)
        
        assert requirements.required_role == AgentRole.DEVELOPER
        assert AgentExpertise.BACKEND in requirements.required_expertise
        assert requirements.required_skills["python"] == 0.8
        assert "agent-0" in requirements.preferred_agents
        assert requirements.estimated_hours == 10.0


class TestAgentCoordinationRepository:
    """Test agent coordination repository"""
    
    @pytest.fixture
    def repo(self):
        """Create repository instance"""
        return AgentCoordinationRepository()
    
    @pytest.mark.asyncio
    async def test_coordination_request_operations(self, repo):
        """Test coordination request CRUD operations"""
        # Create request
        request = CoordinationRequest(
            request_id="req-123",
            coordination_type=CoordinationType.HANDOFF,
            requesting_agent_id="agent-1",
            target_agent_id="agent-2",
            task_id="task-123",
            created_at=datetime.now(),
            reason="Phase complete"
        )
        
        # Save and retrieve
        await repo.save_coordination_request(request)
        retrieved = await repo.get_coordination_request("req-123")
        
        assert retrieved is not None
        assert retrieved.request_id == "req-123"
        assert retrieved.coordination_type == CoordinationType.HANDOFF
        
        # Get pending requests
        pending = await repo.get_pending_coordination_requests(agent_id="agent-2")
        assert len(pending) == 1
        assert pending[0].request_id == "req-123"
    
    @pytest.mark.asyncio
    async def test_work_assignment_operations(self, repo):
        """Test work assignment operations"""
        # Create assignments
        assignment1 = WorkAssignment(
            assignment_id="assign-1",
            task_id="task-123",
            assigned_agent_id="agent-1",
            assigned_by_agent_id="manager",
            assigned_at=datetime.now(),
            role="developer"
        )
        
        assignment2 = WorkAssignment(
            assignment_id="assign-2",
            task_id="task-123",
            assigned_agent_id="agent-2",
            assigned_by_agent_id="manager",
            assigned_at=datetime.now(),
            role="reviewer"
        )
        
        # Save
        await repo.save_work_assignment(assignment1)
        await repo.save_work_assignment(assignment2)
        
        # Get by agent
        agent_assignments = await repo.get_agent_assignments("agent-1")
        assert len(agent_assignments) == 1
        assert agent_assignments[0].role == "developer"
        
        # Get by task
        task_assignments = await repo.get_task_assignments("task-123")
        assert len(task_assignments) == 2
    
    @pytest.mark.asyncio
    async def test_coordination_stats(self, repo):
        """Test coordination statistics"""
        # Create some data
        assignment = WorkAssignment(
            assignment_id="assign-1",
            task_id="task-123",
            assigned_agent_id="agent-1",
            assigned_by_agent_id="manager",
            assigned_at=datetime.now(),
            role="developer"
        )
        await repo.save_work_assignment(assignment)
        
        handoff = WorkHandoff(
            handoff_id="handoff-1",
            from_agent_id="agent-1",
            to_agent_id="agent-2",
            task_id="task-123",
            initiated_at=datetime.now()
        )
        await repo.save_handoff(handoff)
        
        # Get stats
        stats = await repo.get_coordination_stats(agent_id="agent-1")
        
        assert stats["total_assignments"] == 1
        assert stats["total_handoffs"] == 1
        assert stats["assignments_by_role"]["developer"] == 1


if __name__ == "__main__":
    pytest.main([__file__])