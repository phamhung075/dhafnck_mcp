#!/usr/bin/env python3
"""
🔍 ANALYZE AGENT WITH MCP INTEGRATION
Full implementation with MCP tools for architecture compliance analysis
"""

import time
import re
from datetime import datetime
from pathlib import Path

# This script would be run through the MCP agent system
# Here's the complete implementation with MCP tools

def analyze_agent_workflow():
    """
    Complete analyze agent workflow with MCP integration
    This would be executed through the Task tool with @architecture_compliance_agent
    """
    
    script = '''
# 🔍 ANALYZE AGENT SCRIPT - Architecture Compliance Analysis with Checkpoint Control
# Executive Summary: Analyze compliance, update workplace.md, control workflow via checkpoints

import time
import re
from datetime import datetime
from pathlib import Path

## Phase 1: Check Checkpoint & Initialize

def check_my_turn():
    """Check if it's analyze agent's turn to work"""
    try:
        workplace = Read(file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md")
        
        # Extract checkpoint status
        for line in workplace.split('\\n'):
            if "## 🚦 WORKFLOW CHECKPOINTS" in line:
                # Find the checkpoint section
                checkpoint_section = workplace[workplace.index(line):]
                
                if "**ANALYZE** | active" in checkpoint_section:
                    return True
                elif "**ANALYZE** | waiting" in checkpoint_section:
                    return False
                    
        # First run - no checkpoints yet
        return True
        
    except:
        # No workplace.md yet - analyze should start
        return True

def wait_for_turn():
    """Wait until it's analyze agent's turn"""
    while not check_my_turn():
        print("⏱️ ANALYZE agent waiting for turn...")
        print("   Current workflow position: Not my turn")
        time.sleep(60)  # Check every minute
    
    print("✅ ANALYZE agent's turn - starting analysis!")

# Load Architecture Compliance Agent
analyze_agent = mcp__dhafnck_mcp_http__call_agent(name_agent="@architecture_compliance_agent")

# Wait for turn
wait_for_turn()

print("🔍 Starting Architecture Analysis...")
print("📝 Will update workplace.md with checkpoints")

## Phase 2: Analysis Functions

def analyze_controllers():
    """Analyze controller layer compliance"""
    violations = []
    files_scanned = 0
    violation_details = []
    
    # Search for controller files
    controller_files = Glob(pattern="**/interface/controllers/*.py")
    
    for controller_file in controller_files:
        files_scanned += 1
        content = Read(file_path=controller_file)
        
        # Check for violations
        if 'from ...infrastructure.database import' in content:
            violations.append(f"{Path(controller_file).name}: Direct DB import")
            violation_details.append(f"- {Path(controller_file).name} (Direct database access)")
        if 'from ...infrastructure.repositories import' in content:
            violations.append(f"{Path(controller_file).name}: Direct repo import")
            violation_details.append(f"- {Path(controller_file).name} (Direct repository import)")
        if 'SessionLocal()' in content:
            violations.append(f"{Path(controller_file).name}: Creates DB session")
            violation_details.append(f"- {Path(controller_file).name} (Creates database session)")
    
    return {
        "files_scanned": files_scanned,
        "violations": len(violations),
        "details": '\\n'.join(violation_details) if violation_details else "- None found (✅ COMPLIANT)"
    }

def analyze_factories():
    """Analyze factory pattern implementation"""
    # Find all factory files
    factory_files = Glob(pattern="**/repositories/*factory*.py")
    
    working_factories = 0
    broken_details = []
    fixed_details = []
    files_scanned = len(factory_files)
    
    for factory_file in factory_files:
        content = Read(file_path=factory_file)
        
        # Check if factory checks environment
        has_env_check = "os.getenv('ENVIRONMENT'" in content or "os.environ.get('ENVIRONMENT'" in content
        has_db_check = "os.getenv('DATABASE_TYPE'" in content or "os.environ.get('DATABASE_TYPE'" in content
        has_redis_check = "os.getenv('REDIS_ENABLED'" in content or "os.environ.get('REDIS_ENABLED'" in content
        
        # Check for central factory usage
        uses_central = "from .repository_factory import RepositoryFactory" in content or \\
                      "RepositoryFactory." in content
        
        if uses_central or (has_env_check and has_db_check):
            working_factories += 1
            fixed_details.append(f"✅ {Path(factory_file).name}")
        else:
            broken_details.append(f"❌ {Path(factory_file).name} (Missing env checks)")
    
    details = f"- {len(factory_files)} total factories\\n"
    details += f"- {working_factories} working correctly\\n"
    details += f"- {len(factory_files) - working_factories} need fixes\\n\\n"
    
    if fixed_details:
        details += "Fixed Factories:\\n" + '\\n'.join(fixed_details) + "\\n\\n"
    
    if broken_details:
        details += "Broken Factories:\\n" + '\\n'.join(broken_details)
    
    return {
        "files_scanned": files_scanned,
        "violations": len(factory_files) - working_factories,
        "details": details
    }

def analyze_cache_invalidation():
    """Analyze cache invalidation implementation"""
    # Find cached repository files
    cached_repos = Glob(pattern="**/repositories/cached_*.py")
    
    methods_with_invalidation = 0
    missing_details = []
    implemented_details = []
    
    mutations_needing_cache = [
        "create", "update", "delete", "save", "remove", "clear"
    ]
    
    for repo_file in cached_repos:
        content = Read(file_path=repo_file)
        has_invalidation = False
        
        for mutation in mutations_needing_cache:
            if f"def {mutation}" in content:
                # Check if invalidation exists near the method
                if 'invalidate' in content or '_invalidate' in content or 'cache.delete' in content:
                    has_invalidation = True
                    methods_with_invalidation += 1
        
        if has_invalidation:
            implemented_details.append(f"✅ {Path(repo_file).name}")
        else:
            missing_details.append(f"❌ {Path(repo_file).name}")
    
    details = f"- {len(cached_repos)} cached repositories found\\n"
    
    if implemented_details:
        details += f"- {len(implemented_details)} with invalidation:\\n"
        details += '\\n'.join(implemented_details) + "\\n"
    
    if missing_details:
        details += f"- {len(missing_details)} missing invalidation:\\n"
        details += '\\n'.join(missing_details)
    
    if not cached_repos:
        details = "- No cached repository implementations found"
    
    all_repos = Glob(pattern="**/repositories/*repository.py")
    
    return {
        "files_scanned": len(all_repos),
        "violations": len(missing_details),
        "details": details
    }

## Phase 3: Create/Update Workplace Report

def create_workplace_with_checkpoints(analysis_results):
    """Create workplace.md with checkpoint control system"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine grade based on compliance score
    score = analysis_results["compliance_score"]
    if score >= 90:
        grade = "A - EXCELLENT"
    elif score >= 80:
        grade = "B - GOOD"
    elif score >= 70:
        grade = "C - SATISFACTORY"
    elif score >= 60:
        grade = "D - NEEDS IMPROVEMENT"
    else:
        grade = "F - CRITICAL FAILURE"
    
    workplace_content = f"""# 📋 ARCHITECTURE COMPLIANCE WORKPLACE
## Central Coordination & Checkpoint Control

**Report Status**: ACTIVE ANALYSIS
**Last Updated**: {timestamp}
**Compliance Score**: {analysis_results["compliance_score"]}/100 (Grade {grade})
**Total Violations**: {analysis_results["total_violations"]}

## 🚦 WORKFLOW CHECKPOINTS
**Control the agent workflow through these checkpoints:**

| Agent | Status | Can Work? | Notes |
|-------|--------|-----------|-------|
| **ANALYZE** | active | ✅ | Currently analyzing architecture |
| **PLANNER** | waiting | ⏸️ | Waiting for analyze to complete |
| **CODE** | waiting | ⏸️ | Waiting for tasks from planner |
| **TEST** | waiting | ⏸️ | Waiting for code implementation |
| **REVIEW** | waiting | ⏸️ | Waiting for test completion |
| **REANALYZE** | waiting | ⏸️ | Waiting for review completion |

### Workflow Rules:
1. Only ONE agent can be "active" at a time
2. Agents check their checkpoint before working
3. If status is "waiting", agent sleeps for 60 seconds
4. Planner can be "skip" if tasks already exist
5. Code and Test can be "active" simultaneously

---

## 🚨 CRITICAL ISSUES IDENTIFIED

### 1. Controller Layer Violations
**Status**: {analysis_results["controller_status"]}
**Count**: {analysis_results["controller_violations"]["violations"]} files with violations
**Impact**: {"Breaks DDD architecture" if analysis_results["controller_violations"]["violations"] > 0 else "DDD architecture properly separated"}
**Description**: {"Controllers directly access database/repositories" if analysis_results["controller_violations"]["violations"] > 0 else "All controllers use facades correctly"}

#### Affected Files:
{analysis_results["controller_violations"]["details"]}

---

### 2. Repository Factory Pattern
**Status**: {analysis_results["factory_status"]}
**Count**: {analysis_results["factory_analysis"]["violations"]} factories missing checks
**Impact**: {"No environment switching capability" if analysis_results["factory_analysis"]["violations"] > 0 else "Full environment switching enabled"}
**Description**: {"Factory files don't check environment variables" if analysis_results["factory_analysis"]["violations"] > 0 else "All factories properly configured"}

#### Problem Analysis:
{analysis_results["factory_analysis"]["details"]}

---

### 3. Cache Invalidation
**Status**: {analysis_results["cache_status"]}
**Count**: {analysis_results["cache_violations"]["violations"]} repositories missing invalidation
**Impact**: {"Stale data when Redis enabled" if analysis_results["cache_violations"]["violations"] > 0 else "Proper cache management"}
**Description**: {"Missing cache invalidation on mutations" if analysis_results["cache_violations"]["violations"] > 0 else "Cache invalidation properly implemented"}

#### Cache Status:
{analysis_results["cache_violations"]["details"]}

---

## 📋 NEXT AGENT ACTION

**ANALYZE COMPLETE** → **ACTIVATE PLANNER**

To activate the next agent, the analyze agent will update checkpoints:
- Set ANALYZE to "complete"
- Set PLANNER to "active"
- Planner will then read this file and create tasks

---

## 📊 ANALYSIS METRICS

- **Total Files Analyzed**: {analysis_results["files_analyzed"]}
- **Violations Found**: {analysis_results["total_violations"]}
- **Compliance Score**: {analysis_results["compliance_score"]}/100
- **Estimated Fix Time**: {"30 minutes" if analysis_results["total_violations"] < 10 else "2-3 hours" if analysis_results["total_violations"] < 50 else "1-2 days"}
- **Blocking Production**: {"NO" if analysis_results["compliance_score"] >= 80 else "PARTIALLY" if analysis_results["compliance_score"] >= 60 else "YES"}
- **Next Analysis**: After all fixes applied

---

**Report Generated By**: @architecture_compliance_agent
**Next Agent**: @task_planning_agent (when PLANNER = active)
"""
    
    Write(
        file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md",
        content=workplace_content
    )
    
    print(f"📝 Created/Updated workplace.md at {timestamp}")

## Phase 4: Update Checkpoint Function

def update_checkpoint(agent_name, new_status):
    """Update a specific agent's checkpoint status"""
    
    workplace = Read(file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md")
    
    # Update the checkpoint for the specified agent
    lines = workplace.split('\\n')
    for i, line in enumerate(lines):
        if f"**{agent_name.upper()}**" in line and "|" in line:
            parts = line.split('|')
            if new_status == "active":
                parts[2] = " active "
                parts[3] = " ✅ "
            elif new_status == "complete":
                parts[2] = " complete "
                parts[3] = " ✔️ "
            elif new_status == "waiting":
                parts[2] = " waiting "
                parts[3] = " ⏸️ "
            elif new_status == "skip":
                parts[2] = " skip "
                parts[3] = " ⏭️ "
            
            lines[i] = '|'.join(parts)
            break
    
    updated_content = '\\n'.join(lines)
    
    Write(
        file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md",
        content=updated_content
    )
    
    print(f"✅ Updated {agent_name} checkpoint to: {new_status}")

## Phase 5: Main Analysis Function

def analyze_and_update():
    """Run analysis and update workplace with results"""
    
    print("🔄 Running architecture analysis...")
    
    # Perform actual analysis
    controller_analysis = analyze_controllers()
    factory_analysis = analyze_factories()
    cache_analysis = analyze_cache_invalidation()
    
    # Calculate metrics
    total_violations = (
        controller_analysis["violations"] + 
        factory_analysis["violations"] + 
        cache_analysis["violations"]
    )
    
    # More realistic scoring
    controller_score = 40 if controller_analysis["violations"] == 0 else max(0, 40 - (controller_analysis["violations"] * 2.5))
    factory_score = 40 if factory_analysis["violations"] == 0 else max(0, 40 - (factory_analysis["violations"] * 5))
    cache_score = 20 if cache_analysis["violations"] == 0 else max(0, 20 - (cache_analysis["violations"] * 4))
    
    compliance_score = int(controller_score + factory_score + cache_score)
    
    # Determine status messages
    controller_status = "✅ RESOLVED - NO VIOLATIONS" if controller_analysis["violations"] == 0 else "❌ VIOLATIONS FOUND"
    factory_status = "✅ COMPLETE - ALL CONFIGURED" if factory_analysis["violations"] == 0 else f"⚠️ {factory_analysis['violations']} NEED FIXES"
    cache_status = "✅ IMPLEMENTED" if cache_analysis["violations"] == 0 else f"⚠️ {cache_analysis['violations']} MISSING"
    
    analysis_results = {
        "compliance_score": compliance_score,
        "total_violations": total_violations,
        "controller_violations": controller_analysis,
        "controller_status": controller_status,
        "factory_analysis": factory_analysis,
        "factory_status": factory_status,
        "cache_violations": cache_analysis,
        "cache_status": cache_status,
        "files_analyzed": controller_analysis["files_scanned"] + factory_analysis["files_scanned"] + cache_analysis["files_scanned"]
    }
    
    # Create/update workplace with results
    create_workplace_with_checkpoints(analysis_results)
    
    return compliance_score, total_violations

## Phase 6: Main Loop with Checkpoint Control

def main_analyze_loop():
    """Main analysis loop with checkpoint control"""
    
    analysis_run = 1
    max_runs = 50
    
    while analysis_run <= max_runs:
        print(f"\\n{'='*60}")
        print(f"🔍 Analysis Run #{analysis_run}")
        print(f"{'='*60}")
        
        # Check if it's our turn
        if not check_my_turn():
            print("⏸️ Not analyze agent's turn. Waiting 60 seconds...")
            time.sleep(60)
            continue
        
        # Set our status to active
        print("✅ Analyze agent active - running analysis")
        
        # Run analysis
        compliance_score, total_violations = analyze_and_update()
        
        print(f"📊 Analysis Results:")
        print(f"   - Compliance Score: {compliance_score}/100")
        print(f"   - Total Violations: {total_violations}")
        
        # Check if we're done
        if compliance_score >= 100:
            print("🎉 TARGET ACHIEVED: 100/100 Compliance!")
            
            # Update final report
            update_checkpoint("ANALYZE", "complete")
            
            print("✅ Analysis complete - system is compliant!")
            break
        
        # Hand off to planner
        print("\\n🔄 Analysis complete - activating PLANNER agent")
        update_checkpoint("ANALYZE", "complete")
        update_checkpoint("PLANNER", "active")
        
        # Update context with analysis results
        mcp__dhafnck_mcp_http__manage_context(
            action="update",
            level="global",
            context_id="global",
            data={
                "analysis_run": analysis_run,
                "compliance_score": compliance_score,
                "total_violations": total_violations,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print("⏸️ Analyze agent going to sleep...")
        print("   Will reactivate after REVIEW completes")
        
        # Wait for our next turn (after review)
        while True:
            time.sleep(60)  # Check every minute
            
            workplace = Read(file_path="dhafnck_mcp_main/docs/architecture/working/workplace.md")
            
            # Check if review is done and we should reanalyze
            if "**REANALYZE** | active" in workplace or "**ANALYZE** | active" in workplace:
                print("\\n✅ Reanalysis requested - starting new analysis run")
                analysis_run += 1
                
                # Reset checkpoints for new cycle
                update_checkpoint("ANALYZE", "active")
                update_checkpoint("PLANNER", "waiting")
                update_checkpoint("CODE", "waiting")
                update_checkpoint("TEST", "waiting")
                update_checkpoint("REVIEW", "waiting")
                update_checkpoint("REANALYZE", "waiting")
                break
            
            # Check if review marked us complete
            if "**ANALYZE** | complete" in workplace and compliance_score >= 100:
                print("✅ System fully compliant - analyze agent done!")
                return
    
    print("⚠️ Maximum analysis runs reached. Manual intervention needed.")

# Execute the main loop
main_analyze_loop()

print("🏁 Analyze agent workflow complete")
'''
    
    return script

# To use this in MCP:
# 1. Load the agent: mcp__dhafnck_mcp_http__call_agent(name_agent="@architecture_compliance_agent")
# 2. Execute through Task tool with the script above
# 3. The agent will continuously monitor compliance and update workplace.md