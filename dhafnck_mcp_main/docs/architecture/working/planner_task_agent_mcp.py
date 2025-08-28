#!/usr/bin/env python3
"""
📋 PLANNER TASK AGENT WITH MCP INTEGRATION
Full implementation with MCP tools for task creation and checkpoint control
"""

import time
import re
from datetime import datetime
import json

# This script would be run through the MCP agent system
# Here's the complete implementation as requested in the document

def planner_agent_workflow():
    """
    Complete planner agent workflow with MCP integration
    This would be executed through the Task tool with @task_planning_agent
    """
    
    script = '''
# 📋 PLANNER TASK AGENT SCRIPT - Task Creation with Checkpoint Control
# Executive Summary: Read workplace.md, check for existing tasks, create new tasks if needed

import time
import re
from datetime import datetime

## Phase 1: Check Checkpoint & Initialize

def check_my_turn():
    """Check if it's planner agent's turn to work"""
    try:
        workplace = Read(file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md")
        
        # Check checkpoint status
        if "**PLANNER** | active" in workplace:
            return "active"
        elif "**PLANNER** | skip" in workplace:
            return "skip"
        elif "**PLANNER** | waiting" in workplace:
            return "waiting"
        elif "**PLANNER** | complete" in workplace:
            return "complete"
            
        return "waiting"  # Default to waiting
        
    except:
        return "waiting"  # No workplace.md yet

def wait_for_turn():
    """Wait until it's planner agent's turn"""
    while True:
        status = check_my_turn()
        
        if status == "active":
            print("✅ PLANNER agent's turn - checking for tasks!")
            return "active"
        elif status == "skip":
            print("⏭️ PLANNER skipping - tasks already exist")
            return "skip"
        elif status == "complete":
            print("✔️ PLANNER already complete this cycle")
            return "complete"
        else:
            print("⏱️ PLANNER agent waiting for turn...")
            print("   Current status: waiting for ANALYZE to complete")
            time.sleep(60)  # Check every minute

# Load Task Planning Agent
planner_agent = mcp__dhafnck_mcp_http__call_agent(name_agent="@task_planning_agent")

print("📋 Starting Task Planning Agent...")
print("🔍 Will check workplace.md and existing tasks")

## Phase 2: Check Existing Tasks

def check_existing_tasks(git_branch_id):
    """Check if tasks already exist for current issues"""
    
    # Get all pending/in_progress tasks
    existing_tasks = mcp__dhafnck_mcp_http__manage_task(
        action="list",
        git_branch_id=git_branch_id,
        status="pending"
    )
    
    in_progress_tasks = mcp__dhafnck_mcp_http__manage_task(
        action="list",
        git_branch_id=git_branch_id,
        status="in_progress"
    )
    
    # Combine lists
    all_tasks = existing_tasks.get("tasks", []) + in_progress_tasks.get("tasks", [])
    total_active_tasks = len(all_tasks)
    
    if total_active_tasks > 0:
        print(f"📋 Found {total_active_tasks} active tasks")
        
        # Group by type
        code_tasks = 0
        test_tasks = 0
        review_tasks = 0
        
        for task in all_tasks:
            task_str = str(task)
            if "@coding_agent" in task_str or "Code" in task.get("title", ""):
                code_tasks += 1
            elif "@test" in task_str or "Test" in task.get("title", ""):
                test_tasks += 1
            elif "@review" in task_str or "Review" in task.get("title", ""):
                review_tasks += 1
        
        print(f"  - Code tasks: {code_tasks}")
        print(f"  - Test tasks: {test_tasks}")
        print(f"  - Review tasks: {review_tasks}")
        
        return {
            "has_tasks": True,
            "total": total_active_tasks,
            "code": code_tasks,
            "test": test_tasks,
            "review": review_tasks,
            "tasks": all_tasks
        }
    
    return {
        "has_tasks": False,
        "total": 0
    }

## Phase 3: Read and Parse Workplace Report

def read_workplace_report():
    """Read and parse the workplace report"""
    try:
        report_content = Read(file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md")
        
        # Parse key metrics
        compliance_score = 0
        total_violations = 0
        
        lines = report_content.split('\\n')
        for line in lines:
            if "**Compliance Score**:" in line:
                score_match = re.search(r'(\\d+)/100', line)
                if score_match:
                    compliance_score = int(score_match.group(1))
            
            if "**Total Violations**:" in line:
                violation_match = re.search(r'(\\d+)', line)
                if violation_match:
                    total_violations = int(violation_match.group(1))
        
        # Check what tasks are needed
        needs_controller_fixes = "Code Agent: Fix all 16 controller files" in report_content
        needs_factory_fixes = "Code Agent: Update 7 factory files" in report_content or \\
                            "6 factories missing checks" in report_content
        needs_cache_fixes = "Code Agent: Create cached repository wrappers" in report_content
        needs_tests = "Test Agent: Create controller compliance tests" in report_content
        needs_review = "Review Agent: Verify fixes maintain functionality" in report_content
        
        return {
            "compliance_score": compliance_score,
            "total_violations": total_violations,
            "tasks_needed": {
                "controller": needs_controller_fixes,
                "factory": needs_factory_fixes,
                "cache": needs_cache_fixes,
                "test": needs_tests,
                "review": needs_review
            },
            "content": report_content
        }
    except Exception as e:
        print(f"⚠️ Could not read workplace.md: {e}")
        return None

## Phase 4: Decision Logic - Skip or Create Tasks

def should_create_tasks(report_analysis, existing_tasks):
    """Decide if we should create tasks or skip"""
    
    if not report_analysis:
        print("❌ No report to analyze")
        return False
    
    if report_analysis["compliance_score"] >= 100:
        print("✅ System already compliant (100/100)")
        return False
    
    if existing_tasks["has_tasks"]:
        # Check if existing tasks cover the issues
        has_coverage = (
            existing_tasks["code"] > 0 and
            existing_tasks["test"] > 0
        )
        
        if has_coverage:
            print("⏭️ Existing tasks cover current issues")
            return False
        else:
            print("⚠️ Existing tasks incomplete - creating additional tasks")
            return True
    
    print("📋 No existing tasks - will create new ones")
    return True

## Phase 5: Create Tasks Based on Report

def create_tasks_from_report(report_analysis, git_branch_id):
    """Create tasks based on workplace report"""
    
    tasks_created = []
    
    # Check if we need factory fixes (most likely at 65% compliance)
    if report_analysis["compliance_score"] < 100:
        
        # Create master task for remaining compliance issues
        master_task = mcp__dhafnck_mcp_http__manage_task(
            action="create",
            git_branch_id=git_branch_id,
            title=f"Complete Architecture Compliance - {report_analysis['compliance_score']}/100 to 100/100",
            description=f"Fix remaining {report_analysis['total_violations']} violations to achieve 100% compliance",
            priority="critical",
            estimated_effort="2-4 hours",
            labels=["architecture", "compliance", "factory-pattern"]
        )
        tasks_created.append(master_task)
        master_id = master_task["task"]["id"]
        
        # Create subtasks for specific factory fixes
        if report_analysis["tasks_needed"]["factory"]:
            # Individual factory files needing fixes
            factories = [
                "task_repository_factory.py",
                "subtask_repository_factory.py",
                "git_branch_repository_factory.py",
                "agent_repository_factory.py",
                "template_repository_factory.py",
                "mock_repository_factory.py"
            ]
            
            for factory in factories:
                factory_task = mcp__dhafnck_mcp_http__manage_subtask(
                    action="create",
                    task_id=master_id,
                    title=f"Fix {factory} Environment Checks",
                    description=f"Add environment variable checks to {factory} for proper Redis/DB switching",
                    assignees="@coding_agent",
                    priority="high"
                )
                tasks_created.append(factory_task)
        
        # Create test task for factory validation
        test_task = mcp__dhafnck_mcp_http__manage_subtask(
            action="create",
            task_id=master_id,
            title="Test Factory Environment Switching",
            description="Verify all factories properly switch between Redis/DB based on environment",
            assignees="@test_orchestrator_agent",
            priority="high"
        )
        tasks_created.append(test_task)
        
        # Create final review task
        review_task = mcp__dhafnck_mcp_http__manage_subtask(
            action="create",
            task_id=master_id,
            title="Final Compliance Review",
            description="Verify system achieves 100/100 compliance score",
            assignees="@review_agent",
            priority="medium"
        )
        tasks_created.append(review_task)
    
    return tasks_created

## Phase 6: Update Checkpoints

def update_checkpoint(agent_name, new_status):
    """Update checkpoint status in workplace.md"""
    
    workplace = Read(file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md")
    
    lines = workplace.split('\\n')
    for i, line in enumerate(lines):
        if f"**{agent_name.upper()}**" in line and "|" in line:
            parts = line.split('|')
            
            # Update status and icon
            if new_status == "active":
                parts[2] = " active "
                parts[3] = " ✅ "
            elif new_status == "complete":
                parts[2] = " complete "
                parts[3] = " ✔️ "
            elif new_status == "skip":
                parts[2] = " skip "
                parts[3] = " ⏭️ "
            elif new_status == "waiting":
                parts[2] = " waiting "
                parts[3] = " ⏸️ "
            
            lines[i] = '|'.join(parts)
            break
    
    updated_content = '\\n'.join(lines)
    
    Write(
        file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md",
        content=updated_content
    )
    
    print(f"✅ Updated {agent_name} checkpoint to: {new_status}")

## Phase 7: Main Planner Loop

def main_planner_loop():
    """Main planner loop with checkpoint control"""
    
    # Get branch context
    project = mcp__dhafnck_mcp_http__manage_project(action="list")
    if project and project.get("projects"):
        # Find the agentic-project
        project_id = None
        git_branch_id = None
        
        for proj in project["projects"]:
            if proj["name"] == "agentic-project":
                project_id = proj["id"]
                # Find the architecture compliance branch
                for branch_id, branch_info in proj.get("git_branchs", {}).items():
                    if "architecture" in branch_info["name"].lower():
                        git_branch_id = branch_id
                        break
                break
        
        if not git_branch_id:
            print("⚠️ No architecture compliance branch found")
            return
    else:
        print("⚠️ No projects found")
        return
    
    while True:
        print(f"\\n{'='*60}")
        print("📋 PLANNER Agent Check")
        print(f"{'='*60}")
        
        # Wait for our turn
        status = wait_for_turn()
        
        if status == "skip":
            print("⏭️ Skipping - tasks already exist")
            # Don't change checkpoints since they're already set
            break
        
        if status == "complete":
            print("✔️ Planner already ran this cycle")
            break
        
        if status != "active":
            continue
        
        # Check existing tasks
        print("\\n📊 Checking existing tasks...")
        existing_tasks = check_existing_tasks(git_branch_id)
        
        # Read workplace report
        print("\\n📖 Reading workplace report...")
        report_analysis = read_workplace_report()
        
        if not report_analysis:
            print("⚠️ No report found - waiting...")
            time.sleep(60)
            continue
        
        print(f"📊 Compliance Score: {report_analysis['compliance_score']}/100")
        print(f"🚨 Total Violations: {report_analysis['total_violations']}")
        
        # Decide whether to create tasks
        if should_create_tasks(report_analysis, existing_tasks):
            print("\\n✅ Creating tasks from report...")
            
            # Create tasks
            tasks_created = create_tasks_from_report(report_analysis, git_branch_id)
            
            print(f"📋 Created {len(tasks_created)} tasks/subtasks")
            
            for task in tasks_created:
                if "subtask" in task:
                    print(f"  - {task['subtask']['title']}")
                else:
                    print(f"  - {task['task']['title']}")
            
            # Update context
            mcp__dhafnck_mcp_http__manage_context(
                action="update",
                level="branch",
                context_id=git_branch_id,
                data={
                    "planner_run": datetime.now().isoformat(),
                    "tasks_created": len(tasks_created),
                    "compliance_score": report_analysis["compliance_score"],
                    "violations": report_analysis["total_violations"],
                    "focus": "Factory pattern completion"
                }
            )
            
            # Mark planner complete and activate next agents
            update_checkpoint("PLANNER", "complete")
            update_checkpoint("CODE", "active")
            update_checkpoint("TEST", "waiting")  # Wait for code
            
            print("\\n✅ Tasks created - activating CODE agent")
            break
            
        else:
            print("\\n⏭️ No new tasks needed")
            
            if existing_tasks["has_tasks"]:
                # Skip and let existing tasks continue
                print("✅ Existing tasks sufficient - monitoring progress")
            else:
                # System might be complete
                if report_analysis["compliance_score"] >= 100:
                    update_checkpoint("PLANNER", "complete")
                    print("🎉 System compliant - planner complete")
                else:
                    print("⚠️ No tasks but not compliant - check manually")
            
            break

# Execute the main loop
main_planner_loop()

print("\\n🏁 Planner agent workflow complete")
print("\\n📊 Summary:")
print("  - Checkpoint respected ✅")
print("  - Existing tasks checked ✅")
print("  - Duplicate prevention ✅")
print("  - Next agents activated ✅")
'''
    
    return script

# Write the full MCP script
if __name__ == "__main__":
    script_content = planner_agent_workflow()
    print("📋 PLANNER TASK AGENT MCP SCRIPT GENERATED")
    print("=" * 60)
    print("This script should be executed through the MCP Task tool")
    print("with @task_planning_agent for full integration")
    print("\nKey Features:")
    print("  ✅ Respects checkpoint system")
    print("  ✅ Checks existing tasks")
    print("  ✅ Creates tasks via MCP")
    print("  ✅ Updates checkpoints")
    print("  ✅ Activates next agents")
    print("\nDecision Tree:")
    print("  ACTIVE → Check Tasks → Create if Needed → Complete")
    print("  SKIP → No Action (tasks exist)")
    print("  WAITING → Sleep 60s → Recheck")
    print("  COMPLETE → Already Done")