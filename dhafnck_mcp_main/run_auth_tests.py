#!/usr/bin/env python
"""
Simple test runner for auth bridge tests
Sets up test environment without triggering database initialization
"""

import os
import sys
import unittest
from unittest.mock import patch, Mock

# Set test environment
os.environ['TESTING'] = 'true'
os.environ['MCP_DB_PATH'] = '/tmp/test_auth.db'

# Mock database config to prevent initialization during import
sys.modules['fastmcp.task_management.infrastructure.database.database_config'] = Mock()

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Now we can import and run tests
if __name__ == "__main__":
    # Import test module
    from tests.auth.test_auth_bridge_integration import (
        TestAuthBridge,
        TestAuthBridgeDependency,
        TestAuthBridgeIntegration
    )
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuthBridge))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuthBridgeDependency))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuthBridgeIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)