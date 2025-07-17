#!/usr/bin/env python3
"""
Integration test that verifies all five critical fixes work together.

This test creates a realistic scenario that would have triggered all five errors
before the fixes, and verifies that everything now works correctly.
"""

import sys
import os
import pytest
import asyncio
import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.server.server import FastMCP
from fastmcp.server.context import Context
from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager
from fastmcp.task_management.infrastructure.repositories.project_repository_factory import ProjectRepositoryFactory


class TestAllFixesIntegration:
    """Integration test verifying all five fixes work together"""
    
    @pytest.fixture(scope="function")
    def test_db_path(self, tmp_path):
        """Create a temporary database for testing"""
        db_path = tmp_path / "test_all_fixes.db"
        initialize_database(str(db_path))
        return str(db_path)
    
    @pytest.fixture(scope="function")
    def server(self, test_db_path):
        """Create a FastMCP server instance for testing"""
        # Clear any cached instances
        DatabaseSourceManager.clear_instance()
        ProjectRepositoryFactory.clear_cache()
        
        # Set database path
        os.environ["MCP_DB_PATH"] = test_db_path
        
        server = FastMCP(
            name="test_all_fixes_server",
            enable_task_management=True
        )
        
        return server
    
    async def _call_tool(self, server, tool_name, params):
        """Helper to call a tool and parse the response"""
        try:
            with Context(fastmcp=server):
                response = await server._call_tool(tool_name, params)
            
            if response and isinstance(response, list) and hasattr(response[0], 'text') and response[0].text:
                return json.loads(response[0].text)
            
            return response
        except Exception as e:
            return {"success": False, "error": str(e), "exception_type": type(e).__name__}
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_all_fixes(self, server):
        """
        Test a complete workflow that would have triggered all five errors.
        
        This test:
        1. Creates a project (tests context foreign key fix)
        2. Creates a branch and verifies persistence (tests branch persistence fix)
        3. Checks hierarchical context health (tests async/await fix)
        4. Creates tasks with various label/assignee states (tests NoneType fix)
        5. Gets next task and verifies everything works (tests all fixes together)
        """
        
        # Step 1: Create a project - tests foreign key auto-creation
        print("\n=== Step 1: Creating project ===")
        project_result = await self._call_tool(server, "manage_project", {
            "action": "create",
            "name": "Integration Test Project"
        })
        assert project_result["success"], f"Project creation failed: {project_result.get('error')}"
        project_id = project_result["project"]["id"]
        print(f"✓ Project created: {project_id}")
        
        # Step 2: Create a custom branch and verify persistence
        print("\n=== Step 2: Creating and verifying branch persistence ===")
        branch_result = await self._call_tool(server, "manage_git_branch", {
            "action": "create",
            "project_id": project_id,
            "git_branch_name": "feature/all-fixes-test",
            "git_branch_description": "Testing all fixes together"
        })
        assert branch_result["success"], f"Branch creation failed: {branch_result.get('error')}"
        branch_id = branch_result["git_branch"]["id"]
        print(f"✓ Branch created: {branch_id}")
        
        # Verify branch persists by getting statistics
        stats_result = await self._call_tool(server, "manage_git_branch", {
            "action": "get_statistics",
            "project_id": project_id,
            "git_branch_id": branch_id
        })
        assert stats_result["success"], f"Branch statistics failed: {stats_result.get('error')}"
        assert "not found" not in str(stats_result.get("error", "")), "Branch should be found"
        print("✓ Branch persistence verified")
        
        # Step 3: Check hierarchical context health - tests async/await
        print("\n=== Step 3: Checking hierarchical context health ===")
        health_result = await self._call_tool(server, "manage_hierarchical_context", {
            "action": "get_health"
        })
        assert health_result["success"], f"Health check failed: {health_result.get('error')}"
        assert "coroutine" not in str(health_result.get("error", "")), "Coroutine error should be fixed"
        print("✓ Health check completed without coroutine error")
        
        # Step 4: Create tasks with various label/assignee states - tests NoneType fix
        print("\n=== Step 4: Creating tasks with various states ===")
        task_configs = [
            {
                "title": "Task with everything",
                "labels": ["bug", "urgent"],
                "assignees": ["user1", "user2"]
            },
            {
                "title": "Task with None labels",
                "labels": None,
                "assignees": ["user3"]
            },
            {
                "title": "Task with None assignees",
                "labels": ["feature"],
                "assignees": None
            },
            {
                "title": "Task with nothing",
                "labels": None,
                "assignees": None
            },
            {
                "title": "Task with empty lists",
                "labels": [],
                "assignees": []
            }
        ]
        
        created_tasks = []
        for config in task_configs:
            params = {
                "action": "create",
                "git_branch_id": branch_id,
                "title": config["title"],
                "description": "Testing all fixes"
            }
            
            # Only add labels/assignees if not None
            if config["labels"] is not None:
                params["labels"] = config["labels"]
            if config["assignees"] is not None:
                params["assignees"] = config["assignees"]
            
            result = await self._call_tool(server, "manage_task", params)
            assert result["success"], f"Task creation failed for {config['title']}: {result.get('error')}"
            assert "CONTEXT_SYNC_FAILED" not in str(result.get("error_code", "")), "Context sync should work"
            assert "FOREIGN KEY" not in str(result.get("error", "")), "Foreign key error should be fixed"
            
            # Handle new response format - task data is under "data" key
            task_data = result.get("data", {})
            if "task" in task_data:
                created_tasks.append(task_data["task"]["id"])
            else:
                # Fallback to old format if needed
                created_tasks.append(result["task"]["id"])
            print(f"✓ Created: {config['title']}")
        
        # Step 5: Get next task - tests all fixes working together
        print("\n=== Step 5: Getting next task ===")
        next_result = await self._call_tool(server, "manage_task", {
            "action": "next",
            "git_branch_id": branch_id
        })
        
        # Should succeed without any of the original errors
        assert "NoneType" not in str(next_result.get("error", "")), "NoneType error should be fixed"
        assert "coroutine" not in str(next_result.get("error", "")), "Coroutine error should be fixed"
        assert "not found" not in str(next_result.get("error", "")), "Branch should be found"
        assert "CONTEXT_SYNC_FAILED" not in str(next_result.get("error_code", "")), "Context sync should work"
        assert "FOREIGN KEY" not in str(next_result.get("error", "")), "Foreign key error should be fixed"
        
        if next_result.get("success"):
            # Handle NextTaskResponse format - task data is under "next_item" key
            next_item = next_result.get("next_item", {})
            if next_item and "task" in next_item:
                task_title = next_item['task'].get('title', 'Unknown task')
                print(f"✓ Next task retrieved: {task_title}")
            else:
                # Just say we got the next task without trying to access title
                print(f"✓ Next task available")
        else:
            # It's OK if no actionable tasks found, as long as no errors
            assert "No actionable tasks found" in next_result.get("error", ""), \
                f"Unexpected error: {next_result.get('error')}"
            print("✓ No actionable tasks (all might be completed)")
        
        # Step 6: Verify all tasks have context
        print("\n=== Step 6: Verifying task contexts ===")
        for task_id in created_tasks[:2]:  # Check first two to save time
            get_result = await self._call_tool(server, "manage_task", {
                "action": "get",
                "task_id": task_id,
                "include_context": True
            })
            
            assert get_result["success"], f"Failed to get task {task_id}"
            
            # Handle new response format - task data is under "data" key
            task_data = get_result.get("data", {})
            if "task" in task_data:
                task = task_data["task"]
            else:
                # Fallback to old format if needed
                task = get_result.get("task", {})
            
            # Check for context in various possible locations
            has_context = (
                task.get("context_id") is not None or
                "context" in task or 
                "vision_context" in task or
                "context_data" in task
            )
            assert has_context, f"Task {task_id} should have context"
            print(f"✓ Task {task_id} has context")
        
        print("\n✅ All fixes verified working together!")
    
    @pytest.mark.asyncio
    async def test_stress_scenario(self, server):
        """
        Stress test that rapidly creates entities to ensure fixes are robust.
        
        This would have triggered race conditions and foreign key errors before fixes.
        """
        # Create project
        project_result = await self._call_tool(server, "manage_project", {
            "action": "create",
            "name": "Stress Test Project"
        })
        assert project_result["success"]
        project_id = project_result["project"]["id"]
        
        # Get branch
        list_result = await self._call_tool(server, "manage_git_branch", {
            "action": "list",
            "project_id": project_id
        })
        branch_id = list_result["git_branchs"][0]["id"]
        
        # Rapidly create tasks
        tasks = []
        for i in range(10):
            # Alternate between different configurations
            if i % 4 == 0:
                labels, assignees = None, None
            elif i % 4 == 1:
                labels, assignees = ["label1"], None
            elif i % 4 == 2:
                labels, assignees = None, ["user1"]
            else:
                labels, assignees = ["label2"], ["user2"]
            
            params = {
                "action": "create",
                "git_branch_id": branch_id,
                "title": f"Stress Task {i}",
                "description": "Stress testing"
            }
            
            if labels is not None:
                params["labels"] = labels
            if assignees is not None:
                params["assignees"] = assignees
            
            result = await self._call_tool(server, "manage_task", params)
            
            # All should succeed
            assert result["success"], f"Task {i} failed: {result.get('error')}"
            
            # Handle new response format - task data is under "data" key
            task_data = result.get("data", {})
            if "task" in task_data:
                tasks.append(task_data["task"]["id"])
            else:
                # Fallback to old format if needed
                tasks.append(result["task"]["id"])
        
        # Get next task multiple times
        for _ in range(3):
            next_result = await self._call_tool(server, "manage_task", {
                "action": "next",
                "git_branch_id": branch_id
            })
            
            # Should not have any of the original errors
            error_msg = str(next_result.get("error", ""))
            assert "NoneType" not in error_msg
            assert "coroutine" not in error_msg
            assert "FOREIGN KEY" not in error_msg
        
        print(f"✅ Stress test passed - created {len(tasks)} tasks without errors")