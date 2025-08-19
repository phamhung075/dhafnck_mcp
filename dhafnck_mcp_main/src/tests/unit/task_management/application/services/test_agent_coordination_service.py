"""
Unit tests for Agent Coordination Service

Tests multi-agent task management, handoffs, conflict resolution, and workload balancing.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from fastmcp.task_management.application.services.agent_coordination_service import (
    AgentCoordinationService, AgentCoordinationException, CoordinationContext
)
from fastmcp.task_management.domain.entities.agent import Agent, AgentStatus as EntityAgentStatus
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.agents import (
    AgentProfile, AgentCapabilities, AgentRole, AgentExpertise, AgentStatus
)
from fastmcp.task_management.domain.value_objects.coordination import (
    CoordinationType, CoordinationRequest, WorkAssignment, WorkHandoff,
    HandoffStatus, ConflictResolution, ConflictType, ResolutionStrategy,
    AgentCommunication
)


class TestAgentCoordinationService:
    """Test cases for AgentCoordinationService"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        repo = Mock()
        repo.get = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_agent_repository(self):
        """Create a mock agent repository"""
        repo = Mock()
        repo.get = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_project = AsyncMock()
        repo.get_all = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus"""
        bus = Mock()
        bus.publish = AsyncMock()
        return bus
    
    @pytest.fixture
    def service(self, mock_task_repository, mock_agent_repository, mock_event_bus):
        """Create service instance with mocks"""
        return AgentCoordinationService(
            task_repository=mock_task_repository,
            agent_repository=mock_agent_repository,
            event_bus=mock_event_bus,
            user_id="test_user"
        )
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task"""
        task = Mock(spec=Task)
        task.id = "task123"
        task.title = "Test Task"
        return task
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent"""
        agent = Mock(spec=Agent)
        agent.id = "agent123"
        agent.name = "Test Agent"
        agent.active_tasks = set()
        agent.max_concurrent_tasks = 5
        agent.success_rate = 95.0
        agent.is_available = Mock(return_value=True)
        agent.start_task = Mock()
        agent.get_workload_percentage = Mock(return_value=60.0)
        return agent
    
    def test_init(self, mock_task_repository, mock_agent_repository, mock_event_bus):
        """Test service initialization"""
        user_id = "test_user"
        service = AgentCoordinationService(
            task_repository=mock_task_repository,
            agent_repository=mock_agent_repository,
            event_bus=mock_event_bus,
            user_id=user_id
        )
        
        assert service.task_repository == mock_task_repository
        assert service.agent_repository == mock_agent_repository
        assert service.event_bus == mock_event_bus
        assert service._user_id == user_id
        assert service.coordination_requests == {}
        assert service.work_assignments == {}
        assert service.handoffs == {}
        assert service.conflicts == {}
        assert service.communications == []
    
    def test_with_user(self, service):
        """Test creating user-scoped service"""
        new_user_id = "new_user"
        new_service = service.with_user(new_user_id)
        
        assert isinstance(new_service, AgentCoordinationService)
        assert new_service._user_id == new_user_id
        assert new_service.task_repository == service.task_repository
        assert new_service.agent_repository == service.agent_repository
        assert new_service.event_bus == service.event_bus
    
    def test_get_user_scoped_repository_with_user_method(self, service):
        """Test getting user-scoped repository with with_user method"""
        # Mock repository with with_user method
        repo = Mock()
        repo.with_user = Mock(return_value="scoped_repo")
        
        result = service._get_user_scoped_repository(repo)
        
        repo.with_user.assert_called_once_with("test_user")
        assert result == "scoped_repo"
    
    def test_get_user_scoped_repository_with_user_id_property(self, service):
        """Test getting user-scoped repository with user_id property"""
        # Mock repository with user_id property
        repo = Mock()
        repo.user_id = "different_user"
        repo.session = Mock()
        
        with patch('fastmcp.task_management.application.services.agent_coordination_service.type') as mock_type:
            mock_class = Mock()
            mock_class.return_value = "new_scoped_repo"
            mock_type.return_value = mock_class
            
            result = service._get_user_scoped_repository(repo)
            
            mock_class.assert_called_once_with(repo.session, user_id="test_user")
            assert result == "new_scoped_repo"
    
    def test_get_user_scoped_repository_no_user_support(self, service):
        """Test getting repository without user support"""
        repo = Mock()
        result = service._get_user_scoped_repository(repo)
        assert result == repo
    
    def test_get_user_scoped_repository_none(self, service):
        """Test getting None repository"""
        result = service._get_user_scoped_repository(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_task_success(self, service, mock_task, mock_agent):
        """Test successful agent assignment to task"""
        # Setup
        task_id = "task123"
        agent_id = "agent123"
        role = "developer"
        assigned_by = "manager123"
        responsibilities = ["implement", "test"]
        estimated_hours = 8.0
        due_date = datetime.now()
        
        service.task_repository.get.return_value = mock_task
        service.agent_repository.get.return_value = mock_agent
        
        # Execute
        assignment = await service.assign_agent_to_task(
            task_id=task_id,
            agent_id=agent_id,
            role=role,
            assigned_by=assigned_by,
            responsibilities=responsibilities,
            estimated_hours=estimated_hours,
            due_date=due_date
        )
        
        # Assert
        assert assignment.task_id == task_id
        assert assignment.assigned_agent_id == agent_id
        assert assignment.role == role
        assert assignment.assigned_by_agent_id == assigned_by
        assert assignment.responsibilities == responsibilities
        assert assignment.estimated_hours == estimated_hours
        assert assignment.due_date == due_date
        
        # Verify agent state was updated
        mock_agent.start_task.assert_called_once_with(task_id)
        service.agent_repository.save.assert_called_once_with(mock_agent)
        
        # Verify event was published
        service.event_bus.publish.assert_called_once()
        event = service.event_bus.publish.call_args[0][0]
        assert event.agent_id == agent_id
        assert event.task_id == task_id
        assert event.role == role
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_task_task_not_found(self, service):
        """Test assignment when task not found"""
        service.task_repository.get.return_value = None
        
        with pytest.raises(AgentCoordinationException) as exc_info:
            await service.assign_agent_to_task(
                task_id="nonexistent",
                agent_id="agent123",
                role="developer",
                assigned_by="manager123"
            )
        
        assert "Task nonexistent not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_task_agent_not_found(self, service, mock_task):
        """Test assignment when agent not found"""
        service.task_repository.get.return_value = mock_task
        service.agent_repository.get.return_value = None
        
        with pytest.raises(AgentCoordinationException) as exc_info:
            await service.assign_agent_to_task(
                task_id="task123",
                agent_id="nonexistent",
                role="developer",
                assigned_by="manager123"
            )
        
        assert "Agent nonexistent not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_task_agent_not_available(self, service, mock_task, mock_agent):
        """Test assignment when agent not available"""
        mock_agent.is_available.return_value = False
        service.task_repository.get.return_value = mock_task
        service.agent_repository.get.return_value = mock_agent
        
        with pytest.raises(AgentCoordinationException) as exc_info:
            await service.assign_agent_to_task(
                task_id="task123",
                agent_id="agent123",
                role="developer",
                assigned_by="manager123"
            )
        
        assert "Agent agent123 is not available for new assignments" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_work_handoff_success(self, service, mock_agent):
        """Test successful work handoff request"""
        # Setup
        from_agent_id = "agent1"
        to_agent_id = "agent2"
        task_id = "task123"
        work_summary = "Completed backend"
        completed_items = ["API endpoints", "Database schema"]
        remaining_items = ["Frontend integration", "Testing"]
        handoff_notes = "API docs in wiki"
        
        # Mock both agents
        from_agent = Mock(spec=Agent)
        to_agent = Mock(spec=Agent)
        service.agent_repository.get.side_effect = [from_agent, to_agent]
        
        # Execute
        handoff = await service.request_work_handoff(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            task_id=task_id,
            work_summary=work_summary,
            completed_items=completed_items,
            remaining_items=remaining_items,
            handoff_notes=handoff_notes
        )
        
        # Assert
        assert handoff.from_agent_id == from_agent_id
        assert handoff.to_agent_id == to_agent_id
        assert handoff.task_id == task_id
        assert handoff.work_summary == work_summary
        assert handoff.completed_items == completed_items
        assert handoff.remaining_items == remaining_items
        assert handoff.handoff_notes == handoff_notes
        assert handoff.status == HandoffStatus.PENDING
        
        # Verify handoff was stored
        assert handoff.handoff_id in service.handoffs
        
        # Verify event was published
        service.event_bus.publish.assert_called_once()
        event = service.event_bus.publish.call_args[0][0]
        assert event.from_agent_id == from_agent_id
        assert event.to_agent_id == to_agent_id
    
    @pytest.mark.asyncio
    async def test_request_work_handoff_invalid_agents(self, service):
        """Test handoff request with invalid agents"""
        service.agent_repository.get.side_effect = [None, None]
        
        with pytest.raises(AgentCoordinationException) as exc_info:
            await service.request_work_handoff(
                from_agent_id="invalid1",
                to_agent_id="invalid2",
                task_id="task123",
                work_summary="Summary",
                completed_items=[],
                remaining_items=[]
            )
        
        assert "Invalid agent IDs for handoff" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_accept_handoff_success(self, service, mock_agent):
        """Test accepting a work handoff"""
        # Setup handoff
        handoff_id = str(uuid4())
        handoff = WorkHandoff(
            handoff_id=handoff_id,
            from_agent_id="agent1",
            to_agent_id="agent2",
            task_id="task123",
            initiated_at=datetime.now(),
            work_summary="Test summary",
            completed_items=[],
            remaining_items=["task1", "task2"]
        )
        service.handoffs[handoff_id] = handoff
        
        # Mock repositories
        service.task_repository.get.return_value = Mock()
        service.agent_repository.get.return_value = mock_agent
        
        # Execute
        await service.accept_handoff(handoff_id, "agent2", "Ready to continue")
        
        # Assert
        assert handoff.status == HandoffStatus.ACCEPTED
        
        # Verify reassignment occurred
        assert len(service.work_assignments) == 1
        
        # Verify event was published
        assert service.event_bus.publish.call_count == 2  # HandoffAccepted + AgentAssigned
    
    @pytest.mark.asyncio
    async def test_accept_handoff_not_found(self, service):
        """Test accepting non-existent handoff"""
        with pytest.raises(AgentCoordinationException) as exc_info:
            await service.accept_handoff("nonexistent", "agent123")
        
        assert "Handoff nonexistent not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_accept_handoff_wrong_agent(self, service):
        """Test accepting handoff by wrong agent"""
        # Setup handoff
        handoff_id = str(uuid4())
        handoff = WorkHandoff(
            handoff_id=handoff_id,
            from_agent_id="agent1",
            to_agent_id="agent2",
            task_id="task123",
            initiated_at=datetime.now(),
            work_summary="Test",
            completed_items=[],
            remaining_items=[]
        )
        service.handoffs[handoff_id] = handoff
        
        with pytest.raises(AgentCoordinationException) as exc_info:
            await service.accept_handoff(handoff_id, "agent3")
        
        assert "Agent agent3 is not the target of this handoff" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_reject_handoff_success(self, service):
        """Test rejecting a work handoff"""
        # Setup handoff
        handoff_id = str(uuid4())
        handoff = WorkHandoff(
            handoff_id=handoff_id,
            from_agent_id="agent1",
            to_agent_id="agent2",
            task_id="task123",
            initiated_at=datetime.now(),
            work_summary="Test",
            completed_items=[],
            remaining_items=[]
        )
        service.handoffs[handoff_id] = handoff
        
        # Execute
        reason = "Overloaded with other tasks"
        await service.reject_handoff(handoff_id, "agent2", reason)
        
        # Assert
        assert handoff.status == HandoffStatus.REJECTED
        assert handoff.rejection_reason == reason
        
        # Verify event was published
        service.event_bus.publish.assert_called_once()
        event = service.event_bus.publish.call_args[0][0]
        assert event.rejection_reason == reason
    
    @pytest.mark.asyncio
    async def test_detect_and_resolve_conflict_manual(self, service):
        """Test detecting and manually resolving a conflict"""
        # Execute
        conflict = await service.detect_and_resolve_conflict(
            task_id="task123",
            conflict_type=ConflictType.ROLE_OVERLAP,
            involved_agents=["agent1", "agent2"],
            description="Both agents working on same module"
        )
        
        # Assert
        assert conflict.conflict_type == ConflictType.ROLE_OVERLAP
        assert conflict.involved_agents == ["agent1", "agent2"]
        assert conflict.task_id == "task123"
        assert conflict.resolved is False
        
        # Verify conflict was stored
        assert conflict.conflict_id in service.conflicts
        
        # Verify only detection event was published (no resolution)
        service.event_bus.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_and_resolve_conflict_auto(self, service):
        """Test detecting and auto-resolving a conflict"""
        # Execute
        conflict = await service.detect_and_resolve_conflict(
            task_id="task123",
            conflict_type=ConflictType.RESOURCE_CONTENTION,
            involved_agents=["agent1", "agent2"],
            description="Database lock conflict",
            resolution_strategy=ResolutionStrategy.PRIORITY_BASED
        )
        
        # Assert
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ResolutionStrategy.PRIORITY_BASED
        
        # Verify two events were published (detection + resolution)
        assert service.event_bus.publish.call_count == 2
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_success(self, service):
        """Test resolving an existing conflict"""
        # Setup conflict
        conflict_id = str(uuid4())
        conflict = ConflictResolution(
            conflict_id=conflict_id,
            conflict_type=ConflictType.DEPENDENCY_CONFLICT,
            involved_agents=["agent1", "agent2"],
            task_id="task123",
            detected_at=datetime.now(),
            description="Test conflict"
        )
        service.conflicts[conflict_id] = conflict
        
        # Execute
        await service.resolve_conflict(
            conflict_id=conflict_id,
            strategy=ResolutionStrategy.MANUAL_INTERVENTION,
            resolved_by="manager123",
            details="Reassigned tasks"
        )
        
        # Assert
        assert conflict.resolved is True
        assert conflict.resolution_strategy == ResolutionStrategy.MANUAL_INTERVENTION
        assert conflict.resolved_by == "manager123"
        assert conflict.resolution_details == "Reassigned tasks"
        
        # Verify event was published
        service.event_bus.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_agent_status(self, service, mock_agent):
        """Test broadcasting agent status"""
        # Setup
        agent_id = "agent123"
        status = "busy"
        current_task_id = "task456"
        current_activity = "Implementing feature"
        blocker = "Waiting for API specs"
        
        service.agent_repository.get.return_value = mock_agent
        
        # Execute
        await service.broadcast_agent_status(
            agent_id=agent_id,
            status=status,
            current_task_id=current_task_id,
            current_activity=current_activity,
            blocker_description=blocker
        )
        
        # Verify event was published
        service.event_bus.publish.assert_called_once()
        event = service.event_bus.publish.call_args[0][0]
        assert event.agent_id == agent_id
        assert event.status == status
        assert event.current_task_id == current_task_id
        assert event.current_activity == current_activity
        assert event.blocker_description == blocker
        assert event.workload_percentage == 60.0
    
    @pytest.mark.asyncio
    async def test_rebalance_workload(self, service):
        """Test workload rebalancing"""
        # Setup agents with different workloads
        overloaded_agent = Mock(spec=Agent)
        overloaded_agent.id = "agent1"
        overloaded_agent.active_tasks = {"task1", "task2", "task3"}
        overloaded_agent.get_workload_percentage.return_value = 90.0
        
        underutilized_agent = Mock(spec=Agent)
        underutilized_agent.id = "agent2"
        underutilized_agent.active_tasks = {"task4"}
        underutilized_agent.get_workload_percentage.side_effect = [30.0, 50.0]  # Before and after
        underutilized_agent.is_available.return_value = True
        
        service.agent_repository.get_by_project.side_effect = [
            [overloaded_agent, underutilized_agent],  # Initial call
            [overloaded_agent, underutilized_agent]   # After rebalancing
        ]
        
        # Execute
        result = await service.rebalance_workload(
            project_id="proj123",
            initiated_by="manager123",
            reason="Weekly rebalancing"
        )
        
        # Assert
        assert len(result["tasks_reassigned"]) > 0
        assert "workload_before" in result
        assert "workload_after" in result
        
        # Verify event was published
        service.event_bus.publish.assert_called()
        event = service.event_bus.publish.call_args[0][0]
        assert event.initiated_by == "manager123"
        assert event.reason == "Weekly rebalancing"
    
    @pytest.mark.asyncio
    async def test_get_agent_workload(self, service, mock_agent):
        """Test getting detailed agent workload"""
        # Setup
        agent_id = "agent123"
        mock_agent.active_tasks = {"task1", "task2"}
        mock_agent.status = Mock(value="busy")
        service.agent_repository.get.return_value = mock_agent
        
        # Add some assignments
        assignment = WorkAssignment(
            assignment_id="assign1",
            task_id="task1",
            assigned_agent_id=agent_id,
            assigned_by_agent_id="manager",
            assigned_at=datetime.now(),
            role="developer"
        )
        service.work_assignments["assign1"] = assignment
        
        # Add pending handoffs
        handoff_to = WorkHandoff(
            handoff_id="hand1",
            from_agent_id="other_agent",
            to_agent_id=agent_id,
            task_id="task3",
            initiated_at=datetime.now(),
            work_summary="Test",
            completed_items=[],
            remaining_items=[]
        )
        service.handoffs["hand1"] = handoff_to
        
        # Execute
        result = await service.get_agent_workload(agent_id)
        
        # Assert
        assert result["agent_id"] == agent_id
        assert result["status"] == "busy"
        assert result["workload_percentage"] == 60.0
        assert result["current_tasks"] == 2
        assert result["max_tasks"] == 5
        assert len(result["active_assignments"]) == 1
        assert result["pending_handoffs_to_receive"] == 1
        assert result["pending_handoffs_to_give"] == 0
        assert result["can_accept_work"] is True
    
    @pytest.mark.asyncio
    async def test_find_best_agent_for_task_success(self, service, mock_task):
        """Test finding the best agent for a task"""
        # Setup
        task_id = "task123"
        service.task_repository.get.return_value = mock_task
        
        # Create available agents with different scores
        agent1 = Mock(spec=Agent)
        agent1.id = "agent1"
        agent1.name = "Agent 1"
        agent1.is_available.return_value = True
        agent1.get_workload_percentage.return_value = 30.0
        agent1.success_rate = 90.0
        
        agent2 = Mock(spec=Agent)
        agent2.id = "agent2"
        agent2.name = "Agent 2"
        agent2.is_available.return_value = True
        agent2.get_workload_percentage.return_value = 70.0
        agent2.success_rate = 95.0
        
        service.agent_repository.get_all.return_value = [agent1, agent2]
        
        # Execute
        result = await service.find_best_agent_for_task(
            task_id=task_id,
            required_role=AgentRole.DEVELOPER,
            required_expertise={AgentExpertise.BACKEND}
        )
        
        # Assert - agent1 should be selected due to lower workload
        assert result == agent1
    
    @pytest.mark.asyncio
    async def test_find_best_agent_for_task_none_available(self, service, mock_task):
        """Test finding agent when none are available"""
        # Setup
        service.task_repository.get.return_value = mock_task
        service.agent_repository.get_all.return_value = []
        
        # Execute
        result = await service.find_best_agent_for_task("task123")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_best_agent_for_task_low_scores(self, service, mock_task):
        """Test finding agent when all have low suitability scores"""
        # Setup
        service.task_repository.get.return_value = mock_task
        
        # Create agent with very high workload
        agent = Mock(spec=Agent)
        agent.id = "agent1"
        agent.name = "Overloaded Agent"
        agent.is_available.return_value = True
        agent.get_workload_percentage.return_value = 95.0
        agent.success_rate = 50.0
        
        service.agent_repository.get_all.return_value = [agent]
        
        # Execute
        result = await service.find_best_agent_for_task("task123")
        
        # Assert - no agent selected due to low score
        assert result is None
    
    def test_coordination_context_workload_methods(self):
        """Test CoordinationContext helper methods"""
        # Setup
        task = Mock()
        agents = [Mock(), Mock()]
        assignments = {"agent1": ["task1", "task2"], "agent2": ["task3"]}
        metrics = {"agent1": 0.7, "agent2": 0.3, "agent3": 0.9}
        
        context = CoordinationContext(
            task=task,
            available_agents=agents,
            current_assignments=assignments,
            workload_metrics=metrics
        )
        
        # Test get_agent_workload
        assert context.get_agent_workload("agent1") == 0.7
        assert context.get_agent_workload("agent2") == 0.3
        assert context.get_agent_workload("unknown") == 0.0
        
        # Test is_agent_overloaded with default threshold
        assert context.is_agent_overloaded("agent1") is False  # 0.7 < 0.8
        assert context.is_agent_overloaded("agent3") is True   # 0.9 > 0.8
        
        # Test is_agent_overloaded with custom threshold
        assert context.is_agent_overloaded("agent1", threshold=0.6) is True  # 0.7 > 0.6
        assert context.is_agent_overloaded("agent2", threshold=0.5) is False  # 0.3 < 0.5