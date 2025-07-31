#!/usr/bin/env python3
"""
Manual test for unified context system.
Run this to verify the unified context MCP tool is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from fastmcp.server.server import FastMCP
from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools


async def main():
    """Test the unified context system through MCP tools."""
    print("Testing Unified Context System...")
    
    # Create FastMCP server
    mcp = FastMCP("test-server")
    
    # Initialize DDD compliant tools
    tools = DDDCompliantMCPTools()
    tools.register_tools(mcp)
    
    # Get the manage_context tool
    manage_context_tool = None
    for tool in mcp.list_tools():
        if tool["name"] == "manage_context":
            manage_context_tool = tool
            break
    
    if not manage_context_tool:
        print("❌ ERROR: manage_context tool not found!")
        return
    
    print(f"✅ Found manage_context tool")
    print(f"   Description: {manage_context_tool['description'][:100]}...")
    
    # Test creating a task context
    print("\n1. Testing CREATE action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "create",
                "level": "task",
                "context_id": "test-task-123",
                "data": {
                    "title": "Test Task",
                    "description": "Testing unified context system",
                    "status": "in_progress",
                    "branch_id": "test-branch-456"
                }
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ CREATE successful")
        else:
            print(f"   ❌ CREATE failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ CREATE error: {e}")
    
    # Test getting the context
    print("\n2. Testing GET action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "get",
                "level": "task",
                "context_id": "test-task-123"
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ GET successful")
        else:
            print(f"   ❌ GET failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ GET error: {e}")
    
    # Test adding an insight
    print("\n3. Testing ADD_INSIGHT action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "add_insight",
                "level": "task",
                "context_id": "test-task-123",
                "content": "Found reusable authentication pattern",
                "category": "discovery",
                "importance": "high"
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ ADD_INSIGHT successful")
        else:
            print(f"   ❌ ADD_INSIGHT failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ ADD_INSIGHT error: {e}")
    
    # Test updating context
    print("\n4. Testing UPDATE action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "update",
                "level": "task",
                "context_id": "test-task-123",
                "data": {
                    "progress": 75,
                    "status": "testing"
                }
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ UPDATE successful")
        else:
            print(f"   ❌ UPDATE failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ UPDATE error: {e}")
    
    # Test delegation
    print("\n5. Testing DELEGATE action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "delegate",
                "level": "task",
                "context_id": "test-task-123",
                "delegate_to": "project",
                "delegate_data": {
                    "pattern_name": "jwt_authentication",
                    "implementation": "Use JWT tokens with refresh mechanism"
                },
                "delegation_reason": "Reusable authentication pattern for all tasks"
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ DELEGATE successful")
        else:
            print(f"   ❌ DELEGATE failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ DELEGATE error: {e}")
    
    # Test resolve (with inheritance)
    print("\n6. Testing RESOLVE action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "resolve",
                "level": "task",
                "context_id": "test-task-123"
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ RESOLVE successful")
            print(f"   Resolved context has {len(result.get('resolved_context', {}))} keys")
        else:
            print(f"   ❌ RESOLVE failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ RESOLVE error: {e}")
    
    # Test list
    print("\n7. Testing LIST action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "list",
                "level": "task"
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print(f"   ✅ LIST successful - found {len(result.get('contexts', []))} contexts")
        else:
            print(f"   ❌ LIST failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ LIST error: {e}")
    
    # Test delete
    print("\n8. Testing DELETE action...")
    try:
        result = await mcp.call_tool(
            "manage_context",
            arguments={
                "action": "delete",
                "level": "task",
                "context_id": "test-task-123"
            }
        )
        print(f"   Result: {result}")
        if result.get("success"):
            print("   ✅ DELETE successful")
        else:
            print(f"   ❌ DELETE failed: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ DELETE error: {e}")
    
    print("\n✅ Unified Context System test complete!")


if __name__ == "__main__":
    asyncio.run(main())