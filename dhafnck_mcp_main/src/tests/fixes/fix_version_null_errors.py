#!/usr/bin/env python3
"""
Fix null value errors for version field in context tests for PostgreSQL.

This script fixes tests that are failing with 'null value in column version' errors
when running with PostgreSQL. The main issue is that the version field needs to be
explicitly set in some cases where PostgreSQL doesn't apply the default value.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_project_context_version(content: str) -> str:
    """Fix ProjectContext creation to ensure version is set."""
    
    # Pattern to find ProjectContext creation without version
    pattern = r'(ProjectContext\s*\((?:(?!version\s*=)[^)]*)+)\)'
    
    def add_version(match):
        # Check if version is already there
        context_args = match.group(1)
        if 'version=' in context_args:
            return match.group(0)
        
        # Add version=1 before the closing parenthesis
        # Remove trailing whitespace/comma
        context_args = context_args.rstrip().rstrip(',')
        return f'{context_args},\n                    version=1\n                )'
    
    content = re.sub(pattern, add_version, content, flags=re.DOTALL)
    return content


def fix_branch_context_version(content: str) -> str:
    """Fix BranchContext creation to ensure version is set."""
    
    # Pattern to find BranchContext creation without version
    pattern = r'(BranchContext\s*\((?:(?!version\s*=)[^)]*)+)\)'
    
    def add_version(match):
        # Check if version is already there
        context_args = match.group(1)
        if 'version=' in context_args:
            return match.group(0)
        
        # Add version=1 before the closing parenthesis
        # Remove trailing whitespace/comma
        context_args = context_args.rstrip().rstrip(',')
        return f'{context_args},\n                    version=1\n                )'
    
    content = re.sub(pattern, add_version, content, flags=re.DOTALL)
    return content


def fix_task_context_version(content: str) -> str:
    """Fix TaskContext creation to ensure version is set."""
    
    # Pattern to find TaskContext creation without version
    pattern = r'(TaskContext\s*\((?:(?!version\s*=)[^)]*)+)\)'
    
    def add_version(match):
        # Check if version is already there
        context_args = match.group(1)
        if 'version=' in context_args:
            return match.group(0)
        
        # Add version=1 before the closing parenthesis
        # Remove trailing whitespace/comma
        context_args = context_args.rstrip().rstrip(',')
        return f'{context_args},\n                    version=1\n                )'
    
    content = re.sub(pattern, add_version, content, flags=re.DOTALL)
    return content


def fix_test_file(file_path: Path) -> bool:
    """Fix a single test file."""
    print(f"Checking {file_path}...")
    
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        content = fix_project_context_version(content)
        content = fix_branch_context_version(content)
        content = fix_task_context_version(content)
        
        # Only write if changed
        if content != original_content:
            file_path.write_text(content)
            print(f"✓ Fixed {file_path}")
            return True
        else:
            print(f"  No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix all affected test files."""
    # List of test files that might have version field issues
    test_files = [
        "src/tests/e2e/test_branch_context_resolution_simple_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py", 
        "src/tests/integration/test_context_resolution_simple.py",
        "src/tests/e2e/test_branch_context_resolution_e2e.py",
        "src/tests/integration/test_context_resolution_differentiation.py",
        "src/tests/integration/test_unified_context_integration.py",
        "src/tests/integration/test_unified_context_unit.py",
        "src/tests/unit/test_context_inheritance.py",
    ]
    
    fixed_count = 0
    
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            if fix_test_file(file_path):
                fixed_count += 1
        else:
            print(f"✗ File not found: {test_file}")
    
    print(f"\n✅ Fixed {fixed_count} files for PostgreSQL version field errors")


if __name__ == "__main__":
    main()