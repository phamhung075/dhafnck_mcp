"""
Agent Repository Implementation using SQLAlchemy ORM

This module provides agent repository implementation using SQLAlchemy ORM,
supporting both SQLite and PostgreSQL databases.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import and_, desc

from ..base_orm_repository import BaseORMRepository
from ...database.models import Agent
from ....domain.repositories.agent_repository import AgentRepository
from ....domain.entities.agent import Agent as AgentEntity, AgentStatus, AgentCapability
from ....domain.exceptions.base_exceptions import (
    ResourceNotFoundException,
    ValidationException,
    DatabaseException
)

logger = logging.getLogger(__name__)


class ORMAgentRepository(BaseORMRepository[Agent], AgentRepository):
    """
    Agent repository implementation using SQLAlchemy ORM.
    
    This repository handles all agent-related database operations
    using SQLAlchemy, supporting both SQLite and PostgreSQL.
    """
    
    def __init__(self, project_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize ORM agent repository.
        
        Args:
            project_id: Project ID for context
            user_id: User ID for context
        """
        super().__init__(Agent)
        self.project_id = project_id
        self.user_id = user_id or "default_id"
    
    def _model_to_entity(self, agent: Agent) -> AgentEntity:
        """Convert SQLAlchemy model to domain entity"""
        try:
            # Parse capabilities from JSON list of strings to AgentCapability enum
            capabilities = set()
            if agent.capabilities:
                for cap_str in agent.capabilities:
                    try:
                        capabilities.add(AgentCapability(cap_str))
                    except ValueError:
                        # Skip invalid capabilities
                        logger.warning(f"Invalid capability '{cap_str}' for agent {agent.id}")
            
            # Parse status
            status = AgentStatus.AVAILABLE
            if agent.status:
                try:
                    status = AgentStatus(agent.status)
                except ValueError:
                    logger.warning(f"Invalid status '{agent.status}' for agent {agent.id}")
            
            return AgentEntity(
                id=agent.id,
                name=agent.name,
                description=agent.description or "",
                created_at=agent.created_at,
                updated_at=agent.updated_at,
                capabilities=capabilities,
                specializations=[],  # Agent model doesn't have specializations
                preferred_languages=[],  # Agent model doesn't have preferred languages
                preferred_frameworks=[],  # Agent model doesn't have preferred frameworks
                status=status,
                max_concurrent_tasks=1,  # Agent model doesn't have this field
                current_workload=0,  # Agent model doesn't have this field
                work_hours=None,  # Agent model doesn't have this field
                timezone="UTC",  # Agent model doesn't have this field
                priority_preference="medium",  # Agent model doesn't have this field
                completed_tasks=0,  # Agent model doesn't have this field
                average_task_duration=None,  # Agent model doesn't have this field
                success_rate=100.0,  # Agent model doesn't have this field
                assigned_projects=set(),  # Calculated from relationships
                assigned_trees=set(),  # Calculated from relationships
                active_tasks=set()  # Calculated from relationships
            )
        except Exception as e:
            logger.error(f"Error converting agent model to entity: {e}")
            raise DatabaseException(
                message=f"Failed to convert agent model to entity: {str(e)}",
                operation="model_to_entity",
                table="agents"
            )
    
    def _entity_to_model_dict(self, agent: AgentEntity) -> Dict[str, Any]:
        """Convert domain entity to model dictionary"""
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "capabilities": [cap.value for cap in agent.capabilities],
            "status": agent.status.value,
            "availability_score": 1.0 if agent.is_available() else 0.0,
            "last_active_at": datetime.now() if agent.status == AgentStatus.AVAILABLE else None,
            "model_metadata": {
                "specializations": agent.specializations,
                "preferred_languages": agent.preferred_languages,
                "preferred_frameworks": agent.preferred_frameworks,
                "max_concurrent_tasks": agent.max_concurrent_tasks,
                "current_workload": agent.current_workload,
                "work_hours": agent.work_hours,
                "timezone": agent.timezone,
                "priority_preference": agent.priority_preference,
                "completed_tasks": agent.completed_tasks,
                "average_task_duration": agent.average_task_duration,
                "success_rate": agent.success_rate,
                "assigned_projects": list(agent.assigned_projects),
                "assigned_trees": list(agent.assigned_trees),
                "active_tasks": list(agent.active_tasks)
            }
        }
    
    def register_agent(self, project_id: str, agent_id: str, name: str, call_agent: str = None) -> Dict[str, Any]:
        """Register a new agent to a project"""
        try:
            # Check if agent already exists
            if self.exists(id=agent_id):
                raise ValidationException(
                    message=f"Agent with ID '{agent_id}' already exists",
                    field="id",
                    value=agent_id
                )
            
            # Create agent entity
            agent_entity = AgentEntity(
                id=agent_id,
                name=name,
                description=f"Agent for project {project_id}",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Convert to model dict
            model_dict = self._entity_to_model_dict(agent_entity)
            
            # Add call_agent to model_metadata if provided
            if call_agent:
                model_dict["model_metadata"]["call_agent"] = call_agent
            
            # Create agent in database
            agent = self.create(**model_dict)
            
            # Convert back to dict for response
            agent_data = {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities or [],
                "status": agent.status,
                "availability_score": agent.availability_score,
                "model_metadata": agent.model_metadata or {},
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat()
            }
            
            logger.info(f"Registered agent {agent_id} for project {project_id}")
            return agent_data
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {e}")
            raise DatabaseException(
                message=f"Failed to register agent: {str(e)}",
                operation="register_agent",
                table="agents"
            )
    
    def unregister_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Unregister an agent from a project"""
        try:
            # Get agent data before deletion
            agent = self.get_by_id(agent_id)
            if not agent:
                raise ResourceNotFoundException(
                    message=f"Agent {agent_id} not found",
                    resource_type="agent",
                    resource_id=agent_id
                )
            
            # Store agent data for response
            agent_data = {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities or [],
                "status": agent.status,
                "model_metadata": agent.model_metadata or {}
            }
            
            # Delete the agent
            deleted = self.delete(agent_id)
            if not deleted:
                raise DatabaseException(
                    message=f"Failed to delete agent {agent_id}",
                    operation="unregister_agent",
                    table="agents"
                )
            
            logger.info(f"Unregistered agent {agent_id} from project {project_id}")
            return {
                "agent_data": agent_data,
                "removed_assignments": []  # Would need to implement assignment tracking
            }
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error unregistering agent {agent_id}: {e}")
            raise DatabaseException(
                message=f"Failed to unregister agent: {str(e)}",
                operation="unregister_agent",
                table="agents"
            )
    
    def assign_agent_to_tree(self, project_id: str, agent_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Assign an agent to a task tree"""
        try:
            # Get agent
            agent = self.get_by_id(agent_id)
            if not agent:
                raise ResourceNotFoundException(
                    message=f"Agent {agent_id} not found",
                    resource_type="agent",
                    resource_id=agent_id
                )
            
            # Update agent model_metadata to include assignment
            model_metadata = agent.model_metadata or {}
            assigned_trees = set(model_metadata.get("assigned_trees", []))
            
            if git_branch_id in assigned_trees:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} already assigned to tree {git_branch_id}"
                }
            
            assigned_trees.add(git_branch_id)
            model_metadata["assigned_trees"] = list(assigned_trees)
            
            # Update agent
            self.update(agent_id, 
                       model_metadata=model_metadata,
                       updated_at=datetime.now())
            
            logger.info(f"Assigned agent {agent_id} to tree {git_branch_id} in project {project_id}")
            return {
                "success": True,
                "message": f"Agent {agent_id} assigned to tree {git_branch_id}"
            }
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error assigning agent {agent_id} to tree {git_branch_id}: {e}")
            raise DatabaseException(
                message=f"Failed to assign agent to tree: {str(e)}",
                operation="assign_agent_to_tree",
                table="agents"
            )
    
    def unassign_agent_from_tree(self, project_id: str, agent_id: str, git_branch_id: str = None) -> Dict[str, Any]:
        """Unassign an agent from task tree(s)"""
        try:
            # Get agent
            agent = self.get_by_id(agent_id)
            if not agent:
                raise ResourceNotFoundException(
                    message=f"Agent {agent_id} not found",
                    resource_type="agent",
                    resource_id=agent_id
                )
            
            # Update agent metadata to remove assignment
            model_metadata = agent.model_metadata or {}
            assigned_trees = set(model_metadata.get("assigned_trees", []))
            
            if git_branch_id:
                # Remove specific assignment
                if git_branch_id in assigned_trees:
                    assigned_trees.remove(git_branch_id)
                    removed_assignments = [git_branch_id]
                else:
                    removed_assignments = []
            else:
                # Remove all assignments
                removed_assignments = list(assigned_trees)
                assigned_trees.clear()
            
            model_metadata["assigned_trees"] = list(assigned_trees)
            
            # Update agent
            self.update(agent_id, 
                       model_metadata=model_metadata,
                       updated_at=datetime.now())
            
            logger.info(f"Unassigned agent {agent_id} from {len(removed_assignments)} tree(s) in project {project_id}")
            return {
                "removed_assignments": removed_assignments,
                "remaining_assignments": list(assigned_trees)
            }
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error unassigning agent {agent_id}: {e}")
            raise DatabaseException(
                message=f"Failed to unassign agent from tree: {str(e)}",
                operation="unassign_agent_from_tree",
                table="agents"
            )
    
    def get_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Get agent details"""
        try:
            agent = self.get_by_id(agent_id)
            if not agent:
                raise ResourceNotFoundException(
                    message=f"Agent {agent_id} not found",
                    resource_type="agent",
                    resource_id=agent_id
                )
            
            # Get assignments from model_metadata
            model_metadata = agent.model_metadata or {}
            assignments = model_metadata.get("assigned_trees", [])
            
            agent_data = {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities or [],
                "status": agent.status,
                "availability_score": agent.availability_score,
                "model_metadata": model_metadata,
                "assignments": assignments,
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat()
            }
            
            return agent_data
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            raise DatabaseException(
                message=f"Failed to get agent: {str(e)}",
                operation="get_agent",
                table="agents"
            )
    
    def list_agents(self, project_id: str) -> Dict[str, Any]:
        """List all agents in a project"""
        try:
            # Get all agents (project filtering would need to be implemented)
            agents = self.get_all()
            
            agent_list = []
            for agent in agents:
                model_metadata = agent.model_metadata or {}
                assignments = model_metadata.get("assigned_trees", [])
                
                agent_data = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": agent.capabilities or [],
                    "status": agent.status,
                    "availability_score": agent.availability_score,
                    "model_metadata": model_metadata,
                    "assignments": assignments,
                    "created_at": agent.created_at.isoformat(),
                    "updated_at": agent.updated_at.isoformat()
                }
                agent_list.append(agent_data)
            
            return {
                "agents": agent_list,
                "total_agents": len(agent_list)
            }
            
        except Exception as e:
            logger.error(f"Error listing agents for project {project_id}: {e}")
            raise DatabaseException(
                message=f"Failed to list agents: {str(e)}",
                operation="list_agents",
                table="agents"
            )
    
    def update_agent(self, project_id: str, agent_id: str, name: str = None, call_agent: str = None) -> Dict[str, Any]:
        """Update agent details"""
        try:
            # Get agent
            agent = self.get_by_id(agent_id)
            if not agent:
                raise ResourceNotFoundException(
                    message=f"Agent {agent_id} not found",
                    resource_type="agent",
                    resource_id=agent_id
                )
            
            # Prepare updates
            updates = {"updated_at": datetime.now()}
            
            if name is not None:
                updates["name"] = name
            
            if call_agent is not None:
                model_metadata = agent.model_metadata or {}
                model_metadata["call_agent"] = call_agent
                updates["model_metadata"] = model_metadata
            
            # Update agent
            if len(updates) > 1:  # More than just updated_at
                updated_agent = self.update(agent_id, **updates)
            else:
                updated_agent = agent
            
            # Get assignments from model_metadata
            model_metadata = updated_agent.model_metadata or {}
            assignments = model_metadata.get("assigned_trees", [])
            
            agent_data = {
                "id": updated_agent.id,
                "name": updated_agent.name,
                "description": updated_agent.description,
                "capabilities": updated_agent.capabilities or [],
                "status": updated_agent.status,
                "availability_score": updated_agent.availability_score,
                "model_metadata": model_metadata,
                "assignments": assignments,
                "created_at": updated_agent.created_at.isoformat(),
                "updated_at": updated_agent.updated_at.isoformat()
            }
            
            logger.info(f"Updated agent {agent_id} in project {project_id}")
            return agent_data
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            raise DatabaseException(
                message=f"Failed to update agent: {str(e)}",
                operation="update_agent",
                table="agents"
            )
    
    def rebalance_agents(self, project_id: str) -> Dict[str, Any]:
        """Rebalance agent assignments across task trees"""
        try:
            # Get all agents
            agents = self.get_all()
            
            if not agents:
                return {
                    "rebalance_result": {
                        "changes_made": False,
                        "message": "No agents found in project"
                    }
                }
            
            # Simple rebalancing logic (would need more sophisticated implementation)
            changes = []
            
            for agent in agents:
                model_metadata = agent.model_metadata or {}
                assignments = model_metadata.get("assigned_trees", [])
                
                # For now, just log current assignments
                if assignments:
                    changes.append(f"Agent '{agent.name}' has {len(assignments)} assignments")
            
            logger.info(f"Rebalanced agents in project {project_id}")
            return {
                "rebalance_result": {
                    "changes_made": len(changes) > 0,
                    "changes": changes,
                    "message": f"Analyzed {len(agents)} agents"
                }
            }
            
        except Exception as e:
            logger.error(f"Error rebalancing agents in project {project_id}: {e}")
            raise DatabaseException(
                message=f"Failed to rebalance agents: {str(e)}",
                operation="rebalance_agents",
                table="agents"
            )
    
    def get_available_agents(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all available agents"""
        try:
            # Find agents with available status
            agents = self.find_by(status=AgentStatus.AVAILABLE.value)
            
            available_agents = []
            for agent in agents:
                model_metadata = agent.model_metadata or {}
                assignments = model_metadata.get("assigned_trees", [])
                
                agent_data = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": agent.capabilities or [],
                    "status": agent.status,
                    "availability_score": agent.availability_score,
                    "assignments": assignments,
                    "created_at": agent.created_at.isoformat(),
                    "updated_at": agent.updated_at.isoformat()
                }
                available_agents.append(agent_data)
            
            return available_agents
            
        except Exception as e:
            logger.error(f"Error getting available agents: {e}")
            raise DatabaseException(
                message=f"Failed to get available agents: {str(e)}",
                operation="get_available_agents",
                table="agents"
            )
    
    def search_agents(self, project_id: str, query: str) -> List[Dict[str, Any]]:
        """Search agents by name or capabilities"""
        try:
            # This would need more sophisticated search implementation
            # For now, do a simple name search
            with self.get_db_session() as session:
                search_pattern = f"%{query}%"
                agents = session.query(Agent).filter(
                    Agent.name.ilike(search_pattern)
                ).all()
            
            search_results = []
            for agent in agents:
                model_metadata = agent.model_metadata or {}
                assignments = model_metadata.get("assigned_trees", [])
                
                agent_data = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": agent.capabilities or [],
                    "status": agent.status,
                    "availability_score": agent.availability_score,
                    "assignments": assignments,
                    "created_at": agent.created_at.isoformat(),
                    "updated_at": agent.updated_at.isoformat()
                }
                search_results.append(agent_data)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching agents: {e}")
            raise DatabaseException(
                message=f"Failed to search agents: {str(e)}",
                operation="search_agents",
                table="agents"
            )