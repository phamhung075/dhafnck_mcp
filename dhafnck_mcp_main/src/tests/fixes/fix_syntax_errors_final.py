#!/usr/bin/env python3
"""
Fix remaining syntax errors in test files
"""
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_extra_parentheses(content):
    """Fix extra closing parentheses"""
    # Fix pattern like "delegation_rules={}, ),"
    content = re.sub(
        r"delegation_rules={},\s*\),",
        r"delegation_rules={},",
        content
    )
    
    # Fix pattern like "delegation_triggers={}, ),"
    content = re.sub(
        r"delegation_triggers={},\s*\),",
        r"delegation_triggers={},",
        content
    )
    
    # Fix any "{}, )," pattern
    content = re.sub(
        r"({}),\s*\),",
        r"\1,",
        content
    )
    
    return content


def fix_model_fields(content):
    """Fix model field issues"""
    # Add missing local_overrides and delegation_rules to BranchContext
    content = re.sub(
        r"(agent_assignments={},)\s*\n\s*(delegation_rules={},)",
        r"\1\n            local_overrides={},\n            \2",
        content
    )
    
    # Add missing fields to TaskContext
    content = re.sub(
        r"(task_data={[^}]*},)\s*\n",
        r"\1\n            local_overrides={},\n            implementation_notes={},\n            delegation_triggers={},\n",
        content
    )
    
    return content


def fix_created_at_pattern(content):
    """Fix created_at pattern issues"""
    # Fix pattern where created_at comes after a stray comma and paren
    content = re.sub(
        r",\s*\),\s*(created_at=datetime\.utcnow\(\))",
        r",\n            \1",
        content
    )
    
    # Fix pattern where updated_at comes after a stray comma and paren
    content = re.sub(
        r",\s*\),\s*(updated_at=datetime\.utcnow\(\))",
        r",\n            \1",
        content
    )
    
    return content


def process_file(filepath):
    """Process a single file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        content = fix_extra_parentheses(content)
        content = fix_model_fields(content)
        content = fix_created_at_pattern(content)
        
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
    # Files with syntax errors
    problem_files = [
        "src/tests/integration/test_json_fields.py",
        "src/tests/integration/test_orm_relationships.py",
        "src/tests/integration/test_context_resolution_simple.py",
        "src/tests/integration/test_context_resolution_differentiation.py",
        "src/tests/e2e/test_branch_context_resolution_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e.py",
    ]
    
    fixed_count = 0
    
    for test_file in problem_files:
        filepath = Path(test_file)
        if filepath.exists():
            if process_file(filepath):
                fixed_count += 1
                logger.info(f"Fixed: {test_file}")
    
    logger.info(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())