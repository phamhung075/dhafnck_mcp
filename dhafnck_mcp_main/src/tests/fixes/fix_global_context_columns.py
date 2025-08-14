#!/usr/bin/env python3
"""
Fix tests that use incorrect column names for global_contexts table
"""
import os
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_global_context_columns(content):
    """Fix global_contexts column references"""
    # The actual columns are:
    # id, organization_id, autonomous_rules, security_policies, coding_standards,
    # workflow_templates, delegation_rules, created_at, updated_at, version
    
    # Fix INSERT statements
    old_insert = r"""INSERT INTO global_contexts \(
                        id, data, insights, progress_tracking,
                        shared_patterns, implementation_notes,
                        local_overrides, delegation_triggers,
                        created_at, updated_at
                    \) VALUES \(
                        :id, :data, :insights, :progress_tracking,
                        :shared_patterns, :implementation_notes,
                        :local_overrides, :delegation_triggers,
                        :created_at, :updated_at
                    \)"""
    
    new_insert = """INSERT INTO global_contexts (
                        id, organization_id, autonomous_rules, security_policies,
                        coding_standards, workflow_templates, delegation_rules,
                        created_at, updated_at
                    ) VALUES (
                        :id, :organization_id, :autonomous_rules, :security_policies,
                        :coding_standards, :workflow_templates, :delegation_rules,
                        :created_at, :updated_at
                    )"""
    
    content = re.sub(old_insert, new_insert, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix the parameter dictionary
    old_params = r"""'id': 'global_singleton',
                    'data': '{"organization": "test-org"}',
                    'insights': '\[\]',
                    'progress_tracking': '{}',
                    'shared_patterns': '{}',
                    'implementation_notes': '{}',
                    'local_overrides': '{}',
                    'delegation_triggers': '{}',"""
    
    new_params = """'id': 'global_singleton',
                    'organization_id': 'test-org',
                    'autonomous_rules': '{}',
                    'security_policies': '{}',
                    'coding_standards': '{}',
                    'workflow_templates': '{}',
                    'delegation_rules': '{}',"""
    
    content = re.sub(old_params, new_params, content, flags=re.MULTILINE)
    
    # Fix ON CONFLICT clause
    content = re.sub(
        r"ON CONFLICT \(id\) DO UPDATE SET\s+data = EXCLUDED\.data,\s+updated_at = EXCLUDED\.updated_at",
        "ON CONFLICT (id) DO UPDATE SET organization_id = EXCLUDED.organization_id, updated_at = EXCLUDED.updated_at",
        content
    )
    
    return content


def fix_context_model_columns(content):
    """Fix references to old context model columns"""
    # Fix references to 'data' column
    if "ProjectContext" in content and "parent_global_id='global_singleton'" in content:
        content = re.sub(
            r"data={'project': '([^']+)'}",
            r"team_preferences={}, technology_stack={'project': '\1'}, project_workflow={}, local_standards={}, global_overrides={}, delegation_rules={}",
            content
        )
    
    if "BranchContext" in content and "parent_project_id" in content:
        content = re.sub(
            r"data={'branch': '([^']+)'}",
            r"branch_workflow={}, branch_standards={'branch': '\1'}, agent_assignments={}, local_overrides={}, delegation_rules={}",
            content
        )
    
    return content


def fix_missing_fields(content):
    """Add missing required fields"""
    # Fix Project creation missing metadata
    content = re.sub(
        r"(Project\([^)]*?)(created_at=datetime\.utcnow\(\))",
        r"\1user_id='test-user', status='active', metadata='{}', \2",
        content
    )
    
    # Fix ProjectGitBranch missing fields
    content = re.sub(
        r"(ProjectGitBranch\([^)]*?)(created_at=datetime\.utcnow\(\))",
        r"\1priority='medium', status='todo', metadata='{}', task_count=0, completed_task_count=0, \2",
        content
    )
    
    return content


def process_file(filepath):
    """Process a single test file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Apply all fixes
        content = fix_global_context_columns(content)
        content = fix_context_model_columns(content)
        content = fix_missing_fields(content)
        
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
        "dhafnck_mcp_main/src/tests/test_postgresql_isolation_demo.py",
        "dhafnck_mcp_main/src/tests/test_postgresql_isolation_fix.py",
    ]
    
    fixed_count = 0
    
    for test_file in test_files:
        filepath = Path(test_file)
        if filepath.exists():
            if process_file(filepath):
                fixed_count += 1
                logger.info(f"Fixed: {test_file}")
        else:
            logger.warning(f"File not found: {test_file}")
    
    logger.info(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())