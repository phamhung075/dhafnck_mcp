#!/usr/bin/env python3
"""
Fix async/await syntax errors in test files
"""
import os
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_await_outside_async(content):
    """Fix 'await' outside async function errors"""
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if line contains await
        if 'await' in line and not line.strip().startswith('#'):
            # Look backward to find the function definition
            j = i - 1
            function_line = None
            indent_level = len(line) - len(line.lstrip())
            
            while j >= 0:
                prev_line = lines[j]
                if 'def ' in prev_line and (prev_line.strip().startswith('def ') or ' def ' in prev_line):
                    function_line = j
                    break
                j -= 1
            
            if function_line is not None:
                func_def = lines[function_line]
                # Check if it's not already async
                if 'async def' not in func_def and 'def test_' in func_def:
                    # This is a test function with await - need to make it sync
                    # Remove await and handle the call synchronously
                    line = line.replace('await ', '')
                    logger.info(f"Removed 'await' from line {i+1}: {line.strip()}")
        
        new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)


def fix_async_test_decorators(content):
    """Ensure async test functions have proper decorators"""
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    # First, ensure pytest is imported if we have async tests
    has_async_tests = 'async def test_' in content
    has_pytest_import = 'import pytest' in content
    
    if has_async_tests and not has_pytest_import:
        # Add pytest import at the beginning
        for j, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                lines.insert(j, 'import pytest')
                break
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is an async test function
        if re.match(r'^\s*async def test_', line):
            # Look backward to check for @pytest.mark.asyncio
            has_asyncio_mark = False
            j = i - 1
            while j >= 0 and (lines[j].strip().startswith('@') or lines[j].strip() == ''):
                if '@pytest.mark.asyncio' in lines[j]:
                    has_asyncio_mark = True
                    break
                j -= 1
            
            if not has_asyncio_mark:
                # Add the decorator
                indent = len(line) - len(line.lstrip())
                new_lines.append(' ' * indent + '@pytest.mark.asyncio')
                logger.info(f"Added @pytest.mark.asyncio decorator to line {i+1}")
        
        new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)


def fix_specific_test_file_issues(filepath, content):
    """Fix specific issues based on the test file"""
    
    if 'test_context_cache_service_fix.py' in str(filepath):
        # Fix the specific async issue in this file
        # The invalidate method is not async, so remove await
        content = re.sub(
            r"result = await self\.cache_service\.invalidate\('task', 'test-id'\)",
            r"result = self.cache_service.invalidate('task', 'test-id')",
            content
        )
        
        # Also fix get_context_with_inheritance if it's not async
        content = re.sub(
            r"result = await facade\.get_context_with_inheritance\(",
            r"result = facade.get_context_with_inheritance(",
            content
        )
    
    return content


def process_file(filepath):
    """Process a single test file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Apply general fixes
        content = fix_await_outside_async(content)
        content = fix_async_test_decorators(content)
        
        # Apply file-specific fixes
        content = fix_specific_test_file_issues(filepath, content)
        
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
    # Files known to have async issues
    problem_files = [
        "src/tests/unit/test_context_cache_service_fix.py",
        "src/tests/integration/test_comprehensive_e2e.py",
        "src/tests/integration/test_mvp_end_to_end.py",
        "src/tests/integration/test_real_docker_e2e.py",
        "src/tests/tools/test_known_working_tools.py",
        "src/tests/tools/test_working_tools_comprehensive.py",
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
    
    # Also scan all test files for async issues
    test_dir = Path("src/tests")
    if test_dir.exists():
        for test_file in test_dir.rglob("test_*.py"):
            if str(test_file) not in problem_files:
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                    if 'await ' in content or 'async def' in content:
                        if process_file(test_file):
                            fixed_count += 1
                            logger.info(f"Fixed: {test_file}")
                except Exception as e:
                    logger.error(f"Error checking {test_file}: {e}")
    
    logger.info(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())