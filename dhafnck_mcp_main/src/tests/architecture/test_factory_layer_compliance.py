"""
Test Factory Layer Compliance

Verifies that factory classes are properly located in the infrastructure layer
and that no application layer files import directly from infrastructure.
"""

import os
import ast
import unittest
from pathlib import Path


class TestFactoryLayerCompliance(unittest.TestCase):
    """Test that factories follow DDD layer architecture"""
    
    def setUp(self):
        """Set up test paths"""
        self.project_root = Path(__file__).parents[2]  # Go up to src directory
        self.app_layer = self.project_root / "fastmcp" / "task_management" / "application"
        self.infra_layer = self.project_root / "fastmcp" / "task_management" / "infrastructure"
        
    def test_no_factories_in_application_layer(self):
        """Verify no factory classes exist in application layer"""
        app_factories_dir = self.app_layer / "factories"
        
        # Directory should not exist or be empty
        if app_factories_dir.exists():
            factory_files = list(app_factories_dir.glob("*_factory.py"))
            self.assertEqual(
                len(factory_files), 0,
                f"Found factory files in application layer: {factory_files}"
            )
            
    def test_factories_exist_in_infrastructure_layer(self):
        """Verify factory classes exist in infrastructure layer"""
        infra_factories_dir = self.infra_layer / "factories"
        
        # Directory should exist and contain factory files
        self.assertTrue(
            infra_factories_dir.exists(),
            "Infrastructure factories directory does not exist"
        )
        
        factory_files = list(infra_factories_dir.glob("*_factory.py"))
        expected_factories = [
            "task_facade_factory.py",
            "subtask_facade_factory.py",
            "unified_context_facade_factory.py",
            "project_facade_factory.py",
            "git_branch_facade_factory.py",
            "agent_facade_factory.py",
            "context_response_factory.py"
        ]
        
        for expected in expected_factories:
            self.assertIn(
                expected,
                [f.name for f in factory_files],
                f"Missing factory in infrastructure layer: {expected}"
            )
            
    def test_no_direct_infrastructure_imports_in_application(self):
        """Verify application layer doesn't import directly from infrastructure"""
        
        def check_imports(file_path):
            """Check a Python file for infrastructure imports"""
            with open(file_path, 'r') as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and 'infrastructure' in node.module:
                                # Exception: importing from infrastructure/factories is allowed
                                if 'factories' not in node.module:
                                    return f"{file_path}: imports from {node.module}"
                except SyntaxError:
                    pass  # Skip files with syntax errors
            return None
        
        violations = []
        for py_file in self.app_layer.rglob("*.py"):
            violation = check_imports(py_file)
            if violation:
                violations.append(violation)
                
        self.assertEqual(
            len(violations), 0,
            f"Found infrastructure imports in application layer:\\n" + "\\n".join(violations)
        )
        
    def test_factory_imports_are_from_infrastructure(self):
        """Verify all factory imports reference infrastructure layer"""
        
        def check_factory_imports(file_path):
            """Check if factory imports are from infrastructure"""
            with open(file_path, 'r') as f:
                content = f.read()
                # Look for factory imports
                if 'from fastmcp.task_management.application.factories' in content:
                    return f"{file_path}: imports factories from application layer"
                if 'from ..application.factories' in content:
                    return f"{file_path}: imports factories from application layer (relative)"
                if 'from ...application.factories' in content:
                    return f"{file_path}: imports factories from application layer (relative)"
            return None
        
        violations = []
        # Check all Python files in the project
        for py_file in self.project_root.rglob("*.py"):
            # Skip test files and migration scripts
            if 'test' not in str(py_file) and 'migration' not in str(py_file):
                violation = check_factory_imports(py_file)
                if violation:
                    violations.append(violation)
                    
        self.assertEqual(
            len(violations), 0,
            f"Found application factory imports:\\n" + "\\n".join(violations[:10])  # Show first 10
        )


if __name__ == '__main__':
    unittest.main()