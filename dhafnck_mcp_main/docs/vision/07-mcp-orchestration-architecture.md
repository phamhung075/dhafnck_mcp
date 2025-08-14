# MCP Server Orchestration Architecture for Multi-AI Vision & Context Management

## Overview

This document describes the architecture for managing vision and context updates through an MCP (Model Context Protocol) server that can be used by multiple AI clients (Cursor, Claude, ChatGPT, Gemini, Grok, etc.). The design ensures consistent vision and context updates regardless of which AI client is performing the work.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Clients                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ Cursor │ │ Claude │ │ChatGPT │ │ Gemini │ │  Grok  │   │
│  └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘   │
│       └──────────┴──────────┴──────────┴──────────┘        │
└───────────────────────────┬─────────────────────────────────┘
                            │ MCP Protocol
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Session Manager                         │   │
│  │  (Tracks which AI is working on which task)        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Orchestration Tools                        │   │
│  │  - start_work_session                              │   │
│  │  - report_progress                                 │   │
│  │  - report_insight                                  │   │
│  │  - complete_work                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Update Orchestrator                         │   │
│  │  (Handles vision & context updates)                │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
         ┌──────────────┐      ┌──────────────┐
         │Vision System │      │Context System│
         └──────────────┘      └──────────────┘
```

## Core Design Principles

### 1. Stateless MCP Tools
Each tool call is stateless, but the server maintains session state internally.

### 2. AI Client Identification
The server identifies which AI is making the call through session tokens or client metadata.

### 3. Automatic Update Propagation
Vision and context updates happen automatically based on tool calls, without AI clients needing to understand the update logic.

### 4. Multi-AI Coordination
Multiple AIs can work on different tasks simultaneously with proper session isolation.

## MCP Tool Definitions

### 1. Work Session Management Tools

```python
# File: mcp_tools/orchestration_tools.py

from mcp.server import Server
from mcp.server.models import Tool, CallToolRequest, CallToolResult
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

server = Server("task-orchestration")

# Internal session storage
work_sessions: Dict[str, WorkSession] = {}
ai_client_registry: Dict[str, AIClientInfo] = {}

@server.tool()
async def start_work_session(
    task_id: str,
    ai_client_id: Optional[str] = None,
    ai_client_type: Optional[str] = None,
    capabilities: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Start a work session for an AI to work on a task.
    
    Args:
        task_id: The ID of the task to work on
        ai_client_id: Optional identifier for the AI client
        ai_client_type: Type of AI (cursor, claude, chatgpt, gemini, grok)
        capabilities: List of capabilities the AI has
    
    Returns:
        session_id: Unique session identifier to use for subsequent calls
        task_details: Information about the task including vision alignment
    """
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Get or create AI client info
    if not ai_client_id:
        ai_client_id = f"{ai_client_type or 'unknown'}_{uuid.uuid4().hex[:8]}"
    
    if ai_client_id not in ai_client_registry:
        ai_client_registry[ai_client_id] = AIClientInfo(
            client_id=ai_client_id,
            client_type=ai_client_type or "unknown",
            capabilities=capabilities or [],
            first_seen=datetime.now()
        )
    
    # Get task details
    task = await task_service.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    
    # Create work session
    session = WorkSession(
        session_id=session_id,
        task_id=task_id,
        ai_client_id=ai_client_id,
        started_at=datetime.now(),
        task=task
    )
    
    work_sessions[session_id] = session
    
    # Initialize context
    context = await context_service.get_or_create_context(task_id)
    context.status = "in_progress"
    context.current_agent = ai_client_id
    context.add_progress(f"Work started by {ai_client_type or 'AI'} ({ai_client_id})")
    await context_service.save_context(context)
    
    # Return session info and task details
    response = {
        "session_id": session_id,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority
        }
    }
    
    # Include vision alignment if present
    if task.vision_alignment:
        response["vision_alignment"] = {
            "objectives": task.vision_alignment.contributes_to_objectives,
            "business_value": task.vision_alignment.business_value_score,
            "success_criteria": task.vision_alignment.success_criteria,
            "strategic_importance": task.vision_alignment.strategic_importance
        }
    
    # Include current context state
    response["context"] = {
        "status": context.status,
        "progress_percentage": context.progress_percentage or 0,
        "completed_criteria": context.completed_criteria or [],
        "current_blockers": context.blockers or []
    }
    
    return response

@server.tool()
async def report_progress(
    session_id: str,
    description: str,
    percentage: Optional[float] = None,
    metrics_affected: Optional[Dict[str, float]] = None,
    criteria_completed: Optional[List[str]] = None,
    deliverables_completed: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Report progress on the current work session.
    
    Args:
        session_id: The work session ID from start_work_session
        description: Description of what was accomplished
        percentage: Overall progress percentage (0-100)
        metrics_affected: Dict of metric_id -> new_value
        criteria_completed: List of success criteria that were completed
        deliverables_completed: List of deliverables that were completed
    
    Returns:
        success: Whether the update was successful
        vision_updated: Whether vision metrics were updated
        context_updated: Whether context was updated
    """
    # Validate session
    session = work_sessions.get(session_id)
    if not session:
        return {"error": "Invalid session ID"}
    
    # Update context with progress
    context = await context_service.get_context(session.task_id)
    context.add_progress(description, agent=session.ai_client_id)
    
    if percentage is not None:
        context.progress_percentage = percentage
        session.last_progress_percentage = percentage
    
    # Handle completed criteria
    if criteria_completed:
        for criterion in criteria_completed:
            if criterion not in context.completed_criteria:
                context.completed_criteria.append(criterion)
        
        # Update vision based on criteria completion
        if session.task.vision_alignment:
            await _update_vision_for_criteria(session.task, criteria_completed)
    
    # Handle deliverables
    if deliverables_completed:
        context.deliverables.extend(deliverables_completed)
    
    await context_service.save_context(context)
    
    # Update vision metrics if provided
    vision_updated = False
    if metrics_affected and session.task.vision_alignment:
        for metric_id, value in metrics_affected.items():
            await vision_service.update_metric(metric_id, value, source=f"task_{session.task_id}")
        vision_updated = True
        
        # Check for metric milestones
        await _check_metric_milestones(session.task, metrics_affected)
    
    # Update session tracking
    session.last_update = datetime.now()
    session.updates_count += 1
    
    return {
        "success": True,
        "vision_updated": vision_updated,
        "context_updated": True,
        "current_progress": context.progress_percentage,
        "total_criteria": len(session.task.vision_alignment.success_criteria) if session.task.vision_alignment else 0,
        "completed_criteria": len(context.completed_criteria)
    }

@server.tool()
async def report_insight(
    session_id: str,
    content: str,
    category: str = "general",
    importance: str = "medium",
    affects_vision: bool = False,
    innovation_opportunity: Optional[str] = None,
    risk_identified: Optional[str] = None,
    strategic_recommendation: Optional[str] = None,
    technical_discovery: Optional[str] = None
) -> Dict[str, Any]:
    """
    Report an insight discovered during work.
    
    Args:
        session_id: The work session ID
        content: The insight description
        category: Category (performance, security, architecture, etc.)
        importance: Importance level (low, medium, high, critical)
        affects_vision: Whether this affects strategic vision
        innovation_opportunity: Description of innovation opportunity
        risk_identified: Description of identified risk
        strategic_recommendation: Strategic recommendation
        technical_discovery: Technical discovery details
    
    Returns:
        success: Whether the insight was recorded
        vision_impact: Details of vision impact if any
    """
    # Validate session
    session = work_sessions.get(session_id)
    if not session:
        return {"error": "Invalid session ID"}
    
    # Add insight to context
    context = await context_service.get_context(session.task_id)
    context.add_insight(
        content=content,
        agent=session.ai_client_id,
        category=category,
        importance=importance
    )
    
    # Track technical discoveries
    if technical_discovery:
        context.technical_decisions[f"discovery_{datetime.now().timestamp()}"] = technical_discovery
    
    await context_service.save_context(context)
    
    vision_impact = {}
    
    # Handle vision-affecting insights
    if affects_vision and session.task.vision_alignment:
        if innovation_opportunity:
            await vision_service.add_innovation_opportunity(
                session.task.git_branch_id,
                innovation_opportunity
            )
            vision_impact["innovation_added"] = innovation_opportunity
        
        if risk_identified:
            await vision_service.add_risk_factor(
                session.task.git_branch_id,
                risk_identified,
                severity="high" if importance == "critical" else "medium"
            )
            vision_impact["risk_added"] = risk_identified
        
        if strategic_recommendation:
            await vision_service.add_strategic_recommendation(
                session.task.git_branch_id,
                strategic_recommendation
            )
            vision_impact["recommendation_added"] = strategic_recommendation
    
    return {
        "success": True,
        "insight_id": f"insight_{datetime.now().timestamp()}",
        "affects_vision": affects_vision,
        "vision_impact": vision_impact,
        "total_insights": len(context.insights)
    }

@server.tool()
async def report_blocker(
    session_id: str,
    description: str,
    severity: str = "medium",
    category: str = "general",
    suggested_resolution: Optional[str] = None,
    blocks_completion: bool = False
) -> Dict[str, Any]:
    """
    Report a blocker encountered during work.
    
    Args:
        session_id: The work session ID
        description: Description of the blocker
        severity: Severity level (low, medium, high, critical)
        category: Category of blocker (technical, dependency, access, etc.)
        suggested_resolution: Suggested way to resolve
        blocks_completion: Whether this prevents task completion
    
    Returns:
        success: Whether the blocker was recorded
        task_status_changed: Whether task status was updated
    """
    # Validate session
    session = work_sessions.get(session_id)
    if not session:
        return {"error": "Invalid session ID"}
    
    # Add blocker to context
    context = await context_service.get_context(session.task_id)
    blocker = {
        "description": description,
        "severity": severity,
        "category": category,
        "suggested_resolution": suggested_resolution,
        "reported_by": session.ai_client_id,
        "reported_at": datetime.now().isoformat()
    }
    context.blockers.append(blocker)
    
    # Update task status if critical
    task_status_changed = False
    if severity == "critical" or blocks_completion:
        await task_service.update_status(session.task_id, "blocked")
        task_status_changed = True
        context.status = "blocked"
    
    await context_service.save_context(context)
    
    # Add to vision risks if severe
    if severity in ["high", "critical"] and session.task.vision_alignment:
        await vision_service.add_risk_factor(
            session.task.git_branch_id,
            f"Blocker: {description}",
            severity=severity
        )
    
    return {
        "success": True,
        "blocker_id": f"blocker_{datetime.now().timestamp()}",
        "task_status_changed": task_status_changed,
        "current_task_status": "blocked" if task_status_changed else session.task.status,
        "total_blockers": len(context.blockers)
    }

@server.tool()
async def complete_work_session(
    session_id: str,
    summary: str,
    deliverables: Optional[List[str]] = None,
    metrics_achieved: Optional[Dict[str, float]] = None,
    quality_score: Optional[float] = None,
    next_steps: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Complete the work session and finalize all updates.
    
    Args:
        session_id: The work session ID
        summary: Summary of work completed
        deliverables: List of deliverables produced
        metrics_achieved: Final metric values achieved
        quality_score: Quality score of work (0.0-1.0)
        next_steps: Recommended next steps
    
    Returns:
        success: Whether completion was successful
        vision_impact: Summary of vision impact
        can_complete_task: Whether the task can be marked complete
    """
    # Validate session
    session = work_sessions.get(session_id)
    if not session:
        return {"error": "Invalid session ID"}
    
    # Update context with completion
    context = await context_service.get_context(session.task_id)
    context.completion_summary = summary
    
    if deliverables:
        context.deliverables.extend(deliverables)
    
    if next_steps:
        context.next_steps = next_steps
    
    # Calculate work duration
    duration = (datetime.now() - session.started_at).total_seconds()
    context.add_insight(
        f"Work completed in {duration/3600:.1f} hours by {session.ai_client_id}",
        category="completion",
        importance="low"
    )
    
    await context_service.save_context(context)
    
    # Update final metrics
    vision_impact = {}
    if metrics_achieved and session.task.vision_alignment:
        for metric_id, value in metrics_achieved.items():
            await vision_service.update_metric(
                metric_id, 
                value,
                source=f"task_{session.task_id}_final"
            )
        vision_impact["metrics_updated"] = list(metrics_achieved.keys())
    
    # Calculate vision contribution
    if session.task.vision_alignment:
        contribution = await _calculate_vision_contribution(
            session.task,
            context,
            quality_score or 1.0
        )
        
        # Update objective progress
        for obj_id, impact in contribution.items():
            await vision_service.update_objective_progress(
                obj_id,
                impact,
                source=f"task_{session.task_id}"
            )
        
        vision_impact["objective_contributions"] = contribution
    
    # Check if task can be completed
    can_complete = await _check_task_completion_criteria(session.task, context)
    
    # Clean up session
    session.completed_at = datetime.now()
    session.is_active = False
    
    # Log AI client performance
    ai_client = ai_client_registry[session.ai_client_id]
    ai_client.tasks_completed += 1
    ai_client.total_work_duration += duration
    
    return {
        "success": True,
        "session_duration_hours": duration / 3600,
        "vision_impact": vision_impact,
        "can_complete_task": can_complete,
        "criteria_status": {
            "total": len(session.task.vision_alignment.success_criteria) if session.task.vision_alignment else 0,
            "completed": len(context.completed_criteria)
        },
        "ai_client_stats": {
            "tasks_completed": ai_client.tasks_completed,
            "average_duration_hours": ai_client.total_work_duration / ai_client.tasks_completed / 3600
        }
    }

@server.tool()
async def get_active_sessions() -> Dict[str, Any]:
    """
    Get all active work sessions across all AI clients.
    
    Returns:
        active_sessions: List of active sessions with details
        by_ai_type: Sessions grouped by AI type
    """
    active = []
    by_ai_type = {}
    
    for session_id, session in work_sessions.items():
        if session.is_active:
            ai_info = ai_client_registry.get(session.ai_client_id)
            session_data = {
                "session_id": session_id,
                "task_id": session.task_id,
                "ai_client_id": session.ai_client_id,
                "ai_type": ai_info.client_type if ai_info else "unknown",
                "started_at": session.started_at.isoformat(),
                "duration_minutes": (datetime.now() - session.started_at).seconds / 60,
                "last_update": session.last_update.isoformat() if session.last_update else None,
                "progress": session.last_progress_percentage or 0
            }
            
            active.append(session_data)
            
            # Group by AI type
            ai_type = ai_info.client_type if ai_info else "unknown"
            if ai_type not in by_ai_type:
                by_ai_type[ai_type] = []
            by_ai_type[ai_type].append(session_data)
    
    return {
        "total_active": len(active),
        "active_sessions": active,
        "by_ai_type": by_ai_type,
        "ai_client_summary": {
            ai_type: len(sessions) for ai_type, sessions in by_ai_type.items()
        }
    }

@server.tool()
async def get_ai_client_stats() -> Dict[str, Any]:
    """
    Get statistics about AI clients using the system.
    
    Returns:
        Statistics about different AI clients and their performance
    """
    stats_by_type = {}
    
    for client_id, client_info in ai_client_registry.items():
        ai_type = client_info.client_type
        
        if ai_type not in stats_by_type:
            stats_by_type[ai_type] = {
                "total_clients": 0,
                "total_tasks": 0,
                "total_hours": 0,
                "capabilities": set()
            }
        
        stats_by_type[ai_type]["total_clients"] += 1
        stats_by_type[ai_type]["total_tasks"] += client_info.tasks_completed
        stats_by_type[ai_type]["total_hours"] += client_info.total_work_duration / 3600
        stats_by_type[ai_type]["capabilities"].update(client_info.capabilities)
    
    # Convert sets to lists for JSON serialization
    for ai_type in stats_by_type:
        stats_by_type[ai_type]["capabilities"] = list(stats_by_type[ai_type]["capabilities"])
        if stats_by_type[ai_type]["total_tasks"] > 0:
            stats_by_type[ai_type]["avg_hours_per_task"] = (
                stats_by_type[ai_type]["total_hours"] / stats_by_type[ai_type]["total_tasks"]
            )
    
    return {
        "ai_types": list(stats_by_type.keys()),
        "stats_by_type": stats_by_type,
        "total_unique_clients": len(ai_client_registry),
        "most_active_type": max(stats_by_type.items(), key=lambda x: x[1]["total_tasks"])[0] if stats_by_type else None
    }
```

### 2. Supporting Data Models

```python
# File: mcp_tools/orchestration_models.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class AIClientInfo:
    """Information about an AI client"""
    client_id: str
    client_type: str  # cursor, claude, chatgpt, gemini, grok
    capabilities: List[str]
    first_seen: datetime
    last_seen: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    total_work_duration: float = 0.0  # seconds
    
    def update_last_seen(self):
        self.last_seen = datetime.now()

@dataclass
class WorkSession:
    """Represents an active work session"""
    session_id: str
    task_id: str
    ai_client_id: str
    started_at: datetime
    task: Any  # Task entity
    completed_at: Optional[datetime] = None
    last_update: Optional[datetime] = None
    is_active: bool = True
    updates_count: int = 0
    last_progress_percentage: Optional[float] = None
    
    def duration_seconds(self) -> float:
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
```

### 3. Helper Functions

```python
# File: mcp_tools/orchestration_helpers.py

async def _update_vision_for_criteria(task: Task, completed_criteria: List[str]) -> None:
    """Update vision based on completed criteria"""
    if not task.vision_alignment:
        return
    
    # Calculate progress based on criteria completion
    total_criteria = len(task.vision_alignment.success_criteria)
    completed_count = len(completed_criteria)
    
    if total_criteria > 0:
        criteria_progress = (completed_count / total_criteria) * 100
        
        # Update objective progress proportionally
        contribution = task.vision_alignment.business_value_score * (criteria_progress / 100) * 0.1
        
        for obj_id in task.vision_alignment.contributes_to_objectives:
            await vision_service.increment_objective_progress(
                obj_id,
                contribution,
                source=f"task_{task.id}_criteria"
            )

async def _check_metric_milestones(task: Task, metrics: Dict[str, float]) -> None:
    """Check if metric updates cross important milestones"""
    milestones = {
        'response_time_ms': [1000, 750, 500, 250, 100],
        'error_rate': [0.05, 0.02, 0.01, 0.001],
        'test_coverage': [60, 70, 80, 90, 95]
    }
    
    for metric_id, value in metrics.items():
        if metric_id in milestones:
            for milestone in milestones[metric_id]:
                # Check if we crossed this milestone
                old_metric = await vision_service.get_metric(metric_id)
                if old_metric and old_metric.current_value > milestone >= value:
                    # Milestone achieved!
                    await context_service.add_insight(
                        task.id,
                        f"Achieved {metric_id} milestone: {milestone}",
                        category="achievement",
                        importance="high"
                    )

async def _calculate_vision_contribution(
    task: Task,
    context: Context,
    quality_score: float
) -> Dict[str, float]:
    """Calculate task's contribution to vision objectives"""
    if not task.vision_alignment:
        return {}
    
    # Base contribution from business value
    base_contribution = task.vision_alignment.business_value_score / 10
    
    # Adjust for completion quality
    quality_adjusted = base_contribution * quality_score
    
    # Adjust for criteria completion
    total_criteria = len(task.vision_alignment.success_criteria)
    completed_criteria = len(context.completed_criteria)
    criteria_factor = (completed_criteria / total_criteria) if total_criteria > 0 else 1.0
    
    final_contribution = quality_adjusted * criteria_factor
    
    # Distribute to objectives
    contributions = {}
    for obj_id in task.vision_alignment.contributes_to_objectives:
        contributions[obj_id] = final_contribution
    
    return contributions

async def _check_task_completion_criteria(task: Task, context: Context) -> bool:
    """Check if task meets completion criteria"""
    if not task.vision_alignment:
        # No vision alignment, can complete if context updated
        return context.status != "blocked"
    
    # Check all success criteria are met
    all_criteria_met = all(
        criterion in context.completed_criteria
        for criterion in task.vision_alignment.success_criteria
    )
    
    # Check no critical blockers
    no_critical_blockers = not any(
        blocker.get("severity") == "critical"
        for blocker in context.blockers
    )
    
    return all_criteria_met and no_critical_blockers
```

## Integration with Different AI Clients

### 1. Cursor Integration

```python
# Example: How Cursor would use these tools

# In Cursor's command/task execution
async def execute_task_with_mcp(task_id: str):
    # Start work session
    session_result = await mcp_client.call_tool(
        "start_work_session",
        {
            "task_id": task_id,
            "ai_client_type": "cursor",
            "capabilities": ["coding", "refactoring", "testing"]
        }
    )
    
    session_id = session_result["session_id"]
    
    # Work on task...
    
    # Report progress
    await mcp_client.call_tool(
        "report_progress",
        {
            "session_id": session_id,
            "description": "Implemented caching layer",
            "percentage": 50,
            "metrics_affected": {
                "response_time_ms": 450
            }
        }
    )
    
    # Report insight
    await mcp_client.call_tool(
        "report_insight",
        {
            "session_id": session_id,
            "content": "Found opportunity for query optimization",
            "category": "performance",
            "affects_vision": True,
            "innovation_opportunity": "Implement query result caching"
        }
    )
    
    # Complete session
    await mcp_client.call_tool(
        "complete_work_session",
        {
            "session_id": session_id,
            "summary": "Implemented performance optimizations",
            "deliverables": ["Caching layer", "Optimized queries"],
            "metrics_achieved": {
                "response_time_ms": 250
            }
        }
    )
```

### 2. Claude Integration

```python
# Claude would use function calling with MCP tools

tools = [
    {
        "name": "start_work_session",
        "description": "Start working on a task",
        "parameters": {...}
    },
    {
        "name": "report_progress",
        "description": "Report progress on current task",
        "parameters": {...}
    }
]

# Claude's response would include tool use:
# <function_calls>
# <invoke name="start_work_session">
#   <parameter name="task_id">task_123</parameter>
#   <parameter name="ai_client_type">claude</parameter>
# </invoke>
# </function_calls>
```

### 3. ChatGPT Integration

```python
# ChatGPT function calling format

functions = [
    {
        "name": "start_work_session",
        "description": "Start a work session on a task",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "ai_client_type": {"type": "string", "enum": ["chatgpt"]}
            }
        }
    }
]

# ChatGPT would call functions and get results
```

## Configuration

### MCP Server Configuration

```yaml
# File: mcp_server_config.yaml

server:
  name: "task-orchestration"
  version: "1.0.0"
  
  # Session management
  sessions:
    max_duration_hours: 24
    cleanup_interval_minutes: 60
    max_concurrent_per_client: 5
  
  # AI client configuration
  ai_clients:
    supported_types:
      - cursor
      - claude
      - chatgpt
      - gemini
      - grok
    
    default_capabilities:
      cursor: ["coding", "refactoring", "debugging"]
      claude: ["analysis", "documentation", "architecture"]
      chatgpt: ["general", "research", "planning"]
      gemini: ["multimodal", "analysis", "coding"]
      grok: ["analysis", "optimization", "research"]
  
  # Update strategies
  update_strategies:
    vision_update_on:
      - criteria_completed
      - metrics_achieved
      - deliverable_completed
    
    context_update_on:
      - any_progress
      - insight_added
      - blocker_reported
    
    objective_contribution:
      mode: "incremental"  # or "milestone"
      max_contribution_per_task: 10.0
  
  # Monitoring
  monitoring:
    track_client_performance: true
    aggregate_metrics_interval: 300
    export_prometheus: true
```

### Client-Specific Configuration

```yaml
# File: ai_client_configs/cursor_config.yaml

cursor:
  # Progress reporting
  progress:
    report_interval: "on_save"  # Report on file save
    include_metrics: true
    track_file_changes: true
  
  # Insight detection
  insights:
    auto_detect:
      - performance_issues
      - code_smells
      - security_vulnerabilities
    
    importance_mapping:
      security: "critical"
      performance: "high"
      code_quality: "medium"
  
  # Integration
  integration:
    auto_start_session: true
    session_persistence: true
    sync_with_git: true
```

## Monitoring and Analytics

### 1. Cross-AI Analytics

```python
@server.tool()
async def get_analytics_dashboard() -> Dict[str, Any]:
    """
    Get analytics across all AI clients.
    
    Returns:
        Comprehensive analytics dashboard data
    """
    # Task completion by AI type
    completion_by_type = {}
    
    # Performance metrics by AI type
    performance_by_type = {}
    
    # Vision impact by AI type
    vision_impact_by_type = {}
    
    for session in work_sessions.values():
        if not session.is_active:
            ai_info = ai_client_registry.get(session.ai_client_id)
            ai_type = ai_info.client_type if ai_info else "unknown"
            
            # Track completions
            if ai_type not in completion_by_type:
                completion_by_type[ai_type] = 0
            completion_by_type[ai_type] += 1
            
            # Track performance
            if ai_type not in performance_by_type:
                performance_by_type[ai_type] = {
                    "avg_duration_hours": 0,
                    "total_tasks": 0
                }
            
            duration_hours = session.duration_seconds() / 3600
            perf = performance_by_type[ai_type]
            perf["avg_duration_hours"] = (
                (perf["avg_duration_hours"] * perf["total_tasks"] + duration_hours) /
                (perf["total_tasks"] + 1)
            )
            perf["total_tasks"] += 1
    
    # Get vision metrics
    vision_metrics = await vision_service.get_aggregated_metrics()
    
    return {
        "overview": {
            "total_sessions": len(work_sessions),
            "active_sessions": sum(1 for s in work_sessions.values() if s.is_active),
            "unique_ai_clients": len(ai_client_registry)
        },
        "completion_by_type": completion_by_type,
        "performance_by_type": performance_by_type,
        "vision_progress": vision_metrics,
        "top_performers": _calculate_top_performers(),
        "recommendations": _generate_ai_recommendations()
    }

def _calculate_top_performers() -> List[Dict[str, Any]]:
    """Calculate top performing AI clients"""
    performers = []
    
    for client_id, client_info in ai_client_registry.items():
        if client_info.tasks_completed > 0:
            avg_duration = client_info.total_work_duration / client_info.tasks_completed
            performers.append({
                "client_id": client_id,
                "type": client_info.client_type,
                "tasks_completed": client_info.tasks_completed,
                "avg_duration_hours": avg_duration / 3600,
                "efficiency_score": 100 / (avg_duration / 3600)  # Simple efficiency metric
            })
    
    # Sort by efficiency
    performers.sort(key=lambda x: x["efficiency_score"], reverse=True)
    return performers[:10]

def _generate_ai_recommendations() -> List[str]:
    """Generate recommendations for AI usage"""
    recommendations = []
    
    # Analyze patterns
    type_performance = {}
    for client_id, client_info in ai_client_registry.items():
        ai_type = client_info.client_type
        if ai_type not in type_performance:
            type_performance[ai_type] = []
        
        if client_info.tasks_completed > 0:
            type_performance[ai_type].append(
                client_info.total_work_duration / client_info.tasks_completed
            )
    
    # Generate recommendations
    for ai_type, durations in type_performance.items():
        if durations:
            avg_duration = sum(durations) / len(durations) / 3600
            if avg_duration < 1:
                recommendations.append(
                    f"{ai_type} excels at quick tasks (avg {avg_duration:.1f}h)"
                )
            elif avg_duration > 4:
                recommendations.append(
                    f"Consider breaking down complex tasks for {ai_type}"
                )
    
    return recommendations
```

### 2. Session Monitoring

```python
@server.tool()
async def monitor_session_health() -> Dict[str, Any]:
    """
    Monitor health of active sessions.
    
    Returns:
        Health status of all active sessions
    """
    health_report = {
        "healthy": [],
        "stale": [],
        "stuck": []
    }
    
    current_time = datetime.now()
    
    for session_id, session in work_sessions.items():
        if not session.is_active:
            continue
        
        session_info = {
            "session_id": session_id,
            "task_id": session.task_id,
            "ai_client": session.ai_client_id,
            "duration_hours": (current_time - session.started_at).seconds / 3600
        }
        
        # Check if session is stale (no updates for 30 min)
        if session.last_update:
            minutes_since_update = (current_time - session.last_update).seconds / 60
            if minutes_since_update > 30:
                session_info["minutes_since_update"] = minutes_since_update
                health_report["stale"].append(session_info)
                continue
        
        # Check if session is stuck (running > 8 hours)
        if session_info["duration_hours"] > 8:
            health_report["stuck"].append(session_info)
        else:
            health_report["healthy"].append(session_info)
    
    return {
        "summary": {
            "healthy": len(health_report["healthy"]),
            "stale": len(health_report["stale"]),
            "stuck": len(health_report["stuck"])
        },
        "details": health_report,
        "recommendations": _generate_session_recommendations(health_report)
    }

def _generate_session_recommendations(health_report: Dict) -> List[str]:
    """Generate recommendations for session management"""
    recommendations = []
    
    if health_report["stale"]:
        recommendations.append(
            f"Check {len(health_report['stale'])} stale sessions - AI may need assistance"
        )
    
    if health_report["stuck"]:
        recommendations.append(
            f"Review {len(health_report['stuck'])} long-running sessions for potential issues"
        )
    
    return recommendations
```

## Security and Access Control

### 1. Session Validation

```python
async def validate_session_access(session_id: str, client_identifier: str) -> bool:
    """Validate that client has access to session"""
    session = work_sessions.get(session_id)
    if not session:
        return False
    
    # For now, any client can access any session
    # In production, implement proper access control
    return True

async def validate_task_access(task_id: str, client_identifier: str) -> bool:
    """Validate that client can work on task"""
    # Implement task access control
    # Could check:
    # - Task assignment
    # - Client capabilities vs task requirements
    # - Security clearance
    return True
```

### 2. Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Rate limiting for MCP calls
rate_limits = defaultdict(list)
RATE_LIMIT_WINDOW = timedelta(minutes=1)
MAX_CALLS_PER_MINUTE = 60

async def check_rate_limit(client_id: str) -> bool:
    """Check if client is within rate limits"""
    now = datetime.now()
    
    # Clean old entries
    rate_limits[client_id] = [
        timestamp for timestamp in rate_limits[client_id]
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limits[client_id]) >= MAX_CALLS_PER_MINUTE:
        return False
    
    # Add current call
    rate_limits[client_id].append(now)
    return True
```

## Best Practices for AI Clients

### 1. Session Management
- Always start a session before working on a task
- Complete or abandon sessions properly
- Don't keep sessions open unnecessarily

### 2. Progress Reporting
- Report progress at meaningful milestones
- Include metrics when they change significantly
- Mark criteria as completed when achieved

### 3. Insight Reporting
- Categorize insights appropriately
- Mark vision-affecting insights
- Include actionable recommendations

### 4. Error Handling
- Report blockers promptly
- Include severity and suggested resolutions
- Update task status when blocked

### 5. Completion
- Summarize work done
- List all deliverables
- Report final metric values
- Suggest next steps

## Example Integration Patterns

### Pattern 1: Simple Task Execution

```python
# Minimal integration for basic task work
session = await start_work_session(task_id, "my_ai")
await report_progress(session["session_id"], "Completed task", 100)
await complete_work_session(session["session_id"], "Task done")
```

### Pattern 2: Progressive Reporting

```python
# Detailed progress tracking
session = await start_work_session(task_id, "cursor")

# Multiple progress updates
for step in range(5):
    await report_progress(
        session["session_id"],
        f"Completed step {step + 1}",
        (step + 1) * 20
    )

# Report insights discovered
await report_insight(
    session["session_id"],
    "Found performance bottleneck",
    category="performance",
    affects_vision=True
)

# Complete with metrics
await complete_work_session(
    session["session_id"],
    "Optimized performance",
    metrics_achieved={"response_time": 200}
)
```

### Pattern 3: Collaborative Work

```python
# Multiple AIs working on related tasks
cursor_session = await start_work_session(task1_id, "cursor")
claude_session = await start_work_session(task2_id, "claude")

# Cursor does implementation
await report_progress(cursor_session["session_id"], "Implementation complete", 100)

# Claude does documentation
await report_progress(claude_session["session_id"], "Documentation complete", 100)

# Complete both
await complete_work_session(cursor_session["session_id"], "Code implemented")
await complete_work_session(claude_session["session_id"], "Docs written")
```