# tests/test_controller_compliance.py
"""
Test suite to verify that controllers follow DDD architecture patterns.
Controllers must not directly access database or repositories.
All 16 controller files must comply with architecture rules.
"""

import pytest
from pathlib import Path
import re

class TestControllerCompliance:
    """Test that controllers follow DDD architecture - no direct DB/repo access"""
    
    def setup_method(self):
        """Setup test environment with absolute paths"""
        self.controller_path = Path('/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers')
        self.controller_files = list(self.controller_path.glob('*_controller.py'))
        assert len(self.controller_files) > 0, f"No controller files found in {self.controller_path}"
    
    def test_no_direct_database_imports(self):
        """Controllers must not import database directly"""
        violations = []
        
        for controller_file in self.controller_files:
            if not controller_file.exists():
                continue
                
            content = controller_file.read_text()
            
            # Check for direct database imports - expanded list
            forbidden_imports = [
                'from infrastructure.database import',
                'from infrastructure.repositories import',
                'import infrastructure.database',
                'import infrastructure.repositories',
                'from ...infrastructure.database import',
                'from ...infrastructure.repositories import',
                'from fastmcp.task_management.infrastructure.database import',
                'from fastmcp.task_management.infrastructure.repositories import',
            ]
            
            for forbidden in forbidden_imports:
                if forbidden in content:
                    violations.append(f"{controller_file.name}: {forbidden}")
        
        assert not violations, f"Controllers with direct DB/repo imports:\n" + "\n".join(violations)
    
    def test_no_direct_database_usage(self):
        """Controllers must not create database sessions"""
        violations = []
        
        for controller_file in self.controller_files:
            if not controller_file.exists():
                continue
                
            content = controller_file.read_text()
            
            # Check for direct database usage patterns
            forbidden_usage = [
                'SessionLocal()',
                '.session()',
                'Session()',
                'create_engine',
                'Repository()',  # Direct repository instantiation
                'get_db()',
                'next(get_db())',
                'database.connect',
                'db.query(',
                'db.execute(',
                'db.commit()',
                'db.rollback()'
            ]
            
            for forbidden in forbidden_usage:
                if forbidden in content:
                    # Check if it's not in a comment
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if forbidden in line and not line.strip().startswith('#'):
                            violations.append(f"{controller_file.name}:{line_num}: {forbidden}")
        
        assert not violations, f"Controllers with direct DB usage:\n" + "\n".join(violations)
    
    def test_controllers_use_facades(self):
        """Controllers must use facades, not repositories directly"""
        violations = []
        missing_facade = []
        
        for controller_file in self.controller_files:
            if not controller_file.exists():
                continue
                
            content = controller_file.read_text()
            
            # Skip base controller classes
            if 'BaseController' in content or 'AbstractController' in content:
                continue
            
            # Controllers should import facades
            if 'class' in content and 'Controller' in content:
                # Check for facade import
                has_facade_import = any([
                    'from fastmcp.task_management.application.facades import' in content,
                    'from application.facades import' in content,
                    'from ...application.facades import' in content
                ])
                
                if not has_facade_import:
                    missing_facade.append(f"{controller_file.name}: No facade import")
                
                # Check for repository usage instead of facade
                if 'self.repository =' in content and 'self.facade =' not in content:
                    violations.append(f"{controller_file.name}: Uses repository instead of facade")
                
                # Check for direct repository instantiation
                if re.search(r'\w+Repository\(\)', content):
                    violations.append(f"{controller_file.name}: Direct repository instantiation")
        
        all_issues = violations + missing_facade
        assert not all_issues, f"Controllers not properly using facades:\n" + "\n".join(all_issues)
    
    def test_specific_controller_fixes(self):
        """Test that specific known violating controllers are fixed"""
        known_violators = [
            'git_branch_mcp_controller.py',
            'task_mcp_controller.py',
            'subtask_mcp_controller.py',
            'agent_mcp_controller.py',
            'project_mcp_controller.py'
        ]
        
        for controller_name in known_violators:
            controller_path = self.controller_path / controller_name
            if controller_path.exists():
                content = controller_path.read_text()
                
                # These should NOT be present after fixes
                assert 'from infrastructure.repositories.orm import' not in content, \
                    f"{controller_name} still has direct repository import"
                assert 'from infrastructure.database import SessionLocal' not in content, \
                    f"{controller_name} still has SessionLocal import"
                assert 'SessionLocal()' not in content, \
                    f"{controller_name} still creates database sessions"
                assert 'Repository()' not in content, \
                    f"{controller_name} still instantiates repositories directly"
                
                # These SHOULD be present after fixes (for controllers with logic)
                if 'BaseController' not in content:
                    # Check if controller has any methods that need facade
                    if re.search(r'def \w+\(self', content) and 'pass' not in content:
                        assert any([
                            'from application.facades import' in content,
                            'from fastmcp.task_management.application.facades import' in content,
                            'facade' in content.lower()
                        ]), f"{controller_name} should use facades for business logic"
    
    def test_controller_separation_of_concerns(self):
        """Controllers should only handle HTTP/MCP concerns, not business logic"""
        violations = []
        
        for controller_file in self.controller_files:
            if not controller_file.exists():
                continue
                
            content = controller_file.read_text()
            
            # Check for business logic that should be in facades
            business_logic_patterns = [
                r'def calculate_',  # Calculations should be in domain/application
                r'def validate_business_',  # Business validation in domain
                r'def generate_report_',  # Report generation in application
                r'def process_payment_',  # Payment processing in domain
                r'def send_email_',  # Email sending in infrastructure
            ]
            
            for pattern in business_logic_patterns:
                if re.search(pattern, content):
                    violations.append(f"{controller_file.name}: Contains business logic pattern '{pattern}'")
        
        assert not violations, f"Controllers with business logic violations:\n" + "\n".join(violations)