#!/usr/bin/env python3
"""
Test Supabase Performance Improvements
"""

import time
import requests
import json
from statistics import mean, stdev

def test_mcp_task_list():
    """Test task listing performance through MCP API"""
    
    print("=" * 60)
    print("Testing Supabase Performance with MCP API")
    print("=" * 60)
    
    # Test configuration
    tests = 5
    times = []
    
    for i in range(tests):
        start = time.time()
        
        # Call the MCP API
        response = requests.post(
            "http://localhost:8000/json-rpc",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "jsonrpc": "2.0",
                "method": "manage_task",
                "params": {
                    "action": "list",
                    "limit": "10"
                },
                "id": f"test-{i+1}"
            },
            timeout=30
        )
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
        
        # Print result
        if response.status_code == 200:
            try:
                data = response.json()
                if "result" in data and data["result"].get("success"):
                    tasks = data["result"].get("tasks", [])
                    print(f"Test {i+1}: {elapsed:>8.2f}ms - {len(tasks)} tasks retrieved")
                else:
                    error = data.get("result", {}).get("error", "Unknown error")
                    print(f"Test {i+1}: {elapsed:>8.2f}ms - Error: {error}")
            except json.JSONDecodeError:
                print(f"Test {i+1}: {elapsed:>8.2f}ms - Invalid JSON response")
        else:
            print(f"Test {i+1}: {elapsed:>8.2f}ms - HTTP {response.status_code}")
    
    # Calculate statistics
    if times:
        avg = mean(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\n" + "=" * 60)
        print("Performance Results:")
        print(f"  Average: {avg:>8.2f}ms")
        print(f"  Minimum: {min_time:>8.2f}ms")
        print(f"  Maximum: {max_time:>8.2f}ms")
        
        if len(times) > 1:
            std = stdev(times)
            print(f"  Std Dev: {std:>8.2f}ms")
        
        print("\nPerformance Assessment:")
        if avg < 1000:
            print("  ✅ EXCELLENT - Under 1 second!")
            improvement = ((6500 - avg) / 6500) * 100
            print(f"  📈 {improvement:.1f}% improvement from baseline (6.5s)")
        elif avg < 2000:
            print("  ✅ GOOD - Under 2 seconds")
            improvement = ((6500 - avg) / 6500) * 100
            print(f"  📈 {improvement:.1f}% improvement from baseline (6.5s)")
        elif avg < 3000:
            print("  ⚠️  MODERATE - 2-3 seconds")
            improvement = ((6500 - avg) / 6500) * 100
            print(f"  📈 {improvement:.1f}% improvement from baseline (6.5s)")
        else:
            print("  ❌ NEEDS IMPROVEMENT - Over 3 seconds")
            if avg < 6500:
                improvement = ((6500 - avg) / 6500) * 100
                print(f"  📈 Still {improvement:.1f}% better than baseline")
            else:
                print("  📉 No improvement from baseline")
    
    print("=" * 60)

if __name__ == "__main__":
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(5)
    
    test_mcp_task_list()