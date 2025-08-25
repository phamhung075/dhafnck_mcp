#!/usr/bin/env python3
"""
Debug script to test MCP connection and tool availability
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment():
    """Test 1: Check environment configuration"""
    print("\n" + "="*80)
    print("TEST 1: Environment Configuration")
    print("="*80)
    
    transport = os.getenv("FASTMCP_TRANSPORT", "not set")
    host = os.getenv("FASTMCP_HOST", "not set")
    port = os.getenv("FASTMCP_PORT", "not set")
    
    print(f"FASTMCP_TRANSPORT: {transport}")
    print(f"FASTMCP_HOST: {host}")
    print(f"FASTMCP_PORT: {port}")
    
    # Check if we're in Docker or local
    if Path("/.dockerenv").exists():
        print("Running in Docker container")
    else:
        print("Running locally")
    
    return transport


def test_mcp_server_import():
    """Test 2: Try to import and create MCP server"""
    print("\n" + "="*80)
    print("TEST 2: MCP Server Import")
    print("="*80)
    
    try:
        from fastmcp import FastMCP
        print("✅ FastMCP imported successfully")
        
        # Try to create server
        mcp = FastMCP("debug-server")
        print(f"✅ MCP server created: {mcp}")
        
        return mcp
    except Exception as e:
        print(f"❌ Failed to import/create MCP server: {e}")
        return None


def test_tool_registration(mcp):
    """Test 3: Check tool registration"""
    print("\n" + "="*80)
    print("TEST 3: Tool Registration")
    print("="*80)
    
    if not mcp:
        print("❌ No MCP server to test")
        return
    
    try:
        # Check if we can access tools
        from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
        
        print("✅ DDDCompliantMCPTools imported")
        
        # Create tools instance
        tools = DDDCompliantMCPTools()
        print(f"✅ Tools instance created")
        
        # List available methods
        tool_methods = [m for m in dir(tools) if not m.startswith('_')]
        print(f"Available tool methods: {len(tool_methods)}")
        for method in tool_methods[:10]:  # Show first 10
            print(f"  - {method}")
            
    except Exception as e:
        print(f"❌ Failed to test tools: {e}")
        import traceback
        traceback.print_exc()


async def test_http_mcp_endpoint():
    """Test 4: Test HTTP MCP endpoint"""
    print("\n" + "="*80)
    print("TEST 4: HTTP MCP Endpoint")
    print("="*80)
    
    import urllib.request
    import urllib.error
    
    try:
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "debug-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "http://localhost:8000/mcp",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"✅ MCP endpoint responded: {json.dumps(result, indent=2)}")
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            print(f"❌ URL Error: {e}")
                    
    except Exception as e:
        print(f"❌ Failed to connect to HTTP endpoint: {e}")


async def test_sse_endpoint():
    """Test 5: Test SSE endpoint"""
    print("\n" + "="*80)
    print("TEST 5: SSE Endpoint")
    print("="*80)
    
    import urllib.request
    import urllib.error
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/mcp/sse",
            headers={"Accept": "text/event-stream"}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                print(f"✅ SSE endpoint exists (status: {response.status})")
                # Read a bit of the stream
                chunk = response.read(100)
                print(f"First 100 bytes: {chunk}")
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
        except urllib.error.URLError as e:
            print(f"❌ URL Error: {e}")
                    
    except Exception as e:
        print(f"❌ Failed to connect to SSE endpoint: {e}")


def test_stdio_mode():
    """Test 6: Test STDIO mode"""
    print("\n" + "="*80)
    print("TEST 6: STDIO Mode")
    print("="*80)
    
    # Check if we can run in STDIO mode
    stdio_script = Path(__file__).parent / "mcp_stdio_server.py"
    if stdio_script.exists():
        print(f"✅ STDIO server script exists: {stdio_script}")
        
        # Try to import it
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("mcp_stdio", stdio_script)
            module = importlib.util.module_from_spec(spec)
            print("✅ STDIO server script can be imported")
        except Exception as e:
            print(f"❌ Failed to import STDIO script: {e}")
    else:
        print("❌ STDIO server script not found")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("MCP CONNECTION DEBUG TESTS")
    print("="*80)
    
    # Test 1: Environment
    transport = test_environment()
    
    # Test 2: MCP Server
    mcp = test_mcp_server_import()
    
    # Test 3: Tools
    test_tool_registration(mcp)
    
    # Test 4: HTTP endpoint
    await test_http_mcp_endpoint()
    
    # Test 5: SSE endpoint
    await test_sse_endpoint()
    
    # Test 6: STDIO mode
    test_stdio_mode()
    
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)
    
    if transport == "streamable-http":
        print("🔍 Server is configured for HTTP mode but MCP endpoints are not exposed")
        print("📝 The server is running as a regular HTTP API, not an MCP server")
        print("⚠️  MCP tools won't be available through mcp__ prefix")
        print("\nTO FIX:")
        print("1. The server needs to expose MCP protocol endpoints (/mcp or /mcp/sse)")
        print("2. Or run a separate MCP server in STDIO mode")
        print("3. Or configure Claude Code to use HTTP API directly")
    elif transport == "stdio":
        print("🔍 Server is configured for STDIO mode")
        print("📝 This mode requires direct process communication")
        print("⚠️  Won't work with Docker HTTP server")
    else:
        print("❌ No transport configured")
    
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())