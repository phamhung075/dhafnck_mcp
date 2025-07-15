#!/usr/bin/env python3
"""
Manual test script for ContextIDDetector

This script can be run manually to test the ID detector against
the current database with real IDs.

Usage:
    python tests/manual/test_context_id_detector_manual.py [id_to_test]
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.interface.controllers.context_id_detector import ContextIDDetector


def test_id_detection(test_id: str):
    """Test ID detection for a given ID"""
    print(f"\nTesting ID: {test_id}")
    print("-" * 50)
    
    # Detect ID type
    id_type, associated_project_id = ContextIDDetector.detect_id_type(test_id)
    
    print(f"ID Type: {id_type}")
    print(f"Associated Project ID: {associated_project_id}")
    
    # Get context level
    context_level = ContextIDDetector.get_context_level_for_id(test_id)
    print(f"Context Level: {context_level}")
    
    # Interpretation
    print("\nInterpretation:")
    if id_type == "project":
        print("✓ This is a PROJECT ID")
        print("→ Context should be created at PROJECT level")
    elif id_type == "git_branch":
        print("✓ This is a GIT BRANCH ID")
        print("→ Context should be created at TASK level (per architecture)")
        print(f"→ Associated with project: {associated_project_id}")
    elif id_type == "task":
        print("✓ This is a TASK ID")
        print("→ Context should be created at TASK level")
        print(f"→ Associated with project: {associated_project_id}")
    else:
        print("✗ This ID was not found in any table")
        print("→ Context will default to TASK level")


def main():
    """Main function"""
    print("Context ID Detector - Manual Test")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Test specific ID provided as argument
        test_id = sys.argv[1]
        test_id_detection(test_id)
    else:
        # Test with some example IDs
        print("\nNo ID provided. Testing with example IDs...")
        
        # You can update these with actual IDs from your database
        example_ids = [
            "ae88dd28-1905-444d-81d0-e338297239a4",  # Example project ID
            "529a5847-ceb7-4b06-9fc4-472865ec40d1",  # Example branch ID
            "d00a377e-535d-4518-9d2f-c952c9af8b2c",  # Example task ID
            "00000000-0000-0000-0000-000000000000"   # Non-existent ID
        ]
        
        for test_id in example_ids:
            test_id_detection(test_id)
            print()
    
    print("\nTo test a specific ID, run:")
    print("  python tests/manual/test_context_id_detector_manual.py <id-to-test>")


if __name__ == "__main__":
    main()