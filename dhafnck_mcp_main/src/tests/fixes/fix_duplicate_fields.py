#!/usr/bin/env python3
"""
Fix duplicate field declarations in test files
"""
import os
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_duplicate_fields(content):
    """Fix duplicate field declarations"""
    # Fix duplicate user_id, status, metadata in Project
    content = re.sub(
        r"user_id='test-user',\s*status='active',\s*metadata='{}',\s*user_id='test-user',\s*status='active',\s*metadata='{}',\s*user_id='test-user',\s*status='active',\s*metadata='{}',",
        r"user_id='test-user', status='active', metadata='{}',",
        content
    )
    
    # Also fix the simpler duplicate
    content = re.sub(
        r"user_id='test-user',\s*status='active',\s*metadata='{}',\s*user_id='test-user',\s*status='active',\s*metadata='{}',",
        r"user_id='test-user', status='active', metadata='{}',",
        content
    )
    
    # Fix duplicate priority, status, metadata, task_count, completed_task_count in ProjectGitBranch
    content = re.sub(
        r"priority='medium',\s*status='todo',\s*metadata='{}',\s*task_count=0,\s*completed_task_count=0,\s*priority='medium',\s*status='todo',\s*metadata='{}',\s*task_count=0,\s*completed_task_count=0,",
        r"priority='medium', status='todo', metadata='{}', task_count=0, completed_task_count=0,",
        content
    )
    
    # Fix BranchContext wrong field names
    content = re.sub(
        r"team_preferences={},\s*technology_stack={'branch_data':\s*'test'},\s*project_workflow={},\s*local_standards={},\s*global_overrides={},\s*delegation_rules={},",
        r"branch_workflow={}, branch_standards={'branch_data': 'test'}, agent_assignments={}, local_overrides={}, delegation_rules={},",
        content
    )
    
    # Fix TaskContext wrong field names
    content = re.sub(
        r"team_preferences={},\s*technology_stack={'task_data':\s*'test'},\s*project_workflow={},\s*local_standards={},\s*global_overrides={},\s*delegation_rules={},",
        r"task_data={'task_data': 'test'}, local_overrides={}, implementation_notes={}, delegation_triggers={},",
        content
    )
    
    # Remove duplicate field declarations from model instantiations
    content = re.sub(
        r"(\w+)\s*=\s*(\w+)\([^)]*\),\s*\1\s*=",
        r"\1 =",
        content
    )
    
    # Remove lines that have only field removals (cleanup after fixes)
    content = re.sub(
        r"^\s*insights=\[\],?\s*$",
        "",
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"^\s*progress_tracking={},?\s*$",
        "",
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"^\s*shared_patterns={},?\s*$",
        "",
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"^\s*implementation_notes={},?\s*$",
        "",
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"^\s*local_overrides={},?\s*$",
        "",
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"^\s*delegation_triggers={},?\s*$",
        "",
        content,
        flags=re.MULTILINE
    )
    
    return content


def fix_branch_context_constructor(content):
    """Fix BranchContext constructor to include parent_project_context_id"""
    # Pattern to match BranchContext instantiation
    pattern = r"(BranchContext\([^)]*parent_project_id=project\.id,)([^)]*)(parent_project_context_id=project\.id,)?([^)]*\))"
    
    def replacer(match):
        start = match.group(1)
        middle = match.group(2)
        has_parent_context = match.group(3)
        end = match.group(4)
        
        if not has_parent_context:
            # Add parent_project_context_id after delegation_rules
            middle = re.sub(
                r"(delegation_rules={})",
                r"\1, parent_project_context_id=project.id",
                middle
            )
        
        return start + middle + end
    
    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
    
    return content


def fix_task_context_constructor(content):
    """Fix TaskContext constructor to include parent_branch_context_id"""
    # Pattern to match TaskContext instantiation
    pattern = r"(TaskContext\([^)]*parent_branch_id=branch\.id,)([^)]*)(parent_branch_context_id=branch\.id,)?([^)]*\))"
    
    def replacer(match):
        start = match.group(1)
        middle = match.group(2)
        has_branch_context = match.group(3)
        end = match.group(4)
        
        if not has_branch_context:
            # Add parent_branch_context_id after delegation_triggers
            middle = re.sub(
                r"(delegation_triggers={})",
                r"\1, parent_branch_context_id=branch.id",
                middle
            )
        
        return start + middle + end
    
    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
    
    return content


def process_file(filepath):
    """Process a single test file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Apply all fixes
        content = fix_duplicate_fields(content)
        content = fix_branch_context_constructor(content)
        content = fix_task_context_constructor(content)
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")
        return False


def main():
    """Main function"""
    test_files = [
        "dhafnck_mcp_main/src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py",
        "dhafnck_mcp_main/src/tests/integration/vision/test_basic_vision.py",
        "dhafnck_mcp_main/src/tests/test_postgresql_isolation_demo.py",
    ]
    
    # Also scan for all test files
    test_dir = Path("dhafnck_mcp_main/src/tests")
    if test_dir.exists():
        for test_file in test_dir.rglob("test_*.py"):
            if str(test_file) not in test_files:
                test_files.append(str(test_file))
    
    fixed_count = 0
    
    for test_file in test_files:
        filepath = Path(test_file)
        if filepath.exists():
            if process_file(filepath):
                fixed_count += 1
                logger.info(f"Fixed: {test_file}")
    
    logger.info(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())