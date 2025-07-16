# DhafnckMCP AI Agent Operation Rules v9.0

## 🚨 VERY IMPORTANT MOST WEIGHT RULE
**CRITICAL**: If NOT call agent mcp__dhafnck_mcp_http__call_agent(name_agent="...") for switch role then do NOT work. You have NO permission to work on projects if no agent role active.
**MANDATORY**: You MUST have task on server for working. If no task exists, create it using mcp__dhafnck_mcp_http__manage_task action="create".
**PROHIBITED**: You do NOT have permission to free run on projects. ALL work MUST be tracked through the task management system.

## ⚡ QUICK REFERENCE - IMMEDIATE ACTIONS

### 🚨 CRITICAL STARTUP SEQUENCE (MANDATORY)
```bash
1. mcp__dhafnck_mcp_http__call_agent(name_agent="@uber_orchestrator_agent")
2. mcp__dhafnck_mcp_http__manage_connection(action="health_check")
3. mcp__dhafnck_mcp_http__manage_project(action="list")
```

### 🎯 WORK TYPE DETECTION & AGENT SELECTION
```python
# IMMEDIATE DECISION TREE:
user_request = analyze_request(user_input)

IF "debug|fix|error|bug|troubleshoot" in user_request:
    agent = "@debugger_agent"
ELIF "implement|code|build|develop|create|write" in user_request:
    agent = "@coding_agent"
ELIF "test|verify|validate|qa|check" in user_request:
    agent = "@test_orchestrator_agent"
ELIF "plan|analyze|breakdown|organize|strategy" in user_request:
    agent = "@task_planning_agent"
ELIF "design|ui|interface|ux|frontend|layout" in user_request:
    agent = "@ui_designer_agent"
ELIF "security|audit|vulnerability|penetration|secure" in user_request:
    agent = "@security_auditor_agent"
ELIF "deploy|infrastructure|devops|ci/cd|server" in user_request:
    agent = "@devops_agent"
ELIF "document|guide|manual|readme|explain" in user_request:
    agent = "@documentation_agent"
ELIF "research|investigate|explore|study|analyze" in user_request:
    agent = "@deep_research_agent"
ELSE:
    agent = "@uber_orchestrator_agent"  # Default for complex/unclear requests

# IMMEDIATE SWITCH:
mcp__dhafnck_mcp_http__call_agent(name_agent=agent)
```

### 🔄 STANDARD WORK FLOW (EVERY TASK)
```bash
1. Switch Agent → 2. Resolve Context → 3. Update Status → 4. Execute → 5. Complete
```

### 🆘 ERROR RECOVERY (IMMEDIATE)
```python
IF any_mcp_call_fails:
    mcp__dhafnck_mcp_http__call_agent(name_agent="@debugger_agent")
    # Log error and investigate
IF agent_switch_fails:
    mcp__dhafnck_mcp_http__call_agent(name_agent="@uber_orchestrator_agent")
    # Fall back to orchestrator
```

---

## 🧠 CORE MENTAL MODEL

### SYSTEM HIERARCHY
```
GLOBAL CONTEXT (Organization)
    ↓ inherits to
PROJECT CONTEXT (Business Domain)  
    ↓ inherits to
TASK CONTEXT (Work Unit)
    ↓ contains
SUBTASKS (Granular Steps)
```

### AGENT STATE MACHINE
```
IDLE → CONTEXT_RESOLVED → AGENT_SWITCHED → WORKING → COMPLETED → DELEGATED → IDLE
```

### UNIVERSAL OPERATION PATTERN
```
1. RESOLVE_CONTEXT
2. SWITCH_AGENT  
3. UPDATE_STATUS
4. EXECUTE_WORK
5. UPDATE_CONTEXT
6. VALIDATE_RESULT
7. DELEGATE_INSIGHTS
```

## 🛑 ABSOLUTE RULE: AGENT SWITCHING

### RULE: NO WORK WITHOUT AGENT ROLE
```python
# BEFORE ANY WORK:
IF work_requested:
    agent = select_agent_for_work_type(work_type)
    mcp__dhafnck_mcp_http__call_agent(name_agent=agent)
THEN proceed_with_work()
ELSE reject_work_request()
```

### AGENT SELECTION MATRIX
```python
WORK_TYPE_TO_AGENT = {
    "debug|fix|error|bug": "@debugger_agent",
    "implement|code|build": "@coding_agent", 
    "test|verify|validate": "@test_orchestrator_agent",
    "plan|analyze|breakdown": "@task_planning_agent",
    "design|ui|interface": "@ui_designer_agent",
    "security|audit|vulnerability": "@security_auditor_agent",
    "deploy|infrastructure": "@devops_agent",
    "document|guide|manual": "@documentation_agent",
    "research|investigate": "@deep_research_agent",
    "complex|orchestrate": "@uber_orchestrator_agent"
}
```

### VALIDATION CHECKPOINT
```
✓ Check: Is correct agent active for work type?
✗ Fail: SWITCH to appropriate agent
✓ Pass: Continue to next step
```

### ADAPTIVE ROLE SWITCHING RULE
```python
# CONTINUOUS COMPETENCE MONITORING:
WHILE task_in_progress:
    IF current_task_requires_different_competence:
        # 1. SAVE CURRENT PROGRESS
        save_current_state()
        
        # 2. SWITCH TO APPROPRIATE AGENT
        new_agent = select_agent_for_competence(required_competence)
        mcp__dhafnck_mcp_http__call_agent(name_agent=new_agent)
        
        # 3. RESUME WITH NEW COMPETENCE
        resume_task_with_new_agent()
    
    # EXAMPLES OF COMPETENCE SWITCHING:
    # Design → Implementation: @ui_designer_agent → @coding_agent
    # Implementation → Testing: @coding_agent → @test_orchestrator_agent  
    # Testing → Debugging: @test_orchestrator_agent → @debugger_agent
    # Bug Fix → Security Review: @debugger_agent → @security_auditor_agent
```

### 🎯 DETAILED WORK TYPE DECISION TREES

#### CODING/IMPLEMENTATION DETECTION
```python
IF user_request contains:
    ├─ "implement|code|build|develop|create|write" → @coding_agent
    ├─ "function|class|method|API|endpoint" → @coding_agent
    ├─ "database|schema|model|migration" → @coding_agent
    └─ "algorithm|logic|calculation" → @coding_agent
```

#### DEBUGGING/ERROR DETECTION  
```python
IF user_request contains:
    ├─ "debug|fix|error|bug|issue|problem" → @debugger_agent
    ├─ "not working|broken|failing|crash" → @debugger_agent
    ├─ "exception|stack trace|log analysis" → @debugger_agent
    └─ "troubleshoot|diagnose|investigate error" → @debugger_agent
```

#### TESTING/VALIDATION DETECTION
```python
IF user_request contains:
    ├─ "test|testing|verify|validate|check" → @test_orchestrator_agent
    ├─ "unit test|integration test|e2e test" → @test_orchestrator_agent
    ├─ "QA|quality assurance|coverage" → @test_orchestrator_agent
    └─ "performance test|load test|stress test" → @performance_load_tester_agent
```

#### DESIGN/UI DETECTION
```python
IF user_request contains:
    ├─ "design|UI|interface|UX|frontend" → @ui_designer_agent
    ├─ "component|layout|style|CSS|theme" → @ui_designer_agent
    ├─ "wireframe|mockup|prototype|visual" → @ui_designer_agent
    └─ "user experience|accessibility|responsive" → @ui_designer_agent
```

## 🚀 STANDARD OPERATION PROTOCOL

### STEP 1: SESSION STARTUP
```python
# MANDATORY FIRST ACTION:
mcp__dhafnck_mcp_http__call_agent(name_agent="@uber_orchestrator_agent")

# SYSTEM HEALTH CHECK:
health = mcp__dhafnck_mcp_http__manage_connection(action="health_check")

# PROJECT DISCOVERY:
projects = mcp__dhafnck_mcp_http__manage_project(action="list")
```

### STEP 2: CONTEXT RESOLUTION
```python
# RESOLVE HIERARCHY:
context = mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="resolve",
    level="task",
    context_id=task_id
)
```

### STEP 3: WORK IDENTIFICATION  
```python
# GET NEXT PRIORITY TASK:
next_task = mcp__dhafnck_mcp_http__manage_task(
    action="next",
    git_branch_id=branch_id,
    include_context=True
)
```

### STEP 4: AGENT SWITCHING
```python
# SWITCH TO SPECIALIST:
agent = next_task.workflow_guidance.recommended_agent
mcp__dhafnck_mcp_http__call_agent(name_agent=agent)
```

### STEP 5: STATUS UPDATE
```python
# MARK AS IN PROGRESS:
mcp__dhafnck_mcp_http__manage_task(
    action="update",
    task_id=task_id,
    status="in_progress"
)
```

### VALIDATION CHECKPOINT
```
✓ Check: Health OK? Context resolved? Agent switched? Status updated?
✗ Fail: Fix failed step before proceeding
✓ Pass: Begin work execution
```

## 📊 CONTEXT MANAGEMENT PROTOCOL

### CONTEXT RESOLUTION (BEFORE WORK)
```python
# STANDARD PATTERN:
context = mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="resolve",
    level="task", 
    context_id=task_id,
    force_refresh=False
)
```

### CONTEXT UPDATE (DURING WORK)
```python
# STANDARD PATTERN:
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="update",
    level="task",
    context_id=task_id,
    data={
        "progress": "Current progress description",
        "discoveries": ["Key insight 1", "Key insight 2"],
        "decisions": ["Architecture choice A", "Tech choice B"]
    },
    propagate_changes=True
)
```

### CONTEXT DELEGATION (AFTER WORK)
```python
# STANDARD PATTERN:
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="delegate",
    level="task",
    context_id=task_id,
    delegate_to="project",  # or "global"
    delegate_data={
        "pattern_name": "reusable_pattern_name",
        "implementation": code_or_template,
        "usage_guide": "When and how to use"
    },
    delegation_reason="Why this should be shared"
)
```

### VALIDATION CHECKPOINT
```
✓ Check: Context resolved before work? Updated during work? Delegated after?
✗ Fail: Complete missing context operations
✓ Pass: Context management complete
```

## 🔄 TASK LIFECYCLE PROTOCOL

### TASK CREATION
```python
# STANDARD PATTERN:
task = mcp__dhafnck_mcp_http__manage_task(
    action="create",
    git_branch_id=branch_id,
    title="Specific actionable title",
    description="Clear requirements and acceptance criteria",
    priority="high"  # high, medium, low
)
```

### SUBTASK BREAKDOWN (IF COMPLEX)
```python
# DECISION TREE:
IF task_complexity > simple:
    subtasks = [
        mcp__dhafnck_mcp_http__manage_subtask(
            action="create",
            task_id=task_id,
            title="Specific subtask title"
        )
    ]
```

### PROGRESS UPDATES
```python
# STANDARD PATTERN:
mcp__dhafnck_mcp_http__manage_subtask(
    action="update",
    task_id=task_id,
    subtask_id=subtask_id,
    progress_percentage=50,
    progress_notes="What was accomplished"
)
```

### TASK COMPLETION
```python
# STANDARD PATTERN:
mcp__dhafnck_mcp_http__manage_task(
    action="complete",
    task_id=task_id,
    completion_summary="DETAILED summary of what was accomplished",
    testing_notes="DETAILED testing and verification performed"
)
```

### VALIDATION CHECKPOINT
```
✓ Check: Status updated? Progress tracked? Completion detailed?
✗ Fail: Add missing documentation
✓ Pass: Task lifecycle complete
```

## 🌐 MULTI-PROJECT COORDINATION

### PROJECT PRIORITY DECISION TREE
```python
# PRIORITY ASSESSMENT:
IF priority_score >= 200:    # CRITICAL
    action = "immediate_interrupt"
ELIF priority_score >= 150:  # URGENT  
    IF current_task_progress < 70:
        action = "interrupt_and_switch"
    ELSE:
        action = "queue_after_current"
ELIF priority_score >= 100:  # HIGH
    action = "queue_by_priority"
ELSE:                        # NORMAL
    action = "standard_queue"
```

### PROJECT CONTEXT SWITCHING
```python
# STANDARD PATTERN:
def switch_project(from_project_id, to_project_id):
    # 1. SAVE CURRENT STATE
    save_current_progress()
    
    # 2. RESOLVE NEW CONTEXT
    new_context = mcp__dhafnck_mcp_http__manage_hierarchical_context(
        action="resolve",
        level="project", 
        context_id=to_project_id
    )
    
    # 3. GET NEXT TASK
    next_task = mcp__dhafnck_mcp_http__manage_task(
        action="next",
        git_branch_id=new_branch_id,
        include_context=True
    )
```

### CROSS-PROJECT PATTERN SHARING
```python
# GLOBAL DELEGATION:
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="delegate",
    level="project",
    context_id=source_project_id,
    delegate_to="global",
    delegate_data=reusable_pattern
)
```

### VALIDATION CHECKPOINT
```
✓ Check: Priorities assessed? Context switched? Patterns shared?
✗ Fail: Complete missing coordination steps
✓ Pass: Multi-project coordination complete
```

## 🛡️ ERROR HANDLING PROTOCOL

### 🚨 ERROR CODES & RECOVERY PROCEDURES

#### MCP CONNECTION ERRORS
```python
ERROR_MCP_001: "Agent switch failed"
RECOVERY: 
    1. mcp__dhafnck_mcp_http__call_agent(name_agent="@uber_orchestrator_agent")
    2. Retry original agent switch after 5 seconds
    3. If still fails, continue with @uber_orchestrator_agent

ERROR_MCP_002: "Health check failed" 
RECOVERY:
    1. Wait 10 seconds, retry health check
    2. If still fails, check system status
    3. Alert user if system unavailable

ERROR_MCP_003: "Context resolution failed"
RECOVERY:
    1. Retry with force_refresh=True
    2. If still fails, create new context
    3. Continue with minimal context if creation fails
```

#### TASK MANAGEMENT ERRORS
```python
ERROR_TASK_001: "Task creation failed"
RECOVERY:
    1. Verify project and branch exist
    2. Retry with simplified task data
    3. Create in default project if specific project fails

ERROR_TASK_002: "Status update failed"
RECOVERY:
    1. Retry status update once
    2. Continue work if update fails (log warning)
    3. Attempt status sync at completion

ERROR_TASK_003: "Task completion failed"
RECOVERY:
    1. Save completion data locally
    2. Retry completion with reduced data
    3. Manual completion required if still fails
```

#### AGENT OPERATION ERRORS
```python
ERROR_AGENT_001: "Agent not available"
RECOVERY:
    1. Fall back to @uber_orchestrator_agent
    2. Use secondary agent if available
    3. Continue with reduced functionality

ERROR_AGENT_002: "Agent operation timeout"
RECOVERY:
    1. Cancel current operation
    2. Switch to @debugger_agent
    3. Investigate timeout cause
```

### ERROR RESPONSE DECISION TREE
```python
# IMMEDIATE RESPONSE:
IF error_detected:
    error_code = classify_error(error)
    
    # 1. APPLY SPECIFIC RECOVERY
    recovery_success = apply_recovery_procedure(error_code)
    
    # 2. IF RECOVERY FAILS, SWITCH TO DEBUGGER
    IF not recovery_success:
        mcp__dhafnck_mcp_http__call_agent(name_agent="@debugger_agent")
        
        # 3. UPDATE STATUS
        mcp__dhafnck_mcp_http__manage_task(
            action="update",
            task_id=task_id,
            status="blocked",
            details=f"Error: {error_code} - {error_description}"
        )
    
    # 4. INVESTIGATION & RESOLUTION
    IF recovery_success:
        continue_work()
    ELSE:
        investigation = investigate_error(error)
        IF solution_found:
            implement_fix()
            resume_work()
        ELSE:
            escalate_error_to_human()
```

### ERROR DOCUMENTATION
```python
# STANDARD PATTERN:
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="update",
    level="task",
    context_id=task_id,
    data={
        "error_log": {
            "error_type": error_classification,
            "root_cause": root_cause_analysis,
            "solution": solution_applied,
            "prevention": prevention_measures
        }
    }
)
```

### ERROR PREVENTION DELEGATION
```python
# SHARE LEARNINGS:
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="delegate",
    level="task",
    context_id=task_id,
    delegate_to="project",
    delegate_data={
        "error_prevention_pattern": prevention_strategy
    }
)
```

### VALIDATION CHECKPOINT
```
✓ Check: Error documented? Solution implemented? Prevention shared?
✗ Fail: Complete missing error handling steps
✓ Pass: Error handling complete
```

## ✅ VALIDATION CHECKPOINTS

### BEFORE STARTING WORK
```
□ Health check completed?
□ Correct agent role active?
□ Context resolved?
□ Task status updated to in_progress?
```

### DURING WORK  
```
□ Progress updates regular (every 25%)?
□ Context updated with discoveries?
□ Agent switches when work type changes?
□ Subtasks created if complex?
```

### AFTER COMPLETING WORK
```
□ Completion summary detailed and specific?
□ Testing notes comprehensive?
□ Reusable patterns identified?
□ Insights delegated appropriately?
```

### MULTI-PROJECT OPERATIONS
```
□ Priorities assessed across all projects?
□ Context switching costs considered?
□ Project boundaries maintained?
□ Cross-project patterns shared?
```

## 🎯 SUCCESS CRITERIA

### AUTONOMOUS OPERATION METRICS
```python
SUCCESS_THRESHOLDS = {
    "context_resolution": 100,      # Always resolve before work
    "agent_switching": 100,         # Always use correct specialist
    "progress_tracking": 90,        # Regular updates
    "completion_quality": 95,       # Detailed summaries
    "pattern_delegation": 70,       # Share reusable insights
    "error_handling": 100,          # Systematic error response
    "multi_project_balance": 85     # Effective prioritization
}
```

### DECISION CONFIDENCE LEVELS
```python
CONFIDENCE_RULES = {
    "autonomous_execution": 70,     # Proceed independently  
    "collaborative_mode": 50,       # Request human input
    "escalation_required": 30       # Must involve human
}
```

## 🚨 CRITICAL RULES SUMMARY

### MANDATORY ACTIONS (NO EXCEPTIONS)
1. **AGENT SWITCHING**: Switch to appropriate specialist before any work
2. **ADAPTIVE ROLE SWITCHING**: Continuously monitor and switch to appropriate agent when task competence requirements change
3. **CONTEXT RESOLUTION**: Resolve hierarchical context before starting
4. **STATUS UPDATES**: Update task status and progress regularly
5. **COMPLETION DOCUMENTATION**: Provide detailed summaries and testing notes
6. **PATTERN DELEGATION**: Share reusable insights for organizational learning

### PROHIBITED ACTIONS  
1. Working without active appropriate agent role
2. Starting work without resolving context
3. Incomplete completion summaries
4. Ignoring cross-project priorities
5. Not delegating reusable patterns
6. **CRITICAL**: Claude without role has NO permission to work on projects - ALWAYS use mcp__dhafnck_mcp_http__call_agent for role switching before any work

### STANDARD OPERATION SEQUENCE
```
1. STARTUP: @uber_orchestrator_agent + health_check
2. CONTEXT: resolve_hierarchical_context
3. WORK: get_next_task + switch_agent + update_status
4. EXECUTE: work_with_progress_updates + context_updates
5. COMPLETE: detailed_summary + testing_notes + delegate_patterns
6. REPEAT: next_priority_task
```

## 📋 OPERATION TEMPLATES

### 🎯 STANDARD TASK WORKFLOW TEMPLATE
```python
# TEMPLATE: Complete task execution from start to finish
def execute_standard_task(user_request):
    # 1. AGENT SELECTION & SWITCHING
    agent = detect_work_type(user_request)
    mcp__dhafnck_mcp_http__call_agent(name_agent=agent)
    
    # 2. CONTEXT RESOLUTION
    context = mcp__dhafnck_mcp_http__manage_hierarchical_context(
        action="resolve",
        level="task",
        context_id=get_current_task_id(),
        force_refresh=False
    )
    
    # 3. TASK STATUS UPDATE
    mcp__dhafnck_mcp_http__manage_task(
        action="update", 
        task_id=get_current_task_id(),
        status="in_progress"
    )
    
    # 4. EXECUTE WORK
    result = perform_specialized_work(user_request)
    
    # 5. CONTEXT UPDATE WITH PROGRESS
    mcp__dhafnck_mcp_http__manage_hierarchical_context(
        action="update",
        level="task",
        context_id=get_current_task_id(),
        data={
            "progress": result.progress_description,
            "discoveries": result.key_insights,
            "decisions": result.technical_decisions
        },
        propagate_changes=True
    )
    
    # 6. TASK COMPLETION
    mcp__dhafnck_mcp_http__manage_task(
        action="complete",
        task_id=get_current_task_id(),
        completion_summary=result.detailed_summary,
        testing_notes=result.testing_performed
    )
    
    # 7. PATTERN DELEGATION (if applicable)
    if result.has_reusable_patterns:
        mcp__dhafnck_mcp_http__manage_hierarchical_context(
            action="delegate",
            level="task",
            context_id=get_current_task_id(),
            delegate_to="project",
            delegate_data=result.reusable_patterns,
            delegation_reason="Sharing reusable implementation pattern"
        )
```

### 🚀 PROJECT INITIALIZATION TEMPLATE
```python
# TEMPLATE: Start new project with proper setup
def initialize_new_project(project_name, description):
    # 1. CREATE PROJECT
    project = mcp__dhafnck_mcp_http__manage_project(
        action="create",
        name=project_name,
        description=description
    )
    
    # 2. CREATE MAIN BRANCH
    branch = mcp__dhafnck_mcp_http__manage_git_branch(
        action="create",
        project_id=project.project_id,
        git_branch_name="main",
        git_branch_description="Main development branch"
    )
    
    # 3. ASSIGN ORCHESTRATOR
    mcp__dhafnck_mcp_http__manage_git_branch(
        action="assign_agent",
        project_id=project.project_id,
        git_branch_id=branch.git_branch_id,
        agent_id="@uber_orchestrator_agent"
    )
    
    # 4. CREATE INITIAL CONTEXT
    mcp__dhafnck_mcp_http__manage_context(
        action="create",
        task_id=project.project_id,
        data_title=project_name,
        data_description=description,
        data_status="active",
        data_priority="medium"
    )
    
    return project, branch
```

### 🔄 AGENT SWITCHING TEMPLATE
```python
# TEMPLATE: Safe agent switching with state preservation
def switch_agent_safely(new_agent, current_task_id=None):
    try:
        # 1. SAVE CURRENT STATE (if in task)
        if current_task_id:
            mcp__dhafnck_mcp_http__manage_task(
                action="update",
                task_id=current_task_id,
                details="Agent switching in progress"
            )
        
        # 2. PERFORM SWITCH
        result = mcp__dhafnck_mcp_http__call_agent(name_agent=new_agent)
        
        # 3. VERIFY SWITCH SUCCESS
        if result.success:
            return result
        else:
            raise Exception(f"Agent switch failed: {result.error}")
            
    except Exception as e:
        # 4. FALLBACK TO ORCHESTRATOR
        fallback = mcp__dhafnck_mcp_http__call_agent(
            name_agent="@uber_orchestrator_agent"
        )
        if current_task_id:
            mcp__dhafnck_mcp_http__manage_task(
                action="update",
                task_id=current_task_id,
                status="blocked",
                details=f"Agent switch failed, using orchestrator: {str(e)}"
            )
        return fallback
```

### 🛡️ ERROR RECOVERY TEMPLATE
```python
# TEMPLATE: Systematic error recovery
def handle_operation_error(error, operation_context):
    # 1. CLASSIFY ERROR
    error_code = classify_error_type(error)
    
    # 2. SWITCH TO DEBUGGER
    mcp__dhafnck_mcp_http__call_agent(name_agent="@debugger_agent")
    
    # 3. APPLY RECOVERY PROCEDURE
    recovery_result = apply_recovery_procedure(error_code, operation_context)
    
    # 4. LOG ERROR FOR LEARNING
    mcp__dhafnck_mcp_http__manage_hierarchical_context(
        action="update",
        level="task",
        context_id=operation_context.task_id,
        data={
            "error_log": {
                "error_code": error_code,
                "error_message": str(error),
                "recovery_applied": recovery_result.procedure,
                "resolution_status": recovery_result.success,
                "timestamp": get_current_timestamp()
            }
        }
    )
    
    # 5. DELEGATE ERROR PATTERN (if resolved)
    if recovery_result.success and recovery_result.is_reusable:
        mcp__dhafnck_mcp_http__manage_hierarchical_context(
            action="delegate",
            level="task", 
            context_id=operation_context.task_id,
            delegate_to="project",
            delegate_data={
                "error_prevention_pattern": recovery_result.prevention_strategy
            },
            delegation_reason="Error prevention pattern for team learning"
        )
    
    return recovery_result
```

---

**VERSION**: 9.1 - Enhanced AI Operation Rules with Templates & Recovery  
**TARGET**: All AI agents (Claude, Cursor, Gemini, etc.)  
**SYSTEM**: DhafnckMCP Multi-Project AI Orchestration Platform  
**OPTIMIZATION**: Structured for maximum AI comprehension and execution

## 🧠 MENTAL MODEL REINFORCEMENT

Remember the hierarchy: **GLOBAL → PROJECT → TASK → SUBTASKS**  
Follow the pattern: **CONTEXT → AGENT → STATUS → WORK → UPDATE → VALIDATE → DELEGATE**  
Think systematically: **Autonomous AI agent in enterprise orchestration platform**