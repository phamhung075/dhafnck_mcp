"""Enhanced Workflow Hint System - Autonomous AI guidance with multi-project awareness and conflict detection"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class WorkflowHintEnhancer:
    """Enhanced workflow guidance for autonomous AI operation across multiple projects"""
    
    def __init__(self):
        self.workflow_rules = self._load_workflow_rules()
        self.autonomous_rules = self._load_autonomous_operation_rules()
        self.conflict_resolver = ConflictResolver()
        self.schema_validator = ResponseSchemaValidator()
        self.multi_project_coordinator = MultiProjectCoordinator()
    
    def enhance_task_response(self, 
                             response: Dict[str, Any], 
                             action: str,
                             request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced response processing with validation, conflict detection, and autonomous guidance"""
        
        # Step 1: Validate response schema
        validation_result = self.schema_validator.validate_response(response, action)
        if not validation_result["valid"]:
            response["schema_validation"] = validation_result
        
        # Step 2: Handle errors with enhanced analysis
        if not response.get("success"):
            return self._enhance_error_response_v2(response, action, request_params)
        
        # Step 3: Extract task context with multi-project awareness
        task_context = self._extract_task_context(response, request_params)
        if not task_context:
            return response
        
        # Step 4: Generate autonomous workflow guidance
        response["workflow_guidance"] = self._generate_autonomous_guidance(task_context, action, request_params)
        
        # Step 5: Add multi-project coordination
        response["autonomous_coordination"] = self.multi_project_coordinator.analyze_context(task_context, action)
        
        # Step 6: Detect and resolve conflicts
        conflicts = self.conflict_resolver.detect_conflicts(response)
        if conflicts:
            response["conflict_resolution"] = self.conflict_resolver.resolve_conflicts(conflicts)
        
        # Step 7: Add autonomous decision schema
        response["autonomous_schema"] = self._generate_decision_schema(task_context, action)
        
        return response
    
    def _generate_autonomous_guidance(self, task_context: Dict[str, Any], action: str, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate autonomous workflow guidance with multi-project awareness"""
        
        state = self._analyze_enhanced_state(task_context)
        
        guidance = {
            "current_state": state,
            "autonomous_rules": self._get_autonomous_rules(state, action),
            "decision_matrix": self._generate_decision_matrix(state, task_context),
            "next_actions": self._suggest_autonomous_actions(state, task_context),
            "multi_project_context": self._analyze_multi_project_context(task_context),
            "priority_guidance": self._generate_priority_guidance(state, task_context),
            "conflict_prevention": self._generate_conflict_prevention_rules(state),
            "hints": self._generate_autonomous_hints(state, task_context, action),
            "warnings": self._check_autonomous_warnings(state, task_context),
            "examples": self._get_autonomous_examples(state, action, task_context),
            "validation_schema": self._get_validation_schema(action)
        }
        
        # Add autonomous progression rules
        guidance["autonomous_progression"] = self._generate_autonomous_progression_rules(state)
        
        # Add cross-project dependency analysis
        guidance["dependency_analysis"] = self._analyze_cross_project_dependencies(task_context)
        
        return guidance
    
    def _extract_task_context(self, response: Dict[str, Any], request_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract comprehensive task context with multi-project awareness"""
        
        # Extract task from various response formats
        task = None
        if "task" in response:
            task = response["task"]
        elif "tasks" in response and response["tasks"]:
            task = response["tasks"][0]
        elif "data" in response and response["data"] and "task" in response["data"]:
            task = response["data"]["task"]
        
        if not task:
            return None
        
        # Enhance with request context
        context = {
            "task": task,
            "project_id": request_params.get("project_id") or task.get("project_id"),
            "git_branch_id": request_params.get("git_branch_id") or task.get("git_branch_id"),
            "user_context": request_params.get("user_id", "autonomous_ai"),
            "action_context": request_params,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        
        return context
    
    def _analyze_enhanced_state(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced state analysis with autonomous operation focus"""
        
        task = task_context["task"]
        
        # Basic state analysis
        base_state = self._analyze_task_state(task)
        
        # Enhanced autonomous state analysis
        enhanced_state = {
            **base_state,
            "autonomous_ready": self._check_autonomous_readiness(task, task_context),
            "multi_project_impact": self._assess_multi_project_impact(task_context),
            "decision_confidence": self._calculate_decision_confidence(task, task_context),
            "switching_cost": self._calculate_context_switching_cost(task_context),
            "priority_score": self._calculate_priority_score(task, task_context),
            "blocking_others": self._check_if_blocking_others(task, task_context),
            "resource_requirements": self._analyze_resource_requirements(task),
            "completion_risk": self._assess_completion_risk(task, task_context)
        }
        
        return enhanced_state
    
    def _get_autonomous_rules(self, state: Dict[str, Any], action: str) -> List[Dict[str, Any]]:
        """Get autonomous operation rules with conflict prevention"""
        
        rules = []
        
        # Core autonomous operation rules
        rules.append({
            "rule_id": "AUTO_001",
            "type": "autonomous_operation",
            "priority": "critical",
            "condition": "always",
            "rule": "🤖 AUTONOMOUS: AI must validate all decisions against multi-project context",
            "enforcement": "mandatory",
            "conflict_resolution": "defer_to_higher_priority_project"
        })
        
        rules.append({
            "rule_id": "AUTO_002", 
            "type": "context_preservation",
            "priority": "high",
            "condition": "progress > 70%",
            "rule": "🔄 CONTEXT: Tasks >70% complete take priority unless critical emergency",
            "enforcement": "mandatory",
            "conflict_resolution": "complete_current_before_switching"
        })
        
        rules.append({
            "rule_id": "AUTO_003",
            "type": "dependency_resolution", 
            "priority": "high",
            "condition": "has_dependencies",
            "rule": "🔗 DEPENDENCIES: Blocking tasks must be prioritized over non-blocking",
            "enforcement": "mandatory",
            "conflict_resolution": "dependency_chain_analysis"
        })
        
        # Phase-specific autonomous rules
        if state["phase"] == "not_started":
            rules.append({
                "rule_id": "AUTO_004",
                "type": "initiation",
                "priority": "medium",
                "rule": "🚀 START: Autonomous agents must begin work immediately after assignment",
                "enforcement": "recommended",
                "auto_action": "update_status_to_in_progress"
            })
        
        elif state["phase"] in ["analysis", "implementation"]:
            rules.append({
                "rule_id": "AUTO_005", 
                "type": "progress_tracking",
                "priority": "medium",
                "rule": "📊 PROGRESS: Update progress every 25% completion or 30 minutes",
                "enforcement": "recommended",
                "auto_action": "report_progress_update"
            })
        
        elif state["phase"] == "finalizing":
            rules.append({
                "rule_id": "AUTO_006",
                "type": "completion",
                "priority": "high", 
                "rule": "✅ COMPLETION: All subtasks and context must be complete before finishing",
                "enforcement": "mandatory",
                "auto_action": "validate_completion_readiness"
            })
        
        return rules
    
    def _generate_decision_matrix(self, state: Dict[str, Any], task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate autonomous decision matrix for AI agents"""
        
        task = task_context["task"]
        
        matrix = {
            "decision_framework": "autonomous_multi_project",
            "priority_factors": {
                "business_priority": self._get_business_priority_score(task),
                "completion_preservation": 100 if state["progress"] > 70 else 0,
                "dependency_impact": self._calculate_dependency_impact(task, task_context),
                "urgency_score": self._calculate_urgency_score(task),
                "resource_efficiency": self._calculate_resource_efficiency(task, task_context)
            },
            "decision_thresholds": {
                "switch_task_threshold": 150,  # Combined score needed to switch tasks
                "emergency_override": 200,     # Score that overrides all other rules
                "completion_protection": 70    # Progress % that protects task from switching
            },
            "autonomous_actions": self._generate_autonomous_action_recommendations(state, task_context),
            "conflict_resolution_order": [
                "emergency_override",
                "completion_preservation", 
                "dependency_blocking",
                "business_priority",
                "resource_efficiency"
            ]
        }
        
        return matrix
    
    def _suggest_autonomous_actions(self, state: Dict[str, Any], task_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest specific autonomous actions with executable parameters"""
        
        actions = []
        task = task_context["task"]
        task_id = task.get("id", "UNKNOWN")
        
        # Immediate action based on state
        if state["autonomous_ready"] and state["phase"] == "not_started":
            actions.append({
                "action_id": "AUTO_START",
                "priority": "immediate",
                "action": "Begin autonomous work",
                "tool": "manage_task",
                "params": {
                    "action": "update",
                    "task_id": task_id,
                    "status": "in_progress", 
                    "details": "Autonomous AI agent beginning work"
                },
                "reason": "Task is ready for autonomous execution",
                "confidence": state["decision_confidence"],
                "execution_time": "now"
            })
        
        elif state["phase"] in ["analysis", "implementation"] and state.get("time_since_update", 0) > 1800:
            actions.append({
                "action_id": "AUTO_PROGRESS",
                "priority": "high",
                "action": "Report autonomous progress",
                "tool": "manage_hierarchical_context",
                "params": {
                    "action": "add_progress",
                    "level": "task",
                    "context_id": task_id,
                    "content": f"Autonomous progress update - {state['progress']}% complete",
                    "agent": "autonomous_ai"
                },
                "reason": "Progress update required for autonomous operation",
                "confidence": 95,
                "execution_time": "within_5_minutes"
            })
        
        elif state["can_complete"] and state["phase"] == "finalizing":
            actions.append({
                "action_id": "AUTO_COMPLETE",
                "priority": "high",
                "action": "Complete task autonomously",
                "tool": "manage_task",
                "params": {
                    "action": "complete",
                    "task_id": task_id,
                    "completion_summary": "Task completed by autonomous AI agent",
                    "testing_notes": "Autonomous validation completed"
                },
                "reason": "Task meets all completion criteria",
                "confidence": state["decision_confidence"],
                "execution_time": "now"
            })
        
        # Multi-project coordination actions
        if state.get("blocking_others"):
            actions.append({
                "action_id": "AUTO_PRIORITIZE",
                "priority": "critical",
                "action": "Prioritize blocking task",
                "reason": f"Task is blocking {len(state['blocking_others'])} other tasks",
                "affected_tasks": state["blocking_others"],
                "confidence": 100,
                "execution_time": "immediate"
            })
        
        return actions
    
    def _analyze_task_state(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current task state"""
        
        status = task.get("status", "todo")
        progress = task.get("completion_percentage", 0)
        has_context = task.get("context_id") is not None
        subtasks = task.get("subtasks", [])
        
        # Determine workflow phase
        if status == "todo":
            phase = "not_started"
        elif status == "in_progress":
            if progress < 25:
                phase = "analysis"
            elif progress < 75:
                phase = "implementation"
            else:
                phase = "finalizing"
        elif status == "review":
            phase = "review"
        elif status == "done":
            phase = "completed"
        else:
            phase = "unknown"
        
        # Check subtask status - handle both dict objects and string IDs
        subtasks_complete = 0
        for s in subtasks:
            if isinstance(s, dict) and s.get("status") == "done":
                subtasks_complete += 1
            elif isinstance(s, str):
                # For string IDs, we can't determine status without repository access
                # This is a temporary fix - ideally subtasks should be enriched with full data
                continue
        
        return {
            "phase": phase,
            "status": status,
            "progress": progress,
            "has_context": has_context,
            "has_subtasks": len(subtasks) > 0,
            "subtasks_total": len(subtasks),
            "subtasks_complete": subtasks_complete,
            "can_complete": has_context and (not subtasks or subtasks_complete == len(subtasks)),
            "time_since_update": self._get_time_since_update(task)
        }
    
    def _get_applicable_rules(self, state: Dict[str, Any], action: str) -> List[str]:
        """Get rules applicable to current state and action"""
        
        rules = []
        
        # Universal rules
        rules.append("📝 Update context/progress regularly (every 30 min)")
        
        # Phase-specific rules
        if state["phase"] == "not_started":
            rules.append("🚀 Must update status to 'in_progress' to begin work")
            rules.append("📋 Consider breaking into subtasks if complex")
        
        elif state["phase"] in ["analysis", "implementation"]:
            rules.append("💡 Report insights and blockers as you find them")
            rules.append("📊 Update progress percentage as you complete parts")
        
        elif state["phase"] == "finalizing":
            rules.append("✅ Context update required before completion")
            rules.append("📝 Completion requires 'completion_summary' parameter")
            if state["has_subtasks"] and state["subtasks_complete"] < state["subtasks_total"]:
                rules.append("❌ All subtasks must be complete before parent task")
        
        # Action-specific rules
        if action == "complete":
            rules.append("🎯 Must provide completion_summary")
            if not state["has_context"]:
                rules.append("⚠️ BLOCKED: Update context first!")
        
        return rules
    
    def _suggest_next_actions(self, state: Dict[str, Any], task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest next actions based on current state"""
        
        actions = []
        task_id = task.get("id", "TASK_ID")
        
        if state["phase"] == "not_started":
            actions.append({
                "priority": "high",
                "action": "Start the task",
                "tool": "manage_task",
                "params": {
                    "action": "update",
                    "task_id": task_id,
                    "status": "in_progress",
                    "work_notes": "Starting analysis and planning"
                },
                "reason": "Task needs to be marked as in progress"
            })
        
        elif state["phase"] in ["analysis", "implementation"]:
            # Suggest progress update if stale
            if state["time_since_update"] > 1800:  # 30 minutes
                actions.append({
                    "priority": "high",
                    "action": "Update progress",
                    "tool": "report_progress",
                    "params": {
                        "task_id": task_id,
                        "progress_type": "implementation",
                        "description": "Describe what you've done",
                        "percentage_complete": state["progress"] + 10
                    },
                    "reason": "No updates in 30+ minutes"
                })
            
            # Suggest subtask work if applicable
            if state["has_subtasks"] and state["subtasks_complete"] < state["subtasks_total"]:
                actions.append({
                    "priority": "medium",
                    "action": "Work on subtasks",
                    "tool": "manage_subtask",
                    "params": {
                        "action": "list",
                        "task_id": task_id
                    },
                    "reason": f"{state['subtasks_total'] - state['subtasks_complete']} subtasks remaining"
                })
        
        elif state["phase"] == "finalizing":
            if state["can_complete"]:
                actions.append({
                    "priority": "high",
                    "action": "Complete the task",
                    "tool": "complete_task_with_update",
                    "params": {
                        "task_id": task_id,
                        "completion_summary": "Describe what was accomplished",
                        "testing_notes": "How it was tested (optional)",
                        "next_recommendations": ["Future improvements (optional)"]
                    },
                    "reason": "Task is ready for completion"
                })
            else:
                if not state["has_context"]:
                    actions.append({
                        "priority": "critical",
                        "action": "Update context first",
                        "tool": "quick_task_update",
                        "params": {
                            "task_id": task_id,
                            "what_i_did": "Summary of work done",
                            "progress_percentage": 100
                        },
                        "reason": "Context update required before completion"
                    })
        
        return actions
    
    def _generate_contextual_hints(self, state: Dict[str, Any], task: Dict[str, Any], action: str) -> List[str]:
        """Generate helpful hints based on context"""
        
        hints = []
        
        # Phase-based hints
        phase_hints = {
            "not_started": "💡 Begin by understanding the requirements and planning your approach",
            "analysis": "🔍 Focus on understanding the problem before implementing",
            "implementation": "🛠️ Remember to test as you build",
            "finalizing": "✨ Review your work and ensure all requirements are met",
            "review": "👀 Address any feedback before marking as done"
        }
        
        if state["phase"] in phase_hints:
            hints.append(phase_hints[state["phase"]])
        
        # Stale task hint
        if state["time_since_update"] > 1800:
            hints.append(f"⏰ Last update was {state['time_since_update'] // 60} minutes ago - consider updating progress")
        
        # Subtask hints
        if state["has_subtasks"]:
            remaining = state["subtasks_total"] - state["subtasks_complete"]
            if remaining > 0:
                hints.append(f"📋 {remaining} subtask(s) need completion")
            else:
                hints.append("✅ All subtasks complete - parent task can be completed")
        
        # Vision hints
        if task.get("vision", {}).get("strategic_importance") == "high":
            hints.append("⭐ High strategic importance - ensure vision alignment")
        
        # Action-specific hints
        if action == "next":
            hints.append("👉 Ready to start? Update status to 'in_progress' first")
        elif action == "complete" and not state["can_complete"]:
            hints.append("❌ Cannot complete yet - check the warnings")
        
        return hints
    
    def _check_warnings(self, state: Dict[str, Any], task: Dict[str, Any]) -> List[str]:
        """Check for potential issues and warnings"""
        
        warnings = []
        
        # Completion blockers
        if state["phase"] == "finalizing" or state["status"] == "in_progress" and state["progress"] > 90:
            if not state["has_context"]:
                warnings.append("⚠️ Context not updated - required for completion")
            
            if state["has_subtasks"] and state["subtasks_complete"] < state["subtasks_total"]:
                warnings.append(f"⚠️ {state['subtasks_total'] - state['subtasks_complete']} subtasks incomplete - must finish first")
        
        # Stale task warning
        if state["time_since_update"] > 3600:  # 1 hour
            warnings.append("⏰ Task hasn't been updated in over an hour")
        
        # Low progress warning
        if state["status"] == "in_progress" and state["progress"] == 0:
            warnings.append("📊 Task is in progress but shows 0% completion")
        
        return warnings
    
    def _get_relevant_examples(self, state: Dict[str, Any], action: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant example commands"""
        
        task_id = task.get("id", "TASK_ID")
        examples = {}
        
        if state["phase"] == "not_started":
            examples["start_task"] = {
                "description": "Begin working on the task",
                "command": f"manage_task(action='update', task_id='{task_id}', status='in_progress', work_notes='Starting implementation')"
            }
        
        if state["phase"] in ["analysis", "implementation"]:
            examples["update_progress"] = {
                "description": "Report progress",
                "command": f"report_progress(task_id='{task_id}', progress_type='implementation', description='Added feature X', percentage_complete={state['progress'] + 25})"
            }
        
        if state["can_complete"]:
            examples["complete_task"] = {
                "description": "Complete the task",
                "command": f"complete_task_with_update(task_id='{task_id}', completion_summary='Implemented all features', testing_notes='All tests pass')"
            }
        elif state["phase"] == "finalizing" and not state["has_context"]:
            examples["update_context_first"] = {
                "description": "Update context before completing",
                "command": f"quick_task_update(task_id='{task_id}', what_i_did='Completed all implementation', progress_percentage=100)"
            }
        
        return examples
    
    def _enhance_error_response(self, response: Dict[str, Any], action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance error responses with helpful guidance"""
        
        error = response.get("error", "Unknown error")
        
        # Add resolution guidance
        response["resolution_guidance"] = {
            "error_summary": error,
            "likely_cause": self._diagnose_error(error, action, params),
            "resolution_steps": self._get_resolution_steps(error, action),
            "alternative_approaches": self._suggest_alternatives(error, action),
            "examples": self._get_error_resolution_examples(error, action)
        }
        
        return response
    
    def _get_progress_indicator(self, state: Dict[str, Any]) -> str:
        """Generate visual progress indicator"""
        
        progress = state["progress"]
        filled = int(progress / 10)
        empty = 10 - filled
        
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {progress}%"
    
    def _get_time_since_update(self, task: Dict[str, Any]) -> int:
        """Get seconds since last update"""
        
        last_update = task.get("updated_at")
        if not last_update:
            return 0
        
        try:
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            
            time_diff = datetime.now(timezone.utc) - last_update.replace(tzinfo=None)
            return int(time_diff.total_seconds())
        except:
            return 0
    
    def _load_workflow_rules(self) -> Dict[str, Any]:
        """Load workflow rules configuration"""
        
        # Default rules - would normally load from config
        return {
            "update_interval": 1800,  # 30 minutes
            "require_context_for_completion": True,
            "require_subtask_completion": True,
            "phases": {
                "not_started": {
                    "allowed_actions": ["update", "create_subtask"],
                    "required_fields": ["status", "work_notes"]
                },
                "implementation": {
                    "allowed_actions": ["update", "report_progress", "create_subtask"],
                    "reminder_interval": 1800
                },
                "finalizing": {
                    "allowed_actions": ["update", "complete"],
                    "required_fields": ["completion_summary"]
                }
            }
        }
    
    def _diagnose_error(self, error: str, action: str, params: Dict[str, Any]) -> str:
        """Diagnose likely cause of error"""
        
        if "context must be updated" in error.lower():
            return "Task context is outdated or missing"
        elif "missing required field" in error.lower():
            return f"Required parameter not provided for {action}"
        elif "subtasks must be completed" in error.lower():
            return "Parent task has incomplete subtasks"
        else:
            return "Check error message for specific requirements"
    
    def _get_resolution_steps(self, error: str, action: str) -> List[str]:
        """Get steps to resolve the error"""
        
        steps = []
        
        if "context must be updated" in error.lower():
            steps.extend([
                "1. Update task context using quick_task_update",
                "2. Ensure progress percentage is accurate",
                "3. Retry the completion"
            ])
        elif "subtasks must be completed" in error.lower():
            steps.extend([
                "1. List subtasks to see which are incomplete",
                "2. Complete all remaining subtasks",
                "3. Then complete the parent task"
            ])
        
        return steps
    
    def _suggest_alternatives(self, error: str, action: str) -> List[str]:
        """Suggest alternative approaches"""
        
        alternatives = []
        
        if action == "complete" and "context" in error.lower():
            alternatives.append("Use complete_task_with_update to update context and complete in one step")
        
        return alternatives
    
    def _get_error_resolution_examples(self, error: str, action: str) -> Dict[str, Any]:
        """Get examples to resolve the error"""
        
        examples = {}
        
        if "context must be updated" in error.lower():
            examples["fix_context"] = {
                "description": "Update context first",
                "command": "quick_task_update(task_id='123', what_i_did='Completed implementation', progress_percentage=100)"
            }
        
        return examples
    
    # Enhancement methods for specific actions
    
    def _enhance_get_task_response(self, response: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance get/next task response"""
        
        if task.get("status") == "todo":
            response["workflow_guidance"]["quick_start"] = {
                "message": "Ready to begin? Here's how to start:",
                "steps": [
                    "1. Review task requirements",
                    "2. Update status to 'in_progress'",
                    "3. Break into subtasks if needed",
                    "4. Report initial progress"
                ]
            }
        
        return response
    
    def _enhance_update_response(self, response: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance update response"""
        
        response["workflow_guidance"]["update_confirmation"] = {
            "message": "✅ Task updated successfully",
            "next_reminder": "Remember to update again within 30 minutes",
            "progress_tip": "Use report_progress for quick updates"
        }
        
        return response
    
    def _enhance_complete_response(self, response: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance completion response"""
        
        response["workflow_guidance"]["completion_confirmation"] = {
            "message": "🎉 Task completed successfully!",
            "next_actions": [
                {"action": "Get next task", "command": "manage_task(action='next')"},
                {"action": "Review completed work", "command": "manage_task(action='list', status='done')"}
            ]
        }
        
        return response
    
    def _enhance_list_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance list response"""
        
        tasks = response.get("tasks", [])
        if tasks:
            summary = {
                "total": len(tasks),
                "by_status": {},
                "need_attention": []
            }
            
            for task in tasks:
                status = task.get("status", "unknown")
                summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
                
                # Check for tasks needing attention
                if status == "in_progress" and task.get("completion_percentage", 0) == 0:
                    summary["need_attention"].append({
                        "task_id": task.get("id"),
                        "reason": "In progress but 0% complete"
                    })
            
            response["workflow_guidance"]["summary"] = summary
        
        return response

    # New autonomous operation helper methods
    
    def _load_autonomous_operation_rules(self) -> Dict[str, Any]:
        """Load autonomous operation rules for multi-project coordination"""
        return {
            "priority_matrix": {
                "critical": 100,
                "high": 75,
                "medium": 50,
                "low": 25
            },
            "context_switching_cost": {
                "progress_0_25": 10,
                "progress_26_50": 25,
                "progress_51_75": 50,
                "progress_76_100": 100
            },
            "autonomous_thresholds": {
                "auto_start": True,
                "auto_progress_updates": True,
                "auto_completion": True,
                "context_switch_threshold": 150,
                "emergency_override": 200
            },
            "multi_project_rules": {
                "max_projects_per_agent": 3,
                "project_priority_respect": True,
                "dependency_chain_analysis": True,
                "resource_contention_detection": True
            }
        }
    
    def _check_autonomous_readiness(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> bool:
        """Check if task is ready for autonomous execution"""
        requirements = [
            task.get("title") is not None,
            task.get("description") is not None,
            task_context.get("git_branch_id") is not None,
            task.get("status") in ["todo", "in_progress"]
        ]
        return all(requirements)
    
    def _assess_multi_project_impact(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess impact across multiple projects"""
        return {
            "cross_project_dependencies": 0,  # Would query actual dependencies
            "resource_conflicts": [],
            "priority_conflicts": [],
            "coordination_required": False
        }
    
    def _calculate_decision_confidence(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> int:
        """Calculate confidence score for autonomous decisions"""
        confidence = 100
        
        # Reduce confidence for incomplete information
        if not task.get("description"):
            confidence -= 20
        if not task.get("estimated_effort"):
            confidence -= 15
        if not task_context.get("project_id"):
            confidence -= 25
        
        return max(0, confidence)
    
    def _calculate_context_switching_cost(self, task_context: Dict[str, Any]) -> int:
        """Calculate cost of switching to this task"""
        task = task_context["task"]
        progress = task.get("completion_percentage", 0)
        
        if progress < 25:
            return 10
        elif progress < 50:
            return 25
        elif progress < 75:
            return 50
        else:
            return 100
    
    def _calculate_priority_score(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> int:
        """Calculate overall priority score for autonomous decision making"""
        priority_map = {"critical": 100, "high": 75, "medium": 50, "low": 25}
        base_score = priority_map.get(task.get("priority", "medium"), 50)
        
        # Adjust for dependencies
        if task.get("dependencies"):
            base_score += 25
        
        # Adjust for urgency
        due_date = task.get("due_date")
        if due_date:
            # Would calculate urgency based on due date
            base_score += 10
        
        return base_score
    
    def _check_if_blocking_others(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> List[str]:
        """Check if this task is blocking other tasks"""
        # This would query the actual dependency system
        return []
    
    def _analyze_resource_requirements(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource requirements for the task"""
        return {
            "estimated_effort": task.get("estimated_effort", "unknown"),
            "complexity": "medium",  # Would be calculated based on task analysis
            "required_skills": [],
            "external_dependencies": []
        }
    
    def _assess_completion_risk(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk factors for task completion"""
        return {
            "risk_level": "low",
            "blocking_factors": [],
            "missing_requirements": [],
            "completion_probability": 85
        }
    
    def _get_business_priority_score(self, task: Dict[str, Any]) -> int:
        """Get business priority score for decision matrix"""
        priority_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
        return priority_scores.get(task.get("priority", "medium"), 50)
    
    def _calculate_dependency_impact(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> int:
        """Calculate impact of task dependencies"""
        dependencies = task.get("dependencies", [])
        if not dependencies:
            return 0
        
        # Calculate impact based on number and type of dependencies
        impact = len(dependencies) * 25
        return min(impact, 100)
    
    def _calculate_urgency_score(self, task: Dict[str, Any]) -> int:
        """Calculate urgency score based on due date and other factors"""
        due_date = task.get("due_date")
        if not due_date:
            return 25
        
        # Would calculate based on actual due date proximity
        return 50
    
    def _calculate_resource_efficiency(self, task: Dict[str, Any], task_context: Dict[str, Any]) -> int:
        """Calculate resource efficiency score"""
        # Base efficiency score
        efficiency = 75
        
        # Adjust based on estimated effort
        effort = task.get("estimated_effort", "")
        if "hour" in effort.lower():
            efficiency += 10  # Quick tasks are more efficient
        elif "week" in effort.lower():
            efficiency -= 10  # Long tasks less efficient for context switching
        
        return efficiency
    
    def _generate_autonomous_action_recommendations(self, state: Dict[str, Any], task_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate autonomous action recommendations"""
        recommendations = []
        
        if state["autonomous_ready"]:
            recommendations.append({
                "action": "execute_autonomously",
                "confidence": state["decision_confidence"],
                "estimated_duration": "auto_calculated"
            })
        
        return recommendations
    
    def _analyze_multi_project_context(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context across multiple projects"""
        return {
            "current_project": task_context.get("project_id"),
            "cross_project_impact": "none",
            "coordination_needed": False,
            "resource_sharing": []
        }
    
    def _generate_priority_guidance(self, state: Dict[str, Any], task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate priority guidance for autonomous operation"""
        return {
            "priority_level": state.get("priority_score", 50),
            "context_switch_recommendation": "continue" if state["progress"] > 70 else "evaluate",
            "autonomous_decision": "proceed" if state["autonomous_ready"] else "wait_for_clarification"
        }
    
    def _generate_conflict_prevention_rules(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rules to prevent conflicts in autonomous operation"""
        return [
            {
                "rule": "Respect task completion thresholds",
                "condition": "progress > 70%",
                "action": "complete_before_switching"
            },
            {
                "rule": "Honor dependency chains",
                "condition": "has_blocking_dependencies",
                "action": "resolve_dependencies_first"
            },
            {
                "rule": "Validate cross-project impact",
                "condition": "multi_project_operation",
                "action": "check_resource_conflicts"
            }
        ]
    
    def _generate_autonomous_hints(self, state: Dict[str, Any], task_context: Dict[str, Any], action: str) -> List[str]:
        """Generate hints specific to autonomous operation"""
        hints = []
        
        if state["autonomous_ready"]:
            hints.append("🤖 AUTONOMOUS: Ready for independent execution")
        
        if state["progress"] > 70:
            hints.append("🔄 COMPLETION: High progress - consider finishing before switching tasks")
        
        if state.get("blocking_others"):
            hints.append(f"🚫 BLOCKING: This task is blocking {len(state['blocking_others'])} other tasks")
        
        return hints
    
    def _check_autonomous_warnings(self, state: Dict[str, Any], task_context: Dict[str, Any]) -> List[str]:
        """Check for warnings specific to autonomous operation"""
        warnings = []
        
        if not state["autonomous_ready"]:
            warnings.append("⚠️ AUTONOMOUS: Task not ready for independent execution")
        
        if state["decision_confidence"] < 70:
            warnings.append(f"⚠️ CONFIDENCE: Low decision confidence ({state['decision_confidence']}%)")
        
        if state.get("completion_risk", {}).get("risk_level") == "high":
            warnings.append("⚠️ RISK: High completion risk detected")
        
        return warnings
    
    def _get_autonomous_examples(self, state: Dict[str, Any], action: str, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get examples specific to autonomous operation"""
        task_id = task_context["task"].get("id", "TASK_ID")
        
        examples = {
            "autonomous_start": {
                "description": "Start autonomous execution",
                "command": f"manage_task(action='update', task_id='{task_id}', status='in_progress', details='Autonomous AI beginning work')"
            },
            "autonomous_progress": {
                "description": "Report autonomous progress",
                "command": f"manage_hierarchical_context(action='add_progress', level='task', context_id='{task_id}', content='Autonomous progress update', agent='ai_agent')"
            },
            "autonomous_complete": {
                "description": "Complete autonomously",
                "command": f"manage_task(action='complete', task_id='{task_id}', completion_summary='Autonomous completion', testing_notes='AI validation complete')"
            }
        }
        
        return examples
    
    def _get_validation_schema(self, action: str) -> Dict[str, Any]:
        """Get validation schema for the action"""
        schemas = {
            "create": {
                "required_fields": ["git_branch_id", "title"],
                "optional_fields": ["description", "priority", "estimated_effort"],
                "validation_rules": ["title_not_empty", "git_branch_id_valid"]
            },
            "update": {
                "required_fields": ["task_id"],
                "optional_fields": ["status", "details", "priority"],
                "validation_rules": ["task_id_exists", "status_valid_transition"]
            },
            "complete": {
                "required_fields": ["task_id", "completion_summary"],
                "optional_fields": ["testing_notes"],
                "validation_rules": ["task_completable", "context_updated"]
            }
        }
        
        return schemas.get(action, {"required_fields": [], "optional_fields": [], "validation_rules": []})
    
    def _generate_autonomous_progression_rules(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rules for autonomous progression"""
        return {
            "auto_start_conditions": ["task_assigned", "requirements_clear", "no_blockers"],
            "auto_progress_triggers": ["time_interval_30min", "milestone_reached", "blocker_resolved"],
            "auto_complete_conditions": ["all_requirements_met", "testing_complete", "context_updated"],
            "context_switch_rules": {
                "never_switch_above": 70,  # Never switch if progress > 70%
                "switch_threshold": 150,   # Combined priority score needed to switch
                "emergency_override": 200  # Emergency tasks override all rules
            }
        }
    
    def _analyze_cross_project_dependencies(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependencies across multiple projects"""
        return {
            "upstream_dependencies": [],
            "downstream_dependencies": [],
            "cross_project_blockers": [],
            "resource_conflicts": [],
            "coordination_requirements": []
        }
    
    def _generate_decision_schema(self, task_context: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Generate decision schema for AI autonomous operation"""
        return {
            "decision_tree": {
                "condition_checks": [
                    {"check": "task_ready", "result": "boolean"},
                    {"check": "no_conflicts", "result": "boolean"},
                    {"check": "resources_available", "result": "boolean"}
                ],
                "decision_paths": {
                    "all_true": "execute_immediately",
                    "task_not_ready": "gather_requirements",
                    "conflicts_exist": "resolve_conflicts_first",
                    "resources_unavailable": "queue_for_later"
                }
            },
            "execution_parameters": {
                "max_execution_time": "auto_calculated",
                "progress_update_interval": 1800,  # 30 minutes
                "completion_validation": "required"
            },
            "error_handling": {
                "retry_attempts": 3,
                "escalation_threshold": "human_intervention_needed",
                "fallback_strategies": ["reduce_scope", "defer_to_human", "partial_completion"]
            }
        }
    
    def _enhance_error_response_v2(self, response: Dict[str, Any], action: str, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced error response with autonomous guidance"""
        
        error = response.get("error", "Unknown error")
        
        # Enhanced resolution guidance
        response["autonomous_error_guidance"] = {
            "error_classification": self._classify_error_for_autonomous_handling(error),
            "autonomous_resolution": self._get_autonomous_error_resolution(error, action),
            "confidence_impact": self._calculate_error_confidence_impact(error),
            "retry_strategy": self._get_autonomous_retry_strategy(error, action),
            "escalation_path": self._get_error_escalation_path(error),
            "alternative_actions": self._get_error_alternative_actions(error, action, request_params)
        }
        
        return response
    
    def _classify_error_for_autonomous_handling(self, error: str) -> Dict[str, Any]:
        """Classify error for autonomous handling"""
        if "context must be updated" in error.lower():
            return {"type": "context_error", "severity": "medium", "auto_resolvable": True}
        elif "subtasks must be completed" in error.lower():
            return {"type": "dependency_error", "severity": "high", "auto_resolvable": True}
        elif "missing required field" in error.lower():
            return {"type": "validation_error", "severity": "medium", "auto_resolvable": False}
        else:
            return {"type": "unknown_error", "severity": "high", "auto_resolvable": False}
    
    def _get_autonomous_error_resolution(self, error: str, action: str) -> Dict[str, Any]:
        """Get autonomous error resolution steps"""
        if "context must be updated" in error.lower():
            return {
                "auto_action": "update_context",
                "steps": ["gather_current_progress", "update_context", "retry_action"],
                "estimated_time": "2_minutes"
            }
        elif "subtasks must be completed" in error.lower():
            return {
                "auto_action": "complete_subtasks",
                "steps": ["list_incomplete_subtasks", "complete_each_subtask", "retry_parent_completion"],
                "estimated_time": "variable"
            }
        else:
            return {
                "auto_action": "escalate_to_human",
                "steps": ["log_error_details", "gather_context", "request_human_intervention"],
                "estimated_time": "immediate"
            }
    
    def _calculate_error_confidence_impact(self, error: str) -> int:
        """Calculate how error impacts decision confidence"""
        if "context must be updated" in error.lower():
            return -20  # Moderate confidence reduction
        elif "subtasks must be completed" in error.lower():
            return -30  # Higher confidence reduction
        else:
            return -50  # Significant confidence reduction
    
    def _get_autonomous_retry_strategy(self, error: str, action: str) -> Dict[str, Any]:
        """Get retry strategy for autonomous operation"""
        return {
            "max_retries": 3,
            "backoff_strategy": "exponential",
            "retry_conditions": ["error_resolved", "context_updated", "dependencies_met"],
            "abort_conditions": ["max_retries_exceeded", "unresolvable_error", "human_intervention_required"]
        }
    
    def _get_error_escalation_path(self, error: str) -> List[str]:
        """Get escalation path for errors"""
        return [
            "autonomous_resolution_attempt",
            "alternative_approach_attempt", 
            "human_notification",
            "task_deferral"
        ]
    
    def _get_error_alternative_actions(self, error: str, action: str, request_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get alternative actions for error scenarios"""
        alternatives = []
        
        if action == "complete" and "context" in error.lower():
            alternatives.append({
                "action": "update_context_then_complete",
                "description": "Update context and complete in sequence",
                "confidence": 90
            })
        
        return alternatives


class ConflictResolver:
    """Detects and resolves conflicts in autonomous AI responses"""
    
    def detect_conflicts(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential conflicts in response"""
        conflicts = []
        
        guidance = response.get("workflow_guidance", {})
        rules = guidance.get("autonomous_rules", [])
        actions = guidance.get("next_actions", [])
        
        # Check for rule conflicts
        for i, rule1 in enumerate(rules):
            for j, rule2 in enumerate(rules[i+1:], i+1):
                if self._rules_conflict(rule1, rule2):
                    conflicts.append({
                        "type": "rule_conflict",
                        "rule1": rule1,
                        "rule2": rule2,
                        "severity": "medium"
                    })
        
        # Check for action conflicts
        for i, action1 in enumerate(actions):
            for j, action2 in enumerate(actions[i+1:], i+1):
                if self._actions_conflict(action1, action2):
                    conflicts.append({
                        "type": "action_conflict",
                        "action1": action1,
                        "action2": action2,
                        "severity": "high"
                    })
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve detected conflicts"""
        resolutions = []
        
        for conflict in conflicts:
            if conflict["type"] == "rule_conflict":
                resolution = self._resolve_rule_conflict(conflict)
            elif conflict["type"] == "action_conflict":
                resolution = self._resolve_action_conflict(conflict)
            else:
                resolution = {"status": "unresolved", "reason": "unknown_conflict_type"}
            
            resolutions.append(resolution)
        
        return {
            "conflicts_detected": len(conflicts),
            "resolutions": resolutions,
            "overall_status": "resolved" if all(r.get("status") == "resolved" for r in resolutions) else "partial"
        }
    
    def _rules_conflict(self, rule1: Dict[str, Any], rule2: Dict[str, Any]) -> bool:
        """Check if two rules conflict"""
        # Example conflict detection logic
        if rule1.get("enforcement") == "mandatory" and rule2.get("enforcement") == "mandatory":
            if rule1.get("priority") != rule2.get("priority"):
                return True
        return False
    
    def _actions_conflict(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> bool:
        """Check if two actions conflict"""
        # Example conflict detection logic
        if action1.get("tool") == action2.get("tool") and action1.get("priority") == action2.get("priority"):
            return True
        return False
    
    def _resolve_rule_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve rule conflict"""
        rule1 = conflict["rule1"]
        rule2 = conflict["rule2"]
        
        # Priority-based resolution
        if rule1.get("priority") == "critical" and rule2.get("priority") != "critical":
            return {"status": "resolved", "chosen_rule": rule1, "reason": "critical_priority"}
        elif rule2.get("priority") == "critical" and rule1.get("priority") != "critical":
            return {"status": "resolved", "chosen_rule": rule2, "reason": "critical_priority"}
        else:
            return {"status": "escalated", "reason": "equal_priority_conflict"}
    
    def _resolve_action_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve action conflict"""
        action1 = conflict["action1"]
        action2 = conflict["action2"]
        
        # Confidence-based resolution
        conf1 = action1.get("confidence", 0)
        conf2 = action2.get("confidence", 0)
        
        if conf1 > conf2:
            return {"status": "resolved", "chosen_action": action1, "reason": "higher_confidence"}
        elif conf2 > conf1:
            return {"status": "resolved", "chosen_action": action2, "reason": "higher_confidence"}
        else:
            return {"status": "escalated", "reason": "equal_confidence"}


class ResponseSchemaValidator:
    """Validates response schemas for consistency"""
    
    def validate_response(self, response: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Validate response against expected schema"""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "schema_version": "autonomous_v1"
        }
        
        # Basic structure validation
        if not isinstance(response, dict):
            validation_result["valid"] = False
            validation_result["errors"].append("Response must be a dictionary")
            return validation_result
        
        # Required fields validation
        required_fields = ["success"]
        for field in required_fields:
            if field not in response:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Success response validation
        if response.get("success"):
            self._validate_success_response(response, action, validation_result)
        else:
            self._validate_error_response(response, action, validation_result)
        
        return validation_result
    
    def _validate_success_response(self, response: Dict[str, Any], action: str, result: Dict[str, Any]):
        """Validate successful response structure"""
        
        # Check for expected data fields based on action
        if action in ["create", "update", "get"] and "task" not in response.get("data", {}):
            result["warnings"].append("Success response missing task data")
        
        if action == "list" and "tasks" not in response:
            result["warnings"].append("List response missing tasks array")
    
    def _validate_error_response(self, response: Dict[str, Any], action: str, result: Dict[str, Any]):
        """Validate error response structure"""
        
        if "error" not in response:
            result["errors"].append("Error response missing error message")
        
        if "autonomous_error_guidance" not in response:
            result["warnings"].append("Error response missing autonomous guidance")


class MultiProjectCoordinator:
    """Coordinates actions across multiple projects"""
    
    def analyze_context(self, task_context: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Analyze multi-project coordination requirements"""
        
        return {
            "coordination_level": "single_project",  # Would analyze actual multi-project context
            "cross_project_impact": "none",
            "resource_sharing_required": False,
            "priority_conflicts": [],
            "recommendations": []
        }