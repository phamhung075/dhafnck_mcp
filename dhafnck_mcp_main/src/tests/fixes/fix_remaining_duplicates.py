#!/usr/bin/env python3
"""
Fix remaining duplicate field issues in test files
"""
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_file_content(content):
    """Fix all duplicate field issues"""
    
    # Fix duplicate user_id, status, metadata in Project constructor
    content = re.sub(
        r"user_id='test-user',\s*status='active',\s*metadata='{}',\s*user_id='test-user',\s*status='active',\s*metadata='{}',",
        r"",  # Remove the duplicate part entirely since fields are already defined
        content
    )
    
    # Fix duplicate priority, status, metadata, etc. in ProjectGitBranch
    content = re.sub(
        r"priority='medium',\s*status='todo',\s*metadata='{}',\s*task_count=0,\s*completed_task_count=0,\s*(priority='medium',\s*status='todo',\s*metadata='{}',\s*task_count=0,\s*completed_task_count=0,\s*)?",
        r"priority='medium', status='todo', metadata='{}', task_count=0, completed_task_count=0, ",
        content
    )
    
    # Fix duplicate parent_project_context_id
    content = re.sub(
        r"parent_project_context_id=project\.id,\s*parent_project_context_id=project\.id,",
        r"parent_project_context_id=project.id,",
        content
    )
    
    # Fix empty lines from removed fields
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Fix Project model instantiation pattern
    content = re.sub(
        r'''(Project\(\s*
            id=test_ids\.project_id,\s*
            name="[^"]+",\s*
            description="[^"]+",)\s*
            (user_id="test-user",\s*
            status="active",)\s*
            user_id='test-user',\s*status='active',\s*metadata='{}',\s*
            (created_at=datetime\.utcnow\(\),\s*
            updated_at=datetime\.utcnow\(\))''',
        r'\1\n                    \2\n                    metadata={},\n                    \3',
        content,
        flags=re.VERBOSE | re.MULTILINE
    )
    
    # Fix ProjectGitBranch model instantiation pattern
    content = re.sub(
        r'''(ProjectGitBranch\(\s*
            id=test_ids\.branch_id,\s*
            project_id=project\.id,\s*
            name="[^"]+",\s*
            description="[^"]+",)\s*
            priority='medium',\s*status='todo',\s*metadata='{}',\s*task_count=0,\s*completed_task_count=0,\s*
            (created_at=datetime\.utcnow\(\),\s*updated_at=datetime\.utcnow\(\))''',
        r'\1\n                    priority="medium", status="todo", metadata={}, task_count=0, completed_task_count=0,\n                    \2',
        content,
        flags=re.VERBOSE | re.MULTILINE
    )
    
    return content


def process_file(filepath):
    """Process a single file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        content = fix_file_content(content)
        
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
    # Target the specific file with issues
    test_file = Path("dhafnck_mcp_main/src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py")
    
    if test_file.exists():
        if process_file(test_file):
            logger.info(f"Fixed: {test_file}")
        else:
            logger.info(f"No changes needed: {test_file}")
    else:
        logger.error(f"File not found: {test_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())