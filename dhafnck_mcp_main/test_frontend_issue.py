#!/usr/bin/env python3
"""
Frontend Issue Investigation - Why does frontend show 0 tasks?
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("="*70)
    print("🔍 FRONTEND ISSUE INVESTIGATION - Why 0 tasks?")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        print("\n📊 TEST 1: Direct Database Query")
        print("-" * 50)
        
        from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository
        
        # Test direct repository access
        repo = SupabaseOptimizedRepository()
        tasks = repo.list_tasks_minimal(limit=50)
        print(f"Direct repository query: {len(tasks)} tasks found")
        
        if tasks:
            print("Sample task:")
            print(f"  ID: {tasks[0]['id']}")
            print(f"  Title: {tasks[0]['title']}")
            print(f"  Status: {tasks[0]['status']}")
            print(f"  Created: {tasks[0]['created_at']}")
        
        print("\n📊 TEST 2: MCP Tool Direct Call")
        print("-" * 50)
        
        # Test MCP tool directly
        try:
            from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
            tools = DDDCompliantMCPTools()
            result = tools.manage_task(action="list", limit=50)
            print(f"MCP tools result: {type(result)}")
            
            if isinstance(result, dict) and 'tasks' in result:
                tasks_from_mcp = result['tasks']
                print(f"MCP tool query: {len(tasks_from_mcp)} tasks found")
                
                if tasks_from_mcp:
                    print("Sample MCP task:")
                    print(f"  ID: {tasks_from_mcp[0].get('id', 'N/A')}")
                    print(f"  Title: {tasks_from_mcp[0].get('title', 'N/A')}")
            else:
                print(f"MCP result format: {str(result)[:200]}")
                
        except Exception as e:
            print(f"MCP tool error: {str(e)[:100]}")
        
        print("\n📊 TEST 3: HTTP API Check")
        print("-" * 50)
        
        # Test API endpoints
        api_base = "http://localhost:8000"
        
        endpoints_to_test = [
            "/health",
            "/api/tasks",
            "/api/tasks?limit=10",
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{api_base}{endpoint}", timeout=5)
                print(f"GET {endpoint}: {response.status_code}")
                
                if endpoint == "/api/tasks" and response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"  API returned {len(data)} tasks")
                    elif isinstance(data, dict) and 'tasks' in data:
                        print(f"  API returned {len(data['tasks'])} tasks")
                    else:
                        print(f"  API response format: {str(data)[:100]}")
                        
            except requests.exceptions.ConnectionError:
                print(f"GET {endpoint}: Connection refused (API not running?)")
            except Exception as e:
                print(f"GET {endpoint}: Error - {str(e)[:50]}")
        
        print("\n📊 TEST 4: Frontend API Check")
        print("-" * 50)
        
        # Check if frontend is running and what it's calling
        frontend_url = "http://localhost:3800"
        
        try:
            response = requests.get(frontend_url, timeout=5)
            print(f"Frontend status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Frontend: Not running or not accessible")
        except Exception as e:
            print(f"Frontend error: {str(e)[:50]}")
        
        print("\n📊 TEST 5: Database Table Check")
        print("-" * 50)
        
        # Check database table directly
        try:
            with repo.get_db_session() as session:
                # Count total tasks
                result = session.execute("SELECT COUNT(*) FROM tasks").scalar()
                print(f"Total tasks in database: {result}")
                
                # Count by status
                statuses = session.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status").fetchall()
                print("Tasks by status:")
                for status, count in statuses:
                    print(f"  {status}: {count}")
                
                # Check recent tasks
                recent = session.execute("""
                    SELECT id, title, status, created_at 
                    FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """).fetchall()
                
                print("Recent tasks:")
                for task in recent:
                    print(f"  {task.id[:8]}... {task.title[:30]} ({task.status})")
                    
        except Exception as e:
            print(f"Database check error: {str(e)[:100]}")
        
        print("\n📊 TEST 6: Branch/Project Context Check")
        print("-" * 50)
        
        # Check if frontend is filtering by branch/project
        try:
            # Get all tasks without filtering
            all_tasks = repo.list_tasks_minimal(limit=100)
            print(f"All tasks (no filter): {len(all_tasks)}")
            
            # Check if repo has branch filter
            if repo.git_branch_id:
                print(f"Repository has branch filter: {repo.git_branch_id}")
                
                # Try without branch filter
                repo_no_filter = SupabaseOptimizedRepository(git_branch_id=None)
                tasks_no_filter = repo_no_filter.list_tasks_minimal(limit=100)
                print(f"Tasks without branch filter: {len(tasks_no_filter)}")
            else:
                print("Repository has no branch filter")
            
            # Check git branches
            with repo.get_db_session() as session:
                branches = session.execute("""
                    SELECT git_branch_id, COUNT(*) 
                    FROM tasks 
                    WHERE git_branch_id IS NOT NULL
                    GROUP BY git_branch_id
                """).fetchall()
                
                print("Tasks by git branch:")
                for branch_id, count in branches:
                    print(f"  {branch_id}: {count} tasks")
                    
        except Exception as e:
            print(f"Branch context error: {str(e)[:100]}")
        
        print("\n📊 TEST 7: API Endpoint Simulation")
        print("-" * 50)
        
        # Simulate what the frontend might be calling
        test_calls = [
            ("No parameters", lambda: repo.list_tasks_minimal()),
            ("With limit", lambda: repo.list_tasks_minimal(limit=20)),
            ("With status filter", lambda: repo.list_tasks_minimal(status="todo")),
            ("Standard repo", lambda: repo.list_tasks(limit=20)),
        ]
        
        for test_name, test_func in test_calls:
            try:
                result = test_func()
                print(f"{test_name}: {len(result)} tasks")
            except Exception as e:
                print(f"{test_name}: Error - {str(e)[:50]}")
        
        print("\n📊 TEST 8: Frontend Expected Format Check")
        print("-" * 50)
        
        # Check if the data format matches what frontend expects
        try:
            sample_task = repo.list_tasks_minimal(limit=1)
            if sample_task:
                task = sample_task[0]
                print("Task data structure:")
                for key, value in task.items():
                    print(f"  {key}: {type(value).__name__}")
                
                # Check for required fields
                required_fields = ['id', 'title', 'status', 'created_at']
                missing_fields = [field for field in required_fields if field not in task]
                
                if missing_fields:
                    print(f"Missing required fields: {missing_fields}")
                else:
                    print("All required fields present")
            else:
                print("No tasks to check structure")
                
        except Exception as e:
            print(f"Format check error: {str(e)[:100]}")
        
    except Exception as e:
        print(f"\n❌ Investigation Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("📋 INVESTIGATION SUMMARY")
    print("="*70)
    
    print("\n💡 POSSIBLE CAUSES:")
    print("1. Frontend calling wrong API endpoint")
    print("2. Frontend filtering by non-existent branch/project")
    print("3. API not running or returning wrong format")
    print("4. Frontend caching old empty result")
    print("5. CORS issues preventing API calls")
    print("6. Database connection issues from frontend")
    
    print("\n🔧 TROUBLESHOOTING STEPS:")
    print("1. Check browser dev tools for API calls")
    print("2. Verify API server is running on port 8000")
    print("3. Check for JavaScript errors in console")
    print("4. Clear browser cache and reload")
    print("5. Test API endpoints directly with curl")
    
    print("="*70)

if __name__ == "__main__":
    main()