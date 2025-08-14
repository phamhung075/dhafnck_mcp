#!/usr/bin/env python3
"""
Test script for agent auto-registration duplicate key constraint fix

This script tests that the agent auto-registration properly handles:
1. Duplicate key constraint violations
2. Race conditions
3. @ prefix handling
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent_auto_registration():
    """Test agent auto-registration with duplicate handling"""
    
    try:
        # Import required modules
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from fastmcp.task_management.infrastructure.repositories.orm.agent_repository import ORMAgentRepository
        
        logger.info("=" * 60)
        logger.info("TESTING AGENT AUTO-REGISTRATION DUPLICATE FIX")
        logger.info("=" * 60)
        
        # Get database configuration
        db_config = get_db_config()
        if not db_config:
            logger.error("Could not get database configuration")
            return False
        
        # Create repository
        agent_repo = ORMAgentRepository(project_id="test_project")
        
        # Test 1: Auto-register an agent with a name
        logger.info("\nTest 1: Auto-register agent with name...")
        test_agent_id = str(uuid.uuid4())
        test_branch_id = str(uuid.uuid4())
        
        result1 = agent_repo.assign_agent_to_tree(
            project_id="test_project",
            agent_id=f"{test_agent_id}:test_agent",
            git_branch_id=test_branch_id
        )
        
        logger.info(f"Result 1: {result1}")
        assert result1["success"], "First assignment should succeed"
        assert result1.get("auto_registered"), "Agent should be auto-registered"
        
        # Test 2: Try to assign the same agent again (should not duplicate)
        logger.info("\nTest 2: Assign same agent again...")
        result2 = agent_repo.assign_agent_to_tree(
            project_id="test_project",
            agent_id=f"{test_agent_id}:test_agent",
            git_branch_id=test_branch_id
        )
        
        logger.info(f"Result 2: {result2}")
        assert result2["success"], "Second assignment should succeed"
        assert not result2.get("auto_registered", False), "Agent should not be re-registered"
        
        # Test 3: Test with @ prefix
        logger.info("\nTest 3: Test agent name with @ prefix...")
        test_agent_name = "@coding_agent"
        
        # First find by name to see if it exists
        existing = agent_repo.find_by_name(test_agent_name)
        if existing:
            logger.info(f"Agent {test_agent_name} already exists with ID: {existing.id}")
            agent_id_to_use = existing.id
        else:
            # Generate UUID for new agent
            namespace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "test_project")
            agent_id_to_use = str(uuid.uuid5(namespace_uuid, test_agent_name.lstrip('@')))
        
        result3 = agent_repo.assign_agent_to_tree(
            project_id="test_project",
            agent_id=f"{agent_id_to_use}:coding_agent",
            git_branch_id=test_branch_id
        )
        
        logger.info(f"Result 3: {result3}")
        assert result3["success"], "Assignment with @ prefix should succeed"
        
        # Test 4: Simulate race condition (try to create the same agent twice rapidly)
        logger.info("\nTest 4: Simulate race condition...")
        race_agent_id = str(uuid.uuid4())
        race_branch_id = str(uuid.uuid4())
        
        # Try to assign the same agent from two "concurrent" operations
        # In reality, these will be sequential, but the code should handle it
        result4a = agent_repo.assign_agent_to_tree(
            project_id="test_project",
            agent_id=f"{race_agent_id}:race_agent",
            git_branch_id=race_branch_id
        )
        
        result4b = agent_repo.assign_agent_to_tree(
            project_id="test_project",
            agent_id=f"{race_agent_id}:race_agent",
            git_branch_id=race_branch_id
        )
        
        logger.info(f"Result 4a: {result4a}")
        logger.info(f"Result 4b: {result4b}")
        
        assert result4a["success"], "First race condition assignment should succeed"
        assert result4b["success"], "Second race condition assignment should succeed"
        
        # Only one should be auto-registered
        auto_registered_count = sum([
            result4a.get("auto_registered", False),
            result4b.get("auto_registered", False)
        ])
        assert auto_registered_count <= 1, "Only one agent should be auto-registered in race condition"
        
        # Test 5: Verify all agents were created correctly
        logger.info("\nTest 5: Verify all agents exist...")
        
        agent1 = agent_repo.get_by_id(test_agent_id)
        assert agent1 is not None, "Test agent should exist"
        logger.info(f"✓ Agent 1 exists: {agent1.name}")
        
        agent3 = agent_repo.get_by_id(agent_id_to_use)
        assert agent3 is not None, "Coding agent should exist"
        logger.info(f"✓ Agent 3 exists: {agent3.name}")
        
        agent4 = agent_repo.get_by_id(race_agent_id)
        assert agent4 is not None, "Race condition agent should exist"
        logger.info(f"✓ Agent 4 exists: {agent4.name}")
        
        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    success = asyncio.run(test_agent_auto_registration())
    
    if success:
        logger.info("✅ Agent duplicate fix test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Agent duplicate fix test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()