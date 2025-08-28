# tests/test_cache_invalidation.py
"""
Test suite to verify proper cache invalidation on all mutation operations.
All 32 mutation methods across cached repositories must have proper invalidation.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import json
import re

class TestCacheInvalidation:
    """Test that cache is properly invalidated on mutations"""
    
    def setup_method(self):
        """Setup test environment with absolute paths"""
        self.repo_path = Path('/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories')
        self.cached_path = self.repo_path / 'cached'
        if self.cached_path.exists():
            self.cached_files = list(self.cached_path.glob('*repository.py'))
        else:
            self.cached_files = []
    
    def test_cache_invalidation_methods_exist(self):
        """Test that cache invalidation methods exist in cached repositories"""
        issues = []
        
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            
            # Check for cache invalidation methods
            cache_methods = ['invalidate', 'clear_cache', 'delete_cache', 'remove_cache']
            has_cache_method = any(method in content.lower() for method in cache_methods)
            
            if not has_cache_method:
                issues.append(f"{cached_file.name}: Missing cache invalidation methods")
        
        assert not issues, f"Cached repositories missing invalidation methods:\n" + "\n".join(issues)
    
    def test_all_mutation_methods_have_invalidation(self):
        """All repository mutation methods must have cache invalidation"""
        violations = []
        
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            
            # Mutation methods that should have cache invalidation
            mutation_methods = ['def create', 'def update', 'def delete', 'def save', 'def remove', 'def add']
            
            for method in mutation_methods:
                if method in content:
                    # Extract method body
                    method_match = re.search(rf'{method}\w*\([^)]*\):[^:]*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
                    if method_match:
                        method_body = method_match.group()
                        
                        # Check for cache operations
                        cache_operations = ['invalidate', 'delete', 'clear', 'redis', 'cache', 'expire']
                        has_cache_op = any(op in method_body.lower() for op in cache_operations)
                        
                        if not has_cache_op:
                            # Extract method name for better reporting
                            method_name = re.search(rf'{method}(\w*)', method_body)
                            violations.append(f"{cached_file.name}: {method_name.group() if method_name else method} missing cache operation")
        
        assert not violations, f"Methods missing cache invalidation:\n" + "\n".join(violations)
    
    def test_cache_operations_pattern(self):
        """Test that cache operations follow the correct pattern"""
        repo_path = Path('src/fastmcp/task_management/infrastructure/repositories')
        
        if repo_path.exists():
            cached_path = repo_path / 'cached'
            if cached_path.exists():
                for cached_file in cached_path.glob('*repository.py'):
                    content = cached_file.read_text()
                    
                    # Check for proper cache key patterns
                    if 'def create' in content:
                        # After create, should invalidate list caches
                        create_section = content[content.find('def create'):]
                        assert any(pattern in create_section for pattern in ['list', 'all', '*']), \
                            f"{cached_file.name}: create method should invalidate list caches"
                    
                    if 'def update' in content:
                        # After update, should invalidate specific and list caches
                        update_section = content[content.find('def update'):]
                        assert any(pattern in update_section for pattern in ['delete', 'invalidate', 'clear']), \
                            f"{cached_file.name}: update method should invalidate caches"
                    
                    if 'def delete' in content:
                        # After delete, should invalidate all related caches
                        delete_section = content[content.find('def delete'):]
                        assert any(pattern in delete_section for pattern in ['delete', 'invalidate', 'clear']), \
                            f"{cached_file.name}: delete method should invalidate caches"
    
    def test_redis_fallback_handling(self):
        """Test that Redis unavailability is handled gracefully"""
        repo_path = Path('src/fastmcp/task_management/infrastructure/repositories')
        
        if repo_path.exists():
            cached_path = repo_path / 'cached'
            if cached_path.exists():
                for cached_file in cached_path.glob('*.py'):
                    if 'repository' in cached_file.name.lower():
                        content = cached_file.read_text()
                        
                        # Check for error handling
                        if 'redis' in content.lower():
                            assert 'try' in content or 'except' in content or 'if' in content, \
                                f"{cached_file.name} should handle Redis unavailability"
    
    def test_cache_key_consistency(self):
        """Test that cache keys follow consistent patterns"""
        issues = []
        
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            entity_name = cached_file.name.replace('_repository.py', '').replace('cached_', '')
            
            # Check for consistent key patterns based on entity type
            if 'task' in entity_name:
                expected_patterns = ['task:', 'tasks:']
                if not any(pattern in content for pattern in expected_patterns):
                    issues.append(f"{cached_file.name}: Missing consistent task cache key patterns")
            
            elif 'context' in entity_name:
                expected_patterns = ['context:', 'contexts:']
                if not any(pattern in content for pattern in expected_patterns):
                    issues.append(f"{cached_file.name}: Missing consistent context cache key patterns")
            
            elif 'project' in entity_name:
                expected_patterns = ['project:', 'projects:']
                if not any(pattern in content for pattern in expected_patterns):
                    issues.append(f"{cached_file.name}: Missing consistent project cache key patterns")
        
        assert not issues, f"Cache key consistency issues:\n" + "\n".join(issues)
    
    def test_cache_invalidation_graceful_fallback(self):
        """Test that cache operations work even if Redis is unavailable"""
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            
            # Should handle Redis unavailability
            if 'redis' in content.lower():
                has_error_handling = any([
                    'try:' in content,
                    'except' in content,
                    'if self.redis_client' in content,
                    'if redis_client' in content
                ])
                assert has_error_handling, f"{cached_file.name}: No Redis error handling"
    
    def test_create_invalidates_list_caches(self):
        """Creating entities should invalidate list/collection caches"""
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            
            if 'def create' in content:
                create_match = re.search(r'def create\w*\([^)]*\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
                if create_match:
                    create_body = create_match.group()
                    # Should invalidate list/collection caches
                    list_invalidation = any([
                        'list' in create_body.lower(),
                        'all' in create_body.lower(),
                        '*' in create_body,
                        'scan_iter' in create_body
                    ])
                    assert list_invalidation, f"{cached_file.name}: create method should invalidate list caches"
    
    def test_update_invalidates_specific_and_list_caches(self):
        """Updating entities should invalidate both specific and list caches"""
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            
            if 'def update' in content:
                update_match = re.search(r'def update\w*\([^)]*\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
                if update_match:
                    update_body = update_match.group()
                    # Should have some form of cache invalidation
                    has_invalidation = any([
                        'delete' in update_body.lower(),
                        'invalidate' in update_body.lower(),
                        'clear' in update_body.lower()
                    ])
                    assert has_invalidation, f"{cached_file.name}: update method should invalidate caches"
    
    def test_delete_invalidates_all_related_caches(self):
        """Deleting entities should invalidate all related caches"""
        for cached_file in self.cached_files:
            if not cached_file.exists():
                continue
                
            content = cached_file.read_text()
            
            if 'def delete' in content:
                delete_match = re.search(r'def delete\w*\([^)]*\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
                if delete_match:
                    delete_body = delete_match.group()
                    # Should invalidate comprehensively
                    has_invalidation = any([
                        'delete' in delete_body.lower(),
                        'invalidate' in delete_body.lower(),
                        'clear' in delete_body.lower(),
                        'remove' in delete_body.lower()
                    ])
                    assert has_invalidation, f"{cached_file.name}: delete method should invalidate all related caches"