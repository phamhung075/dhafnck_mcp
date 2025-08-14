"""
Test for ContextCacheService missing methods fix
"""

import unittest
from unittest.mock import Mock, AsyncMock
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["PYTEST_CURRENT_TEST"] = "test_context_cache_service_fix.py::test_context_cache_service_has_invalidate_method"
test_db_path = project_root / "database" / "data" / "dhafnck_mcp_test.db"
test_db_path.parent.mkdir(parents=True, exist_ok=True)
os.environ["MCP_DB_PATH"] = str(test_db_path)

from fastmcp.task_management.application.services.context_cache_service import ContextCacheService


class TestContextCacheServiceFix(unittest.TestCase):
    def setup_method(self, method):
        """Setup before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data
            session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
            session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
            session.commit()
    
    def setUp(self):
        """Set up test"""
        # Mock repository
        self.mock_repository = Mock()
        self.cache_service = ContextCacheService(repository=self.mock_repository)
    
    def test_context_cache_service_has_invalidate_method(self):
        """Test that ContextCacheService has the invalidate method"""
        # Check that the invalidate method exists
        self.assertTrue(hasattr(self.cache_service, 'invalidate'))
        
        # Check that it's callable
        self.assertTrue(callable(getattr(self.cache_service, 'invalidate')))
        
        # Check method signature
        import inspect
        sig = inspect.signature(self.cache_service.invalidate)
        params = list(sig.parameters.keys())
        self.assertIn('level', params)
        self.assertIn('context_id', params)
        
        print("✓ ContextCacheService.invalidate method exists and has correct signature")
    
    def test_context_cache_service_has_get_method(self):
        """Test that ContextCacheService has the get method"""
        # Check that the get method exists
        self.assertTrue(hasattr(self.cache_service, 'get'))
        
        # Check that it's callable
        self.assertTrue(callable(getattr(self.cache_service, 'get')))
        
        # Check method signature
        import inspect
        sig = inspect.signature(self.cache_service.get)
        params = list(sig.parameters.keys())
        self.assertIn('level', params)
        self.assertIn('context_id', params)
        
        print("✓ ContextCacheService.get method exists and has correct signature")
    
    def test_context_cache_service_has_required_sync_methods(self):
        """Test that ContextCacheService has sync wrapper methods"""
        required_methods = [
            'get_context',
            'set_context', 
            'invalidate_context',
            'clear_cache'
        ]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(self.cache_service, method_name), 
                          f"Missing method: {method_name}")
            self.assertTrue(callable(getattr(self.cache_service, method_name)),
                          f"Method not callable: {method_name}")
        
        print("✓ All required sync wrapper methods exist")
    
    def test_invalidate_method_is_async(self):
        """Test that invalidate method returns expected result"""
        # The invalidate method is async, so it returns a coroutine
        import asyncio
        import inspect
        
        # Check if the method is async
        self.assertTrue(inspect.iscoroutinefunction(self.cache_service.invalidate))
        
        # Run the async method and check result
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.cache_service.invalidate('task', 'test-id'))
            self.assertIsInstance(result, bool)
        finally:
            loop.close()
        
        print("✓ ContextCacheService.invalidate method works asynchronously")


if __name__ == "__main__":
    # Run the test
    test = TestContextCacheServiceFix()
    test.setUp()
    
    try:
        test.test_context_cache_service_has_invalidate_method()
        test.test_context_cache_service_has_get_method() 
        test.test_context_cache_service_has_required_sync_methods()
        
        # Run async test
        import asyncio
        asyncio.run(test.test_invalidate_method_is_async())
        
        print("\n✅ All ContextCacheService fix tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()