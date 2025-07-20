#!/usr/bin/env python3
"""
Comprehensive fixes for PostgreSQL test failures
"""
import os
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_duplicate_fields(content):
    """Fix duplicate field definitions"""
    # Fix duplicate user_id, status, metadata fields
    content = re.sub(
        r"user_id='test-user', status='active', metadata='{}',\s*user_id='test-user', status='active', metadata='{}',",
        r"user_id='test-user', status='active', metadata='{}',",
        content
    )
    
    # Fix duplicate priority, status, metadata fields
    content = re.sub(
        r"priority='medium', status='todo', metadata='{}', task_count=0, completed_task_count=0,\s*created_at=datetime\.utcnow\(\),\s*updated_at=datetime\.utcnow\(\),\s*priority=\"medium\",\s*status=\"todo\",\s*metadata=\"{}\",\s*task_count=0,\s*completed_task_count=0",
        r"priority='medium', status='todo', metadata='{}', task_count=0, completed_task_count=0, created_at=datetime.utcnow(), updated_at=datetime.utcnow()",
        content
    )
    
    return content


def fix_context_model_fields(content):
    """Fix context model field references"""
    # Fix ProjectContext fields
    content = re.sub(
        r"data={'([^']+)': '([^']+)'}",
        r"team_preferences={}, technology_stack={'\1': '\2'}, project_workflow={}, local_standards={}, global_overrides={}, delegation_rules={}",
        content
    )
    
    # Fix BranchContext fields
    content = re.sub(
        r"branch_workflow={}, branch_standards={'branch': '([^']+)'}, agent_assignments={}, local_overrides={}, delegation_rules={},\s*insights=\[\],\s*progress_tracking={},\s*shared_patterns={},\s*implementation_notes={},\s*local_overrides={},\s*delegation_triggers={}",
        r"branch_workflow={}, branch_standards={'branch': '\1'}, agent_assignments={}, local_overrides={}, delegation_rules={}, parent_project_context_id=project.id",
        content
    )
    
    # Fix TaskContext fields
    content = re.sub(
        r"data={'task_data': 'test'},\s*insights=\[\],\s*progress_tracking={},\s*local_overrides={},\s*implementation_notes={},\s*delegation_triggers={}",
        r"task_data={'task_data': 'test'}, local_overrides={}, implementation_notes={}, delegation_triggers={}, parent_branch_context_id=branch.id",
        content
    )
    
    return content


def fix_global_context_insert(content):
    """Fix global context INSERT statements"""
    # Fix the INSERT statement that still has old columns
    content = re.sub(
        r"""INSERT INTO global_contexts \(
                        id, data, insights, progress_tracking,
                        shared_patterns, implementation_notes,
                        local_overrides, delegation_triggers,
                        created_at, updated_at
                    \) VALUES \(
                        'global_singleton',
                        '\{"global_data": "test"\}',
                        '\[\]', '\{\}', '\{\}', '\{\}', '\{\}', '\{\}',
                        :created_at, :updated_at
                    \)""",
        r"""INSERT INTO global_contexts (
                        id, organization_id, autonomous_rules, security_policies,
                        coding_standards, workflow_templates, delegation_rules,
                        created_at, updated_at
                    ) VALUES (
                        'global_singleton',
                        'test-org',
                        '{}',
                        '{}',
                        '{"global_data": "test"}',
                        '{}',
                        '{}',
                        :created_at, :updated_at
                    )""",
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    return content


def fix_async_tests(content):
    """Fix async test functions"""
    # Find all async test functions without @pytest.mark.asyncio
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is an async test function
        if re.match(r'^async def test_', line.strip()):
            # Look backwards to see if there's @pytest.mark.asyncio
            has_asyncio_mark = False
            j = i - 1
            while j >= 0 and (lines[j].strip().startswith('@') or lines[j].strip() == ''):
                if '@pytest.mark.asyncio' in lines[j]:
                    has_asyncio_mark = True
                    break
                j -= 1
            
            if not has_asyncio_mark:
                # Change async def to def
                line = line.replace('async def', 'def')
        
        new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)


def fix_test_file(filepath):
    """Fix a single test file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Apply all fixes
        content = fix_duplicate_fields(content)
        content = fix_context_model_fields(content)
        content = fix_global_context_insert(content)
        content = fix_async_tests(content)
        
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
    # Fix specific test files with known issues
    specific_files = [
        "dhafnck_mcp_main/src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py",
        "dhafnck_mcp_main/src/tests/integration/test_all_fixes.py",
        "dhafnck_mcp_main/src/tests/integration/validation/test_parameter_validation.py",
        "dhafnck_mcp_main/src/tests/integration/vision/test_basic_vision.py",
    ]
    
    fixed_count = 0
    
    for filepath in specific_files:
        path = Path(filepath)
        if path.exists():
            if fix_test_file(path):
                fixed_count += 1
                logger.info(f"Fixed: {filepath}")
        else:
            logger.warning(f"File not found: {filepath}")
    
    # Also run on all test files to catch others
    test_dir = Path("dhafnck_mcp_main/src/tests")
    if test_dir.exists():
        for test_file in test_dir.rglob("test_*.py"):
            if str(test_file) not in specific_files:
                if fix_test_file(test_file):
                    fixed_count += 1
                    logger.info(f"Fixed: {test_file.relative_to(test_dir.parent.parent)}")
    
    logger.info(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())