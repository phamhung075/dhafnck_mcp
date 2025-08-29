#!/usr/bin/env python
"""Test script to verify MCP integration and identify issues."""

import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = os.getenv("TEST_JWT_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU1OTcwODQ3LCJpYXQiOjE3NTU4ODQ0NDcsImlzcyI6Imh0dHBzOi8vcG1zd212eGh6ZGZ4ZXFzZmRnaWYuc3VwYWJhc2UuY28vYXV0aC92MSIsInN1YiI6IjY1ZDczM2U5LTA0ZDYtNGRkYS05NTM2LTY4OGMzYTU5NDQ4ZSIsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7InVzZXJuYW1lIjoidGVzdHVzZXIiLCJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTU4ODQ0NDd9XSwic2Vzc2lvbl9pZCI6IjEyMzQ1Njc4LTEyMzQtMTIzNC0xMjM0LTEyMzQ1Njc4OTAxMiJ9.NRTRq3d4uVM9PHrqvwkvCA9QXdyHtaXWvx_hcH-dai8")

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        data = response.json()
        print(f"   Server: {data.get('server')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Auth enabled: {data.get('auth_enabled')}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_api_endpoints():
    """Test various API endpoints."""
    print("\nTesting API endpoints...")
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Test projects endpoint
    print("  Testing /api/v2/projects/...")
    try:
        response = requests.get(f"{BASE_URL}/api/v2/projects/", headers=headers)
        if response.status_code == 200:
            print("  ✅ Projects endpoint accessible")
            projects = response.json()
            print(f"     Found {len(projects)} projects")
        else:
            print(f"  ❌ Projects endpoint failed: {response.status_code}")
            print(f"     Response: {response.text}")
    except Exception as e:
        print(f"  ❌ Projects endpoint error: {e}")
    
    # Test tasks endpoint
    print("  Testing /api/v2/tasks/...")
    try:
        response = requests.get(f"{BASE_URL}/api/v2/tasks/", headers=headers)
        if response.status_code == 200:
            print("  ✅ Tasks endpoint accessible")
            tasks = response.json()
            print(f"     Found {len(tasks)} tasks")
        else:
            print(f"  ❌ Tasks endpoint failed: {response.status_code}")
            print(f"     Response: {response.text}")
    except Exception as e:
        print(f"  ❌ Tasks endpoint error: {e}")

def test_create_project():
    """Test creating a project."""
    print("\nTesting project creation...")
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    project_data = {
        "name": "Test MCP Integration",
        "description": "Testing MCP server integration"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v2/projects/", 
                                headers=headers, 
                                json=project_data)
        if response.status_code in [200, 201]:
            print("  ✅ Project created successfully")
            project = response.json()
            print(f"     Project ID: {project.get('id')}")
            return project.get('id')
        else:
            print(f"  ❌ Project creation failed: {response.status_code}")
            print(f"     Response: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Project creation error: {e}")
        return None

def test_create_task(project_id: str = None):
    """Test creating a task."""
    print("\nTesting task creation...")
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    task_data = {
        "title": "Test Task",
        "description": "Testing task creation",
        "status": "pending"
    }
    
    if project_id:
        task_data["project_id"] = project_id
    
    try:
        response = requests.post(f"{BASE_URL}/api/v2/tasks/", 
                                headers=headers, 
                                json=task_data)
        if response.status_code in [200, 201]:
            print("  ✅ Task created successfully")
            task = response.json()
            print(f"     Task ID: {task.get('id')}")
            return task.get('id')
        else:
            print(f"  ❌ Task creation failed: {response.status_code}")
            print(f"     Response: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Task creation error: {e}")
        return None

def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Integration Test Suite")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n⚠️  Server health check failed. Stopping tests.")
        return
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test creating resources
    project_id = test_create_project()
    if project_id:
        test_create_task(project_id)
    else:
        test_create_task()
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)

if __name__ == "__main__":
    main()