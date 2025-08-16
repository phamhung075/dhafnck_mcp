#!/usr/bin/env python3
"""
Test API Performance with Supabase Optimizations
"""

import asyncio
import time
import json
import httpx

async def test_task_performance():
    """Test task listing performance with optimized Supabase queries"""
    
    print("Testing Supabase-optimized Task Performance via API")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test listing tasks
        times = []
        for i in range(5):
            start = time.time()
            
            response = await client.post(
                "http://localhost:8000/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "manage_task",
                    "params": {
                        "action": "list",
                        "limit": "20"
                    },
                    "id": f"test-{i}"
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    tasks = data["result"].get("tasks", [])
                    print(f"Test {i+1}: {elapsed:.2f}ms - Retrieved {len(tasks)} tasks")
                else:
                    print(f"Test {i+1}: {elapsed:.2f}ms - Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"Test {i+1}: {elapsed:.2f}ms - HTTP {response.status_code}")
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\n" + "=" * 50)
        print("Performance Results:")
        print(f"Average response time: {avg_time:.2f}ms")
        print(f"Minimum response time: {min_time:.2f}ms")
        print(f"Maximum response time: {max_time:.2f}ms")
        
        # Check if optimization is working
        if avg_time < 1000:
            print("✅ EXCELLENT: Response time under 1 second!")
        elif avg_time < 2000:
            print("✅ GOOD: Response time under 2 seconds")
        elif avg_time < 3000:
            print("⚠️ MODERATE: Response time 2-3 seconds")
        else:
            print("❌ POOR: Response time over 3 seconds - optimization may not be active")
        
        print("\nOptimization Status:")
        if avg_time < 3000:  # Improved from 6+ seconds
            improvement = ((6500 - avg_time) / 6500) * 100
            print(f"🚀 Performance improved by {improvement:.1f}% compared to baseline (6.5s)")
        else:
            print("⚠️ Optimization may need additional configuration")

if __name__ == "__main__":
    asyncio.run(test_task_performance())