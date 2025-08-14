#!/usr/bin/env python3
"""
Fix missing closing parentheses
"""
import re
from pathlib import Path

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix missing closing parenthesis
    content = re.sub(
        r"(delegation_rules={})\s*\n\s*(self\.session\.add)",
        r"\1)\n        \2",
        content
    )
    
    # Fix missing closing parenthesis for TaskContext
    content = re.sub(
        r"(delegation_triggers={},)\s*\n\s*\n\s*(self\.session\.add)",
        r"\1\n        )\n        \n        \2",
        content
    )
    
    # Fix missing closing parenthesis for BranchContext before task_context
    content = re.sub(
        r"(delegation_rules={})\s*\n\s*\n\s*(task_context = TaskContext)",
        r"\1)\n        \n        \2",
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed: {filepath}")

# Fix the two problem files
fix_file("src/tests/integration/test_json_fields.py")
fix_file("src/tests/integration/test_orm_relationships.py")