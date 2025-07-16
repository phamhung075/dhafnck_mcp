"""SQLite Agent Repository Implementation"""

import sqlite3
import json
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from ....domain.repositories.agent_repository import AgentRepository
from ....domain.entities.agent import Agent, AgentCapability, AgentStatus
from ....domain.exceptions import AgentNotFoundError, ProjectNotFoundError
from ...database.database_source_manager import get_database_path, get_database_info
from ...database.database_initializer import initialize_database

logger = logging.getLogger(__name__)


class SQLiteAgentRepository(AgentRepository):
    """SQLite-based implementation of AgentRepository using new simplified schema"""
    
    def __init__(self, db_path: Optional[str] = None, user_id: Optional[str] = None, 
                 project_id: Optional[str] = None, git_branch_name: Optional[str] = None):
        """
        Initialize SQLiteAgentRepository
        
        Args:
            db_path: Path to SQLite database file
            user_id: User ID (compatibility parameter)
            project_id: Project ID (compatibility parameter)
            git_branch_name: Git branch name (compatibility parameter)
        """
        # Store user_id for filtering
        self.user_id = user_id or "default_id"
        
        # Use database source manager for single source of truth
        if db_path:
            # If explicit path provided, use it (for testing/override)
            self._db_path = str(Path(db_path).resolve()) if not Path(db_path).is_absolute() else str(db_path)
        else:
            # Use database source manager to determine correct database
            self._db_path = get_database_path()
        
        # Log database info
        db_info = get_database_info()
        logger.info(f"SQLiteAgentRepository using db_path: {self._db_path}")
        logger.info(f"Database mode: {db_info['mode']}, is_test: {db_info['is_test']}")
        
        # Ensure database exists and schema is initialized
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database using the central initializer."""
        try:
            # The central initializer is idempotent and thread-safe
            initialize_database(self._db_path)
        except Exception as e:
            logger.critical(f"Failed to initialize database via central initializer: {e}", exc_info=True)
            raise
    
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _agent_row_to_dict(self, agent_row: sqlite3.Row) -> Dict[str, Any]:
        """Convert agent database row to dictionary"""
        return {
            "id": agent_row["id"],
            "project_id": agent_row["project_id"],
            "name": agent_row["name"],
            "description": agent_row["description"] or "",
            "call_agent": agent_row["call_agent"] or "",
            "capabilities": json.loads(agent_row["capabilities"] or "[]"),
            "specializations": json.loads(agent_row["specializations"] or "[]"),
            "preferred_languages": json.loads(agent_row["preferred_languages"] or "[]"),
            "preferred_frameworks": json.loads(agent_row["preferred_frameworks"] or "[]"),
            "status": agent_row["status"],
            "max_concurrent_tasks": agent_row["max_concurrent_tasks"],
            "current_workload": agent_row["current_workload"],
            "completed_tasks": agent_row["completed_tasks"],
            "average_task_duration": agent_row["average_task_duration"],
            "success_rate": agent_row["success_rate"],
            "work_hours": json.loads(agent_row["work_hours"] or "{}"),
            "timezone": agent_row["timezone"],
            "priority_preference": agent_row["priority_preference"],
            "created_at": agent_row["created_at"],
            "updated_at": agent_row["updated_at"]
        }
    
    def _ensure_project_exists(self, project_id: str) -> None:
        """Ensure project exists"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM projects WHERE id = ?",
                (project_id,)
            )
            if not cursor.fetchone():
                raise ProjectNotFoundError(f"Project {project_id} not found")
    
    def _get_agent_assignments(self, project_id: str, agent_id: str) -> List[str]:
        """Get all assignments for an agent"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT git_branch_id FROM project_agent_assignments WHERE project_id = ? AND agent_id = ?",
                (project_id, agent_id)
            )
            return [row["git_branch_id"] for row in cursor.fetchall()]
    
    def register_agent(self, project_id: str, agent_id: str, name: str, call_agent: str = None) -> Dict[str, Any]:
        """Register a new agent to a project"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Check if agent already exists
                cursor = conn.execute(
                    "SELECT id FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                if cursor.fetchone():
                    raise ValueError(f"Agent with ID '{agent_id}' already exists in project '{project_id}'")
                
                # Insert new agent
                now = datetime.now(timezone.utc).isoformat()
                conn.execute('''
                    INSERT INTO project_agents (
                        id, project_id, name, description, call_agent, capabilities,
                        specializations, preferred_languages, preferred_frameworks,
                        status, max_concurrent_tasks, current_workload, completed_tasks,
                        average_task_duration, success_rate, work_hours, timezone,
                        priority_preference, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_id, project_id, name, "", call_agent or "",
                    json.dumps([]), json.dumps([]), json.dumps([]), json.dumps([]),
                    AgentStatus.AVAILABLE.value, 1, 0, 0, 0.0, 100.0, json.dumps({}),
                    "UTC", "high", now, now))
                
                # Get the created agent
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                agent_row = cursor.fetchone()
                
                if not agent_row:
                    raise Exception("Failed to create agent")
                
                agent_data = self._agent_row_to_dict(agent_row)
                agent_data["assignments"] = []
                
                logger.info(f"Registered agent {agent_id} in project {project_id}")
                return agent_data
                
        except ProjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {e}")
            raise
    
    def unregister_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Unregister an agent from a project"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Get agent data before deletion
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                agent_row = cursor.fetchone()
                
                if not agent_row:
                    raise AgentNotFoundError(f"Agent {agent_id} not found in project {project_id}")
                
                agent_data = self._agent_row_to_dict(agent_row)
                
                # Get current assignments
                assignments = self._get_agent_assignments(project_id, agent_id)
                
                # Delete agent assignments (following database schema source of truth)
                conn.execute(
                    "DELETE FROM project_agent_assignments WHERE agent_id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                
                # Delete the agent
                conn.execute(
                    "DELETE FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                
                logger.info(f"Unregistered agent {agent_id} from project {project_id} for user {self.user_id}")
                return {
                    "agent_data": agent_data,
                    "removed_assignments": assignments
                }
                
        except (ProjectNotFoundError, AgentNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error unregistering agent {agent_id}: {e}")
            raise
    
    def assign_agent_to_tree(self, project_id: str, agent_id: str, git_branch_id: str) -> Dict[str, Any]:
        """Assign an agent to a task tree, auto-registering the agent if it doesn't exist"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Check if agent exists, if not auto-register it
                cursor = conn.execute(
                    "SELECT id FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                agent_exists = cursor.fetchone()
                
                if not agent_exists:
                    # Auto-register the agent with default settings
                    logger.info(f"Auto-registering agent {agent_id} in project {project_id}")
                    try:
                        # Use agent_id as-is for the database ID to match the assignment lookup
                        # Extract agent name from agent_id (remove @ prefix if present)
                        agent_name = agent_id.lstrip('@')
                        
                        # Insert new agent with default settings
                        now = datetime.now(timezone.utc).isoformat()
                        conn.execute('''
                            INSERT INTO project_agents (
                                id, project_id, name, description, call_agent, capabilities,
                                specializations, preferred_languages, preferred_frameworks,
                                status, max_concurrent_tasks, current_workload, completed_tasks,
                                average_task_duration, success_rate, work_hours, timezone,
                                priority_preference, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            agent_id, project_id, agent_name, f"Auto-registered agent {agent_name}", agent_id,
                            json.dumps([]), json.dumps([]), json.dumps([]), json.dumps([]),
                            AgentStatus.AVAILABLE.value, 1, 0, 0, 0.0, 100.0, json.dumps({}),
                            "UTC", "high", now, now))
                        
                        logger.info(f"Successfully auto-registered agent {agent_id} in project {project_id}")
                        
                    except Exception as reg_error:
                        logger.error(f"Failed to auto-register agent {agent_id}: {reg_error}")
                        raise AgentNotFoundError(f"Agent {agent_id} not found in project {project_id} and auto-registration failed: {str(reg_error)}")
                
                # Verify task tree exists
                cursor = conn.execute(
                    "SELECT id FROM project_task_trees WHERE id = ? AND project_id = ?",
                    (git_branch_id, project_id)
                )
                if not cursor.fetchone():
                    raise Exception(f"Task tree {git_branch_id} not found in project {project_id}")
                
                # Check if already assigned
                cursor = conn.execute(
                    "SELECT 1 FROM project_agent_assignments WHERE project_id = ? AND agent_id = ? AND git_branch_id = ?",
                    (project_id, agent_id, git_branch_id)
                )
                if cursor.fetchone():
                    return {
                        "success": True,
                        "message": f"Agent {agent_id} already assigned to tree {git_branch_id}",
                        "auto_registered": not agent_exists
                    }
                
                # Create assignment
                conn.execute('''
                    INSERT INTO project_agent_assignments (project_id, agent_id, git_branch_id)
                    VALUES (?, ?, ?)
                ''', (project_id, agent_id, git_branch_id))
                
                # Update agent workload
                conn.execute(
                    "UPDATE project_agents SET current_workload = current_workload + 1 WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                
                logger.info(f"Assigned agent {agent_id} to tree {git_branch_id} in project {project_id}")
                return {
                    "success": True,
                    "message": f"Agent {agent_id} assigned to tree {git_branch_id}",
                    "auto_registered": not agent_exists
                }
                
        except (ProjectNotFoundError):
            raise
        except AgentNotFoundError:
            # Re-raise agent not found errors (from auto-registration failure)
            raise
        except Exception as e:
            logger.error(f"Error assigning agent {agent_id} to tree {git_branch_id}: {e}")
            raise
    
    def unassign_agent_from_tree(self, project_id: str, agent_id: str, git_branch_id: str = None) -> Dict[str, Any]:
        """Unassign an agent from task tree(s)"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Verify agent exists
                cursor = conn.execute(
                    "SELECT id FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                if not cursor.fetchone():
                    raise AgentNotFoundError(f"Agent {agent_id} not found in project {project_id}")
                
                # Get current assignments
                if git_branch_id:
                    # Unassign from specific tree
                    cursor = conn.execute(
                        "SELECT git_branch_id FROM project_agent_assignments WHERE project_id = ? AND agent_id = ? AND git_branch_id = ?",
                        (project_id, agent_id, git_branch_id)
                    )
                    assignment = cursor.fetchone()
                    if not assignment:
                        return {
                            "removed_assignments": [],
                            "remaining_assignments": self._get_agent_assignments(project_id, agent_id)
                        }
                    
                    # Remove specific assignment
                    conn.execute(
                        "DELETE FROM project_agent_assignments WHERE project_id = ? AND agent_id = ? AND git_branch_id = ?",
                        (project_id, agent_id, git_branch_id)
                    )
                    
                    removed_assignments = [git_branch_id]
                else:
                    # Unassign from all trees
                    current_assignments = self._get_agent_assignments(project_id, agent_id)
                    
                    # Remove all assignments
                    conn.execute(
                        "DELETE FROM project_agent_assignments WHERE project_id = ? AND agent_id = ?",
                        (project_id, agent_id)
                    )
                    
                    removed_assignments = current_assignments
                
                # Update agent workload
                workload_reduction = len(removed_assignments)
                if workload_reduction > 0:
                    conn.execute(
                        "UPDATE project_agents SET current_workload = MAX(0, current_workload - ?) WHERE id = ? AND project_id = ?",
                        (workload_reduction, agent_id, project_id)
                    )
                
                remaining_assignments = self._get_agent_assignments(project_id, agent_id)
                
                logger.info(f"Unassigned agent {agent_id} from {len(removed_assignments)} tree(s) in project {project_id}")
                return {
                    "removed_assignments": removed_assignments,
                    "remaining_assignments": remaining_assignments
                }
                
        except (ProjectNotFoundError, AgentNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error unassigning agent {agent_id}: {e}")
            raise
    
    def get_agent(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Get agent details"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                agent_row = cursor.fetchone()
                
                if not agent_row:
                    raise AgentNotFoundError(f"Agent {agent_id} not found in project {project_id}")
                
                agent_data = self._agent_row_to_dict(agent_row)
                agent_data["assignments"] = self._get_agent_assignments(project_id, agent_id)
                
                return agent_data
                
        except (ProjectNotFoundError, AgentNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            raise
    
    def list_agents(self, project_id: str) -> Dict[str, Any]:
        """List all agents in a project"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE project_id = ? ORDER BY name",
                    (project_id,)
                )
                agent_rows = cursor.fetchall()
                
                agents = []
                for agent_row in agent_rows:
                    agent_data = self._agent_row_to_dict(agent_row)
                    agent_data["assignments"] = self._get_agent_assignments(project_id, agent_data["id"])
                    agents.append(agent_data)
                
                return {
                    "agents": agents,
                    "total_agents": len(agents)
                }
                
        except ProjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error listing agents for project {project_id}: {e}")
            raise
    
    def update_agent(self, project_id: str, agent_id: str, name: str = None, call_agent: str = None) -> Dict[str, Any]:
        """Update agent details"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Verify agent exists
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                agent_row = cursor.fetchone()
                
                if not agent_row:
                    raise AgentNotFoundError(f"Agent {agent_id} not found in project {project_id}")
                
                # Build update query
                updates = []
                params = []
                
                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                
                if call_agent is not None:
                    updates.append("call_agent = ?")
                    params.append(call_agent)
                
                if not updates:
                    # No updates, return current data
                    agent_data = self._agent_row_to_dict(agent_row)
                    agent_data["assignments"] = self._get_agent_assignments(project_id, agent_id)
                    return agent_data
                
                # Add updated_at and conditions
                updates.append("updated_at = ?")
                params.append(datetime.now(timezone.utc).isoformat())
                params.extend([agent_id, project_id])  # Following clean relationship chain
                
                # Execute update
                conn.execute(
                    f"UPDATE project_agents SET {', '.join(updates)} WHERE id = ? AND project_id = ?",
                    params
                )
                
                # Get updated agent
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                updated_row = cursor.fetchone()
                
                agent_data = self._agent_row_to_dict(updated_row)
                agent_data["assignments"] = self._get_agent_assignments(project_id, agent_id)
                
                logger.info(f"Updated agent {agent_id} in project {project_id}")
                return agent_data
                
        except (ProjectNotFoundError, AgentNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            raise
    
    def rebalance_agents(self, project_id: str) -> Dict[str, Any]:
        """Rebalance agent assignments across task trees"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Get all agents and their current workloads
                cursor = conn.execute(
                    "SELECT id, name, current_workload, max_concurrent_tasks FROM project_agents WHERE project_id = ? ORDER BY current_workload",
                    (project_id,)
                )
                agents = cursor.fetchall()
                
                if not agents:
                    return {
                        "rebalance_result": {
                            "changes_made": False,
                            "message": "No agents found in project"
                        }
                    }
                
                # Get all task trees
                cursor = conn.execute(
                    "SELECT id, name FROM project_task_trees WHERE project_id = ?",
                    (project_id,)
                )
                task_trees = cursor.fetchall()
                
                if not task_trees:
                    return {
                        "rebalance_result": {
                            "changes_made": False,
                            "message": "No task trees found in project"
                        }
                    }
                
                # Get current assignments
                cursor = conn.execute(
                    "SELECT agent_id, git_branch_name FROM project_agent_assignments WHERE project_id = ?",
                    (project_id,)
                )
                assignments = cursor.fetchall()
                
                # Calculate ideal distribution
                total_trees = len(task_trees)
                total_agents = len(agents)
                
                if total_agents == 0:
                    return {
                        "rebalance_result": {
                            "changes_made": False,
                            "message": "No agents available for rebalancing"
                        }
                    }
                
                # Simple rebalancing: distribute trees evenly among agents
                trees_per_agent = total_trees // total_agents
                extra_trees = total_trees % total_agents
                
                changes = []
                agent_index = 0
                
                # Clear existing assignments
                conn.execute(
                    "DELETE FROM project_agent_assignments WHERE project_id = ?",
                    (project_id,)
                )
                
                # Redistribute trees
                for i, tree in enumerate(task_trees):
                    agent = agents[agent_index % total_agents]
                    
                    # Assign tree to agent
                    conn.execute(
                        "INSERT INTO project_agent_assignments (project_id, agent_id, git_branch_name) VALUES (?, ?, ?)",
                        (project_id, agent["id"], tree["id"])
                    )
                    
                    changes.append(f"Assigned tree '{tree['name']}' to agent '{agent['name']}'")
                    
                    # Move to next agent after distributing base amount + extra
                    trees_assigned_to_current = (i // total_agents) + 1
                    if trees_assigned_to_current >= trees_per_agent + (1 if agent_index < extra_trees else 0):
                        agent_index += 1
                
                # Update agent workloads
                for agent in agents:
                    cursor = conn.execute(
                        "SELECT COUNT(*) as count FROM project_agent_assignments WHERE agent_id = ? AND project_id = ?",
                        (agent["id"], project_id)
                    )
                    new_workload = cursor.fetchone()["count"]
                    
                    conn.execute(
                        "UPDATE project_agents SET current_workload = ? WHERE id = ? AND project_id = ?",
                        (new_workload, agent["id"], project_id)
                    )
                
                logger.info(f"Rebalanced {total_trees} trees among {total_agents} agents in project {project_id}")
                return {
                    "rebalance_result": {
                        "changes_made": len(changes) > 0,
                        "changes": changes,
                        "message": f"Rebalanced {total_trees} trees among {total_agents} agents"
                    }
                }
                
        except ProjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error rebalancing agents in project {project_id}: {e}")
            raise
    
    def get_agent_statistics(self, project_id: str, agent_id: str) -> Dict[str, Any]:
        """Get detailed statistics for an agent"""
        try:
            # Ensure project exists
            self._ensure_project_exists(project_id)
            
            with self._get_connection() as conn:
                # Get agent basic info
                cursor = conn.execute(
                    "SELECT * FROM project_agents WHERE id = ? AND project_id = ?",
                    (agent_id, project_id)
                )
                agent_row = cursor.fetchone()
                
                if not agent_row:
                    raise AgentNotFoundError(f"Agent {agent_id} not found in project {project_id}")
                
                agent_data = self._agent_row_to_dict(agent_row)
                
                # Get performance metrics
                cursor = conn.execute(
                    "SELECT metric_type, AVG(metric_value) as avg_value, COUNT(*) as count FROM agent_performance_metrics WHERE agent_id = ? AND project_id = ? GROUP BY metric_type",
                    (agent_id, project_id)
                )
                metrics = {row["metric_type"]: {"average": row["avg_value"], "count": row["count"]} for row in cursor.fetchall()}
                
                # Get workload history
                cursor = conn.execute(
                    "SELECT * FROM agent_workload_tracking WHERE agent_id = ? AND project_id = ? ORDER BY started_at DESC LIMIT 10",
                    (agent_id, project_id)
                )
                workload_history = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "agent": agent_data,
                    "performance_metrics": metrics,
                    "workload_history": workload_history,
                    "assignments": self._get_agent_assignments(project_id, agent_id)
                }
                
        except (ProjectNotFoundError, AgentNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error getting agent statistics for {agent_id}: {e}")
            raise 