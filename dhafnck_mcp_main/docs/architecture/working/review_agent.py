#!/usr/bin/env python3
"""
REVIEW AGENT SCRIPT - Code & Test Review with Report Updates

Reviews code implementations and appends findings to workplace.md
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Any

# MCP Tool imports (simulated - replace with actual MCP client)
def mcp__dhafnck_mcp_http__call_agent(name_agent: str) -> Dict:
    """Load agent from MCP server"""
    print(f"📡 Loading agent: {name_agent}")
    return {"success": True, "agent_info": {"name": name_agent}}

def mcp__dhafnck_mcp_http__manage_task(action: str, **kwargs) -> Dict:
    """Task management operations"""
    print(f"📋 Task action: {action}")
    return {"task": {"title": "Review Controller Fixes", "id": "task-123"}}

def Read(file_path: str) -> str:
    """Read file content"""
    with open(file_path, 'r') as f:
        return f.read()

def Write(file_path: str, content: str):
    """Write file content"""
    with open(file_path, 'w') as f:
        f.write(content)

def Bash(command: str) -> str:
    """Execute bash command"""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

# Configuration
WORKPLACE_PATH = "dhafnck_mcp_main/docs/architecture/working/workplace.md"
BRANCH_ID = "branch-xyz-123"
PROJECT_ROOT = "/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main"

class ReviewAgent:
    """Review agent for code and test compliance verification"""
    
    def __init__(self):
        self.review_results = []
        self.compliance_scores = {}
        
    def run(self):
        """Main review loop"""
        print("🔍 REVIEW AGENT STARTING...")
        
        # Load review agent
        agent = mcp__dhafnck_mcp_http__call_agent(name_agent="@review_agent")
        print(f"✅ Review agent loaded: {agent['agent_info']['name']}")
        
        # Check workplace for current status
        status = self.check_workplace_status()
        
        if status.get("review_checkpoint") != "active":
            print(f"⏸️ Review checkpoint is {status.get('review_checkpoint', 'waiting')}. Waiting...")
            time.sleep(60)
            return
        
        # Get review task
        task = self.get_review_task()
        
        if not task:
            print("⏱️ No review tasks available. Waiting 5 minutes...")
            time.sleep(300)
            return
            
        # Execute review based on task type
        if "Controller" in task["task"]["title"]:
            self.review_controllers()
        elif "Factory" in task["task"]["title"]:
            self.review_factories()
        elif "Cache" in task["task"]["title"]:
            self.review_cache()
        elif "Test" in task["task"]["title"]:
            self.review_tests()
        else:
            self.perform_final_review()
            
    def check_workplace_status(self) -> Dict:
        """Check current workplace status and checkpoints"""
        try:
            content = Read(WORKPLACE_PATH)
            
            # Parse checkpoint status
            status = {}
            if "| **REVIEW**" in content:
                review_line = [line for line in content.split('\n') if "| **REVIEW**" in line][0]
                if "active" in review_line.lower():
                    status["review_checkpoint"] = "active"
                elif "complete" in review_line.lower():
                    status["review_checkpoint"] = "complete"
                else:
                    status["review_checkpoint"] = "waiting"
                    
            # Parse current compliance score
            if "Compliance Score:" in content:
                score_match = re.search(r'Compliance Score:\s*(\d+)/100', content)
                if score_match:
                    status["current_score"] = int(score_match.group(1))
                    
            return status
            
        except Exception as e:
            print(f"⚠️ Could not check workplace status: {e}")
            return {}
            
    def get_review_task(self) -> Dict:
        """Get next review task"""
        try:
            task = mcp__dhafnck_mcp_http__manage_task(
                action="next",
                git_branch_id=BRANCH_ID,
                assigned_agent="@review_agent",
                include_context=True
            )
            return task
        except:
            return None
            
    def review_controllers(self):
        """Review controller implementations for DDD compliance"""
        print("🔍 Starting controller review...")
        
        controller_files = [
            "src/fastmcp/task_management/interface/controllers/claude_agent_controller.py",
            "src/fastmcp/task_management/interface/controllers/context_id_detector_orm.py",
            "src/fastmcp/task_management/interface/controllers/rule_orchestration_controller.py",
            "src/fastmcp/task_management/interface/controllers/unified_context_controller.py",
            "src/fastmcp/task_management/interface/controllers/subtask_mcp_controller.py",
            "src/fastmcp/task_management/interface/controllers/task_mcp_controller.py"
        ]
        
        results = []
        compliant_count = 0
        
        for controller_file in controller_files:
            file_path = os.path.join(PROJECT_ROOT, controller_file)
            result = self.review_controller_file(file_path)
            results.append(result)
            if result["compliant"]:
                compliant_count += 1
                
        # Calculate compliance
        compliance_rate = (compliant_count / len(results)) * 100 if results else 0
        
        # Update workplace with results
        self.append_review_to_workplace("Controller Review", {
            "files_reviewed": len(results),
            "compliant_files": compliant_count,
            "compliance_rate": compliance_rate,
            "status": "FIXED" if compliance_rate >= 90 else "NEEDS_REWORK",
            "detailed_results": results
        })
        
    def review_controller_file(self, file_path: str) -> Dict:
        """Review a single controller file"""
        try:
            content = Read(file_path)
            
            result = {
                "file": os.path.basename(file_path),
                "status": "PASS",
                "issues": [],
                "compliant": True
            }
            
            # Check for direct database imports
            if 'from infrastructure.database import' in content:
                result["issues"].append("❌ Direct database import found")
                result["status"] = "FAIL"
                result["compliant"] = False
                
            # Check for direct repository imports
            if 'from infrastructure.repositories import' in content and 'repository_factory' not in content.lower():
                result["issues"].append("❌ Direct repository import (not factory)")
                result["status"] = "FAIL"
                result["compliant"] = False
                
            # Check for database session creation
            if 'SessionLocal()' in content or 'get_db()' in content:
                result["issues"].append("❌ Creates database sessions directly")
                result["status"] = "FAIL"
                result["compliant"] = False
                
            # Check for facade usage
            if 'ApplicationFacade' in content or 'from application.facades' in content:
                result["issues"].append("✅ Uses ApplicationFacade pattern")
            else:
                result["issues"].append("⚠️ No ApplicationFacade usage detected")
                result["status"] = "NEEDS_WORK" if result["status"] == "PASS" else result["status"]
                
            # If no issues found, it's compliant
            if not result["issues"] or all("✅" in issue for issue in result["issues"]):
                result["issues"].append("✅ DDD compliant - no violations found")
                result["compliant"] = True
                
            return result
            
        except Exception as e:
            return {
                "file": os.path.basename(file_path),
                "status": "ERROR",
                "issues": [f"❌ Could not read file: {e}"],
                "compliant": False
            }
            
    def review_factories(self):
        """Review repository factory implementations"""
        print("🔍 Starting factory review...")
        
        factory_files = [
            "src/fastmcp/task_management/infrastructure/repositories/repository_factory.py",
            "src/fastmcp/task_management/infrastructure/repositories/task_repository_factory.py",
            "src/fastmcp/task_management/infrastructure/repositories/subtask_repository_factory.py",
            "src/fastmcp/task_management/infrastructure/repositories/project_repository_factory.py",
            "src/fastmcp/task_management/infrastructure/repositories/agent_repository_factory.py"
        ]
        
        results = []
        compliant_count = 0
        
        for factory_file in factory_files:
            file_path = os.path.join(PROJECT_ROOT, factory_file)
            result = self.review_factory_file(file_path)
            results.append(result)
            if result["compliant"]:
                compliant_count += 1
                
        compliance_rate = (compliant_count / len(results)) * 100 if results else 0
        
        self.append_review_to_workplace("Factory Review", {
            "components_reviewed": len(results),
            "compliant_components": compliant_count,
            "compliance_rate": compliance_rate,
            "status": "FIXED" if compliance_rate >= 90 else "NEEDS_REWORK",
            "detailed_results": results
        })
        
    def review_factory_file(self, file_path: str) -> Dict:
        """Review a single factory file"""
        try:
            content = Read(file_path)
            
            result = {
                "file": os.path.basename(file_path),
                "status": "PASS",
                "issues": [],
                "compliant": True
            }
            
            # Check for environment variable checking
            env_checks = ["os.getenv('ENVIRONMENT'", "os.getenv('DATABASE_TYPE'", "os.getenv('REDIS_ENABLED'"]
            
            if "repository_factory.py" in file_path:
                # Central factory should have all checks
                for check in env_checks:
                    if check in content:
                        result["issues"].append(f"✅ Has {check}")
                    else:
                        result["issues"].append(f"❌ Missing {check}")
                        result["status"] = "FAIL"
                        result["compliant"] = False
            else:
                # Other factories should delegate to central
                if "from .repository_factory import RepositoryFactory" in content:
                    result["issues"].append("✅ Imports central RepositoryFactory")
                else:
                    result["issues"].append("❌ Doesn't import central factory")
                    result["status"] = "FAIL"
                    result["compliant"] = False
                    
                if "RepositoryFactory.get_" in content:
                    result["issues"].append("✅ Delegates to central factory")
                else:
                    result["issues"].append("⚠️ May not delegate to central factory")
                    result["status"] = "NEEDS_WORK" if result["status"] == "PASS" else result["status"]
                    
            return result
            
        except Exception as e:
            return {
                "file": os.path.basename(file_path),
                "status": "ERROR",
                "issues": [f"❌ Could not read file: {e}"],
                "compliant": False
            }
            
    def review_cache(self):
        """Review cache implementation"""
        print("🔍 Starting cache review...")
        
        cache_files = [
            "src/fastmcp/task_management/infrastructure/repositories/cache_invalidation_mixin.py",
            "src/fastmcp/task_management/infrastructure/cache/cache_manager.py",
            "src/fastmcp/task_management/infrastructure/cache/context_cache.py"
        ]
        
        results = []
        compliant_count = 0
        
        for cache_file in cache_files:
            file_path = os.path.join(PROJECT_ROOT, cache_file)
            result = self.review_cache_file(file_path)
            results.append(result)
            if result["compliant"]:
                compliant_count += 1
                
        compliance_rate = (compliant_count / len(results)) * 100 if results else 0
        
        self.append_review_to_workplace("Cache Review", {
            "components_reviewed": len(results),
            "compliant_components": compliant_count,
            "compliance_rate": compliance_rate,
            "status": "FIXED" if compliance_rate >= 80 else "NEEDS_REWORK",
            "detailed_results": results
        })
        
    def review_cache_file(self, file_path: str) -> Dict:
        """Review a cache-related file"""
        try:
            content = Read(file_path)
            
            result = {
                "file": os.path.basename(file_path),
                "status": "PASS",
                "issues": [],
                "compliant": True
            }
            
            # Check for cache invalidation methods
            if "invalidate" in content.lower():
                result["issues"].append("✅ Has cache invalidation logic")
            else:
                result["issues"].append("⚠️ No explicit invalidation methods")
                
            # Check for Redis support
            if "redis" in content.lower():
                result["issues"].append("✅ Has Redis support")
            
            # Check for mutation handling
            if "create" in content or "update" in content or "delete" in content:
                if "invalidate" in content:
                    result["issues"].append("✅ Invalidates on mutations")
                else:
                    result["issues"].append("❌ Missing invalidation on mutations")
                    result["status"] = "FAIL"
                    result["compliant"] = False
                    
            return result
            
        except Exception as e:
            return {
                "file": os.path.basename(file_path),
                "status": "ERROR",
                "issues": [f"❌ Could not read file: {e}"],
                "compliant": False
            }
            
    def review_tests(self):
        """Review test implementations"""
        print("🧪 Starting test review...")
        
        test_files = [
            "src/tests/test_controller_compliance.py",
            "src/tests/test_factory_environment.py",
            "src/tests/test_cache_invalidation.py",
            "src/tests/test_full_architecture_compliance.py"
        ]
        
        results = []
        passing_count = 0
        
        for test_file in test_files:
            file_path = os.path.join(PROJECT_ROOT, test_file)
            
            # Check if test exists
            if os.path.exists(file_path):
                # Try to run the test
                test_result = self.run_test(test_file)
                results.append(test_result)
                if test_result["passing"]:
                    passing_count += 1
            else:
                results.append({
                    "file": os.path.basename(test_file),
                    "status": "MISSING",
                    "passing": False,
                    "issues": ["❌ Test file not found"]
                })
                
        compliance_rate = (passing_count / len(results)) * 100 if results else 0
        
        self.append_review_to_workplace("Test Review", {
            "test_files_reviewed": len(results),
            "passing_test_files": passing_count,
            "compliance_rate": compliance_rate,
            "status": "FIXED" if compliance_rate >= 80 else "NEEDS_WORK",
            "detailed_results": results
        })
        
    def run_test(self, test_file: str) -> Dict:
        """Run a test file and check results"""
        try:
            # Run pytest on the specific test file
            cmd = f"cd {PROJECT_ROOT} && python -m pytest {test_file} -v --tb=short"
            result = Bash(cmd)
            
            test_result = {
                "file": os.path.basename(test_file),
                "status": "PASS" if "PASSED" in result and "FAILED" not in result else "FAIL",
                "passing": "PASSED" in result and "FAILED" not in result,
                "issues": []
            }
            
            if test_result["passing"]:
                test_result["issues"].append("✅ All tests passing")
            else:
                test_result["issues"].append("❌ Some tests failing")
                # Extract failure info
                if "FAILED" in result:
                    failures = re.findall(r'FAILED.*', result)
                    for failure in failures[:3]:  # Show first 3 failures
                        test_result["issues"].append(f"  - {failure}")
                        
            return test_result
            
        except Exception as e:
            return {
                "file": os.path.basename(test_file),
                "status": "ERROR",
                "passing": False,
                "issues": [f"❌ Could not run test: {e}"]
            }
            
    def perform_final_review(self):
        """Perform final compliance review"""
        print("🎯 Performing final compliance review...")
        
        # Read current workplace to get all review results
        try:
            content = Read(WORKPLACE_PATH)
            
            # Count review sections
            controller_reviewed = "Controller Review" in content
            factory_reviewed = "Factory Review" in content
            cache_reviewed = "Cache Review" in content
            test_reviewed = "Test Review" in content
            
            all_reviewed = all([controller_reviewed, factory_reviewed, cache_reviewed, test_reviewed])
            
            # Extract compliance scores
            scores = []
            for match in re.findall(r'Compliance Rate:\s*(\d+)%', content):
                scores.append(int(match))
                
            final_score = sum(scores) / len(scores) if scores else 0
            
            # Determine production readiness
            production_ready = final_score >= 85 and all_reviewed
            
            # Append final review
            self.append_final_review(final_score, production_ready, all_reviewed)
            
        except Exception as e:
            print(f"❌ Could not perform final review: {e}")
            
    def append_review_to_workplace(self, review_type: str, data: Dict):
        """Append review results to workplace.md"""
        try:
            # Read current workplace
            content = Read(WORKPLACE_PATH)
            
            # Create review section
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            review_section = f"""
---

## 🔍 REVIEW RESULTS - {review_type.upper()}

**Review Date**: {timestamp}
**Reviewer**: @review_agent
**Component**: {review_type}

### Review Summary:
- **Items Reviewed**: {data.get('files_reviewed', data.get('components_reviewed', data.get('test_files_reviewed', 0)))}
- **Compliant Items**: {data.get('compliant_files', data.get('compliant_components', data.get('passing_test_files', 0)))}
- **Compliance Rate**: {data['compliance_rate']:.0f}%
- **Status**: {data['status']}

### Review Decision:
{"✅ **APPROVED** - Implementation meets DDD standards" if data['status'] == 'FIXED' else "⚠️ **NEEDS REWORK** - Issues found requiring fixes"}

### Detailed Findings:
"""
            
            # Add detailed results
            if "detailed_results" in data:
                for result in data["detailed_results"]:
                    file_name = result.get("file", "Unknown")
                    status = result.get("status", "UNKNOWN")
                    review_section += f"\n**{file_name}**: {status}\n"
                    
                    for issue in result.get("issues", []):
                        review_section += f"  - {issue}\n"
                        
            # Find insertion point (before success criteria or at end)
            if "## 🎯 SUCCESS CRITERIA" in content:
                insert_point = content.find("## 🎯 SUCCESS CRITERIA")
                updated_content = content[:insert_point] + review_section + "\n" + content[insert_point:]
            elif "## 🚦 NEXT WORKFLOW STEP" in content:
                insert_point = content.find("## 🚦 NEXT WORKFLOW STEP")
                updated_content = content[:insert_point] + review_section + "\n" + content[insert_point:]
            else:
                updated_content = content + review_section
                
            # Update checkpoint status if review complete
            if "REVIEW" in review_type.upper() and data['compliance_rate'] >= 85:
                updated_content = updated_content.replace(
                    "| **REVIEW** | waiting |",
                    "| **REVIEW** | complete |"
                )
                
            # Write updated content
            Write(WORKPLACE_PATH, updated_content)
            print(f"📝 Updated workplace.md with {review_type} results")
            
        except Exception as e:
            print(f"❌ Could not update workplace: {e}")
            
    def append_final_review(self, final_score: float, production_ready: bool, all_reviewed: bool):
        """Append final review conclusion"""
        try:
            content = Read(WORKPLACE_PATH)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            final_section = f"""
---

## 🎉 FINAL REVIEW COMPLETE

**Review Date**: {timestamp}
**Final Compliance Score**: {final_score:.0f}/100
**All Components Reviewed**: {"✅ Yes" if all_reviewed else "❌ No"}
**Production Ready**: {"✅ YES" if production_ready else "❌ NO"}

### Final Decision:
{"**✅ APPROVED FOR PRODUCTION** - System meets all DDD compliance standards" if production_ready else "**⚠️ NOT READY FOR PRODUCTION** - Further improvements needed"}

### Review Completion Checklist:
{"✅" if "Controller Review" in content else "❌"} Controllers Reviewed
{"✅" if "Factory Review" in content else "❌"} Factories Reviewed  
{"✅" if "Cache Review" in content else "❌"} Cache Implementation Reviewed
{"✅" if "Test Review" in content else "❌"} Tests Reviewed

**Final Reviewer**: @review_agent
**Review Status**: COMPLETE
"""
            
            # Update report status
            updated_content = content.replace(
                "**Report Status**: FRESH ANALYSIS COMPLETE",
                f"**Report Status**: ✅ REVIEW COMPLETE - {'PRODUCTION READY' if production_ready else 'IMPROVEMENTS NEEDED'}"
            )
            
            # Update compliance score
            updated_content = re.sub(
                r'Compliance Score:\s*\d+/100',
                f'Compliance Score: {final_score:.0f}/100',
                updated_content
            )
            
            # Add final review section
            updated_content += final_section
            
            # Update review checkpoint to complete
            updated_content = updated_content.replace(
                "| **REVIEW** | active |",
                "| **REVIEW** | complete |"
            )
            
            Write(WORKPLACE_PATH, updated_content)
            print(f"🎯 Final review complete - Score: {final_score:.0f}/100")
            
        except Exception as e:
            print(f"❌ Could not append final review: {e}")

# Main execution
if __name__ == "__main__":
    reviewer = ReviewAgent()
    
    # Run review loop
    while True:
        reviewer.run()
        
        # Check if review is complete
        try:
            content = Read(WORKPLACE_PATH)
            if "FINAL REVIEW COMPLETE" in content:
                print("✅ Review agent work complete")
                break
        except:
            pass
            
        # Wait before next check
        time.sleep(60)