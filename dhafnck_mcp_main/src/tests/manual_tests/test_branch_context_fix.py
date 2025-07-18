#!/usr/bin/env python3
"""
Manual test script to validate the branch context creation fix.
This script tests the fix for Issue #2: Branch Context Management.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from fastmcp.task_management.application.services.git_branch_service import GitBranchService
from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService

async def test_branch_context_fix():
    """Test the branch context creation fix"""
    
    print("🔧 Testing Branch Context Creation Fix")
    print("="*50)
    
    # Test data
    problematic_branch_id = "e27402a1-3cf1-4b94-889b-0447ed7539bf"
    project_id = "7518324b-bb37-4e19-8e07-f6f9127cfffa"
    
    print(f"📋 Test Data:")
    print(f"   Branch ID: {problematic_branch_id}")
    print(f"   Project ID: {project_id}")
    print()
    
    # Initialize services
    git_branch_service = GitBranchService()
    hierarchical_context_service = HierarchicalContextService()
    
    # Step 1: Verify the branch context doesn't exist (should fail)
    print("🧪 Step 1: Verify branch context doesn't exist")
    try:
        result = hierarchical_context_service.resolve_full_context("branch", problematic_branch_id)
        print("   ❌ UNEXPECTED: Branch context already exists!")
        return False
    except Exception as e:
        print(f"   ✅ EXPECTED: Branch context not found - {str(e)}")
    
    # Step 2: Create the missing branch context
    print("\n🔨 Step 2: Create missing branch context")
    try:
        result = await git_branch_service.create_missing_branch_context(
            branch_id=problematic_branch_id
            # project_id will be auto-detected from the git branch
            # branch_name and description will be auto-detected too
        )
        
        if result["success"]:
            print("   ✅ SUCCESS: Branch context created successfully")
            print(f"   📄 Message: {result['message']}")
        else:
            print(f"   ❌ FAILED: {result['error']}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False
    
    # Step 3: Verify the branch context now exists (should succeed)
    print("\n✅ Step 3: Verify branch context now exists")
    try:
        result = hierarchical_context_service.resolve_full_context("branch", problematic_branch_id)
        print("   ✅ SUCCESS: Branch context resolved successfully")
        print(f"   📊 Resolution path: {result.resolution_path}")
        print(f"   🏃 Cache hit: {result.cache_hit}")
        print(f"   ⏱️  Resolution time: {result.resolution_time_ms:.2f}ms")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: Branch context still not found - {str(e)}")
        return False

async def main():
    """Main test runner"""
    print("🚀 Branch Context Fix Validation Test")
    print("="*50)
    
    try:
        success = await test_branch_context_fix()
        
        print("\n" + "="*50)
        if success:
            print("🎉 ALL TESTS PASSED! Branch context fix is working.")
        else:
            print("💥 TESTS FAILED! Branch context fix needs more work.")
            
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)