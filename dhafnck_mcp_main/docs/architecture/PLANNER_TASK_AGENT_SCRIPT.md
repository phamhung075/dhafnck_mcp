# 📋 PLANNER TASK AGENT SCRIPT - Task Creation from Issues Report

## Executive Summary for Planner Task Agent

**YOUR MISSION**: Read `issues_report.md` and create specific tasks for code, test, and review agents based on identified issues.

## 🔄 Planner Task Agent Workflow

### Phase 1: Load Planner Agent
```python
# Load Task Planning Agent
planner_agent = mcp__dhafnck_mcp_http__call_agent(name_agent="@task_planning_agent")

print("📋 Starting Task Planning...")
print("📖 Will read issues_report.md and create tasks")
```

### Phase 2: Read Issues Report & Track Changes

```python
def read_issues_report():
    """Read the current issues report"""
    try:
        report_content = Read(file_path="dhafnck_mcp_main/docs/architecture/issues_report.md")
        return {
            "content": report_content,
            "exists": True,
            "last_modified": datetime.now()
        }
    except:
        return {
            "content": None,
            "exists": False,
            "last_modified": None
        }

def parse_report_status(report_content):
    """Parse the report to extract current status and issues"""
    if not report_content:
        return None
    
    # Extract key metrics
    compliance_score = 0
    total_violations = 0
    report_status = "UNKNOWN"
    
    lines = report_content.split('\n')
    for line in lines:
        if "**Compliance Score**:" in line:
            score_match = re.search(r'(\d+)/100', line)
            if score_match:
                compliance_score = int(score_match.group(1))
        
        if "**Total Violations**:" in line:
            violation_match = re.search(r'(\d+)', line)
            if violation_match:
                total_violations = int(violation_match.group(1))
        
        if "**Report Status**:" in line:
            if "ACTIVE ANALYSIS" in line:
                report_status = "ACTIVE"
            elif "ANALYSIS UPDATED" in line:
                report_status = "UPDATED"
            elif "ANALYSIS COMPLETE" in line:
                report_status = "COMPLETE"
    
    # Extract task assignments
    controller_tasks_needed = "Code Agent: Fix all 16 controller files" in report_content
    factory_tasks_needed = "Code Agent: Create central RepositoryFactory" in report_content
    cache_tasks_needed = "Code Agent: Create cached repository wrappers" in report_content
    test_tasks_needed = "Test Agent: Create controller compliance tests" in report_content
    review_tasks_needed = "Review Agent: Verify fixes maintain functionality" in report_content
    
    return {
        "compliance_score": compliance_score,
        "total_violations": total_violations,
        "status": report_status,
        "tasks_needed": {
            "controller_fixes": controller_tasks_needed,
            "factory_implementation": factory_tasks_needed,
            "cache_invalidation": cache_tasks_needed,
            "testing": test_tasks_needed,
            "review": review_tasks_needed
        }
    }

# Track report changes
last_report_content = None
last_report_time = None
no_change_count = 0
```

### Phase 3: Create Tasks Based on Report Analysis

```python
def create_tasks_from_report(report_analysis, git_branch_id):
    """Create MCP tasks based on issues report analysis"""
    
    if not report_analysis or report_analysis["status"] == "COMPLETE":
        print("✅ Report shows analysis complete - no new tasks needed")
        return []
    
    tasks_created = []
    
    # Create master task if compliance score < 100
    if report_analysis["compliance_score"] < 100:
        master_task = mcp__dhafnck_mcp_http__manage_task(
            action="create",
            git_branch_id=git_branch_id,
            title=f"CRITICAL: Fix {report_analysis['total_violations']} Architecture Violations",
            description=f"Current compliance: {report_analysis['compliance_score']}/100. System needs fixes before production.",
            priority="critical",
            metadata={
                "compliance_score": report_analysis["compliance_score"],
                "total_violations": report_analysis["total_violations"],
                "blocking_production": True
            }
        )
        
        # Create context for the master task
        mcp__dhafnck_mcp_http__manage_context(
            action="create",
            level="task",
            context_id=master_task["task"]["id"],
            git_branch_id=git_branch_id,
            data={
                "source": "issues_report.md",
                "compliance_score": report_analysis["compliance_score"],
                "violations": report_analysis["total_violations"],
                "report_status": report_analysis["status"],
                "agents_involved": ["@coding_agent", "@test_orchestrator_agent", "@review_agent"]
            }
        )
        
        tasks_created.append(master_task)
        master_task_id = master_task["task"]["id"]
    else:
        master_task_id = None
    
    # Create Code Agent Tasks
    if report_analysis["tasks_needed"]["controller_fixes"]:
        controller_task = mcp__dhafnck_mcp_http__manage_subtask(
            action="create",
            task_id=master_task_id,
            title="Fix Controller Layer Violations",
            description="Remove direct database/repository access from 16 controller files",
            assigned_agent="@coding_agent",
            priority="P1",
            metadata={
                "files_affected": 16,
                "violation_type": "direct_database_access",
                "estimated_time": "4-6 hours"
            }
        )
        tasks_created.append(controller_task)
    
    if report_analysis["tasks_needed"]["factory_implementation"]:
        factory_task = mcp__dhafnck_mcp_http__manage_subtask(
            action="create",
            task_id=master_task_id,
            title="Implement Repository Factory Pattern",
            description="Create central factory with environment checking for 27 factory files",
            assigned_agent="@coding_agent",
            priority="P1",
            metadata={
                "files_affected": 27,
                "violation_type": "broken_factory_pattern",
                "estimated_time": "6-8 hours"
            }
        )
        tasks_created.append(factory_task)
    
    if report_analysis["tasks_needed"]["cache_invalidation"]:
        cache_task = mcp__dhafnck_mcp_http__manage_subtask(
            action="create",
            task_id=master_task_id,
            title="Add Cache Invalidation",
            description="Implement cache invalidation for 32 mutation methods",
            assigned_agent="@coding_agent",
            priority="P2",
            metadata={
                "methods_affected": 32,
                "violation_type": "missing_cache_invalidation",
                "estimated_time": "4-6 hours"
            }
        )
        tasks_created.append(cache_task)
    
    # Create Test Agent Tasks
    if report_analysis["tasks_needed"]["testing"]:
        test_tasks = [
            {
                "title": "Create Controller Compliance Tests",
                "description": "Tests to verify controllers only use facades, no direct DB access",
                "test_type": "compliance",
                "coverage": "All 16 controller files"
            },
            {
                "title": "Create Factory Environment Tests",
                "description": "Tests to verify factories check environment variables correctly",
                "test_type": "integration",
                "coverage": "All 27 factory files"
            },
            {
                "title": "Create Cache Invalidation Tests",
                "description": "Tests to verify cache is invalidated on mutations",
                "test_type": "unit",
                "coverage": "All 32 mutation methods"
            },
            {
                "title": "Create Full Compliance Test Suite",
                "description": "End-to-end tests for complete architecture compliance",
                "test_type": "end-to-end",
                "coverage": "Full system compliance verification"
            }
        ]
        
        for test_spec in test_tasks:
            test_task = mcp__dhafnck_mcp_http__manage_subtask(
                action="create",
                task_id=master_task_id,
                title=test_spec["title"],
                description=test_spec["description"],
                assigned_agent="@test_orchestrator_agent",
                priority="P2",
                metadata={
                    "test_type": test_spec["test_type"],
                    "coverage": test_spec["coverage"]
                }
            )
            tasks_created.append(test_task)
    
    # Create Review Agent Tasks
    if report_analysis["tasks_needed"]["review"]:
        review_tasks = [
            {
                "title": "Review Controller Fixes",
                "description": "Verify controller fixes maintain functionality and follow DDD",
                "review_type": "code_review",
                "focus": "Controllers use facades correctly"
            },
            {
                "title": "Review Factory Implementation",
                "description": "Verify factory correctly switches based on environment",
                "review_type": "integration_review",
                "focus": "Environment switching works"
            },
            {
                "title": "Review Cache Implementation",
                "description": "Verify cache invalidation works correctly",
                "review_type": "performance_review", 
                "focus": "Cache behavior and performance"
            },
            {
                "title": "Final Compliance Review",
                "description": "Verify system achieves 100/100 compliance score",
                "review_type": "compliance_review",
                "focus": "Production readiness verification"
            }
        ]
        
        for review_spec in review_tasks:
            review_task = mcp__dhafnck_mcp_http__manage_subtask(
                action="create",
                task_id=master_task_id,
                title=review_spec["title"],
                description=review_spec["description"],
                assigned_agent="@review_agent",
                priority="P3",
                metadata={
                    "review_type": review_spec["review_type"],
                    "focus": review_spec["focus"]
                }
            )
            tasks_created.append(review_task)
    
    return tasks_created
```

### Phase 4: Monitor Report Changes & Create Tasks

```python
def monitor_report_and_create_tasks():
    """Main loop to monitor report changes and create tasks"""
    
    global last_report_content, last_report_time, no_change_count
    
    print("🔄 Starting report monitoring loop...")
    
    while True:
        print(f"📖 Checking issues_report.md...")
        
        # Read current report
        current_report = read_issues_report()
        
        if not current_report["exists"]:
            print("⚠️ issues_report.md not found. Waiting for analyze agent...")
            time.sleep(300)  # 5 minutes
            continue
        
        # Parse report status
        report_analysis = parse_report_status(current_report["content"])
        
        if not report_analysis:
            print("⚠️ Could not parse report. Waiting...")
            time.sleep(300)  # 5 minutes
            continue
        
        # Check if report has changed
        if current_report["content"] == last_report_content:
            no_change_count += 1
            print(f"📊 Report unchanged (check #{no_change_count})")
            
            if report_analysis["status"] == "COMPLETE":
                print("✅ Analysis complete - planner task finished")
                break
                
            if no_change_count >= 20:  # 20 * 5 minutes = 100 minutes max wait
                print("⚠️ Report hasn't changed for 100 minutes. Manual intervention needed.")
                break
            
            print("⏱️ Waiting 5 minutes for report changes...")
            time.sleep(300)  # 5 minutes
            continue
        
        # Report has changed - reset counter and create tasks
        no_change_count = 0
        last_report_content = current_report["content"]
        last_report_time = current_report["last_modified"]
        
        print(f"📝 Report updated! Status: {report_analysis['status']}")
        print(f"📊 Compliance Score: {report_analysis['compliance_score']}/100")
        print(f"🚨 Total Violations: {report_analysis['total_violations']}")
        
        # Create tasks based on current report
        tasks_created = create_tasks_from_report(report_analysis, git_branch_id)
        
        if tasks_created:
            print(f"✅ Created {len(tasks_created)} tasks from report analysis")
            
            # Log task creation
            for task in tasks_created:
                if "subtask" in task:
                    print(f"  📋 Subtask: {task['subtask']['title']} → {task['subtask']['assigned_agent']}")
                else:
                    print(f"  📋 Task: {task['task']['title']}")
            
            # Update context with task creation info
            mcp__dhafnck_mcp_http__manage_context(
                action="update",
                level="branch",
                context_id=git_branch_id,
                data={
                    "planner_last_run": datetime.now().isoformat(),
                    "tasks_created": len(tasks_created),
                    "report_compliance_score": report_analysis["compliance_score"],
                    "report_violations": report_analysis["total_violations"],
                    "agents_assigned": ["@coding_agent", "@test_orchestrator_agent", "@review_agent"]
                }
            )
        else:
            print("📋 No new tasks needed based on current report")
        
        # Check if analysis is complete
        if report_analysis["status"] == "COMPLETE" and report_analysis["compliance_score"] >= 100:
            print("🎉 Report shows analysis complete with 100/100 score!")
            
            # Create final completion task
            completion_task = mcp__dhafnck_mcp_http__manage_task(
                action="create",
                git_branch_id=git_branch_id,
                title="✅ Architecture Compliance Achieved",
                description="System achieved 100/100 compliance score - ready for production",
                priority="info",
                metadata={
                    "final_score": report_analysis["compliance_score"],
                    "violations_fixed": report_analysis["total_violations"],
                    "production_ready": True
                }
            )
            
            print("✅ Created completion task - planner work finished")
            break
        
        # Continue monitoring
        print("🔄 Tasks created. Continuing to monitor report for changes...")
        print("⏱️ Waiting 5 minutes for next check...")
        time.sleep(300)  # 5 minutes

# Execute the monitoring loop
monitor_report_and_create_tasks()
```

### Phase 5: Task Coordination & Status Updates

```python
def update_task_assignments():
    """Update task assignments and notify agents"""
    
    # Get all active tasks for the branch
    active_tasks = mcp__dhafnck_mcp_http__manage_task(
        action="list",
        git_branch_id=git_branch_id,
        status="pending"
    )
    
    if not active_tasks:
        print("📋 No active tasks found")
        return
    
    # Group tasks by assigned agent
    agent_assignments = {
        "@coding_agent": [],
        "@test_orchestrator_agent": [],
        "@review_agent": []
    }
    
    for task in active_tasks:
        assigned_agent = task.get("assigned_agent", "unassigned")
        if assigned_agent in agent_assignments:
            agent_assignments[assigned_agent].append(task)
    
    # Update context with agent assignments
    mcp__dhafnck_mcp_http__manage_context(
        action="update",
        level="branch",
        context_id=git_branch_id,
        data={
            "task_assignments": {
                "coding_agent_tasks": len(agent_assignments["@coding_agent"]),
                "test_agent_tasks": len(agent_assignments["@test_orchestrator_agent"]),
                "review_agent_tasks": len(agent_assignments["@review_agent"]),
                "total_active_tasks": len(active_tasks)
            },
            "planner_status": "active",
            "last_assignment_update": datetime.now().isoformat()
        }
    )
    
    # Print assignment summary
    print("📋 Task Assignment Summary:")
    for agent, tasks in agent_assignments.items():
        print(f"  {agent}: {len(tasks)} tasks assigned")
        for task in tasks:
            print(f"    - {task['title']} (Priority: {task.get('priority', 'normal')})")
    
    print(f"📊 Total active tasks: {len(active_tasks)}")

# Update assignments before finishing
update_task_assignments()
```

## 📊 Report Monitoring Strategy

The planner agent:

1. **Reads Report Continuously** - Monitors `issues_report.md` for changes every 5 minutes
2. **Parses Current Status** - Extracts compliance score, violations, and needed tasks
3. **Creates Specific Tasks** - Generates detailed tasks for code, test, and review agents
4. **Tracks Changes** - Only creates new tasks when report content changes
5. **Coordinates Agents** - Ensures proper task assignment and priority

## 🔄 Task Creation Logic

```python
# Task creation based on report status:

if compliance_score < 30:
    # Critical - focus on high-impact fixes
    create_priority_tasks(["controllers", "factories"])

elif compliance_score < 70:
    # Improving - continue with all fixes
    create_all_tasks(["controllers", "factories", "cache"])

elif compliance_score < 90:
    # Good progress - add comprehensive testing
    create_testing_tasks(["compliance_tests", "integration_tests"])

elif compliance_score < 100:
    # Almost there - final verification
    create_review_tasks(["final_compliance_check"])

else:
    # Complete - create completion task
    create_completion_task("production_ready")
```

## 🎯 Success Criteria

- ✅ `issues_report.md` monitored continuously with 5-minute intervals
- ✅ Tasks created only when report content changes (no duplicates)
- ✅ Specific tasks created for each agent type (code, test, review)
- ✅ Task priorities assigned based on compliance score
- ✅ Context updated with task assignments for coordination
- ✅ Planner stops when 100/100 compliance achieved

The planner agent serves as the task coordinator, translating report findings into actionable work items for all other agents.