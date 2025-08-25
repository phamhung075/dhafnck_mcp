#!/usr/bin/env python3
"""
Test JWT Authentication with the MCP Server

This script tests the JWT authentication flow by making direct HTTP requests
to the MCP server with the JWT token provided by the user.
"""

import requests
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# The JWT token provided by the user (should be passed via environment variable)
import os
JWT_TOKEN = os.getenv("TEST_JWT_TOKEN", "")

# Server URL
SERVER_URL = "http://localhost:8000"

def test_jwt_decode():
    """Test decoding the JWT token without verification to see its contents."""
    import jwt
    
    try:
        # Decode without verification to see payload
        payload = jwt.decode(JWT_TOKEN, options={"verify_signature": False})
        print("✅ JWT Token Payload:")
        print(json.dumps(payload, indent=2))
        
        # Check token expiration
        import datetime
        exp = payload.get('exp')
        if exp:
            exp_date = datetime.datetime.fromtimestamp(exp)
            now = datetime.datetime.now()
            print(f"\n📅 Token expires: {exp_date}")
            print(f"📅 Current time: {now}")
            print(f"📅 Token valid: {'Yes' if exp_date > now else 'No (EXPIRED!)'}")
        
        return payload
    except Exception as e:
        print(f"❌ Failed to decode JWT: {e}")
        return None

def test_server_health():
    """Test if the server is running and responding."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        print(f"✅ Server health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False

def test_mcp_manage_project():
    """Test the manage_project MCP tool with JWT authentication."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    # MCP request to list projects
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "tools/call",
        "params": {
            "name": "manage_project",
            "arguments": {
                "action": "list"
            }
        }
    }
    
    try:
        print(f"\n🔍 Testing MCP manage_project with JWT authentication...")
        print(f"Request URL: {SERVER_URL}/mcp")
        print(f"Request Headers: {headers}")
        print(f"Request Body: {json.dumps(mcp_request, indent=2)}")
        
        response = requests.post(
            f"{SERVER_URL}/mcp",
            headers=headers,
            json=mcp_request,
            timeout=10
        )
        
        print(f"\n📈 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.content:
            try:
                response_json = response.json()
                print(f"Response Body: {json.dumps(response_json, indent=2)}")
                
                # Check if the response contains the expected result
                if "result" in response_json:
                    result = response_json["result"]
                    if "success" in result and result["success"]:
                        print("✅ MCP call succeeded!")
                        return True
                    else:
                        print(f"❌ MCP call failed: {result.get('error', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Unexpected response format: {response_json}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print("❌ Empty response")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_mcp_initialize():
    """Test the MCP initialize handshake."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    # MCP initialize request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "test-init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": True
                },
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        print(f"\n🔍 Testing MCP initialize with JWT authentication...")
        response = requests.post(
            f"{SERVER_URL}/mcp/initialize",
            headers=headers,
            json=mcp_request,
            timeout=10
        )
        
        print(f"📈 Initialize Response Status: {response.status_code}")
        
        if response.content:
            try:
                response_json = response.json()
                print(f"Initialize Response: {json.dumps(response_json, indent=2)}")
                return response.status_code == 200
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        
        return False
            
    except Exception as e:
        print(f"❌ Initialize request failed: {e}")
        return False

def main():
    """Run all authentication tests."""
    print("🧪 Testing JWT Authentication with MCP Server")
    print("=" * 60)
    
    # Step 1: Decode and validate the JWT token
    print("\n1. JWT Token Analysis:")
    payload = test_jwt_decode()
    if not payload:
        print("❌ Cannot proceed without valid JWT token")
        return
    
    # Step 2: Check server health
    print("\n2. Server Health Check:")
    if not test_server_health():
        print("❌ Cannot proceed without running server")
        return
    
    # Step 3: Test MCP initialize
    print("\n3. MCP Initialize Test:")
    if test_mcp_initialize():
        print("✅ MCP initialize succeeded")
    else:
        print("❌ MCP initialize failed")
    
    # Step 4: Test MCP tool with authentication
    print("\n4. MCP Tool Authentication Test:")
    if test_mcp_manage_project():
        print("✅ JWT authentication working!")
    else:
        print("❌ JWT authentication failed")
    
    print("\n" + "=" * 60)
    print("🏁 Test completed")

if __name__ == "__main__":
    main()