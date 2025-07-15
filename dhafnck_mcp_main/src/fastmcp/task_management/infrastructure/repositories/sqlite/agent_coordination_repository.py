"""SQLite Agent Coordination Repository"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict

from .base_repository import SQLiteBaseRepository
from ....domain.value_objects.coordination import (
    CoordinationRequest, WorkAssignment, WorkHandoff, ConflictResolution,
    AgentCommunication, HandoffStatus, ConflictType, ResolutionStrategy
)

logger = logging.getLogger(__name__)


class AgentCoordinationRepository(SQLiteBaseRepository):
    """SQLite repository for agent coordination data"""
    
    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path)
    
    async def save_coordination_request(self, request: CoordinationRequest) -> None:
        """Save a coordination request"""
        query = """
        INSERT OR REPLACE INTO coordination_requests 
        (request_id, requesting_agent_id, target_agent_id, coordination_type, 
         priority, created_at, expires_at, request_data, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Store task_id in context data
        context_data = dict(request.context) if request.context else {}
        context_data["task_id"] = request.task_id
        
        metadata = {
            "reason": request.reason,
            "handoff_notes": request.handoff_notes,
            "completion_criteria": request.completion_criteria,
            "review_items": request.review_items,
            "review_checklist": request.review_checklist
        }
        
        params = (
            request.request_id,
            request.requesting_agent_id,
            request.target_agent_id,
            request.coordination_type.value,
            request.priority,
            request.created_at.isoformat(),
            request.deadline.isoformat() if request.deadline else None,
            json.dumps(context_data),
            json.dumps(metadata)
        )
        self._execute_insert(query, params)
        logger.debug(f"Saved coordination request {request.request_id}")
    
    async def get_coordination_request(self, request_id: str) -> Optional[CoordinationRequest]:
        """Get a coordination request by ID"""
        query = "SELECT * FROM coordination_requests WHERE request_id = ?"
        row = self._execute_query(query, (request_id,), fetch_one=True)
        
        if row:
            return self._row_to_coordination_request(row)
        return None
    
    async def get_pending_coordination_requests(
        self,
        agent_id: Optional[str] = None,
        coordination_type: Optional[str] = None
    ) -> List[CoordinationRequest]:
        """Get pending coordination requests"""
        query = """
        SELECT * FROM coordination_requests 
        WHERE (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """
        params = []
        
        if agent_id:
            query += " AND target_agent_id = ?"
            params.append(agent_id)
        
        if coordination_type:
            query += " AND coordination_type = ?"
            params.append(coordination_type)
        
        query += " ORDER BY created_at DESC"
        
        rows = self._execute_query(query, tuple(params))
        return [self._row_to_coordination_request(row) for row in rows]
    
    async def save_work_assignment(self, assignment: WorkAssignment) -> None:
        """Save a work assignment"""
        query = """
        INSERT OR REPLACE INTO work_assignments 
        (assignment_id, task_id, assigned_agent_id, assigning_agent_id, 
         assigned_at, deadline, role, priority, capabilities_required, 
         context, metadata, is_completed, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Build metadata from assignment fields
        metadata = {
            "responsibilities": assignment.responsibilities,
            "deliverables": assignment.deliverables,
            "constraints": assignment.constraints,
            "collaborating_agents": assignment.collaborating_agents,
            "reporting_to": assignment.reporting_to,
            "estimated_hours": assignment.estimated_hours
        }
        
        params = (
            assignment.assignment_id,
            assignment.task_id,
            assignment.assigned_agent_id,
            assignment.assigned_by_agent_id,
            assignment.assigned_at.isoformat(),
            assignment.due_date.isoformat() if assignment.due_date else None,
            assignment.role,
            50,  # Default priority since WorkAssignment doesn't have priority field
            None,  # capabilities_required not in WorkAssignment
            None,  # context not directly in WorkAssignment
            json.dumps(metadata),
            assignment.is_overdue(),
            None  # completed_at not in WorkAssignment
        )
        self._execute_insert(query, params)
        logger.debug(f"Saved work assignment {assignment.assignment_id}")
    
    async def get_work_assignment(self, assignment_id: str) -> Optional[WorkAssignment]:
        """Get a work assignment by ID"""
        query = "SELECT * FROM work_assignments WHERE assignment_id = ?"
        row = self._execute_query(query, (assignment_id,), fetch_one=True)
        
        if row:
            return self._row_to_work_assignment(row)
        return None
    
    async def get_agent_assignments(
        self,
        agent_id: str,
        include_completed: bool = False
    ) -> List[WorkAssignment]:
        """Get all assignments for an agent"""
        query = "SELECT * FROM work_assignments WHERE assigned_agent_id = ?"
        params = [agent_id]
        
        if not include_completed:
            query += " AND is_completed = FALSE"
        
        query += " ORDER BY assigned_at DESC"
        
        rows = self._execute_query(query, tuple(params))
        return [self._row_to_work_assignment(row) for row in rows]
    
    async def get_task_assignments(self, task_id: str) -> List[WorkAssignment]:
        """Get all assignments for a task"""
        query = "SELECT * FROM work_assignments WHERE task_id = ? ORDER BY assigned_at DESC"
        rows = self._execute_query(query, (task_id,))
        return [self._row_to_work_assignment(row) for row in rows]
    
    async def save_handoff(self, handoff: WorkHandoff) -> None:
        """Save a work handoff"""
        query = """
        INSERT OR REPLACE INTO work_handoffs 
        (handoff_id, task_id, from_agent_id, to_agent_id, initiated_at, 
         accepted_at, completed_at, status, reason, handoff_data, context, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Build handoff data from WorkHandoff fields
        handoff_data = {
            "work_summary": handoff.work_summary,
            "completed_items": handoff.completed_items,
            "remaining_items": handoff.remaining_items,
            "known_issues": handoff.known_issues,
            "handoff_notes": handoff.handoff_notes,
            "artifacts": handoff.artifacts,
            "documentation_links": handoff.documentation_links
        }
        
        params = (
            handoff.handoff_id,
            handoff.task_id,
            handoff.from_agent_id,
            handoff.to_agent_id,
            handoff.initiated_at.isoformat(),
            handoff.accepted_at.isoformat() if handoff.accepted_at else None,
            handoff.completed_at.isoformat() if handoff.completed_at else None,
            handoff.status.value,
            handoff.rejection_reason,
            json.dumps(handoff_data),
            None,  # context not directly in WorkHandoff
            None   # metadata not directly in WorkHandoff
        )
        self._execute_insert(query, params)
        logger.debug(f"Saved handoff {handoff.handoff_id}")
    
    async def get_handoff(self, handoff_id: str) -> Optional[WorkHandoff]:
        """Get a handoff by ID"""
        query = "SELECT * FROM work_handoffs WHERE handoff_id = ?"
        row = self._execute_query(query, (handoff_id,), fetch_one=True)
        
        if row:
            return self._row_to_work_handoff(row)
        return None
    
    async def get_agent_handoffs(
        self,
        agent_id: str,
        direction: Optional[str] = None
    ) -> List[WorkHandoff]:
        """Get handoffs involving an agent"""
        if direction == 'from':
            query = "SELECT * FROM work_handoffs WHERE from_agent_id = ?"
        elif direction == 'to':
            query = "SELECT * FROM work_handoffs WHERE to_agent_id = ?"
        else:
            query = "SELECT * FROM work_handoffs WHERE from_agent_id = ? OR to_agent_id = ?"
            return self._execute_query_with_agent_filter(query, agent_id, agent_id)
        
        query += " ORDER BY initiated_at DESC"
        rows = self._execute_query(query, (agent_id,))
        return [self._row_to_work_handoff(row) for row in rows]
    
    async def get_pending_handoffs(self, agent_id: Optional[str] = None) -> List[WorkHandoff]:
        """Get pending handoffs"""
        query = "SELECT * FROM work_handoffs WHERE status = 'PENDING'"
        params = []
        
        if agent_id:
            query += " AND to_agent_id = ?"
            params.append(agent_id)
        
        query += " ORDER BY initiated_at"
        
        rows = self._execute_query(query, tuple(params))
        return [self._row_to_work_handoff(row) for row in rows]
    
    async def save_conflict(self, conflict: ConflictResolution) -> None:
        """Save a conflict resolution"""
        query = """
        INSERT OR REPLACE INTO conflict_resolutions 
        (conflict_id, task_id, conflict_type, detected_at, resolved_at, 
         resolution_strategy, involved_agents, conflict_details, 
         resolution_details, resolved_by_agent_id, metadata, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            conflict.conflict_id,
            conflict.task_id,
            conflict.conflict_type.value,
            conflict.detected_at.isoformat(),
            conflict.resolved_at.isoformat() if conflict.resolved_at else None,
            conflict.resolution_strategy.value if conflict.resolution_strategy else None,
            json.dumps(list(conflict.involved_agents)),
            json.dumps(conflict.conflict_details) if conflict.conflict_details else None,
            json.dumps(conflict.resolution_details) if conflict.resolution_details else None,
            conflict.resolved_by_agent_id,
            json.dumps(conflict.metadata) if conflict.metadata else None,
            conflict.is_resolved()
        )
        self._execute_insert(query, params)
        logger.debug(f"Saved conflict {conflict.conflict_id}")
    
    async def get_conflict(self, conflict_id: str) -> Optional[ConflictResolution]:
        """Get a conflict by ID"""
        query = "SELECT * FROM conflict_resolutions WHERE conflict_id = ?"
        row = self._execute_query(query, (conflict_id,), fetch_one=True)
        
        if row:
            return self._row_to_conflict_resolution(row)
        return None
    
    async def get_task_conflicts(
        self,
        task_id: str,
        include_resolved: bool = False
    ) -> List[ConflictResolution]:
        """Get conflicts for a task"""
        query = "SELECT * FROM conflict_resolutions WHERE task_id = ?"
        params = [task_id]
        
        if not include_resolved:
            query += " AND is_resolved = FALSE"
        
        query += " ORDER BY detected_at DESC"
        
        rows = self._execute_query(query, tuple(params))
        return [self._row_to_conflict_resolution(row) for row in rows]
    
    async def get_unresolved_conflicts(
        self,
        agent_id: Optional[str] = None
    ) -> List[ConflictResolution]:
        """Get unresolved conflicts"""
        query = "SELECT * FROM conflict_resolutions WHERE is_resolved = FALSE"
        params = []
        
        if agent_id:
            query += " AND involved_agents LIKE ?"
            params.append(f'%"{agent_id}"%')
        
        query += " ORDER BY detected_at"
        
        rows = self._execute_query(query, tuple(params))
        return [self._row_to_conflict_resolution(row) for row in rows]
    
    async def save_communication(self, communication: AgentCommunication) -> None:
        """Save an agent communication"""
        query = """
        INSERT OR REPLACE INTO agent_communications 
        (message_id, from_agent_id, to_agent_ids, task_id, 
         communication_type, content, priority, sent_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            communication.message_id,
            communication.from_agent_id,
            json.dumps(communication.to_agent_ids),
            communication.task_id,
            communication.communication_type.value,
            communication.content,
            communication.priority.value,
            communication.sent_at.isoformat(),
            json.dumps(communication.metadata) if communication.metadata else None
        )
        self._execute_insert(query, params)
        logger.debug(f"Saved communication {communication.message_id}")
    
    async def get_agent_communications(
        self,
        agent_id: str,
        limit: int = 50,
        include_sent: bool = True,
        include_received: bool = True
    ) -> List[AgentCommunication]:
        """Get communications for an agent"""
        conditions = []
        params = []
        
        if include_sent and include_received:
            conditions.append("(from_agent_id = ? OR to_agent_ids LIKE ?)")
            params.extend([agent_id, f'%"{agent_id}"%'])
        elif include_sent:
            conditions.append("from_agent_id = ?")
            params.append(agent_id)
        elif include_received:
            conditions.append("to_agent_ids LIKE ?")
            params.append(f'%"{agent_id}"%')
        
        if not conditions:
            return []
        
        query = f"SELECT * FROM agent_communications WHERE {' OR '.join(conditions)}"
        query += " ORDER BY sent_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self._execute_query(query, tuple(params))
        return [self._row_to_agent_communication(row) for row in rows]
    
    async def get_task_communications(self, task_id: str) -> List[AgentCommunication]:
        """Get communications related to a task"""
        query = "SELECT * FROM agent_communications WHERE task_id = ? ORDER BY sent_at DESC"
        rows = self._execute_query(query, (task_id,))
        return [self._row_to_agent_communication(row) for row in rows]
    
    async def get_coordination_stats(
        self,
        agent_id: Optional[str] = None,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get coordination statistics"""
        cutoff_time = None
        if time_window:
            cutoff_time = (datetime.now() - time_window).isoformat()
        
        stats = {
            "total_assignments": 0,
            "active_assignments": 0,
            "total_handoffs": 0,
            "pending_handoffs": 0,
            "accepted_handoffs": 0,
            "rejected_handoffs": 0,
            "total_conflicts": 0,
            "unresolved_conflicts": 0,
            "total_communications": 0,
            "assignments_by_role": {},
            "handoffs_by_status": {},
            "conflicts_by_type": {}
        }
        
        # Count assignments
        assignments_query = "SELECT role, is_completed FROM work_assignments WHERE 1=1"
        assignments_params = []
        
        if cutoff_time:
            assignments_query += " AND assigned_at >= ?"
            assignments_params.append(cutoff_time)
        
        if agent_id:
            assignments_query += " AND assigned_agent_id = ?"
            assignments_params.append(agent_id)
        
        assignment_rows = self._execute_query(assignments_query, tuple(assignments_params))
        
        for row in assignment_rows:
            stats["total_assignments"] += 1
            if row["role"]:
                stats["assignments_by_role"][row["role"]] = stats["assignments_by_role"].get(row["role"], 0) + 1
            if not row["is_completed"]:
                stats["active_assignments"] += 1
        
        # Count handoffs
        handoffs_query = "SELECT status FROM work_handoffs WHERE 1=1"
        handoffs_params = []
        
        if cutoff_time:
            handoffs_query += " AND initiated_at >= ?"
            handoffs_params.append(cutoff_time)
        
        if agent_id:
            handoffs_query += " AND (from_agent_id = ? OR to_agent_id = ?)"
            handoffs_params.extend([agent_id, agent_id])
        
        handoff_rows = self._execute_query(handoffs_query, tuple(handoffs_params))
        
        for row in handoff_rows:
            stats["total_handoffs"] += 1
            status = row["status"]
            stats["handoffs_by_status"][status] = stats["handoffs_by_status"].get(status, 0) + 1
            
            if status == "PENDING":
                stats["pending_handoffs"] += 1
            elif status == "ACCEPTED":
                stats["accepted_handoffs"] += 1
            elif status == "REJECTED":
                stats["rejected_handoffs"] += 1
        
        # Count conflicts
        conflicts_query = "SELECT conflict_type, is_resolved FROM conflict_resolutions WHERE 1=1"
        conflicts_params = []
        
        if cutoff_time:
            conflicts_query += " AND detected_at >= ?"
            conflicts_params.append(cutoff_time)
        
        if agent_id:
            conflicts_query += " AND involved_agents LIKE ?"
            conflicts_params.append(f'%"{agent_id}"%')
        
        conflict_rows = self._execute_query(conflicts_query, tuple(conflicts_params))
        
        for row in conflict_rows:
            stats["total_conflicts"] += 1
            conflict_type = row["conflict_type"]
            stats["conflicts_by_type"][conflict_type] = stats["conflicts_by_type"].get(conflict_type, 0) + 1
            
            if not row["is_resolved"]:
                stats["unresolved_conflicts"] += 1
        
        # Count communications
        comms_query = "SELECT COUNT(*) as count FROM agent_communications WHERE 1=1"
        comms_params = []
        
        if cutoff_time:
            comms_query += " AND sent_at >= ?"
            comms_params.append(cutoff_time)
        
        if agent_id:
            comms_query += " AND (from_agent_id = ? OR to_agent_ids LIKE ?)"
            comms_params.extend([agent_id, f'%"{agent_id}"%'])
        
        comm_result = self._execute_query(comms_query, tuple(comms_params), fetch_one=True)
        stats["total_communications"] = comm_result["count"] if comm_result else 0
        
        return stats
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Clean up old coordination data"""
        cutoff_time = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        removed = {
            "coordination_requests": 0,
            "work_assignments": 0,
            "handoffs": 0,
            "conflicts": 0,
            "communications": 0
        }
        
        # Clean coordination requests
        query = "DELETE FROM coordination_requests WHERE created_at < ?"
        removed["coordination_requests"] = self._execute_update(query, (cutoff_time,))
        
        # Clean completed work assignments
        query = "DELETE FROM work_assignments WHERE assigned_at < ? AND is_completed = TRUE"
        removed["work_assignments"] = self._execute_update(query, (cutoff_time,))
        
        # Clean completed handoffs
        query = """
        DELETE FROM work_handoffs 
        WHERE initiated_at < ? AND status IN ('COMPLETED', 'REJECTED', 'CANCELLED')
        """
        removed["handoffs"] = self._execute_update(query, (cutoff_time,))
        
        # Clean resolved conflicts
        query = "DELETE FROM conflict_resolutions WHERE detected_at < ? AND is_resolved = TRUE"
        removed["conflicts"] = self._execute_update(query, (cutoff_time,))
        
        # Clean old communications
        query = "DELETE FROM agent_communications WHERE sent_at < ?"
        removed["communications"] = self._execute_update(query, (cutoff_time,))
        
        logger.info(f"Cleaned up old coordination data: {removed}")
        return removed
    
    def _execute_query_with_agent_filter(self, query: str, agent1: str, agent2: str) -> List[WorkHandoff]:
        """Helper method for queries with dual agent filter"""
        rows = self._execute_query(query, (agent1, agent2))
        return [self._row_to_work_handoff(row) for row in rows]
    
    def _row_to_coordination_request(self, row) -> CoordinationRequest:
        """Convert database row to CoordinationRequest"""
        from ....domain.value_objects.coordination import CoordinationType
        
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        context_data = json.loads(row["request_data"]) if row["request_data"] else {}
        task_id = context_data.pop("task_id", "")
        
        return CoordinationRequest(
            request_id=row["request_id"],
            requesting_agent_id=row["requesting_agent_id"],
            target_agent_id=row["target_agent_id"],
            coordination_type=CoordinationType(row["coordination_type"]),
            task_id=task_id,
            created_at=datetime.fromisoformat(row["created_at"]),
            reason=metadata.get("reason", ""),
            priority=row["priority"],
            deadline=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            context=context_data,
            handoff_notes=metadata.get("handoff_notes"),
            completion_criteria=metadata.get("completion_criteria", []),
            review_items=metadata.get("review_items", []),
            review_checklist=metadata.get("review_checklist", {})
        )
    
    def _row_to_work_assignment(self, row) -> WorkAssignment:
        """Convert database row to WorkAssignment"""
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return WorkAssignment(
            assignment_id=row["assignment_id"],
            task_id=row["task_id"],
            assigned_agent_id=row["assigned_agent_id"],
            assigned_by_agent_id=row["assigning_agent_id"],
            assigned_at=datetime.fromisoformat(row["assigned_at"]),
            role=row["role"],
            responsibilities=metadata.get("responsibilities", []),
            deliverables=metadata.get("deliverables", []),
            constraints=metadata.get("constraints", {}),
            estimated_hours=metadata.get("estimated_hours"),
            due_date=datetime.fromisoformat(row["deadline"]) if row["deadline"] else None,
            collaborating_agents=metadata.get("collaborating_agents", []),
            reporting_to=metadata.get("reporting_to")
        )
    
    def _row_to_work_handoff(self, row) -> WorkHandoff:
        """Convert database row to WorkHandoff"""
        handoff_data = json.loads(row["handoff_data"]) if row["handoff_data"] else {}
        return WorkHandoff(
            handoff_id=row["handoff_id"],
            task_id=row["task_id"],
            from_agent_id=row["from_agent_id"],
            to_agent_id=row["to_agent_id"],
            initiated_at=datetime.fromisoformat(row["initiated_at"]),
            status=HandoffStatus(row["status"]),
            work_summary=handoff_data.get("work_summary", ""),
            completed_items=handoff_data.get("completed_items", []),
            remaining_items=handoff_data.get("remaining_items", []),
            known_issues=handoff_data.get("known_issues", []),
            handoff_notes=handoff_data.get("handoff_notes", ""),
            artifacts=handoff_data.get("artifacts", {}),
            documentation_links=handoff_data.get("documentation_links", []),
            accepted_at=datetime.fromisoformat(row["accepted_at"]) if row["accepted_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            rejection_reason=row["reason"]
        )
    
    def _row_to_conflict_resolution(self, row) -> ConflictResolution:
        """Convert database row to ConflictResolution"""
        return ConflictResolution(
            conflict_id=row["conflict_id"],
            task_id=row["task_id"],
            conflict_type=ConflictType(row["conflict_type"]),
            detected_at=datetime.fromisoformat(row["detected_at"]),
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            resolution_strategy=ResolutionStrategy(row["resolution_strategy"]) if row["resolution_strategy"] else None,
            involved_agents=set(json.loads(row["involved_agents"])),
            conflict_details=json.loads(row["conflict_details"]) if row["conflict_details"] else None,
            resolution_details=json.loads(row["resolution_details"]) if row["resolution_details"] else None,
            resolved_by_agent_id=row["resolved_by_agent_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None
        )
    
    def _row_to_agent_communication(self, row) -> AgentCommunication:
        """Convert database row to AgentCommunication"""
        from ....domain.value_objects.coordination import CommunicationType, CommunicationPriority
        
        return AgentCommunication(
            message_id=row["message_id"],
            from_agent_id=row["from_agent_id"],
            to_agent_ids=json.loads(row["to_agent_ids"]),
            task_id=row["task_id"],
            communication_type=CommunicationType(row["communication_type"]),
            content=row["content"],
            priority=CommunicationPriority(row["priority"]),
            sent_at=datetime.fromisoformat(row["sent_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else None
        )