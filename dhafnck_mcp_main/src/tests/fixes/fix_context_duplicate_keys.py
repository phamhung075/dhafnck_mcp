#!/usr/bin/env python3
"""
Fix duplicate key violations in context resolution tests for PostgreSQL.

This script fixes tests that are failing with 'duplicate key value violates unique constraint' errors
when running with PostgreSQL. The main issue is that multiple tests are trying to create the same
global_singleton context without proper cleanup or checking if it already exists.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_global_singleton_creation(content: str) -> str:
    """Fix global_singleton creation to handle existing records."""
    
    # Pattern 1: Direct GlobalContext creation with id="global_singleton"
    pattern1 = r'(global_ctx\s*=\s*GlobalContext\s*\(\s*id\s*=\s*["\']global_singleton["\'])'
    
    # Replace with ON CONFLICT handling for raw SQL or check existence first
    if 'session.execute(text(' in content:
        # For tests using raw SQL, add ON CONFLICT
        content = re.sub(
            r'(INSERT INTO global_contexts.*?VALUES.*?\))\s*(\)|;)',
            r'\1 ON CONFLICT (id) DO UPDATE SET updated_at = EXCLUDED.updated_at\2',
            content,
            flags=re.DOTALL
        )
    
    # For ORM-based tests, add existence check before creation
    if 'global_ctx = GlobalContext(' in content and 'id="global_singleton"' in content:
        # Add check before creation
        check_code = '''
            # Check if global_singleton already exists
            existing_global = db_session.query(GlobalContext).filter_by(id="global_singleton").first()
            if not existing_global:'''
        
        # Find the global_ctx creation and indent it
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'global_ctx = GlobalContext(' in line and 'id="global_singleton"' in lines[i:i+20]:
                # Find the indentation
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                # Add the check
                new_lines.append(indent_str + '# Check if global_singleton already exists')
                new_lines.append(indent_str + 'existing_global = db_session.query(GlobalContext).filter_by(id="global_singleton").first()')
                new_lines.append(indent_str + 'if existing_global:')
                new_lines.append(indent_str + '    global_ctx = existing_global')
                new_lines.append(indent_str + 'else:')
                
                # Add the original creation with extra indent
                j = i
                while j < len(lines) and (j == i or not lines[j].strip() or lines[j].startswith(indent_str + ' ')):
                    new_lines.append('    ' + lines[j])
                    j += 1
                i = j - 1
            else:
                new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
    
    return content


def fix_project_context_duplicate(content: str) -> str:
    """Fix project context creation to handle duplicates."""
    
    # For project contexts, add ON CONFLICT for SQL inserts
    if 'INSERT INTO project_contexts' in content:
        content = re.sub(
            r'(INSERT INTO project_contexts.*?VALUES.*?\))\s*(\)|;)',
            r'\1 ON CONFLICT (project_id) DO UPDATE SET updated_at = EXCLUDED.updated_at\2',
            content,
            flags=re.DOTALL
        )
    
    # For ORM-based project context creation
    if 'ProjectContext(' in content:
        # Add try-except around db_session.add() for project contexts
        content = re.sub(
            r'(db_session\.add\(project_ctx\))',
            r'try:\n                \1\n            except Exception:\n                db_session.rollback()\n                project_ctx = db_session.query(ProjectContext).filter_by(project_id=project.id).first()',
            content
        )
    
    return content


def fix_branch_context_duplicate(content: str) -> str:
    """Fix branch context creation to handle duplicates."""
    
    # For branch contexts, add ON CONFLICT for SQL inserts
    if 'INSERT INTO branch_contexts' in content:
        content = re.sub(
            r'(INSERT INTO branch_contexts.*?VALUES.*?\))\s*(\)|;)',
            r'\1 ON CONFLICT (branch_id) DO UPDATE SET updated_at = EXCLUDED.updated_at\2',
            content,
            flags=re.DOTALL
        )
    
    return content


def add_cleanup_to_setup_method(content: str) -> str:
    """Enhance setup_method to clean up contexts properly."""
    
    # Find setup_method and add context cleanup
    if 'def setup_method(self, method):' in content:
        # Add context cleanup queries
        cleanup_addition = '''
                # Clean up contexts
                session.execute(text("DELETE FROM task_contexts WHERE task_id LIKE 'test-%'"))
                session.execute(text("DELETE FROM branch_contexts WHERE branch_id IN (SELECT id FROM project_git_branchs WHERE project_id LIKE 'test-%')"))
                session.execute(text("DELETE FROM project_contexts WHERE project_id LIKE 'test-%'"))
                # Don't delete global_singleton - it might be needed by the test framework'''
        
        # Insert after the tasks/projects cleanup
        content = re.sub(
            r'(session\.execute\(text\("DELETE FROM projects.*?\)\))',
            r'\1' + cleanup_addition,
            content,
            flags=re.DOTALL
        )
    
    return content


def fix_test_file(file_path: Path) -> bool:
    """Fix a single test file."""
    print(f"Fixing {file_path}...")
    
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        content = fix_global_singleton_creation(content)
        content = fix_project_context_duplicate(content)
        content = fix_branch_context_duplicate(content)
        content = add_cleanup_to_setup_method(content)
        
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
    test_files = [
        "src/tests/e2e/test_branch_context_resolution_simple_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py", 
        "src/tests/integration/test_context_resolution_simple.py",
        "src/tests/e2e/test_branch_context_resolution_e2e.py",
        "src/tests/integration/test_context_resolution_differentiation.py",
        "src/tests/integration/test_unified_context_integration.py",
    ]
    
    fixed_count = 0
    
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            if fix_test_file(file_path):
                fixed_count += 1
        else:
            print(f"✗ File not found: {test_file}")
    
    print(f"\n✅ Fixed {fixed_count} files for PostgreSQL duplicate key violations")


if __name__ == "__main__":
    main()