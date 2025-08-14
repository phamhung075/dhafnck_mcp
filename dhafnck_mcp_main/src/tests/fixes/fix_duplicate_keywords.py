#!/usr/bin/env python3
"""
Fix duplicate keyword arguments in test files
"""
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_duplicate_keywords(content):
    """Fix duplicate keyword arguments in function calls"""
    
    # Fix duplicate parent_project_context_id
    content = re.sub(
        r"(parent_project_context_id=project\.id[,\s]*){2,}",
        r"parent_project_context_id=project.id, ",
        content
    )
    
    # Fix duplicate parent_branch_context_id
    content = re.sub(
        r"(parent_branch_context_id=branch\.id[,\s]*){2,}",
        r"parent_branch_context_id=branch.id, ",
        content
    )
    
    # Fix any line that has parent_project_context_id without a comma and then more params
    content = re.sub(
        r"(delegation_rules={}),\s*(parent_project_context_id=project\.id)\s*\n",
        r"\1, \2,\n",
        content
    )
    
    # Fix missing commas before parent_project_context_id
    content = re.sub(
        r"(delegation_rules={})\s+(parent_project_context_id=project\.id)",
        r"\1, \2",
        content
    )
    
    # Fix missing commas before parent_branch_context_id  
    content = re.sub(
        r"(delegation_triggers={})\s+(parent_branch_context_id=branch\.id)",
        r"\1, \2",
        content
    )
    
    return content


def fix_model_constructors(content):
    """Fix model constructor issues"""
    # Fix BranchContext constructors
    pattern = r"(BranchContext\([^)]*)"
    
    def fix_branch_context(match):
        text = match.group(1)
        # Ensure parent_project_context_id comes after delegation_rules
        if "parent_project_context_id" not in text and "delegation_rules={}" in text:
            text = text.replace("delegation_rules={}", "delegation_rules={}, parent_project_context_id=project.id")
        # Remove duplicate parent_project_context_id
        if text.count("parent_project_context_id") > 1:
            # Keep only the first occurrence
            parts = text.split("parent_project_context_id")
            text = parts[0] + "parent_project_context_id" + parts[1].split(",")[0] + "," + ",".join(parts[1].split(",")[1:]).replace("parent_project_context_id=project.id,", "")
        return text
    
    content = re.sub(pattern, fix_branch_context, content, flags=re.MULTILINE | re.DOTALL)
    
    # Similar fix for TaskContext
    pattern = r"(TaskContext\([^)]*)"
    
    def fix_task_context(match):
        text = match.group(1)
        # Ensure parent_branch_context_id comes after delegation_triggers
        if "parent_branch_context_id" not in text and "delegation_triggers={}" in text:
            text = text.replace("delegation_triggers={}", "delegation_triggers={}, parent_branch_context_id=branch.id")
        # Remove duplicate parent_branch_context_id
        if text.count("parent_branch_context_id") > 1:
            parts = text.split("parent_branch_context_id")
            text = parts[0] + "parent_branch_context_id" + parts[1].split(",")[0] + "," + ",".join(parts[1].split(",")[1:]).replace("parent_branch_context_id=branch.id,", "")
        return text
    
    content = re.sub(pattern, fix_task_context, content, flags=re.MULTILINE | re.DOTALL)
    
    return content


def process_file(filepath):
    """Process a single file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        content = fix_duplicate_keywords(content)
        content = fix_model_constructors(content)
        
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
    # Files with known syntax errors
    problem_files = [
        "src/tests/integration/test_json_fields.py",
        "src/tests/integration/test_orm_relationships.py",
        "src/tests/integration/test_context_resolution_simple.py",
        "src/tests/integration/test_context_resolution_differentiation.py",
        "src/tests/e2e/test_branch_context_resolution_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py",
    ]
    
    fixed_count = 0
    
    for test_file in problem_files:
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