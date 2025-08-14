#!/usr/bin/env python3
"""
Fix PostgreSQL test failures comprehensively
"""
import re
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def fix_missing_version_fields(content):
    """Add version field to context model instantiations"""
    # Fix ProjectContext missing version
    content = re.sub(
        r"(ProjectContext\([^)]*)(created_at=datetime\.utcnow\(\),\s*updated_at=datetime\.utcnow\(\))",
        r"\1version=1,\n            \2",
        content
    )
    
    # Fix BranchContext missing version
    content = re.sub(
        r"(BranchContext\([^)]*)(created_at=datetime\.utcnow\(\),\s*updated_at=datetime\.utcnow\(\))",
        r"\1version=1,\n            \2",
        content
    )
    
    # Fix TaskContext missing version
    content = re.sub(
        r"(TaskContext\([^)]*)(created_at=datetime\.utcnow\(\),\s*updated_at=datetime\.utcnow\(\))",
        r"\1version=1,\n            \2",
        content
    )
    
    return content


def fix_missing_metadata_fields(content):
    """Fix missing metadata fields in models"""
    # Project model - ensure metadata is a dict
    content = re.sub(
        r"metadata='{}',",
        r"metadata={},",
        content
    )
    
    # Fix model_metadata references
    content = re.sub(
        r"metadata=\{\}",
        r"model_metadata={}",
        content
    )
    
    return content


def fix_duplicate_key_handling(content):
    """Add unique ID generation and ON CONFLICT handling"""
    # Add import for uuid if not present
    if "import uuid" not in content and "from uuid import" not in content:
        content = re.sub(
            r"(import pytest\n)",
            r"\1import uuid\n",
            content
        )
    
    # Fix global_singleton insertions to use ON CONFLICT
    content = re.sub(
        r"(INSERT INTO global_contexts[^;]+)(;|\n\s*\"\"\"\))",
        r"\1 ON CONFLICT (id) DO UPDATE SET updated_at = EXCLUDED.updated_at\2",
        content
    )
    
    # Add unique ID generation for test entities
    if "test_ids.project_id" not in content and "Project(" in content:
        # Add unique ID generation before Project creation
        content = re.sub(
            r"(\s+)(project = Project\()",
            r"\1project_id = f'test-project-{uuid.uuid4().hex[:8]}'\n\1\2",
            content
        )
        content = re.sub(
            r"(Project\(\s*\n?\s*)(name=)",
            r"\1id=project_id,\n            \2",
            content
        )
    
    return content


def fix_sqlite_syntax(content):
    """Fix SQLite-specific syntax for PostgreSQL"""
    # Fix EXCLUDED.updated_at syntax
    content = re.sub(
        r"ON CONFLICT\s*\([^)]+\)\s*DO UPDATE SET\s+updated_at\s*=\s*EXCLUDED\.updated_at",
        r"ON CONFLICT (name) DO UPDATE SET updated_at = labels.updated_at",
        content
    )
    
    return content


def fix_import_errors(content):
    """Fix import and module errors"""
    # Fix missing _initialize_test_database
    if "_initialize_test_database" in content and "def _initialize_test_database" not in content:
        # Replace with proper database initialization
        content = re.sub(
            r"_initialize_test_database\(\)",
            r"# Database initialization handled by fixtures",
            content
        )
    
    # Fix 'src' module imports
    content = re.sub(
        r"from src\.",
        r"from ",
        content
    )
    
    return content


def fix_async_handling(content):
    """Fix async/coroutine handling"""
    # Fix coroutine assertions
    if "assertIsInstance(result, bool)" in content and "invalidate" in content:
        content = re.sub(
            r"result = self\.cache_service\.invalidate\('task', 'test-id'\)\s*\n\s*self\.assertIsInstance\(result, bool\)",
            r"# The invalidate method returns a coroutine, need to handle async\n        import asyncio\n        loop = asyncio.new_event_loop()\n        result = loop.run_until_complete(self.cache_service.invalidate('task', 'test-id'))\n        self.assertIsInstance(result, bool)",
            content
        )
    
    return content


def fix_test_setup(content):
    """Fix test setup and teardown"""
    # Add proper setup_method if missing
    if "class Test" in content and "setup_method" not in content:
        content = re.sub(
            r"(class Test[^:]+:)\n",
            r"\1\n    def setup_method(self, method):\n        \"\"\"Setup before each test\"\"\"\n        from fastmcp.task_management.infrastructure.database.database_config import get_db_config\n        db_config = get_db_config()\n        with db_config.get_session() as session:\n            # Clean test data\n            session.execute(text(\"DELETE FROM tasks WHERE id LIKE 'test-%'\"))\n            session.execute(text(\"DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'\"))\n            session.commit()\n\n",
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
        content = fix_missing_version_fields(content)
        content = fix_missing_metadata_fields(content)
        content = fix_duplicate_key_handling(content)
        content = fix_sqlite_syntax(content)
        content = fix_import_errors(content)
        content = fix_async_handling(content)
        content = fix_test_setup(content)
        
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
    # Files from the TDD failures
    failing_files = [
        "src/tests/e2e/test_branch_context_resolution_simple_e2e.py",
        "src/tests/e2e/test_branch_context_resolution_simple_e2e_fixed.py",
        "src/tests/integration/test_context_inheritance_fix.py",
        "src/tests/integration/test_context_resolution_simple.py",
        "src/tests/integration/test_label_functionality.py",
        "src/tests/integration/test_unified_context_integration.py",
        "src/tests/test_postgresql_isolation_demo.py",
        "src/tests/test_postgresql_isolation_fix.py",
        "src/tests/unit/test_context_cache_service_fix.py",
        "src/tests/integration/test_mcp_task_retrieval_working.py",
        "src/tests/integration/test_real_scenario_task_completion_fix.py",
        "src/tests/unit/test_automatic_context_sync.py",
    ]
    
    fixed_count = 0
    
    for test_file in failing_files:
        filepath = Path(test_file)
        if filepath.exists():
            if process_file(filepath):
                fixed_count += 1
                logger.info(f"Fixed: {test_file}")
    
    logger.info(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())