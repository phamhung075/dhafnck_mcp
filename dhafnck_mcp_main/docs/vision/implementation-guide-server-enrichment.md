# Server-Side Vision and Context Enrichment Implementation Guide

## Overview

This guide explains how to enhance the MCP server to automatically provide vision and context to AI clients when they request tasks. The server will enrich all task responses with hierarchical vision alignment and execution context, eliminating the need for AI clients to manage state.

## Core Principle

**Server Enriches → AI Receives → AI Works**

The server automatically:
1. Loads vision hierarchy when tasks are retrieved
2. Includes current context with every task response
3. Tracks AI client interactions for context updates
4. Maintains vision alignment scores and metrics

## Implementation Steps

### Step 1: Enhance Task MCP Controller

Modify the existing `TaskMCPController` to always include context and vision:

```python
# In task_mcp_controller.py - Update default behavior

def register_tools(self, mcp: "FastMCP") -> None:
    """Register enhanced task management tools with vision/context"""
    
    @mcp.tool()
    async def manage_task(
        action: str,
        # ... existing parameters ...
        include_context: bool = True,  # Change default to True
        include_vision: bool = True,    # New parameter
        # ... rest of parameters ...
    ) -> Dict[str, Any]:
        """Enhanced task management with automatic vision/context inclusion"""
        
        # For get, list, search, next actions - always enrich with vision
        if action in ["get", "list", "search", "next"]:
            result = self.manage_task(
                action=action,
                include_context=True,  # Force context inclusion
                # ... other parameters ...
            )
            
            # Enrich with vision data
            if include_vision:
                result = await self._enrich_with_vision(result)
            
            return result
```

### Step 2: Create Vision Enrichment Service

```python
# New file: vision_enrichment_service.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class VisionHierarchy:
    """Complete vision hierarchy for a task"""
    organization_vision: Dict[str, Any]
    project_vision: Dict[str, Any]
    branch_vision: Dict[str, Any]
    task_vision: Dict[str, Any]
    alignment_score: float
    strategic_metrics: Dict[str, Any]

class VisionEnrichmentService:
    """Service to enrich tasks with vision hierarchy"""
    
    def __init__(self, vision_repository, project_repository, branch_repository):
        self._vision_repo = vision_repository
        self._project_repo = project_repository
        self._branch_repo = branch_repository
    
    async def enrich_task_with_vision(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single task with complete vision hierarchy"""
        
        # Load vision hierarchy
        vision_hierarchy = await self._load_vision_hierarchy(
            task["project_id"],
            task["git_branch_id"],
            task["id"]
        )
        
        # Add vision data to task
        task["vision"] = {
            "hierarchy": vision_hierarchy,
            "alignment": {
                "project_alignment": vision_hierarchy.alignment_score,
                "strategic_importance": self._calculate_strategic_importance(task),
                "business_value": task.get("business_value", 0),
                "user_impact": task.get("user_impact", 0)
            },
            "metrics": {
                "kpis": vision_hierarchy.strategic_metrics,
                "progress": self._calculate_vision_progress(task)
            }
        }
        
        # Add AI guidance based on vision
        task["ai_guidance"] = self._generate_ai_guidance(task, vision_hierarchy)
        
        return task
    
    def _generate_ai_guidance(self, task: Dict[str, Any], vision: VisionHierarchy) -> Dict[str, Any]:
        """Generate AI-specific guidance based on vision alignment"""
        return {
            "focus_areas": self._identify_focus_areas(task, vision),
            "success_criteria": vision.task_vision.get("success_criteria", []),
            "innovation_opportunities": vision.branch_vision.get("innovation_priorities", []),
            "constraints": vision.project_vision.get("constraints", []),
            "recommended_approach": self._recommend_approach(task, vision)
        }
```

### Step 3: Enhance Context Response Factory

```python
# Update context_response_factory.py

class ContextResponseFactory:
    """Enhanced factory with vision integration"""
    
    @staticmethod
    def create_unified_context(context_data: Optional[Dict[str, Any]], 
                              vision_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create unified context with vision integration"""
        
        # ... existing context creation ...
        
        if unified_context and vision_data:
            # Add vision section to context
            unified_context["vision"] = {
                "current_objectives": vision_data.get("hierarchy", {}).get("task_vision", {}).get("objectives", []),
                "alignment_score": vision_data.get("alignment", {}).get("project_alignment", 0),
                "strategic_importance": vision_data.get("alignment", {}).get("strategic_importance", "medium"),
                "kpi_progress": vision_data.get("metrics", {}).get("kpis", {}),
                "success_criteria": vision_data.get("ai_guidance", {}).get("success_criteria", [])
            }
            
            # Add vision-aware guidance to progress section
            unified_context["progress"]["vision_guided_next_steps"] = (
                vision_data.get("ai_guidance", {}).get("focus_areas", [])
            )
        
        return unified_context
```

### Step 4: Update Application Facade

```python
# In task_application_facade.py

class TaskApplicationFacade:
    """Enhanced facade with vision enrichment"""
    
    def __init__(self, *args, vision_enrichment_service=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._vision_service = vision_enrichment_service or VisionEnrichmentService()
    
    async def get_next_task(self, include_context: bool = True, 
                           include_vision: bool = True, **kwargs) -> Dict[str, Any]:
        """Get next task with automatic vision and context enrichment"""
        
        # Get base task using existing logic
        result = await self._next_task_use_case.execute(
            user_id=kwargs.get("user_id"),
            project_id=kwargs.get("project_id"),
            git_branch_name=kwargs.get("git_branch_name")
        )
        
        if result["success"] and result.get("task"):
            task = result["task"]
            
            # Always include context for AI clients
            if include_context:
                context_result = await self._context_manager.get_or_create_context(
                    task_id=task["id"]
                )
                if context_result["success"]:
                    task["context_data"] = context_result.get("template_context")
            
            # Enrich with vision
            if include_vision:
                task = await self._vision_service.enrich_task_with_vision(task)
                
                # Merge vision into context if both present
                if task.get("context_data") and task.get("vision"):
                    task["context_data"] = ContextResponseFactory.create_unified_context(
                        task["context_data"],
                        task["vision"]
                    )
            
            # Add AI work session info
            task["ai_work_session"] = {
                "recommended_approach": task.get("ai_guidance", {}).get("recommended_approach"),
                "estimated_duration": task.get("estimated_effort"),
                "required_capabilities": self._identify_required_capabilities(task)
            }
            
            result["task"] = task
        
        return result
```

### Step 5: Create Vision-Aware Response Format

```python
# Example enriched task response structure

{
    "success": true,
    "task": {
        "id": "task_123",
        "title": "Implement caching layer",
        "description": "Add Redis caching for API responses",
        "status": "todo",
        "priority": "high",
        
        # Always included context
        "context_data": {
            "metadata": { ... },
            "objective": { ... },
            "requirements": { ... },
            "technical": { ... },
            "progress": {
                "vision_guided_next_steps": [
                    "Focus on response time optimization (KPI target: <200ms)",
                    "Implement cache invalidation strategy aligned with data consistency requirements"
                ]
            },
            
            # New vision section
            "vision": {
                "current_objectives": [
                    "Reduce API response time by 50%",
                    "Improve system scalability"
                ],
                "alignment_score": 0.85,
                "strategic_importance": "high",
                "kpi_progress": {
                    "response_time_ms": {
                        "current": 450,
                        "target": 200,
                        "trend": "improving"
                    }
                },
                "success_criteria": [
                    "All API endpoints respond in <200ms",
                    "Cache hit ratio >80%",
                    "Zero data inconsistency issues"
                ]
            }
        },
        
        # AI-specific guidance
        "ai_guidance": {
            "focus_areas": [
                "Performance optimization",
                "Cache invalidation patterns",
                "Monitoring and metrics"
            ],
            "success_criteria": [ ... ],
            "innovation_opportunities": [
                "Consider event-driven cache invalidation",
                "Explore edge caching possibilities"
            ],
            "recommended_approach": "Start with read-heavy endpoints, implement monitoring, then expand coverage"
        },
        
        # AI work session info
        "ai_work_session": {
            "recommended_approach": "iterative",
            "estimated_duration": "2-3 hours",
            "required_capabilities": ["backend", "caching", "performance"]
        }
    }
}
```

### Step 6: Configuration Updates

```yaml
# mcp_server_config.yaml

task_management:
  # Always include context and vision for AI clients
  default_include_context: true
  default_include_vision: true
  
  vision_enrichment:
    enabled: true
    cache_ttl_seconds: 300
    
    # AI client detection
    ai_client_patterns:
      - "cursor"
      - "claude"
      - "chatgpt"
      - "gemini"
      - "grok"
    
    # Vision alignment thresholds
    alignment_thresholds:
      high: 0.8
      medium: 0.5
      low: 0.3

context_management:
  # Auto-create context for tasks without one
  auto_create_context: true
  
  # Include vision in context by default
  include_vision_in_context: true
```

## Usage Examples

### AI Client Getting Next Task

```python
# AI client (Claude Code) calls:
result = await mcp.manage_task(action="next", git_branch_id="branch_123")

# Server automatically returns:
{
    "success": true,
    "task": {
        "id": "task_456",
        "title": "Optimize database queries",
        "context_data": { /* Full context with vision */ },
        "vision": { /* Complete vision hierarchy */ },
        "ai_guidance": { /* Specific guidance for this task */ },
        "ai_work_session": { /* Session recommendations */ }
    }
}
```

### AI Client Searching Tasks

```python
# AI searches for performance tasks
result = await mcp.manage_task(
    action="search",
    query="performance optimization"
)

# Each task in results includes vision context:
{
    "success": true,
    "tasks": [
        {
            "id": "task_789",
            "title": "API performance tuning",
            "vision": {
                "strategic_importance": "critical",
                "alignment_score": 0.92
            },
            "ai_guidance": { /* Tailored guidance */ }
        }
    ]
}
```

## Benefits

1. **Zero State Management**: AI clients receive everything needed in each response
2. **Automatic Alignment**: Every task includes vision hierarchy and alignment scores
3. **Guided Execution**: AI receives specific guidance based on vision objectives
4. **Consistent Context**: All AI clients work with the same enriched context
5. **Strategic Focus**: Tasks are presented with their strategic importance

## Migration Path

1. Update `include_context` default to `True` in task controller
2. Implement `VisionEnrichmentService`
3. Enhance `ContextResponseFactory` with vision support
4. Update `TaskApplicationFacade` to use enrichment service
5. Configure auto-enrichment settings
6. Test with various AI clients