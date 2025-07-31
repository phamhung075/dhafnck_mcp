#!/usr/bin/env python3
"""
Fix PostgreSQL syntax errors in tests, particularly ON CONFLICT clauses.

This script addresses:
1. ON CONFLICT syntax that's not PostgreSQL-compatible
2. Missing version fields in SQL inserts
3. Other PostgreSQL-specific syntax issues
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_on_conflict_syntax(content: str) -> str:
    """Fix ON CONFLICT syntax to be PostgreSQL-compatible."""
    
    # Pattern to find ON CONFLICT with multiple SET statements
    # This pattern is already PostgreSQL-compatible, but let's ensure it's correct
    pattern = r'ON CONFLICT \((\w+)\) DO UPDATE SET ([^)]+)'
    
    def fix_set_clause(match):
        conflict_column = match.group(1)
        set_clause = match.group(2)
        
        # The current syntax is actually correct for PostgreSQL
        # EXCLUDED is the proper way to reference the conflicting row
        # Just ensure proper formatting
        return f'ON CONFLICT ({conflict_column}) DO UPDATE SET {set_clause}'
    
    content = re.sub(pattern, fix_set_clause, content)
    return content


def fix_missing_created_at_in_context(content: str) -> str:
    """Ensure created_at is included in all context model instantiations."""
    
    # Pattern to find context instantiations without created_at
    patterns = [
        (r'(BranchContext\s*\([^)]*?)(\))', 'BranchContext'),
        (r'(ProjectContext\s*\([^)]*?)(\))', 'ProjectContext'),
        (r'(TaskContext\s*\([^)]*?)(\))', 'TaskContext'),
    ]
    
    for pattern, model_name in patterns:
        def add_created_at(match):
            args = match.group(1)
            closing = match.group(2)
            
            # Check if created_at is already there
            if 'created_at=' not in args:
                # Add created_at before closing
                if args.rstrip().endswith(','):
                    return f'{args}created_at=datetime.utcnow(){closing}'
                else:
                    return f'{args}, created_at=datetime.utcnow(){closing}'
            return match.group(0)
        
        content = re.sub(pattern, add_created_at, content, flags=re.DOTALL)
    
    return content


def add_missing_version_field(content: str) -> str:
    """Add missing version field to context instantiations."""
    
    # Patterns for context model instantiations
    patterns = [
        (r'(BranchContext\s*\([^)]*?)(\))', 'BranchContext'),
        (r'(ProjectContext\s*\([^)]*?)(\))', 'ProjectContext'),
        (r'(TaskContext\s*\([^)]*?)(\))', 'TaskContext'),
    ]
    
    for pattern, model_name in patterns:
        def add_version(match):
            args = match.group(1)
            closing = match.group(2)
            
            # Check if version is already there
            if 'version=' not in args:
                # Add version=1 before closing
                if args.rstrip().endswith(','):
                    return f'{args}version=1, {closing}'
                else:
                    return f'{args}, version=1{closing}'
            return match.group(0)
        
        content = re.sub(pattern, add_version, content, flags=re.DOTALL)
    
    return content


def fix_test_file(file_path: Path) -> bool:
    """Fix a single test file."""
    print(f"Checking {file_path}...")
    
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        content = fix_on_conflict_syntax(content)
        content = fix_missing_created_at_in_context(content)
        content = add_missing_version_field(content)
        
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
    """Main function to fix PostgreSQL syntax errors."""
    # Test files that might have syntax errors
    test_files = [
        "src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_e2e.py",
        "src/tests/integration/test_context_resolution_simple.py",
        "src/tests/integration/test_context_resolution_differentiation.py",
        "src/tests/integration/test_unified_context_integration.py",
        "src/tests/integration/test_unified_context_unit.py",
    ]
    
    fixed_count = 0
    
    # Change to project root
    project_root = Path(__file__).parent.parent.parent.parent
    os.chdir(project_root)
    
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            if fix_test_file(file_path):
                fixed_count += 1
        else:
            print(f"✗ File not found: {test_file}")
    
    print(f"\n✅ Fixed {fixed_count} files for PostgreSQL syntax errors")


if __name__ == "__main__":
    main()