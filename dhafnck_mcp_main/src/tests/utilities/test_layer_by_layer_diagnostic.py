#!/usr/bin/env python3
"""
Layer-by-layer diagnostic module to identify where MCP tools registration fails

This module provides diagnostic functions to test each architectural layer
of the DhafnckMCP system independently, helping to identify exactly where
failures occur.
"""

import sys
import os
import traceback
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path dynamically based on file location
project_root = Path(__file__).resolve().parents[2]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Set database type for testing
os.environ.setdefault('DATABASE_TYPE', 'supabase')

def test_layer(layer_name, test_func):
    """Test a specific layer and report results"""
    print(f"\n{'='*60}")
    print(f"Testing {layer_name}")
    print('='*60)
    try:
        result = test_func()
        print(f"✅ {layer_name} - SUCCESS")
        return True, result
    except Exception as e:
        print(f"❌ {layer_name} - FAILED")
        print(f"   Error: {e}")
        print(f"   Traceback:")
        traceback.print_exc()
        return False, str(e)

def test_domain_layer():
    """Test domain entities and interfaces"""
    logger.info("Testing domain entities...")
    from fastmcp.task_management.domain.entities.task import Task
    from fastmcp.task_management.domain.entities.project import Project
    from fastmcp.task_management.domain.entities.git_branch import GitBranch
    from datetime import datetime
    
    # Create test entities with all required fields
    now = datetime.now()
    task = Task(
        id="test-1", 
        title="Test Task", 
        description="Test description", 
        git_branch_id="branch-1",
        status="pending",
        priority="medium",
        created_at=now,
        updated_at=now
    )
    project = Project(
        id="proj-1", 
        name="Test Project", 
        description="Test project",
        created_at=now,
        updated_at=now
    )
    branch = GitBranch(
        id="branch-1", 
        name="main", 
        description="Main branch", 
        project_id="proj-1",
        created_at=now,
        updated_at=now
    )
    
    logger.info(f"Created task: {task.id}")
    logger.info(f"Created project: {project.id}")
    logger.info(f"Created branch: {branch.id}")
    return "Domain entities work"

def test_infrastructure_database():
    """Test database configuration"""
    logger.info("Testing database configuration...")
    try:
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        db_config = get_db_config()
        logger.info(f"Database type: {db_config.database_type}")
        return f"Database config created with type: {db_config.database_type}"
    except Exception as e:
        logger.warning(f"Database config failed (expected): {e}")
        # This is expected to fail without database config
        # Let's see if repositories can work without it
        return "Database config failed (expected) - checking if mock repositories work"

def test_infrastructure_repositories():
    """Test repository factories"""
    logger.info("Testing repository factories...")
    
    # Test project repository factory
    from fastmcp.task_management.infrastructure.repositories.project_repository_factory import ProjectRepositoryFactory
    proj_repo = ProjectRepositoryFactory.create(repository_type=None, user_id="test")
    logger.info(f"Project repository type: {type(proj_repo).__name__}")
    
    # Test task repository factory
    from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
    task_factory = TaskRepositoryFactory()
    task_repo = task_factory.create_repository("test-project", "main", "test-user")
    logger.info(f"Task repository type: {type(task_repo).__name__}")
    
    # Test subtask repository factory  
    from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory
    subtask_factory = SubtaskRepositoryFactory()
    subtask_repo = subtask_factory.create_subtask_repository("test-project", "main", "test-user")
    logger.info(f"Subtask repository type: {type(subtask_repo).__name__}")
    
    return "Repository factories work"

def test_application_facades():
    """Test application layer facades"""
    logger.info("Testing application facades...")
    
    # Test project facade factory
    from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
    proj_facade_factory = ProjectFacadeFactory()
    proj_facade = proj_facade_factory.create_project_facade(user_id="test")
    logger.info(f"Project facade created: {type(proj_facade).__name__}")
    
    # Test task facade factory
    from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
    from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
    from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory
    
    task_repo_factory = TaskRepositoryFactory()
    subtask_repo_factory = SubtaskRepositoryFactory()
    task_facade_factory = TaskFacadeFactory(task_repo_factory, subtask_repo_factory)
    task_facade = task_facade_factory.create_task_facade("test-project", "branch-1", "test-user")
    logger.info(f"Task facade created: {type(task_facade).__name__}")
    
    return "Application facades work"

def test_interface_controllers():
    """Test interface layer controllers"""
    logger.info("Testing interface controllers...")
    
    # Test project controller
    from fastmcp.task_management.interface.controllers.project_mcp_controller import ProjectMCPController
    from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
    
    proj_facade_factory = ProjectFacadeFactory()
    proj_controller = ProjectMCPController(proj_facade_factory)
    logger.info(f"Project controller created: {type(proj_controller).__name__}")
    
    # Test task controller
    from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
    from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
    from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
    from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory
    
    task_repo_factory = TaskRepositoryFactory()
    subtask_repo_factory = SubtaskRepositoryFactory()
    task_facade_factory = TaskFacadeFactory(task_repo_factory, subtask_repo_factory)
    task_controller = TaskMCPController(task_facade_factory, None, None, task_repo_factory)
    logger.info(f"Task controller created: {type(task_controller).__name__}")
    
    return "Interface controllers work"

def test_ddd_compliant_tools_init():
    """Test DDDCompliantMCPTools initialization"""
    logger.info("Testing DDDCompliantMCPTools initialization...")
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    
    tools = DDDCompliantMCPTools()
    logger.info(f"DDDCompliantMCPTools created: {type(tools).__name__}")
    
    # Check which controllers were initialized
    logger.info(f"Task controller: {tools._task_controller is not None}")
    logger.info(f"Project controller: {tools._project_controller is not None}")
    logger.info(f"Subtask controller: {tools._subtask_controller is not None}")
    logger.info(f"Context controller: {tools._context_controller is not None}")
    logger.info(f"Git branch controller: {tools._git_branch_controller is not None}")
    
    return tools

def test_tool_registration():
    """Test tool registration with mock MCP server"""
    logger.info("Testing tool registration...")
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    
    # Create a mock MCP server
    class MockMCP:
        def __init__(self):
            self.tools = {}
            self.resources = {}
        
        def tool(self, name=None, description=None):
            def decorator(func):
                tool_name = name or func.__name__
                self.tools[tool_name] = func
                logger.info(f"Registered tool: {tool_name}")
                return func
            return decorator
        
        def resource(self, name=None, description=None):
            def decorator(func):
                resource_name = name or func.__name__
                self.resources[resource_name] = func
                logger.info(f"Registered resource: {resource_name}")
                return func
            return decorator
        
        def add_resource(self, resource):
            """Add a resource to the server"""
            logger.info(f"Adding resource: {resource}")
            return resource
    
    mock_mcp = MockMCP()
    
    # Try to register tools
    tools = DDDCompliantMCPTools()
    tools.register_tools(mock_mcp)
    
    logger.info(f"Total tools registered: {len(mock_mcp.tools)}")
    logger.info(f"Registered tools: {list(mock_mcp.tools.keys())}")
    
    return f"Registered {len(mock_mcp.tools)} tools"

def run_diagnostic():
    """Run all layer tests and return results
    
    Returns:
        tuple: (success: bool, results: list, failure_point: str or None)
    """
    print("\n" + "="*60)
    print("LAYER-BY-LAYER DIAGNOSTIC TEST")
    print("="*60)
    
    results = []
    
    # Test each layer
    tests = [
        ("1. Domain Layer", test_domain_layer),
        ("2. Infrastructure - Database Config", test_infrastructure_database),
        ("3. Infrastructure - Repositories", test_infrastructure_repositories),
        ("4. Application - Facades", test_application_facades),
        ("5. Interface - Controllers", test_interface_controllers),
        ("6. DDD Compliant Tools Init", test_ddd_compliant_tools_init),
        ("7. Tool Registration", test_tool_registration),
    ]
    
    for name, test_func in tests:
        success, result = test_layer(name, test_func)
        results.append((name, success, result))
        if not success:
            print(f"\n⚠️  Stopping at {name} due to failure")
            break
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = True
    failed_layer = None
    
    for name, success, result in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if not success:
            print(f"   Failed with: {result[:100]}...")
            all_passed = False
            if failed_layer is None:
                failed_layer = name
    
    # Find the exact failure point
    if failed_layer:
        print(f"\n🎯 FAILURE POINT: {failed_layer}")
        print("This is where we need to focus our fix!")
    else:
        print("\n✅ All layers passed! The issue might be in the actual MCP server integration.")
    
    return all_passed, results, failed_layer


def main():
    """Command-line entry point for diagnostic"""
    success, results, failure_point = run_diagnostic()
    
    # Exit with appropriate code
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()